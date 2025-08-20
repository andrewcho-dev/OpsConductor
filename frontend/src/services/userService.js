import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || '',
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
      console.log('🚪 Session expired in userService, redirecting to login...');

      // Clear tokens and redirect to login (no refresh tokens in session-based auth)
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token'); // Remove any old refresh tokens
      window.location.href = '/login';
      return Promise.reject(error);
    }

    return Promise.reject(error);
  }
);

export const userService = {
  // Get all users
  async getUsers(skip = 0, limit = 100) {
    console.log('Making request to:', '/users/', 'with baseURL:', api.defaults.baseURL);
    const response = await api.get('/users/', {
      params: { skip, limit },
    });
    return response.data;
  },

  // Get user by ID
  async getUserById(userId) {
    const response = await api.get(`/users/${userId}`);
    return response.data;
  },

  // Create new user
  async createUser(userData) {
    const response = await api.post('/users/', userData);
    return response.data;
  },

  // Update user
  async updateUser(userId, userData) {
    const response = await api.put(`/users/${userId}`, userData);
    return response.data;
  },

  // Delete user
  async deleteUser(userId) {
    const response = await api.delete(`/users/${userId}`);
    return response.data;
  },

  // Get user sessions
  async getUserSessions(userId) {
    const response = await api.get(`/users/${userId}/sessions`);
    return response.data;
  },
}; 