/**
 * Communication Methods Manager
 * Advanced interface for managing multiple communication methods and credentials per target
 */
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Grid,
  Paper,
  Chip,
  IconButton,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  Stack,
  Tooltip,
  CircularProgress
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  ExpandMore as ExpandMoreIcon,
  NetworkCheck as NetworkCheckIcon,
  VpnKey as VpnKeyIcon,
  Settings as SettingsIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import { CloseAction } from '../common/StandardActions';

import { 
  addCommunicationMethod, 
  updateCommunicationMethod, 
  deleteCommunicationMethod,
  testCommunicationMethod,
  getTargetById 
} from '../../services/targetService';

const CommunicationMethodsManager = ({ 
  open, 
  target, 
  onClose, 
  onMethodsUpdated 
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [methods, setMethods] = useState([]);
  const [editingMethod, setEditingMethod] = useState(null);
  const [newMethod, setNewMethod] = useState(null);

  // Load target's communication methods
  useEffect(() => {
    if (open && target?.communication_methods) {
      setMethods(target.communication_methods);
    }
  }, [open, target]);

  const handleClose = () => {
    setEditingMethod(null);
    setNewMethod(null);
    setError('');
    onClose();
  };

  const handleAddMethod = () => {
    // Get target's primary IP address
    const primaryIP = target?.communication_methods?.[0]?.config?.host || '';
    
    setNewMethod({
      method_type: 'ssh',
      config: { 
        host: primaryIP, // Use target's IP by default
        port: 22 
      },
      is_primary: methods.length === 0, // First method is primary
      is_active: true,
      credentials: [{
        credential_type: 'password',
        credential_name: '',
        username: '',
        password: '',
        ssh_key: '',
        ssh_passphrase: '',
        is_primary: true,
        is_active: true
      }]
    });
  };

  const handleSaveNewMethod = async () => {
    try {
      setLoading(true);
      setError('');
      
      const credential = newMethod.credentials?.[0] || {};
      
      // Prepare method data for API
      const methodData = {
        method_type: newMethod.method_type,
        config: newMethod.config,
        is_primary: newMethod.is_primary,
        is_active: newMethod.is_active,
        priority: newMethod.priority || 1,
        credential_type: credential.credential_type || 'password',
        username: credential.username,
        password: credential.password,
        ssh_key: credential.ssh_key,
        ssh_passphrase: credential.ssh_passphrase
      };
      
      // Call API to add communication method
      const createdMethod = await addCommunicationMethod(target.id, methodData);
      console.log('Created method:', createdMethod);
      
      // Add to local state
      setMethods(prev => {
        const updated = [...prev, createdMethod];
        console.log('Updated methods:', updated);
        return updated;
      });
      setNewMethod(null);
      
      if (onMethodsUpdated) {
        onMethodsUpdated();
      }
    } catch (err) {
      console.error('Error adding communication method:', err);
      setError(`Failed to add communication method: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteMethod = async (methodId) => {
    if (window.confirm('Are you sure you want to delete this communication method?')) {
      try {
        setLoading(true);
        setError('');
        
        // Call API to delete communication method
        await deleteCommunicationMethod(target.id, methodId);
        
        // Remove from local state
        setMethods(prev => prev.filter(m => m.id !== methodId));
        
        if (onMethodsUpdated) {
          onMethodsUpdated();
        }
      } catch (err) {
        setError(`Failed to delete communication method: ${err.message}`);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleSetPrimary = async (methodId) => {
    try {
      setLoading(true);
      setError('');
      
      // Call API to update method as primary
      const updatedMethod = await updateCommunicationMethod(target.id, methodId, { is_primary: true });
      console.log('Updated method response:', updatedMethod);
      
      // Update local state
      setMethods(prev => {
        const updated = prev.map(m => ({
          ...m,
          is_primary: m.id === methodId
        }));
        console.log('Updated methods state:', updated);
        return updated;
      });
      
      if (onMethodsUpdated) {
        onMethodsUpdated();
      }
    } catch (err) {
      setError(`Failed to set primary method: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleTestMethod = async (method) => {
    try {
      setLoading(true);
      setError('');
      
      // Call API to test this specific method
      const result = await testCommunicationMethod(target.id, method.id);
      
      // Show detailed test results
      const resultMessage = `
🔧 Method: ${result.method_type?.toUpperCase() || method.method_type.toUpperCase()}
🌐 Host: ${result.host || method.config.host}:${result.port || method.config.port}
👤 User: ${result.username || 'unknown'}
🔐 Auth: ${result.credential_type || 'unknown'}
⏱️ Duration: ${result.test_duration || 0}ms

${result.success ? '✅ SUCCESS' : '❌ FAILED'}
${result.message}

🐛 Debug: ${result.debug_info || 'No debug info'}
Frontend Method ID: ${method.id}
Frontend Method Type: ${method.method_type}

${result.details ? JSON.stringify(result.details, null, 2) : ''}
      `.trim();
      
      if (result.success) {
        alert(`Connection Test Successful!\n\n${resultMessage}`);
      } else {
        alert(`Connection Test Failed!\n\n${resultMessage}`);
      }
      
    } catch (err) {
      setError(`Connection test failed: ${err.message}`);
      alert(`Connection Test Error!\n\n❌ ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const renderMethodForm = (method, isNew = false) => {
    const credential = method.credentials?.[0] || {};
    
    const updateMethod = (updates) => {
      const updatedMethod = { ...method, ...updates };
      if (isNew) {
        setNewMethod(updatedMethod);
      } else {
        setEditingMethod(updatedMethod);
      }
    };

    const updateCredential = (credUpdates) => {
      const updatedCredentials = [...(method.credentials || [])];
      updatedCredentials[0] = { ...credential, ...credUpdates };
      updateMethod({ credentials: updatedCredentials });
    };

    return (
      <Box sx={{ p: 2 }}>
        <Grid container spacing={2}>
          {/* Method Configuration */}
          <Grid item xs={12}>
            <Typography variant="subtitle2" gutterBottom sx={{ color: 'primary.main' }}>
              Connection Method
            </Typography>
          </Grid>
          
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Method Type</InputLabel>
              <Select
                value={method.method_type}
                label="Method Type"
                onChange={(e) => {
                  const newType = e.target.value;
                  updateMethod({
                    method_type: newType,
                    config: {
                      ...method.config,
                      port: newType === 'ssh' ? 22 : 5985
                    },
                    credentials: [{
                      ...credential,
                      credential_type: newType === 'ssh' ? 'password' : 'password'
                    }]
                  });
                }}
              >
                <MenuItem value="ssh">SSH</MenuItem>
                <MenuItem value="winrm">WinRM</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              size="small"
              label="Host/IP Address"
              value={method.config.host || ''}
              onChange={(e) => updateMethod({
                config: { ...method.config, host: e.target.value }
              })}
              helperText="Usually same as target's primary IP"
            />
          </Grid>
          
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              size="small"
              label="Port"
              type="number"
              value={method.config.port || ''}
              onChange={(e) => updateMethod({
                config: { ...method.config, port: parseInt(e.target.value) }
              })}
              helperText={method.method_type === 'ssh' ? 'Default: 22' : 'Default: 5985 (HTTP), 5986 (HTTPS)'}
            />
          </Grid>

          {/* Method Settings */}
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth size="small">
              <InputLabel>Priority</InputLabel>
              <Select
                value={method.is_primary ? 'primary' : 'secondary'}
                label="Priority"
                onChange={(e) => updateMethod({
                  is_primary: e.target.value === 'primary'
                })}
              >
                <MenuItem value="primary">Primary Method</MenuItem>
                <MenuItem value="secondary">Secondary Method</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={method.is_active ? 'active' : 'inactive'}
                label="Status"
                onChange={(e) => updateMethod({
                  is_active: e.target.value === 'active'
                })}
              >
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="inactive">Inactive</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* Credentials Section */}
          <Grid item xs={12}>
            <Typography variant="subtitle2" gutterBottom sx={{ color: 'secondary.main', mt: 2 }}>
              Authentication Credentials
            </Typography>
          </Grid>

          <Grid item xs={12} sm={6}>
            <FormControl fullWidth size="small">
              <InputLabel>Credential Type</InputLabel>
              <Select
                value={credential.credential_type || 'password'}
                label="Credential Type"
                onChange={(e) => {
                  const newType = e.target.value;
                  updateCredential({
                    credential_type: newType,
                    credential_name: `${credential.username || 'user'}_${newType}`
                  });
                }}
              >
                <MenuItem value="password">Username & Password</MenuItem>
                {method.method_type === 'ssh' && (
                  <MenuItem value="ssh_key">SSH Key</MenuItem>
                )}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              size="small"
              label="Username"
              value={credential.username || ''}
              onChange={(e) => updateCredential({
                username: e.target.value,
                credential_name: `${e.target.value}_${credential.credential_type || 'password'}`
              })}
              required
            />
          </Grid>

          {/* Password Authentication */}
          {credential.credential_type !== 'ssh_key' && (
            <Grid item xs={12}>
              <TextField
                fullWidth
                size="small"
                label="Password"
                type="password"
                value={credential.password || ''}
                onChange={(e) => updateCredential({ password: e.target.value })}
                required
              />
            </Grid>
          )}

          {/* SSH Key Authentication */}
          {credential.credential_type === 'ssh_key' && (
            <>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  size="small"
                  label="SSH Private Key"
                  multiline
                  rows={4}
                  value={credential.ssh_key || ''}
                  onChange={(e) => updateCredential({ ssh_key: e.target.value })}
                  placeholder="-----BEGIN OPENSSH PRIVATE KEY-----&#10;...&#10;-----END OPENSSH PRIVATE KEY-----"
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  size="small"
                  label="SSH Key Passphrase (Optional)"
                  type="password"
                  value={credential.ssh_passphrase || ''}
                  onChange={(e) => updateCredential({ ssh_passphrase: e.target.value })}
                  helperText="Leave empty if key has no passphrase"
                />
              </Grid>
            </>
          )}
          
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end', mt: 2 }}>
              <Button
                startIcon={<CancelIcon />}
                onClick={() => {
                  if (isNew) {
                    setNewMethod(null);
                  } else {
                    setEditingMethod(null);
                  }
                }}
                size="small"
              >
                Cancel
              </Button>
              <Button
                startIcon={<SaveIcon />}
                onClick={isNew ? handleSaveNewMethod : () => {
                  // TODO: Save edited method
                  setEditingMethod(null);
                }}
                variant="contained"
                size="small"
                disabled={loading || !credential.username || 
                  (credential.credential_type === 'ssh_key' ? !credential.ssh_key : !credential.password)}
              >
                {isNew ? 'Add Method' : 'Save Changes'}
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Box>
    );
  };

  const renderMethod = (method) => (
    <Accordion key={method.id} sx={{ mb: 1 }}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {method.method_type === 'ssh' ? <VpnKeyIcon /> : <SettingsIcon />}
            <Typography variant="subtitle1" fontWeight={500}>
              {method.method_type.toUpperCase()}
            </Typography>
            <Typography variant="body2" color="text.secondary" fontFamily="monospace">
              {method.config.host}:{method.config.port}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, ml: 'auto', mr: 2 }}>
            {method.is_primary && (
              <Chip label="Primary" size="small" color="primary" />
            )}
            <Chip 
              label={method.is_active ? 'Active' : 'Inactive'} 
              size="small"
              color={method.is_active ? 'success' : 'default'}
            />
          </Box>
        </Box>
      </AccordionSummary>
      
      <AccordionDetails>
        {editingMethod?.id === method.id ? (
          renderMethodForm(editingMethod)
        ) : (
          <Box>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Configuration
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Host</Typography>
                    <Typography variant="body2" fontFamily="monospace">
                      {method.config.host}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Port</Typography>
                    <Typography variant="body2">{method.config.port}</Typography>
                  </Box>
                </Box>
              </Grid>
              
              <Grid item xs={12}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Credentials ({method.credentials?.length || 0})
                </Typography>
                {method.credentials?.map((cred) => (
                  <Paper key={cred.id} variant="outlined" sx={{ p: 1, mb: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box>
                        <Typography variant="body2" fontWeight={500}>
                          {cred.credential_name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {cred.credential_type}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        {cred.is_primary && (
                          <Chip label="Primary" size="small" color="primary" />
                        )}
                        <Chip 
                          label={cred.is_active ? 'Active' : 'Inactive'} 
                          size="small"
                          color={cred.is_active ? 'success' : 'default'}
                        />
                      </Box>
                    </Box>
                  </Paper>
                ))}
                <Button
                  startIcon={<AddIcon />}
                  size="small"
                  variant="outlined"
                  onClick={() => {
                    // TODO: Add credential to this method
                    console.log('Add credential to method:', method.id);
                  }}
                >
                  Add Credential
                </Button>
              </Grid>
            </Grid>
            
            <Divider sx={{ my: 2 }} />
            
            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
              <Button
                startIcon={<NetworkCheckIcon />}
                onClick={() => handleTestMethod(method)}
                disabled={loading || !method.is_active}
                variant="outlined"
                size="small"
              >
                Test
              </Button>
              
              {!method.is_primary && (
                <Tooltip title="Set as primary method">
                  <Button
                    startIcon={<StarIcon />}
                    onClick={() => handleSetPrimary(method.id)}
                    disabled={loading}
                    variant="outlined"
                    size="small"
                  >
                    Set Primary
                  </Button>
                </Tooltip>
              )}
              
              <Button
                startIcon={<EditIcon />}
                onClick={() => setEditingMethod(method)}
                disabled={loading}
                variant="outlined"
                size="small"
              >
                Edit
              </Button>
              
              <Button
                startIcon={<DeleteIcon />}
                onClick={() => handleDeleteMethod(method.id)}
                disabled={loading || method.is_primary}
                color="error"
                variant="outlined"
                size="small"
              >
                Delete
              </Button>
            </Box>
          </Box>
        )}
      </AccordionDetails>
    </Accordion>
  );

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">
            Communication Methods - {target?.name}
          </Typography>
          <CloseAction onClick={handleClose} />
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        <Box sx={{ mb: 2 }}>
          <Button
            startIcon={<AddIcon />}
            onClick={handleAddMethod}
            variant="contained"
            size="small"
            disabled={loading || newMethod !== null}
          >
            Add Communication Method
          </Button>
        </Box>

        {/* New Method Form */}
        {newMethod && (
          <Paper variant="outlined" sx={{ mb: 2 }}>
            <Box sx={{ p: 2, bgcolor: 'primary.50', borderBottom: 1, borderColor: 'divider' }}>
              <Typography variant="h6" gutterBottom>
                Add New Communication Method
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Configure connection method and credentials for {target?.name}
              </Typography>
            </Box>
            {renderMethodForm(newMethod, true)}
          </Paper>
        )}

        {/* Existing Methods */}
        {methods.length === 0 ? (
          <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
            No communication methods configured
          </Typography>
        ) : (
          <Box>
            {methods.map(renderMethod)}
          </Box>
        )}
      </DialogContent>
      

    </Dialog>
  );
};

export default CommunicationMethodsManager;