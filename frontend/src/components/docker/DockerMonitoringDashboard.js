import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Chip,
  IconButton,
  Button,
  Alert,
  CircularProgress,
  Tooltip,
  Paper,
  Switch,
  FormControlLabel,
  Snackbar,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  RestartAlt as RestartIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  AutorenewIcon,
} from '@mui/icons-material';

import ContainersList from './ContainersList';
import VolumesList from './VolumesList';
import NetworksList from './NetworksList';
import SystemOverview from './SystemOverview';
import dockerService from '../../services/dockerService';

const DockerMonitoringDashboard = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [systemInfo, setSystemInfo] = useState(null);
  const [containers, setContainers] = useState([]);
  const [volumes, setVolumes] = useState([]);
  const [networks, setNetworks] = useState([]);
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [dockerStatus, setDockerStatus] = useState(null);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });

  const tabs = [
    { label: 'Overview', value: 0 },
    { label: 'Containers', value: 1 },
    { label: 'Volumes', value: 2 },
    { label: 'Networks', value: 3 },
  ];

  const fetchAllData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // First check Docker status
      const status = await dockerService.getDockerStatus();
      setDockerStatus(status);
      
      if (status.status !== 'connected') {
        setError(`Docker connection issue: ${status.message}`);
        return;
      }

      const [systemData, containersData, volumesData, networksData] = await Promise.all([
        dockerService.getSystemInfo(),
        dockerService.getContainers(),
        dockerService.getVolumes(),
        dockerService.getNetworks(),
      ]);

      setSystemInfo(systemData);
      setContainers(containersData);
      setVolumes(volumesData);
      setNetworks(networksData);
      setLastRefresh(new Date());
      
      // Show success notification on first load
      if (!systemInfo) {
        showNotification('Docker environment loaded successfully', 'success');
      }
    } catch (err) {
      setError('Failed to fetch Docker data. Make sure the backend and Portainer are running.');
      console.error('Docker data fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const showNotification = (message, severity = 'info') => {
    setNotification({ open: true, message, severity });
  };

  useEffect(() => {
    fetchAllData();
    
    // Auto-refresh every 30 seconds if enabled
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchAllData, 30000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  const handleRefresh = () => {
    fetchAllData();
  };

  if (loading && !systemInfo) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading Docker environment...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button variant="contained" onClick={handleRefresh} startIcon={<RefreshIcon />}>
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 600 }}>
            Docker Environment
          </Typography>
          {dockerStatus && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
              <Chip 
                label={dockerStatus.status === 'connected' ? 'Connected' : 'Disconnected'} 
                color={dockerStatus.status === 'connected' ? 'success' : 'error'}
                size="small"
              />
              {dockerStatus.portainer_authenticated && (
                <Chip label="Portainer Ready" color="info" size="small" />
              )}
            </Box>
          )}
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                size="small"
              />
            }
            label="Auto-refresh"
          />
          <Typography variant="body2" color="text.secondary">
            Last updated: {lastRefresh.toLocaleTimeString()}
          </Typography>
          <Tooltip title="Refresh">
            <IconButton onClick={handleRefresh} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Quick Stats */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Containers
              </Typography>
              <Typography variant="h4">
                {containers.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {containers.filter(c => c.State === 'running').length} running
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Volumes
              </Typography>
              <Typography variant="h4">
                {volumes.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Networks
              </Typography>
              <Typography variant="h4">
                {networks.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Images
              </Typography>
              <Typography variant="h4">
                {systemInfo?.Images || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={currentTab}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
        >
          {tabs.map((tab) => (
            <Tab key={tab.value} label={tab.label} />
          ))}
        </Tabs>
      </Paper>

      {/* Tab Content */}
      <Box>
        {currentTab === 0 && (
          <SystemOverview 
            systemInfo={systemInfo} 
            containers={containers}
            volumes={volumes}
            networks={networks}
          />
        )}
        {currentTab === 1 && (
          <ContainersList 
            containers={containers} 
            onRefresh={fetchAllData}
            loading={loading}
            onNotification={showNotification}
          />
        )}
        {currentTab === 2 && (
          <VolumesList 
            volumes={volumes} 
            onRefresh={fetchAllData}
          />
        )}
        {currentTab === 3 && (
          <NetworksList 
            networks={networks} 
            onRefresh={fetchAllData}
          />
        )}
      </Box>

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={4000}
        onClose={() => setNotification({ ...notification, open: false })}
        message={notification.message}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      />
    </Box>
  );
};

export default DockerMonitoringDashboard;