import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || '',  // Use relative URLs to avoid origin issues
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refresh_token = localStorage.getItem('refresh_token');
        if (!refresh_token) {
          throw new Error('No refresh token');
        }

        const response = await axios.post(
          `${process.env.REACT_APP_API_URL || ''}/auth/refresh`,
          {},
          {
            headers: {
              Authorization: `Bearer ${refresh_token}`,
            },
          }
        );

        const { access_token, refresh_token: new_refresh_token } = response.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', new_refresh_token);

        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export const authService = {
  // Expose the api instance for direct use
  api,

  // Login user
  async login(username, password) {
    console.log('Making login request to:', '/auth/login');
    console.log('Base URL:', api.defaults.baseURL);
    console.log('Window location:', window.location.origin);
    const response = await api.post('/auth/login', {
      username,
      password,
    });
    return response.data;
  },

  // Logout user
  async logout() {
    const response = await api.post('/auth/logout');
    return response.data;
  },

  // Refresh token
  async refreshToken(refresh_token) {
    const response = await api.post('/auth/refresh', {}, {
      headers: {
        Authorization: `Bearer ${refresh_token}`,
      },
    });
    return response.data;
  },

  // Get current user info
  async getCurrentUser() {
    const response = await api.get('/auth/me');
    return response.data;
  },
}; 