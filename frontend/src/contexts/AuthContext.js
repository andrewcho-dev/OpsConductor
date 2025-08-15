import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('access_token'));

  useEffect(() => {
    // Check if user is already logged in (check localStorage for token)
    const storedToken = localStorage.getItem('access_token');
    if (storedToken) {
      setToken(storedToken);
      authService.getCurrentUser()
        .then(userData => {
          setUser(userData);
          setIsAuthenticated(true);
        })
        .catch(() => {
          // Token is invalid, clear it
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          setToken(null);
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }

    // Listen for force logout events from API service
    const handleForceLogout = () => {
      console.log('🚪 Received force logout event, clearing auth state...');
      setToken(null);
      setUser(null);
      setIsAuthenticated(false);
    };

    window.addEventListener('forceLogout', handleForceLogout);
    
    // Set up periodic token validation (every 5 minutes)
    const tokenCheckInterval = setInterval(() => {
      const currentToken = localStorage.getItem('access_token');
      if (currentToken && isAuthenticated) {
        // Try to decode the JWT to check expiration
        try {
          const payload = JSON.parse(atob(currentToken.split('.')[1]));
          const currentTime = Math.floor(Date.now() / 1000);
          
          // If token expires in less than 5 minutes, try to refresh
          if (payload.exp && payload.exp - currentTime < 300) {
            console.log('🔄 Token expiring soon, attempting refresh...');
            authService.getCurrentUser().catch(() => {
              console.log('🚪 Token refresh failed, forcing logout...');
              handleForceLogout();
              window.location.href = '/login';
            });
          }
        } catch (error) {
          console.log('🚪 Invalid token format, forcing logout...');
          handleForceLogout();
          window.location.href = '/login';
        }
      }
    }, 5 * 60 * 1000); // Check every 5 minutes
    
    return () => {
      window.removeEventListener('forceLogout', handleForceLogout);
      clearInterval(tokenCheckInterval);
    };
  }, [isAuthenticated]);

  const login = async (username, password) => {
    try {
      console.log('Starting login process...');
      const response = await authService.login(username, password);
      console.log('Login response:', response);
      const { access_token, refresh_token } = response;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      setToken(access_token);
      console.log('Tokens stored, getting user data...');
      
      const userData = await authService.getCurrentUser();
      console.log('User data:', userData);
      setUser(userData);
      setIsAuthenticated(true);
      
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || error.message || 'Login failed' 
      };
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setToken(null);
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  const refreshToken = async () => {
    try {
      const refresh_token = localStorage.getItem('refresh_token');
      if (!refresh_token) {
        throw new Error('No refresh token available');
      }

      const response = await authService.refreshToken(refresh_token);
      const { access_token, refresh_token: new_refresh_token } = response;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', new_refresh_token);
      setToken(access_token);
      
      return { success: true };
    } catch (error) {
      // Refresh failed, logout user
      await logout();
      return { success: false };
    }
  };

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    logout,
    refreshToken,
    token
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 