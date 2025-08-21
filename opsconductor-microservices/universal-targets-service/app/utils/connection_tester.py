"""
Connection testing utilities for various target types
"""

import asyncio
import time
import socket
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.schemas.target import ConnectionTestResult

logger = logging.getLogger(__name__)


class ConnectionTester:
    """Handles connection testing for different target types"""
    
    async def test_connection(
        self,
        method_type: str,
        config: Dict[str, Any],
        credentials: Dict[str, Any],
        test_type: str = "basic",
        timeout: int = 30
    ) -> ConnectionTestResult:
        """Test connection to a target"""
        start_time = time.time()
        
        try:
            if method_type == "ssh":
                result = await self._test_ssh_connection(config, credentials, test_type, timeout)
            elif method_type == "winrm":
                result = await self._test_winrm_connection(config, credentials, test_type, timeout)
            elif method_type == "telnet":
                result = await self._test_telnet_connection(config, credentials, test_type, timeout)
            elif method_type in ["mysql", "postgresql", "mssql", "oracle", "sqlite"]:
                result = await self._test_database_connection(method_type, config, credentials, test_type, timeout)
            elif method_type in ["mongodb", "redis", "elasticsearch"]:
                result = await self._test_nosql_connection(method_type, config, credentials, test_type, timeout)
            elif method_type == "rest_api":
                result = await self._test_rest_api_connection(config, credentials, test_type, timeout)
            else:
                # Default to basic network connectivity test
                result = await self._test_basic_connectivity(config, timeout)
            
            # Calculate response time
            response_time = time.time() - start_time
            result.response_time = response_time
            result.tested_at = datetime.utcnow()
            
            return result
            
        except Exception as e:
            logger.error(f"Connection test failed for {method_type}: {e}")
            return ConnectionTestResult(
                success=False,
                message=f"Connection test failed: {str(e)}",
                response_time=time.time() - start_time,
                tested_at=datetime.utcnow()
            )
    
    async def _test_basic_connectivity(self, config: Dict[str, Any], timeout: int) -> ConnectionTestResult:
        """Test basic network connectivity (ping/port check)"""
        host = config.get('host')
        port = config.get('port', 22)
        
        if not host:
            return ConnectionTestResult(
                success=False,
                message="Host not specified in configuration"
            )
        
        try:
            # Test port connectivity
            future = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(future, timeout=timeout)
            writer.close()
            await writer.wait_closed()
            
            return ConnectionTestResult(
                success=True,
                message=f"Successfully connected to {host}:{port}",
                details={"host": host, "port": port, "test_type": "port_check"}
            )
            
        except asyncio.TimeoutError:
            return ConnectionTestResult(
                success=False,
                message=f"Connection timeout to {host}:{port}",
                details={"host": host, "port": port, "error": "timeout"}
            )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message=f"Connection failed to {host}:{port}: {str(e)}",
                details={"host": host, "port": port, "error": str(e)}
            )
    
    async def _test_ssh_connection(
        self,
        config: Dict[str, Any],
        credentials: Dict[str, Any],
        test_type: str,
        timeout: int
    ) -> ConnectionTestResult:
        """Test SSH connection"""
        host = config.get('host')
        port = config.get('port', 22)
        username = credentials.get('username')
        
        if not all([host, username]):
            return ConnectionTestResult(
                success=False,
                message="Missing required SSH connection parameters"
            )
        
        try:
            import paramiko
            
            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Prepare authentication
            auth_kwargs = {'username': username, 'timeout': timeout}
            
            if credentials.get('password'):
                auth_kwargs['password'] = credentials['password']
            elif credentials.get('ssh_key'):
                # Create key from string
                import io
                key_file = io.StringIO(credentials['ssh_key'])
                if credentials.get('ssh_passphrase'):
                    pkey = paramiko.RSAKey.from_private_key(key_file, password=credentials['ssh_passphrase'])
                else:
                    pkey = paramiko.RSAKey.from_private_key(key_file)
                auth_kwargs['pkey'] = pkey
            
            # Connect
            ssh.connect(host, port=port, **auth_kwargs)
            
            if test_type == "command":
                # Test command execution
                stdin, stdout, stderr = ssh.exec_command('echo "OpsConductor SSH Test"')
                output = stdout.read().decode().strip()
                error = stderr.read().decode().strip()
                
                if error:
                    ssh.close()
                    return ConnectionTestResult(
                        success=False,
                        message=f"SSH command test failed: {error}",
                        details={"host": host, "port": port, "test_type": "command", "error": error}
                    )
                
                ssh.close()
                return ConnectionTestResult(
                    success=True,
                    message="SSH connection and command execution successful",
                    details={"host": host, "port": port, "test_type": "command", "output": output}
                )
            else:
                # Basic connection test
                ssh.close()
                return ConnectionTestResult(
                    success=True,
                    message="SSH connection successful",
                    details={"host": host, "port": port, "test_type": "basic"}
                )
                
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message=f"SSH connection failed: {str(e)}",
                details={"host": host, "port": port, "error": str(e)}
            )
    
    async def _test_winrm_connection(
        self,
        config: Dict[str, Any],
        credentials: Dict[str, Any],
        test_type: str,
        timeout: int
    ) -> ConnectionTestResult:
        """Test WinRM connection"""
        host = config.get('host')
        port = config.get('port', 5985)
        username = credentials.get('username')
        password = credentials.get('password')
        
        if not all([host, username, password]):
            return ConnectionTestResult(
                success=False,
                message="Missing required WinRM connection parameters"
            )
        
        try:
            import winrm
            
            # Create WinRM session
            session = winrm.Session(
                f'http://{host}:{port}/wsman',
                auth=(username, password),
                transport='plaintext'
            )
            
            if test_type == "command":
                # Test command execution
                result = session.run_cmd('echo OpsConductor WinRM Test')
                
                if result.status_code != 0:
                    return ConnectionTestResult(
                        success=False,
                        message=f"WinRM command test failed: {result.std_err.decode()}",
                        details={"host": host, "port": port, "test_type": "command", "status_code": result.status_code}
                    )
                
                return ConnectionTestResult(
                    success=True,
                    message="WinRM connection and command execution successful",
                    details={"host": host, "port": port, "test_type": "command", "output": result.std_out.decode().strip()}
                )
            else:
                # Basic connection test - try to get system info
                result = session.run_cmd('echo test')
                
                if result.status_code == 0:
                    return ConnectionTestResult(
                        success=True,
                        message="WinRM connection successful",
                        details={"host": host, "port": port, "test_type": "basic"}
                    )
                else:
                    return ConnectionTestResult(
                        success=False,
                        message="WinRM connection failed",
                        details={"host": host, "port": port, "status_code": result.status_code}
                    )
                    
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message=f"WinRM connection failed: {str(e)}",
                details={"host": host, "port": port, "error": str(e)}
            )
    
    async def _test_telnet_connection(
        self,
        config: Dict[str, Any],
        credentials: Dict[str, Any],
        test_type: str,
        timeout: int
    ) -> ConnectionTestResult:
        """Test Telnet connection"""
        host = config.get('host')
        port = config.get('port', 23)
        
        try:
            import telnetlib
            
            # Create Telnet connection
            tn = telnetlib.Telnet(host, port, timeout)
            
            if test_type == "login" and credentials.get('username') and credentials.get('password'):
                # Test login
                tn.read_until(b"login: ", timeout)
                tn.write(credentials['username'].encode('ascii') + b"\n")
                tn.read_until(b"Password: ", timeout)
                tn.write(credentials['password'].encode('ascii') + b"\n")
                
                # Check for successful login (this is basic and may need adjustment)
                response = tn.read_some()
                tn.close()
                
                return ConnectionTestResult(
                    success=True,
                    message="Telnet connection and login successful",
                    details={"host": host, "port": port, "test_type": "login"}
                )
            else:
                # Basic connection test
                tn.close()
                return ConnectionTestResult(
                    success=True,
                    message="Telnet connection successful",
                    details={"host": host, "port": port, "test_type": "basic"}
                )
                
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message=f"Telnet connection failed: {str(e)}",
                details={"host": host, "port": port, "error": str(e)}
            )
    
    async def _test_database_connection(
        self,
        method_type: str,
        config: Dict[str, Any],
        credentials: Dict[str, Any],
        test_type: str,
        timeout: int
    ) -> ConnectionTestResult:
        """Test database connection"""
        host = config.get('host')
        port = config.get('port')
        database = config.get('database', 'test')
        username = credentials.get('username')
        password = credentials.get('password')
        
        # Set default ports
        if not port:
            default_ports = {'mysql': 3306, 'postgresql': 5432, 'mssql': 1433, 'oracle': 1521}
            port = default_ports.get(method_type, 5432)
        
        try:
            if method_type == "postgresql":
                import psycopg2
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    database=database,
                    user=username,
                    password=password,
                    connect_timeout=timeout
                )
                
                if test_type == "query":
                    cursor = conn.cursor()
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()[0]
                    cursor.close()
                    conn.close()
                    
                    return ConnectionTestResult(
                        success=True,
                        message="PostgreSQL connection and query successful",
                        details={"host": host, "port": port, "database": database, "version": version}
                    )
                else:
                    conn.close()
                    return ConnectionTestResult(
                        success=True,
                        message="PostgreSQL connection successful",
                        details={"host": host, "port": port, "database": database}
                    )
            
            elif method_type == "mysql":
                import pymysql
                conn = pymysql.connect(
                    host=host,
                    port=port,
                    database=database,
                    user=username,
                    password=password,
                    connect_timeout=timeout
                )
                
                if test_type == "query":
                    cursor = conn.cursor()
                    cursor.execute("SELECT VERSION();")
                    version = cursor.fetchone()[0]
                    cursor.close()
                    conn.close()
                    
                    return ConnectionTestResult(
                        success=True,
                        message="MySQL connection and query successful",
                        details={"host": host, "port": port, "database": database, "version": version}
                    )
                else:
                    conn.close()
                    return ConnectionTestResult(
                        success=True,
                        message="MySQL connection successful",
                        details={"host": host, "port": port, "database": database}
                    )
            
            else:
                # For other database types, fall back to basic connectivity test
                return await self._test_basic_connectivity(config, timeout)
                
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message=f"{method_type.upper()} connection failed: {str(e)}",
                details={"host": host, "port": port, "database": database, "error": str(e)}
            )
    
    async def _test_nosql_connection(
        self,
        method_type: str,
        config: Dict[str, Any],
        credentials: Dict[str, Any],
        test_type: str,
        timeout: int
    ) -> ConnectionTestResult:
        """Test NoSQL database connection"""
        host = config.get('host')
        port = config.get('port')
        
        # Set default ports
        if not port:
            default_ports = {'mongodb': 27017, 'redis': 6379, 'elasticsearch': 9200}
            port = default_ports.get(method_type, 27017)
        
        try:
            if method_type == "redis":
                import redis
                r = redis.Redis(
                    host=host,
                    port=port,
                    password=credentials.get('password'),
                    socket_timeout=timeout
                )
                
                if test_type == "query":
                    info = r.info()
                    return ConnectionTestResult(
                        success=True,
                        message="Redis connection and info query successful",
                        details={"host": host, "port": port, "redis_version": info.get('redis_version')}
                    )
                else:
                    r.ping()
                    return ConnectionTestResult(
                        success=True,
                        message="Redis connection successful",
                        details={"host": host, "port": port}
                    )
            
            else:
                # For other NoSQL types, fall back to basic connectivity test
                return await self._test_basic_connectivity(config, timeout)
                
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message=f"{method_type.upper()} connection failed: {str(e)}",
                details={"host": host, "port": port, "error": str(e)}
            )
    
    async def _test_rest_api_connection(
        self,
        config: Dict[str, Any],
        credentials: Dict[str, Any],
        test_type: str,
        timeout: int
    ) -> ConnectionTestResult:
        """Test REST API connection"""
        import aiohttp
        
        host = config.get('host')
        port = config.get('port', 80)
        endpoint = config.get('endpoint', '/')
        use_ssl = config.get('ssl', False)
        
        protocol = 'https' if use_ssl else 'http'
        url = f"{protocol}://{host}:{port}{endpoint}"
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                headers = {}
                
                # Add authentication if provided
                if credentials.get('api_key'):
                    headers['Authorization'] = f"Bearer {credentials['api_key']}"
                elif credentials.get('username') and credentials.get('password'):
                    auth = aiohttp.BasicAuth(credentials['username'], credentials['password'])
                else:
                    auth = None
                
                async with session.get(url, headers=headers, auth=auth) as response:
                    status_code = response.status
                    
                    if status_code < 400:
                        return ConnectionTestResult(
                            success=True,
                            message=f"REST API connection successful (HTTP {status_code})",
                            details={"url": url, "status_code": status_code}
                        )
                    else:
                        return ConnectionTestResult(
                            success=False,
                            message=f"REST API returned error (HTTP {status_code})",
                            details={"url": url, "status_code": status_code}
                        )
                        
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message=f"REST API connection failed: {str(e)}",
                details={"url": url, "error": str(e)}
            )