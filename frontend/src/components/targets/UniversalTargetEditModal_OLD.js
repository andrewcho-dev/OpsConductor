/**
 * Universal Target Edit Modal
 * Compact single-form target editing.
 */
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Alert,
  CircularProgress,
  Typography,
  Box,
  Paper,
  Chip,
  FormControlLabel,
  RadioGroup,
  Radio,
  IconButton,
  Stack,
  Divider
} from '@mui/material';
import {
  Computer as ComputerIcon,
  Save as SaveIcon,
  Add as AddIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';

import { 
  updateTarget,
  updateTargetComprehensive,
  getTargetById,
  getEnvironmentOptions,
  getStatusOptions,
  getOSTypeOptions,
  getCommunicationMethodOptions
} from '../../services/targetService';

const UniversalTargetEditModal = ({ open, target, onClose, onTargetUpdated }) => {
  const [loading, setLoading] = useState(false);
  const [loadingTarget, setLoadingTarget] = useState(false);
  const [error, setError] = useState('');
  const [validationErrors, setValidationErrors] = useState({});
  
  // Communication methods state
  const [communicationMethods, setCommunicationMethods] = useState([]);
  const [nextMethodId, setNextMethodId] = useState(1);

  
  // Form data state - all editable fields
  const [formData, setFormData] = useState({
    // Basic information
    name: '',
    description: '',
    environment: 'development',
    location: '',
    data_center: '',
    region: '',
    status: 'active',
    os_type: 'linux',
    
    // Connection details
    ip_address: '',
    method_type: 'ssh',
    
    // Credentials
    username: '',
    password: '',
    ssh_key: '',
    ssh_passphrase: ''
  });

  // Load full target data when modal opens
  useEffect(() => {
    const loadFullTarget = async () => {
      if (open && target?.id) {
        try {
          setLoadingTarget(true);
          setError('');
          
          // Get full target details
          const fullTarget = await getTargetById(target.id);
          
          // Set basic form data
          setFormData({
            // Basic information
            name: fullTarget.name || '',
            description: fullTarget.description || '',
            environment: fullTarget.environment || 'development',
            location: fullTarget.location || '',
            data_center: fullTarget.data_center || '',
            region: fullTarget.region || '',
            status: fullTarget.status || 'active',
            os_type: fullTarget.os_type || 'linux',
            ip_address: fullTarget.ip_address || ''
          });
          
          // Load communication methods
          if (fullTarget.communication_methods && fullTarget.communication_methods.length > 0) {
            const methods = fullTarget.communication_methods.map((method, index) => {
              const primaryCredential = method.credentials?.find(c => c.is_primary && c.is_active) ||
                                       method.credentials?.find(c => c.is_active);
              
              return {
                id: method.id || index + 1,
                method_type: method.method_type || 'ssh',
                host: method.config?.host || '',
                port: method.config?.port || (method.method_type === 'ssh' ? 22 : 5985),
                username: '', // Don't show existing username for security
                credential_type: primaryCredential?.credential_type || 'password',
                password: '', // Don't show existing password
                ssh_key: '', // Don't show existing SSH key
                is_primary: method.is_primary || false,
                existing_method: true // Flag to indicate this is an existing method
              };
            });
            setCommunicationMethods(methods);
            setNextMethodId(Math.max(...methods.map(m => m.id)) + 1);
          } else {
            // Create default method if none exist
            setCommunicationMethods([{
              id: 1,
              method_type: 'ssh',
              host: fullTarget.ip_address || '',
              port: 22,
              username: '',
              credential_type: 'password',
              password: '',
              ssh_key: '',
              is_primary: true,
              existing_method: false
            }]);
            setNextMethodId(2);
          }
          
          setValidationErrors({});
        } catch (err) {
          setError(`Failed to load target details: ${err.message}`);
        } finally {
          setLoadingTarget(false);
        }
      }
    };

    loadFullTarget();
  }, [open, target?.id]);

  // Reset when modal closes
  useEffect(() => {
    if (!open) {
      setError('');
      setValidationErrors({});
    }
  }, [open]);

  const handleInputChange = (field, value) => {
    setFormData(prev => {
      const newData = {
        ...prev,
        [field]: value
      };
      
      // If OS type changes, reset method_type to appropriate default
      if (field === 'os_type') {
        const availableMethods = getCommunicationMethodOptions(value);
        if (availableMethods.length > 0 && !availableMethods.find(m => m.value === prev.method_type)) {
          newData.method_type = availableMethods[0].value;
        }
      }
      
      return newData;
    });
    
    // Clear validation error for this field
    if (validationErrors[field]) {
      setValidationErrors(prev => ({
        ...prev,
        [field]: undefined
      }));
    }
  };

  // Communication Methods Helper Functions
  const addCommunicationMethod = () => {
    const newMethod = {
      id: nextMethodId,
      method_type: 'ssh',
      host: formData.ip_address,
      port: 22,
      username: '',
      credential_type: 'password',
      password: '',
      ssh_key: '',
      is_primary: false,
      existing_method: false
    };
    setCommunicationMethods(prev => [...prev, newMethod]);
    setNextMethodId(prev => prev + 1);
  };

  const removeCommunicationMethod = (methodId) => {
    setCommunicationMethods(prev => {
      const filtered = prev.filter(m => m.id !== methodId);
      // If we removed the primary method, make the first one primary
      if (filtered.length > 0 && !filtered.some(m => m.is_primary)) {
        filtered[0].is_primary = true;
      }
      return filtered;
    });
  };

  const updateCommunicationMethod = (methodId, field, value) => {
    setCommunicationMethods(prev => prev.map(method => 
      method.id === methodId 
        ? { 
            ...method, 
            [field]: value,
            // Auto-update port based on method type
            ...(field === 'method_type' && {
              port: value === 'ssh' ? 22 : value === 'winrm' ? 5985 : method.port
            })
          }
        : method
    ));
  };

  const setPrimaryMethod = (methodId) => {
    setCommunicationMethods(prev => prev.map(method => ({
      ...method,
      is_primary: method.id === methodId
    })));
  };

  const validateForm = () => {
    const errors = {};
    
    // Basic required fields
    if (!formData.name.trim()) errors.name = 'Target name is required';
    if (!formData.ip_address.trim()) {
      errors.ip_address = 'IP address is required';
    } else if (!/^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/.test(formData.ip_address)) {
      errors.ip_address = 'Invalid IP address format';
    }
    
    // Validate communication methods
    if (communicationMethods.length === 0) {
      errors.methods = 'At least one communication method is required';
    } else {
      communicationMethods.forEach((method, index) => {
        // Only validate credentials if they're being updated (not empty)
        if (method.username.trim() || method.password.trim() || method.ssh_key.trim()) {
          if (!method.username.trim()) {
            errors[`method_${method.id}_username`] = `Username required for method ${index + 1}`;
          }
          if (method.credential_type === 'password' && method.username.trim() && !method.password.trim()) {
            errors[`method_${method.id}_password`] = `Password required for method ${index + 1}`;
          }
          if (method.credential_type === 'ssh_key' && method.username.trim() && !method.ssh_key.trim()) {
            errors[`method_${method.id}_ssh_key`] = `SSH key required for method ${index + 1}`;
          }
        }
      });
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) {
      setError('Please fix the validation errors before saving');
      return;
    }

    try {
      setLoading(true);
      setError('');
      
      // Prepare comprehensive update data with communication methods
      const updateData = {
        // Basic information
        name: formData.name,
        description: formData.description,
        os_type: formData.os_type,
        environment: formData.environment,
        location: formData.location,
        data_center: formData.data_center,
        region: formData.region,
        status: formData.status,
        ip_address: formData.ip_address,
        
        // Communication methods
        communication_methods: communicationMethods.map(method => ({
          ...(method.existing_method && { id: method.id }), // Include ID for existing methods
          method_type: method.method_type,
          config: {
            host: method.host || formData.ip_address,
            port: method.port
          },
          // Only include credentials if they're being updated
          ...(method.username.trim() && {
            credentials: [{
              credential_type: method.credential_type,
              encrypted_credentials: method.credential_type === 'password' 
                ? { username: method.username, password: method.password }
                : { username: method.username, ssh_key: method.ssh_key },
              is_primary: true,
              is_active: true
            }]
          }),
          is_primary: method.is_primary,
          is_active: true
        }))
      };
      
      await updateTargetComprehensive(target.id, updateData);
      onTargetUpdated();
      onClose();
    } catch (err) {
      setError(`Failed to update target: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (!target) return null;

  if (loadingTarget) {
    return (
      <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
        <DialogContent sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
          <CircularProgress />
          <Typography sx={{ ml: 2 }}>Loading target details...</Typography>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ComputerIcon />
          <Typography variant="h6">Edit Target - Full CRUD</Typography>
          <Chip 
            label={formData.os_type?.toUpperCase()} 
            size="small" 
            variant="outlined" 
          />
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          {/* Basic Information */}
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle1" gutterBottom>Basic Information</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={8}>
                <TextField
                  fullWidth
                  label="Target Name"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  error={!!validationErrors.name}
                  helperText={validationErrors.name}
                  required
                  size="small"
                />
              </Grid>
              
              <Grid item xs={12} md={4}>
                <FormControl fullWidth size="small">
                  <InputLabel>OS Type</InputLabel>
                  <Select
                    value={formData.os_type}
                    label="OS Type"
                    onChange={(e) => handleInputChange('os_type', e.target.value)}
                  >
                    {getOSTypeOptions().map(option => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Environment</InputLabel>
                  <Select
                    value={formData.environment}
                    label="Environment"
                    onChange={(e) => handleInputChange('environment', e.target.value)}
                  >
                    {getEnvironmentOptions().map(option => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Status</InputLabel>
                  <Select
                    value={formData.status}
                    label="Status"
                    onChange={(e) => handleInputChange('status', e.target.value)}
                  >
                    {getStatusOptions().map(option => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Description"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  multiline
                  rows={2}
                  size="small"
                />
              </Grid>
              
              <Grid item xs={4}>
                <TextField
                  fullWidth
                  label="Location"
                  value={formData.location}
                  onChange={(e) => handleInputChange('location', e.target.value)}
                  size="small"
                />
              </Grid>
              
              <Grid item xs={4}>
                <TextField
                  fullWidth
                  label="Data Center"
                  value={formData.data_center}
                  onChange={(e) => handleInputChange('data_center', e.target.value)}
                  size="small"
                />
              </Grid>
              
              <Grid item xs={4}>
                <TextField
                  fullWidth
                  label="Region"
                  value={formData.region}
                  onChange={(e) => handleInputChange('region', e.target.value)}
                  size="small"
                />
              </Grid>
            </Grid>
          </Paper>

          {/* Connection Details */}
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle1" gutterBottom>Connection Details</Typography>
            <Grid container spacing={2}>
              <Grid item xs={8}>
                <TextField
                  fullWidth
                  label="IP Address"
                  value={formData.ip_address}
                  onChange={(e) => handleInputChange('ip_address', e.target.value)}
                  error={!!validationErrors.ip_address}
                  helperText={validationErrors.ip_address}
                  required
                  size="small"
                />
              </Grid>
              
              <Grid item xs={4}>
                <FormControl fullWidth error={!!validationErrors.method_type} size="small">
                  <InputLabel>Method *</InputLabel>
                  <Select
                    value={formData.method_type}
                    label="Method *"
                    onChange={(e) => handleInputChange('method_type', e.target.value)}
                  >
                    {getCommunicationMethodOptions(formData.os_type).map(option => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Paper>

          {/* Credentials */}
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle1" gutterBottom>Credentials (Optional Update)</Typography>
            <Alert severity="info" sx={{ mb: 2 }}>
              Leave fields empty to keep existing credentials. Only enter new values if you want to update them.
            </Alert>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Username (optional)"
                  value={formData.username}
                  onChange={(e) => handleInputChange('username', e.target.value)}
                  error={!!validationErrors.username}
                  helperText={validationErrors.username || 'Leave empty to keep current username'}
                  size="small"
                />
              </Grid>
              
              <Grid item xs={12}>
                <FormControl component="fieldset">
                  <RadioGroup
                    row
                    value="password"
                    onChange={() => {}}
                  >
                    <FormControlLabel value="password" control={<Radio size="small" />} label="Password" />
                    <FormControlLabel value="ssh_key" control={<Radio size="small" />} label="SSH Key" />
                  </RadioGroup>
                </FormControl>
              </Grid>
              
              <Grid item xs={12}>
                {true ? (
                  <TextField
                    fullWidth
                    label="Password (optional)"
                    type="password"
                    value={formData.password}
                    onChange={(e) => handleInputChange('password', e.target.value)}
                    error={!!validationErrors.password}
                    helperText={validationErrors.password || 'Leave empty to keep current password'}
                    size="small"
                  />
                ) : (
                  <>
                    <TextField
                      fullWidth
                      label="SSH Private Key (optional)"
                      multiline
                      rows={3}
                      value={formData.ssh_key}
                      onChange={(e) => handleInputChange('ssh_key', e.target.value)}
                      error={!!validationErrors.ssh_key}
                      helperText={validationErrors.ssh_key || 'Leave empty to keep current SSH key'}
                      size="small"
                      sx={{ mb: 2 }}
                    />
                    <TextField
                      fullWidth
                      label="SSH Key Passphrase (optional)"
                      type="password"
                      value={formData.ssh_passphrase}
                      onChange={(e) => handleInputChange('ssh_passphrase', e.target.value)}
                      helperText="Leave empty if key has no passphrase"
                      size="small"
                    />
                  </>
                )}
              </Grid>
            </Grid>
          </Paper>
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 2, justifyContent: 'space-between' }}>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        
        <Button 
          onClick={handleSave} 
          variant="contained" 
          disabled={loading}
          startIcon={loading ? <CircularProgress size={16} /> : <SaveIcon />}
        >
          {loading ? 'Saving...' : 'Save All Changes'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default UniversalTargetEditModal;
