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
  Card,
  CardContent,
  LinearProgress,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  People as PeopleIcon,
  Security as SecurityIcon,
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
      <div className="dashboard-container">
        <div className="loading-container">
          <CircularProgress size={40} />
          <Typography variant="body2" sx={{ ml: 2, color: 'text.secondary' }}>
            Loading System Health...
          </Typography>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="page-header">
        <Typography className="page-title">
          System Health Dashboard
        </Typography>
        <div className="page-actions">
          {lastUpdated && (
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem', mr: 2 }}>
              Last updated: {lastUpdated.toLocaleTimeString()}
            </Typography>
          )}
          <Tooltip title="Refresh Data">
            <IconButton 
              onClick={fetchAllHealthData}
              disabled={refreshing}
              className="btn-icon"
              size="small"
            >
              <RefreshIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </div>
      </div>

      {healthData && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-card-content">
              <div className="stat-icon info">
                <SecurityIcon fontSize="small" />
              </div>
              <div className="stat-details">
                <h3>{healthData.uptime || 'Unknown'}</h3>
                <p>Uptime</p>
              </div>
            </div>
          </div>

          {systemData ? (
            <>
              <div className="stat-card">
                <div className="stat-card-content">
                  <div className={`stat-icon ${systemData.cpu?.usage_percent > 80 ? 'error' : systemData.cpu?.usage_percent > 60 ? 'warning' : 'success'}`}>
                    <RefreshIcon fontSize="small" />
                  </div>
                  <div className="stat-details">
                    <h3>{systemData.cpu?.usage_percent?.toFixed(1) || 0}%</h3>
                    <p>CPU Usage</p>
                  </div>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-card-content">
                  <div className={`stat-icon ${systemData.memory?.usage_percent > 85 ? 'error' : systemData.memory?.usage_percent > 70 ? 'warning' : 'success'}`}>
                    <PeopleIcon fontSize="small" />
                  </div>
                  <div className="stat-details">
                    <h3>{systemData.memory?.usage_percent?.toFixed(1) || 0}%</h3>
                    <p>Memory Usage</p>
                  </div>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-card-content">
                  <div className={`stat-icon ${systemData.disk?.usage_percent > 90 ? 'error' : systemData.disk?.usage_percent > 75 ? 'warning' : 'success'}`}>
                    <SecurityIcon fontSize="small" />
                  </div>
                  <div className="stat-details">
                    <h3>{systemData.disk?.usage_percent?.toFixed(1) || 0}%</h3>
                    <p>Disk Usage</p>
                  </div>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-card-content">
                  <div className="stat-icon success">
                    <PeopleIcon fontSize="small" />
                  </div>
                  <div className="stat-details">
                    <h3>
                      {healthData.health_checks?.docker_containers?.details?.summary?.running || 0}/
                      {healthData.health_checks?.docker_containers?.details?.summary?.total || 0}
                    </h3>
                    <p>Containers</p>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <>
              <div className="stat-card">
                <div className="stat-card-content">
                  <div className="stat-icon success">
                    <PeopleIcon fontSize="small" />
                  </div>
                  <div className="stat-details">
                    <h3>
                      {healthData.health_checks?.docker_containers?.details?.summary?.running || 0}/
                      {healthData.health_checks?.docker_containers?.details?.summary?.total || 0}
                    </h3>
                    <p>Containers</p>
                  </div>
                </div>
              </div>
            </>
          )}


        </div>
      )}

      {/* Docker Containers Section */}
      {healthData?.health_checks?.docker_containers && (
        <div className="main-content-card" style={{ marginBottom: '20px' }}>
          <div className="content-card-header">
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Docker Containers
            </Typography>
            <div style={{ display: 'flex', gap: '8px' }}>
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
            </div>
          </div>
          <div className="content-card-body">
            <Grid container spacing={2}>
              {healthData.health_checks.docker_containers.details?.containers && 
                Object.entries(healthData.health_checks.docker_containers.details.containers).map(([name, container]) => (
                  <Grid item xs={12} sm={4} md={3} lg={2} key={name}>
                    <Paper 
                      variant="outlined"
                      sx={{ 
                        p: 2, 
                        height: '100%',
                        display: 'flex',
                        flexDirection: 'column',
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
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.875rem' }}>
                          {name.replace('opsconductor-', '')}
                        </Typography>
                      </Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                        Status: <strong>{container.status}</strong>
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                        Health: <strong>{container.health_status}</strong>
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem', mb: 1 }}>
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
          </div>
        </div>
      )}

      {/* System Services Section */}
      {healthData?.health_checks?.nginx && (
        <div className="main-content-card" style={{ marginBottom: '20px' }}>
          <div className="content-card-header">
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              System Services
            </Typography>
          </div>
          <div className="content-card-body">
            <Grid container spacing={2}>
              {/* Nginx Status */}
              <Grid item xs={12} sm={4} md={3} lg={2}>
                <Paper variant="outlined" sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Box 
                      sx={{ 
                        width: 8, 
                        height: 8, 
                        borderRadius: '50%', 
                        backgroundColor: healthData.health_checks.nginx.healthy ? '#4caf50' : '#f44336',
                        mr: 1 
                      }} 
                    />
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                      Nginx Proxy
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                    Status: <strong>{healthData.health_checks.nginx.status || 'Unknown'}</strong>
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Container: <strong>{healthData.health_checks.nginx.details?.container_name || 'N/A'}</strong>
                  </Typography>
                </Paper>
              </Grid>

              {/* Celery Status */}
              {healthData.health_checks.celery && (
                <Grid item xs={12} sm={4} md={3} lg={2}>
                  <Paper variant="outlined" sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Box 
                        sx={{ 
                          width: 8, 
                          height: 8, 
                          borderRadius: '50%', 
                          backgroundColor: healthData.health_checks.celery.healthy ? '#4caf50' : '#f44336',
                          mr: 1 
                        }} 
                      />
                      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                        Task Queue
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                      Workers: <strong>{healthData.health_checks.celery.details?.workers_count || 0}</strong>
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Scheduler: <strong>{healthData.health_checks.celery.details?.scheduler_running ? 'Running' : 'Stopped'}</strong>
                    </Typography>
                  </Paper>
                </Grid>
              )}

              {/* Volumes Status */}
              {healthData.health_checks.volumes && (
                <Grid item xs={12} sm={4} md={3} lg={2}>
                  <Paper variant="outlined" sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Box 
                        sx={{ 
                          width: 8, 
                          height: 8, 
                          borderRadius: '50%', 
                          backgroundColor: healthData.health_checks.volumes.healthy ? '#4caf50' : '#f44336',
                          mr: 1 
                        }} 
                      />
                      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                        Storage
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                      Volumes: <strong>{healthData.health_checks.volumes.details?.volumes_count || 0}</strong>
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Disk: <strong>{healthData.health_checks.volumes.details?.disk_usage?.percent?.toFixed(1) || 0}%</strong>
                    </Typography>
                  </Paper>
                </Grid>
              )}
            </Grid>
          </div>
        </div>
      )}

      {/* System Utilities Section */}
      <div className="main-content-card" style={{ marginBottom: '20px' }}>
        <div className="content-card-header">
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            System Utilities
          </Typography>
        </div>
        <div className="content-card-body">
          <Grid container spacing={2}>
            {/* System Information */}
            <Grid item xs={12} sm={4} md={3} lg={2}>
              <Paper variant="outlined" sx={{ p: 2, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column' }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                  System Info
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  CPU: {healthData?.health_checks?.system?.details?.cpu_usage?.toFixed(1) || 0}%
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Memory: {healthData?.health_checks?.system?.details?.memory_usage?.toFixed(1) || 0}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Disk: {healthData?.health_checks?.system?.details?.disk_usage?.toFixed(1) || 0}%
                </Typography>
              </Paper>
            </Grid>

            {/* Database Info */}
            <Grid item xs={12} sm={4} md={3} lg={2}>
              <Paper variant="outlined" sx={{ p: 2, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column' }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                  Database
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Status: <strong>{healthData?.health_checks?.database?.status || 'Unknown'}</strong>
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Response: {healthData?.health_checks?.database?.response_time?.toFixed(1) || 0}ms
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Health: <strong>{healthData?.health_checks?.database?.healthy ? 'Good' : 'Issues'}</strong>
                </Typography>
              </Paper>
            </Grid>

            {/* Redis Info */}
            <Grid item xs={12} sm={4} md={3} lg={2}>
              <Paper variant="outlined" sx={{ p: 2, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column' }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                  Cache (Redis)
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Status: <strong>{healthData?.health_checks?.redis?.status || 'Unknown'}</strong>
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Response: {healthData?.health_checks?.redis?.response_time?.toFixed(1) || 0}ms
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Health: <strong>{healthData?.health_checks?.redis?.healthy ? 'Good' : 'Issues'}</strong>
                </Typography>
              </Paper>
            </Grid>

            {/* System Actions */}
            <Grid item xs={12} sm={4} md={3} lg={2}>
              <Paper variant="outlined" sx={{ p: 2, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                  Quick Actions
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mt: 'auto' }}>
                  <Button
                    size="small"
                    variant="outlined"
                    color="primary"
                    onClick={() => fetchAllHealthData()}
                    disabled={refreshing}
                  >
                    Refresh All
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    color="secondary"
                    onClick={() => handleServiceAction('nginx', 'restart')}
                  >
                    Restart Nginx
                  </Button>
                </Box>
              </Paper>
            </Grid>
          </Grid>
        </div>
      </div>

      <Grid container spacing={2}>
        {healthData?.health_checks && (
          <Grid item xs={12} md={2}>
            <div className="main-content-card" style={{ height: '100%' }}>
              <div className="content-card-header">
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                  Service Status
                </Typography>
                <Chip 
                  label={`${Object.keys(healthData.health_checks).length} Services`}
                  size="small"
                  className="chip-compact"
                  color="primary"
                  variant="outlined"
                />
              </div>
              <div className="content-card-body">
                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
                  {Object.entries(healthData.health_checks).map(([service, status]) => (
                    <Paper 
                      key={service}
                      variant="outlined"
                      sx={{ 
                        p: 1, 
                        display: 'flex', 
                        flexDirection: 'column',
                        alignItems: 'center',
                        textAlign: 'center'
                      }}
                    >
                      <SecurityIcon 
                        color={status.healthy ? 'success' : 'error'} 
                        fontSize="small" 
                        sx={{ mb: 0.5 }}
                      />
                      <Typography variant="caption" sx={{ fontWeight: 500, textTransform: 'capitalize', fontSize: '0.7rem' }}>
                        {service}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>
                        {status.status}
                      </Typography>
                      {status.response_time && (
                        <Typography variant="caption" sx={{ fontSize: '0.6rem', color: 'text.disabled' }}>
                          {status.response_time.toFixed(1)}ms
                        </Typography>
                      )}
                    </Paper>
                  ))}
                </Box>
              </div>
            </div>
          </Grid>
        )}

        <Grid item xs={12} md={2}>
          <div className="main-content-card" style={{ height: '100%' }}>
            <div className="content-card-header">
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                System Information
              </Typography>
            </div>
            <div className="content-card-body">
              {healthData ? (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>
                      Status
                    </Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                      {healthData.status || 'Unknown'}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>
                      Environment
                    </Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                      {healthData.environment || 'Unknown'}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>
                      Version
                    </Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                      {healthData.version || 'Unknown'}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>
                      Uptime
                    </Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                      {healthData.uptime || 'Unknown'}
                    </Typography>
                  </Box>
                  {healthData.timestamp && (
                    <Box>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>
                        Last Updated
                      </Typography>
                      <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                        {new Date(healthData.timestamp).toLocaleString()}
                      </Typography>
                    </Box>
                  )}
                  
                  {/* Test Progress Bar */}
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>
                      System Health
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={healthData.status === 'healthy' ? 100 : 50}
                      color={healthData.status === 'healthy' ? 'success' : 'warning'}
                      sx={{ height: 4, borderRadius: 2, mt: 0.5 }}
                    />
                  </Box>
                </Box>
              ) : (
                <Typography variant="body2">
                  No system information available
                </Typography>
              )}
            </div>
          </div>
        </Grid>

        {/* System Resources Card */}
        {systemData && (
          <Grid item xs={12} md={2}>
            <div className="main-content-card" style={{ height: '100%' }}>
              <div className="content-card-header">
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                  System Resources
                </Typography>
                <Chip 
                  label={systemData.status?.toUpperCase() || 'UNKNOWN'}
                  size="small"
                  className="chip-compact"
                  color="primary"
                />
              </div>
              <div className="content-card-body">
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {/* CPU */}
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" sx={{ fontWeight: 500, fontSize: '0.65rem' }}>
                        CPU
                      </Typography>
                      <Typography variant="caption" sx={{ fontWeight: 600, fontSize: '0.65rem' }}>
                        {systemData.cpu?.usage_percent?.toFixed(1) || 0}%
                      </Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={systemData.cpu?.usage_percent || 0}
                      color={systemData.cpu?.usage_percent > 80 ? 'error' : systemData.cpu?.usage_percent > 60 ? 'warning' : 'success'}
                      sx={{ height: 4, borderRadius: 2 }}
                    />
                  </Box>

                  {/* Memory */}
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" sx={{ fontWeight: 500, fontSize: '0.65rem' }}>
                        Memory
                      </Typography>
                      <Typography variant="caption" sx={{ fontWeight: 600, fontSize: '0.65rem' }}>
                        {systemData.memory?.usage_percent?.toFixed(1) || 0}%
                      </Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={systemData.memory?.usage_percent || 0}
                      color={systemData.memory?.usage_percent > 85 ? 'error' : systemData.memory?.usage_percent > 70 ? 'warning' : 'success'}
                      sx={{ height: 4, borderRadius: 2 }}
                    />
                  </Box>

                  {/* Disk */}
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" sx={{ fontWeight: 500, fontSize: '0.65rem' }}>
                        Disk
                      </Typography>
                      <Typography variant="caption" sx={{ fontWeight: 600, fontSize: '0.65rem' }}>
                        {systemData.disk?.usage_percent?.toFixed(1) || 0}%
                      </Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={systemData.disk?.usage_percent || 0}
                      color={systemData.disk?.usage_percent > 90 ? 'error' : systemData.disk?.usage_percent > 75 ? 'warning' : 'success'}
                      sx={{ height: 4, borderRadius: 2 }}
                    />
                  </Box>

                  {/* System Info */}
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>Platform</Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.7rem' }}>{systemData.platform || 'Unknown'}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>Processes</Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.7rem' }}>{systemData.processes || 0}</Typography>
                  </Box>
                </Box>
              </div>
            </div>
          </Grid>
        )}

        {/* Database Health Card */}
        {databaseData && (
          <Grid item xs={12} md={2}>
            <div className="main-content-card" style={{ height: '100%' }}>
              <div className="content-card-header">
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                  Database Health
                </Typography>
                <Chip 
                  label={databaseData.status?.toUpperCase() || 'UNKNOWN'}
                  size="small"
                  className="chip-compact"
                  color="primary"
                />
              </div>
              <div className="content-card-body">
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>Connection</Typography>
                    <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 0.5, fontSize: '0.7rem' }}>
                      <SecurityIcon 
                        color={databaseData.connection?.healthy ? 'success' : 'error'} 
                        fontSize="small" 
                        sx={{ fontSize: '12px' }}
                      />
                      {databaseData.connection?.status || 'Unknown'}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>Response Time</Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.7rem' }}>
                      {databaseData.connection?.response_time?.toFixed(1) || 0}ms
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>Pool Size</Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.7rem' }}>
                      {databaseData.connection_pool?.pool_size || 0}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>Active Connections</Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.7rem' }}>
                      {databaseData.statistics?.active_connections || 0}
                    </Typography>
                  </Box>
                </Box>
              </div>
            </div>
          </Grid>
        )}

        {/* Application Health Card */}
        {applicationData && (
          <Grid item xs={12} md={2}>
            <div className="main-content-card" style={{ height: '100%' }}>
              <div className="content-card-header">
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                  Application Health
                </Typography>
                <Chip 
                  label={applicationData.status?.toUpperCase() || 'UNKNOWN'}
                  size="small"
                  className="chip-compact"
                  color="primary"
                />
              </div>
              <div className="content-card-body">
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>Avg Response Time</Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.7rem' }}>
                      {applicationData.metrics?.avg_response_time?.toFixed(1) || 0}ms
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>Success Rate</Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.7rem' }}>
                      {applicationData.performance?.success_rate?.toFixed(1) || 0}%
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>Total Requests</Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.7rem' }}>
                      {applicationData.metrics?.total_requests?.toLocaleString() || 0}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>Error Rate</Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.7rem' }}>
                      {(applicationData.performance?.error_rate * 100)?.toFixed(2) || 0}%
                    </Typography>
                  </Box>

                  {/* Service Status */}
                  {applicationData.services && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem', fontWeight: 600 }}>
                        Services
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                        {Object.entries(applicationData.services).map(([service, status]) => (
                          <Chip
                            key={service}
                            label={service}
                            color={status === 'running' || status === 'connected' ? 'success' : 'error'}
                            variant="outlined"
                            size="small"
                            sx={{ fontSize: '0.6rem', height: '16px' }}
                          />
                        ))}
                      </Box>
                    </Box>
                  )}
                </Box>
              </div>
            </div>
          </Grid>
        )}

      </Grid>
    </div>
  );
};

export default SystemHealthDashboard;