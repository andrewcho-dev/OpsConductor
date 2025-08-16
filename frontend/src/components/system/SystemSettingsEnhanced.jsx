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
  Card,
  CardContent,
  CardHeader,
  Grid,
  Box,
  Chip,
  LinearProgress,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  AlertTitle,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Paper,
  Stack,
  Badge,
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
  Language as LanguageIcon,
  Public as PublicIcon,
  Memory as MemoryIcon,
  Speed as SpeedIcon,
  Dns as DnsIcon,
  Database as DatabaseIcon,
  CloudQueue as CloudQueueIcon,
  Notifications as NotificationsIcon,
  Backup as BackupIcon,
  RestartAlt as RestartAltIcon,
  Build as BuildIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  History as HistoryIcon,
} from '@mui/icons-material';
import { useTheme } from '../../contexts/ThemeContext';
import { useAlert } from '../layout/BottomStatusBar';

// Use centralized auth service with automatic token refresh and logout
const api = authService.api;



const SystemSettingsEnhanced = () => {
  // Existing state
  const [systemInfo, setSystemInfo] = useState(null);
  const [timezones, setTimezones] = useState({});
  const [currentTime, setCurrentTime] = useState(null);
  const [selectedTimezone, setSelectedTimezone] = useState('UTC');
  const [sessionTimeout, setSessionTimeout] = useState(28800);
  const [maxJobs, setMaxJobs] = useState(50);
  const [logRetention, setLogRetention] = useState(30);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // New enhanced state
  const [systemStatus, setSystemStatus] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);
  const [systemConfiguration, setSystemConfiguration] = useState(null);
  const [expandedSections, setExpandedSections] = useState({
    core: true,
    appearance: true,
    advanced: false,
    maintenance: false
  });
  const [confirmDialog, setConfirmDialog] = useState({ open: false, action: null, title: '', message: '' });
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);

  // New configuration state
  const [databaseConfig, setDatabaseConfig] = useState({
    poolSize: 20,
    timeout: 30,
    healthCheckInterval: 60
  });
  const [securityConfig, setSecurityConfig] = useState({
    jwtExpiry: 3600,
    passwordMinLength: 8,
    requireTwoFactor: false,
    sessionSecurity: 'standard'
  });
  const [performanceConfig, setPerformanceConfig] = useState({
    workerCount: 4,
    memoryLimit: 1024,
    cacheSize: 256
  });
  const [loggingConfig, setLoggingConfig] = useState({
    level: 'INFO',
    format: 'json',
    rotation: 'daily'
  });

  const { theme, changeTheme, availableThemes } = useTheme();
  const { addAlert } = useAlert();

  useEffect(() => {
    loadAllSystemData();
    const interval = setInterval(loadCurrentTime, 30000); // Update time every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadAllSystemData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadSystemInfo(),
        loadTimezones(),
        loadCurrentTime(),
        loadSystemStatus(),
        loadSystemHealth(),
        loadSystemConfiguration()
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
      const response = await api.get('/api/v2/system/info');
      setSystemInfo(response.data);
      setSelectedTimezone(response.data.timezone?.current || 'UTC');
      setSessionTimeout(response.data.session_timeout || 28800);
      setMaxJobs(response.data.max_concurrent_jobs || 50);
      setLogRetention(response.data.log_retention_days || 30);
    } catch (err) {
      console.error('Failed to load system information:', err);
      const errorMessage = err.response?.data?.detail || 'Failed to load system information';
      addAlert(errorMessage, 'error', 0);
    }
  };

  const loadTimezones = async () => {
    try {
      const response = await api.get('/api/v2/system/timezones');
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
      const response = await api.get('/api/v2/system/current-time');
      setCurrentTime(response.data);
    } catch (err) {
      console.error('Failed to load current time:', err);
    }
  };

  const loadSystemStatus = async () => {
    try {
      const response = await api.get('/api/v2/system/status');
      setSystemStatus(response.data);
    } catch (err) {
      console.error('Failed to load system status:', err);
    }
  };

  const loadSystemHealth = async () => {
    try {
      const response = await api.get('/api/v2/system/health');
      setSystemHealth(response.data);
    } catch (err) {
      console.error('Failed to load system health:', err);
    }
  };

  const loadSystemConfiguration = async () => {
    try {
      const response = await api.get('/api/v2/system/configuration');
      setSystemConfiguration(response.data);
      
      // Update local config state from response
      if (response.data.database) {
        setDatabaseConfig(prev => ({ ...prev, ...response.data.database }));
      }
      if (response.data.security) {
        setSecurityConfig(prev => ({ ...prev, ...response.data.security }));
      }
    } catch (err) {
      console.error('Failed to load system configuration:', err);
    }
  };

  const saveSettings = async () => {
    try {
      setSaving(true);
      
      // Save all settings in parallel
      const promises = [
        api.put('/api/v2/system/timezone', { timezone: selectedTimezone }),
        api.put('/api/v2/system/session-timeout', { timeout_seconds: sessionTimeout }),
        api.put('/api/v2/system/max-concurrent-jobs', { max_jobs: maxJobs }),
        api.put('/api/v2/system/log-retention', { retention_days: logRetention })
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

  const saveAdvancedConfiguration = async () => {
    try {
      setSaving(true);
      
      const configUpdate = {
        database: databaseConfig,
        security: securityConfig,
        application: {
          performance: performanceConfig,
          logging: loggingConfig
        }
      };
      
      await api.put('/api/v2/system/configuration', configUpdate);
      await loadSystemConfiguration();
      addAlert('Advanced configuration saved successfully', 'success', 3000);
    } catch (err) {
      console.error('Failed to save advanced configuration:', err);
      const errorMessage = err.response?.data?.detail || 'Failed to save advanced configuration';
      addAlert(errorMessage, 'error', 0);
    } finally {
      setSaving(false);
    }
  };

  const handleThemeChange = (themeKey) => {
    changeTheme(themeKey);
    addAlert(`Theme changed to ${availableThemes[themeKey].name}`, 'success', 3000);
  };

  const handleSectionToggle = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const handleConfirmAction = (action, title, message) => {
    setConfirmDialog({
      open: true,
      action,
      title,
      message
    });
  };

  const executeConfirmedAction = async () => {
    const { action } = confirmDialog;
    setConfirmDialog({ open: false, action: null, title: '', message: '' });
    
    try {
      switch (action) {
        case 'restart':
          await api.post('/api/v2/system/restart');
          addAlert('System restart initiated', 'info', 5000);
          break;
        case 'backup':
          await api.post('/api/v2/system/backup');
          addAlert('Configuration backup created', 'success', 3000);
          break;
        case 'maintenance':
          await api.post('/api/v2/system/maintenance-mode');
          addAlert('Maintenance mode toggled', 'info', 3000);
          break;
        default:
          break;
      }
    } catch (err) {
      addAlert(`Failed to execute ${action}`, 'error', 5000);
    }
  };

  const getHealthStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy': return 'success';
      case 'warning': return 'warning';
      case 'error': case 'critical': return 'error';
      default: return 'info';
    }
  };

  const getHealthStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy': return <CheckCircleIcon />;
      case 'warning': return <WarningIcon />;
      case 'error': case 'critical': return <ErrorIcon />;
      default: return <InfoIcon />;
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatUptime = (uptime) => {
    if (!uptime) return 'N/A';
    return uptime;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>Loading system settings...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, maxWidth: '1400px', margin: '0 auto' }}>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 1, display: 'flex', alignItems: 'center' }}>
          <SettingsIcon sx={{ mr: 2, fontSize: '2rem' }} />
          System Settings
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Configure system-wide settings, monitor health, and manage advanced options
        </Typography>
      </Box>

      {/* System Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <ComputerIcon sx={{ fontSize: '2rem', color: 'primary.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {systemInfo?.version || '1.0.0'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Version
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <AccessTimeIcon sx={{ fontSize: '2rem', color: 'success.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {formatUptime(systemStatus?.uptime)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Uptime
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Badge 
                badgeContent={systemHealth?.overall_health === 'healthy' ? '✓' : '!'}
                color={getHealthStatusColor(systemHealth?.overall_health)}
              >
                {getHealthStatusIcon(systemHealth?.overall_health)}
              </Badge>
              <Typography variant="h6" sx={{ fontWeight: 600, mt: 1 }}>
                {systemHealth?.overall_health || 'Unknown'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Health
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <SpeedIcon sx={{ fontSize: '2rem', color: 'warning.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {systemStatus?.resource_usage?.cpu_percent?.toFixed(1) || 'N/A'}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                CPU Usage
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <MemoryIcon sx={{ fontSize: '2rem', color: 'info.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {systemStatus?.resource_usage?.memory?.percent?.toFixed(1) || 'N/A'}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Memory
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <StorageIcon sx={{ fontSize: '2rem', color: 'secondary.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {systemStatus?.resource_usage?.disk?.percent?.toFixed(1) || 'N/A'}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Disk Usage
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* System Alerts */}
      {systemStatus?.alerts && systemStatus.alerts.length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <AlertTitle>System Alerts</AlertTitle>
          {systemStatus.alerts.map((alert, index) => (
            <Typography key={index} variant="body2">
              • {alert.message}
            </Typography>
          ))}
        </Alert>
      )}

      {/* Core System Configuration */}
      <Accordion 
        expanded={expandedSections.core} 
        onChange={() => handleSectionToggle('core')}
        sx={{ mb: 2 }}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <SettingsIcon sx={{ mr: 2 }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Core System Configuration & Appearance
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            {/* Core System Configuration - 3 columns */}
            <Grid item xs={12} md={3}>
              <Grid container spacing={2}>
                {/* Timezone Configuration */}
                <Grid item xs={12}>
                  <Card sx={{ height: '100%' }}>
                    <CardHeader 
                      avatar={<PublicIcon />}
                      title="Timezone"
                      subheader={currentTime && `${currentTime.local.split(' ')[1]}`}
                      titleTypographyProps={{ variant: 'subtitle2', fontWeight: 600 }}
                      subheaderTypographyProps={{ variant: 'caption' }}
                    />
                    <CardContent sx={{ pt: 0 }}>
                      <FormControl fullWidth size="small" sx={{ mb: 1 }}>
                        <InputLabel>System Timezone</InputLabel>
                        <Select
                          value={selectedTimezone}
                          label="System Timezone"
                          onChange={(e) => setSelectedTimezone(e.target.value)}
                        >
                          {Object.entries(timezones).map(([tz, display]) => (
                            <MenuItem key={tz} value={tz}>
                              {display}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                      {systemInfo?.timezone && (
                        <Typography variant="caption" color="text.secondary">
                          UTC: {systemInfo.timezone.current_utc_offset}
                        </Typography>
                      )}
                    </CardContent>
                  </Card>
                </Grid>

                {/* Security Settings */}
                <Grid item xs={12}>
                  <Card sx={{ height: '100%' }}>
                    <CardHeader 
                      avatar={<SecurityIcon />}
                      title="Security"
                      subheader="Session timeout"
                      titleTypographyProps={{ variant: 'subtitle2', fontWeight: 600 }}
                      subheaderTypographyProps={{ variant: 'caption' }}
                    />
                    <CardContent sx={{ pt: 0 }}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Session Timeout (sec)"
                        type="number"
                        value={sessionTimeout}
                        onChange={(e) => setSessionTimeout(parseInt(e.target.value))}
                        inputProps={{ min: 60, max: 86400 }}
                        sx={{ mb: 1 }}
                      />
                      <Typography variant="caption" color="text.secondary">
                        60s - 24h range
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                {/* Job Management */}
                <Grid item xs={12}>
                  <Card sx={{ height: '100%' }}>
                    <CardHeader 
                      avatar={<CloudQueueIcon />}
                      title="Jobs"
                      subheader="Execution limits"
                      titleTypographyProps={{ variant: 'subtitle2', fontWeight: 600 }}
                      subheaderTypographyProps={{ variant: 'caption' }}
                    />
                    <CardContent sx={{ pt: 0 }}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Max Concurrent"
                        type="number"
                        value={maxJobs}
                        onChange={(e) => setMaxJobs(parseInt(e.target.value))}
                        inputProps={{ min: 1, max: 1000 }}
                        sx={{ mb: 1 }}
                      />
                      <TextField
                        fullWidth
                        size="small"
                        label="Log Retention (days)"
                        type="number"
                        value={logRetention}
                        onChange={(e) => setLogRetention(parseInt(e.target.value))}
                        inputProps={{ min: 1, max: 3650 }}
                      />
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Grid>

            {/* Appearance & Interface - 2 columns */}
            <Grid item xs={12} md={2}>
              <Grid container spacing={2}>
                {/* Theme Settings */}
                <Grid item xs={12}>
                  <Card sx={{ height: '100%' }}>
                    <CardHeader 
                      avatar={<PaletteIcon />}
                      title="Theme"
                      subheader="Visual style"
                      titleTypographyProps={{ variant: 'subtitle2', fontWeight: 600 }}
                      subheaderTypographyProps={{ variant: 'caption' }}
                    />
                    <CardContent sx={{ pt: 0 }}>
                      <Grid container spacing={1}>
                        {Object.entries(availableThemes).map(([key, themeData]) => (
                          <Grid item xs={6} key={key}>
                            <Button
                              fullWidth
                              size="small"
                              variant={theme === key ? 'contained' : 'outlined'}
                              onClick={() => handleThemeChange(key)}
                              sx={{ 
                                height: '40px',
                                fontSize: '0.7rem',
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
                          </Grid>
                        ))}
                      </Grid>
                    </CardContent>
                  </Card>
                </Grid>

                {/* UI Settings */}
                <Grid item xs={12}>
                  <Card sx={{ height: '100%' }}>
                    <CardHeader 
                      avatar={<LanguageIcon />}
                      title="Interface"
                      subheader="Language & format"
                      titleTypographyProps={{ variant: 'subtitle2', fontWeight: 600 }}
                      subheaderTypographyProps={{ variant: 'caption' }}
                    />
                    <CardContent sx={{ pt: 0 }}>
                      <FormControl fullWidth size="small" sx={{ mb: 1 }}>
                        <InputLabel>Language</InputLabel>
                        <Select value="en" label="Language">
                          <MenuItem value="en">English</MenuItem>
                          <MenuItem value="es">Español</MenuItem>
                          <MenuItem value="fr">Français</MenuItem>
                        </Select>
                      </FormControl>
                      <FormControl fullWidth size="small">
                        <InputLabel>Date Format</InputLabel>
                        <Select value="MM/DD/YYYY" label="Date Format">
                          <MenuItem value="MM/DD/YYYY">MM/DD/YYYY</MenuItem>
                          <MenuItem value="DD/MM/YYYY">DD/MM/YYYY</MenuItem>
                          <MenuItem value="YYYY-MM-DD">YYYY-MM-DD</MenuItem>
                        </Select>
                      </FormControl>
                    </CardContent>
                  </Card>
                </Grid>

                {/* Notification Settings */}
                <Grid item xs={12}>
                  <Card sx={{ height: '100%' }}>
                    <CardHeader 
                      avatar={<NotificationsIcon />}
                      title="Notifications"
                      subheader="Alert settings"
                      titleTypographyProps={{ variant: 'subtitle2', fontWeight: 600 }}
                      subheaderTypographyProps={{ variant: 'caption' }}
                    />
                    <CardContent sx={{ pt: 0 }}>
                      <Stack spacing={1}>
                        <FormControlLabel
                          control={<Switch defaultChecked size="small" />}
                          label="System Alerts"
                          componentsProps={{ typography: { variant: 'caption' } }}
                        />
                        <FormControlLabel
                          control={<Switch defaultChecked size="small" />}
                          label="Job Notifications"
                          componentsProps={{ typography: { variant: 'caption' } }}
                        />
                        <FormControlLabel
                          control={<Switch size="small" />}
                          label="Email Notifications"
                          componentsProps={{ typography: { variant: 'caption' } }}
                        />
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>



      {/* Advanced System Configuration */}
      <Accordion 
        expanded={expandedSections.advanced} 
        onChange={() => handleSectionToggle('advanced')}
        sx={{ mb: 2 }}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <BuildIcon sx={{ mr: 2 }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Advanced Configuration & Maintenance
            </Typography>
            <Chip 
              label="Advanced" 
              size="small" 
              color="warning" 
              sx={{ ml: 2 }} 
            />
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Alert severity="warning" sx={{ mb: 3 }}>
            <AlertTitle>Advanced Settings</AlertTitle>
            These settings can significantly impact system performance. Change with caution.
          </Alert>
          
          <Grid container spacing={2}>
            {/* Advanced System Configuration - 3 columns */}
            <Grid item xs={12} md={3}>
              <Grid container spacing={2}>
                {/* Database Configuration */}
                <Grid item xs={12}>
                  <Card sx={{ height: '100%' }}>
                    <CardHeader 
                      avatar={<DatabaseIcon />}
                      title="Database"
                      subheader="Connection settings"
                      titleTypographyProps={{ variant: 'subtitle2', fontWeight: 600 }}
                      subheaderTypographyProps={{ variant: 'caption' }}
                    />
                    <CardContent sx={{ pt: 0 }}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Pool Size"
                        type="number"
                        value={databaseConfig.poolSize}
                        onChange={(e) => setDatabaseConfig(prev => ({ ...prev, poolSize: parseInt(e.target.value) }))}
                        sx={{ mb: 1 }}
                      />
                      <TextField
                        fullWidth
                        size="small"
                        label="Timeout (sec)"
                        type="number"
                        value={databaseConfig.timeout}
                        onChange={(e) => setDatabaseConfig(prev => ({ ...prev, timeout: parseInt(e.target.value) }))}
                        sx={{ mb: 1 }}
                      />
                      <TextField
                        fullWidth
                        size="small"
                        label="Health Check (sec)"
                        type="number"
                        value={databaseConfig.healthCheckInterval}
                        onChange={(e) => setDatabaseConfig(prev => ({ ...prev, healthCheckInterval: parseInt(e.target.value) }))}
                      />
                    </CardContent>
                  </Card>
                </Grid>

                {/* Performance Settings */}
                <Grid item xs={12}>
                  <Card sx={{ height: '100%' }}>
                    <CardHeader 
                      avatar={<SpeedIcon />}
                      title="Performance"
                      subheader="Resource allocation"
                      titleTypographyProps={{ variant: 'subtitle2', fontWeight: 600 }}
                      subheaderTypographyProps={{ variant: 'caption' }}
                    />
                    <CardContent sx={{ pt: 0 }}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Workers"
                        type="number"
                        value={performanceConfig.workerCount}
                        onChange={(e) => setPerformanceConfig(prev => ({ ...prev, workerCount: parseInt(e.target.value) }))}
                        sx={{ mb: 1 }}
                      />
                      <TextField
                        fullWidth
                        size="small"
                        label="Memory (MB)"
                        type="number"
                        value={performanceConfig.memoryLimit}
                        onChange={(e) => setPerformanceConfig(prev => ({ ...prev, memoryLimit: parseInt(e.target.value) }))}
                        sx={{ mb: 1 }}
                      />
                      <TextField
                        fullWidth
                        size="small"
                        label="Cache (MB)"
                        type="number"
                        value={performanceConfig.cacheSize}
                        onChange={(e) => setPerformanceConfig(prev => ({ ...prev, cacheSize: parseInt(e.target.value) }))}
                      />
                    </CardContent>
                  </Card>
                </Grid>

                {/* Logging Configuration */}
                <Grid item xs={12}>
                  <Card sx={{ height: '100%' }}>
                    <CardHeader 
                      avatar={<VisibilityIcon />}
                      title="Logging"
                      subheader="Debug & monitoring"
                      titleTypographyProps={{ variant: 'subtitle2', fontWeight: 600 }}
                      subheaderTypographyProps={{ variant: 'caption' }}
                    />
                    <CardContent sx={{ pt: 0 }}>
                      <FormControl fullWidth size="small" sx={{ mb: 1 }}>
                        <InputLabel>Level</InputLabel>
                        <Select
                          value={loggingConfig.level}
                          label="Level"
                          onChange={(e) => setLoggingConfig(prev => ({ ...prev, level: e.target.value }))}
                        >
                          <MenuItem value="DEBUG">DEBUG</MenuItem>
                          <MenuItem value="INFO">INFO</MenuItem>
                          <MenuItem value="WARNING">WARNING</MenuItem>
                          <MenuItem value="ERROR">ERROR</MenuItem>
                        </Select>
                      </FormControl>
                      <FormControl fullWidth size="small" sx={{ mb: 1 }}>
                        <InputLabel>Format</InputLabel>
                        <Select
                          value={loggingConfig.format}
                          label="Format"
                          onChange={(e) => setLoggingConfig(prev => ({ ...prev, format: e.target.value }))}
                        >
                          <MenuItem value="json">JSON</MenuItem>
                          <MenuItem value="text">Text</MenuItem>
                        </Select>
                      </FormControl>
                      <FormControl fullWidth size="small">
                        <InputLabel>Rotation</InputLabel>
                        <Select
                          value={loggingConfig.rotation}
                          label="Rotation"
                          onChange={(e) => setLoggingConfig(prev => ({ ...prev, rotation: e.target.value }))}
                        >
                          <MenuItem value="daily">Daily</MenuItem>
                          <MenuItem value="weekly">Weekly</MenuItem>
                          <MenuItem value="monthly">Monthly</MenuItem>
                        </Select>
                      </FormControl>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Grid>

            {/* System Maintenance & Operations - 1 column */}
            <Grid item xs={12} md={1}>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <Card sx={{ height: '100%' }}>
                    <CardHeader 
                      avatar={<BackupIcon />}
                      title="Maintenance"
                      subheader="Config operations"
                      titleTypographyProps={{ variant: 'subtitle2', fontWeight: 600 }}
                      subheaderTypographyProps={{ variant: 'caption' }}
                    />
                    <CardContent sx={{ pt: 0 }}>
                      <Button
                        fullWidth
                        variant="outlined"
                        startIcon={<BackupIcon />}
                        onClick={() => handleConfirmAction('backup', 'Create Configuration Backup', 'This will create a backup of all system configurations.')}
                        sx={{ mb: 1, height: '40px', fontSize: '0.7rem' }}
                      >
                        Backup
                      </Button>
                      <Button
                        fullWidth
                        variant="outlined"
                        startIcon={<UploadIcon />}
                        sx={{ height: '40px', fontSize: '0.7rem' }}
                      >
                        Restore
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>



      {/* Action Buttons */}
      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', mt: 4 }}>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={loadAllSystemData}
          disabled={loading}
        >
          Refresh All
        </Button>
        <Button
          variant="outlined"
          startIcon={<SaveIcon />}
          onClick={saveAdvancedConfiguration}
          disabled={saving}
        >
          Save Advanced Settings
        </Button>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={saveSettings}
          disabled={saving}
        >
          {saving ? <CircularProgress size={20} /> : 'Save Core Settings'}
        </Button>
      </Box>

      {/* Confirmation Dialog */}
      <Dialog
        open={confirmDialog.open}
        onClose={() => setConfirmDialog({ open: false, action: null, title: '', message: '' })}
      >
        <DialogTitle>{confirmDialog.title}</DialogTitle>
        <DialogContent>
          <Typography>{confirmDialog.message}</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({ open: false, action: null, title: '', message: '' })}>
            Cancel
          </Button>
          <Button onClick={executeConfirmedAction} color="primary" variant="contained">
            Confirm
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SystemSettingsEnhanced;