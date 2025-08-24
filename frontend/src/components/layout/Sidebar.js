import React, { useState } from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  IconButton,
  Box,
  Typography,
  Divider,
  Tooltip,
  Chip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  ChevronLeft as ChevronLeftIcon,
  Computer as ComputerIcon,
  Work as WorkIcon,
  Assessment as AssessmentIcon,
  People as PeopleIcon,
  Settings as SettingsIcon,
  Dashboard as DashboardIcon,
  AutoAwesome as AutoAwesomeIcon,
  Speed as SpeedIcon,

  Security as SecurityIcon,
  VpnKey as VpnKeyIcon,
  Visibility as VisibilityIcon,
  ViewInAr as DockerIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useSessionAuth } from '../../contexts/SessionAuthContext';

const DRAWER_WIDTH = 240;
const DRAWER_WIDTH_COLLAPSED = 60;

const Sidebar = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useSessionAuth();

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  const menuItems = [
    {
      text: 'Dashboard',
      icon: <DashboardIcon />,
      path: '/dashboard',
      roles: ['admin', 'user']
    },
    {
      text: 'Universal Targets',
      icon: <ComputerIcon />,
      path: '/targets',
      roles: ['admin', 'user']
    },
    {
      text: 'Job Management',
      icon: <WorkIcon />,
      path: '/jobs',
      roles: ['admin', 'user']
    },



    {
      text: 'Docker Environment',
      icon: <DockerIcon />,
      path: '/docker-monitoring',
      roles: ['admin', 'user']
    },

    {
      text: 'Audit & Security',
      icon: <SecurityIcon />,
      path: '/audit',
      roles: ['admin']
    },
    {
      text: 'User Management',
      icon: <PeopleIcon />,
      path: '/users',
      roles: ['admin']
    },
    {
      text: 'Auth Configuration',
      icon: <VpnKeyIcon />,
      path: '/auth-config',
      roles: ['admin']
    },
    {
      text: 'System Settings',
      icon: <SettingsIcon />,
      path: '/system-settings',
      roles: ['admin']
    }
  ];

  const filteredMenuItems = menuItems.filter(item => {
    const userRole = user?.role?.name || user?.role;
    // Super admin has access to all menu items
    if (userRole === 'super_admin') {
      return true;
    }
    return item.roles.includes(userRole);
  });

  const handleNavigation = (path, external = false) => {
    if (external) {
      window.open(path, '_blank');
    } else {
      navigate(path);
    }
  };

  const isActive = (path) => {
    return location.pathname === path;
  };



  return (
    <Drawer
      variant="permanent"
      sx={{
        width: isCollapsed ? DRAWER_WIDTH_COLLAPSED : DRAWER_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: isCollapsed ? DRAWER_WIDTH_COLLAPSED : DRAWER_WIDTH,
          boxSizing: 'border-box',
          transition: 'width 0.3s ease',
          overflowX: 'hidden',
          borderRight: '1px solid #e0e0e0',
          backgroundColor: '#fafafa',
          paddingBottom: '28px', // Account for bottom status bar
        },
      }}
    >
      {/* Header with toggle button */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: isCollapsed ? 'center' : 'space-between',
          p: 1,
          minHeight: '64px',
          borderBottom: '1px solid #e0e0e0',
        }}
      >
        {!isCollapsed && (
          <Typography variant="h6" sx={{ fontWeight: 600, color: '#1976d2' }}>
            OpsConductor
          </Typography>
        )}
        <IconButton onClick={toggleSidebar} size="small">
          {isCollapsed ? <MenuIcon /> : <ChevronLeftIcon />}
        </IconButton>
      </Box>

      {/* Navigation Menu */}
      <List sx={{ pt: 1 }}>
        {filteredMenuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <Tooltip 
              title={isCollapsed ? item.text : ''} 
              placement="right"
              arrow
            >
              <ListItemButton
                onClick={() => handleNavigation(item.path, item.external)}
                sx={{
                  minHeight: 48,
                  justifyContent: isCollapsed ? 'center' : 'initial',
                  px: 2.5,
                  backgroundColor: isActive(item.path) ? '#e3f2fd' : 'transparent',
                  borderRight: isActive(item.path) ? '3px solid #1976d2' : 'none',
                  '&:hover': {
                    backgroundColor: isActive(item.path) ? '#e3f2fd' : '#f5f5f5',
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 0,
                    mr: isCollapsed ? 0 : 3,
                    justifyContent: 'center',
                    color: isActive(item.path) ? '#1976d2' : '#666',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText 
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <span>{item.text}</span>
                      {item.badge && !isCollapsed && (
                        <Chip 
                          label={item.badge} 
                          size="small" 
                          sx={{ 
                            height: 16, 
                            fontSize: '0.6rem',
                            backgroundColor: '#ff4444',
                            color: 'white',
                            fontWeight: 'bold',
                            '& .MuiChip-label': {
                              px: 0.5
                            }
                          }} 
                        />
                      )}
                    </Box>
                  }
                  sx={{ 
                    opacity: isCollapsed ? 0 : 1,
                    color: isActive(item.path) ? '#1976d2' : '#333',
                    '& .MuiListItemText-primary': {
                      fontSize: '0.875rem',
                      fontWeight: isActive(item.path) ? 600 : 400,
                    }
                  }}
                />
              </ListItemButton>
            </Tooltip>
          </ListItem>
        ))}
      </List>

      {/* User info at bottom */}
      <Box sx={{ mt: 'auto', p: 2, borderTop: '1px solid #e0e0e0' }}>
        {!isCollapsed && user && (
          <Box>
            <Typography variant="caption" color="text.secondary">
              Logged in as:
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {user.username}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Role: {user.role?.name || user.role || 'No Role'}
            </Typography>
          </Box>
        )}
        {isCollapsed && user && (
          <Tooltip title={`${user.username} (${user.role?.name || user.role || 'No Role'})`} placement="right" arrow>
            <Box sx={{ display: 'flex', justifyContent: 'center' }}>
              <Box
                sx={{
                  width: 32,
                  height: 32,
                  borderRadius: '50%',
                  backgroundColor: '#1976d2',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                }}
              >
                {user.username?.charAt(0).toUpperCase()}
              </Box>
            </Box>
          </Tooltip>
        )}
      </Box>
    </Drawer>
  );
};

export default Sidebar;