/**
 * Network Discovery Service
 * Handles API calls for network discovery functionality
 */

import apiService from './apiService';

class DiscoveryService {
  constructor() {
    this.baseUrl = process.env.REACT_APP_API_URL ? `${process.env.REACT_APP_API_URL}/discovery` : '/discovery';
  }

  // Discovery Jobs
  async createDiscoveryJob(jobData) {
    try {
      const response = await apiService.post(`${this.baseUrl}/jobs`, jobData);
      return await response.json();
    } catch (error) {
      console.error('Error creating discovery job:', error);
      throw error;
    }
  }

  async getDiscoveryJobs(params = {}) {
    try {
      const queryParams = new URLSearchParams();
      if (params.skip) queryParams.append('skip', params.skip);
      if (params.limit) queryParams.append('limit', params.limit);
      if (params.status) queryParams.append('status_filter', params.status);

      const response = await apiService.get(`${this.baseUrl}/jobs?${queryParams}`);
      return await response.json();
    } catch (error) {
      console.error('Error fetching discovery jobs:', error);
      throw error;
    }
  }

  async getDiscoveryJob(jobId) {
    try {
      const response = await apiService.get(`${this.baseUrl}/jobs/${jobId}`);
      return await response.json();
    } catch (error) {
      console.error('Error fetching discovery job:', error);
      throw error;
    }
  }

  async updateDiscoveryJob(jobId, jobData) {
    try {
      const response = await apiService.put(`${this.baseUrl}/jobs/${jobId}`, jobData);
      return await response.json();
    } catch (error) {
      console.error('Error updating discovery job:', error);
      throw error;
    }
  }

  async deleteDiscoveryJob(jobId) {
    try {
      await apiService.delete(`${this.baseUrl}/jobs/${jobId}`);
      return true;
    } catch (error) {
      console.error('Error deleting discovery job:', error);
      throw error;
    }
  }

  async runDiscoveryJob(jobId) {
    try {
      const response = await apiService.post(`${this.baseUrl}/jobs/${jobId}/run`);
      return await response.json();
    } catch (error) {
      console.error('Error running discovery job:', error);
      throw error;
    }
  }

  async cancelDiscoveryJob(jobId) {
    try {
      const response = await apiService.post(`${this.baseUrl}/jobs/${jobId}/cancel`);
      return await response.json();
    } catch (error) {
      console.error('Error cancelling discovery job:', error);
      throw error;
    }
  }

  // Discovered Devices
  async getDiscoveredDevices(params = {}) {
    try {
      const queryParams = new URLSearchParams();
      if (params.jobId) queryParams.append('job_id', params.jobId);
      if (params.status) queryParams.append('status_filter', params.status);
      if (params.deviceType) queryParams.append('device_type', params.deviceType);
      if (params.skip) queryParams.append('skip', params.skip);
      if (params.limit) queryParams.append('limit', params.limit);

      const response = await apiService.get(`${this.baseUrl}/devices?${queryParams}`);
      return await response.json();
    } catch (error) {
      console.error('Error fetching discovered devices:', error);
      throw error;
    }
  }

  async getDiscoveredDevice(deviceId) {
    try {
      const response = await apiService.get(`${this.baseUrl}/devices/${deviceId}`);
      return await response.json();
    } catch (error) {
      console.error('Error fetching discovered device:', error);
      throw error;
    }
  }

  async updateDiscoveredDeviceStatus(deviceId, status) {
    try {
      const response = await apiService.put(`${this.baseUrl}/devices/${deviceId}/status`, { status });
      return await response.json();
    } catch (error) {
      console.error('Error updating device status:', error);
      throw error;
    }
  }

  async getImportableDevices(jobId = null, params = {}) {
    try {
      const queryParams = new URLSearchParams();
      if (jobId) queryParams.append('job_id', jobId);
      if (params.deviceType) queryParams.append('device_type', params.deviceType);
      if (params.skip) queryParams.append('skip', params.skip);
      if (params.limit) queryParams.append('limit', params.limit);

      const response = await apiService.get(`${this.baseUrl}/devices/importable?${queryParams}`);
      return await response.json();
    } catch (error) {
      console.error('Error fetching importable devices:', error);
      throw error;
    }
  }

  // Run in-memory discovery (no persistence) using Celery
  async runInMemoryDiscovery(discoveryConfig, progressCallback = null) {
    try {
      if (progressCallback) {
        progressCallback(0, 'Starting discovery task...');
      }
      
      // Start the Celery task
      const startResponse = await apiService.post(`${this.baseUrl}/discover-memory`, discoveryConfig);
      const taskData = await startResponse.json();
      
      if (!taskData.task_id) {
        throw new Error('Failed to start discovery task');
      }
      
      if (progressCallback) {
        progressCallback(5, 'Discovery task started, scanning network...');
      }
      
      // Poll for results
      return await this.pollDiscoveryTask(taskData.task_id, progressCallback);
      
    } catch (error) {
      console.error('Error running in-memory discovery:', error);
      throw error;
    }
  }

  // Poll discovery task for completion
  async pollDiscoveryTask(taskId, progressCallback = null) {
    const maxAttempts = 300; // 5 minutes max (300 * 1 second) for large network scans
    let attempts = 0;
    
    while (attempts < maxAttempts) {
      try {
        const response = await apiService.get(`${this.baseUrl}/discover-memory/${taskId}`);
        const result = await response.json();
        
        console.log(`Discovery poll attempt ${attempts + 1}: Status=${result.status}, Progress=${result.progress}`);
        
        if (progressCallback) {
          const progress = result.progress || 0;
          const message = result.message || 'Discovery in progress...';
          progressCallback(progress, message);
        }
        
        if (result.status === 'completed') {
          console.log('Discovery completed, returning devices:', result.devices);
          return result.devices || [];
        } else if (result.status === 'failed') {
          throw new Error(result.error || 'Discovery task failed');
        }
        
        // Wait 1 second before next poll
        await new Promise(resolve => setTimeout(resolve, 1000));
        attempts++;
        
      } catch (error) {
        console.error(`Error polling discovery task (attempt ${attempts + 1}):`, error);
        throw error;
      }
    }
    
    throw new Error('Discovery task timed out');
  }

  async importDiscoveredDevices(importData) {
    try {
      const response = await apiService.post(`${this.baseUrl}/devices/import`, importData);
      return await response.json();
    } catch (error) {
      console.error('Error importing devices:', error);
      throw error;
    }
  }

  async importConfiguredDevices(importData) {
    try {
      const response = await apiService.post(`${this.baseUrl}/devices/import-configured`, importData);
      return await response.json();
    } catch (error) {
      console.error('Error importing configured devices:', error);
      throw error;
    }
  }

  async importInMemoryDevices(importData) {
    try {
      const response = await apiService.post(`${this.baseUrl}/devices/import-memory`, importData);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error importing in-memory devices:', error);
      throw error;
    }
  }

  // Discovery Templates
  async createDiscoveryTemplate(templateData) {
    try {
      const response = await apiService.post(`${this.baseUrl}/templates`, templateData);
      return await response.json();
    } catch (error) {
      console.error('Error creating discovery template:', error);
      throw error;
    }
  }

  async getDiscoveryTemplates(activeOnly = true) {
    try {
      const response = await apiService.get(`${this.baseUrl}/templates?active_only=${activeOnly}`);
      return await response.json();
    } catch (error) {
      console.error('Error fetching discovery templates:', error);
      throw error;
    }
  }

  async getDiscoveryTemplate(templateId) {
    try {
      const response = await apiService.get(`${this.baseUrl}/templates/${templateId}`);
      return await response.json();
    } catch (error) {
      console.error('Error fetching discovery template:', error);
      throw error;
    }
  }

  // Statistics and Quick Scan
  async getDiscoveryStats() {
    try {
      const response = await apiService.get(`${this.baseUrl}/stats`);
      return await response.json();
    } catch (error) {
      console.error('Error fetching discovery stats:', error);
      throw error;
    }
  }

  async quickNetworkScan(scanData) {
    try {
      const response = await apiService.post(`${this.baseUrl}/scan`, scanData);
      return await response.json();
    } catch (error) {
      console.error('Error performing quick scan:', error);
      throw error;
    }
  }

  // Utility methods
  getDeviceTypeIcon(deviceType) {
    const iconMap = {
      'linux': '🐧',
      'windows': '🪟',
      'windows_desktop': '💻',
      'windows_server': '🖥️',
      'cisco_switch': '🔀',
      'cisco_router': '📡',
      'proxmox': '☁️',
      'vmware_esxi': '☁️',
      'mysql': '🗄️',
      'postgresql': '🗄️',
      'apache': '🌐',
      'nginx': '🌐',
      'smtp_server': '📧',
      'generic_device': '📱',
      'network_device': '🔌',
      'storage_device': '💾',
      'printer': '🖨️',
      'camera': '📷',
      'iot_device': '🏠'
    };
    return iconMap[deviceType] || '❓';
  }

  getDeviceTypeColor(deviceType) {
    const colorMap = {
      'linux': '#FD7E14',
      'windows': '#0EA5E9',
      'windows_desktop': '#3B82F6',
      'windows_server': '#1E40AF',
      'cisco_switch': '#10B981',
      'cisco_router': '#059669',
      'proxmox': '#F59E0B',
      'vmware_esxi': '#EF4444',
      'mysql': '#3B82F6',
      'postgresql': '#6366F1',
      'apache': '#DC2626',
      'nginx': '#059669',
      'smtp_server': '#F59E0B',
      'generic_device': '#6B7280',
      'network_device': '#8B5CF6',
      'storage_device': '#EC4899',
      'printer': '#F59E0B',
      'camera': '#10B981',
      'iot_device': '#8B5CF6'
    };
    return colorMap[deviceType] || '#6B7280';
  }

  getStatusColor(status) {
    const colorMap = {
      'pending': '#F59E0B',
      'running': '#3B82F6',
      'completed': '#10B981',
      'failed': '#EF4444',
      'cancelled': '#6B7280',
      'discovered': '#3B82F6',
      'imported': '#10B981',
      'ignored': '#6B7280'
    };
    return colorMap[status] || '#6B7280';
  }

  formatDiscoveryTime(timestamp) {
    if (!timestamp) return 'Unknown';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
  }

  validateNetworkRange(networkRange) {
    // Basic CIDR validation
    const cidrRegex = /^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/;
    if (!cidrRegex.test(networkRange)) {
      return false;
    }

    const [ip, prefix] = networkRange.split('/');
    const prefixNum = parseInt(prefix);
    
    // Validate prefix
    if (prefixNum < 0 || prefixNum > 32) {
      return false;
    }

    // Validate IP octets
    const octets = ip.split('.');
    for (const octet of octets) {
      const num = parseInt(octet);
      if (num < 0 || num > 255) {
        return false;
      }
    }

    return true;
  }

  validatePortRange(portRange) {
    if (!Array.isArray(portRange) || portRange.length !== 2) {
      return false;
    }

    const [start, end] = portRange;
    return start >= 1 && start <= 65535 && end >= 1 && end <= 65535 && start <= end;
  }

  getCommonPortPresets() {
    return {
      'basic': {
        name: 'Basic Services',
        ports: [22, 23, 25, 53, 80, 110, 143, 443, 993, 995]
      },
      'windows': {
        name: 'Windows Services',
        ports: [135, 139, 445, 3389, 5985, 5986]
      },
      'network': {
        name: 'Network Infrastructure',
        ports: [22, 23, 80, 161, 162, 443, 514, 8080, 8443]
      },
      'database': {
        name: 'Database Services',
        ports: [1433, 1521, 3306, 5432, 27017, 6379]
      },
      'virtualization': {
        name: 'Virtualization',
        ports: [22, 80, 443, 902, 8006, 8080, 9443]
      },
      'comprehensive': {
        name: 'Comprehensive Scan',
        ports: [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 161, 443, 445, 993, 995, 1433, 3306, 3389, 5432, 5985, 8080, 8443]
      }
    };
  }
}

export default new DiscoveryService();