"""
Network Discovery Service
Pure Python implementation for discovering devices on the network using asyncio.
"""
import asyncio
import socket
import ipaddress
import logging
from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import ssl
import struct
from urllib.parse import urlparse

# SNMP imports
try:
    from pysnmp.hlapi import *
    SNMP_AVAILABLE = True
except ImportError:
    SNMP_AVAILABLE = False
    logging.warning("SNMP not available - install pysnmp for SNMP discovery")

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredDevice:
    """Represents a discovered device on the network."""
    ip_address: str
    hostname: Optional[str] = None
    mac_address: Optional[str] = None
    open_ports: List[int] = field(default_factory=list)
    services: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    device_type: Optional[str] = None
    os_type: Optional[str] = None
    snmp_info: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    discovery_time: datetime = field(default_factory=datetime.utcnow)
    suggested_communication_methods: List[str] = field(default_factory=list)


@dataclass
class DiscoveryConfig:
    """Configuration for network discovery scans."""
    network_ranges: List[str]
    port_ranges: List[Tuple[int, int]] = field(default_factory=lambda: [(1, 1024)])
    common_ports: List[int] = field(default_factory=lambda: [
        22, 23, 25, 53, 80, 110, 143, 443, 993, 995,  # Common services
        135, 139, 445, 3389, 5985, 5986,              # Windows (enhanced)
        161, 162,                                       # SNMP
        1433, 3306, 5432, 27017,                      # Databases
        8080, 8443, 9000, 9090,                       # Web services
        6443, 2379, 2380,                             # Kubernetes
        8006,                                          # Proxmox (removed duplicate 8080)
        49152, 49153, 49154, 49155,                   # Windows dynamic ports
    ])
    timeout: float = 2.0
    max_concurrent: int = 200
    snmp_communities: List[str] = field(default_factory=lambda: ['public', 'private'])
    enable_snmp: bool = True
    enable_service_detection: bool = True
    enable_hostname_resolution: bool = True


class NetworkDiscoveryService:
    """Pure Python network discovery service using asyncio."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.discovery_hints = self._load_discovery_hints()
    
    def _load_discovery_hints(self) -> Dict[str, Any]:
        """Load device discovery hints for classification."""
        return {
            # Operating Systems
            'linux': {
                'ports': [22, 111, 2049],
                'banners': ['OpenSSH', 'Linux', 'Ubuntu', 'CentOS', 'Red Hat'],
                'snmp_oids': ['1.3.6.1.2.1.1.1.0'],
                'keywords': ['linux', 'ubuntu', 'centos', 'redhat', 'debian']
            },
            'windows': {
                'ports': [135, 139, 445, 3389, 5985, 5986],
                'banners': ['Microsoft', 'Windows', 'IIS', 'Server'],
                'snmp_oids': ['1.3.6.1.2.1.1.1.0'],
                'keywords': ['windows', 'microsoft', 'iis', 'server']
            },
            'windows_desktop': {
                'ports': [135, 139, 445, 3389],
                'banners': ['Microsoft', 'Windows'],
                'keywords': ['windows 10', 'windows 11', 'workstation', 'desktop']
            },
            'windows_server': {
                'ports': [135, 139, 445, 3389, 5985, 5986, 80, 443],
                'banners': ['Microsoft', 'Windows', 'IIS', 'Server'],
                'keywords': ['windows server', 'server 2019', 'server 2022', 'iis']
            },
            # Network Infrastructure
            'router_gateway': {
                'ports': [53, 80, 443, 161],  # DNS + Web management
                'banners': ['Router', 'Gateway', 'OpenWrt', 'DD-WRT'],
                'keywords': ['router', 'gateway', 'openwrt', 'dd-wrt', 'pfsense']
            },
            'cisco_switch': {
                'ports': [22, 23, 80, 443, 161],
                'banners': ['Cisco', 'IOS'],
                'snmp_oids': ['1.3.6.1.4.1.9.1'],
                'keywords': ['cisco', 'ios', 'switch']
            },
            'cisco_router': {
                'ports': [22, 23, 80, 443, 161],
                'banners': ['Cisco', 'IOS'],
                'snmp_oids': ['1.3.6.1.4.1.9.1'],
                'keywords': ['cisco', 'ios', 'router']
            },
            # Virtualization
            'proxmox': {
                'ports': [22, 8006],
                'banners': ['Proxmox', 'pve'],
                'keywords': ['proxmox', 'pve']
            },
            'vmware_esxi': {
                'ports': [22, 80, 443, 902],
                'banners': ['VMware', 'ESXi'],
                'keywords': ['vmware', 'esxi', 'vcenter']
            },
            # Databases
            'mysql': {
                'ports': [3306],
                'banners': ['MySQL'],
                'keywords': ['mysql']
            },
            'postgresql': {
                'ports': [5432],
                'banners': ['PostgreSQL'],
                'keywords': ['postgresql', 'postgres']
            },
            # Web servers
            'apache': {
                'ports': [80, 443],
                'banners': ['Apache'],
                'keywords': ['apache']
            },
            'nginx': {
                'ports': [80, 443],
                'banners': ['nginx'],
                'keywords': ['nginx']
            },
            # Generic fallback
            'generic_device': {
                'ports': [80, 443, 161],
                'banners': [],
                'keywords': []
            }
        }
    
    async def discover_network(self, config: DiscoveryConfig, progress_callback=None) -> List[DiscoveredDevice]:
        """
        Discover devices on the network using the provided configuration.
        
        Args:
            config: Discovery configuration
            progress_callback: Optional callback function for progress updates
            
        Returns:
            List of discovered devices
        """
        self.logger.info(f"Starting network discovery for ranges: {config.network_ranges}")
        
        # Generate list of IP addresses to scan
        ip_addresses = []
        for network_range in config.network_ranges:
            ip_addresses.extend(self._generate_ip_list(network_range))
        
        total_ips = len(ip_addresses)
        self.logger.info(f"Scanning {total_ips} IP addresses")
        
        if progress_callback:
            await progress_callback(0, total_ips, 0, "Starting scan...")
        
        # Create semaphore to limit concurrent connections
        semaphore = asyncio.Semaphore(config.max_concurrent)
        
        # Track progress
        completed = 0
        discovered_count = 0
        discovered_devices = []
        
        # Process IPs in larger batches for better performance
        batch_size = min(config.max_concurrent, 100)
        
        for i in range(0, total_ips, batch_size):
            batch_ips = ip_addresses[i:i + batch_size]
            
            # Scan batch concurrently
            tasks = [
                self._scan_host(ip, config, semaphore)
                for ip in batch_ips
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process batch results
            for result in batch_results:
                completed += 1
                if isinstance(result, DiscoveredDevice):
                    discovered_devices.append(result)
                    discovered_count += 1
            
            # Update progress less frequently (only after each batch)
            if progress_callback:
                progress_percent = (completed / total_ips) * 100
                await progress_callback(
                    progress_percent, 
                    total_ips, 
                    discovered_count,
                    f"Scanned {completed}/{total_ips} IPs, found {discovered_count} devices"
                )
        
        self.logger.info(f"Discovery complete. Found {len(discovered_devices)} devices")
        
        if progress_callback:
            await progress_callback(100, total_ips, discovered_count, "Discovery complete")
        
        return discovered_devices
    
    def _generate_ip_list(self, network_range: str) -> List[str]:
        """Generate list of IP addresses from network range."""
        try:
            network = ipaddress.ip_network(network_range, strict=False)
            return [str(ip) for ip in network.hosts()]
        except ValueError as e:
            self.logger.error(f"Invalid network range {network_range}: {e}")
            return []
    
    async def _scan_host(self, ip: str, config: DiscoveryConfig, semaphore: asyncio.Semaphore) -> Optional[DiscoveredDevice]:
        """Scan a single host for open ports and services."""
        async with semaphore:
            try:
                # First, do a quick ping-like check
                if not await self._is_host_alive(ip, config.timeout):
                    return None
                
                device = DiscoveredDevice(ip_address=ip)
                
                # Resolve hostname if enabled
                if config.enable_hostname_resolution:
                    device.hostname = await self._resolve_hostname(ip)
                
                # Scan ports
                open_ports = await self._scan_ports(ip, config)
                device.open_ports = open_ports
                
                if not open_ports:
                    return None  # No open ports found
                
                # Detect services on open ports
                if config.enable_service_detection:
                    device.services = await self._detect_services(ip, open_ports, config.timeout)
                
                # SNMP discovery
                if config.enable_snmp and SNMP_AVAILABLE and 161 in open_ports:
                    device.snmp_info = await self._snmp_discovery(ip, config.snmp_communities)
                
                # Classify device type
                device.device_type, device.confidence_score = self._classify_device(device)
                
                # Suggest communication methods
                device.suggested_communication_methods = self._suggest_communication_methods(device)
                
                self.logger.debug(f"Discovered device: {ip} ({device.device_type})")
                return device
                
            except Exception as e:
                self.logger.debug(f"Error scanning {ip}: {e}")
                return None
    
    async def _is_host_alive(self, ip: str, timeout: float) -> bool:
        """Quick check if host is alive using common ports."""
        # Enhanced port list with better Windows support
        common_check_ports = [
            22,    # SSH (Linux)
            80,    # HTTP
            135,   # Windows RPC
            139,   # NetBIOS
            443,   # HTTPS
            445,   # SMB (Windows file sharing)
            3389,  # RDP (Windows Remote Desktop)
            5985,  # WinRM HTTP
            5986,  # WinRM HTTPS
            161    # SNMP
        ]
        
        # Use shorter timeout per port for faster scanning
        port_timeout = min(timeout / len(common_check_ports), 0.5)
        
        for port in common_check_ports:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, port),
                    timeout=port_timeout
                )
                writer.close()
                await writer.wait_closed()
                return True
            except:
                continue
        
        return False
    
    async def _resolve_hostname(self, ip: str) -> Optional[str]:
        """Resolve hostname for IP address."""
        try:
            hostname, _, _ = await asyncio.get_event_loop().run_in_executor(
                None, socket.gethostbyaddr, ip
            )
            return hostname
        except:
            return None
    
    async def _scan_ports(self, ip: str, config: DiscoveryConfig) -> List[int]:
        """Scan ports on a host."""
        ports_to_scan = set(config.common_ports)
        
        # Add ports from ranges
        for start, end in config.port_ranges:
            ports_to_scan.update(range(start, end + 1))
        
        # Limit concurrent port scans per host
        port_semaphore = asyncio.Semaphore(20)
        
        tasks = [
            self._scan_port(ip, port, config.timeout, port_semaphore)
            for port in ports_to_scan
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        open_ports = [
            port for port, result in zip(ports_to_scan, results)
            if result is True
        ]
        
        return sorted(open_ports)
    
    async def _scan_port(self, ip: str, port: int, timeout: float, semaphore: asyncio.Semaphore) -> bool:
        """Scan a single port."""
        async with semaphore:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, port),
                    timeout=timeout
                )
                writer.close()
                await writer.wait_closed()
                return True
            except:
                return False
    
    async def _detect_services(self, ip: str, ports: List[int], timeout: float) -> Dict[int, Dict[str, Any]]:
        """Detect services running on open ports."""
        services = {}
        
        for port in ports:
            try:
                service_info = await self._get_service_banner(ip, port, timeout)
                if service_info:
                    services[port] = service_info
            except Exception as e:
                self.logger.debug(f"Error detecting service on {ip}:{port}: {e}")
        
        return services
    
    async def _get_service_banner(self, ip: str, port: int, timeout: float) -> Optional[Dict[str, Any]]:
        """Get service banner from a port."""
        try:
            if port in [80, 8080, 8000, 9000]:
                return await self._get_http_banner(ip, port, timeout, False)
            elif port in [443, 8443]:
                return await self._get_http_banner(ip, port, timeout, True)
            elif port == 22:
                return await self._get_ssh_banner(ip, port, timeout)
            elif port == 23:
                return await self._get_telnet_banner(ip, port, timeout)
            elif port == 25:
                return await self._get_smtp_banner(ip, port, timeout)
            else:
                return await self._get_generic_banner(ip, port, timeout)
        except Exception as e:
            self.logger.debug(f"Error getting banner for {ip}:{port}: {e}")
            return None
    
    async def _get_http_banner(self, ip: str, port: int, timeout: float, use_ssl: bool) -> Dict[str, Any]:
        """Get HTTP service information."""
        try:
            import aiohttp
            
            protocol = 'https' if use_ssl else 'http'
            url = f"{protocol}://{ip}:{port}/"
            
            connector = aiohttp.TCPConnector(ssl=False) if use_ssl else None
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                async with session.get(url) as response:
                    server = response.headers.get('Server', 'Unknown')
                    return {
                        'service': 'http',
                        'banner': server,
                        'status_code': response.status,
                        'headers': dict(response.headers)
                    }
        except ImportError:
            # Fallback to basic socket connection
            return await self._get_generic_banner(ip, port, timeout)
        except Exception as e:
            self.logger.debug(f"HTTP banner detection failed for {ip}:{port}: {e}")
            return {'service': 'http', 'banner': 'Unknown', 'error': str(e)}
    
    async def _get_ssh_banner(self, ip: str, port: int, timeout: float) -> Dict[str, Any]:
        """Get SSH service banner."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=timeout
            )
            
            # Read SSH banner
            banner = await asyncio.wait_for(
                reader.readline(),
                timeout=timeout
            )
            
            writer.close()
            await writer.wait_closed()
            
            banner_str = banner.decode('utf-8', errors='ignore').strip()
            
            return {
                'service': 'ssh',
                'banner': banner_str,
                'version': banner_str
            }
        except Exception as e:
            return {'service': 'ssh', 'banner': 'Unknown', 'error': str(e)}
    
    async def _get_telnet_banner(self, ip: str, port: int, timeout: float) -> Dict[str, Any]:
        """Get Telnet service banner."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=timeout
            )
            
            # Read initial telnet negotiation/banner
            data = await asyncio.wait_for(
                reader.read(1024),
                timeout=timeout
            )
            
            writer.close()
            await writer.wait_closed()
            
            banner = data.decode('utf-8', errors='ignore').strip()
            
            return {
                'service': 'telnet',
                'banner': banner
            }
        except Exception as e:
            return {'service': 'telnet', 'banner': 'Unknown', 'error': str(e)}
    
    async def _get_smtp_banner(self, ip: str, port: int, timeout: float) -> Dict[str, Any]:
        """Get SMTP service banner."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=timeout
            )
            
            # Read SMTP greeting
            greeting = await asyncio.wait_for(
                reader.readline(),
                timeout=timeout
            )
            
            writer.close()
            await writer.wait_closed()
            
            banner = greeting.decode('utf-8', errors='ignore').strip()
            
            return {
                'service': 'smtp',
                'banner': banner
            }
        except Exception as e:
            return {'service': 'smtp', 'banner': 'Unknown', 'error': str(e)}
    
    async def _get_generic_banner(self, ip: str, port: int, timeout: float) -> Dict[str, Any]:
        """Get generic service banner."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=timeout
            )
            
            # Try to read some data
            try:
                data = await asyncio.wait_for(
                    reader.read(1024),
                    timeout=min(timeout, 2.0)
                )
                banner = data.decode('utf-8', errors='ignore').strip()
            except asyncio.TimeoutError:
                banner = "No banner"
            
            writer.close()
            await writer.wait_closed()
            
            return {
                'service': 'unknown',
                'banner': banner,
                'port': port
            }
        except Exception as e:
            return {'service': 'unknown', 'banner': 'Unknown', 'error': str(e)}
    
    async def _snmp_discovery(self, ip: str, communities: List[str]) -> Dict[str, Any]:
        """Discover device information via SNMP."""
        if not SNMP_AVAILABLE:
            return {}
        
        snmp_info = {}
        
        for community in communities:
            try:
                # System description OID
                for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
                    SnmpEngine(),
                    CommunityData(community),
                    UdpTransportTarget((ip, 161)),
                    ContextData(),
                    ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0')),  # sysDescr
                    lexicographicMode=False,
                    maxRows=1
                ):
                    if errorIndication:
                        break
                    elif errorStatus:
                        break
                    else:
                        for varBind in varBinds:
                            oid, value = varBind
                            snmp_info['sysDescr'] = str(value)
                            snmp_info['community'] = community
                            return snmp_info
            except Exception as e:
                self.logger.debug(f"SNMP discovery failed for {ip} with community {community}: {e}")
                continue
        
        return snmp_info
    
    def _classify_device(self, device: DiscoveredDevice) -> Tuple[str, float]:
        """
        Classify device type based on discovered information.
        
        Returns:
            Tuple of (device_type, confidence_score)
        """
        scores = {}
        
        for device_type, hints in self.discovery_hints.items():
            score = 0.0
            
            # Check port matches
            port_matches = len(set(device.open_ports) & set(hints['ports']))
            if port_matches > 0:
                score += port_matches * 0.3
                
                # Special case: DNS port 53 strongly indicates router/gateway
                if device_type == 'router_gateway' and 53 in device.open_ports:
                    score += 0.5
            
            # Check banner matches
            for port, service_info in device.services.items():
                banner = service_info.get('banner', '').lower()
                for hint_banner in hints['banners']:
                    if hint_banner.lower() in banner:
                        score += 0.4
            
            # Check SNMP info matches
            if device.snmp_info and 'sysDescr' in device.snmp_info:
                sys_descr = device.snmp_info['sysDescr'].lower()
                for keyword in hints['keywords']:
                    if keyword.lower() in sys_descr:
                        score += 0.5
            
            # Check hostname matches
            if device.hostname:
                hostname_lower = device.hostname.lower()
                for keyword in hints['keywords']:
                    if keyword.lower() in hostname_lower:
                        score += 0.2
            
            if score > 0:
                scores[device_type] = score
        
        if not scores:
            return 'generic_device', 0.1
        
        # Return device type with highest score
        best_type = max(scores.items(), key=lambda x: x[1])
        return best_type[0], min(best_type[1], 1.0)
    
    def _suggest_communication_methods(self, device: DiscoveredDevice) -> List[str]:
        """Suggest appropriate communication methods based on discovered services."""
        methods = []
        
        # SSH
        if 22 in device.open_ports:
            methods.append('ssh')
        
        # WinRM
        if 5985 in device.open_ports or 5986 in device.open_ports:
            methods.append('winrm')
        
        # SNMP
        if 161 in device.open_ports:
            methods.append('snmp')
        
        # HTTP/HTTPS
        if any(port in device.open_ports for port in [80, 443, 8080, 8443]):
            methods.append('rest_api')
        
        # Telnet
        if 23 in device.open_ports:
            methods.append('telnet')
        
        # SMTP
        if 25 in device.open_ports:
            methods.append('smtp')
        
        return methods


# Utility functions for testing
async def quick_discovery_test():
    """Quick test function for development."""
    service = NetworkDiscoveryService()
    
    config = DiscoveryConfig(
        network_ranges=['192.168.1.0/24'],
        common_ports=[22, 80, 443, 161],
        timeout=2.0,
        max_concurrent=20
    )
    
    devices = await service.discover_network(config)
    
    for device in devices:
        print(f"Found: {device.ip_address} ({device.device_type}) - Ports: {device.open_ports}")
    
    return devices


if __name__ == "__main__":
    # Test the discovery service
    asyncio.run(quick_discovery_test())