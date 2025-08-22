"""
Enhanced Discovery Service with event-driven architecture.
"""
import asyncio
import ipaddress
import socket
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime, timezone
import logging

from app.shared.infrastructure.container import injectable
from app.shared.infrastructure.events import event_bus
from app.domains.target_management.events.target_events_simple import TargetDiscoveredEvent
from app.shared.infrastructure.cache import cache_service, cached

logger = logging.getLogger(__name__)


@injectable()
class EnhancedDiscoveryService:
    """Enhanced network discovery service with caching and events."""
    
    def __init__(self):
        self.discovery_sessions: Dict[str, Dict[str, Any]] = {}
        self.common_ports = [
            22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 993, 995,
            1433, 1521, 3306, 3389, 5432, 5900, 8080, 8443
        ]
        self.service_signatures = {
            22: "SSH",
            23: "Telnet", 
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            135: "RPC",
            139: "NetBIOS",
            143: "IMAP",
            443: "HTTPS",
            993: "IMAPS",
            995: "POP3S",
            1433: "MSSQL",
            1521: "Oracle",
            3306: "MySQL",
            3389: "RDP",
            5432: "PostgreSQL",
            5900: "VNC",
            8080: "HTTP-Alt",
            8443: "HTTPS-Alt"
        }
    
    async def start_network_discovery(
        self,
        network_range: str,
        ports: Optional[List[int]] = None,
        discovery_id: str = None,
        discovered_by: int = 0,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start network discovery with real-time progress updates."""
        if not discovery_id:
            discovery_id = f"discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Validate network range
        try:
            network = ipaddress.ip_network(network_range, strict=False)
        except ValueError as e:
            raise ValueError(f"Invalid network range: {e}")
        
        # Initialize discovery session
        self.discovery_sessions[discovery_id] = {
            "id": discovery_id,
            "network_range": network_range,
            "status": "running",
            "progress": 0,
            "total_hosts": network.num_addresses,
            "scanned_hosts": 0,
            "discovered_targets": [],
            "started_at": datetime.now(timezone.utc),
            "discovered_by": discovered_by,
            "options": options or {}
        }
        
        # Use common ports if none specified
        scan_ports = ports or self.common_ports
        
        # Start discovery in background
        asyncio.create_task(self._perform_discovery(
            discovery_id, network, scan_ports, discovered_by
        ))
        
        return discovery_id
    
    async def get_discovery_status(self, discovery_id: str) -> Optional[Dict[str, Any]]:
        """Get discovery session status."""
        return self.discovery_sessions.get(discovery_id)
    
    async def stop_discovery(self, discovery_id: str) -> bool:
        """Stop a running discovery session."""
        if discovery_id in self.discovery_sessions:
            self.discovery_sessions[discovery_id]["status"] = "stopped"
            return True
        return False
    
    async def get_active_discoveries(self) -> List[Dict[str, Any]]:
        """Get all active discovery sessions."""
        return [
            session for session in self.discovery_sessions.values()
            if session["status"] == "running"
        ]
    
    @cached(ttl=300, key_prefix="port_scan")
    async def scan_host_ports(
        self, 
        host: str, 
        ports: List[int], 
        timeout: float = 3.0
    ) -> Dict[str, Any]:
        """Scan ports on a specific host with caching."""
        open_ports = []
        services = {}
        
        # Create connection tasks
        tasks = []
        for port in ports:
            task = asyncio.create_task(self._check_port(host, port, timeout))
            tasks.append((port, task))
        
        # Wait for all tasks to complete
        for port, task in tasks:
            try:
                is_open = await task
                if is_open:
                    open_ports.append(port)
                    service = self.service_signatures.get(port, "Unknown")
                    services[port] = service
            except Exception as e:
                logger.debug(f"Error scanning {host}:{port} - {e}")
        
        return {
            "host": host,
            "open_ports": open_ports,
            "services": services,
            "scan_time": datetime.now(timezone.utc).isoformat()
        }
    
    async def discover_service_details(self, host: str, port: int) -> Dict[str, Any]:
        """Discover detailed service information."""
        service_info = {
            "host": host,
            "port": port,
            "service": self.service_signatures.get(port, "Unknown"),
            "details": {}
        }
        
        try:
            # Basic service detection
            if port == 22:
                service_info["details"] = await self._detect_ssh_service(host, port)
            elif port in [80, 8080]:
                service_info["details"] = await self._detect_http_service(host, port)
            elif port in [443, 8443]:
                service_info["details"] = await self._detect_https_service(host, port)
            elif port == 3389:
                service_info["details"] = await self._detect_rdp_service(host, port)
            else:
                service_info["details"] = await self._detect_generic_service(host, port)
                
        except Exception as e:
            service_info["details"]["error"] = str(e)
        
        return service_info
    
    async def _perform_discovery(
        self,
        discovery_id: str,
        network: ipaddress.IPv4Network,
        ports: List[int],
        discovered_by: int
    ):
        """Perform the actual network discovery."""
        session = self.discovery_sessions[discovery_id]
        
        try:
            # Limit concurrent scans to avoid overwhelming the network
            semaphore = asyncio.Semaphore(50)
            
            async def scan_host(host_ip):
                async with semaphore:
                    if session["status"] != "running":
                        return
                    
                    try:
                        # Scan host
                        result = await self.scan_host_ports(str(host_ip), ports)
                        
                        # Update progress
                        session["scanned_hosts"] += 1
                        session["progress"] = (session["scanned_hosts"] / session["total_hosts"]) * 100
                        
                        # If host has open ports, it's a discovered target
                        if result["open_ports"]:
                            discovered_target = {
                                "host": str(host_ip),
                                "open_ports": result["open_ports"],
                                "services": result["services"],
                                "discovered_at": datetime.now(timezone.utc).isoformat()
                            }
                            
                            session["discovered_targets"].append(discovered_target)
                            
                            # Publish discovery event for each service
                            for port in result["open_ports"]:
                                service_type = result["services"].get(port, "Unknown")
                                
                                event = TargetDiscoveredEvent(
                                    discovered_host=str(host_ip),
                                    discovered_port=port,
                                    discovery_method="network_scan",
                                    target_type=service_type,
                                    additional_info={
                                        "discovery_id": discovery_id,
                                        "all_open_ports": result["open_ports"],
                                        "services": result["services"]
                                    },
                                    discovered_by=discovered_by
                                )
                                await event_bus.publish(event)
                        
                    except Exception as e:
                        logger.error(f"Error scanning host {host_ip}: {e}")
                        session["scanned_hosts"] += 1
                        session["progress"] = (session["scanned_hosts"] / session["total_hosts"]) * 100
            
            # Create tasks for all hosts
            tasks = []
            for host_ip in network.hosts():
                if session["status"] != "running":
                    break
                task = asyncio.create_task(scan_host(host_ip))
                tasks.append(task)
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Mark discovery as completed
            if session["status"] == "running":
                session["status"] = "completed"
                session["completed_at"] = datetime.now(timezone.utc)
                session["progress"] = 100
            
        except Exception as e:
            logger.error(f"Discovery error for {discovery_id}: {e}")
            session["status"] = "failed"
            session["error"] = str(e)
            session["completed_at"] = datetime.now(timezone.utc)
    
    async def _check_port(self, host: str, port: int, timeout: float) -> bool:
        """Check if a port is open on a host."""
        try:
            future = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(future, timeout=timeout)
            writer.close()
            await writer.wait_closed()
            return True
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            return False
    
    async def _detect_ssh_service(self, host: str, port: int) -> Dict[str, Any]:
        """Detect SSH service details."""
        try:
            future = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(future, timeout=5.0)
            
            # Read SSH banner
            banner = await asyncio.wait_for(reader.readline(), timeout=3.0)
            writer.close()
            await writer.wait_closed()
            
            return {
                "service_type": "SSH",
                "banner": banner.decode().strip(),
                "version": banner.decode().split()[0] if banner else "Unknown"
            }
        except Exception as e:
            return {"service_type": "SSH", "error": str(e)}
    
    async def _detect_http_service(self, host: str, port: int) -> Dict[str, Any]:
        """Detect HTTP service details."""
        try:
            future = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(future, timeout=5.0)
            
            # Send HTTP request
            request = f"GET / HTTP/1.1\r\nHost: {host}\r\n\r\n"
            writer.write(request.encode())
            await writer.drain()
            
            # Read response
            response = await asyncio.wait_for(reader.read(1024), timeout=3.0)
            writer.close()
            await writer.wait_closed()
            
            response_text = response.decode(errors='ignore')
            lines = response_text.split('\n')
            
            return {
                "service_type": "HTTP",
                "status_line": lines[0] if lines else "",
                "server": next((line.split(':', 1)[1].strip() for line in lines if line.startswith('Server:')), "Unknown")
            }
        except Exception as e:
            return {"service_type": "HTTP", "error": str(e)}
    
    async def _detect_https_service(self, host: str, port: int) -> Dict[str, Any]:
        """Detect HTTPS service details."""
        # For HTTPS, we'd need SSL/TLS handling - simplified for now
        return {
            "service_type": "HTTPS",
            "note": "SSL/TLS service detected"
        }
    
    async def _detect_rdp_service(self, host: str, port: int) -> Dict[str, Any]:
        """Detect RDP service details."""
        return {
            "service_type": "RDP",
            "note": "Remote Desktop Protocol detected"
        }
    
    async def _detect_generic_service(self, host: str, port: int) -> Dict[str, Any]:
        """Generic service detection."""
        try:
            future = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(future, timeout=3.0)
            
            # Try to read any banner
            try:
                banner = await asyncio.wait_for(reader.read(256), timeout=2.0)
                banner_text = banner.decode(errors='ignore').strip()
            except:
                banner_text = ""
            
            writer.close()
            await writer.wait_closed()
            
            return {
                "service_type": "Generic",
                "banner": banner_text if banner_text else "No banner detected"
            }
        except Exception as e:
            return {"service_type": "Generic", "error": str(e)}