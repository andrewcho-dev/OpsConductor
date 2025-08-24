import { apiService } from './apiService';

/**
 * Enhanced User Service
 * Handles comprehensive user management operations
 */
class EnhancedUserService {
  constructor() {
    this.baseUrl = '/api/v1/users/';
  }

  /**
   * Get all available roles
   */
  async getRoles() {
    try {
      const response = await apiService.get('/api/v1/roles/');
      const data = await response.json();
      return data.roles || data;
    } catch (error) {
      console.error('Failed to fetch roles:', error);
      // Return default roles if API call fails
      return [
        { id: 1, name: 'admin', display_name: 'Administrator' },
        { id: 2, name: 'user', display_name: 'User' }
      ];
    }
  }

  /**
   * Get paginated list of users with filtering and sorting
   */
  async getUsers(params = {}) {
    try {
      const queryParams = new URLSearchParams();
      
      // Convert skip/limit to page/page_size for backend compatibility
      if (params.skip !== undefined && params.limit !== undefined) {
        const page = Math.floor(params.skip / params.limit) + 1;
        queryParams.append('page', page);
        queryParams.append('page_size', params.limit);
      } else {
        // Default pagination
        queryParams.append('page', 1);
        queryParams.append('page_size', params.limit || 20);
      }
      
      // Add filtering parameters (map frontend params to backend params)
      if (params.search) queryParams.append('search', params.search);
      if (params.role_id) queryParams.append('role_id', params.role_id);
      if (params.is_active !== undefined) queryParams.append('is_active', params.is_active);
      if (params.is_verified !== undefined) queryParams.append('is_verified', params.is_verified);
      if (params.department) queryParams.append('department', params.department);
      if (params.organization) queryParams.append('organization', params.organization);
      
      // Note: Backend doesn't support sorting parameters yet
      // TODO: Add sorting support to backend API
      
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
   * Calculates stats from user data since backend doesn't have stats endpoint
   */
  async getUserStats() {
    try {
      // Fetch all users to calculate stats
      const userData = await this.getUsers({ page_size: 1000 }); // Get all users
      const users = userData.users || [];
      
      // Calculate stats
      const totalUsers = users.length;
      const activeUsers = users.filter(user => user.is_active === true).length;
      const inactiveUsers = users.filter(user => user.is_active === false).length;
      
      // Calculate recent signups (last 7 days)
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
      
      const recentSignups = users.filter(user => {
        if (!user.created_at) return false;
        const createdDate = new Date(user.created_at);
        return createdDate >= sevenDaysAgo;
      }).length;
      
      return {
        total_users: totalUsers,
        active_users: activeUsers,
        inactive_users: inactiveUsers,
        recent_signups: recentSignups
      };
    } catch (error) {
      console.error('Failed to calculate user statistics:', error);
      // Return default stats if calculation fails
      return {
        total_users: 0,
        active_users: 0,
        inactive_users: 0,
        recent_signups: 0
      };
    }
  }

  /**
   * Get user by ID
   */
  async getUserById(userId) {
    try {
      const response = await apiService.get(`${this.baseUrl}${userId}`);
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
      const response = await apiService.get(`${this.baseUrl}${userId}/activity?limit=${limit}`);
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
      const response = await apiService.put(`${this.baseUrl}${userId}`, userData);
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
      const response = await apiService.delete(`${this.baseUrl}${userId}`);
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
      const response = await apiService.put(`${this.baseUrl}${userId}/password`, passwordData);
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
      const response = await apiService.post(`${this.baseUrl}bulk-action`, actionData);
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
      const response = await apiService.post(`${this.baseUrl}validate-password`, { password });
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
    const currentUserRole = currentUser.role?.name || currentUser.role;
    const targetUserRole = targetUser.role?.name || targetUser.role;
    
    // Administrators can perform any action
    if (currentUserRole === 'administrator' || currentUserRole === 'admin') {
      return true;
    }

    // Users can only perform actions on themselves for certain operations
    if (currentUser.id === targetUser.id) {
      const selfActions = ['view', 'update_profile', 'change_password'];
      return selfActions.includes(action);
    }

    // Managers can perform limited actions on regular users
    if (currentUserRole === 'manager' && targetUserRole === 'user') {
      const managerActions = ['view', 'update', 'lock', 'unlock'];
      return managerActions.includes(action);
    }

    return false;
  }
}

// Export singleton instance
export const enhancedUserService = new EnhancedUserService();
export default enhancedUserService;