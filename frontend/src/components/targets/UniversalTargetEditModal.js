/**
 * Universal Target Edit Modal - COMPLETELY REWRITTEN
 * Clean, compact design matching Create Target modal
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
  IconButton,
  Stack,
  Divider
} from '@mui/material';
import {
  Computer as ComputerIcon,
  Save as SaveIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  PlayArrow as TestIcon
} from '@mui/icons-material';

import { 
  updateTargetComprehensive,
  getTargetById,
  getEnvironmentOptions,
  getStatusOptions,
  getOSTypeOptions,
  getCommunicationMethodOptions,
  testMethodConfiguration,
  testCommunicationMethod
} from '../../services/targetService';

const UniversalTargetEditModal = ({ open, target, onClose, onTargetUpdated }) => {
  const [loading, setLoading] = useState(false);
  const [loadingTarget, setLoadingTarget] = useState(false);
  const [error, setError] = useState('');
  const [validationErrors, setValidationErrors] = useState({});
  
  // Communication methods state
  const [communicationMethods, setCommunicationMethods] = useState([]);
  const [nextMethodId, setNextMethodId] = useState(1);
  const [testingMethods, setTestingMethods] = useState(new Set());
  const [testResults, setTestResults] = useState({});
  
  // Form data state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    environment: 'development',
    location: '',
    data_center: '',
    status: 'active',
    os_type: 'linux',
    ip_address: ''
  });

  // Load full target data when modal opens
  useEffect(() => {
    const loadFullTarget = async () => {
      if (open && target?.id) {
        try {
          setLoadingTarget(true);
          setError('');
          
          console.log('Loading target:', target.id);
          const fullTarget = await getTargetById(target.id);
          console.log('Full target loaded:', fullTarget);
          
          // Extract IP address from primary communication method
          let ipAddress = '';
          if (fullTarget.communication_methods && fullTarget.communication_methods.length > 0) {
            const primaryMethod = fullTarget.communication_methods.find(m => m.is_primary) || 
                                 fullTarget.communication_methods[0];
            if (primaryMethod && primaryMethod.config && primaryMethod.config.host) {
              ipAddress = primaryMethod.config.host;
            }
          }
          
          // Set basic form data - ensure ALL fields are properly loaded
          setFormData({
            name: fullTarget.name || '',
            description: fullTarget.description || '',
            environment: fullTarget.environment || 'development',
            location: fullTarget.location || '',
            data_center: fullTarget.data_center || '',
            region: fullTarget.region || '',
            status: fullTarget.status || 'active',
            os_type: fullTarget.os_type || 'linux',
            ip_address: ipAddress
          });
          
          // Load communication methods
          console.log('Communication methods:', fullTarget.communication_methods);
          if (fullTarget.communication_methods && fullTarget.communication_methods.length > 0) {
            const methods = fullTarget.communication_methods.map((method, index) => {
              const primaryCredential = method.credentials?.find(c => c.is_primary && c.is_active) ||
                                       method.credentials?.find(c => c.is_active);
              
              console.log(`Processing method ${index + 1}:`, {
                id: method.id,
                method_type: method.method_type,
                config: method.config,
                is_primary: method.is_primary,
                credential: primaryCredential
              });
              
              const processedMethod = {
                id: method.id || (1000 + index), // Use high IDs for existing methods
                method_type: method.method_type || 'ssh',
                host: ipAddress, // ALL methods use the target's IP address
                port: method.config?.port || (method.method_type === 'ssh' ? 22 : 5985),
                username: primaryCredential?.encrypted_credentials?.username || '',
                credential_type: primaryCredential?.credential_type || 'password',
                password: '', // Don't show existing password
                ssh_key: '', // Don't show existing SSH key
                is_primary: method.is_primary || false,
                existing_method: true
              };
              
              console.log(`Processed method ${index + 1}:`, processedMethod);
              return processedMethod;
            });
            
            console.log('Processed methods:', methods);
            setCommunicationMethods(methods);
            setNextMethodId(2000); // Start new methods at 2000
          } else {
            // Create default method if none exist
            console.log('No existing methods, creating default');
            setCommunicationMethods([{
              id: 1,
              method_type: 'ssh',
              host: ipAddress || '',
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
          console.error('Error loading target:', err);
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
      setCommunicationMethods([]);
      setFormData({
        name: '',
        description: '',
        environment: 'development',
        location: '',
        data_center: '',
        status: 'active',
        os_type: 'linux',
        ip_address: ''
      });
    }
  }, [open]);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
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

  const testMethodConnection = async (methodId) => {
    const method = communicationMethods.find(m => m.id === methodId);
    if (!method) return;

    try {
      setTestingMethods(prev => new Set([...prev, methodId]));
      setError('');
      
      let result;
      
      // For existing methods, test using the saved method if no credentials are provided
      if (method.existing_method && (!method.username || (!method.password && !method.ssh_key))) {
        console.log('Testing existing method:', methodId);
        result = await testCommunicationMethod(target.id, methodId);
      } else {
        // For new methods or when updating credentials, test the configuration
        if (!formData.ip_address) {
          setError('IP address is required to test connection');
          return;
        }

        // SNMP v1 and v2c validation
        if (method.method_type === 'snmp') {
          if (method.version === '3') {
            // SNMPv3 requires username
            if (!method.username) {
              setError('Username is required to test SNMPv3 connection');
              return;
            }
            if (method.credential_type === 'password' && !method.password) {
              setError('Password is required to test SNMPv3 connection');
              return;
            }
          } else {
            // SNMPv1 and v2c require community string
            if (!method.community) {
              setError('Community string is required to test SNMP connection');
              return;
            }
          }
        } else {
          // All other methods require username
          if (!method.username) {
            setError('Username is required to test connection');
            return;
          }
          if (method.credential_type === 'password' && !method.password) {
            setError('Password is required to test connection');
            return;
          }
          if (method.credential_type === 'ssh_key' && !method.ssh_key) {
            setError('SSH key is required to test connection');
            return;
          }
        }

        console.log('Testing method configuration:', method);
        
        const testConfig = {
          method_type: method.method_type,
          host: formData.ip_address, // Use target's IP address
          port: method.port,
          username: method.username,
          credential_type: method.credential_type,
          password: method.password,
          ssh_key: method.ssh_key
        };

        // Add SNMP-specific parameters
        if (method.method_type === 'snmp') {
          testConfig.version = method.version;
          testConfig.community = method.community;
          testConfig.retries = method.retries;
          if (method.version === '3') {
            testConfig.security_level = method.security_level;
            testConfig.auth_protocol = method.auth_protocol;
            testConfig.privacy_protocol = method.privacy_protocol;
          }
        }

        result = await testMethodConfiguration(testConfig);
      }

      setTestResults(prev => ({
        ...prev,
        [methodId]: {
          success: true,
          message: result.message || 'Connection successful!',
          timestamp: new Date().toLocaleTimeString()
        }
      }));

    } catch (err) {
      setTestResults(prev => ({
        ...prev,
        [methodId]: {
          success: false,
          message: err.message || 'Connection failed',
          timestamp: new Date().toLocaleTimeString()
        }
      }));
    } finally {
      setTestingMethods(prev => {
        const newSet = new Set(prev);
        newSet.delete(methodId);
        return newSet;
      });
    }
  };

  const validateForm = () => {
    const errors = {};
    
    // Basic required fields
    if (!formData.name.trim()) errors.name = 'Target name is required';
    if (!formData.ip_address.trim()) {
      errors.ip_address = 'IP address or DNS name is required';
    } else {
      const ipAddress = formData.ip_address.trim();
      
      // Check if it's a valid IPv4 address
      const isValidIP = () => {
        const ipv4Regex = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/;
        if (!ipv4Regex.test(ipAddress)) return false;
        
        // Check each octet is 0-255
        const octets = ipAddress.split('.');
        return octets.every(octet => {
          const num = parseInt(octet, 10);
          return num >= 0 && num <= 255;
        });
      };
      
      // Check if it's a valid DNS name
      const isValidDNS = () => {
        // Don't allow pure numeric domains (like 300.300.300.300)
        if (/^[0-9.]+$/.test(ipAddress)) return false;
        
        const dnsRegex = /^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$/;
        return dnsRegex.test(ipAddress) && ipAddress.length <= 253;
      };
      
      if (!isValidIP() && !isValidDNS()) {
        errors.ip_address = 'Invalid IP address or DNS name format';
      }
    }
    
    // Validate communication methods
    if (communicationMethods.length === 0) {
      errors.methods = 'At least one communication method is required';
    } else {
      communicationMethods.forEach((method, index) => {
        // For new methods, require credentials based on method type
        if (!method.existing_method) {
          // SNMP v1 and v2c don't require username/password, only community string
          if (method.method_type === 'snmp') {
            if (method.version === '3') {
              // SNMPv3 requires username
              if (!method.username.trim()) {
                errors[`method_${method.id}_username`] = `Username required for SNMPv3 method ${index + 1}`;
              }
              if (method.credential_type === 'password' && !method.password.trim()) {
                errors[`method_${method.id}_password`] = `Password required for SNMPv3 method ${index + 1}`;
              }
            } else {
              // SNMPv1 and v2c require community string
              if (!method.community || !method.community.trim()) {
                errors[`method_${method.id}_community`] = `Community string required for SNMP v${method.version} method ${index + 1}`;
              }
            }
          } else {
            // All other methods require username
            if (!method.username.trim()) {
              errors[`method_${method.id}_username`] = `Username required for new method ${index + 1}`;
            }
            if (method.credential_type === 'password' && !method.password.trim()) {
              errors[`method_${method.id}_password`] = `Password required for new method ${index + 1}`;
            }
            if (method.credential_type === 'ssh_key' && !method.ssh_key.trim()) {
              errors[`method_${method.id}_ssh_key`] = `SSH key required for new method ${index + 1}`;
            }
          }
        }
        // For existing methods, only validate if credentials are being updated
        else if (method.username.trim() || method.password.trim() || method.ssh_key.trim()) {
          // Skip validation for SNMP v1/v2c methods as they don't use username/password
          if (method.method_type !== 'snmp' || method.version === '3') {
            if (method.username.trim() && method.credential_type === 'password' && !method.password.trim()) {
              errors[`method_${method.id}_password`] = `Password required when updating credentials for method ${index + 1}`;
            }
            if (method.username.trim() && method.credential_type === 'ssh_key' && !method.ssh_key.trim()) {
              errors[`method_${method.id}_ssh_key`] = `SSH key required when updating credentials for method ${index + 1}`;
            }
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
      
      console.log('Saving target with methods:', communicationMethods);
      
      // Prepare comprehensive update data with communication methods
      const updateData = {
        // Basic information
        name: formData.name,
        description: formData.description,
        os_type: formData.os_type,
        environment: formData.environment,
        location: formData.location,
        data_center: formData.data_center,
        status: formData.status,
        ip_address: formData.ip_address,
        
        // Communication methods
        communication_methods: communicationMethods.map(method => ({
          ...(method.existing_method && method.id >= 1000 && { id: method.id }), // Include ID for existing methods
          method_type: method.method_type,
          config: {
            host: formData.ip_address, // ALL methods use the target's IP address
            port: method.port
          },
          // Only include credentials if they're being updated (not empty)
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
      
      console.log('Update data:', updateData);
      
      await updateTargetComprehensive(target.id, updateData);
      onTargetUpdated();
      onClose();
      
    } catch (err) {
      console.error('Error updating target:', err);
      setError(`Failed to update target: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (!target) return null;

  if (loadingTarget) {
    return (
      <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
        <DialogContent sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
          <CircularProgress />
          <Typography sx={{ ml: 2 }}>Loading target details...</Typography>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ComputerIcon />
          <Typography variant="h6">Edit Target</Typography>
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

        {/* Compact Single-Screen Edit Form */}
        <Grid container spacing={2} sx={{ mt: 0.5 }}>
          {/* Basic Info - Top Row */}
          <Grid item xs={8}>
            <TextField
              fullWidth
              label="Target Name *"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              error={!!validationErrors.name}
              helperText={validationErrors.name}
              size="small"
            />
          </Grid>
          
          <Grid item xs={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Device/OS Type *</InputLabel>
              <Select
                value={formData.os_type}
                label="Device/OS Type *"
                onChange={(e) => handleInputChange('os_type', e.target.value)}
              >
                {(() => {
                  const options = getOSTypeOptions();
                  const categories = [...new Set(options.map(opt => opt.category))];
                  
                  return categories.map(category => [
                    <MenuItem key={`header-${category}`} disabled sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                      {category}
                    </MenuItem>,
                    ...options
                      .filter(opt => opt.category === category)
                      .map(option => (
                        <MenuItem key={option.value} value={option.value} sx={{ pl: 3 }}>
                          {option.label}
                        </MenuItem>
                      ))
                  ]).flat();
                })()}
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
          
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="IP Address / DNS Name *"
              placeholder="192.168.1.100 or smtp.gmail.com"
              value={formData.ip_address}
              onChange={(e) => {
                handleInputChange('ip_address', e.target.value);
                // Auto-update host in ALL communication methods (they all use the same target IP)
                setCommunicationMethods(prev => prev.map(method => ({
                  ...method,
                  host: e.target.value
                })));
              }}
              error={!!validationErrors.ip_address}
              helperText={validationErrors.ip_address}
              size="small"
            />
          </Grid>

          <Grid item xs={4}>
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
          
          <Grid item xs={4}>
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

          {/* Communication Methods Section */}
          <Grid item xs={12}>
            <Divider sx={{ my: 1 }} />
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="subtitle2" color="primary">
                Communication Methods ({communicationMethods.length})
              </Typography>
              <Button
                size="small"
                startIcon={<AddIcon />}
                onClick={addCommunicationMethod}
                variant="outlined"
              >
                Add Method
              </Button>
            </Box>
          </Grid>

          {/* Communication Methods List */}
          {communicationMethods.map((method, index) => (
            <Grid item xs={12} key={method.id}>
              <Paper sx={{ p: 2, bgcolor: method.is_primary ? 'primary.50' : 'grey.50' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Typography variant="body2" fontWeight="medium">
                      Method {index + 1}
                    </Typography>
                    {method.is_primary && (
                      <Chip label="Primary" size="small" color="primary" />
                    )}
                    {method.existing_method && (
                      <Chip label="Existing" size="small" variant="outlined" />
                    )}
                  </Stack>
                  <Box>
                    {!method.is_primary && (
                      <Button
                        size="small"
                        onClick={() => setPrimaryMethod(method.id)}
                        variant="text"
                        sx={{ mr: 1 }}
                      >
                        Set Primary
                      </Button>
                    )}
                    <Button
                      size="small"
                      startIcon={testingMethods.has(method.id) ? <CircularProgress size={12} /> : <TestIcon />}
                      onClick={() => testMethodConnection(method.id)}
                      variant="outlined"
                      disabled={testingMethods.has(method.id)}
                      sx={{ mr: 1 }}
                    >
                      {testingMethods.has(method.id) ? 'Testing...' : 'Test'}
                    </Button>
                    {communicationMethods.length > 1 && (
                      <IconButton
                        size="small"
                        onClick={() => removeCommunicationMethod(method.id)}
                        color="error"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    )}
                  </Box>
                </Box>

                <Grid container spacing={1}>
                  <Grid item xs={6}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Type</InputLabel>
                      <Select
                        value={method.method_type}
                        label="Type"
                        onChange={(e) => updateCommunicationMethod(method.id, 'method_type', e.target.value)}
                      >
                        {getCommunicationMethodOptions(formData.os_type).map(option => (
                          <MenuItem key={option.value} value={option.value}>
                            {option.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Port"
                      type="number"
                      value={method.port}
                      onChange={(e) => updateCommunicationMethod(method.id, 'port', parseInt(e.target.value))}
                      size="small"
                    />
                  </Grid>
                  
                  {/* Row 2: Authentication Details - Hide for SNMP v1/v2c */}
                  {(method.method_type !== 'snmp' || method.version === '3') && (
                    <>
                      <Grid item xs={4}>
                        <FormControl fullWidth size="small">
                          <InputLabel>Auth Method</InputLabel>
                          <Select
                            value={method.credential_type}
                            label="Auth Method"
                            onChange={(e) => updateCommunicationMethod(method.id, 'credential_type', e.target.value)}
                          >
                            <MenuItem value="password">Password</MenuItem>
                            <MenuItem value="ssh_key">SSH Key</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>
                      
                      <Grid item xs={4}>
                        <TextField
                          fullWidth
                          label="Username"
                          value={method.username}
                          onChange={(e) => updateCommunicationMethod(method.id, 'username', e.target.value)}
                          size="small"
                          placeholder={method.existing_method ? 'Leave empty to keep current' : 'Required'}
                          error={!!validationErrors[`method_${method.id}_username`]}
                          helperText={validationErrors[`method_${method.id}_username`]}
                        />
                      </Grid>
                      
                      <Grid item xs={4}>
                        {method.credential_type === 'password' ? (
                          <TextField
                            fullWidth
                            label="Password"
                            type="password"
                            value={method.password}
                            onChange={(e) => updateCommunicationMethod(method.id, 'password', e.target.value)}
                            size="small"
                            placeholder={method.existing_method ? 'Leave empty to keep current' : 'Required'}
                            error={!!validationErrors[`method_${method.id}_password`]}
                            helperText={validationErrors[`method_${method.id}_password`]}
                          />
                        ) : (
                          <TextField
                            fullWidth
                            label="SSH Key"
                            multiline
                            rows={2}
                            value={method.ssh_key}
                            onChange={(e) => updateCommunicationMethod(method.id, 'ssh_key', e.target.value)}
                            size="small"
                            placeholder={method.existing_method ? 'Leave empty to keep current' : 'Required'}
                            error={!!validationErrors[`method_${method.id}_ssh_key`]}
                            helperText={validationErrors[`method_${method.id}_ssh_key`]}
                          />
                        )}
                      </Grid>
                    </>
                  )}
                </Grid>
                
                {/* Test Result Display */}
                {testResults[method.id] && (
                  <Alert 
                    severity={testResults[method.id].success ? 'success' : 'error'} 
                    sx={{ mt: 1 }}
                  >
                    <Typography variant="body2">
                      <strong>{testResults[method.id].success ? 'Connection Successful!' : 'Connection Failed'}</strong>
                      <br />
                      {testResults[method.id].message}
                      <br />
                      <small>Tested at {testResults[method.id].timestamp}</small>
                    </Typography>
                  </Alert>
                )}
              </Paper>
            </Grid>
          ))}
        </Grid>
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
          {loading ? 'Saving...' : 'Save Changes'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default UniversalTargetEditModal;