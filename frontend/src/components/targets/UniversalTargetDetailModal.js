/**
 * Universal Target Detail Modal - Professional Design
 * Modern, organized view of complete target information with intuitive actions.
 */
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogActions,
  Button,
  Typography,
  Box,
  Grid,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  Divider,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  CardHeader,
  Avatar,
  Stack,
  Badge,
  Fade,
  Slide
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  NetworkCheck as NetworkCheckIcon,
  Computer as ComputerIcon,
  Security as SecurityIcon,
  Info as InfoIcon,
  Close as CloseIcon,
  Storage as StorageIcon,
  LocationOn as LocationIcon,
  Schedule as ScheduleIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Settings as SettingsIcon,
  VpnKey as VpnKeyIcon,
  Router as RouterIcon
} from '@mui/icons-material';

import { deleteTarget, testCommunicationMethod, getTargetById } from '../../services/targetService';
import CommunicationMethodsManager from './CommunicationMethodsManager';

const UniversalTargetDetailModal = ({ 
  open, 
  target, 
  onClose, 
  onEditTarget, 
  onDeleteTarget 
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [fullTarget, setFullTarget] = useState(null);
  const [loadingTarget, setLoadingTarget] = useState(false);
  const [showMethodsManager, setShowMethodsManager] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [showTestResult, setShowTestResult] = useState(false);

  // Load full target details when modal opens
  useEffect(() => {
    const loadFullTarget = async () => {
      if (open && target?.id && !fullTarget) {
        try {
          setLoadingTarget(true);
          setError('');
          const targetDetails = await getTargetById(target.id);
          setFullTarget(targetDetails);
        } catch (err) {
          setError(`Failed to load target details: ${err.message}`);
        } finally {
          setLoadingTarget(false);
        }
      }
    };

    loadFullTarget();
  }, [open, target?.id, fullTarget]);

  // Reset when modal closes
  useEffect(() => {
    if (!open) {
      setFullTarget(null);
      setLoadingTarget(false);
      setError('');
    }
  }, [open]);

  const handleClose = () => {
    setError('');
    onClose();
  };

  const handleDelete = async () => {
    if (window.confirm(`Are you sure you want to delete target "${target.name}"?\n\nThis action cannot be undone.`)) {
      try {
        setLoading(true);
        setError('');
        await deleteTarget(target.id);
        onDeleteTarget();
        handleClose();
      } catch (err) {
        setError(`Failed to delete target: ${err.message}`);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleTestConnection = async (methodId) => {
    try {
      setLoading(true);
      setError('');
      
      // Test the specific communication method
      const result = await testCommunicationMethod(target.id, methodId);
      
      // Store test result and show dialog
      setTestResult(result);
      setShowTestResult(true);
    } catch (err) {
      setError(`Connection test failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'default';
      case 'maintenance': return 'warning';
      default: return 'default';
    }
  };

  const getHealthColor = (healthStatus) => {
    switch (healthStatus) {
      case 'healthy': return 'success';
      case 'warning': return 'warning';
      case 'critical': return 'error';
      default: return 'default';
    }
  };

  const getHealthIcon = (healthStatus) => {
    switch (healthStatus) {
      case 'healthy': return <CheckCircleIcon sx={{ color: 'success.main' }} />;
      case 'warning': return <WarningIcon sx={{ color: 'warning.main' }} />;
      case 'critical': return <ErrorIcon sx={{ color: 'error.main' }} />;
      default: return <InfoIcon sx={{ color: 'text.secondary' }} />;
    }
  };

  const getOSIcon = (osType) => {
    switch (osType?.toLowerCase()) {
      case 'windows': return '🪟';
      case 'linux': return '🐧';
      case 'macos': return '🍎';
      default: return '💻';
    }
  };

  if (!target) {
    return null;
  }

  // Use fullTarget if available, otherwise fall back to target
  const displayTarget = fullTarget || target;
  
  // Extract IP address from communication methods
  const getTargetIpAddress = (target) => {
    if (!target.communication_methods || target.communication_methods.length === 0) {
      return null;
    }
    
    // Look for primary communication method first
    const primaryMethod = target.communication_methods.find(method => method.is_primary && method.is_active);
    if (primaryMethod && primaryMethod.config && primaryMethod.config.host) {
      return primaryMethod.config.host;
    }
    
    // If no primary method, get first active method
    const activeMethod = target.communication_methods.find(method => method.is_active);
    if (activeMethod && activeMethod.config && activeMethod.config.host) {
      return activeMethod.config.host;
    }
    
    return null;
  };
  
  const ipAddress = getTargetIpAddress(displayTarget);

  return (
    <Dialog 
      open={open} 
      onClose={handleClose} 
      maxWidth="md" 
      fullWidth
      PaperProps={{ sx: { borderRadius: 1 } }}
    >
      {/* Compact Header */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        p: 2,
        borderBottom: 1,
        borderColor: 'divider'
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="h6" fontWeight={500}>
            {displayTarget.name}
          </Typography>
          <Chip label={displayTarget.os_type} size="small" variant="outlined" />
          <Chip 
            label={displayTarget.status} 
            size="small"
            color={getStatusColor(displayTarget.status)}
          />
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            startIcon={<EditIcon />}
            onClick={onEditTarget}
            disabled={loading}
            variant="outlined"
            size="small"
          >
            Edit
          </Button>
          <Button
            startIcon={<DeleteIcon />}
            onClick={handleDelete}
            disabled={loading}
            color="error"
            variant="outlined"
            size="small"
          >
            Delete
          </Button>
          <IconButton onClick={handleClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </Box>
      
      <DialogContent sx={{ p: 2 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        {loadingTarget && (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
            <CircularProgress />
          </Box>
        )}

        {!loadingTarget && (
          <Grid container spacing={2}>
            {/* Basic Info */}
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" gutterBottom>System Info</Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">Type</Typography>
                  <Typography variant="body2">{displayTarget.target_type || 'Server'}</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">Environment</Typography>
                  <Typography variant="body2">{displayTarget.environment}</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">IP Address</Typography>
                  <Typography variant="body2" fontFamily="monospace">{ipAddress || 'N/A'}</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">Created</Typography>
                  <Typography variant="body2">{new Date(displayTarget.created_at).toLocaleDateString()}</Typography>
                </Box>
              </Box>
            </Grid>

            {/* Location Info */}
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" gutterBottom>Location</Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">Location</Typography>
                  <Typography variant="body2">{displayTarget.location || 'Not specified'}</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">Data Center</Typography>
                  <Typography variant="body2">{displayTarget.data_center || 'Not specified'}</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">Region</Typography>
                  <Typography variant="body2">{displayTarget.region || 'Not specified'}</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">Health</Typography>
                  <Chip 
                    label={displayTarget.health_status} 
                    size="small"
                    color={getHealthColor(displayTarget.health_status)}
                  />
                </Box>
              </Box>
            </Grid>

            {/* Description */}
            {displayTarget.description && (
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>Description</Typography>
                <Typography variant="body2" color="text.secondary">
                  {displayTarget.description}
                </Typography>
              </Grid>
            )}

            {/* Communication Methods - Compact with individual test buttons */}
            {displayTarget.communication_methods && displayTarget.communication_methods.length > 0 && (
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="subtitle2">Communication Methods</Typography>
                  <Button
                    startIcon={<SettingsIcon />}
                    onClick={() => setShowMethodsManager(true)}
                    variant="outlined"
                    size="small"
                  >
                    Manage Methods
                  </Button>
                </Box>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {displayTarget.communication_methods.map((method) => (
                    <Paper 
                      key={method.id} 
                      variant="outlined"
                      sx={{ 
                        p: 1.5,
                        border: method.is_primary ? '2px solid' : '1px solid',
                        borderColor: method.is_primary ? 'primary.main' : 'divider'
                      }}
                    >
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2" fontWeight={500}>
                            {method.method_type.toUpperCase()}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" fontFamily="monospace">
                            {method.config?.host}:{method.config?.port}
                          </Typography>
                          {method.is_primary && (
                            <Chip label="Primary" size="small" color="primary" />
                          )}
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2" color="text.secondary">
                            {method.credentials ? method.credentials.length : 0} creds
                          </Typography>
                          <Chip 
                            label={method.is_active ? 'Active' : 'Inactive'} 
                            size="small"
                            color={method.is_active ? 'success' : 'default'}
                          />
                          <Button
                            startIcon={<NetworkCheckIcon />}
                            onClick={() => handleTestConnection(method.id)}
                            disabled={loading || !method.is_active}
                            variant="outlined"
                            size="small"
                            sx={{ minWidth: 'auto', px: 1 }}
                          >
                            Test
                          </Button>
                        </Box>
                      </Box>
                    </Paper>
                  ))}
                </Box>
              </Grid>
            )}
          </Grid>
        )}
      </DialogContent>

      {/* Communication Methods Manager */}
      <CommunicationMethodsManager
        open={showMethodsManager}
        target={displayTarget}
        onClose={() => setShowMethodsManager(false)}
        onMethodsUpdated={async () => {
          // Reload target data when methods are updated
          console.log('onMethodsUpdated called - reloading target data');
          try {
            setLoadingTarget(true);
            const targetDetails = await getTargetById(target.id);
            console.log('Reloaded target details:', targetDetails);
            setFullTarget(targetDetails);
            setShowMethodsManager(false);
          } catch (err) {
            console.error('Failed to reload target details:', err);
            setError(`Failed to reload target details: ${err.message}`);
          } finally {
            setLoadingTarget(false);
          }
        }}
      />

      {/* Test Result Dialog - Simple & Compact */}
      <Dialog
        open={showTestResult}
        onClose={() => setShowTestResult(false)}
        maxWidth="sm"
      >
        <DialogTitle sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 1,
          bgcolor: testResult?.success ? 'success.main' : 'error.main',
          color: 'white',
          py: 2
        }}>
          {testResult?.success ? (
            <CheckCircleIcon />
          ) : (
            <ErrorIcon />
          )}
          {testResult?.success ? 'Test Successful' : 'Test Failed'}
        </DialogTitle>
        
        <DialogContent sx={{ pt: 2, pb: 1 }}>
          {testResult && (
            <Box>
              {/* Simple message */}
              <Typography variant="body1" sx={{ mb: 2 }}>
                {testResult.message}
              </Typography>
              
              {/* Basic info in compact format */}
              <Typography variant="body2" color="text.secondary" fontFamily="monospace">
                {testResult.method_type?.toUpperCase()} → {testResult.host}:{testResult.port} ({testResult.test_duration || 0}ms)
              </Typography>
            </Box>
          )}
        </DialogContent>
        
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button 
            onClick={() => setShowTestResult(false)}
            variant="contained"
            size="small"
          >
            OK
          </Button>
        </DialogActions>
      </Dialog>
    </Dialog>
  );
};

export default UniversalTargetDetailModal;