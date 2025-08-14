"""
Connection test utilities for testing target connectivity.
"""
import socket
import paramiko
import winrm
import sqlite3
from typing import Dict, Any, Optional
from app.utils.encryption_utils import decrypt_credentials


def test_ssh_connection(host: str, port: int, credentials: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
    """
    Test SSH connection to a target.
    
    Args:
        host: Target IP address or hostname
        port: SSH port (usually 22)
        credentials: Decrypted credentials dictionary
        timeout: Connection timeout in seconds
        
    Returns:
        dict: Test result with success status and message
    """
    try:
        # Create SSH client
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        username = credentials.get('username')
        if not username:
            return {'success': False, 'message': 'Username not found in credentials'}
        
        # Determine authentication method
        if credentials.get('type') == 'ssh_key':
            # SSH key authentication
            private_key_str = credentials.get('private_key')
            passphrase = credentials.get('passphrase')
            
            if not private_key_str:
                return {'success': False, 'message': 'SSH private key not found in credentials'}
            
            try:
                # Try different key types
                private_key = None
                for key_class in [paramiko.RSAKey, paramiko.Ed25519Key, paramiko.ECDSAKey, paramiko.DSSKey]:
                    try:
                        private_key = key_class.from_private_key_string(
                            private_key_str, 
                            password=passphrase if passphrase else None
                        )
                        break
                    except Exception:
                        continue
                
                if private_key is None:
                    return {'success': False, 'message': 'Could not parse SSH private key'}
                
                ssh_client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    pkey=private_key,
                    timeout=timeout,
                    allow_agent=False,
                    look_for_keys=False
                )
                
            except Exception as e:
                return {'success': False, 'message': f'SSH key authentication failed: {str(e)}'}
                
        else:
            # Password authentication
            password = credentials.get('password')
            if not password:
                return {'success': False, 'message': 'Password not found in credentials'}
            
            try:
                ssh_client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    password=password,
                    timeout=timeout,
                    allow_agent=False,
                    look_for_keys=False
                )
            except Exception as e:
                return {'success': False, 'message': f'SSH password authentication failed: {str(e)}'}
        
        # Test command execution
        try:
            stdin, stdout, stderr = ssh_client.exec_command('echo "OpsConductor Connection Test"', timeout=5)
            output = stdout.read().decode().strip()
            
            if "OpsConductor Connection Test" in output:
                return {
                    'success': True, 
                    'message': f'SSH connection successful! Connected to {host}:{port}',
                    'details': f'Authentication: {credentials.get("type", "password")}'
                }
            else:
                return {'success': False, 'message': 'SSH connection established but command execution failed'}
                
        except Exception as e:
            return {'success': False, 'message': f'SSH command execution failed: {str(e)}'}
            
    except socket.timeout:
        return {'success': False, 'message': f'Connection timeout to {host}:{port}'}
    except socket.gaierror:
        return {'success': False, 'message': f'Cannot resolve hostname: {host}'}
    except ConnectionRefusedError:
        return {'success': False, 'message': f'Connection refused by {host}:{port}'}
    except Exception as e:
        return {'success': False, 'message': f'SSH connection failed: {str(e)}'}
    finally:
        try:
            ssh_client.close()
        except:
            pass


def test_winrm_connection(host: str, port: int, credentials: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
    """
    Test WinRM connection to a target.
    
    Args:
        host: Target IP address or hostname
        port: WinRM port (usually 5985 for HTTP, 5986 for HTTPS)
        credentials: Decrypted credentials dictionary
        timeout: Connection timeout in seconds
        
    Returns:
        dict: Test result with success status and message
    """
    try:
        username = credentials.get('username')
        password = credentials.get('password')
        
        if not username or not password:
            return {'success': False, 'message': 'Username and password required for WinRM'}
        
        # Determine protocol based on port
        protocol = 'https' if port == 5986 else 'http'
        endpoint = f'{protocol}://{host}:{port}/wsman'
        
        # Create WinRM session
        try:
            # Use more conservative timeout settings
            session = winrm.Session(
                endpoint,
                auth=(username, password),
                transport='basic'
            )
            
            # Test command execution
            result = session.run_cmd('echo OpsConductor Connection Test')
            
            if result.status_code == 0:
                output = result.std_out.decode().strip()
                if "OpsConductor Connection Test" in output:
                    return {
                        'success': True,
                        'message': f'WinRM connection successful! Connected to {host}:{port}',
                        'details': f'Protocol: {protocol.upper()}, Authentication: Basic'
                    }
                else:
                    return {'success': False, 'message': 'WinRM connection established but command execution failed'}
            else:
                error_msg = result.std_err.decode().strip() if result.std_err else 'Unknown error'
                return {'success': False, 'message': f'WinRM command failed: {error_msg}'}
                
        except winrm.exceptions.WinRMTransportError as e:
            error_msg = str(e).lower()
            if 'timeout' in error_msg:
                return {'success': False, 'message': f'WinRM connection timeout to {host}:{port} - target may be unreachable or WinRM service not running'}
            elif 'unauthorized' in error_msg or 'access is denied' in error_msg:
                return {'success': False, 'message': 'WinRM authentication failed - check username/password'}
            elif 'connection refused' in error_msg:
                return {'success': False, 'message': f'WinRM connection refused by {host}:{port} - check if WinRM service is enabled'}
            elif 'name resolution' in error_msg or 'resolve' in error_msg:
                return {'success': False, 'message': f'Cannot resolve hostname: {host}'}
            else:
                return {'success': False, 'message': f'WinRM transport error: {str(e)}'}
        except Exception as e:
            # More specific error handling for common issues
            error_msg = str(e).lower()
            if 'timeout' in error_msg and 'exceed' in error_msg:
                return {'success': False, 'message': 'WinRM timeout configuration error - this is a client-side issue, please contact support'}
            elif 'connection' in error_msg and 'refused' in error_msg:
                return {'success': False, 'message': f'Connection refused by {host}:{port} - WinRM service may not be running'}
            else:
                return {'success': False, 'message': f'WinRM connection failed: {str(e)}'}
            
    except Exception as e:
        return {'success': False, 'message': f'WinRM connection setup failed: {str(e)}'}


def test_target_connectivity(host: str, port: int, timeout: int = 5) -> bool:
    """
    Test basic network connectivity to a target.
    
    Args:
        host: Target IP address or hostname
        port: Target port
        timeout: Connection timeout in seconds
        
    Returns:
        bool: True if target is reachable, False otherwise
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, socket.gaierror):
        return False


def test_smtp_connection(host: str, port: int, credentials: Dict[str, Any], config: Dict[str, Any] = None, timeout: int = 20) -> Dict[str, Any]:
    """
    Test SMTP connection to an email server.
    
    Args:
        host: SMTP server hostname or IP
        port: SMTP port (usually 587, 465, or 25)
        credentials: Decrypted credentials dictionary
        config: SMTP configuration (encryption, server_type, etc.)
        timeout: Connection timeout in seconds
        
    Returns:
        dict: Test result with success status and message
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        username = credentials.get('username')
        password = credentials.get('password')
        
        if not username or not password:
            return {'success': False, 'message': 'SMTP requires username and password'}
        
        # Get SMTP configuration
        config = config or {}
        encryption = config.get('encryption', 'starttls')
        server_type = config.get('server_type', 'smtp')
        test_recipient = config.get('test_recipient', '')
        
        # Choose the appropriate SMTP class based on encryption
        try:
            if encryption == 'ssl':
                # For SSL connections, we need to handle hostname properly
                import ssl
                context = ssl.create_default_context()
                # Allow self-signed certificates for testing
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                smtp = smtplib.SMTP_SSL(host, port, timeout=timeout, context=context)
            else:
                smtp = smtplib.SMTP(timeout=timeout)
                smtp.connect(host, port)
        except Exception as conn_error:
            return {
                'success': False, 
                'message': f'SMTP connection failed: {str(conn_error)}',
                'details': f'Server: {server_type}, Encryption: {encryption}'
            }
        
        # Start TLS if required
        if encryption == 'starttls':
            try:
                # For STARTTLS, we need to handle it differently
                # Close the current connection and reconnect with proper TLS handling
                smtp.quit()
                
                # Reconnect and do the full STARTTLS sequence
                smtp = smtplib.SMTP(host, port, timeout=timeout)
                smtp.ehlo()
                
                # Try STARTTLS without SSL context first (most compatible)
                try:
                    smtp.starttls()
                    smtp.ehlo()  # EHLO again after STARTTLS
                except Exception:
                    # If that fails, try with disabled SSL verification
                    import ssl
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    smtp.starttls(context=context)
                    smtp.ehlo()  # EHLO again after STARTTLS
                    
            except Exception as tls_error:
                try:
                    smtp.quit()
                except:
                    pass
                return {
                    'success': False, 
                    'message': f'SMTP STARTTLS connection failed: {str(tls_error)}',
                    'details': f'Server: {server_type}, Encryption: {encryption}'
                }
        
        # Test authentication
        try:
            smtp.login(username, password)
            auth_success = True
        except Exception as auth_error:
            smtp.quit()
            return {
                'success': False, 
                'message': f'SMTP authentication failed: {str(auth_error)}',
                'details': f'Server: {server_type}, Encryption: {encryption}'
            }
        
        # Test email sending capability if test recipient is provided
        if auth_success and test_recipient:
            try:
                # Create a simple test message
                msg = MIMEMultipart()
                msg['From'] = username
                msg['To'] = test_recipient
                msg['Subject'] = 'EnableDRM SMTP Connection Test'
                
                body = f"""This is a connection test message from EnableDRM.

Server: {host}:{port}
Server Type: {server_type}
Encryption: {encryption}
Test performed successfully!

This message confirms that the SMTP server is functioning correctly."""
                
                msg.attach(MIMEText(body, 'plain'))
                
                # Send the test email
                smtp.send_message(msg)
                smtp.quit()
                
                return {
                    'success': True, 
                    'message': f'SMTP connection successful! Test email sent to {test_recipient}',
                    'details': f'Server: {server_type}, Encryption: {encryption}, Auth: Success'
                }
                
            except Exception as send_error:
                smtp.quit()
                return {
                    'success': True,  # Connection works, just sending failed
                    'message': f'SMTP connection successful but test email failed: {str(send_error)}',
                    'details': f'Server: {server_type}, Encryption: {encryption}, Auth: Success'
                }
        
        smtp.quit()
        
        # Basic connection successful
        return {
            'success': True, 
            'message': f'SMTP connection successful to {host}:{port} with authentication',
            'details': f'Server: {server_type}, Encryption: {encryption}'
        }
        
    except Exception as e:
        error_msg = str(e).lower()
        if 'timeout' in error_msg:
            return {'success': False, 'message': f'SMTP connection timeout to {host}:{port} - server may be unreachable'}
        elif 'connection refused' in error_msg:
            return {'success': False, 'message': f'SMTP connection refused by {host}:{port} - check if SMTP service is running'}
        elif 'name resolution' in error_msg or 'resolve' in error_msg:
            return {'success': False, 'message': f'Cannot resolve hostname: {host}'}
        else:
            return {'success': False, 'message': f'SMTP connection failed: {str(e)}'}


def test_smtp_health_only(host: str, port: int, credentials: Dict[str, Any], config: Dict[str, Any] = None, timeout: int = 10) -> Dict[str, Any]:
    """
    Test SMTP connectivity for health monitoring - CONNECTIVITY ONLY, NO EMAILS SENT.
    This function only tests connection and authentication, never sends actual emails.
    
    Args:
        host: SMTP server hostname or IP
        port: SMTP server port
        credentials: Decrypted credentials dictionary
        config: SMTP configuration (encryption, server_type, etc.)
        timeout: Connection timeout in seconds
        
    Returns:
        dict: Test result with success status and message
    """
    import logging
    import smtplib
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔍 HEALTH-ONLY SMTP TEST CALLED: {host}:{port} - NO EMAILS WILL BE SENT")
    
    if not host:
        return {'success': False, 'message': 'No host provided'}
    
    username = credentials.get('username', '')
    password = credentials.get('password', '')
    
    if not username or not password:
        return {'success': False, 'message': 'Username and password are required for SMTP authentication'}
    
    # Get configuration - IGNORE test_recipient completely
    encryption = config.get('encryption', 'starttls') if config else 'starttls'
    server_type = config.get('server_type', 'smtp') if config else 'smtp'
    
    # EXPLICITLY IGNORE test_recipient - this function NEVER sends emails
    if config and 'test_recipient' in config:
        logger.warning(f"🚫 IGNORING test_recipient in health check: {config.get('test_recipient')}")
    
    logger.info(f"🔍 Health check config: encryption={encryption}, server_type={server_type}")
    
    try:
        # Establish connection based on encryption type
        try:
            if encryption == 'ssl':
                # For SSL connections, we need to handle hostname properly
                import ssl
                context = ssl.create_default_context()
                # Allow self-signed certificates for testing
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                smtp = smtplib.SMTP_SSL(host, port, timeout=timeout, context=context)
            else:
                smtp = smtplib.SMTP(timeout=timeout)
                smtp.connect(host, port)
        except Exception as conn_error:
            return {
                'success': False, 
                'message': f'SMTP connection failed: {str(conn_error)}',
                'details': f'Server: {server_type}, Encryption: {encryption}'
            }
        
        # Start TLS if required
        if encryption == 'starttls':
            try:
                # For STARTTLS, we need to handle it differently
                # Close the current connection and reconnect with proper TLS handling
                smtp.quit()
                
                # Reconnect and do the full STARTTLS sequence
                smtp = smtplib.SMTP(host, port, timeout=timeout)
                smtp.ehlo()
                
                # Try STARTTLS without SSL context first (most compatible)
                try:
                    smtp.starttls()
                    smtp.ehlo()  # EHLO again after STARTTLS
                except Exception:
                    # If that fails, try with disabled SSL verification
                    import ssl
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    smtp.starttls(context=context)
                    smtp.ehlo()  # EHLO again after STARTTLS
                    
            except Exception as tls_error:
                try:
                    smtp.quit()
                except:
                    pass
                return {
                    'success': False, 
                    'message': f'SMTP STARTTLS connection failed: {str(tls_error)}',
                    'details': f'Server: {server_type}, Encryption: {encryption}'
                }
        
        # Test authentication ONLY - NO EMAIL SENDING
        try:
            smtp.login(username, password)
            smtp.quit()
            
            # Health check successful - connection and auth work
            logger.info(f"✅ SMTP HEALTH CHECK COMPLETED - NO EMAILS SENT: {host}:{port}")
            return {
                'success': True, 
                'message': f'SMTP health check successful - connectivity and authentication verified (NO EMAILS SENT)',
                'details': f'Server: {server_type}, Encryption: {encryption}, Host: {host}:{port}'
            }
            
        except Exception as auth_error:
            smtp.quit()
            return {
                'success': False, 
                'message': f'SMTP authentication failed: {str(auth_error)}',
                'details': f'Server: {server_type}, Encryption: {encryption}'
            }
        
    except Exception as e:
        error_msg = str(e).lower()
        if 'timeout' in error_msg:
            return {'success': False, 'message': f'SMTP health check timeout to {host}:{port} - server may be unreachable'}
        elif 'connection refused' in error_msg:
            return {'success': False, 'message': f'SMTP connection refused by {host}:{port} - check if SMTP service is running'}
        elif 'name resolution' in error_msg or 'resolve' in error_msg:
            return {'success': False, 'message': f'Cannot resolve hostname: {host}'}
        else:
            return {'success': False, 'message': f'SMTP health check failed: {str(e)}'}


def test_snmp_connection(host: str, port: int, credentials: Dict[str, Any], config: Dict[str, Any] = None, timeout: int = 10) -> Dict[str, Any]:
    """
    Test SNMP connection with proper SNMP operations.
    
    Args:
        host: SNMP agent hostname or IP
        port: SNMP port (usually 161)
        credentials: Decrypted credentials dictionary
        config: SNMP configuration (version, community, retries, etc.)
        timeout: Connection timeout in seconds
        
    Returns:
        dict: Test result with success status and message
    """
    try:
        from pysnmp.hlapi import (
            getCmd, SnmpEngine, CommunityData, UdpTransportTarget, 
            ContextData, ObjectType, ObjectIdentity
        )
        
        config = config or {}
        # Community string can come from config or credentials (password field)
        community = config.get('community') or credentials.get('password', 'public')
        version = config.get('version', '2c')  # SNMP version: 1, 2c, 3
        retries = config.get('retries', 3)
        
        # Map SNMP version strings to pysnmp constants
        version_map = {
            '1': 0,   # SNMPv1
            '2c': 1,  # SNMPv2c
            '3': 3    # SNMPv3 (not implemented in this basic version)
        }
        
        snmp_version = version_map.get(version, 1)  # Default to v2c
        
        # Handle SNMPv3 with user-based security
        if version == '3':
            return test_snmpv3_connection(host, port, credentials, config, timeout)
        
        # System description OID (1.3.6.1.2.1.1.1.0)
        system_desc_oid = '1.3.6.1.2.1.1.1.0'
        
        try:
            # Perform SNMP GET operation
            iterator = getCmd(
                SnmpEngine(),
                CommunityData(community, mpModel=snmp_version),
                UdpTransportTarget((host, port), timeout=timeout, retries=retries),
                ContextData(),
                ObjectType(ObjectIdentity(system_desc_oid))
            )
            
            errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
            
            if errorIndication:
                error_msg = str(errorIndication)
                if 'timeout' in error_msg.lower():
                    return {
                        'success': False, 
                        'message': f'SNMP timeout to {host}:{port} - agent may be unreachable or community string incorrect'
                    }
                else:
                    return {
                        'success': False, 
                        'message': f'SNMP error: {errorIndication}'
                    }
            elif errorStatus:
                return {
                    'success': False, 
                    'message': f'SNMP error: {errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1][0] or "?"}'
                }
            else:
                # Success - extract system description
                system_desc = str(varBinds[0][1]) if varBinds else 'Unknown'
                
                # Truncate long descriptions
                if len(system_desc) > 100:
                    system_desc = system_desc[:97] + '...'
                
                return {
                    'success': True,
                    'message': f'SNMP connection successful to {host}:{port}',
                    'details': f'Version: SNMPv{version}, Community: {community}, System: {system_desc}'
                }
                
        except Exception as snmp_error:
            error_msg = str(snmp_error).lower()
            if 'timeout' in error_msg:
                return {
                    'success': False, 
                    'message': f'SNMP timeout to {host}:{port} - check if SNMP agent is running and community string is correct'
                }
            elif 'connection refused' in error_msg:
                return {
                    'success': False, 
                    'message': f'SNMP connection refused by {host}:{port} - SNMP agent may not be running'
                }
            elif 'no route to host' in error_msg:
                return {
                    'success': False, 
                    'message': f'No route to SNMP host {host} - check network connectivity'
                }
            else:
                return {
                    'success': False, 
                    'message': f'SNMP operation failed: {str(snmp_error)}'
                }
            
    except ImportError:
        return {
            'success': False, 
            'message': 'pysnmp library not installed - cannot test SNMP connections. Install with: pip install pysnmp'
        }
    except Exception as e:
        return {
            'success': False, 
            'message': f'SNMP connection test failed: {str(e)}'
        }


def test_snmpv3_connection(host: str, port: int, credentials: Dict[str, Any], config: Dict[str, Any] = None, timeout: int = 10) -> Dict[str, Any]:
    """
    Test SNMPv3 connection with user-based security.
    
    Args:
        host: SNMP agent hostname or IP
        port: SNMP port (usually 161)
        credentials: Decrypted credentials dictionary
        config: SNMPv3 configuration (security level, auth/privacy protocols, etc.)
        timeout: Connection timeout in seconds
        
    Returns:
        dict: Test result with success status and message
    """
    try:
        from pysnmp.hlapi import (
            getCmd, SnmpEngine, UsmUserData, UdpTransportTarget, 
            ContextData, ObjectType, ObjectIdentity,
            usmHMACMD5AuthProtocol, usmHMACSHAAuthProtocol,
            usmDESPrivProtocol, usmAesCfb128Protocol
        )
        
        config = config or {}
        username = credentials.get('username')
        
        if not username:
            return {
                'success': False,
                'message': 'SNMPv3 requires a username'
            }
        
        # SNMPv3 Security Configuration
        security_level = config.get('security_level', 'authPriv')  # noAuthNoPriv, authNoPriv, authPriv
        auth_protocol = config.get('auth_protocol', 'usmHMACMD5AuthProtocol')  # MD5, SHA
        auth_key = credentials.get('password')  # Authentication key
        privacy_protocol = config.get('privacy_protocol', 'usmDESPrivProtocol')  # DES, AES
        privacy_key = credentials.get('ssh_key')  # Privacy key
        retries = config.get('retries', 3)
        
        # Map security levels
        if security_level == 'noAuthNoPriv':
            # No authentication, no privacy
            user_data = UsmUserData(username)
        elif security_level == 'authNoPriv':
            # Authentication only, no privacy
            if not auth_key:
                return {
                    'success': False,
                    'message': 'SNMPv3 authNoPriv requires authentication key (password)'
                }
            
            # Map auth protocol
            auth_proto_map = {
                'MD5': usmHMACMD5AuthProtocol,
                'SHA': usmHMACSHAAuthProtocol,
                'usmHMACMD5AuthProtocol': usmHMACMD5AuthProtocol,
                'usmHMACSHAAuthProtocol': usmHMACSHAAuthProtocol
            }
            auth_proto = auth_proto_map.get(auth_protocol, usmHMACMD5AuthProtocol)
            
            user_data = UsmUserData(username, auth_key, authProtocol=auth_proto)
        elif security_level == 'authPriv':
            # Authentication and privacy
            if not auth_key:
                return {
                    'success': False,
                    'message': 'SNMPv3 authPriv requires authentication key (password)'
                }
            if not privacy_key:
                return {
                    'success': False,
                    'message': 'SNMPv3 authPriv requires privacy key (ssh_key field)'
                }
            
            # Map protocols
            auth_proto_map = {
                'MD5': usmHMACMD5AuthProtocol,
                'SHA': usmHMACSHAAuthProtocol,
                'usmHMACMD5AuthProtocol': usmHMACMD5AuthProtocol,
                'usmHMACSHAAuthProtocol': usmHMACSHAAuthProtocol
            }
            priv_proto_map = {
                'DES': usmDESPrivProtocol,
                'AES': usmAesCfb128Protocol,
                'usmDESPrivProtocol': usmDESPrivProtocol,
                'usmAesCfb128Protocol': usmAesCfb128Protocol
            }
            
            auth_proto = auth_proto_map.get(auth_protocol, usmHMACMD5AuthProtocol)
            priv_proto = priv_proto_map.get(privacy_protocol, usmDESPrivProtocol)
            
            user_data = UsmUserData(
                username, 
                auth_key, 
                privacy_key,
                authProtocol=auth_proto,
                privProtocol=priv_proto
            )
        else:
            return {
                'success': False,
                'message': f'Invalid SNMPv3 security level: {security_level}. Use noAuthNoPriv, authNoPriv, or authPriv'
            }
        
        # System description OID
        system_desc_oid = '1.3.6.1.2.1.1.1.0'
        
        try:
            # Perform SNMPv3 GET operation
            iterator = getCmd(
                SnmpEngine(),
                user_data,
                UdpTransportTarget((host, port), timeout=timeout, retries=retries),
                ContextData(),
                ObjectType(ObjectIdentity(system_desc_oid))
            )
            
            errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
            
            if errorIndication:
                error_msg = str(errorIndication)
                if 'timeout' in error_msg.lower():
                    return {
                        'success': False, 
                        'message': f'SNMPv3 timeout to {host}:{port} - agent may be unreachable or credentials incorrect'
                    }
                elif 'unknownUserName' in error_msg:
                    return {
                        'success': False,
                        'message': f'SNMPv3 authentication failed - unknown username: {username}'
                    }
                elif 'wrongDigest' in error_msg or 'authenticationFailure' in error_msg:
                    return {
                        'success': False,
                        'message': 'SNMPv3 authentication failed - check authentication key'
                    }
                elif 'decryptionError' in error_msg:
                    return {
                        'success': False,
                        'message': 'SNMPv3 decryption failed - check privacy key'
                    }
                else:
                    return {
                        'success': False, 
                        'message': f'SNMPv3 error: {errorIndication}'
                    }
            elif errorStatus:
                return {
                    'success': False, 
                    'message': f'SNMPv3 error: {errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1][0] or "?"}'
                }
            else:
                # Success - extract system description
                system_desc = str(varBinds[0][1]) if varBinds else 'Unknown'
                
                # Truncate long descriptions
                if len(system_desc) > 100:
                    system_desc = system_desc[:97] + '...'
                
                return {
                    'success': True,
                    'message': f'SNMPv3 connection successful to {host}:{port}',
                    'details': f'User: {username}, Security: {security_level}, System: {system_desc}'
                }
                
        except Exception as snmp_error:
            error_msg = str(snmp_error).lower()
            if 'timeout' in error_msg:
                return {
                    'success': False, 
                    'message': f'SNMPv3 timeout to {host}:{port} - check if SNMP agent supports v3 and credentials are correct'
                }
            elif 'authentication' in error_msg:
                return {
                    'success': False, 
                    'message': 'SNMPv3 authentication failed - check username and authentication key'
                }
            elif 'privacy' in error_msg or 'decrypt' in error_msg:
                return {
                    'success': False, 
                    'message': 'SNMPv3 privacy/decryption failed - check privacy key and protocol'
                }
            else:
                return {
                    'success': False, 
                    'message': f'SNMPv3 operation failed: {str(snmp_error)}'
                }
            
    except ImportError:
        return {
            'success': False, 
            'message': 'pysnmp library not installed - cannot test SNMPv3 connections. Install with: pip install pysnmp'
        }
    except Exception as e:
        return {
            'success': False, 
            'message': f'SNMPv3 connection test failed: {str(e)}'
        }


def test_telnet_connection(host: str, port: int, credentials: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
    """Test Telnet connectivity."""
    try:
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            return {
                'success': True, 
                'message': f'Telnet connection successful to {host}:{port}',
                'details': f'Username: {credentials.get("username", "N/A")}'
            }
        else:
            return {'success': False, 'message': f'Telnet connection failed to {host}:{port}'}
            
    except Exception as e:
        return {'success': False, 'message': f'Telnet connection test failed: {str(e)}'}


def test_rest_api_connection(host: str, port: int, credentials: Dict[str, Any], config: Dict[str, Any] = None, timeout: int = 30) -> Dict[str, Any]:
    """Test REST API connectivity."""
    try:
        import requests
        
        config = config or {}
        protocol = config.get('protocol', 'http')
        base_path = config.get('base_path', '/')
        verify_ssl = config.get('verify_ssl', True)
        
        url = f"{protocol}://{host}:{port}{base_path}"
        
        # Simple GET request to check if API is responding
        response = requests.get(url, timeout=timeout, verify=verify_ssl)
        
        if response.status_code < 500:  # Any response under 500 means the API is responding
            return {
                'success': True, 
                'message': f'REST API responding at {url} (status: {response.status_code})',
                'details': f'Protocol: {protocol.upper()}, SSL Verify: {verify_ssl}'
            }
        else:
            return {'success': False, 'message': f'REST API error at {url} (status: {response.status_code})'}
            
    except Exception as e:
        return {'success': False, 'message': f'REST API connection test failed: {str(e)}'}


# ============================================================================
# DATABASE CONNECTION TEST FUNCTIONS
# ============================================================================

def test_mysql_connection(host: str, port: int, credentials: Dict[str, Any], config: Dict[str, Any] = None, timeout: int = 10) -> Dict[str, Any]:
    """
    Test MySQL/MariaDB connection.
    
    Args:
        host: MySQL server hostname or IP
        port: MySQL port (usually 3306)
        credentials: Decrypted credentials dictionary
        config: MySQL configuration (database, charset, ssl_mode, etc.)
        timeout: Connection timeout in seconds
        
    Returns:
        dict: Test result with success status and message
    """
    try:
        import pymysql
        
        username = credentials.get('username')
        password = credentials.get('password')
        
        if not username or not password:
            return {'success': False, 'message': 'MySQL requires username and password'}
        
        config = config or {}
        database = config.get('database', '')
        charset = config.get('charset', 'utf8mb4')
        ssl_mode = config.get('ssl_mode', 'disabled')
        
        # SSL configuration
        ssl_config = None
        if ssl_mode != 'disabled':
            ssl_config = {
                'ssl_disabled': ssl_mode == 'disabled',
                'ssl_verify_cert': ssl_mode == 'required',
                'ssl_verify_identity': ssl_mode == 'verify_identity'
            }
        
        try:
            connection = pymysql.connect(
                host=host,
                port=port,
                user=username,
                password=password,
                database=database,
                charset=charset,
                connect_timeout=timeout,
                ssl=ssl_config,
                autocommit=True
            )
            
            # Test query execution
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION() as version, DATABASE() as current_db, USER() as current_user")
                result = cursor.fetchone()
                
                version = result[0] if result else 'Unknown'
                current_db = result[1] if result and result[1] else 'None'
                current_user = result[2] if result else 'Unknown'
            
            connection.close()
            
            return {
                'success': True,
                'message': f'MySQL connection successful to {host}:{port}',
                'details': f'Version: {version}, Database: {current_db}, User: {current_user}, SSL: {ssl_mode}'
            }
            
        except pymysql.Error as e:
            error_code = e.args[0] if e.args else 0
            error_msg = e.args[1] if len(e.args) > 1 else str(e)
            
            if error_code == 1045:
                return {'success': False, 'message': 'MySQL authentication failed - check username/password'}
            elif error_code == 1049:
                return {'success': False, 'message': f'MySQL database "{database}" does not exist'}
            elif error_code == 2003:
                return {'success': False, 'message': f'MySQL server not reachable at {host}:{port}'}
            elif error_code == 2013:
                return {'success': False, 'message': 'MySQL connection lost during query'}
            else:
                return {'success': False, 'message': f'MySQL error ({error_code}): {error_msg}'}
                
    except ImportError:
        return {'success': False, 'message': 'PyMySQL library not installed - cannot test MySQL connections'}
    except Exception as e:
        return {'success': False, 'message': f'MySQL connection test failed: {str(e)}'}


def test_postgresql_connection(host: str, port: int, credentials: Dict[str, Any], config: Dict[str, Any] = None, timeout: int = 10) -> Dict[str, Any]:
    """
    Test PostgreSQL connection.
    
    Args:
        host: PostgreSQL server hostname or IP
        port: PostgreSQL port (usually 5432)
        credentials: Decrypted credentials dictionary
        config: PostgreSQL configuration (database, ssl_mode, etc.)
        timeout: Connection timeout in seconds
        
    Returns:
        dict: Test result with success status and message
    """
    try:
        import psycopg2
        from psycopg2 import sql
        
        username = credentials.get('username')
        password = credentials.get('password')
        
        if not username or not password:
            return {'success': False, 'message': 'PostgreSQL requires username and password'}
        
        config = config or {}
        database = config.get('database', 'postgres')
        ssl_mode = config.get('ssl_mode', 'prefer')
        
        try:
            connection = psycopg2.connect(
                host=host,
                port=port,
                user=username,
                password=password,
                database=database,
                sslmode=ssl_mode,
                connect_timeout=timeout
            )
            
            # Test query execution
            with connection.cursor() as cursor:
                cursor.execute("SELECT version(), current_database(), current_user")
                result = cursor.fetchone()
                
                version = result[0].split(' ')[1] if result else 'Unknown'
                current_db = result[1] if result else 'Unknown'
                current_user = result[2] if result else 'Unknown'
            
            connection.close()
            
            return {
                'success': True,
                'message': f'PostgreSQL connection successful to {host}:{port}',
                'details': f'Version: {version}, Database: {current_db}, User: {current_user}, SSL: {ssl_mode}'
            }
            
        except psycopg2.OperationalError as e:
            error_msg = str(e).lower()
            if 'authentication failed' in error_msg:
                return {'success': False, 'message': 'PostgreSQL authentication failed - check username/password'}
            elif 'database' in error_msg and 'does not exist' in error_msg:
                return {'success': False, 'message': f'PostgreSQL database "{database}" does not exist'}
            elif 'connection refused' in error_msg:
                return {'success': False, 'message': f'PostgreSQL server not reachable at {host}:{port}'}
            elif 'timeout' in error_msg:
                return {'success': False, 'message': f'PostgreSQL connection timeout to {host}:{port}'}
            else:
                return {'success': False, 'message': f'PostgreSQL connection error: {str(e)}'}
                
    except ImportError:
        return {'success': False, 'message': 'psycopg2 library not available - cannot test PostgreSQL connections'}
    except Exception as e:
        return {'success': False, 'message': f'PostgreSQL connection test failed: {str(e)}'}


def test_mssql_connection(host: str, port: int, credentials: Dict[str, Any], config: Dict[str, Any] = None, timeout: int = 10) -> Dict[str, Any]:
    """
    Test Microsoft SQL Server connection.
    
    Args:
        host: SQL Server hostname or IP
        port: SQL Server port (usually 1433)
        credentials: Decrypted credentials dictionary
        config: SQL Server configuration (database, driver, etc.)
        timeout: Connection timeout in seconds
        
    Returns:
        dict: Test result with success status and message
    """
    try:
        import pyodbc
        
        username = credentials.get('username')
        password = credentials.get('password')
        
        if not username or not password:
            return {'success': False, 'message': 'SQL Server requires username and password'}
        
        config = config or {}
        database = config.get('database', 'master')
        driver = config.get('driver', 'ODBC Driver 17 for SQL Server')
        encrypt = config.get('encrypt', 'yes')
        trust_cert = config.get('trust_server_certificate', 'no')
        
        try:
            connection_string = (
                f"DRIVER={{{driver}}};"
                f"SERVER={host},{port};"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={password};"
                f"Encrypt={encrypt};"
                f"TrustServerCertificate={trust_cert};"
                f"Connection Timeout={timeout};"
            )
            
            connection = pyodbc.connect(connection_string)
            
            # Test query execution
            cursor = connection.cursor()
            cursor.execute("SELECT @@VERSION as version, DB_NAME() as current_db, SYSTEM_USER as current_user")
            result = cursor.fetchone()
            
            version = result[0].split('\n')[0] if result else 'Unknown'
            current_db = result[1] if result else 'Unknown'
            current_user = result[2] if result else 'Unknown'
            
            cursor.close()
            connection.close()
            
            return {
                'success': True,
                'message': f'SQL Server connection successful to {host}:{port}',
                'details': f'Version: {version}, Database: {current_db}, User: {current_user}'
            }
            
        except pyodbc.Error as e:
            error_msg = str(e).lower()
            if 'login failed' in error_msg:
                return {'success': False, 'message': 'SQL Server authentication failed - check username/password'}
            elif 'cannot open database' in error_msg:
                return {'success': False, 'message': f'SQL Server database "{database}" cannot be accessed'}
            elif 'network-related' in error_msg or 'transport-level' in error_msg:
                return {'success': False, 'message': f'SQL Server not reachable at {host}:{port}'}
            elif 'timeout' in error_msg:
                return {'success': False, 'message': f'SQL Server connection timeout to {host}:{port}'}
            else:
                return {'success': False, 'message': f'SQL Server error: {str(e)}'}
                
    except ImportError:
        return {'success': False, 'message': 'pyodbc library not installed - cannot test SQL Server connections'}
    except Exception as e:
        return {'success': False, 'message': f'SQL Server connection test failed: {str(e)}'}


def test_oracle_connection(host: str, port: int, credentials: Dict[str, Any], config: Dict[str, Any] = None, timeout: int = 10) -> Dict[str, Any]:
    """
    Test Oracle Database connection.
    
    Args:
        host: Oracle server hostname or IP
        port: Oracle port (usually 1521)
        credentials: Decrypted credentials dictionary
        config: Oracle configuration (service_name, sid, etc.)
        timeout: Connection timeout in seconds
        
    Returns:
        dict: Test result with success status and message
    """
    try:
        import cx_Oracle
        
        username = credentials.get('username')
        password = credentials.get('password')
        
        if not username or not password:
            return {'success': False, 'message': 'Oracle requires username and password'}
        
        config = config or {}
        service_name = config.get('service_name', '')
        sid = config.get('sid', '')
        
        # Build connection string
        if service_name:
            dsn = f"{host}:{port}/{service_name}"
        elif sid:
            dsn = f"{host}:{port}/{sid}"
        else:
            dsn = f"{host}:{port}"
        
        try:
            connection = cx_Oracle.connect(
                user=username,
                password=password,
                dsn=dsn,
                timeout=timeout
            )
            
            # Test query execution
            cursor = connection.cursor()
            cursor.execute("SELECT banner FROM v$version WHERE ROWNUM = 1")
            version_result = cursor.fetchone()
            
            cursor.execute("SELECT sys_context('USERENV', 'DB_NAME') FROM dual")
            db_result = cursor.fetchone()
            
            cursor.execute("SELECT USER FROM dual")
            user_result = cursor.fetchone()
            
            version = version_result[0] if version_result else 'Unknown'
            current_db = db_result[0] if db_result else 'Unknown'
            current_user = user_result[0] if user_result else 'Unknown'
            
            cursor.close()
            connection.close()
            
            return {
                'success': True,
                'message': f'Oracle connection successful to {host}:{port}',
                'details': f'Version: {version}, Database: {current_db}, User: {current_user}'
            }
            
        except cx_Oracle.Error as e:
            error_obj, = e.args
            error_msg = error_obj.message.lower()
            
            if 'invalid username/password' in error_msg:
                return {'success': False, 'message': 'Oracle authentication failed - check username/password'}
            elif 'listener does not currently know of service' in error_msg:
                return {'success': False, 'message': f'Oracle service/SID not found - check service_name or sid'}
            elif 'no listener' in error_msg:
                return {'success': False, 'message': f'Oracle listener not running at {host}:{port}'}
            elif 'timeout' in error_msg:
                return {'success': False, 'message': f'Oracle connection timeout to {host}:{port}'}
            else:
                return {'success': False, 'message': f'Oracle error: {error_obj.message}'}
                
    except ImportError:
        return {'success': False, 'message': 'cx_Oracle library not installed - cannot test Oracle connections'}
    except Exception as e:
        return {'success': False, 'message': f'Oracle connection test failed: {str(e)}'}


def test_sqlite_connection(host: str, port: int, credentials: Dict[str, Any], config: Dict[str, Any] = None, timeout: int = 10) -> Dict[str, Any]:
    """
    Test SQLite database connection.
    
    Args:
        host: File path to SQLite database (host parameter repurposed)
        port: Not used for SQLite (kept for interface consistency)
        credentials: Not used for SQLite (kept for interface consistency)
        config: SQLite configuration
        timeout: Connection timeout in seconds
        
    Returns:
        dict: Test result with success status and message
    """
    try:
        import sqlite3
        import os
        
        config = config or {}
        db_path = config.get('database_path', host)  # Use host as path if not in config
        
        if not db_path:
            return {'success': False, 'message': 'SQLite database path is required'}
        
        # Check if file exists
        if not os.path.exists(db_path):
            return {'success': False, 'message': f'SQLite database file not found: {db_path}'}
        
        try:
            connection = sqlite3.connect(db_path, timeout=timeout)
            
            # Test query execution
            cursor = connection.cursor()
            cursor.execute("SELECT sqlite_version()")
            version_result = cursor.fetchone()
            
            cursor.execute("PRAGMA database_list")
            db_info = cursor.fetchall()
            
            version = version_result[0] if version_result else 'Unknown'
            db_name = os.path.basename(db_path)
            
            cursor.close()
            connection.close()
            
            return {
                'success': True,
                'message': f'SQLite connection successful to {db_path}',
                'details': f'Version: {version}, Database: {db_name}, Tables: {len(db_info)}'
            }
            
        except sqlite3.Error as e:
            return {'success': False, 'message': f'SQLite error: {str(e)}'}
            
    except Exception as e:
        return {'success': False, 'message': f'SQLite connection test failed: {str(e)}'}


def test_mongodb_connection(host: str, port: int, credentials: Dict[str, Any], config: Dict[str, Any] = None, timeout: int = 10) -> Dict[str, Any]:
    """
    Test MongoDB connection.
    
    Args:
        host: MongoDB server hostname or IP
        port: MongoDB port (usually 27017)
        credentials: Decrypted credentials dictionary
        config: MongoDB configuration (database, auth_source, etc.)
        timeout: Connection timeout in seconds
        
    Returns:
        dict: Test result with success status and message
    """
    try:
        import pymongo
        from pymongo import MongoClient
        
        config = config or {}
        database = config.get('database', 'admin')
        auth_source = config.get('auth_source', 'admin')
        
        username = credentials.get('username')
        password = credentials.get('password')
        
        # Build connection URI
        if username and password:
            uri = f"mongodb://{username}:{password}@{host}:{port}/{database}?authSource={auth_source}"
        else:
            uri = f"mongodb://{host}:{port}/{database}"
        
        try:
            client = MongoClient(
                uri,
                serverSelectionTimeoutMS=timeout * 1000,
                connectTimeoutMS=timeout * 1000
            )
            
            # Test connection
            server_info = client.server_info()
            version = server_info.get('version', 'Unknown')
            
            # Test database access
            db = client[database]
            collections = db.list_collection_names()
            
            client.close()
            
            return {
                'success': True,
                'message': f'MongoDB connection successful to {host}:{port}',
                'details': f'Version: {version}, Database: {database}, Collections: {len(collections)}'
            }
            
        except pymongo.errors.ServerSelectionTimeoutError:
            return {'success': False, 'message': f'MongoDB server not reachable at {host}:{port}'}
        except pymongo.errors.OperationFailure as e:
            if 'Authentication failed' in str(e):
                return {'success': False, 'message': 'MongoDB authentication failed - check username/password'}
            else:
                return {'success': False, 'message': f'MongoDB operation failed: {str(e)}'}
        except pymongo.errors.ConnectionFailure:
            return {'success': False, 'message': f'MongoDB connection failed to {host}:{port}'}
            
    except ImportError:
        return {'success': False, 'message': 'pymongo library not installed - cannot test MongoDB connections'}
    except Exception as e:
        return {'success': False, 'message': f'MongoDB connection test failed: {str(e)}'}


def test_redis_connection(host: str, port: int, credentials: Dict[str, Any], config: Dict[str, Any] = None, timeout: int = 10) -> Dict[str, Any]:
    """
    Test Redis connection.
    
    Args:
        host: Redis server hostname or IP
        port: Redis port (usually 6379)
        credentials: Decrypted credentials dictionary
        config: Redis configuration (database, ssl, etc.)
        timeout: Connection timeout in seconds
        
    Returns:
        dict: Test result with success status and message
    """
    try:
        import redis
        
        config = config or {}
        database = config.get('database', 0)
        ssl_enabled = config.get('ssl', False)
        
        password = credentials.get('password')
        
        try:
            client = redis.Redis(
                host=host,
                port=port,
                password=password,
                db=database,
                ssl=ssl_enabled,
                socket_timeout=timeout,
                socket_connect_timeout=timeout,
                decode_responses=True
            )
            
            # Test connection
            info = client.info()
            version = info.get('redis_version', 'Unknown')
            
            # Test basic operations
            client.ping()
            
            return {
                'success': True,
                'message': f'Redis connection successful to {host}:{port}',
                'details': f'Version: {version}, Database: {database}, SSL: {ssl_enabled}'
            }
            
        except redis.AuthenticationError:
            return {'success': False, 'message': 'Redis authentication failed - check password'}
        except redis.ConnectionError:
            return {'success': False, 'message': f'Redis server not reachable at {host}:{port}'}
        except redis.TimeoutError:
            return {'success': False, 'message': f'Redis connection timeout to {host}:{port}'}
        except redis.ResponseError as e:
            return {'success': False, 'message': f'Redis error: {str(e)}'}
            
    except ImportError:
        return {'success': False, 'message': 'redis library not available - cannot test Redis connections'}
    except Exception as e:
        return {'success': False, 'message': f'Redis connection test failed: {str(e)}'}


def test_elasticsearch_connection(host: str, port: int, credentials: Dict[str, Any], config: Dict[str, Any] = None, timeout: int = 10) -> Dict[str, Any]:
    """
    Test Elasticsearch connection.
    
    Args:
        host: Elasticsearch server hostname or IP
        port: Elasticsearch port (usually 9200)
        credentials: Decrypted credentials dictionary
        config: Elasticsearch configuration (ssl, verify_certs, etc.)
        timeout: Connection timeout in seconds
        
    Returns:
        dict: Test result with success status and message
    """
    try:
        from elasticsearch import Elasticsearch
        
        config = config or {}
        use_ssl = config.get('ssl', False)
        verify_certs = config.get('verify_certs', True)
        
        username = credentials.get('username')
        password = credentials.get('password')
        
        # Build connection parameters
        scheme = 'https' if use_ssl else 'http'
        hosts = [f"{scheme}://{host}:{port}"]
        
        es_config = {
            'hosts': hosts,
            'timeout': timeout,
            'verify_certs': verify_certs
        }
        
        if username and password:
            es_config['http_auth'] = (username, password)
        
        try:
            es = Elasticsearch(**es_config)
            
            # Test connection
            info = es.info()
            version = info['version']['number']
            cluster_name = info['cluster_name']
            
            # Test cluster health
            health = es.cluster.health()
            status = health['status']
            
            return {
                'success': True,
                'message': f'Elasticsearch connection successful to {host}:{port}',
                'details': f'Version: {version}, Cluster: {cluster_name}, Status: {status}, SSL: {use_ssl}'
            }
            
        except Exception as e:
            error_msg = str(e).lower()
            if 'unauthorized' in error_msg or 'authentication' in error_msg:
                return {'success': False, 'message': 'Elasticsearch authentication failed - check username/password'}
            elif 'connection' in error_msg and 'refused' in error_msg:
                return {'success': False, 'message': f'Elasticsearch server not reachable at {host}:{port}'}
            elif 'timeout' in error_msg:
                return {'success': False, 'message': f'Elasticsearch connection timeout to {host}:{port}'}
            else:
                return {'success': False, 'message': f'Elasticsearch error: {str(e)}'}
                
    except ImportError:
        return {'success': False, 'message': 'elasticsearch library not installed - cannot test Elasticsearch connections'}
    except Exception as e:
        return {'success': False, 'message': f'Elasticsearch connection test failed: {str(e)}'}


def perform_connection_test(target, method, credentials_data) -> Dict[str, Any]:
    """
    Perform connection test based on method type.
    
    Args:
        target: Target object
        method: Communication method object
        credentials_data: Decrypted credentials dictionary
        
    Returns:
        dict: Test result with success status and message
    """
    try:
        host = method.config.get('host')
        port = method.config.get('port')
        timeout = method.config.get('timeout', 10)
        
        if not host or not port:
            return {'success': False, 'message': 'Invalid target configuration - missing host or port'}
        
        # Debug logging
        debug_info = f"PERFORM_CONNECTION_TEST: method_type={method.method_type}, host={host}, port={port}, method_id={getattr(method, 'id', 'unknown')}"
        print(debug_info)  # This will show in docker logs
        
        # Test basic connectivity first (skip for SMTP and databases as they have their own connection logic)
        skip_basic_test = method.method_type in ['smtp', 'mysql', 'postgresql', 'mssql', 'oracle', 'sqlite', 'mongodb', 'redis', 'elasticsearch']
        if not skip_basic_test and not test_target_connectivity(host, port, timeout=5):
            return {
                'success': False, 
                'message': f'Cannot reach {host}:{port} - check network connectivity and firewall',
                'debug_info': debug_info
            }
        
        # Perform method-specific connection test
        if method.method_type == 'ssh':
            print(f"CALLING SSH TEST: {host}:{port}")
            result = test_ssh_connection(host, port, credentials_data, timeout)
            result['debug_info'] = debug_info + " -> SSH_TEST_CALLED"
            return result
        elif method.method_type == 'winrm':
            print(f"CALLING WINRM TEST: {host}:{port}")
            result = test_winrm_connection(host, port, credentials_data, timeout)
            result['debug_info'] = debug_info + " -> WINRM_TEST_CALLED"
            return result
        elif method.method_type == 'smtp':
            print(f"CALLING SMTP TEST: {host}:{port}")
            result = test_smtp_connection(host, port, credentials_data, method.config, timeout)
            result['debug_info'] = debug_info + " -> SMTP_TEST_CALLED"
            return result
        elif method.method_type == 'snmp':
            print(f"CALLING SNMP TEST: {host}:{port}")
            result = test_snmp_connection(host, port, credentials_data, method.config, timeout)
            result['debug_info'] = debug_info + " -> SNMP_TEST_CALLED"
            return result
        elif method.method_type == 'telnet':
            print(f"CALLING TELNET TEST: {host}:{port}")
            result = test_telnet_connection(host, port, credentials_data, timeout)
            result['debug_info'] = debug_info + " -> TELNET_TEST_CALLED"
            return result
        elif method.method_type == 'rest_api':
            print(f"CALLING REST_API TEST: {host}:{port}")
            result = test_rest_api_connection(host, port, credentials_data, method.config, timeout)
            result['debug_info'] = debug_info + " -> REST_API_TEST_CALLED"
            return result
        # Database connection tests
        elif method.method_type == 'mysql':
            print(f"CALLING MYSQL TEST: {host}:{port}")
            result = test_mysql_connection(host, port, credentials_data, method.config, timeout)
            result['debug_info'] = debug_info + " -> MYSQL_TEST_CALLED"
            return result
        elif method.method_type == 'postgresql':
            print(f"CALLING POSTGRESQL TEST: {host}:{port}")
            result = test_postgresql_connection(host, port, credentials_data, method.config, timeout)
            result['debug_info'] = debug_info + " -> POSTGRESQL_TEST_CALLED"
            return result
        elif method.method_type == 'mssql':
            print(f"CALLING MSSQL TEST: {host}:{port}")
            result = test_mssql_connection(host, port, credentials_data, method.config, timeout)
            result['debug_info'] = debug_info + " -> MSSQL_TEST_CALLED"
            return result
        elif method.method_type == 'oracle':
            print(f"CALLING ORACLE TEST: {host}:{port}")
            result = test_oracle_connection(host, port, credentials_data, method.config, timeout)
            result['debug_info'] = debug_info + " -> ORACLE_TEST_CALLED"
            return result
        elif method.method_type == 'sqlite':
            print(f"CALLING SQLITE TEST: {host}")
            result = test_sqlite_connection(host, port, credentials_data, method.config, timeout)
            result['debug_info'] = debug_info + " -> SQLITE_TEST_CALLED"
            return result
        elif method.method_type == 'mongodb':
            print(f"CALLING MONGODB TEST: {host}:{port}")
            result = test_mongodb_connection(host, port, credentials_data, method.config, timeout)
            result['debug_info'] = debug_info + " -> MONGODB_TEST_CALLED"
            return result
        elif method.method_type == 'redis':
            print(f"CALLING REDIS TEST: {host}:{port}")
            result = test_redis_connection(host, port, credentials_data, method.config, timeout)
            result['debug_info'] = debug_info + " -> REDIS_TEST_CALLED"
            return result
        elif method.method_type == 'elasticsearch':
            print(f"CALLING ELASTICSEARCH TEST: {host}:{port}")
            result = test_elasticsearch_connection(host, port, credentials_data, method.config, timeout)
            result['debug_info'] = debug_info + " -> ELASTICSEARCH_TEST_CALLED"
            return result
        else:
            return {
                'success': False, 
                'message': f'Connection testing not supported for {method.method_type}',
                'debug_info': debug_info + " -> UNSUPPORTED_METHOD"
            }
            
    except Exception as e:
        return {
            'success': False, 
            'message': f'Connection test failed: {str(e)}',
            'debug_info': f'EXCEPTION in perform_connection_test: {str(e)}'
        }