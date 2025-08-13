import React, { useState, useEffect, createContext, useContext } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  IconButton,
  Tooltip,
  Collapse,
  Alert,
  Chip,
  Divider,
} from '@mui/material';
import {
  Circle as CircleIcon,
  Refresh as RefreshIcon,
  ExpandLess as ExpandLessIcon,
  ExpandMore as ExpandMoreIcon,
  Clear as ClearIcon,
  History as HistoryIcon,
} from '@mui/icons-material';
import { useLocation } from 'react-router-dom';
import { useTheme } from '../../contexts/ThemeContext';

// Create Alert Context for global alert management
const AlertContext = createContext();

export const useAlert = () => {
  const context = useContext(AlertContext);
  if (!context) {
    throw new Error('useAlert must be used within an AlertProvider');
  }
  return context;
};

export const AlertProvider = ({ children }) => {
  const [alerts, setAlerts] = useState([]);

  const addAlert = (message, severity = 'info', duration = 5000) => {
    const id = Date.now() + Math.random();
    const alert = {
      id,
      message,
      severity,
      timestamp: new Date(),
      duration
    };
    
    setAlerts(prev => [alert, ...prev]);
    
    if (duration > 0) {
      setTimeout(() => {
        removeAlert(id);
      }, duration);
    }
  };

  const removeAlert = (id) => {
    setAlerts(prev => prev.filter(alert => alert.id !== id));
  };

  const clearAllAlerts = () => {
    setAlerts([]);
  };

  return (
    <AlertContext.Provider value={{ alerts, addAlert, removeAlert, clearAllAlerts }}>
      {children}
    </AlertContext.Provider>
  );
};

const BottomStatusBar = () => {
  const location = useLocation();
  const { getTheme } = useTheme();
  const { alerts, removeAlert, clearAllAlerts } = useAlert();
  const [currentTime, setCurrentTime] = useState(new Date());
  const [systemStatus] = useState('online');
  const [alertsExpanded, setAlertsExpanded] = useState(false);
  const theme = getTheme();

  // Update time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);



  const formatTime = (date, timeZone = undefined) => {
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZone: timeZone
    });
  };

  const formatDate = (date, timeZone = undefined) => {
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      timeZone: timeZone
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'online': return '#4caf50';
      case 'warning': return '#ff9800';
      case 'error': return '#f44336';
      default: return '#9e9e9e';
    }
  };

  const handleRefresh = () => {
    window.location.reload();
  };

  const toggleAlerts = () => {
    setAlertsExpanded(!alertsExpanded);
  };

  const formatAlertTime = (timestamp) => {
    return timestamp.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getAlertIcon = (severity) => {
    switch (severity) {
      case 'error': return '❌';
      case 'warning': return '⚠️';
      case 'success': return '✅';
      case 'info': return 'ℹ️';
      default: return 'ℹ️';
    }
  };

  const currentAlert = alerts.length > 0 ? alerts[0] : null;

  return (
    <>
      {/* Alert Messages Expansion Panel */}
      <Collapse in={alertsExpanded}>
        <Box
          sx={{
            position: 'fixed',
            bottom: '28px',
            left: 0,
            right: 0,
            maxHeight: '200px',
            backgroundColor: '#ffffff',
            borderTop: '1px solid #e0e0e0',
            boxShadow: '0 -4px 8px rgba(0,0,0,0.1)',
            zIndex: (muiTheme) => muiTheme.zIndex.drawer,
            overflow: 'auto',
          }}
        >
          {alerts.length === 0 ? (
            <Box sx={{ p: 2, textAlign: 'center', color: '#666' }}>
              <Typography variant="body2">No recent alerts</Typography>
            </Box>
          ) : (
            <Box sx={{ p: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'between', alignItems: 'center', mb: 1, px: 1 }}>
                <Typography variant="caption" sx={{ fontWeight: 600, color: '#666' }}>
                  Recent Alerts ({alerts.length})
                </Typography>
                <IconButton size="small" onClick={clearAllAlerts} sx={{ color: '#666' }}>
                  <ClearIcon fontSize="small" />
                </IconButton>
              </Box>
              {alerts.map((alert, index) => (
                <Alert
                  key={alert.id}
                  severity={alert.severity}
                  onClose={() => removeAlert(alert.id)}
                  sx={{
                    mb: 0.5,
                    fontSize: '0.75rem',
                    '& .MuiAlert-message': { fontSize: '0.75rem' },
                    '& .MuiAlert-action': { padding: '0 4px' }
                  }}
                >
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                    <Typography variant="caption" sx={{ flex: 1 }}>
                      {alert.message}
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#666', ml: 2 }}>
                      {formatAlertTime(alert.timestamp)}
                    </Typography>
                  </Box>
                </Alert>
              ))}
            </Box>
          )}
        </Box>
      </Collapse>

      {/* Main Status Bar */}
      <AppBar 
        position="fixed" 
        sx={{ 
          top: 'auto', 
          bottom: 0,
          zIndex: (muiTheme) => muiTheme.zIndex.drawer + 1,
          background: theme.bottomBarBackground,
          color: theme.bottomBarColor,
          borderTop: 'none',
          boxShadow: '0 -2px 8px rgba(0,0,0,0.2)',
        }}
      >
        <Toolbar 
          variant="dense" 
          sx={{ 
            minHeight: '28px !important',
            height: '28px',
            px: 2,
          }}
        >
          {/* System Status */}
          <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
            <CircleIcon 
              sx={{ 
                color: getStatusColor(systemStatus), 
                fontSize: 12, 
                mr: 1 
              }} 
            />
            <Typography 
              variant="caption" 
              sx={{ 
                fontWeight: 400,
                fontSize: '0.7rem',
                color: theme.bottomBarColor
              }}
            >
              System: {systemStatus.charAt(0).toUpperCase() + systemStatus.slice(1)}
            </Typography>
          </Box>

          {/* Current Alert Display */}
          {currentAlert && (
            <Box sx={{ display: 'flex', alignItems: 'center', mr: 2, maxWidth: '300px' }}>
              <Divider orientation="vertical" flexItem sx={{ mr: 2, backgroundColor: 'rgba(255,255,255,0.3)' }} />
              <Typography 
                variant="caption" 
                sx={{ 
                  fontSize: '0.7rem',
                  color: theme.bottomBarColor,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  flex: 1
                }}
              >
                {getAlertIcon(currentAlert.severity)} {currentAlert.message}
              </Typography>
            </Box>
          )}

          {/* Alert History Button */}
          {alerts.length > 0 && (
            <Tooltip title={`${alerts.length} alerts - Click to view history`}>
              <IconButton
                size="small"
                onClick={toggleAlerts}
                sx={{ 
                  color: theme.bottomBarColor,
                  mr: 1,
                  '&:hover': {
                    backgroundColor: 'rgba(255,255,255,0.1)',
                  }
                }}
              >
                <Chip
                  label={alerts.length}
                  size="small"
                  sx={{
                    height: '16px',
                    fontSize: '0.6rem',
                    backgroundColor: alerts.some(a => a.severity === 'error') ? '#f44336' : 
                                   alerts.some(a => a.severity === 'warning') ? '#ff9800' : '#2196f3',
                    color: 'white',
                    mr: 0.5
                  }}
                />
                {alertsExpanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
              </IconButton>
            </Tooltip>
          )}

          {/* Spacer */}
          <Box sx={{ flexGrow: 1 }} />

          {/* Copyright Notice */}
          <Box sx={{ display: 'flex', alignItems: 'center', mr: 3 }}>
            <Typography 
              variant="caption" 
              sx={{ 
                fontWeight: 400,
                fontSize: '0.65rem',
                color: theme.bottomBarColor,
                opacity: 0.7
              }}
            >
              © 2025 Enabled Enterprises LLC
            </Typography>
          </Box>

          {/* UTC Clock */}
          <Box sx={{ display: 'flex', alignItems: 'center', mr: 3 }}>
            <Typography 
              variant="caption" 
              sx={{ 
                mr: 1,
                fontWeight: 400,
                fontSize: '0.7rem',
                color: theme.bottomBarColor,
                opacity: 0.8
              }}
            >
              UTC:
            </Typography>
            <Typography 
              variant="caption" 
              sx={{ 
                mr: 1,
                fontWeight: 400,
                fontSize: '0.7rem',
                color: theme.bottomBarColor
              }}
            >
              {formatDate(currentTime, 'UTC')}
            </Typography>
            <Typography 
              variant="caption" 
              sx={{ 
                fontWeight: 400,
                fontSize: '0.7rem',
                minWidth: '70px',
                letterSpacing: '0.5px',
                color: theme.bottomBarColor
              }}
            >
              {formatTime(currentTime, 'UTC')}
            </Typography>
          </Box>

          {/* Local Clock */}
          <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
            <Typography 
              variant="caption" 
              sx={{ 
                mr: 1,
                fontWeight: 400,
                fontSize: '0.7rem',
                color: theme.bottomBarColor,
                opacity: 0.8
              }}
            >
              Local:
            </Typography>
            <Typography 
              variant="caption" 
              sx={{ 
                mr: 1,
                fontWeight: 400,
                fontSize: '0.7rem',
                color: theme.bottomBarColor
              }}
            >
              {formatDate(currentTime)}
            </Typography>
            <Typography 
              variant="caption" 
              sx={{ 
                fontWeight: 400,
                fontSize: '0.7rem',
                minWidth: '70px',
                letterSpacing: '0.5px',
                color: theme.bottomBarColor
              }}
            >
              {formatTime(currentTime)}
            </Typography>
          </Box>

          {/* Refresh Button */}
          <Tooltip title="Refresh Page">
            <IconButton
              size="small"
              onClick={handleRefresh}
              sx={{ 
                color: theme.bottomBarColor,
                '&:hover': {
                  backgroundColor: 'rgba(255,255,255,0.1)',
                }
              }}
            >
              <RefreshIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>
    </>
  );
};

export default BottomStatusBar;