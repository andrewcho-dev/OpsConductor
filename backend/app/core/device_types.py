"""
Device Type Classification System
Centralized system for device types, communication methods, and auto-discovery
"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum


class DeviceCategory(Enum):
    """Device categories for organization"""
    OPERATING_SYSTEM = "operating_system"
    NETWORK_INFRASTRUCTURE = "network_infrastructure"
    VIRTUALIZATION_CLOUD = "virtualization_cloud"
    STORAGE_SYSTEMS = "storage_systems"
    DATABASE_SYSTEMS = "database_systems"
    APPLICATION_SERVERS = "application_servers"
    COMMUNICATION_EMAIL = "communication_email"
    INFRASTRUCTURE_SERVICES = "infrastructure_services"
    POWER_ENVIRONMENTAL = "power_environmental"
    SECURITY_APPLIANCES = "security_appliances"
    IOT_EMBEDDED = "iot_embedded"
    GENERIC_UNKNOWN = "generic_unknown"


@dataclass
class DeviceType:
    """Device type definition with communication methods and discovery hints"""
    value: str
    label: str
    category: DeviceCategory
    communication_methods: Set[str]
    discovery_ports: List[int]
    discovery_oids: List[str]
    discovery_services: List[str]
    discovery_keywords: List[str]
    description: str = ""


class DeviceTypeRegistry:
    """Centralized registry for all device types"""
    
    def __init__(self):
        self._device_types: Dict[str, DeviceType] = {}
        self._initialize_device_types()
    
    def _initialize_device_types(self):
        """Initialize all device types with their communication methods and discovery hints"""
        
        # Operating Systems
        self._add_device_type(DeviceType(
            value="linux",
            label="Linux Server",
            category=DeviceCategory.OPERATING_SYSTEM,
            communication_methods={"ssh", "snmp", "rest_api", "telnet"},
            discovery_ports=[22, 161, 80, 443],
            discovery_oids=["1.3.6.1.2.1.1.1.0"],
            discovery_services=["ssh", "http", "https"],
            discovery_keywords=["linux", "ubuntu", "centos", "redhat", "debian"],
            description="Linux-based server or workstation"
        ))
        
        self._add_device_type(DeviceType(
            value="windows",
            label="Windows Server",
            category=DeviceCategory.OPERATING_SYSTEM,
            communication_methods={"winrm", "ssh", "snmp", "rest_api"},
            discovery_ports=[135, 445, 3389, 5985, 161],
            discovery_oids=["1.3.6.1.2.1.1.1.0"],
            discovery_services=["winrm", "rdp", "smb", "http"],
            discovery_keywords=["windows", "microsoft", "server"],
            description="Windows Server operating system"
        ))
        
        # Network Infrastructure
        self._add_device_type(DeviceType(
            value="cisco_switch",
            label="Cisco Switch",
            category=DeviceCategory.NETWORK_INFRASTRUCTURE,
            communication_methods={"ssh", "telnet", "snmp"},
            discovery_ports=[22, 23, 161],
            discovery_oids=["1.3.6.1.2.1.1.1.0", "1.3.6.1.4.1.9.1"],
            discovery_services=["ssh", "telnet"],
            discovery_keywords=["cisco", "catalyst", "nexus", "switch"],
            description="Cisco network switch"
        ))
        
        self._add_device_type(DeviceType(
            value="cisco_router",
            label="Cisco Router",
            category=DeviceCategory.NETWORK_INFRASTRUCTURE,
            communication_methods={"ssh", "telnet", "snmp"},
            discovery_ports=[22, 23, 161],
            discovery_oids=["1.3.6.1.2.1.1.1.0", "1.3.6.1.4.1.9.1"],
            discovery_services=["ssh", "telnet"],
            discovery_keywords=["cisco", "router", "isr", "asr"],
            description="Cisco network router"
        ))
        
        # Communication & Email
        self._add_device_type(DeviceType(
            value="smtp_server",
            label="SMTP Server",
            category=DeviceCategory.COMMUNICATION_EMAIL,
            communication_methods={"smtp", "ssh"},
            discovery_ports=[25, 587, 465, 22],
            discovery_oids=["1.3.6.1.2.1.1.1.0"],
            discovery_services=["smtp", "ssh"],
            discovery_keywords=["smtp", "mail", "postfix", "sendmail", "exim"],
            description="Email/SMTP server"
        ))
        
        self._add_device_type(DeviceType(
            value="exchange",
            label="Microsoft Exchange",
            category=DeviceCategory.COMMUNICATION_EMAIL,
            communication_methods={"smtp", "winrm", "rest_api"},
            discovery_ports=[25, 587, 465, 5985, 443],
            discovery_oids=["1.3.6.1.2.1.1.1.0"],
            discovery_services=["smtp", "winrm", "https"],
            discovery_keywords=["exchange", "microsoft", "outlook"],
            description="Microsoft Exchange email server"
        ))
        
        # Database Systems
        self._add_device_type(DeviceType(
            value="mysql",
            label="MySQL/MariaDB Server",
            category=DeviceCategory.DATABASE_SYSTEMS,
            communication_methods={"mysql", "ssh", "snmp"},
            discovery_ports=[3306, 22, 161],
            discovery_oids=["1.3.6.1.2.1.1.1.0"],
            discovery_services=["mysql", "ssh"],
            discovery_keywords=["mysql", "mariadb", "database"],
            description="MySQL or MariaDB database server"
        ))
        
        self._add_device_type(DeviceType(
            value="postgresql",
            label="PostgreSQL Server",
            category=DeviceCategory.DATABASE_SYSTEMS,
            communication_methods={"postgresql", "ssh", "snmp"},
            discovery_ports=[5432, 22, 161],
            discovery_oids=["1.3.6.1.2.1.1.1.0"],
            discovery_services=["postgresql", "ssh"],
            discovery_keywords=["postgresql", "postgres", "database"],
            description="PostgreSQL database server"
        ))
        
        # Generic/Unknown
        self._add_device_type(DeviceType(
            value="generic_device",
            label="Generic Network Device",
            category=DeviceCategory.GENERIC_UNKNOWN,
            communication_methods={"ssh", "snmp", "telnet", "rest_api"},
            discovery_ports=[22, 23, 161, 80, 443],
            discovery_oids=["1.3.6.1.2.1.1.1.0"],
            discovery_services=["ssh", "telnet", "http"],
            discovery_keywords=["device", "network", "unknown"],
            description="Generic network device with unknown type"
        ))
        
        # Legacy types for backward compatibility
        self._add_device_type(DeviceType(
            value="email",
            label="Email Server",
            category=DeviceCategory.COMMUNICATION_EMAIL,
            communication_methods={"smtp", "ssh"},
            discovery_ports=[25, 587, 465, 22],
            discovery_oids=["1.3.6.1.2.1.1.1.0"],
            discovery_services=["smtp", "ssh"],
            discovery_keywords=["email", "mail", "smtp"],
            description="Legacy email server type"
        ))
        
        self._add_device_type(DeviceType(
            value="database",
            label="Database Server",
            category=DeviceCategory.DATABASE_SYSTEMS,
            communication_methods={"mysql", "postgresql", "mssql", "oracle", "ssh"},
            discovery_ports=[3306, 5432, 1433, 1521, 22],
            discovery_oids=["1.3.6.1.2.1.1.1.0"],
            discovery_services=["mysql", "postgresql", "mssql", "oracle", "ssh"],
            discovery_keywords=["database", "db", "sql"],
            description="Legacy database server type"
        ))
    
    def _add_device_type(self, device_type: DeviceType):
        """Add a device type to the registry"""
        self._device_types[device_type.value] = device_type
    
    def get_device_type(self, value: str) -> Optional[DeviceType]:
        """Get a device type by its value"""
        return self._device_types.get(value)
    
    def get_all_device_types(self) -> List[DeviceType]:
        """Get all device types"""
        return list(self._device_types.values())
    
    def get_device_types_by_category(self, category: DeviceCategory) -> List[DeviceType]:
        """Get device types by category"""
        return [dt for dt in self._device_types.values() if dt.category == category]
    
    def get_communication_methods_for_device(self, device_type: str) -> Set[str]:
        """Get communication methods for a specific device type"""
        device = self.get_device_type(device_type)
        return device.communication_methods if device else set()
    
    def get_device_types_for_method(self, method: str) -> List[DeviceType]:
        """Get device types that support a specific communication method"""
        return [dt for dt in self._device_types.values() if method in dt.communication_methods]
    
    def get_discovery_hints(self, device_type: str) -> Dict:
        """Get discovery hints for a device type"""
        device = self.get_device_type(device_type)
        if not device:
            return {}
        
        return {
            "ports": device.discovery_ports,
            "oids": device.discovery_oids,
            "services": device.discovery_services,
            "keywords": device.discovery_keywords
        }
    
    def suggest_device_type(self, ports: List[int], services: List[str], banner: str = "") -> List[str]:
        """Suggest device types based on discovered information"""
        suggestions = []
        
        for device_type in self._device_types.values():
            score = 0
            
            # Check port matches
            for port in ports:
                if port in device_type.discovery_ports:
                    score += 1
            
            # Check service matches
            for service in services:
                if service in device_type.discovery_services:
                    score += 1
            
            # Check keyword matches in banner
            if banner:
                banner_lower = banner.lower()
                for keyword in device_type.discovery_keywords:
                    if keyword.lower() in banner_lower:
                        score += 1
            
            # If we have matches, add to suggestions
            if score > 0:
                suggestions.append((device_type.value, score))
        
        # Sort by score (highest first) and return device type values
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return [device_type for device_type, score in suggestions]


# Global registry instance
device_registry = DeviceTypeRegistry()


def get_valid_device_types() -> List[str]:
    """Get list of valid device type values (for backward compatibility)"""
    return list(device_registry._device_types.keys())


def get_communication_methods_for_device_type(device_type: str) -> Set[str]:
    """Get communication methods for a device type (for backward compatibility)"""
    return device_registry.get_communication_methods_for_device(device_type)


def suggest_device_type_from_discovery(ports: List[int], services: List[str], banner: str = "") -> List[str]:
    """Suggest device type from discovery information (for backward compatibility)"""
    return device_registry.suggest_device_type(ports, services, banner)
