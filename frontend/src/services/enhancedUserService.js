import { apiService } from './apiService';

/**
 * Enhanced User Service
 * Handles comprehensive user management operations
 */
class EnhancedUserService {
  constructor() {
    this.baseUrl = '/api/users';
  }

  /**
   * Get paginated list of users with filtering and sorting
   */
  async getUsers(params = {}) {
    try {
      const queryParams = new URLSearchParams();
      
      // Add pagination parameters
      if (params.skip !== undefined) queryParams.append('skip', params.skip);
      if (params.limit !== undefined) queryParams.append('limit', params.limit);
      
      // Add filtering parameters
      if (params.search) queryParams.append('search', params.search);
      if (params.role) queryParams.append('role', params.role);
      if (params.active_only !== undefined) queryParams.append('active_only', params.active_only);
      
      // Add sorting parameters
      if (params.sort_by) queryParams.append('sort_by', params.sort_by);
      if (params.sort_desc !== undefined) queryParams.append('sort_desc', params.sort_desc);
      
      const url = queryParams.toString() ? `${this.baseUrl}?${queryParams}` : this.baseUrl;
      const response = await apiService.get(url);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch users:', error);
      throw error;
    }
  }

  /**
   * Get comprehensive user statistics
   */
  async getUserStats() {
    try {
      const response = await apiService.get(`${this.baseUrl}/stats`);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch user statistics:', error);
      throw error;
    }
  }

  /**
   * Get user by ID
   */
  async getUserById(userId) {
    try {
      const response = await apiService.get(`${this.baseUrl}/${userId}`);
      return await response.json();
    } catch (error) {
      console.error(`Failed to fetch user ${userId}:`, error);
      throw error;
    }
  }

  /**
   * Get detailed user activity information
   */
  async getUserActivity(userId, limit = 50) {
    try {
      const response = await apiService.get(`${this.baseUrl}/${userId}/activity?limit=${limit}`);
      return await response.json();
    } catch (error) {
      console.error(`Failed to fetch user activity for ${userId}:`, error);
      throw error;
    }
  }

  /**
   * Create a new user
   */
  async createUser(userData) {
    try {
      const response = await apiService.post(this.baseUrl, userData);
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create user');
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to create user:', error);
      throw error;
    }
  }

  /**
   * Update user information
   */
  async updateUser(userId, userData) {
    try {
      const response = await apiService.put(`${this.baseUrl}/${userId}`, userData);
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update user');
      }
      return await response.json();
    } catch (error) {
      console.error(`Failed to update user ${userId}:`, error);
      throw error;
    }
  }

  /**
   * Delete user (soft delete)
   */
  async deleteUser(userId) {
    try {
      const response = await apiService.delete(`${this.baseUrl}/${userId}`);
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete user');
      }
      return true;
    } catch (error) {
      console.error(`Failed to delete user ${userId}:`, error);
      throw error;
    }
  }

  /**
   * Change user password
   */
  async changeUserPassword(userId, passwordData) {
    try {
      const response = await apiService.put(`${this.baseUrl}/${userId}/password`, passwordData);
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to change password');
      }
      return true;
    } catch (error) {
      console.error(`Failed to change password for user ${userId}:`, error);
      throw error;
    }
  }

  /**
   * Perform bulk actions on multiple users
   */
  async bulkUserAction(actionData) {
    try {
      const response = await apiService.post(`${this.baseUrl}/bulk-action`, actionData);
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to perform bulk action');
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to perform bulk action:', error);
      throw error;
    }
  }

  /**
   * Validate password against current policy
   */
  async validatePassword(password) {
    try {
      const response = await apiService.post(`${this.baseUrl}/validate-password`, { password });
      return await response.json();
    } catch (error) {
      console.error('Failed to validate password:', error);
      throw error;
    }
  }

  /**
   * Lock user account
   */
  async lockUser(userId, reason = '') {
    return this.bulkUserAction({
      user_ids: [userId],
      action: 'lock',
      reason
    });
  }

  /**
   * Unlock user account
   */
  async unlockUser(userId, reason = '') {
    return this.bulkUserAction({
      user_ids: [userId],
      action: 'unlock',
      reason
    });
  }

  /**
   * Activate user account
   */
  async activateUser(userId, reason = '') {
    return this.bulkUserAction({
      user_ids: [userId],
      action: 'activate',
      reason
    });
  }

  /**
   * Deactivate user account
   */
  async deactivateUser(userId, reason = '') {
    return this.bulkUserAction({
      user_ids: [userId],
      action: 'deactivate',
      reason
    });
  }

  /**
   * Force password change for user
   */
  async forcePasswordChange(userId, reason = '') {
    return this.bulkUserAction({
      user_ids: [userId],
      action: 'force_password_change',
      reason
    });
  }

  /**
   * Get user roles for dropdown/selection
   */
  getUserRoles() {
    return [
      { value: 'user', label: 'User', description: 'Standard user with basic permissions' },
      { value: 'manager', label: 'Manager', description: 'Manager with elevated permissions' },
      { value: 'administrator', label: 'Administrator', description: 'Full system administrator' }
    ];
  }

  /**
   * Get bulk action options
   */
  getBulkActions() {
    return [
      { value: 'activate', label: 'Activate', description: 'Activate selected users' },
      { value: 'deactivate', label: 'Deactivate', description: 'Deactivate selected users' },
      { value: 'lock', label: 'Lock', description: 'Lock selected user accounts' },
      { value: 'unlock', label: 'Unlock', description: 'Unlock selected user accounts' },
      { value: 'force_password_change', label: 'Force Password Change', description: 'Require password change on next login' },
      { value: 'delete', label: 'Delete', description: 'Delete selected users (soft delete)' }
    ];
  }

  /**
   * Format user status for display
   */
  formatUserStatus(user) {
    if (!user.is_active) {
      return { status: 'Inactive', color: 'error', severity: 'error' };
    }
    if (user.is_locked) {
      return { status: 'Locked', color: 'warning', severity: 'warning' };
    }
    if (!user.is_verified) {
      return { status: 'Unverified', color: 'info', severity: 'info' };
    }
    if (user.must_change_password) {
      return { status: 'Password Reset Required', color: 'warning', severity: 'warning' };
    }
    return { status: 'Active', color: 'success', severity: 'success' };
  }

  /**
   * Format user role for display
   */
  formatUserRole(role) {
    const roleMap = {
      'administrator': { label: 'Administrator', color: 'error' },
      'manager': { label: 'Manager', color: 'warning' },
      'user': { label: 'User', color: 'default' }
    };
    return roleMap[role] || { label: role, color: 'default' };
  }

  /**
   * Check if user has permission for action
   */
  canPerformAction(currentUser, targetUser, action) {
    // Administrators can perform any action
    if (currentUser.role === 'administrator') {
      return true;
    }

    // Users can only perform actions on themselves for certain operations
    if (currentUser.id === targetUser.id) {
      const selfActions = ['view', 'update_profile', 'change_password'];
      return selfActions.includes(action);
    }

    // Managers can perform limited actions on regular users
    if (currentUser.role === 'manager' && targetUser.role === 'user') {
      const managerActions = ['view', 'update', 'lock', 'unlock'];
      return managerActions.includes(action);
    }

    return false;
  }
}

// Export singleton instance
export const enhancedUserService = new EnhancedUserService();
export default enhancedUserService;