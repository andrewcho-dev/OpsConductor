/**
 * Target Service
 * API service for Universal Target management following the architecture plan.
 * CRITICAL: Uses relative URLs as required by architecture.
 */

// Development backend URL
const API_BASE_URL = process.env.REACT_APP_API_URL || '';

/**
 * Get authentication headers with bearer token
 */
const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
};

/**
 * Handle API response and errors
 */
const handleResponse = async (response) => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    console.error('API Error Response:', errorData);
    
    // Handle different error formats
    if (errorData.detail) {
      if (Array.isArray(errorData.detail)) {
        // Pydantic validation errors
        const errors = errorData.detail.map(err => `${err.loc.join('.')}: ${err.msg}`).join(', ');
        throw new Error(errors);
      } else {
        // Simple detail error
        throw new Error(errorData.detail);
      }
    } else if (errorData.message) {
      throw new Error(errorData.message);
    } else {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  }
  return response.json();
};

/**
 * Get all targets with summary information
 */
export const getAllTargets = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/targets/`, {
      method: 'GET',
      headers: getAuthHeaders()
    });
    return await handleResponse(response);
  } catch (error) {
    console.error('Error fetching targets:', error);
    throw error;
  }
};

/**
 * Get a specific target by ID with full details
 */
export const getTargetById = async (targetId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/targets/${targetId}`, {
      method: 'GET',
      headers: getAuthHeaders()
    });
    return await handleResponse(response);
  } catch (error) {
    console.error(`Error fetching target ${targetId}:`, error);
    throw error;
  }
};

/**
 * Create a new target with communication method and credentials (legacy single method)
 */
export const createTarget = async (targetData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/targets/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(targetData)
    });
    return await handleResponse(response);
  } catch (error) {
    console.error('Error creating target:', error);
    throw error;
  }
};

/**
 * Create a new target with comprehensive support for multiple communication methods
 */
export const createTargetComprehensive = async (targetData) => {
  try {
    console.log('Creating target comprehensively:', targetData);
    const response = await fetch(`${API_BASE_URL}/targets/comprehensive`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(targetData)
    });
    const result = await handleResponse(response);
    console.log('Create target comprehensive response:', result);
    return result;
  } catch (error) {
    console.error('Error creating target comprehensively:', error);
    throw error;
  }
};

/**
 * Update target basic information
 */
export const updateTarget = async (targetId, targetData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/targets/${targetId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(targetData)
    });
    return await handleResponse(response);
  } catch (error) {
    console.error(`Error updating target ${targetId}:`, error);
    throw error;
  }
};

/**
 * Comprehensive update of target including communication methods and credentials
 */
export const updateTargetComprehensive = async (targetId, targetData) => {
  try {
    console.log(`Comprehensive update for target ${targetId}:`, targetData);
    const response = await fetch(`${API_BASE_URL}/targets/${targetId}/comprehensive`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(targetData)
    });
    const result = await handleResponse(response);
    console.log(`Comprehensive update response:`, result);
    return result;
  } catch (error) {
    console.error(`Error updating target comprehensively ${targetId}:`, error);
    throw error;
  }
};

/**
 * Delete a target (soft delete)
 */
export const deleteTarget = async (targetId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/targets/${targetId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    
    return true; // Delete returns 204 No Content
  } catch (error) {
    console.error(`Error deleting target ${targetId}:`, error);
    throw error;
  }
};

/**
 * Test connection to a target
 */
export const testTargetConnection = async (targetId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/targets/${targetId}/test-connection`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    return await handleResponse(response);
  } catch (error) {
    console.error(`Error testing connection to target ${targetId}:`, error);
    throw error;
  }
};

/**
 * Add a new communication method to a target
 */
export const addCommunicationMethod = async (targetId, methodData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/targets/${targetId}/communication-methods`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(methodData)
    });
    return await handleResponse(response);
  } catch (error) {
    console.error(`Error adding communication method to target ${targetId}:`, error);
    throw error;
  }
};

/**
 * Update a communication method
 */
export const updateCommunicationMethod = async (targetId, methodId, methodData) => {
  try {
    console.log(`Updating communication method ${methodId} for target ${targetId}:`, methodData);
    const response = await fetch(`${API_BASE_URL}/targets/${targetId}/communication-methods/${methodId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(methodData)
    });
    const result = await handleResponse(response);
    console.log(`Update communication method response:`, result);
    return result;
  } catch (error) {
    console.error(`Error updating communication method ${methodId}:`, error);
    throw error;
  }
};

/**
 * Delete a communication method
 */
export const deleteCommunicationMethod = async (targetId, methodId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/targets/${targetId}/communication-methods/${methodId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    return await handleResponse(response);
  } catch (error) {
    console.error(`Error deleting communication method ${methodId}:`, error);
    throw error;
  }
};

/**
 * Test connection using a specific communication method
 */
export const testCommunicationMethod = async (targetId, methodId) => {
  try {
    console.log(`🔧 TESTING METHOD: targetId=${targetId}, methodId=${methodId}`);
    console.log(`🔧 URL: ${API_BASE_URL}/targets/${targetId}/communication-methods/${methodId}/test`);
    
    const response = await fetch(`${API_BASE_URL}/targets/${targetId}/communication-methods/${methodId}/test?cache=${Date.now()}`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    return await handleResponse(response);
  } catch (error) {
    console.error(`Error testing communication method ${methodId}:`, error);
    throw error;
  }
};

/**
 * Test a communication method configuration before saving
 * This allows testing method configs during create/edit without saving first
 */
export const testMethodConfiguration = async (methodConfig) => {
  try {
    console.log(`🔧 TESTING METHOD CONFIG:`, methodConfig);
    
    const response = await fetch(`${API_BASE_URL}/targets/test-method-config`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        method_type: methodConfig.method_type,
        config: {
          host: methodConfig.host,
          port: methodConfig.port
        },
        credentials: {
          credential_type: methodConfig.credential_type,
          encrypted_credentials: methodConfig.credential_type === 'password' 
            ? { username: methodConfig.username, password: methodConfig.password }
            : { username: methodConfig.username, ssh_key: methodConfig.ssh_key }
        }
      })
    });
    return await handleResponse(response);
  } catch (error) {
    console.error(`Error testing method configuration:`, error);
    throw error;
  }
};

/**
 * Validation helpers
 */
export const validateTargetData = (targetData) => {
  const errors = {};
  
  if (!targetData.name?.trim()) {
    errors.name = 'Target name is required';
  }
  
  if (!targetData.os_type) {
    errors.os_type = 'Device/OS type is required';
  }
  
  if (!targetData.ip_address?.trim()) {
    errors.ip_address = 'IP address is required';
  } else if (!/^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/.test(targetData.ip_address)) {
    errors.ip_address = 'Invalid IP address format';
  }
  
  if (!targetData.method_type) {
    errors.method_type = 'Communication method is required';
  }
  
  if (!targetData.username?.trim()) {
    errors.username = 'Username is required';
  }
  
  // Validate authentication method
  if (targetData.method_type === 'ssh' && targetData.ssh_key) {
    // SSH key authentication
    if (!targetData.ssh_key.trim()) {
      errors.ssh_key = 'SSH key content is required';
    }
  } else if (!targetData.password?.trim()) {
    // Password authentication
    errors.password = 'Password is required';
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};

/**
 * Get default values for new target creation
 */
export const getDefaultTargetData = () => ({
  name: '',
  description: '',
  target_type: 'system',
  os_type: 'linux',
  environment: 'development',
  location: '',
  data_center: '',
  region: '',
  ip_address: '',
  method_type: 'ssh',
  username: '',
  password: '',
  ssh_key: '',
  ssh_passphrase: ''
});

/**
 * Get communication method options - ALL methods available for ANY OS type
 * FIXED: Now returns all connection methods regardless of OS type
 */
export const getCommunicationMethodOptions = (osType) => {
  const systemMethods = [
    { value: 'ssh', label: 'SSH' },
    { value: 'winrm', label: 'WinRM' },
    { value: 'snmp', label: 'SNMP' },
    { value: 'telnet', label: 'Telnet' },
    { value: 'rest_api', label: 'REST API' },
    { value: 'smtp', label: 'SMTP' }
  ];
  
  const databaseMethods = [
    { value: 'mysql', label: 'MySQL/MariaDB' },
    { value: 'postgresql', label: 'PostgreSQL' },
    { value: 'mssql', label: 'Microsoft SQL Server' },
    { value: 'oracle', label: 'Oracle Database' },
    { value: 'sqlite', label: 'SQLite' },
    { value: 'mongodb', label: 'MongoDB' },
    { value: 'redis', label: 'Redis' },
    { value: 'elasticsearch', label: 'Elasticsearch' }
  ];
  
  // FIXED: Return ALL methods for ALL OS types - users should be able to choose any connection method
  // A Linux server might have MySQL, PostgreSQL, Redis, etc. running on it
  // A Windows server might have MSSQL, MongoDB, Elasticsearch, etc. running on it
  return [...systemMethods, ...databaseMethods];
};

/**
 * Get environment options
 */
export const getEnvironmentOptions = () => [
  { value: 'development', label: 'Development' },
  { value: 'testing', label: 'Testing' },
  { value: 'staging', label: 'Staging' }
];

/**
 * Get Device/OS type options - Strategically organized for automation and discovery
 */
export const getOSTypeOptions = () => [
  // Operating Systems
  { value: 'linux', label: 'Linux Server', category: 'Operating Systems' },
  { value: 'windows', label: 'Windows Server', category: 'Operating Systems' },
  { value: 'windows_desktop', label: 'Windows Desktop', category: 'Operating Systems' },
  { value: 'macos', label: 'macOS', category: 'Operating Systems' },
  { value: 'freebsd', label: 'FreeBSD', category: 'Operating Systems' },
  { value: 'aix', label: 'IBM AIX', category: 'Operating Systems' },
  { value: 'solaris', label: 'Oracle Solaris', category: 'Operating Systems' },
  
  // Network Infrastructure
  { value: 'cisco_switch', label: 'Cisco Switch', category: 'Network Infrastructure' },
  { value: 'cisco_router', label: 'Cisco Router', category: 'Network Infrastructure' },
  { value: 'juniper_switch', label: 'Juniper Switch', category: 'Network Infrastructure' },
  { value: 'juniper_router', label: 'Juniper Router', category: 'Network Infrastructure' },
  { value: 'arista_switch', label: 'Arista Switch', category: 'Network Infrastructure' },
  { value: 'hp_switch', label: 'HP/Aruba Switch', category: 'Network Infrastructure' },
  { value: 'dell_switch', label: 'Dell Switch', category: 'Network Infrastructure' },
  { value: 'firewall', label: 'Firewall', category: 'Network Infrastructure' },
  { value: 'load_balancer', label: 'Load Balancer', category: 'Network Infrastructure' },
  { value: 'wireless_controller', label: 'Wireless Controller', category: 'Network Infrastructure' },
  { value: 'access_point', label: 'Wireless Access Point', category: 'Network Infrastructure' },
  
  // Virtualization & Cloud
  { value: 'vmware_esxi', label: 'VMware ESXi', category: 'Virtualization' },
  { value: 'vmware_vcenter', label: 'VMware vCenter', category: 'Virtualization' },
  { value: 'hyper_v', label: 'Microsoft Hyper-V', category: 'Virtualization' },
  { value: 'proxmox', label: 'Proxmox VE', category: 'Virtualization' },
  { value: 'xen', label: 'Citrix XenServer', category: 'Virtualization' },
  { value: 'kubernetes', label: 'Kubernetes Node', category: 'Virtualization' },
  { value: 'docker', label: 'Docker Host', category: 'Virtualization' },
  
  // Storage Systems
  { value: 'netapp', label: 'NetApp Storage', category: 'Storage' },
  { value: 'emc_storage', label: 'Dell EMC Storage', category: 'Storage' },
  { value: 'hp_storage', label: 'HP Storage', category: 'Storage' },
  { value: 'pure_storage', label: 'Pure Storage', category: 'Storage' },
  { value: 'synology', label: 'Synology NAS', category: 'Storage' },
  { value: 'qnap', label: 'QNAP NAS', category: 'Storage' },
  
  // Database Systems
  { value: 'mysql', label: 'MySQL/MariaDB Server', category: 'Database' },
  { value: 'postgresql', label: 'PostgreSQL Server', category: 'Database' },
  { value: 'mssql', label: 'Microsoft SQL Server', category: 'Database' },
  { value: 'oracle_db', label: 'Oracle Database', category: 'Database' },
  { value: 'mongodb', label: 'MongoDB Server', category: 'Database' },
  { value: 'redis', label: 'Redis Server', category: 'Database' },
  { value: 'elasticsearch', label: 'Elasticsearch Node', category: 'Database' },
  { value: 'cassandra', label: 'Apache Cassandra', category: 'Database' },
  
  // Application Servers
  { value: 'apache', label: 'Apache HTTP Server', category: 'Application Servers' },
  { value: 'nginx', label: 'Nginx Server', category: 'Application Servers' },
  { value: 'iis', label: 'Microsoft IIS', category: 'Application Servers' },
  { value: 'tomcat', label: 'Apache Tomcat', category: 'Application Servers' },
  { value: 'jboss', label: 'JBoss/WildFly', category: 'Application Servers' },
  { value: 'websphere', label: 'IBM WebSphere', category: 'Application Servers' },
  
  // Communication & Email
  { value: 'exchange', label: 'Microsoft Exchange', category: 'Communication' },
  { value: 'postfix', label: 'Postfix Mail Server', category: 'Communication' },
  { value: 'sendmail', label: 'Sendmail Server', category: 'Communication' },
  { value: 'zimbra', label: 'Zimbra Server', category: 'Communication' },
  { value: 'smtp_server', label: 'SMTP Server', category: 'Communication' },
  { value: 'email', label: 'Email Server', category: 'Communication' },
  { value: 'asterisk', label: 'Asterisk PBX', category: 'Communication' },
  
  // Infrastructure Services
  { value: 'dns_server', label: 'DNS Server', category: 'Infrastructure Services' },
  { value: 'dhcp_server', label: 'DHCP Server', category: 'Infrastructure Services' },
  { value: 'ntp_server', label: 'NTP Server', category: 'Infrastructure Services' },
  { value: 'ldap_server', label: 'LDAP/Active Directory', category: 'Infrastructure Services' },
  { value: 'backup_server', label: 'Backup Server', category: 'Infrastructure Services' },
  
  // Power & Environmental
  { value: 'ups', label: 'UPS (Uninterruptible Power Supply)', category: 'Power & Environmental' },
  { value: 'pdu', label: 'Power Distribution Unit', category: 'Power & Environmental' },
  { value: 'environmental_monitor', label: 'Environmental Monitor', category: 'Power & Environmental' },
  { value: 'generator', label: 'Backup Generator', category: 'Power & Environmental' },
  
  // Security Appliances
  { value: 'ids_ips', label: 'IDS/IPS System', category: 'Security' },
  { value: 'siem', label: 'SIEM Appliance', category: 'Security' },
  { value: 'vulnerability_scanner', label: 'Vulnerability Scanner', category: 'Security' },
  
  // IoT & Embedded
  { value: 'raspberry_pi', label: 'Raspberry Pi', category: 'IoT & Embedded' },
  { value: 'arduino', label: 'Arduino Device', category: 'IoT & Embedded' },
  { value: 'iot_sensor', label: 'IoT Sensor', category: 'IoT & Embedded' },
  { value: 'embedded_linux', label: 'Embedded Linux Device', category: 'IoT & Embedded' },
  
  // Generic/Unknown
  { value: 'generic_device', label: 'Generic Network Device', category: 'Generic' },
  { value: 'unknown', label: 'Unknown Device Type', category: 'Generic' }
];

/**
 * Get auto-discovery hints for device types
 * This will be used by the future auto-discovery feature
 */
export const getDeviceDiscoveryHints = () => ({
  // Operating Systems
  'linux': { 
    ports: [22], 
    snmp_oids: ['1.3.6.1.2.1.1.1.0'], 
    services: ['ssh'], 
    keywords: ['linux', 'ubuntu', 'centos', 'redhat', 'debian'] 
  },
  'windows': { 
    ports: [135, 445, 3389, 5985], 
    snmp_oids: ['1.3.6.1.2.1.1.1.0'], 
    services: ['winrm', 'rdp', 'smb'], 
    keywords: ['windows', 'microsoft'] 
  },
  
  // Network Infrastructure
  'cisco_switch': { 
    ports: [22, 23, 161], 
    snmp_oids: ['1.3.6.1.2.1.1.1.0', '1.3.6.1.4.1.9.1'], 
    services: ['ssh', 'telnet', 'snmp'], 
    keywords: ['cisco', 'catalyst', 'nexus'] 
  },
  'cisco_router': { 
    ports: [22, 23, 161], 
    snmp_oids: ['1.3.6.1.2.1.1.1.0', '1.3.6.1.4.1.9.1'], 
    services: ['ssh', 'telnet', 'snmp'], 
    keywords: ['cisco', 'router', 'isr'] 
  },
  'juniper_switch': { 
    ports: [22, 161], 
    snmp_oids: ['1.3.6.1.2.1.1.1.0', '1.3.6.1.4.1.2636'], 
    services: ['ssh', 'snmp'], 
    keywords: ['juniper', 'junos', 'ex'] 
  },
  
  // Power & Environmental
  'ups': { 
    ports: [161, 80, 443], 
    snmp_oids: ['1.3.6.1.2.1.33.1.1.1.0', '1.3.6.1.4.1.318'], 
    services: ['snmp', 'http'], 
    keywords: ['ups', 'apc', 'eaton', 'tripp'] 
  },
  'pdu': { 
    ports: [161, 80, 443], 
    snmp_oids: ['1.3.6.1.4.1.318', '1.3.6.1.4.1.534'], 
    services: ['snmp', 'http'], 
    keywords: ['pdu', 'power', 'distribution'] 
  },
  
  // Virtualization
  'vmware_esxi': { 
    ports: [22, 80, 443, 902], 
    snmp_oids: ['1.3.6.1.2.1.1.1.0'], 
    services: ['ssh', 'https'], 
    keywords: ['vmware', 'esxi', 'vsphere'] 
  },
  
  // Storage
  'netapp': { 
    ports: [22, 80, 443, 161], 
    snmp_oids: ['1.3.6.1.4.1.789'], 
    services: ['ssh', 'https', 'snmp'], 
    keywords: ['netapp', 'ontap', 'filer'] 
  },
  
  // Database Systems
  'mysql': { 
    ports: [3306], 
    services: ['mysql'], 
    keywords: ['mysql', 'mariadb'] 
  },
  'postgresql': { 
    ports: [5432], 
    services: ['postgresql'], 
    keywords: ['postgresql', 'postgres'] 
  },
  
  // Communication & Email
  'smtp_server': { 
    ports: [25, 587, 465], 
    services: ['smtp'], 
    keywords: ['smtp', 'mail', 'postfix', 'sendmail', 'exim'] 
  },
  
  // Default for unknown devices
  'unknown': { 
    ports: [22, 23, 80, 443, 161], 
    snmp_oids: ['1.3.6.1.2.1.1.1.0'], 
    services: ['ssh', 'telnet', 'http', 'https', 'snmp'], 
    keywords: [] 
  }
});

/**
 * Get recommended communication methods for device type
 */
export const getRecommendedMethodsForDeviceType = (deviceType) => {
  const methodMap = {
    // Operating Systems
    'linux': ['ssh', 'snmp'],
    'windows': ['winrm', 'snmp'],
    'windows_desktop': ['winrm'],
    'macos': ['ssh'],
    'freebsd': ['ssh', 'snmp'],
    'aix': ['ssh', 'snmp'],
    'solaris': ['ssh', 'snmp'],
    
    // Network Infrastructure
    'cisco_switch': ['ssh', 'telnet', 'snmp'],
    'cisco_router': ['ssh', 'telnet', 'snmp'],
    'juniper_switch': ['ssh', 'snmp'],
    'juniper_router': ['ssh', 'snmp'],
    'arista_switch': ['ssh', 'snmp'],
    'hp_switch': ['ssh', 'snmp'],
    'dell_switch': ['ssh', 'snmp'],
    'firewall': ['ssh', 'snmp', 'rest_api'],
    'load_balancer': ['ssh', 'snmp', 'rest_api'],
    'wireless_controller': ['ssh', 'snmp', 'rest_api'],
    'access_point': ['ssh', 'snmp'],
    
    // Virtualization
    'vmware_esxi': ['ssh', 'rest_api'],
    'vmware_vcenter': ['rest_api'],
    'hyper_v': ['winrm'],
    'proxmox': ['ssh', 'rest_api'],
    'kubernetes': ['rest_api'],
    'docker': ['ssh'],
    
    // Storage
    'netapp': ['ssh', 'snmp', 'rest_api'],
    'emc_storage': ['ssh', 'snmp'],
    'synology': ['ssh', 'snmp', 'rest_api'],
    'qnap': ['ssh', 'snmp', 'rest_api'],
    
    // Database Systems
    'mysql': ['mysql', 'ssh'],
    'postgresql': ['postgresql', 'ssh'],
    'mssql': ['mssql', 'winrm'],
    'oracle_db': ['ssh', 'snmp'],
    'mongodb': ['mongodb', 'ssh'],
    'redis': ['redis', 'ssh'],
    'elasticsearch': ['elasticsearch', 'rest_api', 'ssh'],
    
    // Power & Environmental
    'ups': ['snmp', 'rest_api'],
    'pdu': ['snmp', 'rest_api'],
    'environmental_monitor': ['snmp'],
    
    // Communication & Email
    'exchange': ['winrm', 'rest_api'],
    'postfix': ['ssh', 'smtp'],
    'zimbra': ['ssh', 'rest_api'],
    'smtp_server': ['smtp', 'ssh'],
    
    // IoT & Embedded
    'raspberry_pi': ['ssh', 'snmp'],
    'arduino': ['rest_api'],
    'iot_sensor': ['snmp', 'rest_api'],
    'embedded_linux': ['ssh', 'telnet'],
    
    // Default
    'generic_device': ['ssh', 'snmp'],
    'unknown': ['ssh', 'snmp']
  };
  
  return methodMap[deviceType] || ['ssh', 'snmp'];
};

/**
 * Get default port for communication method type
 */
export const getDefaultPortForMethod = (methodType) => {
  const defaultPorts = {
    'ssh': 22,
    'winrm': 5985,
    'snmp': 161,
    'telnet': 23,
    'rest_api': 80,
    'smtp': 587,
    'mysql': 3306,
    'postgresql': 5432,
    'mssql': 1433,
    'oracle': 1521,
    'sqlite': 0,
    'mongodb': 27017,
    'redis': 6379,
    'elasticsearch': 9200
  };
  return defaultPorts[methodType] || 22;
};

/**
 * Get method-specific configuration fields
 */
export const getDatabaseConfigFields = (methodType) => {
  const configs = {
    'rest_api': {
      protocol: 'http',
      base_path: '/',
      verify_ssl: true
    },
    'snmp': {
      version: '2c',
      community: 'public',
      retries: 3,
      // SNMPv3 fields
      security_level: 'authPriv',
      auth_protocol: 'MD5',
      privacy_protocol: 'DES'
    },
    'mysql': {
      database: '',
      charset: 'utf8mb4',
      ssl_mode: 'disabled'
    },
    'postgresql': {
      database: 'postgres',
      ssl_mode: 'prefer'
    },
    'mssql': {
      database: 'master',
      driver: 'ODBC Driver 17 for SQL Server',
      encrypt: 'yes'
    },
    'oracle': {
      service_name: '',
      sid: ''
    },
    'sqlite': {
      database_path: ''
    },
    'mongodb': {
      database: 'admin',
      auth_source: 'admin'
    },
    'redis': {
      database: 0
    },
    'elasticsearch': {
      ssl: false,
      verify_certs: true
    }
  };
  return configs[methodType] || {};
};

/**
 * Get status options
 */
export const getStatusOptions = () => [
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
  { value: 'maintenance', label: 'Maintenance' }
];