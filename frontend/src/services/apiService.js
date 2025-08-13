/**
 * Centralized API service with automatic token refresh and logout handling
 * All components should use this instead of direct fetch() calls
 */

class ApiService {
  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || '';
  }

  async makeRequest(url, options = {}) {
    const token = localStorage.getItem('access_token');
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers
      },
      ...options
    };

    try {
      // If URL already starts with /api/, use it directly without baseURL
      const fullUrl = url.startsWith('/api/') ? url : `${this.baseURL}${url}`;
      const response = await fetch(fullUrl, config);
      
      // If we get a 401, try to refresh the token
      if (response.status === 401 && !options._retry) {
        console.log('🔄 Got 401, attempting token refresh...');
        const refreshSuccess = await this.refreshToken();
        
        if (refreshSuccess) {
          // Retry the original request with new token
          const newToken = localStorage.getItem('access_token');
          const retryConfig = {
            ...config,
            headers: {
              ...config.headers,
              'Authorization': `Bearer ${newToken}`
            },
            _retry: true // Prevent infinite retry loops
          };
          
          console.log('🔄 Retrying request with new token...');
          return await fetch(fullUrl, retryConfig);
        } else {
          // Refresh failed, force logout
          console.log('❌ Token refresh failed, logging out...');
          this.forceLogout();
          throw new Error('Authentication failed');
        }
      }
      
      return response;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  async refreshToken() {
    try {
      const refresh_token = localStorage.getItem('refresh_token');
      if (!refresh_token) {
        console.log('❌ No refresh token available');
        return false;
      }

      console.log('🔄 Attempting to refresh token...');
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${refresh_token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        console.log('✅ Token refreshed successfully');
        return true;
      } else {
        console.log('❌ Token refresh failed:', response.status);
        return false;
      }
    } catch (error) {
      console.error('❌ Token refresh error:', error);
      return false;
    }
  }

  forceLogout() {
    console.log('🚪 Forcing logout due to authentication failure...');
    
    // Clear tokens
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    
    // Dispatch a custom event that the AuthContext can listen to
    window.dispatchEvent(new CustomEvent('forceLogout'));
    
    // Immediately redirect to login - don't wait
    if (window.location.pathname !== '/login') {
      console.log('🔄 Redirecting to login page...');
      window.location.href = '/login';
    }
  }

  // Convenience methods for common HTTP verbs
  async get(url, options = {}) {
    return this.makeRequest(url, { method: 'GET', ...options });
  }

  async post(url, data, options = {}) {
    return this.makeRequest(url, {
      method: 'POST',
      body: JSON.stringify(data),
      ...options
    });
  }

  async put(url, data, options = {}) {
    return this.makeRequest(url, {
      method: 'PUT',
      body: JSON.stringify(data),
      ...options
    });
  }

  async delete(url, options = {}) {
    return this.makeRequest(url, { method: 'DELETE', ...options });
  }
}

// Export a singleton instance
export const apiService = new ApiService();
export default apiService;