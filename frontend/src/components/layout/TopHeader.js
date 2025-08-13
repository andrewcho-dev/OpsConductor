import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
} from '@mui/material';
import {
  Logout as LogoutIcon,
  Info as InfoIcon,
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
  const [aboutOpen, setAboutOpen] = useState(false);
  const [menuAnchor, setMenuAnchor] = useState(null);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleHomeClick = () => {
    navigate('/dashboard');
  };

  const handleMenuOpen = (event) => {
    setMenuAnchor(event.currentTarget);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
  };

  const handleAboutOpen = () => {
    setAboutOpen(true);
    handleMenuClose();
  };

  const handleAboutClose = () => {
    setAboutOpen(false);
  };





  return (
    <>
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

          {/* About Menu */}
          {user && (
            <>
              <IconButton
                color="inherit"
                onClick={handleMenuOpen}
                sx={{
                  mr: 1,
                  '&:hover': {
                    backgroundColor: 'rgba(255,255,255,0.1)',
                  }
                }}
              >
                <InfoIcon />
              </IconButton>
              <Menu
                anchorEl={menuAnchor}
                open={Boolean(menuAnchor)}
                onClose={handleMenuClose}
                anchorOrigin={{
                  vertical: 'bottom',
                  horizontal: 'right',
                }}
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
              >
                <MenuItem onClick={handleAboutOpen}>About OpsConductor</MenuItem>
              </Menu>
            </>
          )}

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

      {/* About Dialog */}
      <Dialog
        open={aboutOpen}
        onClose={handleAboutClose}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ textAlign: 'center', pb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
            <Logo size={48} />
            <Typography variant="h5" sx={{ ml: 2, fontWeight: 600, color: '#003c82' }}>
              OpsConductor
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h6" sx={{ mb: 2, color: '#666' }}>
              Enterprise Automation Orchestration Platform
            </Typography>
            
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="body1" sx={{ mb: 2 }}>
              OpsConductor provides comprehensive automation capabilities for enterprise infrastructure management, 
              job orchestration, and system monitoring.
            </Typography>
            
            <Typography variant="body2" sx={{ mb: 1, color: '#666' }}>
              Version: 1.0.0
            </Typography>
            
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="body2" sx={{ mb: 1, fontWeight: 600 }}>
              © 2025 Enabled Enterprises LLC
            </Typography>
            <Typography variant="body2" sx={{ mb: 1, color: '#666' }}>
              All rights reserved.
            </Typography>
            
            <Typography variant="body2" sx={{ mt: 2, color: '#666' }}>
              Licensed under the MIT License
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions sx={{ justifyContent: 'center', pb: 3 }}>
          <Button onClick={handleAboutClose} variant="contained">
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default TopHeader;