import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
} from '@mui/material';
import {
  Logout as LogoutIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import Logo from '../common/Logo';

const TopHeader = () => {
  const { user, logout } = useAuth();
  const { getTheme } = useTheme();
  const navigate = useNavigate();
  const theme = getTheme();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleHomeClick = () => {
    navigate('/dashboard');
  };





  return (
    <AppBar 
      position="fixed" 
      sx={{ 
        zIndex: (muiTheme) => muiTheme.zIndex.drawer + 1,
        background: theme.headerBackground,
        color: theme.headerColor,
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
      }}
    >
      <Toolbar sx={{ minHeight: '64px !important' }}>
        {/* Logo and Brand */}
        <IconButton
          edge="start"
          color="inherit"
          onClick={handleHomeClick}
          sx={{ mr: 2, p: 0.5 }}
        >
          <Logo size={40} />
        </IconButton>
        
        <Typography 
          variant="h6" 
          sx={{ 
            mr: 3,
            fontWeight: 600,
            cursor: 'pointer',
          }}
          onClick={handleHomeClick}
        >
          OpsConductor
        </Typography>

        {/* Spacer */}
        <Box sx={{ flexGrow: 1 }} />

        {/* Logout Button */}
        {user && (
          <Button 
            color="inherit" 
            onClick={handleLogout} 
            startIcon={<LogoutIcon />}
            sx={{
              '&:hover': {
                backgroundColor: 'rgba(255,255,255,0.1)',
              }
            }}
          >
            Logout
          </Button>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default TopHeader;