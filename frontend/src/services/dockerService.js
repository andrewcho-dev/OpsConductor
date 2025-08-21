/**
 * Docker Service
 * API service for Docker environment monitoring and management
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
    console.error('Docker API Error Response:', errorData);
    
    if (errorData.detail) {
      if (Array.isArray(errorData.detail)) {
        const errors = errorData.detail.map(err => `${err.loc.join('.')}: ${err.msg}`).join(', ');
        throw new Error(errors);
      } else {
        throw new Error(errorData.detail);
      }
    } else if (errorData.message) {
      throw new Error(errorData.message);
    } else {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
  }
  return response.json();
};

class DockerService {
  constructor() {
    this.baseUrl = `${API_BASE_URL}/docker`;
  }

  // Get all containers
  async getContainers() {
    try {
      const response = await fetch(`${this.baseUrl}/containers?all=true`, {
        method: 'GET',
        headers: getAuthHeaders()
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Failed to fetch containers:', error);
      return [];
    }
  }

  // Get container stats
  async getContainerStats(containerId) {
    try {
      const response = await fetch(`${this.baseUrl}/containers/${containerId}/stats`, {
        method: 'GET',
        headers: getAuthHeaders()
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Failed to fetch container stats:', error);
      return null;
    }
  }

  // Get all volumes
  async getVolumes() {
    try {
      const response = await fetch(`${this.baseUrl}/volumes`, {
        method: 'GET',
        headers: getAuthHeaders()
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Failed to fetch volumes:', error);
      return [];
    }
  }

  // Get all networks
  async getNetworks() {
    try {
      const response = await fetch(`${this.baseUrl}/networks`, {
        method: 'GET',
        headers: getAuthHeaders()
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Failed to fetch networks:', error);
      return [];
    }
  }

  // Get system info
  async getSystemInfo() {
    try {
      const response = await fetch(`${this.baseUrl}/system/info`, {
        method: 'GET',
        headers: getAuthHeaders()
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Failed to fetch system info:', error);
      return null;
    }
  }

  // Container actions
  async startContainer(containerId) {
    try {
      const response = await fetch(`${this.baseUrl}/containers/${containerId}/start`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      const data = await handleResponse(response);
      return data.success;
    } catch (error) {
      console.error('Failed to start container:', error);
      return false;
    }
  }

  async stopContainer(containerId) {
    try {
      const response = await fetch(`${this.baseUrl}/containers/${containerId}/stop`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      const data = await handleResponse(response);
      return data.success;
    } catch (error) {
      console.error('Failed to stop container:', error);
      return false;
    }
  }

  async restartContainer(containerId) {
    try {
      const response = await fetch(`${this.baseUrl}/containers/${containerId}/restart`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      const data = await handleResponse(response);
      return data.success;
    } catch (error) {
      console.error('Failed to restart container:', error);
      return false;
    }
  }

  async removeContainer(containerId) {
    try {
      const response = await fetch(`${this.baseUrl}/containers/${containerId}?force=true`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });
      const data = await handleResponse(response);
      return data.success;
    } catch (error) {
      console.error('Failed to remove container:', error);
      return false;
    }
  }

  // Get container logs
  async getContainerLogs(containerId, tail = 100) {
    try {
      const response = await fetch(`${this.baseUrl}/containers/${containerId}/logs?tail=${tail}`, {
        method: 'GET',
        headers: getAuthHeaders()
      });
      const data = await handleResponse(response);
      return data.logs;
    } catch (error) {
      console.error('Failed to fetch container logs:', error);
      return '';
    }
  }

  // Get Docker status
  async getDockerStatus() {
    try {
      const response = await fetch(`${this.baseUrl}/status`, {
        method: 'GET',
        headers: getAuthHeaders()
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Failed to fetch Docker status:', error);
      return { status: 'error', message: 'Failed to connect to Docker API' };
    }
  }

  // Format bytes to human readable
  formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  // Format container status
  formatContainerStatus(container) {
    const state = container.State;
    const status = container.Status;
    
    return {
      state: state,
      status: status,
      isRunning: state === 'running',
      color: state === 'running' ? 'success' : 
             state === 'exited' ? 'error' : 
             state === 'paused' ? 'warning' : 'default'
    };
  }
}

export default new DockerService();