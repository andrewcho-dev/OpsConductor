import React, { useState, useEffect } from 'react';
import {
  Typography,
  Button,
  IconButton,
  CircularProgress,
  Tooltip,
  Chip,
  Box,
  Paper,
  Grid,
  LinearProgress,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  People as PeopleIcon,
  Security as SecurityIcon,
  Computer as ComputerIcon,
  Storage as StorageIcon,
  Memory as MemoryIcon,
} from '@mui/icons-material';
import { useAlert } from '../layout/BottomStatusBar';
import '../../styles/dashboard.css';

const SystemHealthDashboard = () => {
  const { addAlert } = useAlert();
  const [healthData, setHealthData] = useState(null);
  const [systemData, setSystemData] = useState(null);
  const [databaseData, setDatabaseData] = useState(null);
  const [applicationData, setApplicationData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    fetchAllHealthData();
    const interval = setInterval(fetchAllHealthData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAllHealthData = async () => {
    if (!refreshing) setRefreshing(true);
    
    try {
      const [overallRes, systemRes, databaseRes, applicationRes] = await Promise.all([
        fetch('/api/v2/health/', { 
          headers: { 'Content-Type': 'application/json' }
        }),
        fetch('/api/v2/health/system', { 
          headers: { 'Content-Type': 'application/json' }
        }),
        fetch('/api/v2/health/database', { 
          headers: { 'Content-Type': 'application/json' }
        }),
        fetch('/api/v2/health/application', { 
          headers: { 'Content-Type': 'application/json' }
        })
      ]);

      if (overallRes.ok) {
        const data = await overallRes.json();
        setHealthData(data);
      }

      if (systemRes.ok) {
        const data = await systemRes.json();
        setSystemData(data);
      }

      if (databaseRes.ok) {
        const data = await databaseRes.json();
        setDatabaseData(data);
      }

      if (applicationRes.ok) {
        const data = await applicationRes.json();
        setApplicationData(data);
      }

      setLastUpdated(new Date());
      
    } catch (error) {
      console.error('Failed to fetch health data:', error);
      addAlert('Failed to fetch system health data', 'error', 5000);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleServiceAction = async (serviceName, action) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        addAlert('Authentication required', 'error', 5000);
        return;
      }

      const response = await fetch(`/api/v2/health/services/${serviceName}/${action}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        addAlert(result.message, 'success', 5000);
        
        // Refresh health data after action
        setTimeout(() => {
          fetchAllHealthData();
        }, 2000);
      } else {
        const error = await response.json();
        addAlert(error.detail || `Failed to ${action} service`, 'error', 5000);
      }
    } catch (error) {
      console.error(`Service ${action} error:`, error);
      addAlert(`Failed to ${action} service: ${error.message}`, 'error', 5000);
    }
  };

  if (loading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '400px',
        flexDirection: 'column',
        gap: 2
      }}>
        <CircularProgress size={40} />
        <Typography variant="body2" color="text.secondary">
          Loading System Health...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        mb: 3 
      }}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          System Health Dashboard
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {lastUpdated && (
            <Typography variant="caption" color="text.secondary">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </Typography>
          )}
          <Tooltip title="Refresh Data">
            <IconButton 
              onClick={fetchAllHealthData}
              disabled={refreshing}
              size="small"
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* System Overview Cards */}
      {healthData && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {/* Uptime */}
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <SecurityIcon color="primary" sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {healthData.uptime || 'Unknown'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                System Uptime
              </Typography>
            </Paper>
          </Grid>

          {/* CPU Usage */}
          {systemData && (
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <ComputerIcon 
                  color={systemData.cpu?.usage_percent > 80 ? 'error' : systemData.cpu?.usage_percent > 60 ? 'warning' : 'success'} 
                  sx={{ fontSize: 40, mb: 1 }} 
                />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {systemData.cpu?.usage_percent?.toFixed(1) || 0}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  CPU Usage
                </Typography>
              </Paper>
            </Grid>
          )}

          {/* Memory Usage */}
          {systemData && (
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <MemoryIcon 
                  color={systemData.memory?.usage_percent > 85 ? 'error' : systemData.memory?.usage_percent > 70 ? 'warning' : 'success'} 
                  sx={{ fontSize: 40, mb: 1 }} 
                />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {systemData.memory?.usage_percent?.toFixed(1) || 0}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Memory Usage
                </Typography>
              </Paper>
            </Grid>
          )}

          {/* Containers */}
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <StorageIcon color="success" sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {healthData.health_checks?.docker_containers?.details?.summary?.running || 0}/
                {healthData.health_checks?.docker_containers?.details?.summary?.total || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Containers Running
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Docker Containers */}
      {healthData?.health_checks?.docker_containers && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Docker Containers
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Chip 
                label={`${healthData.health_checks.docker_containers.details?.summary?.running || 0} Running`}
                size="small"
                color="success"
                variant="outlined"
              />
              <Chip 
                label={`${healthData.health_checks.docker_containers.details?.summary?.total || 0} Total`}
                size="small"
                color="primary"
                variant="outlined"
              />
            </Box>
          </Box>
          
          <Grid container spacing={2}>
            {healthData.health_checks.docker_containers.details?.containers && 
              Object.entries(healthData.health_checks.docker_containers.details.containers).map(([name, container]) => (
                <Grid item xs={12} sm={6} md={4} lg={3} key={name}>
                  <Paper 
                    variant="outlined"
                    sx={{ 
                      p: 2, 
                      height: '100%',
                      border: container.healthy ? '1px solid #4caf50' : '1px solid #f44336'
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Box 
                        sx={{ 
                          width: 8, 
                          height: 8, 
                          borderRadius: '50%', 
                          backgroundColor: container.healthy ? '#4caf50' : '#f44336',
                          mr: 1 
                        }} 
                      />
                      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                        {name.replace('opsconductor-', '')}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                      Status: <strong>{container.status}</strong>
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                      Health: <strong>{container.health_status}</strong>
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                      {container.image}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <Button
                        size="small"
                        variant="outlined"
                        color="primary"
                        sx={{ fontSize: '0.7rem', minWidth: 'auto', px: 1 }}
                        onClick={() => handleServiceAction(name, 'restart')}
                      >
                        Restart
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        color="warning"
                        sx={{ fontSize: '0.7rem', minWidth: 'auto', px: 1 }}
                        onClick={() => handleServiceAction(name, 'stop')}
                      >
                        Stop
                      </Button>
                    </Box>
                  </Paper>
                </Grid>
              ))
            }
          </Grid>
        </Paper>
      )}

      {/* System Resources */}
      <Grid container spacing={3}>
        {/* System Information */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
              System Information
            </Typography>
            {healthData ? (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Status
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {healthData.status || 'Unknown'}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Environment
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {healthData.environment || 'Unknown'}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Version
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {healthData.version || 'Unknown'}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    System Health
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={healthData.status === 'healthy' ? 100 : 50}
                    color={healthData.status === 'healthy' ? 'success' : 'warning'}
                    sx={{ height: 8, borderRadius: 4, mt: 0.5 }}
                  />
                </Box>
              </Box>
            ) : (
              <Typography variant="body2">
                No system information available
              </Typography>
            )}
          </Paper>
        </Grid>

        {/* System Resources */}
        {systemData && (
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                System Resources
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {/* CPU */}
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      CPU Usage
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {systemData.cpu?.usage_percent?.toFixed(1) || 0}%
                    </Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={systemData.cpu?.usage_percent || 0}
                    color={systemData.cpu?.usage_percent > 80 ? 'error' : systemData.cpu?.usage_percent > 60 ? 'warning' : 'success'}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>

                {/* Memory */}
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      Memory Usage
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {systemData.memory?.usage_percent?.toFixed(1) || 0}%
                    </Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={systemData.memory?.usage_percent || 0}
                    color={systemData.memory?.usage_percent > 85 ? 'error' : systemData.memory?.usage_percent > 70 ? 'warning' : 'success'}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>

                {/* Disk */}
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      Disk Usage
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {systemData.disk?.usage_percent?.toFixed(1) || 0}%
                    </Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={systemData.disk?.usage_percent || 0}
                    color={systemData.disk?.usage_percent > 90 ? 'error' : systemData.disk?.usage_percent > 75 ? 'warning' : 'success'}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>
              </Box>
            </Paper>
          </Grid>
        )}

        {/* Service Status */}
        {healthData?.health_checks && (
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Service Status
              </Typography>
              <Grid container spacing={1}>
                {Object.entries(healthData.health_checks).map(([service, status]) => (
                  <Grid item xs={6} key={service}>
                    <Paper 
                      variant="outlined"
                      sx={{ 
                        p: 1, 
                        display: 'flex', 
                        flexDirection: 'column',
                        alignItems: 'center',
                        textAlign: 'center',
                        minHeight: '80px'
                      }}
                    >
                      <SecurityIcon 
                        color={status.healthy ? 'success' : 'error'} 
                        fontSize="small" 
                        sx={{ mb: 0.5 }}
                      />
                      <Typography variant="caption" sx={{ fontWeight: 500, textTransform: 'capitalize' }}>
                        {service}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {status.status}
                      </Typography>
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            </Paper>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default SystemHealthDashboard;