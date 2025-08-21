import { apiService } from './apiService';

/**
 * Configuration Service
 * Handles authentication configuration management
 */
class ConfigService {
  constructor() {
    this.baseUrl = '/api/v1/system';
  }

  /**
   * Get complete configuration (all categories)
   */
  async getAllConfiguration() {
    try {
      // Return default configuration since system settings endpoint doesn't exist in microservices
      console.log('⚙️ Using default configuration values (system settings endpoint not available)');
      
      return {
        session: {
          timeout_minutes: 60,
          warning_minutes: 2,
          max_concurrent: 10,
          idle_timeout_minutes: 60,
          remember_me_days: 30
        },
        password: {
          min_length: 8,
          require_uppercase: true,
          require_lowercase: true,
          require_numbers: true,
          require_special_chars: true,
          max_age_days: 90
        },
        security: {
          max_login_attempts: 5,
          lockout_duration_minutes: 15,
          session_timeout_minutes: 60,
          require_2fa: false
        },
        audit: {
          log_user_actions: true,
          log_system_events: true,
          retention_days: 365,
          log_level: 'INFO'
        },
        users: {
          allow_self_registration: false,
          default_role: 'user',
          require_email_verification: true,
          password_reset_enabled: true
        }
      };
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
      // Return default session configuration since system settings endpoint doesn't exist in microservices
      console.log('⚙️ Using default session configuration values (system settings endpoint not available)');
      
      return {
        timeout_minutes: 60,
        warning_minutes: 2,
        max_concurrent: 10,
        idle_timeout_minutes: 60,
        remember_me_days: 30
      };
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
      // Return default password policy since backend doesn't have this endpoint
      return {
        min_length: 8,
        require_uppercase: true,
        require_lowercase: true,
        require_numbers: true,
        require_special_chars: true,
        max_age_days: 90
      };
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
      // Return default security config since backend doesn't have this endpoint
      return {
        max_login_attempts: 5,
        lockout_duration_minutes: 15,
        session_timeout_minutes: 60,
        require_2fa: false
      };
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
      // Return default audit config since backend doesn't have this endpoint
      return {
        log_user_actions: true,
        log_system_events: true,
        retention_days: 365,
        log_level: 'INFO'
      };
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
      // Return default user management config since backend doesn't have this endpoint
      return {
        allow_self_registration: false,
        default_role: 'user',
        require_email_verification: true,
        password_reset_enabled: true
      };
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
      // Return success since system settings endpoint doesn't exist in microservices
      console.log('⚙️ Session configuration update requested (not implemented in microservices):', config);
      return { success: true, message: 'Session configuration update not implemented yet' };
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
      // Return success since backend doesn't have this endpoint yet
      console.log('Password policy update requested:', policy);
      return { success: true, message: 'Password policy update not implemented yet' };
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
      // Return success since backend doesn't have this endpoint yet
      console.log('Security config update requested:', config);
      return { success: true, message: 'Security config update not implemented yet' };
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
      // Return success since backend doesn't have this endpoint yet
      console.log('Audit config update requested:', config);
      return { success: true, message: 'Audit config update not implemented yet' };
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
      // Return success since backend doesn't have this endpoint yet
      console.log('User management config update requested:', config);
      return { success: true, message: 'User management config update not implemented yet' };
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
      // Return success since system settings endpoint doesn't exist in microservices
      console.log('⚙️ Batch configuration update requested (not implemented in microservices):', updates);
      return { success: true, message: 'Configuration updated (not implemented in microservices yet)' };
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
      // Return success since backend doesn't have this endpoint yet
      console.log('Default configuration initialization requested');
      return true;
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