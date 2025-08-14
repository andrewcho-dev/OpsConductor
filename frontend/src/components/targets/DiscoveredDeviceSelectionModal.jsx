/**
 * Discovered Device Selection Modal
 * Allows users to select discovered devices and configure them as targets
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Checkbox,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Typography,
  Box,
  Chip,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Computer as ComputerIcon,
  Router as RouterIcon,
  Storage as StorageIcon,
  DeviceHub as DeviceHubIcon
} from '@mui/icons-material';
import discoveryService from '../../services/discoveryService';

const DiscoveredDeviceSelectionModal = ({ open, onClose, onDevicesImported, devices = [] }) => {
  const [selectedDevices, setSelectedDevices] = useState(new Set());
  const [expandedDevices, setExpandedDevices] = useState(new Set());
  const [deviceConfigs, setDeviceConfigs] = useState({});
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState(null);

  // Initialize device configurations when devices prop changes
  useEffect(() => {
    if (devices && devices.length > 0) {
      const configs = {};
      devices.forEach(device => {
        configs[device.id] = {
          target_name: device.hostname || `device-${device.ip_address.replace(/\./g, '-')}`,
          description: `Discovered device at ${device.ip_address}`,
          environment: 'development',
          communication_method: device.suggested_communication_methods?.[0] || 'ssh',
          username: 'admin',
          password: '',
          ssh_key: '',
          ssh_passphrase: '',
          port: null
        };
      });
      setDeviceConfigs(configs);
    }
  }, [devices]);

  // Reset state when modal opens/closes
  useEffect(() => {
    if (!open) {
      setSelectedDevices(new Set());
      setExpandedDevices(new Set());
      setError(null);
    }
  }, [open]);

  const handleDeviceSelect = (deviceId, selected) => {
    const newSelected = new Set(selectedDevices);
    if (selected) {
      newSelected.add(deviceId);
    } else {
      newSelected.delete(deviceId);
    }
    setSelectedDevices(newSelected);
  };

  const handleAccordionToggle = (deviceId, expanded) => {
    const newExpanded = new Set(expandedDevices);
    if (expanded) {
      newExpanded.add(deviceId);
    } else {
      newExpanded.delete(deviceId);
    }
    setExpandedDevices(newExpanded);
  };

  const handleSelectAll = (selected) => {
    if (selected && devices) {
      setSelectedDevices(new Set(devices.map(d => d.id)));
    } else {
      setSelectedDevices(new Set());
    }
  };

  const handleConfigChange = (deviceId, field, value) => {
    setDeviceConfigs(prev => ({
      ...prev,
      [deviceId]: {
        ...prev[deviceId],
        [field]: value
      }
    }));
  };

  const handleImportSelected = async () => {
    if (selectedDevices.size === 0) {
      setError('Please select at least one device to import');
      return;
    }

    try {
      setImporting(true);
      setError(null);

      // Prepare device configurations for selected devices
      const deviceConfigsList = Array.from(selectedDevices).map(deviceId => {
        const device = devices.find(d => d.id === deviceId);
        const config = deviceConfigs[deviceId];
        
        return {
          // Include the full device data for in-memory devices
          device_data: {
            ip_address: device.ip_address,
            hostname: device.hostname,
            mac_address: device.mac_address,
            open_ports: device.open_ports,
            services: device.services,
            snmp_info: device.snmp_info,
            device_type: device.device_type,
            os_type: device.os_type,
            confidence_score: device.confidence_score,
            suggested_communication_methods: device.suggested_communication_methods
          },
          target_name: config.target_name,
          description: config.description,
          environment: config.environment,
          communication_method: config.communication_method,
          username: config.username,
          password: config.password || null,
          ssh_key: config.ssh_key || null,
          ssh_passphrase: config.ssh_passphrase || null,
          port: config.port || null
        };
      });

      const result = await discoveryService.importInMemoryDevices({
        device_configs: deviceConfigsList
      });

      if (onDevicesImported) {
        onDevicesImported(result);
      }

      onClose();

    } catch (err) {
      console.error('Error importing devices:', err);
      setError(err.message || 'Failed to import selected devices');
    } finally {
      setImporting(false);
    }
  };

  const getDeviceIcon = (deviceType) => {
    switch (deviceType) {
      case 'router':
      case 'switch':
        return <RouterIcon />;
      case 'server':
        return <StorageIcon />;
      case 'workstation':
      case 'desktop':
        return <ComputerIcon />;
      default:
        return <DeviceHubIcon />;
    }
  };

  const getMethodColor = (method) => {
    const colors = {
      ssh: 'primary',
      winrm: 'secondary',
      snmp: 'success',
      telnet: 'warning',
      http: 'info',
      https: 'info'
    };
    return colors[method] || 'default';
  };

  return (
    <Dialog 
      open={open} 
      onClose={onClose}
      maxWidth="lg"
      fullWidth
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">
            Select Devices to Import as Targets
          </Typography>
          {devices && devices.length > 0 && (
            <Typography variant="body2" color="textSecondary">
              {devices.length} importable device{devices.length !== 1 ? 's' : ''} found
            </Typography>
          )}
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {loading ? (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        ) : !devices || devices.length === 0 ? (
          <Alert severity="info">
            No importable devices found. All discovered devices may already be registered as targets.
          </Alert>
        ) : (
          <>
            {/* Selection Controls */}
            <Box mb={2}>
              <Button
                size="small"
                onClick={() => handleSelectAll(true)}
                disabled={importing}
              >
                Select All
              </Button>
              <Button
                size="small"
                onClick={() => handleSelectAll(false)}
                disabled={importing}
                sx={{ ml: 1 }}
              >
                Select None
              </Button>
              <Typography variant="body2" component="span" sx={{ ml: 2 }}>
                {selectedDevices.size} of {devices ? devices.length : 0} selected
              </Typography>
            </Box>

            {/* Device List */}
            <Box>
              {devices && devices.map((device, index) => (
                <Accordion 
                  key={`device-${device.id}-${device.ip_address}`}
                  expanded={expandedDevices.has(device.id)}
                  onChange={(e, expanded) => handleAccordionToggle(device.id, expanded)}
                  sx={{
                    backgroundColor: selectedDevices.has(device.id) ? 'action.selected' : 'background.paper',
                    '&:hover': {
                      backgroundColor: selectedDevices.has(device.id) ? 'action.selected' : 'action.hover'
                    }
                  }}
                >
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box display="flex" alignItems="center" width="100%">
                      <Checkbox
                        checked={selectedDevices.has(device.id)}
                        onChange={(e) => {
                          e.stopPropagation();
                          handleDeviceSelect(device.id, e.target.checked);
                        }}
                        disabled={importing}
                      />
                      <Box display="flex" alignItems="center" ml={1} flex={1}>
                        {getDeviceIcon(device.device_type)}
                        <Box ml={2}>
                          <Typography 
                            variant="subtitle1"
                            sx={{
                              fontWeight: selectedDevices.has(device.id) ? 'bold' : 'normal',
                              color: selectedDevices.has(device.id) ? 'primary.main' : 'text.primary'
                            }}
                          >
                            {selectedDevices.has(device.id) && '✓ '}
                            {device.hostname || device.ip_address}
                          </Typography>
                          <Box display="flex" gap={1} mt={0.5}>
                            <Chip 
                              label={device.ip_address} 
                              size="small" 
                              variant="outlined" 
                            />
                            {device.device_type && (
                              <Chip 
                                label={device.device_type} 
                                size="small" 
                                color="primary" 
                                variant="outlined" 
                              />
                            )}
                            {device.suggested_communication_methods?.map(method => (
                              <Chip
                                key={method}
                                label={method.toUpperCase()}
                                size="small"
                                color={getMethodColor(method)}
                                variant="outlined"
                              />
                            ))}
                          </Box>
                        </Box>
                      </Box>
                    </Box>
                  </AccordionSummary>
                  
                  {selectedDevices.has(device.id) && (
                    <AccordionDetails>
                      <Grid container spacing={2}>
                        <Grid item xs={12} md={6}>
                          <TextField
                            label="Target Name"
                            value={deviceConfigs[device.id]?.target_name || ''}
                            onChange={(e) => handleConfigChange(device.id, 'target_name', e.target.value)}
                            fullWidth
                            size="small"
                            disabled={importing}
                            required
                          />
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <FormControl fullWidth size="small">
                            <InputLabel>Environment</InputLabel>
                            <Select
                              value={deviceConfigs[device.id]?.environment || 'development'}
                              onChange={(e) => handleConfigChange(device.id, 'environment', e.target.value)}
                              disabled={importing}
                            >
                              <MenuItem value="development">Development</MenuItem>
                              <MenuItem value="staging">Staging</MenuItem>
                              <MenuItem value="production">Production</MenuItem>
                            </Select>
                          </FormControl>
                        </Grid>
                        <Grid item xs={12}>
                          <TextField
                            label="Description"
                            value={deviceConfigs[device.id]?.description || ''}
                            onChange={(e) => handleConfigChange(device.id, 'description', e.target.value)}
                            fullWidth
                            size="small"
                            disabled={importing}
                            multiline
                            rows={2}
                          />
                        </Grid>
                        <Grid item xs={12} md={4}>
                          <FormControl fullWidth size="small">
                            <InputLabel>Communication Method</InputLabel>
                            <Select
                              value={deviceConfigs[device.id]?.communication_method || 'ssh'}
                              onChange={(e) => handleConfigChange(device.id, 'communication_method', e.target.value)}
                              disabled={importing}
                            >
                              {/* FIXED: Show ALL available communication methods */}
                              <MenuItem value="ssh">SSH</MenuItem>
                              <MenuItem value="winrm">WinRM</MenuItem>
                              <MenuItem value="snmp">SNMP</MenuItem>
                              <MenuItem value="telnet">Telnet</MenuItem>
                              <MenuItem value="rest_api">REST API</MenuItem>
                              <MenuItem value="smtp">SMTP</MenuItem>
                              <MenuItem value="mysql">MySQL/MariaDB</MenuItem>
                              <MenuItem value="postgresql">PostgreSQL</MenuItem>
                              <MenuItem value="mssql">Microsoft SQL Server</MenuItem>
                              <MenuItem value="oracle">Oracle Database</MenuItem>
                              <MenuItem value="sqlite">SQLite</MenuItem>
                              <MenuItem value="mongodb">MongoDB</MenuItem>
                              <MenuItem value="redis">Redis</MenuItem>
                              <MenuItem value="elasticsearch">Elasticsearch</MenuItem>
                              {/* Include any additional suggested methods not in the standard list */}
                              {device.suggested_communication_methods?.filter(method => 
                                !['ssh', 'winrm', 'snmp', 'telnet', 'rest_api', 'smtp', 'mysql', 'postgresql', 'mssql', 'oracle', 'sqlite', 'mongodb', 'redis', 'elasticsearch'].includes(method)
                              ).map(method => (
                                <MenuItem key={method} value={method}>
                                  {method.toUpperCase()}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        </Grid>
                        <Grid item xs={12} md={4}>
                          <TextField
                            label="Username"
                            value={deviceConfigs[device.id]?.username || ''}
                            onChange={(e) => handleConfigChange(device.id, 'username', e.target.value)}
                            fullWidth
                            size="small"
                            disabled={importing}
                            required
                          />
                        </Grid>
                        <Grid item xs={12} md={4}>
                          <TextField
                            label="Password"
                            type="password"
                            value={deviceConfigs[device.id]?.password || ''}
                            onChange={(e) => handleConfigChange(device.id, 'password', e.target.value)}
                            fullWidth
                            size="small"
                            disabled={importing}
                          />
                        </Grid>
                      </Grid>
                    </AccordionDetails>
                  )}
                </Accordion>
              ))}
            </Box>
          </>
        )}
      </DialogContent>

      <DialogActions>
        <Button 
          onClick={onClose} 
          disabled={importing}
        >
          Cancel
        </Button>
        <Button
          onClick={handleImportSelected}
          variant="contained"
          disabled={importing || selectedDevices.size === 0}
          startIcon={importing ? <CircularProgress size={16} /> : null}
        >
          {importing ? 'Importing...' : `Import ${selectedDevices.size} Selected`}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DiscoveredDeviceSelectionModal;