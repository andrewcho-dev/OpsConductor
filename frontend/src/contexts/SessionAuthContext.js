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

  // Auth service URL - declared once and reused
  // ✅ Use relative URLs since frontend is served through the same nginx proxy
  const authUrl = process.env.REACT_APP_AUTH_URL || '/api/v1/auth';

  useEffect(() => {
    // Initialize session service
    const initializeAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const response = await fetch(`${authUrl}/validate`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ token })
          });

          if (response.ok) {
            const validationData = await response.json();
            if (validationData.valid && validationData.user) {
              setUser(validationData.user);
              setIsAuthenticated(true);
              // Set session ID if available
              if (validationData.session_id) {
                sessionService.setSessionId(validationData.session_id);
              }
            } else {
              // Token is invalid, clear it
              localStorage.removeItem('access_token');
            }
          } else {
            // Token validation failed, clear it
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
      // Clear any existing tokens before login
      localStorage.removeItem('access_token');
      console.log('🧹 Cleared existing tokens');
      
      // Login goes to AUTH SERVICE, not main backend
      const response = await fetch(`${authUrl}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      console.log('🔍 Login response status:', response.status);
      console.log('🔍 Login response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        console.log('❌ Error response text:', errorText);
        try {
          const errorData = JSON.parse(errorText);
          return {
            success: false,
            error: errorData.detail || 'Login failed'
          };
        } catch (parseError) {
          return {
            success: false,
            error: `Server error: ${errorText}`
          };
        }
      }

      const responseText = await response.text();
      console.log('📥 Raw response text:', responseText);
      
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseError) {
        console.error('❌ JSON parse error:', parseError);
        console.error('❌ Response text that failed to parse:', responseText);
        throw new Error(`Invalid JSON response: ${responseText.substring(0, 100)}...`);
      }
      console.log('🔐 Login response data:', data);
      
      // Store token
      localStorage.setItem('access_token', data.access_token);
      
      // Set session ID
      console.log('🔑 Session ID from response:', data.session_id);
      sessionService.setSessionId(data.session_id);
      
      // Use user data from login response (no need for separate /me call)
      console.log('🔍 User data from login response:', data.user);
      setUser(data.user);
      setIsAuthenticated(true);
      return { success: true };

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
        await fetch(`${authUrl}/logout`, {
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