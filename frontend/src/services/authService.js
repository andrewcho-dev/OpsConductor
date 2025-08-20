import axios from 'axios';

// Create axios instance with base configuration
// Get the base URL from environment - keep it relative
const apiBaseUrl = process.env.REACT_APP_API_URL || '';
const authBaseUrl = process.env.REACT_APP_AUTH_URL || '/api/auth';

// Log the API base URL for debugging
console.log('🌐 Using API base URL:', apiBaseUrl);
console.log('🔐 Using Auth base URL:', authBaseUrl);

const api = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create separate axios instance for auth service
const authApi = axios.create({
  baseURL: authBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token and debug info
api.interceptors.request.use(
  (config) => {
    // Add authentication token
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Debug logging for API requests
    console.log(`🌐 API Request: ${config.method?.toUpperCase() || 'GET'} ${config.baseURL}${config.url}`);
    
    // No need to modify URLs - the browser will automatically use the same protocol
    // as the page when using relative URLs
    
    return config;
  },
  (error) => {
    console.error('❌ Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh and errors
api.interceptors.response.use(
  (response) => {
    // Log successful responses
    console.log(`✅ API Response: ${response.status} ${response.config.method?.toUpperCase() || 'GET'} ${response.config.url}`);
    return response;
  },
  async (error) => {
    // Log detailed error information
    console.error('❌ API Error:', error.message);
    if (error.response) {
      console.error(`❌ Status: ${error.response.status}`, error.response.data);
    } else if (error.request) {
      console.error('❌ No response received:', error.request);
      
      // Log if there might be a mixed content issue
      if (window.location.protocol === 'https:' && error.message === 'Network Error') {
        console.error(`
❌ Mixed content issue detected! 

The page is loaded over HTTPS, but API requests are being blocked because they're trying to access HTTP resources.
This is likely because the nginx proxy is forwarding requests to the backend over HTTP.

This is a server configuration issue, not a frontend code issue. The frontend is correctly using relative URLs.

To fix this, either:
1. Access the application over HTTP instead of HTTPS (for development only)
2. Configure the nginx proxy to use HTTPS for backend communication
3. Add the following meta tag to index.html to allow mixed content (not recommended for production):
   <meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">
`);
      }
    }
    
    const originalRequest = error.config;

    // Handle 401 Unauthorized errors - redirect to login (no refresh tokens in session-based auth)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      console.log('🚪 Session expired, redirecting to login...');

      // Clear tokens and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token'); // Remove any old refresh tokens
      window.location.href = '/login';
      return Promise.reject(error);
    }

    return Promise.reject(error);
  }
);

export const authService = {
  // Expose the api instance for direct use
  api,

  // Login user
  async login(username, password) {
    console.log('Making login request to:', '/login');
    console.log('Auth Base URL:', authApi.defaults.baseURL);
    console.log('Window location:', window.location.origin);
    const response = await authApi.post('/login', {
      username,
      password,
    });
    return response.data;
  },

  // Logout user
  async logout() {
    const token = localStorage.getItem('access_token');
    if (token) {
      const response = await authApi.post('/logout', {}, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      return response.data;
    }
  },

  // Session extension (replaces refresh token in session-based auth)
  async extendSession() {
    const token = localStorage.getItem('access_token');
    if (token) {
      const response = await authApi.post('/session/extend', {}, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      return response.data;
    }
    throw new Error('No access token');
  },

  // Validate token
  async validateToken(token) {
    const response = await authApi.post('/validate', { token });
    return response.data;
  },

  // AUTH CONFIGURATION METHODS (minimal - only what auth service provides)

  // Get session configuration
  async getSessionConfig() {
    const response = await authApi.get('/config/session');
    return response.data;
  },

  // Get password policy
  async getPasswordPolicy() {
    const response = await authApi.get('/config/password');
    return response.data;
  },

  // Get security configuration
  async getSecurityConfig() {
    const response = await authApi.get('/config/security');
    return response.data;
  },
}; 