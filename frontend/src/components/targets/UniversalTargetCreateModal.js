/**
 * Universal Target Create Modal
 * Compact single-form target creation.
 */
import React, { useState } from 'react';
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
  Typography,
  Alert,
  CircularProgress,
  Grid,
  Paper,
  Box,
  Divider,
  FormControlLabel,
  RadioGroup,
  Radio,
  IconButton,
  Chip,
  Stack,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Computer as ComputerIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  NetworkCheck as NetworkCheckIcon,
  PlayArrow as TestIcon
} from '@mui/icons-material';

import { 
  createTargetComprehensive, 
  validateTargetData, 
  getDefaultTargetData,
  getCommunicationMethodOptions,
  getEnvironmentOptions,
  getOSTypeOptions,
  getDefaultPortForMethod,
  getDatabaseConfigFields,
  testMethodConfiguration
} from '../../services/targetService';

const UniversalTargetCreateModal = ({ open, onClose, onTargetCreated }) => {
  const [targetData, setTargetData] = useState(getDefaultTargetData());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [validationErrors, setValidationErrors] = useState({});
  
  // Communication methods state
  const [communicationMethods, setCommunicationMethods] = useState([
    {
      id: 1,
      method_type: 'ssh',
      host: '',
      port: 22,
      username: '',
      credential_type: 'password',
      password: '',
      ssh_key: '',
      is_primary: true
    }
  ]);
  const [nextMethodId, setNextMethodId] = useState(2);
  const [testingMethods, setTestingMethods] = useState(new Set());
  const [testResults, setTestResults] = useState({});

  const handleClose = () => {
    if (!loading) {
      resetForm();
      onClose();
    }
  };

  const resetForm = () => {
    setTargetData(getDefaultTargetData());
    setError('');
    setValidationErrors({});
    setCommunicationMethods([
      {
        id: 1,
        method_type: 'ssh',
        host: '',
        port: 22,
        username: '',
        credential_type: 'password',
        password: '',
        ssh_key: '',
        is_primary: true
      }
    ]);
    setNextMethodId(2);
  };

  const handleInputChange = (field, value) => {
    setTargetData(prev => {
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
        
        // Reset communication methods to match new OS type
        const defaultMethodType = availableMethods.length > 0 ? availableMethods[0].value : 'ssh';
        setCommunicationMethods([
          {
            id: 1,
            method_type: defaultMethodType,
            host: prev.ip_address || '',
            port: getDefaultPortForMethod(defaultMethodType),
            username: '',
            credential_type: 'password',
            password: '',
            ssh_key: '',
            is_primary: true,
            ...getDatabaseConfigFields(defaultMethodType)
          }
        ]);
        setNextMethodId(2);
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

  const validateForm = () => {
    const errors = {};
    
    // Basic required fields
    if (!targetData.name.trim()) errors.name = 'Target name is required';
    if (!targetData.os_type) errors.os_type = 'Device/OS type is required';
    if (!targetData.ip_address.trim()) {
      errors.ip_address = 'IP address or DNS name is required';
    } else {
      const ipAddress = targetData.ip_address.trim();
      
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
            errors[`method_${method.id}_username`] = `Username required for method ${index + 1}`;
          }
          if (method.credential_type === 'password' && !method.password.trim()) {
            errors[`method_${method.id}_password`] = `Password required for method ${index + 1}`;
          }
          if (method.credential_type === 'ssh_key' && !method.ssh_key.trim()) {
            errors[`method_${method.id}_ssh_key`] = `SSH key required for method ${index + 1}`;
          }
        }
      });
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleCreate = async () => {
    if (!validateForm()) {
      setError('Please fix the validation errors before creating the target');
      return;
    }

    try {
      setLoading(true);
      setError('');

      // Validate communication methods
      if (!communicationMethods || communicationMethods.length === 0) {
        setError('At least one communication method is required');
        return;
      }

      // Ensure at least one method is marked as primary
      const hasPrimary = communicationMethods.some(method => method.is_primary);
      if (!hasPrimary) {
        communicationMethods[0].is_primary = true;
      }

      // Create the target with comprehensive structure (multiple methods support)
      const targetCreateData = {
        // Basic target information
        ...targetData,

        // Multiple communication methods support
        communication_methods: communicationMethods.map(method => ({
          method_type: method.method_type,
          config: {
            host: targetData.ip_address, // ALL methods use the target's IP address/hostname field
            port: method.port,
            // SMTP-specific config
            ...(method.method_type === 'smtp' && {
              encryption: method.encryption || 'starttls',
              server_type: method.server_type || 'smtp',
              domain: method.domain || '',
              test_recipient: method.test_recipient || '',
              connection_security: method.connection_security || 'auto'
            }),
            // REST API-specific config
            ...(method.method_type === 'rest_api' && {
              protocol: method.protocol || 'http',
              base_path: method.base_path || '/',
              verify_ssl: method.verify_ssl !== undefined ? method.verify_ssl : true
            }),
            // SNMP-specific config
            ...(method.method_type === 'snmp' && {
              version: method.version || '2c',
              community: method.community || 'public',
              retries: method.retries || 3,
              // SNMPv3-specific config
              ...(method.version === '3' && {
                security_level: method.security_level || 'authPriv',
                auth_protocol: method.auth_protocol || 'MD5',
                privacy_protocol: method.privacy_protocol || 'DES'
              })
            }),
            // Database-specific config
            ...(method.method_type === 'mysql' && {
              database: method.database || '',
              charset: method.charset || 'utf8mb4',
              ssl_mode: method.ssl_mode || 'disabled'
            }),
            ...(method.method_type === 'postgresql' && {
              database: method.database || 'postgres',
              ssl_mode: method.ssl_mode || 'prefer'
            }),
            ...(method.method_type === 'mssql' && {
              database: method.database || 'master',
              driver: method.driver || 'ODBC Driver 17 for SQL Server',
              encrypt: method.encrypt || 'yes'
            }),
            ...(method.method_type === 'oracle' && {
              service_name: method.service_name || '',
              sid: method.sid || ''
            }),
            ...(method.method_type === 'sqlite' && {
              database_path: method.database_path || ''
            }),
            ...(method.method_type === 'mongodb' && {
              database: method.database || 'admin',
              auth_source: method.auth_source || 'admin'
            }),
            ...(method.method_type === 'redis' && {
              database: method.database || 0
            }),
            ...(method.method_type === 'elasticsearch' && {
              ssl: method.ssl || false,
              verify_certs: method.verify_certs !== undefined ? method.verify_certs : true
            })
          },
          is_primary: method.is_primary || false,
          is_active: true,
          // Include credentials if provided
          ...(method.username && {
            credentials: [{
              credential_type: method.credential_type,
              encrypted_credentials: method.credential_type === 'password' 
                ? { username: method.username, password: method.password }
                : { username: method.username, ssh_key: method.ssh_key, ssh_passphrase: method.ssh_passphrase },
              is_primary: true,
              is_active: true
            }]
          })
        }))
      };

      console.log('Creating target with comprehensive data:', targetCreateData);
      console.log('Target IP/Hostname:', targetData.ip_address);
      console.log('Communication methods:', communicationMethods);
      await createTargetComprehensive(targetCreateData);
      onTargetCreated();
      resetForm();

    } catch (err) {
      console.error('Target creation error:', err);
      // Try to show backend error details if available
      let errorMsg = 'Failed to create target.';
      
      if (err && typeof err === 'object') {
        if (err.detail) {
          errorMsg = err.detail;
        } else if (err.message) {
          errorMsg = err.message;
        } else if (err.toString && err.toString() !== '[object Object]') {
          errorMsg = err.toString();
        } else {
          errorMsg = JSON.stringify(err);
        }
      } else if (typeof err === 'string') {
        // Try to parse as JSON if it looks like an object
        try {
          const parsed = JSON.parse(err);
          if (parsed && (parsed.detail || parsed.message)) {
            errorMsg = parsed.detail || parsed.message;
          } else {
            errorMsg = err;
          }
        } catch {
          errorMsg = err;
        }
      }
      
      setError(`Failed to create target: ${errorMsg}`);
    } finally {
      setLoading(false);
    }
  };

  // Communication Methods Helper Functions
  const addCommunicationMethod = () => {
    const newMethod = {
      id: nextMethodId,
      method_type: 'ssh',
      host: targetData.ip_address,
      port: 22,
      username: '',
      credential_type: 'password',
      password: '',
      ssh_key: '',
      is_primary: false
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
              port: getDefaultPortForMethod(value),
              // Add database-specific config fields
              ...getDatabaseConfigFields(value)
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

    // Validate required fields for testing
    if (!targetData.ip_address) {
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

    try {
      setTestingMethods(prev => new Set([...prev, methodId]));
      setError('');
      
      const testConfig = {
        method_type: method.method_type,
        host: targetData.ip_address, // Use target's IP address
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

      const result = await testMethodConfiguration(testConfig);

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

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ComputerIcon />
          <Typography variant="h6">Create New Target</Typography>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Compact Single-Screen Form */}
        <Grid container spacing={2} sx={{ mt: 0.5 }}>
          {/* Basic Info - Top Row */}
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Target Name *"
              value={targetData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              error={!!validationErrors.name}
              helperText={validationErrors.name}
              size="small"
            />
          </Grid>
          
          <Grid item xs={8}>
            <TextField
              fullWidth
              label="IP Address / DNS Name *"
              placeholder="192.168.1.100 or smtp.gmail.com"
              value={targetData.ip_address}
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
              <InputLabel>Device/OS Type *</InputLabel>
              <Select
                value={targetData.os_type}
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

          <Grid item xs={6}>
            <FormControl fullWidth size="small">
              <InputLabel>Environment</InputLabel>
              <Select
                value={targetData.environment}
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
            <TextField
              fullWidth
              label="Location"
              value={targetData.location}
              onChange={(e) => handleInputChange('location', e.target.value)}
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
                        {getCommunicationMethodOptions(targetData.os_type).map(option => (
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
                          />
                        )}
                      </Grid>
                    </>
                  )}
                  
                  {/* SMTP-Specific Fields */}
                  {method.method_type === 'smtp' && (
                    <>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" sx={{ mt: 1, mb: 1, color: 'primary.main' }}>
                          SMTP Configuration
                        </Typography>
                      </Grid>
                      

                      
                      <Grid item xs={4}>
                        <FormControl fullWidth size="small">
                          <InputLabel>Encryption</InputLabel>
                          <Select
                            value={method.encryption || 'starttls'}
                            label="Encryption"
                            onChange={(e) => updateCommunicationMethod(method.id, 'encryption', e.target.value)}
                          >
                            <MenuItem value="starttls">STARTTLS</MenuItem>
                            <MenuItem value="ssl">SSL/TLS</MenuItem>
                            <MenuItem value="none">None</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>
                      
                      <Grid item xs={4}>
                        <FormControl fullWidth size="small">
                          <InputLabel>Server Type</InputLabel>
                          <Select
                            value={method.server_type || 'smtp'}
                            label="Server Type"
                            onChange={(e) => updateCommunicationMethod(method.id, 'server_type', e.target.value)}
                          >
                            <MenuItem value="smtp">Generic SMTP</MenuItem>
                            <MenuItem value="exchange">Microsoft Exchange</MenuItem>
                            <MenuItem value="gmail">Gmail</MenuItem>
                            <MenuItem value="outlook">Outlook.com</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>
                      
                      <Grid item xs={4}>
                        <TextField
                          fullWidth
                          label="Email Domain"
                          value={method.domain || ''}
                          onChange={(e) => updateCommunicationMethod(method.id, 'domain', e.target.value)}
                          size="small"
                          placeholder="example.com"
                        />
                      </Grid>
                      
                      <Grid item xs={6}>
                        <TextField
                          fullWidth
                          label="Test Recipient Email"
                          value={method.test_recipient || ''}
                          onChange={(e) => updateCommunicationMethod(method.id, 'test_recipient', e.target.value)}
                          size="small"
                          placeholder="test@example.com"
                        />
                      </Grid>
                      
                      <Grid item xs={6}>
                        <FormControl fullWidth size="small">
                          <InputLabel>Connection Security</InputLabel>
                          <Select
                            value={method.connection_security || 'auto'}
                            label="Connection Security"
                            onChange={(e) => updateCommunicationMethod(method.id, 'connection_security', e.target.value)}
                          >
                            <MenuItem value="auto">Auto-detect</MenuItem>
                            <MenuItem value="ssl">SSL/TLS</MenuItem>
                            <MenuItem value="starttls">STARTTLS</MenuItem>
                            <MenuItem value="none">None</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>
                    </>
                  )}
                  
                  {/* REST API-Specific Fields */}
                  {method.method_type === 'rest_api' && (
                    <>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" sx={{ mt: 1, mb: 1, color: 'primary.main' }}>
                          REST API Configuration
                        </Typography>
                      </Grid>
                      
                      <Grid item xs={4}>
                        <FormControl fullWidth size="small">
                          <InputLabel>Protocol</InputLabel>
                          <Select
                            value={method.protocol || 'http'}
                            label="Protocol"
                            onChange={(e) => updateCommunicationMethod(method.id, 'protocol', e.target.value)}
                          >
                            <MenuItem value="http">HTTP</MenuItem>
                            <MenuItem value="https">HTTPS</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>
                      
                      <Grid item xs={4}>
                        <TextField
                          fullWidth
                          label="Base Path"
                          value={method.base_path || '/'}
                          onChange={(e) => updateCommunicationMethod(method.id, 'base_path', e.target.value)}
                          size="small"
                          placeholder="/api"
                        />
                      </Grid>
                      
                      <Grid item xs={4}>
                        <FormControl fullWidth size="small">
                          <InputLabel>Verify SSL</InputLabel>
                          <Select
                            value={method.verify_ssl !== undefined ? method.verify_ssl.toString() : 'true'}
                            label="Verify SSL"
                            onChange={(e) => updateCommunicationMethod(method.id, 'verify_ssl', e.target.value === 'true')}
                          >
                            <MenuItem value="true">Yes</MenuItem>
                            <MenuItem value="false">No</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>
                    </>
                  )}
                  
                  {/* SNMP-Specific Fields */}
                  {method.method_type === 'snmp' && (
                    <>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" sx={{ mt: 1, mb: 1, color: 'primary.main' }}>
                          SNMP Configuration
                        </Typography>
                      </Grid>
                      
                      <Grid item xs={4}>
                        <FormControl fullWidth size="small">
                          <InputLabel>SNMP Version</InputLabel>
                          <Select
                            value={method.version || '2c'}
                            label="SNMP Version"
                            onChange={(e) => updateCommunicationMethod(method.id, 'version', e.target.value)}
                          >
                            <MenuItem value="1">SNMPv1</MenuItem>
                            <MenuItem value="2c">SNMPv2c</MenuItem>
                            <MenuItem value="3">SNMPv3</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>
                      
                      {method.version !== '3' && (
                        <Grid item xs={4}>
                          <TextField
                            fullWidth
                            label="Community String"
                            value={method.community || 'public'}
                            onChange={(e) => updateCommunicationMethod(method.id, 'community', e.target.value)}
                            size="small"
                            placeholder="public"
                          />
                        </Grid>
                      )}
                      
                      <Grid item xs={4}>
                        <TextField
                          fullWidth
                          label="Retries"
                          type="number"
                          value={method.retries || 3}
                          onChange={(e) => updateCommunicationMethod(method.id, 'retries', parseInt(e.target.value) || 3)}
                          size="small"
                          inputProps={{ min: 1, max: 10 }}
                        />
                      </Grid>
                      
                      {/* SNMPv3-Specific Fields */}
                      {method.version === '3' && (
                        <>
                          <Grid item xs={12}>
                            <Typography variant="subtitle2" sx={{ mt: 1, mb: 1, color: 'secondary.main' }}>
                              SNMPv3 Security Configuration
                            </Typography>
                          </Grid>
                          
                          <Grid item xs={4}>
                            <FormControl fullWidth size="small">
                              <InputLabel>Security Level</InputLabel>
                              <Select
                                value={method.security_level || 'authPriv'}
                                label="Security Level"
                                onChange={(e) => updateCommunicationMethod(method.id, 'security_level', e.target.value)}
                              >
                                <MenuItem value="noAuthNoPriv">No Auth, No Privacy</MenuItem>
                                <MenuItem value="authNoPriv">Auth, No Privacy</MenuItem>
                                <MenuItem value="authPriv">Auth + Privacy</MenuItem>
                              </Select>
                            </FormControl>
                          </Grid>
                          
                          {(method.security_level === 'authNoPriv' || method.security_level === 'authPriv' || !method.security_level) && (
                            <Grid item xs={4}>
                              <FormControl fullWidth size="small">
                                <InputLabel>Auth Protocol</InputLabel>
                                <Select
                                  value={method.auth_protocol || 'MD5'}
                                  label="Auth Protocol"
                                  onChange={(e) => updateCommunicationMethod(method.id, 'auth_protocol', e.target.value)}
                                >
                                  <MenuItem value="MD5">MD5</MenuItem>
                                  <MenuItem value="SHA">SHA</MenuItem>
                                </Select>
                              </FormControl>
                            </Grid>
                          )}
                          
                          {(method.security_level === 'authPriv' || !method.security_level) && (
                            <Grid item xs={4}>
                              <FormControl fullWidth size="small">
                                <InputLabel>Privacy Protocol</InputLabel>
                                <Select
                                  value={method.privacy_protocol || 'DES'}
                                  label="Privacy Protocol"
                                  onChange={(e) => updateCommunicationMethod(method.id, 'privacy_protocol', e.target.value)}
                                >
                                  <MenuItem value="DES">DES</MenuItem>
                                  <MenuItem value="AES">AES</MenuItem>
                                </Select>
                              </FormControl>
                            </Grid>
                          )}
                          
                          <Grid item xs={12}>
                            <Typography variant="body2" sx={{ mt: 1, color: 'text.secondary', fontStyle: 'italic' }}>
                              SNMPv3 Credentials: Username (required), Password (auth key), SSH Key (privacy key)
                            </Typography>
                          </Grid>
                        </>
                      )}
                    </>
                  )}
                  
                  {/* Database-Specific Fields */}
                  {['mysql', 'postgresql', 'mssql', 'oracle', 'sqlite', 'mongodb', 'redis', 'elasticsearch'].includes(method.method_type) && (
                    <>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" sx={{ mt: 1, mb: 1, color: 'primary.main' }}>
                          Database Configuration
                        </Typography>
                      </Grid>
                      
                      {/* MySQL Configuration */}
                      {method.method_type === 'mysql' && (
                        <>
                          <Grid item xs={4}>
                            <TextField
                              fullWidth
                              label="Database Name"
                              value={method.database || ''}
                              onChange={(e) => updateCommunicationMethod(method.id, 'database', e.target.value)}
                              size="small"
                              placeholder="my_database"
                            />
                          </Grid>
                          <Grid item xs={4}>
                            <FormControl fullWidth size="small">
                              <InputLabel>SSL Mode</InputLabel>
                              <Select
                                value={method.ssl_mode || 'disabled'}
                                label="SSL Mode"
                                onChange={(e) => updateCommunicationMethod(method.id, 'ssl_mode', e.target.value)}
                              >
                                <MenuItem value="disabled">Disabled</MenuItem>
                                <MenuItem value="preferred">Preferred</MenuItem>
                                <MenuItem value="required">Required</MenuItem>
                                <MenuItem value="verify_identity">Verify Identity</MenuItem>
                              </Select>
                            </FormControl>
                          </Grid>
                          <Grid item xs={4}>
                            <TextField
                              fullWidth
                              label="Charset"
                              value={method.charset || 'utf8mb4'}
                              onChange={(e) => updateCommunicationMethod(method.id, 'charset', e.target.value)}
                              size="small"
                            />
                          </Grid>
                        </>
                      )}
                      
                      {/* PostgreSQL Configuration */}
                      {method.method_type === 'postgresql' && (
                        <>
                          <Grid item xs={6}>
                            <TextField
                              fullWidth
                              label="Database Name"
                              value={method.database || 'postgres'}
                              onChange={(e) => updateCommunicationMethod(method.id, 'database', e.target.value)}
                              size="small"
                            />
                          </Grid>
                          <Grid item xs={6}>
                            <FormControl fullWidth size="small">
                              <InputLabel>SSL Mode</InputLabel>
                              <Select
                                value={method.ssl_mode || 'prefer'}
                                label="SSL Mode"
                                onChange={(e) => updateCommunicationMethod(method.id, 'ssl_mode', e.target.value)}
                              >
                                <MenuItem value="disable">Disable</MenuItem>
                                <MenuItem value="allow">Allow</MenuItem>
                                <MenuItem value="prefer">Prefer</MenuItem>
                                <MenuItem value="require">Require</MenuItem>
                                <MenuItem value="verify-ca">Verify CA</MenuItem>
                                <MenuItem value="verify-full">Verify Full</MenuItem>
                              </Select>
                            </FormControl>
                          </Grid>
                        </>
                      )}
                      
                      {/* SQL Server Configuration */}
                      {method.method_type === 'mssql' && (
                        <>
                          <Grid item xs={4}>
                            <TextField
                              fullWidth
                              label="Database Name"
                              value={method.database || 'master'}
                              onChange={(e) => updateCommunicationMethod(method.id, 'database', e.target.value)}
                              size="small"
                            />
                          </Grid>
                          <Grid item xs={4}>
                            <FormControl fullWidth size="small">
                              <InputLabel>Encrypt</InputLabel>
                              <Select
                                value={method.encrypt || 'yes'}
                                label="Encrypt"
                                onChange={(e) => updateCommunicationMethod(method.id, 'encrypt', e.target.value)}
                              >
                                <MenuItem value="yes">Yes</MenuItem>
                                <MenuItem value="no">No</MenuItem>
                              </Select>
                            </FormControl>
                          </Grid>
                          <Grid item xs={4}>
                            <TextField
                              fullWidth
                              label="Driver"
                              value={method.driver || 'ODBC Driver 17 for SQL Server'}
                              onChange={(e) => updateCommunicationMethod(method.id, 'driver', e.target.value)}
                              size="small"
                            />
                          </Grid>
                        </>
                      )}
                      
                      {/* Oracle Configuration */}
                      {method.method_type === 'oracle' && (
                        <>
                          <Grid item xs={6}>
                            <TextField
                              fullWidth
                              label="Service Name"
                              value={method.service_name || ''}
                              onChange={(e) => updateCommunicationMethod(method.id, 'service_name', e.target.value)}
                              size="small"
                              placeholder="ORCL"
                            />
                          </Grid>
                          <Grid item xs={6}>
                            <TextField
                              fullWidth
                              label="SID (alternative to Service Name)"
                              value={method.sid || ''}
                              onChange={(e) => updateCommunicationMethod(method.id, 'sid', e.target.value)}
                              size="small"
                              placeholder="ORCL"
                            />
                          </Grid>
                        </>
                      )}
                      
                      {/* SQLite Configuration */}
                      {method.method_type === 'sqlite' && (
                        <Grid item xs={12}>
                          <TextField
                            fullWidth
                            label="Database File Path"
                            value={method.database_path || ''}
                            onChange={(e) => updateCommunicationMethod(method.id, 'database_path', e.target.value)}
                            size="small"
                            placeholder="/path/to/database.db"
                          />
                        </Grid>
                      )}
                      
                      {/* MongoDB Configuration */}
                      {method.method_type === 'mongodb' && (
                        <>
                          <Grid item xs={6}>
                            <TextField
                              fullWidth
                              label="Database Name"
                              value={method.database || 'admin'}
                              onChange={(e) => updateCommunicationMethod(method.id, 'database', e.target.value)}
                              size="small"
                            />
                          </Grid>
                          <Grid item xs={6}>
                            <TextField
                              fullWidth
                              label="Auth Source"
                              value={method.auth_source || 'admin'}
                              onChange={(e) => updateCommunicationMethod(method.id, 'auth_source', e.target.value)}
                              size="small"
                            />
                          </Grid>
                        </>
                      )}
                      
                      {/* Redis Configuration */}
                      {method.method_type === 'redis' && (
                        <Grid item xs={6}>
                          <TextField
                            fullWidth
                            label="Database Number"
                            type="number"
                            value={method.database || 0}
                            onChange={(e) => updateCommunicationMethod(method.id, 'database', parseInt(e.target.value) || 0)}
                            size="small"
                            inputProps={{ min: 0, max: 15 }}
                          />
                        </Grid>
                      )}
                      
                      {/* Elasticsearch Configuration */}
                      {method.method_type === 'elasticsearch' && (
                        <>
                          <Grid item xs={6}>
                            <FormControl fullWidth size="small">
                              <InputLabel>Use SSL</InputLabel>
                              <Select
                                value={method.ssl ? 'true' : 'false'}
                                label="Use SSL"
                                onChange={(e) => updateCommunicationMethod(method.id, 'ssl', e.target.value === 'true')}
                              >
                                <MenuItem value="false">No</MenuItem>
                                <MenuItem value="true">Yes</MenuItem>
                              </Select>
                            </FormControl>
                          </Grid>
                          <Grid item xs={6}>
                            <FormControl fullWidth size="small">
                              <InputLabel>Verify Certificates</InputLabel>
                              <Select
                                value={method.verify_certs !== undefined ? method.verify_certs.toString() : 'true'}
                                label="Verify Certificates"
                                onChange={(e) => updateCommunicationMethod(method.id, 'verify_certs', e.target.value === 'true')}
                              >
                                <MenuItem value="true">Yes</MenuItem>
                                <MenuItem value="false">No</MenuItem>
                              </Select>
                            </FormControl>
                          </Grid>
                        </>
                      )}
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
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        
        <Button 
          onClick={handleCreate} 
          variant="contained" 
          disabled={loading}
          startIcon={loading ? <CircularProgress size={16} /> : <AddIcon />}
        >
          {loading ? 'Creating...' : 'Create Target'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default UniversalTargetCreateModal;