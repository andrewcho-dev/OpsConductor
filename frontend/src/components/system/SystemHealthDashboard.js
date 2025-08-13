import React, { useState, useEffect } from 'react';
import {
  Typography,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  Box,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Divider,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Computer as ComputerIcon,
  Storage as StorageIcon,
  Memory as MemoryIcon,
  Speed as SpeedIcon,
  Cloud as CloudIcon,
  AccountTree as DatabaseIcon,
  Api as ApiIcon,
  Widgets as ContainerIcon,
  Monitor as MonitorHeartIcon,
  RestartAlt as RestartIcon,
  Replay as ReloadIcon,
} from '@mui/icons-material';
import { useAlert } from '../layout/BottomStatusBar';
import { useAuth } from '../../contexts/AuthContext';

const SystemHealthDashboard = () => {
  const { addAlert } = useAlert();
  const { user } = useAuth();
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [restarting, setRestarting] = useState({});
  
  // Check if current user is admin
  const isAdmin = user?.role === 'administrator';

  useEffect(() => {
    fetchSystemHealth();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchSystemHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchSystemHealth = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      // Fetch both system health and monitoring metrics
      const [healthResponse, metricsResponse] = await Promise.all([
        fetch('/api/system-health/health', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }),
        fetch('/api/v1/monitoring/metrics', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })
      ]);

      if (!healthResponse.ok) {
        throw new Error(`Health API error! status: ${healthResponse.status}`);
      }

      const healthData = await healthResponse.json();
      let metricsData = null;
      
      if (metricsResponse.ok) {
        metricsData = await metricsResponse.json();
      }

      // Combine the data
      const combinedData = {
        ...healthData,
        metrics: metricsData
      };

      setHealthData(combinedData);
      setLastUpdated(new Date());
      
      // Check for critical issues
      const criticalIssues = healthData.services?.filter(s => s.status === 'critical').length || 0;
      if (criticalIssues > 0) {
        addAlert(`${criticalIssues} critical system issues detected`, 'error', 5000);
      }
    } catch (err) {
      console.error('Failed to fetch system health:', err);
      addAlert('Failed to load system health data', 'error', 5000);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'running':
      case 'online':
        return 'success';
      case 'warning':
      case 'degraded':
        return 'warning';
      case 'critical':
      case 'error':
      case 'offline':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'running':
      case 'online':
        return <CheckCircleIcon fontSize="small" />;
      case 'warning':
      case 'degraded':
        return <WarningIcon fontSize="small" />;
      case 'critical':
      case 'error':
      case 'offline':
        return <ErrorIcon fontSize="small" />;
      default:
        return <ComputerIcon fontSize="small" />;
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatUptime = (seconds) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const restartContainer = async (containerName) => {
    if (!isAdmin) {
      addAlert('Only administrators can restart containers', 'error', 5000);
      return;
    }

    setRestarting(prev => ({ ...prev, [containerName]: true }));
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/system-health/containers/${containerName}/restart`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (response.ok) {
        addAlert(`${containerName} restarted successfully`, 'success', 5000);
        // Refresh health data after a short delay
        setTimeout(fetchSystemHealth, 3000);
      } else {
        addAlert(`Failed to restart ${containerName}: ${data.detail}`, 'error', 5000);
      }
    } catch (err) {
      console.error('Failed to restart container:', err);
      addAlert(`Failed to restart ${containerName}`, 'error', 5000);
    } finally {
      setRestarting(prev => ({ ...prev, [containerName]: false }));
    }
  };

  const reloadService = async (serviceName) => {
    if (!isAdmin) {
      addAlert('Only administrators can reload services', 'error', 5000);
      return;
    }

    setRestarting(prev => ({ ...prev, [serviceName]: true }));
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/system-health/services/${serviceName}/reload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (response.ok) {
        addAlert(`${serviceName} reloaded successfully`, 'success', 5000);
        // Refresh health data after a short delay
        setTimeout(fetchSystemHealth, 3000);
      } else {
        addAlert(`Failed to reload ${serviceName}: ${data.detail}`, 'error', 5000);
      }
    } catch (err) {
      console.error('Failed to reload service:', err);
      addAlert(`Failed to reload ${serviceName}`, 'error', 5000);
    } finally {
      setRestarting(prev => ({ ...prev, [serviceName]: false }));
    }
  };

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="page-header">
          <Typography className="page-title">System Health & Status</Typography>
        </div>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
          <Typography variant="body2" sx={{ ml: 2 }}>
            Loading system health data...
          </Typography>
        </Box>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      {/* Page Header */}
      <div className="page-header">
        <Typography className="page-title">
          <MonitorHeartIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          System Health & Status
        </Typography>
        <div className="page-actions">
          <Tooltip title="Refresh system health">
            <IconButton 
              className="btn-icon" 
              onClick={fetchSystemHealth} 
              disabled={loading}
              size="small"
            >
              <RefreshIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </div>
      </div>

      {/* Last Updated */}
      {lastUpdated && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="caption" color="text.secondary">
            Last updated: {lastUpdated.toLocaleString()}
          </Typography>
        </Box>
      )}

      {/* System Overview Cards */}
      <div className="stats-grid">
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon primary">
              <ComputerIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{healthData?.overall_status || 'Unknown'}</h3>
              <p>System Status</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon warning">
              <SpeedIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{healthData?.metrics?.system?.cpu?.percent?.toFixed(1) || healthData?.system_metrics?.cpu_usage || 0}%</h3>
              <p>CPU Usage</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon info">
              <MemoryIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{healthData?.metrics?.system?.memory?.percent?.toFixed(1) || healthData?.system_metrics?.memory_usage || 0}%</h3>
              <p>Memory Usage</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon error">
              <StorageIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{healthData?.metrics?.system?.disk?.percent?.toFixed(1) || healthData?.system_metrics?.disk_usage || 0}%</h3>
              <p>Disk Usage</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon success">
              <DatabaseIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{healthData?.metrics?.application?.targets?.total || 0}</h3>
              <p>Total Targets</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon primary">
              <ApiIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{healthData?.metrics?.application?.jobs?.total || 0}</h3>
              <p>Total Jobs</p>
            </div>
          </div>
        </div>
      </div>

      <Grid container spacing={3}>
        {/* Container Health */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: 400 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <ContainerIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Container Health
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Container</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Uptime</TableCell>
                      <TableCell>Health</TableCell>
                      {isAdmin && <TableCell>Actions</TableCell>}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {healthData?.containers?.map((container, index) => (
                      <TableRow key={index}>
                        <TableCell>{container.name}</TableCell>
                        <TableCell>
                          <Chip 
                            label={container.status} 
                            color={getStatusColor(container.status)}
                            size="small"
                            icon={getStatusIcon(container.status)}
                          />
                        </TableCell>
                        <TableCell>{formatUptime(container.uptime || 0)}</TableCell>
                        <TableCell>
                          <Chip 
                            label={container.health || 'Unknown'} 
                            color={getStatusColor(container.health)}
                            size="small"
                          />
                        </TableCell>
                        {isAdmin && (
                          <TableCell>
                            <Tooltip title="Restart Container">
                              <IconButton
                                size="small"
                                onClick={() => restartContainer(container.name)}
                                disabled={restarting[container.name]}
                                color="primary"
                              >
                                {restarting[container.name] ? (
                                  <CircularProgress size={16} />
                                ) : (
                                  <RestartIcon fontSize="small" />
                                )}
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        )}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Service Health */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: 400 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <CloudIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Service Health
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Service</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Response Time</TableCell>
                      <TableCell>Last Check</TableCell>
                      {isAdmin && <TableCell>Actions</TableCell>}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {healthData?.services?.map((service, index) => {
                      // Map service names to reload endpoints
                      const getServiceKey = (serviceName) => {
                        if (serviceName.includes('Nginx')) return 'nginx';
                        if (serviceName.includes('Celery Workers')) return 'celery-workers';
                        if (serviceName.includes('Celery Scheduler')) return 'celery-scheduler';
                        if (serviceName.includes('FastAPI')) return 'backend';
                        if (serviceName.includes('React')) return 'frontend';
                        return null;
                      };
                      
                      const serviceKey = getServiceKey(service.name);
                      const canReload = serviceKey && ['nginx', 'celery-workers', 'celery-scheduler', 'backend', 'frontend'].includes(serviceKey);
                      
                      return (
                        <TableRow key={index}>
                          <TableCell>
                            <Box display="flex" alignItems="center">
                              {service.type === 'database' ? <DatabaseIcon fontSize="small" sx={{ mr: 1 }} /> : <ApiIcon fontSize="small" sx={{ mr: 1 }} />}
                              {service.name}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={service.status} 
                              color={getStatusColor(service.status)}
                              size="small"
                              icon={getStatusIcon(service.status)}
                            />
                          </TableCell>
                          <TableCell>{service.response_time || 'N/A'}</TableCell>
                          <TableCell>
                            <Typography variant="caption">
                              {service.last_check ? new Date(service.last_check).toLocaleString() : 'Never'}
                            </Typography>
                          </TableCell>
                          {isAdmin && (
                            <TableCell>
                              {canReload ? (
                                <Tooltip title={`Reload ${service.name}`}>
                                  <IconButton
                                    size="small"
                                    onClick={() => reloadService(serviceKey)}
                                    disabled={restarting[serviceKey]}
                                    color="secondary"
                                  >
                                    {restarting[serviceKey] ? (
                                      <CircularProgress size={16} />
                                    ) : (
                                      <ReloadIcon fontSize="small" />
                                    )}
                                  </IconButton>
                                </Tooltip>
                              ) : (
                                <Typography variant="caption" color="text.secondary">
                                  N/A
                                </Typography>
                              )}
                            </TableCell>
                          )}
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Performance Metrics */}
        {healthData?.metrics?.performance && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <SpeedIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Performance Metrics (24h)
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="primary">
                        {healthData.metrics.performance.avg_execution_time_seconds || 0}s
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Avg Execution Time
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="success.main">
                        {healthData.metrics.performance.success_rate_24h || 0}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Success Rate
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="info.main">
                        {healthData.metrics.performance.total_executions_24h || 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Executions
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="success.main">
                        {healthData.metrics.performance.successful_executions_24h || 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Successful Executions
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* System Alerts */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Alerts & Warnings
              </Typography>
              {healthData?.alerts?.length > 0 ? (
                <Box>
                  {healthData.alerts.map((alert, index) => (
                    <Alert 
                      key={index}
                      severity={alert.severity || 'info'}
                      sx={{ mb: 1 }}
                    >
                      <Typography variant="body2">
                        <strong>{alert.title}</strong>: {alert.message}
                      </Typography>
                      {alert.timestamp && (
                        <Typography variant="caption" color="text.secondary">
                          {new Date(alert.timestamp).toLocaleString()}
                        </Typography>
                      )}
                    </Alert>
                  ))}
                </Box>
              ) : (
                <Alert severity="success">
                  No system alerts. All systems are operating normally.
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </div>
  );
};

export default SystemHealthDashboard;