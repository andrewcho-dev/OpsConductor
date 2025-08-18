import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  Link,
} from '@mui/material';
import {
  Logout as LogoutIcon,
  Info as InfoIcon,
  Close as CloseIcon,
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
  const [licenseOpen, setLicenseOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleHomeClick = () => {
    navigate('/dashboard');
  };

  const handleAboutOpen = () => {
    setAboutOpen(true);
  };

  const handleAboutClose = () => {
    setAboutOpen(false);
  };

  const handleLicenseOpen = () => {
    setLicenseOpen(true);
  };

  const handleLicenseClose = () => {
    setLicenseOpen(false);
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
            <Logo size={40} variant="hat" theme="dark" />
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

          {/* About Info Button */}
          {user && (
            <IconButton
              color="inherit"
              onClick={handleAboutOpen}
              sx={{
                mr: 1,
                '&:hover': {
                  backgroundColor: 'rgba(255,255,255,0.1)',
                }
              }}
            >
              <InfoIcon />
            </IconButton>
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
        maxWidth="xs"
        PaperProps={{
          sx: {
            borderRadius: 2,
            minWidth: '300px',
            maxWidth: '350px',
          }
        }}
      >
        <DialogTitle sx={{ 
          textAlign: 'center', 
          pb: 1, 
          pt: 2,
          position: 'relative'
        }}>
          <IconButton
            onClick={handleAboutClose}
            sx={{
              position: 'absolute',
              right: 8,
              top: 8,
              color: '#666',
              '&:hover': {
                backgroundColor: 'rgba(0,0,0,0.04)',
              }
            }}
          >
            <CloseIcon fontSize="small" />
          </IconButton>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
            <Logo size={32} variant="hat" theme="light" />
            <Typography variant="h6" sx={{ ml: 1.5, fontWeight: 600, color: '#003c82' }}>
              OpsConductor
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ textAlign: 'center', pt: 0, pb: 3 }}>
          <Typography variant="body2" sx={{ mb: 2, color: '#666' }}>
            Enterprise Automation Platform
          </Typography>
          <Typography variant="caption" sx={{ display: 'block', mb: 1, color: '#999' }}>
            Version 1.0.0
          </Typography>
          <Typography variant="caption" sx={{ display: 'block', mb: 1, color: '#999' }}>
            © 2025 Enabled Enterprises LLC
          </Typography>
          <Link
            component="button"
            onClick={handleLicenseOpen}
            sx={{
              fontSize: '0.75rem',
              color: '#1976d2',
              textDecoration: 'none',
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              '&:hover': {
                textDecoration: 'underline',
              }
            }}
          >
            View License Terms
          </Link>
        </DialogContent>
      </Dialog>

      {/* License Dialog */}
      <Dialog
        open={licenseOpen}
        onClose={handleLicenseClose}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 2,
          }
        }}
      >
        <DialogTitle sx={{ 
          textAlign: 'center', 
          pb: 1, 
          pt: 2,
          position: 'relative'
        }}>
          <IconButton
            onClick={handleLicenseClose}
            sx={{
              position: 'absolute',
              right: 8,
              top: 8,
              color: '#666',
              '&:hover': {
                backgroundColor: 'rgba(0,0,0,0.04)',
              }
            }}
          >
            <CloseIcon fontSize="small" />
          </IconButton>
          <Typography variant="h6" sx={{ fontWeight: 600, color: '#003c82' }}>
            MIT License
          </Typography>
        </DialogTitle>
        <DialogContent sx={{ pt: 1, pb: 3 }}>
          <Typography variant="body2" sx={{ mb: 2, fontWeight: 600 }}>
            Copyright (c) 2025 Enabled Enterprises LLC
          </Typography>

          <Typography variant="body2" sx={{ mb: 2, lineHeight: 1.6 }}>
            Permission is hereby granted, free of charge, to any person obtaining a copy
            of this software and associated documentation files (the "Software"), to deal
            in the Software without restriction, including without limitation the rights
            to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
            copies of the Software, and to permit persons to whom the Software is
            furnished to do so, subject to the following conditions:
          </Typography>

          <Typography variant="body2" sx={{ mb: 2, lineHeight: 1.6 }}>
            The above copyright notice and this permission notice shall be included in all
            copies or substantial portions of the Software.
          </Typography>

          <Typography variant="body2" sx={{ mb: 3, lineHeight: 1.6, fontWeight: 600 }}>
            THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
            IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
            FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
            AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
            LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
            OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
            SOFTWARE.
          </Typography>

          <Box sx={{ 
            pt: 2, 
            borderTop: '1px solid #e0e0e0',
            textAlign: 'center' 
          }}>
            <Typography variant="caption" sx={{ color: '#666' }}>
              For licensing questions: legal@enabledconsultants.com
            </Typography>
          </Box>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default TopHeader;