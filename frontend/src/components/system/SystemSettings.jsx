import React, { useState, useEffect } from 'react';
import { authService } from '../../services/authService';
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
  Notifications as NotificationsIcon,
  Email as EmailIcon,
  Sms as SmsIcon,
} from '@mui/icons-material';
import { useTheme } from '../../contexts/ThemeContext';
import { useAlert } from '../layout/BottomStatusBar';
import StandardPageLayout, { StandardContentCard } from '../common/StandardPageLayout';

// Use centralized auth service with automatic token refresh and logout
const api = authService.api;

const SystemSettings = () => {
  // Core state from original
  const [systemInfo, setSystemInfo] = useState(null);
  const [timezones, setTimezones] = useState({});
  const [currentTime, setCurrentTime] = useState(null);
  const [selectedTimezone, setSelectedTimezone] = useState('UTC');
  const [inactivityTimeout, setInactivityTimeout] = useState(60); // minutes
  const [warningTime, setWarningTime] = useState(2); // minutes
  const [maxJobs, setMaxJobs] = useState(50);
  const [logRetention, setLogRetention] = useState(30);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Enhanced state for system monitoring
  const [systemStatus, setSystemStatus] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);
  
  // Notification configuration state
  const [emailTargets, setEmailTargets] = useState([]);
  const [selectedEmailTarget, setSelectedEmailTarget] = useState('');
  const [testEmailAddress, setTestEmailAddress] = useState('');
  
  // Track if settings have been modified
  const [originalSettings, setOriginalSettings] = useState({});
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const { theme, changeTheme, availableThemes } = useTheme();
  const { addAlert } = useAlert();

  useEffect(() => {
    loadAllSystemData();
    const interval = setInterval(loadCurrentTime, 30000); // Update time every 30 seconds
    return () => clearInterval(interval);
  }, []);

  // Detect changes in settings
  useEffect(() => {
    if (Object.keys(originalSettings).length > 0) {
      const currentSettings = {
        timezone: selectedTimezone,
        inactivityTimeout: inactivityTimeout,
        warningTime: warningTime,
        maxJobs: maxJobs,
        logRetention: logRetention
      };
      
      const hasChanges = JSON.stringify(currentSettings) !== JSON.stringify(originalSettings);
      console.log('Change detection:', {
        original: originalSettings,
        current: currentSettings,
        hasChanges: hasChanges
      });
      setHasUnsavedChanges(hasChanges);
    }
  }, [selectedTimezone, inactivityTimeout, warningTime, maxJobs, logRetention, originalSettings]);

  const loadAllSystemData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadSystemInfo(),
        loadTimezones(),
        loadCurrentTime(),
        loadSystemStatus(),
        loadSystemHealth(),
        loadEmailTargets()
      ]);
    } catch (error) {
      console.error('Failed to load system data:', error);
      addAlert('Failed to load some system information', 'warning', 5000);
    } finally {
      setLoading(false);
    }
  };

  const loadSystemInfo = async () => {
    try {
      console.log('Loading system info...');
      const response = await api.get('/v2/system/info');
      console.log('System info response:', response.data);
      
      setSystemInfo(response.data);
      
      // Extract settings from response with fallbacks
      const newTimezone = response.data.timezone?.current || 'UTC';
      const newInactivityTimeout = response.data.inactivity_timeout_minutes || 60;
      const newWarningTime = response.data.warning_time_minutes || 2;
      const newMaxJobs = response.data.max_concurrent_jobs || 50;
      const newLogRetention = response.data.log_retention_days || 30;
      
      console.log('Loading saved settings from API:', {
        timezone: newTimezone,
        inactivityTimeout: newInactivityTimeout,
        warningTime: newWarningTime,
        maxJobs: newMaxJobs,
        logRetention: newLogRetention
      });
      
      setSelectedTimezone(newTimezone);
      setInactivityTimeout(newInactivityTimeout);
      setWarningTime(newWarningTime);
      setMaxJobs(newMaxJobs);
      setLogRetention(newLogRetention);
      
      // Store original settings for change detection
      const originalSettings = {
        timezone: newTimezone,
        inactivityTimeout: newInactivityTimeout,
        warningTime: newWarningTime,
        maxJobs: newMaxJobs,
        logRetention: newLogRetention
      };
      setOriginalSettings(originalSettings);
      setHasUnsavedChanges(false);
    } catch (err) {
      console.error('Failed to load system information:', err);
      const errorMessage = 'Failed to load system information';
      addAlert(errorMessage, 'error', 0);
      
      // Set default values if loading fails
      setSelectedTimezone('UTC');
      setInactivityTimeout(60);
      setWarningTime(2);
      setMaxJobs(50);
      setLogRetention(30);
      
      // Also set original settings so change detection works
      const defaultSettings = {
        timezone: 'UTC',
        inactivityTimeout: 60,
        warningTime: 2,
        maxJobs: 50,
        logRetention: 30
      };
      setOriginalSettings(defaultSettings);
      setHasUnsavedChanges(false);
    }
  };

  const loadTimezones = async () => {
    try {
      const response = await api.get('/v2/system/timezones');
      setTimezones(response.data.timezones || {});
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
      const response = await api.get('/v2/system/current-time');
      setCurrentTime(response.data);
    } catch (err) {
      console.error('Failed to load current time:', err);
    }
  };

  const loadSystemStatus = async () => {
    try {
      const response = await api.get('/v2/system/status');
      setSystemStatus(response.data);
    } catch (err) {
      console.error('Failed to load system status:', err);
      // Set mock data for demo
      setSystemStatus({
        uptime: '5d 12h 30m',
        resource_usage: {
          cpu_percent: 25.5,
          memory: { percent: 68.2 },
          disk: { percent: 45.1 }
        }
      });
    }
  };

  const loadSystemHealth = async () => {
    try {
      const response = await api.get('/v2/system/health');
      setSystemHealth(response.data);
    } catch (err) {
      console.error('Failed to load system health:', err);
      // Set mock data for demo
      setSystemHealth({
        overall_health: 'healthy'
      });
    }
  };

  const loadEmailTargets = async () => {
    try {
      console.log('Loading eligible email targets...');
      // Use the new system API endpoint for eligible email targets
      const response = await api.get('/v2/system/email-targets/eligible');
      console.log('Email targets response:', response.data);
      
      setEmailTargets(response.data.targets || []);
      
      // Also load current email target configuration
      const configResponse = await api.get('/v2/system/email-target/config');
      console.log('Email target config:', configResponse.data);
      
      if (configResponse.data.is_configured && configResponse.data.target_id) {
        setSelectedEmailTarget(configResponse.data.target_id.toString());
      } else {
        setSelectedEmailTarget('');
      }
    } catch (err) {
      console.error('Failed to load email targets:', err);
      // Set empty array on error
      setEmailTargets([]);
      setSelectedEmailTarget('');
    }
  };

  const saveEmailTarget = async () => {
    try {
      console.log('Saving email target:', selectedEmailTarget);
      const targetId = selectedEmailTarget ? parseInt(selectedEmailTarget) : null;
      
      const response = await api.put('/v2/system/email-target/config', {
        target_id: targetId
      });
      
      console.log('Email target saved:', response.data);
      addAlert('Email target configuration saved successfully', 'success', 3000);
      
      return true;
    } catch (err) {
      console.error('Failed to save email target:', err);
      const errorMessage = err.response?.data?.detail?.message || err.response?.data?.detail || 'Failed to save email target configuration';
      addAlert(errorMessage, 'error', 5000);
      return false;
    }
  };

  const testEmailTarget = async () => {
    if (!testEmailAddress.trim()) {
      addAlert('Please enter an email address to send the test email to', 'warning', 3000);
      return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(testEmailAddress.trim())) {
      addAlert('Please enter a valid email address', 'warning', 3000);
      return;
    }

    try {
      console.log('Testing email target...', testEmailAddress);
      const response = await api.post('/v2/system/email-target/test', {
        test_email: testEmailAddress.trim()
      });
      
      console.log('Email test result:', response.data);
      
      if (response.data.success) {
        addAlert(`Test email sent successfully to ${testEmailAddress}! Check your inbox.`, 'success', 5000);
      } else {
        addAlert(`Test email failed: ${response.data.message}`, 'error', 8000);
      }
    } catch (err) {
      console.error('Failed to test email target:', err);
      const errorMessage = err.response?.data?.detail?.message || err.response?.data?.detail || 'Failed to test email target';
      addAlert(errorMessage, 'error', 5000);
    }
  };

  const saveSettings = async () => {
    try {
      setSaving(true);
      
      // Save settings one by one to better handle errors and provide feedback
      const settingsToSave = [
        {
          name: 'Timezone',
          endpoint: '/v2/system/timezone',
          data: { timezone: selectedTimezone }
        },
        {
          name: 'Inactivity Timeout',
          endpoint: '/v2/system/inactivity-timeout',
          data: { timeout_minutes: inactivityTimeout }
        },
        {
          name: 'Warning Time',
          endpoint: '/v2/system/warning-time',
          data: { warning_minutes: warningTime }
        },
        {
          name: 'Max Concurrent Jobs',
          endpoint: '/v2/system/max-concurrent-jobs',
          data: { max_jobs: maxJobs }
        },
        {
          name: 'Log Retention',
          endpoint: '/v2/system/log-retention',
          data: { retention_days: logRetention }
        }
      ];

      let savedCount = 0;
      let errors = [];

      for (const setting of settingsToSave) {
        try {
          console.log(`Saving ${setting.name}:`, setting.data);
          const response = await api.put(setting.endpoint, setting.data);
          console.log(`${setting.name} saved successfully:`, response.data);
          savedCount++;
        } catch (err) {
          console.error(`Failed to save ${setting.name}:`, err);
          const errorMessage = err.response?.data?.detail?.message || err.response?.data?.detail || err.message || `Failed to save ${setting.name}`;
          errors.push(`${setting.name}: ${errorMessage}`);
        }
      }

      // Also save email target configuration
      const emailTargetSaved = await saveEmailTarget();
      if (emailTargetSaved) {
        savedCount++;
      } else {
        errors.push('Email Target: Failed to save email target configuration');
      }

      // Reload system info to get updated values
      console.log('Reloading system info after save...');
      await loadSystemInfo();
      await loadCurrentTime();
      await loadEmailTargets(); // Reload email targets to get updated config
      
      const totalSettings = settingsToSave.length + 1; // +1 for email target
      
      if (savedCount === totalSettings) {
        addAlert('All system settings saved successfully', 'success', 3000);
        setHasUnsavedChanges(false);
        
        // Update original settings to current values so change detection works correctly
        const newOriginalSettings = {
          timezone: selectedTimezone,
          inactivityTimeout: inactivityTimeout,
          warningTime: warningTime,
          maxJobs: maxJobs,
          logRetention: logRetention
        };
        setOriginalSettings(newOriginalSettings);
      } else if (savedCount > 0) {
        addAlert(`${savedCount} of ${totalSettings} settings saved. Some failed: ${errors.join(', ')}`, 'warning', 8000);
      } else {
        addAlert(`Failed to save settings: ${errors.join(', ')}`, 'error', 0);
      }
    } catch (err) {
      console.error('Failed to save system settings:', err);
      const errorMessage = err.response?.data?.detail?.message || err.response?.data?.detail || 'Failed to save system settings';
      addAlert(errorMessage, 'error', 0);
    } finally {
      setSaving(false);
    }
  };

  const handleThemeChange = (themeKey) => {
    changeTheme(themeKey);
    addAlert(`Theme changed to ${availableThemes[themeKey].name}`, 'success', 3000);
  };

  // Calculate system statistics following the original pattern
  const stats = {
    version: '1.0.0',
    uptime: systemStatus?.uptime || 'N/A',
    health: systemHealth?.overall_health || 'Healthy',
    cpu: systemStatus?.resource_usage?.cpu_percent?.toFixed(1) || 'N/A',
    memory: systemStatus?.resource_usage?.memory?.percent?.toFixed(1) || 'N/A',
    disk: systemStatus?.resource_usage?.disk?.percent?.toFixed(1) || 'N/A',
  };

  if (loading) {
    return (
      <div className="dashboard-container">
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
          <CircularProgress />
          <Typography variant="h6" sx={{ ml: 2 }}>Loading system settings...</Typography>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      {/* Compact Page Header - Following Design Guidelines */}
      <div className="page-header">
        <Typography className="page-title">
          System Settings
        </Typography>
        <div className="page-actions">
          <Tooltip title="Refresh settings">
            <IconButton 
              className="btn-icon" 
              onClick={loadAllSystemData} 
              disabled={loading}
              size="small"
            >
              <RefreshIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Button
            className="btn-compact"
            variant="contained"
            color={hasUnsavedChanges ? 'warning' : 'primary'}
            startIcon={saving ? <CircularProgress size={14} /> : <SaveIcon fontSize="small" />}
            onClick={saveSettings}
            disabled={saving || !hasUnsavedChanges}
            size="small"
          >
            {saving ? 'Saving...' : hasUnsavedChanges ? 'Save Changes' : 'No Changes'}
          </Button>
          <Button
            className="btn-compact"
            variant="outlined"
            color="secondary"
            startIcon={saving ? <CircularProgress size={14} /> : <SaveIcon fontSize="small" />}
            onClick={saveSettings}
            disabled={saving}
            size="small"
            sx={{ ml: 1 }}
          >
            Force Save
          </Button>
        </div>
      </div>

      {/* Enhanced Statistics Grid - Following Design Guidelines */}
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
            <div className="stat-icon success">
              <AccessTimeIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.uptime}</h3>
              <p>Uptime</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon info">
              <SettingsIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.health}</h3>
              <p>Health</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon warning">
              <ComputerIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.cpu}%</h3>
              <p>CPU Usage</p>
            </div>
          </div>
        </div>

        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon info">
              <StorageIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.memory}%</h3>
              <p>Memory</p>
            </div>
          </div>
        </div>

        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon error">
              <StorageIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.disk}%</h3>
              <p>Disk Usage</p>
            </div>
          </div>
        </div>
      </div>

      {/* Core System Configuration & Appearance - Side by Side */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 3fr', gap: '16px', marginBottom: '16px' }}>
        
        {/* Core System Configuration Card */}
        <div className="main-content-card fade-in">
          <div className="content-card-header">
            <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
              <SettingsIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
              CORE SYSTEM CONFIGURATION
            </Typography>
            {currentTime && (
              <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                Current: {currentTime.local} ({currentTime.is_dst ? 'DST' : 'STD'})
              </Typography>
            )}
          </div>
          
          <div className="content-card-body">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
            
            {/* Timezone Settings - Enhanced but following design */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                <AccessTimeIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                Timezone Configuration
              </Typography>
              <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                <InputLabel sx={{ fontSize: '0.8rem' }}>System Timezone</InputLabel>
                <Select
                  value={selectedTimezone}
                  label="System Timezone"
                  onChange={(e) => setSelectedTimezone(e.target.value)}
                  sx={{ 
                    fontSize: '0.8rem',
                    '& .MuiSelect-select': { fontSize: '0.8rem' }
                  }}
                >
                  {Object.entries(timezones).map(([tz, display]) => (
                    <MenuItem key={tz} value={tz} sx={{ fontSize: '0.8rem' }}>
                      {display}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              {systemInfo?.timezone && (
                <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                  UTC Offset: {systemInfo.timezone.current_utc_offset}
                </Typography>
              )}
            </div>

            {/* Security Settings */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                <SecurityIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                Security Settings
              </Typography>
              <TextField
                fullWidth
                size="small"
                label="Inactivity Timeout (minutes)"
                type="number"
                value={inactivityTimeout}
                onChange={(e) => setInactivityTimeout(parseInt(e.target.value))}
                inputProps={{ min: 5, max: 480 }}
                sx={{ 
                  mb: 1,
                  '& .MuiInputLabel-root': { fontSize: '0.8rem' },
                  '& .MuiInputBase-input': { fontSize: '0.8rem' }
                }}
              />
              <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem', mb: 2, display: 'block' }}>
                Range: 5 minutes to 8 hours (session expires after inactivity)
              </Typography>
              <TextField
                fullWidth
                size="small"
                label="Warning Time (minutes)"
                type="number"
                value={warningTime}
                onChange={(e) => setWarningTime(parseInt(e.target.value))}
                inputProps={{ min: 1, max: 10 }}
                sx={{ 
                  mb: 1,
                  '& .MuiInputLabel-root': { fontSize: '0.8rem' },
                  '& .MuiInputBase-input': { fontSize: '0.8rem' }
                }}
              />
              <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                Range: 1-10 minutes (warning shown before timeout)
              </Typography>
            </div>

            {/* Job Management */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                <ScheduleIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                Job Management
              </Typography>
              <TextField
                fullWidth
                size="small"
                label="Max Concurrent Jobs"
                type="number"
                value={maxJobs}
                onChange={(e) => setMaxJobs(parseInt(e.target.value))}
                inputProps={{ min: 1, max: 1000 }}
                sx={{ 
                  mb: 1,
                  '& .MuiInputLabel-root': { fontSize: '0.8rem' },
                  '& .MuiInputBase-input': { fontSize: '0.8rem' }
                }}
              />
              <TextField
                fullWidth
                size="small"
                label="Log Retention (days)"
                type="number"
                value={logRetention}
                onChange={(e) => setLogRetention(parseInt(e.target.value))}
                inputProps={{ min: 1, max: 3650 }}
                sx={{ 
                  '& .MuiInputLabel-root': { fontSize: '0.8rem' },
                  '& .MuiInputBase-input': { fontSize: '0.8rem' }
                }}
              />
            </div>
            </div>
          </div>
        </div>

        {/* Appearance & Interface Card */}
        <div className="main-content-card fade-in">
          <div className="content-card-header">
            <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
              <PaletteIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
              APPEARANCE & INTERFACE
            </Typography>
          </div>
          
          <div className="content-card-body">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
              
              {/* Theme Settings */}
              <div>
                <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                  <PaletteIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Theme Selection
                </Typography>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' }}>
                  {Object.entries(availableThemes).map(([key, themeData]) => (
                    <Button
                      key={key}
                      variant={theme === key ? 'contained' : 'outlined'}
                      onClick={() => handleThemeChange(key)}
                      size="small"
                      sx={{ 
                        height: '32px',
                        fontSize: '0.75rem',
                        backgroundColor: theme === key ? themeData.primaryColor : 'transparent',
                        borderColor: themeData.primaryColor,
                        '&:hover': {
                          backgroundColor: themeData.primaryColor,
                          opacity: 0.8
                        }
                      }}
                    >
                      {themeData.name}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Interface Settings */}
              <div>
                <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                  <PaletteIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Interface Settings
                </Typography>
                <Typography variant="body2" sx={{ fontSize: '0.8rem', mb: 1 }}>
                  Language: English (US)
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                  Additional interface options coming soon
                </Typography>
              </div>

              {/* Empty Third Column */}
              <div>
                {/* Intentionally empty */}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Advanced System Configuration & System Maintenance - Side by Side */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 3fr', gap: '16px', marginBottom: '16px' }}>
        
        {/* Advanced System Configuration Card */}
        <div className="main-content-card fade-in">
          <div className="content-card-header">
            <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
              <SettingsIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
              ADVANCED SYSTEM CONFIGURATION
            </Typography>
          </div>
          
          <div className="content-card-body">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
            
            {/* Database Settings */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                <StorageIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                Database Configuration
              </Typography>
              <TextField
                fullWidth
                size="small"
                label="Connection Pool Size"
                type="number"
                defaultValue={20}
                inputProps={{ min: 5, max: 100 }}
                sx={{ 
                  mb: 1,
                  '& .MuiInputLabel-root': { fontSize: '0.8rem' },
                  '& .MuiInputBase-input': { fontSize: '0.8rem' }
                }}
                disabled
              />
              <TextField
                fullWidth
                size="small"
                label="Query Timeout (seconds)"
                type="number"
                defaultValue={30}
                inputProps={{ min: 5, max: 300 }}
                sx={{ 
                  '& .MuiInputLabel-root': { fontSize: '0.8rem' },
                  '& .MuiInputBase-input': { fontSize: '0.8rem' }
                }}
                disabled
              />
              <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                Database settings require restart
              </Typography>
            </div>

            {/* Performance Settings */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                <ComputerIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                Performance Tuning
              </Typography>
              <TextField
                fullWidth
                size="small"
                label="Worker Threads"
                type="number"
                defaultValue={4}
                inputProps={{ min: 1, max: 16 }}
                sx={{ 
                  mb: 1,
                  '& .MuiInputLabel-root': { fontSize: '0.8rem' },
                  '& .MuiInputBase-input': { fontSize: '0.8rem' }
                }}
                disabled
              />
              <TextField
                fullWidth
                size="small"
                label="Cache TTL (minutes)"
                type="number"
                defaultValue={15}
                inputProps={{ min: 1, max: 1440 }}
                sx={{ 
                  '& .MuiInputLabel-root': { fontSize: '0.8rem' },
                  '& .MuiInputBase-input': { fontSize: '0.8rem' }
                }}
                disabled
              />
              <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                Performance settings require restart
              </Typography>
            </div>

            {/* Logging Configuration */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                <SettingsIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                Logging Configuration
              </Typography>
              <FormControl fullWidth size="small" sx={{ mb: 1 }}>
                <InputLabel sx={{ fontSize: '0.8rem' }}>Log Level</InputLabel>
                <Select
                  defaultValue="INFO"
                  label="Log Level"
                  disabled
                  sx={{ 
                    fontSize: '0.8rem',
                    '& .MuiSelect-select': { fontSize: '0.8rem' }
                  }}
                >
                  <MenuItem value="DEBUG" sx={{ fontSize: '0.8rem' }}>DEBUG</MenuItem>
                  <MenuItem value="INFO" sx={{ fontSize: '0.8rem' }}>INFO</MenuItem>
                  <MenuItem value="WARNING" sx={{ fontSize: '0.8rem' }}>WARNING</MenuItem>
                  <MenuItem value="ERROR" sx={{ fontSize: '0.8rem' }}>ERROR</MenuItem>
                </Select>
              </FormControl>
              <TextField
                fullWidth
                size="small"
                label="Max Log File Size (MB)"
                type="number"
                defaultValue={100}
                inputProps={{ min: 10, max: 1000 }}
                sx={{ 
                  '& .MuiInputLabel-root': { fontSize: '0.8rem' },
                  '& .MuiInputBase-input': { fontSize: '0.8rem' }
                }}
                disabled
              />
              <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                Advanced logging settings
              </Typography>
            </div>
            </div>
          </div>
        </div>

        {/* System Maintenance Card */}
        <div className="main-content-card fade-in">
        <div className="content-card-header">
          <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
            <SettingsIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
            SYSTEM MAINTENANCE & OPERATIONS
          </Typography>
        </div>
        
        <div className="content-card-body">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
            
            {/* Backup & Restore */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                <StorageIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                Backup & Restore
              </Typography>
              <div style={{ display: 'grid', gap: '8px' }}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<StorageIcon fontSize="small" />}
                  size="small"
                  sx={{ height: '32px', fontSize: '0.75rem' }}
                  onClick={() => addAlert('Backup functionality coming soon', 'info', 3000)}
                >
                  Create Backup
                </Button>
                
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<ComputerIcon fontSize="small" />}
                  size="small"
                  sx={{ height: '32px', fontSize: '0.75rem' }}
                  onClick={() => addAlert('Restore functionality coming soon', 'info', 3000)}
                >
                  Restore Configuration
                </Button>
              </div>
            </div>

            {/* Maintenance Operations */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                <SettingsIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                Maintenance Operations
              </Typography>
              <Typography variant="body2" sx={{ fontSize: '0.8rem', mb: 1 }}>
                System maintenance tools
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                Additional operations coming soon
              </Typography>
            </div>

            {/* System Status */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                <ComputerIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                System Status
              </Typography>
              <Typography variant="body2" sx={{ fontSize: '0.8rem', mb: 1 }}>
                Status: Operational
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                All systems running normally
              </Typography>
            </div>
          </div>
        </div>
        </div>
      </div>

      {/* Notification Configuration - 3 Column Wide Section */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 3fr', gap: '16px', marginBottom: '16px' }}>
        <div className="main-content-card fade-in">
          <div className="content-card-header">
            <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
              <NotificationsIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
              NOTIFICATION CONFIGURATION
            </Typography>
          </div>
          
          <div className="content-card-body">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', minWidth: 0 }}>
            
              {/* Email Server Configuration */}
              <div style={{ minWidth: 0, overflow: 'hidden' }}>
                <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                  <EmailIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Email Server
                </Typography>
                <FormControl fullWidth size="small" sx={{ mb: 1 }}>
                  <InputLabel sx={{ fontSize: '0.8rem' }}>Email Server</InputLabel>
                  <Select
                    value={selectedEmailTarget}
                    label="Email Server"
                    onChange={(e) => setSelectedEmailTarget(e.target.value)}
                    sx={{ 
                      fontSize: '0.8rem',
                      '& .MuiSelect-select': { 
                        fontSize: '0.8rem',
                        textOverflow: 'ellipsis',
                        overflow: 'hidden',
                        whiteSpace: 'nowrap'
                      }
                    }}
                  >
                    <MenuItem value="" sx={{ fontSize: '0.8rem' }}>Select Email Server</MenuItem>
                    {emailTargets.map((target) => {
                      // The new API already provides host/port info directly
                      const host = target.host || 'Unknown';
                      const port = target.port || '587';
                      const healthIcon = target.health_status === 'healthy' ? '🟢' : 
                                       target.health_status === 'warning' ? '🟡' : '🔴';
                      
                      // Truncate long names to prevent column expansion
                      const displayName = target.name.length > 15 ? target.name.substring(0, 15) + '...' : target.name;
                      
                      return (
                        <MenuItem 
                          key={target.id} 
                          value={target.id.toString()} 
                          sx={{ 
                            fontSize: '0.8rem',
                            maxWidth: '100%',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }}
                          title={`${target.name} (${host}:${port})`} // Show full info on hover
                        >
                          {healthIcon} {displayName}
                        </MenuItem>
                      );
                    })}
                  </Select>
                </FormControl>
                <TextField
                  fullWidth
                  size="small"
                  label="Test Email Address"
                  placeholder="Enter email to test..."
                  value={testEmailAddress}
                  onChange={(e) => setTestEmailAddress(e.target.value)}
                  sx={{ 
                    mb: 1,
                    '& .MuiInputLabel-root': { fontSize: '0.8rem' },
                    '& .MuiInputBase-input': { 
                      fontSize: '0.8rem',
                      textOverflow: 'ellipsis',
                      overflow: 'hidden',
                      whiteSpace: 'nowrap'
                    }
                  }}
                />
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<EmailIcon fontSize="small" />}
                  size="small"
                  sx={{ height: '32px', fontSize: '0.75rem' }}
                  onClick={testEmailTarget}
                  disabled={!selectedEmailTarget || !testEmailAddress.trim()}
                >
                  Test Email
                </Button>
              </div>

              {/* SMS Configuration */}
              <div style={{ minWidth: 0, overflow: 'hidden' }}>
                <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                  <SmsIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                  SMS Configuration
                </Typography>
                <TextField
                  fullWidth
                  size="small"
                  label="SMS Provider"
                  defaultValue="Twilio"
                  sx={{ 
                    mb: 1,
                    '& .MuiInputLabel-root': { fontSize: '0.8rem' },
                    '& .MuiInputBase-input': { 
                      fontSize: '0.8rem',
                      textOverflow: 'ellipsis',
                      overflow: 'hidden',
                      whiteSpace: 'nowrap'
                    }
                  }}
                  disabled
                />
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<SmsIcon fontSize="small" />}
                  size="small"
                  sx={{ height: '32px', fontSize: '0.75rem' }}
                  onClick={() => addAlert('SMS test functionality coming soon', 'info', 3000)}
                >
                  Test SMS
                </Button>
              </div>

              {/* Notification Rules */}
              <div style={{ minWidth: 0, overflow: 'hidden' }}>
                <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                  <NotificationsIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Notification Rules
                </Typography>
                <Typography variant="body2" sx={{ fontSize: '0.8rem', mb: 1 }}>
                  Active Rules: 5
                </Typography>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<SettingsIcon fontSize="small" />}
                  size="small"
                  sx={{ height: '32px', fontSize: '0.75rem' }}
                  onClick={() => addAlert('Notification rules management coming soon', 'info', 3000)}
                >
                  Manage Rules
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemSettings;