import React, { useState, useEffect } from 'react';
import {
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  CircularProgress,
  Alert,
  Box,
  Chip,
  TextField,
  Grid,
  Paper,
  Divider
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Send as SendIcon,
  Refresh as RefreshIcon,
  Email as EmailIcon
} from '@mui/icons-material';

const EmailTargetSelector = ({ onConfigUpdate }) => {
  const [eligibleTargets, setEligibleTargets] = useState([]);
  const [selectedTargetId, setSelectedTargetId] = useState('');
  const [currentConfig, setCurrentConfig] = useState(null);
  const [testEmail, setTestEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    fetchEligibleTargets();
    fetchCurrentConfig();
  }, []);

  const fetchEligibleTargets = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/notifications/email-targets/eligible');
      if (response.ok) {
        const targets = await response.json();
        setEligibleTargets(targets);
      } else {
        setMessage({ type: 'error', text: 'Failed to load eligible email targets' });
      }
    } catch (error) {
      console.error('Error fetching eligible targets:', error);
      setMessage({ type: 'error', text: 'Failed to load eligible email targets' });
    } finally {
      setLoading(false);
    }
  };

  const fetchCurrentConfig = async () => {
    try {
      const response = await fetch('/api/notifications/email-target/config');
      if (response.ok) {
        const config = await response.json();
        setCurrentConfig(config);
        if (config.target_id) {
          setSelectedTargetId(config.target_id.toString());
        }
      }
    } catch (error) {
      console.error('Error fetching current config:', error);
    }
  };

  const handleTargetChange = (event) => {
    setSelectedTargetId(event.target.value);
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const response = await fetch('/api/notifications/email-target/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          target_id: selectedTargetId ? parseInt(selectedTargetId) : null
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setCurrentConfig(result);
        setMessage({ type: 'success', text: 'Email target configuration saved successfully' });
        if (onConfigUpdate) {
          onConfigUpdate(result);
        }
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || 'Failed to save configuration' });
      }
    } catch (error) {
      console.error('Error saving config:', error);
      setMessage({ type: 'error', text: 'Failed to save email target configuration' });
    } finally {
      setSaving(false);
    }
  };

  const handleTestEmail = async () => {
    if (!testEmail) {
      setMessage({ type: 'error', text: 'Please enter a test email address' });
      return;
    }

    try {
      setTesting(true);
      const response = await fetch('/api/notifications/email-target/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          to_email: testEmail,
          subject: 'EnableDRM Email Target Test',
          body: 'This is a test email from EnableDRM to verify email target configuration.',
          html_body: '<p>This is a test email from <strong>EnableDRM</strong> to verify email target configuration.</p>'
        }),
      });

      const result = await response.json();
      if (result.success) {
        setMessage({ type: 'success', text: 'Test email sent successfully!' });
      } else {
        setMessage({ type: 'error', text: result.message || 'Failed to send test email' });
      }
    } catch (error) {
      console.error('Error sending test email:', error);
      setMessage({ type: 'error', text: 'Failed to send test email' });
    } finally {
      setTesting(false);
    }
  };

  const getHealthStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon color="success" fontSize="small" />;
      case 'warning':
        return <WarningIcon color="warning" fontSize="small" />;
      case 'critical':
        return <ErrorIcon color="error" fontSize="small" />;
      default:
        return <WarningIcon color="disabled" fontSize="small" />;
    }
  };

  const getHealthStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'warning':
        return 'warning';
      case 'critical':
        return 'error';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <CircularProgress size={20} />
        <Typography variant="body2" sx={{ ml: 1, fontSize: '0.75rem' }}>
          Loading email targets...
        </Typography>
      </div>
    );
  }

  return (
    <div>
      {message && (
        <Alert 
          severity={message.type} 
          onClose={() => setMessage(null)}
          sx={{ mb: 2, fontSize: '0.75rem' }}
        >
          {message.text}
        </Alert>
      )}

      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
        <FormControl size="small" sx={{ minWidth: 250 }}>
          <InputLabel sx={{ fontSize: '0.75rem' }}>Email Server</InputLabel>
          <Select
            value={selectedTargetId}
            onChange={handleTargetChange}
            label="Email Server"
            disabled={saving}
            sx={{ fontSize: '0.75rem' }}
          >
            <MenuItem value="" sx={{ fontSize: '0.75rem' }}>
              <em>None selected</em>
            </MenuItem>
            {eligibleTargets.map((target) => (
              <MenuItem key={target.id} value={target.id.toString()} sx={{ fontSize: '0.75rem' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                  {getHealthStatusIcon(target.health_status)}
                  <Box sx={{ ml: 1, flexGrow: 1 }}>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', fontWeight: 500 }}>
                      {target.name}
                    </Typography>
                    <Typography variant="caption" sx={{ fontSize: '0.65rem', color: 'text.secondary' }}>
                      {target.host}:{target.port}
                    </Typography>
                  </Box>
                  <Chip
                    label={target.health_status}
                    size="small"
                    color={getHealthStatusColor(target.health_status)}
                    sx={{ fontSize: '0.6rem', height: '18px' }}
                  />
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={saving || !selectedTargetId}
          size="small"
          sx={{ fontSize: '0.7rem' }}
        >
          {saving ? <CircularProgress size={16} /> : 'Save'}
        </Button>
      </Box>

      {eligibleTargets.length === 0 && (
        <Alert severity="warning" sx={{ mt: 2, fontSize: '0.75rem' }}>
          No eligible email targets found. Create a Universal Target with SMTP configuration.
        </Alert>
      )}

      {/* Test Email Section - Only show if a target is selected and configured */}
      {currentConfig && currentConfig.target_id && (
        <Box sx={{ mt: 3, p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
          <Typography variant="subtitle2" sx={{ mb: 2, fontSize: '0.8rem', fontWeight: 600 }}>
            Send Test Email
          </Typography>
          
          <Alert severity="info" sx={{ mb: 2, fontSize: '0.7rem' }}>
            <strong>Note:</strong> This will send an actual email to the specified address to verify the email server configuration.
            Health checks only test connectivity without sending emails.
          </Alert>
          
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
            <TextField
              size="small"
              label="Test Email Address"
              value={testEmail}
              onChange={(e) => setTestEmail(e.target.value)}
              placeholder="user@example.com"
              type="email"
              sx={{ flexGrow: 1, fontSize: '0.75rem' }}
              InputLabelProps={{ sx: { fontSize: '0.75rem' } }}
              InputProps={{ sx: { fontSize: '0.75rem' } }}
            />
            <Button
              variant="outlined"
              onClick={handleTestEmail}
              disabled={testing || !testEmail || !currentConfig?.target_id}
              size="small"
              sx={{ fontSize: '0.7rem', minWidth: '120px' }}
            >
              {testing ? <CircularProgress size={16} /> : 'Send Test Email'}
            </Button>
          </Box>
          
          <Typography variant="caption" sx={{ mt: 1, display: 'block', color: 'text.secondary', fontSize: '0.65rem' }}>
            This will send a real email to verify SMTP functionality. Use a valid email address you can access.
          </Typography>
        </Box>
      )}
    </div>
  );
};

export default EmailTargetSelector;