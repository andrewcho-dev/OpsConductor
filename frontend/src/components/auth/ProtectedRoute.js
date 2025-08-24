import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { CircularProgress, Box, Typography } from '@mui/material';
import { useSessionAuth } from '../../contexts/SessionAuthContext';

const ProtectedRoute = ({ children, requireAdmin = false }) => {
  const { isAuthenticated, user, loading } = useSessionAuth();
  const location = useLocation();

  // Log authentication attempts for debugging
  useEffect(() => {
    if (!loading) {
      console.log(`🔐 Route Protection Check:`, {
        path: location.pathname,
        isAuthenticated,
        user: user ? { username: user.username, role: user.role?.name || user.role } : null,
        requireAdmin
      });
    }
  }, [isAuthenticated, user, loading, location.pathname, requireAdmin]);

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <Box
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
        gap={2}
      >
        <CircularProgress size={40} />
        <Typography variant="body2" color="textSecondary">
          Checking authentication...
        </Typography>
      </Box>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    console.log(`🚪 Redirecting to login - User not authenticated for ${location.pathname}`);
    // Store the attempted URL to redirect back after login
    const redirectUrl = location.pathname !== '/' ? location.pathname : '/dashboard';
    return <Navigate to="/login" state={{ from: redirectUrl }} replace />;
  }

  // Check admin requirements
  const userRole = user?.role?.name || user?.role;
  if (requireAdmin && userRole !== 'admin') {
    console.log(`⛔ Access denied - Admin required for ${location.pathname}, user role: ${userRole}`);
    return <Navigate to="/dashboard" replace />;
  }

  // User is authenticated and authorized
  console.log(`✅ Access granted to ${location.pathname}`);
  return children;
};

export default ProtectedRoute; 