import React, { useState, useEffect } from 'react';
import { formatLocalDateTime } from '../../utils/timeUtils';
import {
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  AlertTitle,
  Box,
  Switch,
  FormControlLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip,
  CircularProgress,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Healing as HealingIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Computer as ComputerIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
  RestartAlt as RestartIcon,
  Build as BuildIcon,
  CleaningServices as CleanIcon,
  Update as UpdateIcon,
  ExpandMore as ExpandMoreIcon,
  Visibility as ViewIcon,
  Info as InfoIcon,
  Monitor as MonitorIcon,
} from '@mui/icons-material';
import { useAlert } from '../layout/BottomStatusBar';
import axios from 'axios';

const SystemManagement = () => {
  const { addAlert } = useAlert();
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoHealEnabled, setAutoHealEnabled] = useState(true);
  const [actionLoading, setActionLoading] = useState({});
  const [logsDialog, setLogsDialog] = useState({ open: false, service: '', logs: [] });
  const [refreshInterval, setRefreshInterval] = useState(null);

  const fetchSystemStatus = async () => {
    try {
      // Try to fetch data from Portainer API first
      try {
        const [containersResponse, systemResponse] = await Promise.all([
          axios.get('/portainer/api/endpoints/1/docker/containers/json?all=true'),
          axios.get('/portainer/api/endpoints/1/docker/system/info')
        ]);

        // Transform Portainer data to match our expected format
        const containers = containersResponse.data;
        const systemInfo = systemResponse.data;
        
        const services = containers.map(container => ({
          service: container.Names[0].replace('/', ''),
          status: container.State === 'running' ? 'running' : 'stopped',
          health: container.State === 'running' ? 'healthy' : 'unhealthy',
          uptime: container.State === 'running' ? Math.floor((Date.now() - new Date(container.Created * 1000)) / 1000) : null,
          cpu_usage: 0,
          memory_usage: 0,
          last_check: new Date().toISOString(),
          issues: container.State !== 'running' ? [`Container is ${container.State}`] : []
        }));

        const overallHealth = services.every(s => s.health === 'healthy') ? 'healthy' : 
                             services.some(s => s.health === 'unhealthy') ? 'critical' : 'degraded';

        const transformedData = {
          overall_health: overallHealth,
          services: services,
          system_metrics: {
            cpu_usage: 0,
            memory_total: systemInfo.MemTotal || 0,
            memory_used: (systemInfo.MemTotal - systemInfo.MemAvailable) || 0,
            memory_percent: systemInfo.MemTotal ? ((systemInfo.MemTotal - systemInfo.MemAvailable) / systemInfo.MemTotal * 100) : 0,
            disk_total: 0,
            disk_used: 0,
            disk_percent: 0,
            uptime: systemInfo.SystemTime ? Math.floor((Date.now() - new Date(systemInfo.SystemTime)) / 1000) : 0
          },
          recommendations: services.filter(s => s.health !== 'healthy').map(s => `Check ${s.service}: ${s.issues.join(', ')}`),
          last_updated: new Date().toISOString()
        };

        setSystemStatus(transformedData);
        setLoading(false);
        return;
      } catch (portainerError) {
        console.log('Portainer API not available, using fallback data');
      }

      // Fallback: Show basic system information
      const fallbackData = {
        overall_health: 'unknown',
        services: [
          { service: 'opsconductor-backend', status: 'running', health: 'healthy', uptime: 3600, cpu_usage: 0, memory_usage: 0, last_check: new Date().toISOString(), issues: [] },
          { service: 'opsconductor-frontend', status: 'running', health: 'healthy', uptime: 3600, cpu_usage: 0, memory_usage: 0, last_check: new Date().toISOString(), issues: [] },
          { service: 'opsconductor-postgres', status: 'running', health: 'healthy', uptime: 3600, cpu_usage: 0, memory_usage: 0, last_check: new Date().toISOString(), issues: [] },
          { service: 'opsconductor-redis', status: 'running', health: 'healthy', uptime: 3600, cpu_usage: 0, memory_usage: 0, last_check: new Date().toISOString(), issues: [] },
          { service: 'opsconductor-nginx', status: 'running', health: 'healthy', uptime: 3600, cpu_usage: 0, memory_usage: 0, last_check: new Date().toISOString(), issues: [] },
          { service: 'opsconductor-portainer', status: 'running', health: 'healthy', uptime: 3600, cpu_usage: 0, memory_usage: 0, last_check: new Date().toISOString(), issues: [] }
        ],
        system_metrics: {
          cpu_usage: 15.2,
          memory_total: 8589934592, // 8GB
          memory_used: 2684354560,  // ~2.5GB
          memory_percent: 31.25,
          disk_total: 107374182400, // 100GB
          disk_used: 21474836480,   // 20GB
          disk_percent: 20.0,
          uptime: 86400 // 1 day
        },
        recommendations: [
          'Initialize Portainer at /portainer/ for detailed container monitoring',
          'System monitoring is using fallback data - configure Portainer for real-time metrics'
        ],
        last_updated: new Date().toISOString()
      };

      setSystemStatus(fallbackData);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch system status:', error);
      addAlert('Failed to fetch system status', 'error');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemStatus();
    
    // Set up auto-refresh every 30 seconds
    const interval = setInterval(fetchSystemStatus, 30000);
    setRefreshInterval(interval);
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, []);

  const handleHealService = async (serviceName) => {
    setActionLoading(prev => ({ ...prev, [serviceName]: true }));
    try {
      // Find the container ID first
      const containersResponse = await axios.get('/portainer/api/endpoints/1/docker/containers/json?all=true');
      const container = containersResponse.data.find(c => c.Names[0].replace('/', '') === serviceName);
      
      if (container) {
        // Restart the container using Portainer API
        await axios.post(`/portainer/api/endpoints/1/docker/containers/${container.Id}/restart`);
        addAlert(`Container ${serviceName} restarted successfully`, 'success');
        setTimeout(fetchSystemStatus, 3000); // Refresh after 3 seconds
      } else {
        addAlert(`Container ${serviceName} not found`, 'error');
      }
    } catch (error) {
      addAlert(`Failed to restart ${serviceName}`, 'error');
    } finally {
      setActionLoading(prev => ({ ...prev, [serviceName]: false }));
    }
  };

  const handleSystemAction = async (action, target = null) => {
    const actionKey = `${action}_${target || 'system'}`;
    setActionLoading(prev => ({ ...prev, [actionKey]: true }));
    try {
      await axios.post('/api/system-management/action', {
        action,
        target,
      });
      addAlert(`${action} initiated successfully`, 'success');
      if (action === 'restart_all') {
        setTimeout(fetchSystemStatus, 10000); // Wait longer for full restart
      } else {
        setTimeout(fetchSystemStatus, 3000);
      }
    } catch (error) {
      addAlert(`Failed to execute ${action}`, 'error');
    } finally {
      setActionLoading(prev => ({ ...prev, [actionKey]: false }));
    }
  };

  const handleToggleAutoHeal = async (enabled) => {
    try {
      await axios.post('/api/system-management/auto-heal/toggle', null, {
        params: { enabled }
      });
      setAutoHealEnabled(enabled);
      addAlert(`Auto-healing ${enabled ? 'enabled' : 'disabled'}`, 'success');
    } catch (error) {
      addAlert('Failed to toggle auto-healing', 'error');
    }
  };

  const handleViewLogs = async (serviceName) => {
    try {
      // Find the container ID first
      const containersResponse = await axios.get('/portainer/api/endpoints/1/docker/containers/json?all=true');
      const container = containersResponse.data.find(c => c.Names[0].replace('/', '') === serviceName);
      
      if (container) {
        // Get logs using Portainer API
        const response = await axios.get(`/portainer/api/endpoints/1/docker/containers/${container.Id}/logs?stdout=true&stderr=true&tail=100`);
        const logs = response.data.split('\n').filter(line => line.trim());
        
        setLogsDialog({
          open: true,
          service: serviceName,
          logs: logs
        });
      } else {
        addAlert(`Container ${serviceName} not found`, 'error');
      }
    } catch (error) {
      addAlert(`Failed to fetch logs for ${serviceName}`, 'error');
    }
  };

  const getHealthColor = (health) => {
    switch (health) {
      case 'healthy': return 'success';
      case 'degraded': return 'warning';
      case 'unhealthy': return 'error';
      case 'critical': return 'error';
      default: return 'default';
    }
  };

  const getHealthIcon = (health) => {
    switch (health) {
      case 'healthy': return <CheckCircleIcon color="success" />;
      case 'degraded': return <WarningIcon color="warning" />;
      case 'unhealthy': return <ErrorIcon color="error" />;
      case 'critical': return <ErrorIcon color="error" />;
      default: return <ComputerIcon />;
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
    return `${days}d ${hours}h ${minutes}m`;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <div className="dashboard-container">
      {/* Header */}
      <div className="page-header">
        <Typography className="page-title">
          System Management
        </Typography>
        <div className="page-actions">
          <FormControlLabel
            control={
              <Switch
                checked={autoHealEnabled}
                onChange={(e) => handleToggleAutoHeal(e.target.checked)}
                color="primary"
              />
            }
            label="Auto-Healing"
          />
          <Tooltip title={loading ? "Loading..." : "Refresh Status"}>
            <span>
              <IconButton onClick={fetchSystemStatus} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </span>
          </Tooltip>
        </div>
      </div>

      {/* Portainer Setup Banner */}
      {systemStatus?.overall_health === 'unknown' && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12}>
            <Card sx={{ backgroundColor: '#e3f2fd', border: '1px solid #2196f3' }}>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <InfoIcon color="primary" sx={{ mr: 2 }} />
                  <Box flex={1}>
                    <Typography variant="h6" color="primary">
                      Container Monitoring Setup Required
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 1, mb: 2 }}>
                      To get real-time container metrics and management capabilities, please initialize Portainer.
                      This will enable detailed monitoring, logs, and container management features.
                    </Typography>
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={<MonitorIcon />}
                      onClick={() => window.open('/portainer/', '_blank')}
                      sx={{ mr: 2 }}
                    >
                      Open Portainer Setup
                    </Button>
                    <Button
                      variant="outlined"
                      onClick={fetchSystemStatus}
                      startIcon={<RefreshIcon />}
                    >
                      Refresh After Setup
                    </Button>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Overall Health Status */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box display="flex" alignItems="center">
                  {getHealthIcon(systemStatus?.overall_health)}
                  <Box ml={2}>
                    <Typography variant="h6">
                      System Health: {systemStatus?.overall_health?.toUpperCase()}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Last updated: {formatLocalDateTime(systemStatus?.last_updated)}
                    </Typography>
                  </Box>
                </Box>
                <Chip
                  label={systemStatus?.overall_health}
                  color={getHealthColor(systemStatus?.overall_health)}
                  variant="outlined"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* System Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <SpeedIcon color="primary" />
                <Box ml={2} flex={1}>
                  <Typography variant="h6">
                    {systemStatus?.system_metrics?.cpu_usage?.toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="textSecondary">CPU Usage</Typography>
                  <LinearProgress
                    variant="determinate"
                    value={systemStatus?.system_metrics?.cpu_usage || 0}
                    sx={{ mt: 1 }}
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <MemoryIcon color="primary" />
                <Box ml={2} flex={1}>
                  <Typography variant="h6">
                    {systemStatus?.system_metrics?.memory_percent?.toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="textSecondary">Memory Usage</Typography>
                  <LinearProgress
                    variant="determinate"
                    value={systemStatus?.system_metrics?.memory_percent || 0}
                    sx={{ mt: 1 }}
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <StorageIcon color="primary" />
                <Box ml={2} flex={1}>
                  <Typography variant="h6">
                    {systemStatus?.system_metrics?.disk_percent?.toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="textSecondary">Disk Usage</Typography>
                  <LinearProgress
                    variant="determinate"
                    value={systemStatus?.system_metrics?.disk_percent || 0}
                    sx={{ mt: 1 }}
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <ComputerIcon color="primary" />
                <Box ml={2} flex={1}>
                  <Typography variant="h6">
                    {formatUptime(systemStatus?.system_metrics?.uptime || 0)}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">System Uptime</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alerts and Recommendations */}
      {systemStatus?.recommendations?.length > 0 && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12}>
            <Alert severity="warning">
              <AlertTitle>System Recommendations</AlertTitle>
              <ul style={{ margin: 0, paddingLeft: '20px' }}>
                {systemStatus.recommendations.map((rec, index) => (
                  <li key={index}>{rec}</li>
                ))}
              </ul>
            </Alert>
          </Grid>
        </Grid>
      )}

      {/* Quick Actions */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Quick Actions</Typography>
              <Box display="flex" gap={2} flexWrap="wrap">
                <Button
                  variant="contained"
                  startIcon={<RestartIcon />}
                  onClick={() => handleSystemAction('restart_all')}
                  disabled={actionLoading['restart_all_system']}
                  color="warning"
                >
                  {actionLoading['restart_all_system'] ? 'Restarting...' : 'Restart All Services'}
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<RestartIcon />}
                  onClick={() => handleSystemAction('restart_frontend')}
                  disabled={actionLoading['restart_frontend_system']}
                >
                  {actionLoading['restart_frontend_system'] ? 'Restarting...' : 'Restart Frontend'}
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<RestartIcon />}
                  onClick={() => handleSystemAction('restart_backend')}
                  disabled={actionLoading['restart_backend_system']}
                >
                  {actionLoading['restart_backend_system'] ? 'Restarting...' : 'Restart Backend'}
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<CleanIcon />}
                  onClick={() => handleSystemAction('cleanup_logs')}
                  disabled={actionLoading['cleanup_logs_system']}
                >
                  {actionLoading['cleanup_logs_system'] ? 'Cleaning...' : 'Cleanup Logs'}
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<UpdateIcon />}
                  onClick={() => handleSystemAction('update_dependencies')}
                  disabled={actionLoading['update_dependencies_system']}
                >
                  {actionLoading['update_dependencies_system'] ? 'Updating...' : 'Update Dependencies'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Services Status */}
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Services Status</Typography>
              <TableContainer 
                component={Paper} 
                variant="outlined"
                sx={{ 
                  maxHeight: '100%', // Dynamic height - stops 70px above footer
                  overflow: 'auto'
                }}
              >
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Service</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Health</TableCell>
                      <TableCell>CPU</TableCell>
                      <TableCell>Memory</TableCell>
                      <TableCell>Uptime</TableCell>
                      <TableCell>Issues</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {systemStatus?.services?.map((service) => (
                      <TableRow key={service.service}>
                        <TableCell>
                          <Box display="flex" alignItems="center">
                            {getHealthIcon(service.health)}
                            <Typography variant="body2" sx={{ ml: 1 }}>
                              {service.service}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={service.status}
                            size="small"
                            color={service.status === 'running' ? 'success' : 'error'}
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={service.health}
                            size="small"
                            color={getHealthColor(service.health)}
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          {service.cpu_usage ? `${service.cpu_usage.toFixed(1)}%` : 'N/A'}
                        </TableCell>
                        <TableCell>
                          {service.memory_usage ? `${service.memory_usage.toFixed(1)}%` : 'N/A'}
                        </TableCell>
                        <TableCell>
                          {service.uptime || 'N/A'}
                        </TableCell>
                        <TableCell>
                          {service.issues.length > 0 ? (
                            <Tooltip title={service.issues.join(', ')}>
                              <Chip
                                label={`${service.issues.length} issue${service.issues.length > 1 ? 's' : ''}`}
                                size="small"
                                color="error"
                                variant="outlined"
                              />
                            </Tooltip>
                          ) : (
                            <Chip label="None" size="small" color="success" variant="outlined" />
                          )}
                        </TableCell>
                        <TableCell>
                          <Box display="flex" gap={1}>
                            {service.health !== 'healthy' && (
                              <Tooltip title="Heal Service">
                                <IconButton
                                  size="small"
                                  onClick={() => handleHealService(service.service)}
                                  disabled={actionLoading[service.service]}
                                >
                                  {actionLoading[service.service] ? (
                                    <CircularProgress size={16} />
                                  ) : (
                                    <HealingIcon />
                                  )}
                                </IconButton>
                              </Tooltip>
                            )}
                            <Tooltip title="View Logs">
                              <IconButton
                                size="small"
                                onClick={() => handleViewLogs(service.service)}
                              >
                                <ViewIcon />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Logs Dialog */}
      <Dialog
        open={logsDialog.open}
        onClose={() => setLogsDialog({ open: false, service: '', logs: [] })}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Logs for {logsDialog.service}
        </DialogTitle>
        <DialogContent>
          <Paper
            variant="outlined"
            sx={{
              p: 2,
              backgroundColor: '#1e1e1e',
              color: '#ffffff',
              fontFamily: 'monospace',
              fontSize: '0.875rem',
              maxHeight: '400px',
              overflow: 'auto'
            }}
          >
            {logsDialog.logs.map((line, index) => (
              <div key={index}>{line}</div>
            ))}
          </Paper>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLogsDialog({ open: false, service: '', logs: [] })}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default SystemManagement;