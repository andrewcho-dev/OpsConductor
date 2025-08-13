import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Typography, 
  Button, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  TextField,
  IconButton,
  Tooltip,
  CircularProgress,
  Divider,
} from '@mui/material';
import { 
  Settings as SettingsIcon, 
  Palette as PaletteIcon,
  Refresh as RefreshIcon,
  Save as SaveIcon,
  Schedule as ScheduleIcon,
  Storage as StorageIcon,
  Security as SecurityIcon,
  Computer as ComputerIcon,
  AccessTime as AccessTimeIcon,
} from '@mui/icons-material';
import { useTheme } from '../../contexts/ThemeContext';
import { useAlert } from '../layout/BottomStatusBar';

// Create axios instance with auth configuration
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

const SystemSettings = () => {
  const { currentTheme, changeTheme, availableThemes } = useTheme();
  const { addAlert } = useAlert();
  const [systemInfo, setSystemInfo] = useState(null);
  const [timezones, setTimezones] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedTimezone, setSelectedTimezone] = useState('');
  const [sessionTimeout, setSessionTimeout] = useState(28800);
  const [maxJobs, setMaxJobs] = useState(50);
  const [logRetention, setLogRetention] = useState(30);
  const [currentTime, setCurrentTime] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSystemInfo();
    loadTimezones();
    loadCurrentTime();
    
    // Update current time every second
    const interval = setInterval(loadCurrentTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const loadSystemInfo = async () => {
    try {
      const response = await api.get('/system/info');
      setSystemInfo(response.data);
      setSelectedTimezone(response.data.timezone?.current || 'UTC');
      setSessionTimeout(response.data.session_timeout || 28800);
      setMaxJobs(response.data.max_concurrent_jobs || 50);
      setLogRetention(response.data.log_retention_days || 30);
      setLoading(false);
      addAlert('System information loaded successfully', 'success', 3000);
    } catch (err) {
      console.error('Failed to load system information:', err);
      const errorMessage = err.response?.data?.detail || 'Failed to load system information';
      addAlert(errorMessage, 'error', 0);
      setLoading(false);
    }
  };

  const loadTimezones = async () => {
    try {
      const response = await api.get('/system/timezones');
      setTimezones(response.data || {});
    } catch (err) {
      addAlert('Failed to load timezones', 'warning', 5000);
      console.error('Failed to load timezones:', err);
      // Set a fallback timezone list if API fails
      setTimezones({
        'UTC': 'UTC (Coordinated Universal Time)',
        'America/New_York': 'New York, America (UTC-05:00)',
        'America/Chicago': 'Chicago, America (UTC-06:00)',
        'America/Denver': 'Denver, America (UTC-07:00)',
        'America/Los_Angeles': 'Los Angeles, America (UTC-08:00)',
        'Europe/London': 'London, Europe (UTC+00:00)',
        'Europe/Paris': 'Paris, Europe (UTC+01:00)',
        'Asia/Tokyo': 'Tokyo, Asia (UTC+09:00)'
      });
    }
  };

  const loadCurrentTime = async () => {
    try {
      const response = await api.get('/system/current-time');
      setCurrentTime(response.data);
    } catch (err) {
      console.error('Failed to load current time:', err);
    }
  };

  const saveSettings = async () => {
    try {
      setSaving(true);
      
      // Save all settings in parallel
      const promises = [
        api.put('/system/timezone', { timezone: selectedTimezone }),
        api.put('/system/session-timeout', { timeout_seconds: sessionTimeout }),
        api.put('/system/max-concurrent-jobs', { max_jobs: maxJobs }),
        api.put('/system/log-retention', { retention_days: logRetention })
      ];
      
      await Promise.all(promises);
      await loadSystemInfo();
      addAlert('System settings saved successfully', 'success', 3000);
    } catch (err) {
      console.error('Failed to save system settings:', err);
      const errorMessage = err.response?.data?.detail || 'Failed to save system settings';
      addAlert(errorMessage, 'error', 0);
    } finally {
      setSaving(false);
    }
  };

  const handleThemeChange = (themeKey) => {
    changeTheme(themeKey);
    addAlert(`Theme changed to ${availableThemes[themeKey].name}`, 'success', 3000);
  };



  // Calculate system statistics
  const stats = {
    uptime: systemInfo?.uptime || 'N/A',
    version: '1.0.0',
    timezone: systemInfo?.timezone?.display_name || selectedTimezone,
    sessionTimeout: `${Math.floor(sessionTimeout / 60)}m`,
    maxJobs: maxJobs,
    logRetention: `${logRetention}d`,
  };

  return (
    <div className="dashboard-container">
      {/* Compact Page Header */}
      <div className="page-header">
        <Typography className="page-title">
          System Settings
        </Typography>
        <div className="page-actions">
          <Tooltip title="Refresh settings">
            <IconButton 
              className="btn-icon" 
              onClick={loadSystemInfo} 
              disabled={loading}
              size="small"
            >
              <RefreshIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Button
            className="btn-compact"
            variant="contained"
            startIcon={saving ? <CircularProgress size={14} /> : <SaveIcon fontSize="small" />}
            onClick={saveSettings}
            disabled={saving}
            size="small"
          >
            {saving ? 'Saving...' : 'Save All'}
          </Button>
        </div>
      </div>

      {/* Compact Statistics Grid */}
      <div className="stats-grid">
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon primary">
              <ComputerIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.version}</h3>
              <p>Version</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon info">
              <AccessTimeIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.timezone}</h3>
              <p>Timezone</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon warning">
              <SecurityIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.sessionTimeout}</h3>
              <p>Session Timeout</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon success">
              <ScheduleIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.maxJobs}</h3>
              <p>Max Jobs</p>
            </div>
          </div>
        </div>

        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon error">
              <StorageIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.logRetention}</h3>
              <p>Log Retention</p>
            </div>
          </div>
        </div>
        
        {/* Empty slot to maintain 6-column grid */}
        <div className="stat-card" style={{ visibility: 'hidden' }}>
          <div className="stat-card-content">
            <div className="stat-icon primary">
              <ComputerIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>-</h3>
              <p>-</p>
            </div>
          </div>
        </div>
      </div>



      {/* System Configuration Card */}
      <div className="main-content-card fade-in" style={{ marginTop: '16px' }}>
        <div className="content-card-header">
          <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
            <SettingsIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
            SYSTEM CONFIGURATION
          </Typography>
          {currentTime && (
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
              Current: {currentTime.local} ({currentTime.is_dst ? 'DST' : 'STD'})
            </Typography>
          )}
        </div>
        
        <div className="content-card-body">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
            
            {/* Timezone Settings */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                Timezone Configuration
              </Typography>
              <FormControl className="form-control-compact" size="small" fullWidth>
                <InputLabel>System Timezone</InputLabel>
                <Select
                  value={selectedTimezone}
                  label="System Timezone"
                  onChange={(e) => setSelectedTimezone(e.target.value)}
                >
                  {Object.entries(timezones).length > 0 ? (
                    Object.entries(timezones).map(([tz, display]) => (
                      <MenuItem key={tz} value={tz}>
                        {display}
                      </MenuItem>
                    ))
                  ) : (
                    <MenuItem value={selectedTimezone}>
                      {selectedTimezone || 'Loading...'}
                    </MenuItem>
                  )}
                </Select>
              </FormControl>
              {systemInfo?.timezone && (
                <Typography variant="caption" sx={{ fontSize: '0.7rem', color: 'text.secondary', mt: 0.5, display: 'block' }}>
                  UTC Offset: {systemInfo.timezone.current_utc_offset}
                </Typography>
              )}
            </div>

            {/* Session Management */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                Session Management
              </Typography>
              <TextField
                className="form-control-compact"
                size="small"
                fullWidth
                label="Session Timeout (seconds)"
                type="number"
                inputProps={{ min: 60, max: 86400 }}
                value={sessionTimeout}
                onChange={(e) => setSessionTimeout(parseInt(e.target.value) || 28800)}
              />
              <Typography variant="caption" sx={{ fontSize: '0.7rem', color: 'text.secondary', mt: 0.5, display: 'block' }}>
                Range: 60s - 86400s (24h)
              </Typography>
            </div>

            {/* Job Configuration */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                Job Execution
              </Typography>
              <TextField
                className="form-control-compact"
                size="small"
                fullWidth
                label="Max Concurrent Jobs"
                type="number"
                inputProps={{ min: 1, max: 1000 }}
                value={maxJobs}
                onChange={(e) => setMaxJobs(parseInt(e.target.value) || 50)}
              />
              <Typography variant="caption" sx={{ fontSize: '0.7rem', color: 'text.secondary', mt: 0.5, display: 'block' }}>
                Range: 1 - 1000 jobs
              </Typography>
            </div>

            {/* Log Management */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                Log Management
              </Typography>
              <TextField
                className="form-control-compact"
                size="small"
                fullWidth
                label="Log Retention (days)"
                type="number"
                inputProps={{ min: 1, max: 3650 }}
                value={logRetention}
                onChange={(e) => setLogRetention(parseInt(e.target.value) || 30)}
              />
              <Typography variant="caption" sx={{ fontSize: '0.7rem', color: 'text.secondary', mt: 0.5, display: 'block' }}>
                Range: 1 - 3650 days
              </Typography>
            </div>

            {/* Theme Settings */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                <PaletteIcon fontSize="small" sx={{ mr: 0.5, verticalAlign: 'middle' }} />
                Theme Settings
              </Typography>
              <FormControl className="form-control-compact" size="small" fullWidth>
                <InputLabel>Color Theme</InputLabel>
                <Select
                  value={currentTheme}
                  label="Color Theme"
                  onChange={(e) => handleThemeChange(e.target.value)}
                >
                  {Object.entries(availableThemes).map(([key, theme]) => (
                    <MenuItem key={key} value={key}>
                      {theme.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Typography variant="caption" sx={{ fontSize: '0.7rem', color: 'text.secondary', mt: 0.5, display: 'block' }}>
                Current: {availableThemes[currentTheme]?.name}
              </Typography>
            </div>
          </div>

          <Divider sx={{ my: 2 }} />

          {/* System Information */}
          <div>
            <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
              System Information
            </Typography>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '8px' }}>
              <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                <strong>Platform:</strong> EnableDRM Universal Platform
              </Typography>
              <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                <strong>Version:</strong> {stats.version}
              </Typography>
              <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                <strong>Status:</strong> <span style={{ color: '#4caf50' }}>Running</span>
              </Typography>
              <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                <strong>Uptime:</strong> {stats.uptime}
              </Typography>
            </div>
          </div>
        </div>
      </div>

      {loading && (
        <div className="loading-container">
          <CircularProgress size={24} />
          <Typography variant="body2" sx={{ ml: 2, color: 'text.secondary' }}>
            Loading system settings...
          </Typography>
        </div>
      )}
    </div>
  );
};

export default SystemSettings; 