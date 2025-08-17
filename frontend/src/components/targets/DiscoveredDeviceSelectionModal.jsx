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
  Typography,
  Box,
  Chip,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Computer as ComputerIcon,
  Router as RouterIcon,
  Storage as StorageIcon,
  DeviceHub as DeviceHubIcon
} from '@mui/icons-material';
import discoveryService from '../../services/discoveryService';

const DiscoveredDeviceSelectionModal = ({ open, onClose, onDevicesImported, devices = [] }) => {
  const [selectedDevices, setSelectedDevices] = useState(new Set());
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState(null);

  // Reset state when modal opens/closes
  useEffect(() => {
    if (!open) {
      setSelectedDevices(new Set());
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

  const handleSelectAll = (selected) => {
    if (selected && devices) {
      setSelectedDevices(new Set(devices.map(d => d.id || d.ip_address)));
    } else {
      setSelectedDevices(new Set());
    }
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
        const device = devices.find(d => (d.id || d.ip_address) === deviceId);
        
        return {
          // Include the full device data for in-memory devices
          device_data: {
            ip_address: device.ip_address,
            hostname: device.hostname,
            mac_address: device.mac_address,
            open_ports: device.ports || device.open_ports,
            services: device.services,
            snmp_info: device.snmp_info,
            device_type: device.device_type,
            os_type: device.os_type,
            confidence_score: device.confidence_score,
            suggested_communication_methods: device.suggested_communication_methods
          },
          target_name: device.hostname || `device-${device.ip_address.replace(/\./g, '-')}`,
          description: `Discovered device at ${device.ip_address}`,
          environment: 'development',
          communication_method: device.suggested_communication_methods?.[0] || 'ssh',
          username: 'admin',
          password: null,
          ssh_key: null,
          ssh_passphrase: null,
          port: null
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
      case 'network_device':
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

  return (
    <Dialog 
      open={open} 
      onClose={onClose}
      maxWidth="xl"
      fullWidth
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">
            Select Devices to Import as Targets
          </Typography>
          {devices && devices.length > 0 && (
            <Typography variant="body2" color="textSecondary">
              {devices.length} device{devices.length !== 1 ? 's' : ''} found
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

        {!devices || devices.length === 0 ? (
          <Alert severity="info">
            No devices found from discovery.
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

            {/* Device List - Table Format */}
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox">
                      <Checkbox
                        indeterminate={selectedDevices.size > 0 && selectedDevices.size < devices.length}
                        checked={devices.length > 0 && selectedDevices.size === devices.length}
                        onChange={(e) => handleSelectAll(e.target.checked)}
                        disabled={importing}
                      />
                    </TableCell>
                    <TableCell>IP Address</TableCell>
                    <TableCell>Hostname</TableCell>
                    <TableCell>Device Type</TableCell>
                    <TableCell>Network Range</TableCell>
                    <TableCell>Open Ports</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Discovered At</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {devices && devices.map((device, index) => {
                    const deviceId = device.id || device.ip_address;
                    const isSelected = selectedDevices.has(deviceId);
                    
                    return (
                      <TableRow 
                        key={`device-${deviceId}`}
                        hover
                        selected={isSelected}
                        sx={{
                          backgroundColor: isSelected ? 'action.selected' : 'inherit',
                          '&:hover': {
                            backgroundColor: isSelected ? 'action.selected' : 'action.hover'
                          }
                        }}
                      >
                        <TableCell padding="checkbox">
                          <Checkbox
                            checked={isSelected}
                            onChange={(e) => handleDeviceSelect(deviceId, e.target.checked)}
                            disabled={importing}
                          />
                        </TableCell>
                        <TableCell>
                          <Box display="flex" alignItems="center">
                            {getDeviceIcon(device.device_type)}
                            <Typography variant="body2" sx={{ ml: 1, fontWeight: isSelected ? 'bold' : 'normal' }}>
                              {device.ip_address}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {device.hostname || '-'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={device.device_type || 'unknown'} 
                            size="small" 
                            color="primary" 
                            variant="outlined" 
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="textSecondary">
                            {device.network_range || '-'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Box display="flex" gap={0.5} flexWrap="wrap">
                            {device.ports && device.ports.length > 0 ? (
                              device.ports.map(port => (
                                <Chip
                                  key={port}
                                  label={port}
                                  size="small"
                                  variant="outlined"
                                  color="secondary"
                                />
                              ))
                            ) : (
                              <Typography variant="body2" color="textSecondary">-</Typography>
                            )}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={device.status || 'discovered'} 
                            size="small" 
                            color="success" 
                            variant="outlined" 
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="textSecondary">
                            {device.discovered_at ? new Date(device.discovered_at).toLocaleString() : '-'}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
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