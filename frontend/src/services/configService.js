import { apiService } from './apiService';

/**
 * Configuration Service
 * Handles authentication configuration management
 */
class ConfigService {
  constructor() {
    this.baseUrl = '/api/config';
  }

  /**
   * Get complete configuration (all categories)
   */
  async getAllConfiguration() {
    try {
      const response = await apiService.get(this.baseUrl);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch complete configuration:', error);
      throw error;
    }
  }

  /**
   * Get session management configuration
   */
  async getSessionConfig() {
    try {
      const response = await apiService.get(`${this.baseUrl}/session`);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch session configuration:', error);
      throw error;
    }
  }

  /**
   * Get password policy configuration
   */
  async getPasswordPolicy() {
    try {
      const response = await apiService.get(`${this.baseUrl}/password`);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch password policy:', error);
      throw error;
    }
  }

  /**
   * Get security configuration
   */
  async getSecurityConfig() {
    try {
      const response = await apiService.get(`${this.baseUrl}/security`);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch security configuration:', error);
      throw error;
    }
  }

  /**
   * Get audit configuration
   */
  async getAuditConfig() {
    try {
      const response = await apiService.get(`${this.baseUrl}/audit`);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch audit configuration:', error);
      throw error;
    }
  }

  /**
   * Get user management configuration
   */
  async getUserManagementConfig() {
    try {
      const response = await apiService.get(`${this.baseUrl}/users`);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch user management configuration:', error);
      throw error;
    }
  }

  /**
   * Update session configuration
   */
  async updateSessionConfig(config) {
    try {
      const response = await apiService.put(`${this.baseUrl}/session`, config);
      return await response.json();
    } catch (error) {
      console.error('Failed to update session configuration:', error);
      throw error;
    }
  }

  /**
   * Update password policy
   */
  async updatePasswordPolicy(policy) {
    try {
      const response = await apiService.put(`${this.baseUrl}/password`, policy);
      return await response.json();
    } catch (error) {
      console.error('Failed to update password policy:', error);
      throw error;
    }
  }

  /**
   * Update security configuration
   */
  async updateSecurityConfig(config) {
    try {
      const response = await apiService.put(`${this.baseUrl}/security`, config);
      return await response.json();
    } catch (error) {
      console.error('Failed to update security configuration:', error);
      throw error;
    }
  }

  /**
   * Update audit configuration
   */
  async updateAuditConfig(config) {
    try {
      const response = await apiService.put(`${this.baseUrl}/audit`, config);
      return await response.json();
    } catch (error) {
      console.error('Failed to update audit configuration:', error);
      throw error;
    }
  }

  /**
   * Update user management configuration
   */
  async updateUserManagementConfig(config) {
    try {
      const response = await apiService.put(`${this.baseUrl}/users`, config);
      return await response.json();
    } catch (error) {
      console.error('Failed to update user management configuration:', error);
      throw error;
    }
  }

  /**
   * Update multiple configuration values in batch
   */
  async updateConfigurationBatch(updates) {
    try {
      const response = await apiService.put(`${this.baseUrl}/batch`, { updates });
      return await response.json();
    } catch (error) {
      console.error('Failed to update configuration batch:', error);
      throw error;
    }
  }

  /**
   * Initialize default configuration values
   */
  async initializeDefaultConfig() {
    try {
      const response = await apiService.post(`${this.baseUrl}/initialize`);
      return response.ok;
    } catch (error) {
      console.error('Failed to initialize default configuration:', error);
      throw error;
    }
  }

  /**
   * Validate password against current policy
   */
  async validatePassword(password) {
    try {
      const response = await apiService.post('/api/users/validate-password', { password });
      return await response.json();
    } catch (error) {
      console.error('Failed to validate password:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const configService = new ConfigService();
export default configService;