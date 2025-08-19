import React, { createContext, useContext, useState, useEffect } from 'react';
import { sessionService } from '../services/sessionService';
import SessionWarningModal from '../components/auth/SessionWarningModal';

const SessionAuthContext = createContext();

export const useSessionAuth = () => {
  const context = useContext(SessionAuthContext);
  if (!context) {
    throw new Error('useSessionAuth must be used within a SessionAuthProvider');
  }
  return context;
};

export const SessionAuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [sessionWarning, setSessionWarning] = useState({
    show: false,
    timeRemaining: 0
  });

  useEffect(() => {
    // Initialize session service
    const initializeAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const apiUrl = process.env.REACT_APP_API_URL || '/api/v3';
          const response = await fetch(`${apiUrl}/auth/me`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });

          if (response.ok) {
            const userData = await response.json();
            setUser(userData);
            setIsAuthenticated(true);
            sessionService.setSessionId(userData.session_info?.session_id);
          } else {
            // Token is invalid
            localStorage.removeItem('access_token');
          }
        } catch (error) {
          console.error('Auth initialization error:', error);
          localStorage.removeItem('access_token');
        }
      }
      setLoading(false);
    };

    initializeAuth();

    // Set up session event listeners
    const handleSessionWarning = (data) => {
      setSessionWarning({
        show: true,
        timeRemaining: data.timeRemaining
      });
    };

    const handleSessionTimeout = () => {
      handleLogout();
    };

    const handleSessionExtend = () => {
      setSessionWarning({ show: false, timeRemaining: 0 });
    };

    sessionService.addEventListener('warning', handleSessionWarning);
    sessionService.addEventListener('timeout', handleSessionTimeout);
    sessionService.addEventListener('extend', handleSessionExtend);

    // Listen for force logout events from API service
    const handleForceLogout = () => {
      handleLogout();
    };
    
    window.addEventListener('forceLogout', handleForceLogout);

    return () => {
      sessionService.removeEventListener('warning', handleSessionWarning);
      sessionService.removeEventListener('timeout', handleSessionTimeout);
      sessionService.removeEventListener('extend', handleSessionExtend);
      window.removeEventListener('forceLogout', handleForceLogout);
    };
  }, []);

  const login = async (username, password) => {
    try {
      const apiUrl = process.env.REACT_APP_API_URL || '/api/v3';
      const response = await fetch(`${apiUrl}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        return {
          success: false,
          error: errorData.detail || 'Login failed'
        };
      }

      const data = await response.json();
      console.log('🔐 Login response data:', data);
      
      // Store token
      localStorage.setItem('access_token', data.access_token);
      
      // Set session ID
      console.log('🔑 Session ID from response:', data.session_id);
      sessionService.setSessionId(data.session_id);
      
      // Get user data
      const userResponse = await fetch(`${apiUrl}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${data.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      if (userResponse.ok) {
        const userData = await userResponse.json();
        setUser(userData);
        setIsAuthenticated(true);
        return { success: true };
      } else {
        throw new Error('Failed to get user data');
      }

    } catch (error) {
      console.error('Login error:', error);
      return {
        success: false,
        error: error.message || 'Login failed'
      };
    }
  };

  const logout = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (token) {
        const apiUrl = process.env.REACT_APP_API_URL || '/api/v3';
        await fetch(`${apiUrl}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      handleLogout();
    }
  };

  const handleLogout = (forceLogout = true) => {
    console.log(`🔒 Handling logout${forceLogout ? ' (forced)' : ''}`);
    
    // Clear all session data
    localStorage.removeItem('access_token');
    sessionStorage.clear();
    
    // Update state
    setUser(null);
    setIsAuthenticated(false);
    setSessionWarning({ show: false, timeRemaining: 0 });
    
    // Stop session monitoring
    if (sessionService.destroy) {
      sessionService.destroy();
    } else {
      sessionService.stopSessionMonitoring();
    }
    
    // Always redirect to login page
    console.log('🔄 Redirecting to login page');
    window.location.href = '/login';
  };

  const extendSession = async () => {
    try {
      const success = await sessionService.extendSession();
      if (success) {
        setSessionWarning({ show: false, timeRemaining: 0 });
      }
      return success;
    } catch (error) {
      console.error('Extend session error:', error);
      return false;
    }
  };

  const closeSessionWarning = () => {
    setSessionWarning({ show: false, timeRemaining: 0 });
  };

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    logout,
    extendSession,
    // Backward compatibility - provide token for existing components
    token: localStorage.getItem('access_token')
  };

  return (
    <SessionAuthContext.Provider value={value}>
      {children}
      <SessionWarningModal
        open={sessionWarning.show}
        timeRemaining={sessionWarning.timeRemaining}
        onExtend={extendSession}
        onLogout={logout}
        onClose={closeSessionWarning}
      />
    </SessionAuthContext.Provider>
  );
};