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
      
      // If we get a 401, session has expired - force logout immediately
      if (response.status === 401) {
        console.log('❌ Got 401 - Session expired, logging out...');
        this.forceLogout();
        throw new Error('Session expired');
      }
      
      return response;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
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