/**
 * Simple Network Discovery Modal
 * Utilitarian modal for quick network discovery - no fluff, just the essentials
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControlLabel,
  Checkbox,
  Typography,
  Box,
  Chip,
  Alert,
  CircularProgress
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import discoveryService from '../../services/discoveryService';
import DiscoveredDeviceSelectionModal from './DiscoveredDeviceSelectionModal';

const SimpleNetworkDiscoveryModal = ({ open, onClose, onDiscoveryStarted }) => {
  const [formData, setFormData] = useState({
    network_ranges: '192.168.1.0/24',
    enable_snmp: false,
    enable_service_detection: true,
    timeout: 3.0,
    max_concurrent: 50
  });
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);
  const [showDeviceSelection, setShowDeviceSelection] = useState(false);
  const [discoveryStatus, setDiscoveryStatus] = useState(null);
  const [discoveryProgress, setDiscoveryProgress] = useState(0);
  const [devicesFound, setDevicesFound] = useState(0);
  const [discoveredDevices, setDiscoveredDevices] = useState([]);

  const portPresets = {
    basic: { name: 'Basic (22,80,443,3389)', ports: [22, 80, 443, 3389] },
    extended: { name: 'Extended (+21,23,25,53,110,143,993,995)', ports: [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 3389] },
    comprehensive: { name: 'Comprehensive (Top 100)', ports: [] } // Will use service's default
  };

  const [selectedPreset, setSelectedPreset] = useState('basic');

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const runInMemoryDiscovery = async (discoveryConfig) => {
    try {
      setRunning(true);
      setError(null);
      setDiscoveryStatus('running');
      setDiscoveryProgress(0);
      setDevicesFound(0);
      
      // Call the new in-memory discovery endpoint
      const result = await discoveryService.runInMemoryDiscovery(discoveryConfig);
      
      // Ensure result is an array
      const devices = Array.isArray(result) ? result : [];
      
      setDiscoveryProgress(100);
      setDevicesFound(devices.length);
      setDiscoveredDevices(devices);
      setRunning(false);
      
      if (devices.length > 0) {
        setShowDeviceSelection(true);
      } else {
        setError('Discovery completed but no devices were found.');
      }
      
    } catch (err) {
      console.error('Error running discovery:', err);
      setRunning(false);
      setError(`Discovery failed: ${err.message || 'Please try again.'}`);
    }
  };

  const handleDevicesImported = (result) => {
    setShowDeviceSelection(false);
    setRunning(false);
    onClose();
    
    // Show success message
    if (onDiscoveryStarted) {
      onDiscoveryStarted({
        ...result,
        message: `Import completed: ${result.imported_count} new targets, ${result.existing_count} existing targets`
      });
    }
  };

  const handleDeviceSelectionClose = () => {
    setShowDeviceSelection(false);
    setRunning(false);
    onClose();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    try {
      // Parse network ranges
      const ranges = formData.network_ranges
        .split(',')
        .map(r => r.trim())
        .filter(r => r);

      if (ranges.length === 0) {
        throw new Error('Please specify at least one network range');
      }

      // Create discovery config for in-memory discovery
      const discoveryConfig = {
        network_ranges: ranges,
        common_ports: portPresets[selectedPreset].ports,
        timeout: parseFloat(formData.timeout),
        max_concurrent: parseInt(formData.max_concurrent),
        enable_snmp: formData.enable_snmp,
        enable_service_detection: formData.enable_service_detection,
        enable_hostname_resolution: true
      };

      // Run in-memory discovery
      await runInMemoryDiscovery(discoveryConfig);
      
    } catch (err) {
      console.error('Discovery error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to start network discovery');
      setRunning(false);
    }
  };

  const handleClose = () => {
    if (!running) {
      // Reset discovery state and clear in-memory results
      setDiscoveryStatus(null);
      setDiscoveryProgress(0);
      setDevicesFound(0);
      setDiscoveredDevices([]);
      setError(null);
      onClose();
    }
  };

  return (
    <>
    <Dialog 
      open={open} 
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <SearchIcon />
          Discover Network
        </Box>
      </DialogTitle>
      
      <form onSubmit={handleSubmit}>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {running && discoveryStatus && (
            <Alert severity="info" sx={{ mb: 2 }}>
              <Box>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  Discovery Status: <strong>{discoveryStatus.toUpperCase()}</strong>
                </Typography>
                <Box display="flex" alignItems="center" gap={1} sx={{ mb: 1 }}>
                  <CircularProgress 
                    variant="determinate" 
                    value={discoveryProgress} 
                    size={20} 
                  />
                  <Typography variant="body2">
                    {Math.round(discoveryProgress)}% complete
                  </Typography>
                </Box>
                {devicesFound > 0 && (
                  <Typography variant="body2" color="success.main">
                    {devicesFound} device{devicesFound !== 1 ? 's' : ''} found so far
                  </Typography>
                )}
              </Box>
            </Alert>
          )}

          <TextField
            name="network_ranges"
            label="Network Ranges"
            value={formData.network_ranges}
            onChange={handleInputChange}
            fullWidth
            margin="normal"
            placeholder="192.168.1.0/24, 10.0.0.0/16"
            helperText="Comma-separated CIDR ranges or IP addresses"
            disabled={running}
            required
          />

          <Box sx={{ mt: 2, mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Port Scan Preset:
            </Typography>
            <Box display="flex" gap={1} flexWrap="wrap">
              {Object.entries(portPresets).map(([key, preset]) => (
                <Chip
                  key={key}
                  label={preset.name}
                  variant={selectedPreset === key ? "filled" : "outlined"}
                  color={selectedPreset === key ? "primary" : "default"}
                  onClick={() => setSelectedPreset(key)}
                  disabled={running}
                />
              ))}
            </Box>
          </Box>

          <Box display="flex" gap={2} sx={{ mt: 2 }}>
            <TextField
              name="timeout"
              label="Timeout (sec)"
              type="number"
              value={formData.timeout}
              onChange={handleInputChange}
              inputProps={{ min: 1, max: 30, step: 0.5 }}
              disabled={running}
              size="small"
              sx={{ width: 120 }}
            />
            <TextField
              name="max_concurrent"
              label="Max Concurrent"
              type="number"
              value={formData.max_concurrent}
              onChange={handleInputChange}
              inputProps={{ min: 1, max: 200 }}
              disabled={running}
              size="small"
              sx={{ width: 140 }}
            />
          </Box>

          <Box sx={{ mt: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  name="enable_snmp"
                  checked={formData.enable_snmp}
                  onChange={handleInputChange}
                  disabled={running}
                />
              }
              label="Enable SNMP discovery"
            />
            <FormControlLabel
              control={
                <Checkbox
                  name="enable_service_detection"
                  checked={formData.enable_service_detection}
                  onChange={handleInputChange}
                  disabled={running}
                />
              }
              label="Enable service detection"
            />
          </Box>
        </DialogContent>

        <DialogActions>
          <Button 
            onClick={handleClose} 
            disabled={running}
          >
            Cancel
          </Button>

          <Button
            type="submit"
            variant="contained"
            disabled={running}
            startIcon={running ? <CircularProgress size={16} /> : <SearchIcon />}
          >
            {running 
              ? (discoveryStatus === 'running' 
                  ? `Discovering... ${Math.round(discoveryProgress)}%` 
                  : 'Starting Discovery...'
                ) 
              : 'Start Discovery'
            }
          </Button>
        </DialogActions>
      </form>
    </Dialog>
    
    {/* Device Selection Modal */}
    <DiscoveredDeviceSelectionModal
      open={showDeviceSelection}
      onClose={handleDeviceSelectionClose}
      onDevicesImported={handleDevicesImported}
      devices={discoveredDevices}
    />
  </>
  );
};

export default SimpleNetworkDiscoveryModal;