import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography, Button, IconButton, Tooltip, Box, Card, CardContent,
  Grid, Tabs, Tab, TextField, Switch, FormControlLabel, Slider,
  Alert, Snackbar, CircularProgress, Divider, Accordion,
  AccordionSummary, AccordionDetails, Chip
} from '@mui/material';

// Icons
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import RefreshIcon from '@mui/icons-material/Refresh';
import SaveIcon from '@mui/icons-material/Save';
import RestoreIcon from '@mui/icons-material/Restore';
import SecurityIcon from '@mui/icons-material/Security';
import PasswordIcon from '@mui/icons-material/Password';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import AuditIcon from '@mui/icons-material/Assignment';
import PeopleIcon from '@mui/icons-material/People';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningIcon from '@mui/icons-material/Warning';
import InfoIcon from '@mui/icons-material/Info';

import { configService } from '../../services/configService';
import '../../styles/dashboard.css';

const AuthConfigManagement = () => {
  const navigate = useNavigate();
  
  // State management
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [currentTab, setCurrentTab] = useState(0);
  const [hasChanges, setHasChanges] = useState(false);
  
  // Configuration state
  const [config, setConfig] = useState({
    session: {
      timeout_minutes: 30,
      warning_minutes: 5,
      max_concurrent: 3,
      idle_timeout_minutes: 15,
      remember_me_days: 30
    },
    password: {
      min_length: 8,
      max_length: 128,
      require_uppercase: true,
      require_lowercase: true,
      require_numbers: true,
      require_special: true,
      special_chars: '!@#$%^&*()_+-=[]{}|;:,.<>?',
      expiry_days: 90,
      history_count: 5,
      min_age_hours: 24
    },
    security: {
      max_failed_attempts: 5,
      lockout_duration_minutes: 30,
      progressive_lockout: true,
      require_email_verification: true,
      force_password_change_first_login: true,
      enable_two_factor: false
    },
    audit: {
      log_all_events: true,
      retention_days: 365,
      log_failed_attempts: true
    },
    users: {
      default_role: 'user',
      allow_self_registration: false,
      require_admin_approval: true
    }
  });
  
  // Original config for comparison
  const [originalConfig, setOriginalConfig] = useState({});
  
  // Notifications
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });

  useEffect(() => {
    fetchConfiguration();
  }, []);

  useEffect(() => {
    // Check if there are changes
    const hasChanges = JSON.stringify(config) !== JSON.stringify(originalConfig);
    setHasChanges(hasChanges);
  }, [config, originalConfig]);

  const fetchConfiguration = async () => {
    setLoading(true);
    try {
      const data = await configService.getAllConfiguration();
      setConfig(data);
      setOriginalConfig(JSON.parse(JSON.stringify(data)));
    } catch (error) {
      console.error('Failed to fetch configuration:', error);
      showNotification('Failed to load configuration', 'error');
    } finally {
      setLoading(false);
    }
  };

  const saveConfiguration = async () => {
    setSaving(true);
    try {
      // Save each category separately
      const categories = ['session', 'password', 'security', 'audit', 'users'];
      
      for (const category of categories) {
        switch (category) {
          case 'session':
            await configService.updateSessionConfig(config[category]);
            break;
          case 'password':
            await configService.updatePasswordPolicy(config[category]);
            break;
          case 'security':
            await configService.updateSecurityConfig(config[category]);
            break;
          case 'audit':
            await configService.updateAuditConfig(config[category]);
            break;
          case 'users':
            await configService.updateUserManagementConfig(config[category]);
            break;
        }
      }
      
      setOriginalConfig(JSON.parse(JSON.stringify(config)));
      showNotification('Configuration saved successfully', 'success');
    } catch (error) {
      console.error('Failed to save configuration:', error);
      showNotification(error.message || 'Failed to save configuration', 'error');
    } finally {
      setSaving(false);
    }
  };

  const resetConfiguration = () => {
    setConfig(JSON.parse(JSON.stringify(originalConfig)));
  };

  const showNotification = (message, severity = 'info') => {
    setNotification({ open: true, message, severity });
  };

  const updateConfig = (category, field, value) => {
    setConfig(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [field]: value
      }
    }));
  };

  const TabPanel = ({ children, value, index, ...other }) => (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`config-tabpanel-${index}`}
      aria-labelledby={`config-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );

  const ConfigSection = ({ title, description, children, severity = 'info' }) => (
    <Accordion defaultExpanded>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {severity === 'warning' && <WarningIcon color="warning" />}
          {severity === 'error' && <WarningIcon color="error" />}
          {severity === 'success' && <CheckCircleIcon color="success" />}
          {severity === 'info' && <InfoIcon color="info" />}
          <Typography variant="h6">{title}</Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {description}
        </Typography>
        {children}
      </AccordionDetails>
    </Accordion>
  );

  return (
    <div className="dashboard-container">
      {/* Page Header */}
      <div className="page-header">
        <Typography className="page-title">
          Authentication Configuration
        </Typography>
        <div className="page-actions">
          <Tooltip title="Back to Dashboard">
            <IconButton onClick={() => navigate('/dashboard')} size="small">
              <ArrowBackIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Refresh Configuration">
            <IconButton onClick={fetchConfiguration} disabled={loading} size="small">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          {hasChanges && (
            <Tooltip title="Reset Changes">
              <Button
                variant="outlined"
                startIcon={<RestoreIcon />}
                onClick={resetConfiguration}
                size="small"
              >
                Reset
              </Button>
            </Tooltip>
          )}
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={saveConfiguration}
            disabled={!hasChanges || saving}
            size="small"
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </div>

      {/* Changes Alert */}
      {hasChanges && (
        <Alert severity="info" sx={{ mb: 2 }}>
          You have unsaved changes. Don't forget to save your configuration.
        </Alert>
      )}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {/* Configuration Tabs */}
          <Card>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={currentTab} onChange={(_, newValue) => setCurrentTab(newValue)}>
                <Tab icon={<AccessTimeIcon />} label="Session Management" />
                <Tab icon={<PasswordIcon />} label="Password Policy" />
                <Tab icon={<SecurityIcon />} label="Security Settings" />
                <Tab icon={<AuditIcon />} label="Audit & Compliance" />
                <Tab icon={<PeopleIcon />} label="User Management" />
              </Tabs>
            </Box>

            {/* Session Management Tab */}
            <TabPanel value={currentTab} index={0}>
              <ConfigSection
                title="Session Timeouts"
                description="Configure session timeout and warning settings"
                severity="info"
              >
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography gutterBottom>Session Timeout (minutes)</Typography>
                    <Slider
                      value={config.session.timeout_minutes}
                      onChange={(_, value) => updateConfig('session', 'timeout_minutes', value)}
                      min={5}
                      max={480}
                      step={5}
                      marks={[
                        { value: 15, label: '15m' },
                        { value: 30, label: '30m' },
                        { value: 60, label: '1h' },
                        { value: 240, label: '4h' }
                      ]}
                      valueLabelDisplay="on"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography gutterBottom>Warning Before Timeout (minutes)</Typography>
                    <Slider
                      value={config.session.warning_minutes}
                      onChange={(_, value) => updateConfig('session', 'warning_minutes', value)}
                      min={1}
                      max={15}
                      step={1}
                      valueLabelDisplay="on"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography gutterBottom>Idle Timeout (minutes)</Typography>
                    <Slider
                      value={config.session.idle_timeout_minutes}
                      onChange={(_, value) => updateConfig('session', 'idle_timeout_minutes', value)}
                      min={5}
                      max={120}
                      step={5}
                      valueLabelDisplay="on"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography gutterBottom>Max Concurrent Sessions</Typography>
                    <Slider
                      value={config.session.max_concurrent}
                      onChange={(_, value) => updateConfig('session', 'max_concurrent', value)}
                      min={1}
                      max={10}
                      step={1}
                      marks
                      valueLabelDisplay="on"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <Typography gutterBottom>Remember Me Duration (days)</Typography>
                    <Slider
                      value={config.session.remember_me_days}
                      onChange={(_, value) => updateConfig('session', 'remember_me_days', value)}
                      min={1}
                      max={90}
                      step={1}
                      marks={[
                        { value: 7, label: '1w' },
                        { value: 30, label: '1m' },
                        { value: 90, label: '3m' }
                      ]}
                      valueLabelDisplay="on"
                    />
                  </Grid>
                </Grid>
              </ConfigSection>
            </TabPanel>

            {/* Password Policy Tab */}
            <TabPanel value={currentTab} index={1}>
              <ConfigSection
                title="Password Requirements"
                description="Set password complexity and security requirements"
                severity="warning"
              >
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Minimum Length"
                      type="number"
                      value={config.password.min_length}
                      onChange={(e) => updateConfig('password', 'min_length', parseInt(e.target.value))}
                      inputProps={{ min: 4, max: 50 }}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Maximum Length"
                      type="number"
                      value={config.password.max_length}
                      onChange={(e) => updateConfig('password', 'max_length', parseInt(e.target.value))}
                      inputProps={{ min: 8, max: 256 }}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={config.password.require_uppercase}
                            onChange={(e) => updateConfig('password', 'require_uppercase', e.target.checked)}
                          />
                        }
                        label="Require Uppercase"
                      />
                      <FormControlLabel
                        control={
                          <Switch
                            checked={config.password.require_lowercase}
                            onChange={(e) => updateConfig('password', 'require_lowercase', e.target.checked)}
                          />
                        }
                        label="Require Lowercase"
                      />
                      <FormControlLabel
                        control={
                          <Switch
                            checked={config.password.require_numbers}
                            onChange={(e) => updateConfig('password', 'require_numbers', e.target.checked)}
                          />
                        }
                        label="Require Numbers"
                      />
                      <FormControlLabel
                        control={
                          <Switch
                            checked={config.password.require_special}
                            onChange={(e) => updateConfig('password', 'require_special', e.target.checked)}
                          />
                        }
                        label="Require Special Characters"
                      />
                    </Box>
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Allowed Special Characters"
                      value={config.password.special_chars}
                      onChange={(e) => updateConfig('password', 'special_chars', e.target.value)}
                      helperText="Characters that count as special characters"
                    />
                  </Grid>
                </Grid>
              </ConfigSection>

              <ConfigSection
                title="Password Lifecycle"
                description="Configure password expiration and history settings"
                severity="info"
              >
                <Grid container spacing={3}>
                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      label="Password Expiry (days)"
                      type="number"
                      value={config.password.expiry_days}
                      onChange={(e) => updateConfig('password', 'expiry_days', parseInt(e.target.value))}
                      inputProps={{ min: 0, max: 365 }}
                      helperText="0 = never expires"
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      label="Password History Count"
                      type="number"
                      value={config.password.history_count}
                      onChange={(e) => updateConfig('password', 'history_count', parseInt(e.target.value))}
                      inputProps={{ min: 0, max: 20 }}
                      helperText="Previous passwords to remember"
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      label="Minimum Age (hours)"
                      type="number"
                      value={config.password.min_age_hours}
                      onChange={(e) => updateConfig('password', 'min_age_hours', parseInt(e.target.value))}
                      inputProps={{ min: 0, max: 168 }}
                      helperText="Minimum time before password can be changed again"
                    />
                  </Grid>
                </Grid>
              </ConfigSection>
            </TabPanel>

            {/* Security Settings Tab */}
            <TabPanel value={currentTab} index={2}>
              <ConfigSection
                title="Account Lockout"
                description="Configure account lockout policies for failed login attempts"
                severity="error"
              >
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Max Failed Attempts"
                      type="number"
                      value={config.security.max_failed_attempts}
                      onChange={(e) => updateConfig('security', 'max_failed_attempts', parseInt(e.target.value))}
                      inputProps={{ min: 1, max: 20 }}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Lockout Duration (minutes)"
                      type="number"
                      value={config.security.lockout_duration_minutes}
                      onChange={(e) => updateConfig('security', 'lockout_duration_minutes', parseInt(e.target.value))}
                      inputProps={{ min: 1, max: 1440 }}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={config.security.progressive_lockout}
                          onChange={(e) => updateConfig('security', 'progressive_lockout', e.target.checked)}
                        />
                      }
                      label="Progressive Lockout (longer lockouts for repeated failures)"
                    />
                  </Grid>
                </Grid>
              </ConfigSection>

              <ConfigSection
                title="Account Verification"
                description="Configure account verification and security requirements"
                severity="warning"
              >
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={config.security.require_email_verification}
                          onChange={(e) => updateConfig('security', 'require_email_verification', e.target.checked)}
                        />
                      }
                      label="Require Email Verification for New Accounts"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={config.security.force_password_change_first_login}
                          onChange={(e) => updateConfig('security', 'force_password_change_first_login', e.target.checked)}
                        />
                      }
                      label="Force Password Change on First Login"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={config.security.enable_two_factor}
                          onChange={(e) => updateConfig('security', 'enable_two_factor', e.target.checked)}
                        />
                      }
                      label="Enable Two-Factor Authentication"
                    />
                  </Grid>
                </Grid>
              </ConfigSection>
            </TabPanel>

            {/* Audit & Compliance Tab */}
            <TabPanel value={currentTab} index={3}>
              <ConfigSection
                title="Audit Logging"
                description="Configure audit logging and retention policies"
                severity="success"
              >
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={config.audit.log_all_events}
                          onChange={(e) => updateConfig('audit', 'log_all_events', e.target.checked)}
                        />
                      }
                      label="Log All Authentication Events"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={config.audit.log_failed_attempts}
                          onChange={(e) => updateConfig('audit', 'log_failed_attempts', e.target.checked)}
                        />
                      }
                      label="Log Failed Login Attempts"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Log Retention (days)"
                      type="number"
                      value={config.audit.retention_days}
                      onChange={(e) => updateConfig('audit', 'retention_days', parseInt(e.target.value))}
                      inputProps={{ min: 30, max: 2555 }}
                      helperText="How long to keep audit logs"
                    />
                  </Grid>
                </Grid>
              </ConfigSection>
            </TabPanel>

            {/* User Management Tab */}
            <TabPanel value={currentTab} index={4}>
              <ConfigSection
                title="User Registration"
                description="Configure user registration and approval settings"
                severity="info"
              >
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Default Role for New Users"
                      value={config.users.default_role}
                      onChange={(e) => updateConfig('users', 'default_role', e.target.value)}
                      select
                      SelectProps={{ native: true }}
                    >
                      <option value="user">User</option>
                      <option value="manager">Manager</option>
                    </TextField>
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={config.users.allow_self_registration}
                          onChange={(e) => updateConfig('users', 'allow_self_registration', e.target.checked)}
                        />
                      }
                      label="Allow Self-Registration"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={config.users.require_admin_approval}
                          onChange={(e) => updateConfig('users', 'require_admin_approval', e.target.checked)}
                        />
                      }
                      label="Require Admin Approval for New Accounts"
                    />
                  </Grid>
                </Grid>
              </ConfigSection>
            </TabPanel>
          </Card>
        </>
      )}

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={() => setNotification({ ...notification, open: false })}
      >
        <Alert
          onClose={() => setNotification({ ...notification, open: false })}
          severity={notification.severity}
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </div>
  );
};

export default AuthConfigManagement;