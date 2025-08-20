import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Computer as ComputerIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
  ViewInAr as ContainerIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';
import { useSessionAuth } from '../../contexts/SessionAuthContext';

const InfrastructureMonitoring = () => {
  const [systemMetrics, setSystemMetrics] = useState(null);
  const [netdataInfo, setNetdataInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(null);
  const { token } = useSessionAuth();

  const fetchSystemMetrics = async () => {
    try {
      const apiBaseUrl = process.env.REACT_APP_API_URL || '/api/v3';
      const response = await fetch(`${apiBaseUrl}/monitoring/system-metrics`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setSystemMetrics(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching system metrics:', err);
      setError(err.message);
    }
  };

  const fetchNetdataInfo = async () => {
    try {
      const apiBaseUrl = process.env.REACT_APP_API_URL || '/api/v3';
      const response = await fetch(`${apiBaseUrl}/monitoring/netdata-info`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setNetdataInfo(data);
      }
    } catch (err) {
      console.error('Error fetching Netdata info:', err);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    await Promise.all([fetchSystemMetrics(), fetchNetdataInfo()]);
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, [token]);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
      setRefreshInterval(interval);
      return () => clearInterval(interval);
    } else if (refreshInterval) {
      clearInterval(refreshInterval);
      setRefreshInterval(null);
    }
  }, [autoRefresh]);

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

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'success';
      case 'exited': return 'error';
      case 'paused': return 'warning';
      default: return 'default';
    }
  };

  const MetricCard = ({ title, value, unit, percentage, icon, color = 'primary' }) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" mb={2}>
          {icon}
          <Typography variant="h6" ml={1}>
            {title}
          </Typography>
        </Box>
        <Typography variant="h4" color={color}>
          {value}{unit}
        </Typography>
        {percentage !== undefined && (
          <Box mt={1}>
            <LinearProgress 
              variant="determinate" 
              value={percentage} 
              color={percentage > 80 ? 'error' : percentage > 60 ? 'warning' : 'success'}
            />
            <Typography variant="body2" color="textSecondary" mt={0.5}>
              {percentage.toFixed(1)}% used
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );

  if (loading && !systemMetrics) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
        <Typography variant="h6" ml={2}>Loading infrastructure metrics...</Typography>
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Infrastructure Monitoring
        </Typography>
        <Box display="flex" alignItems="center" gap={2}>
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
            }
            label="Auto Refresh"
          />
          <Tooltip title="Refresh Now">
            <IconButton onClick={fetchData} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Error loading metrics: {error}
        </Alert>
      )}

      {/* Monitoring Options */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <TimelineIcon color="primary" />
                <Typography variant="h6" ml={1}>
                  Netdata - Real-time Monitoring
                </Typography>
              </Box>
              <Typography variant="body2" color="textSecondary" mb={2}>
                Beautiful real-time dashboards with zero configuration. Perfect for live monitoring.
              </Typography>
              <Box display="flex" gap={1}>
                <Chip 
                  label={netdataInfo ? `v${netdataInfo.version}` : 'Loading...'} 
                  color="primary" 
                  size="small" 
                />
                <Chip 
                  label="Real-time" 
                  color="success" 
                  size="small" 
                />
                <Chip 
                  label="Zero Config" 
                  color="info" 
                  size="small" 
                />
              </Box>
              <Box mt={2}>
                <a 
                  href="http://192.168.50.100:19999" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  style={{ textDecoration: 'none' }}
                >
                  <Chip 
                    label="Open Netdata Dashboard" 
                    color="primary" 
                    clickable 
                  />
                </a>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <SpeedIcon color="secondary" />
                <Typography variant="h6" ml={1}>
                  Custom Metrics Dashboard
                </Typography>
              </Box>
              <Typography variant="body2" color="textSecondary" mb={2}>
                Lightweight custom dashboard using Node Exporter data. Integrated into your system.
              </Typography>
              <Box display="flex" gap={1}>
                <Chip 
                  label="Node Exporter" 
                  color="secondary" 
                  size="small" 
                />
                <Chip 
                  label="Lightweight" 
                  color="success" 
                  size="small" 
                />
                <Chip 
                  label="Custom UI" 
                  color="info" 
                  size="small" 
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {systemMetrics && (
        <>
          {/* System Overview */}
          <Typography variant="h5" mb={2}>System Overview</Typography>
          <Grid container spacing={3} mb={4}>
            <Grid item xs={12} sm={6} md={3}>
              <MetricCard
                title="CPU Usage"
                value={systemMetrics?.metrics?.cpu_usage_percent?.toFixed(1) || 'N/A'}
                unit="%"
                percentage={systemMetrics?.metrics?.cpu_usage_percent}
                icon={<ComputerIcon color="primary" />}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <MetricCard
                title="Memory"
                value={systemMetrics?.metrics?.memory_total && systemMetrics?.metrics?.memory_available ? 
                  formatBytes(systemMetrics.metrics.memory_total - systemMetrics.metrics.memory_available) : 'N/A'}
                unit=""
                percentage={systemMetrics?.metrics?.memory_usage_percent}
                icon={<MemoryIcon color="secondary" />}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <MetricCard
                title="Disk Usage"
                value={systemMetrics?.metrics?.disk_total && systemMetrics?.metrics?.disk_free ? 
                  formatBytes(systemMetrics.metrics.disk_total - systemMetrics.metrics.disk_free) : 'N/A'}
                unit=""
                percentage={systemMetrics?.metrics?.disk_usage_percent}
                icon={<StorageIcon color="warning" />}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <MetricCard
                title="Load Average"
                value={systemMetrics?.metrics?.load_1min?.toFixed(2) || 'N/A'}
                unit=""
                icon={<SpeedIcon color="info" />}
              />
            </Grid>
          </Grid>

          {/* System Information */}
          <Typography variant="h5" mb={2}>System Information</Typography>
          <Grid container spacing={3} mb={4}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" mb={2}>Host Details</Typography>
                  <Box display="flex" flexDirection="column" gap={1}>
                    <Typography><strong>Hostname:</strong> {systemMetrics?.system?.hostname || 'N/A'}</Typography>
                    <Typography><strong>Platform:</strong> {systemMetrics?.system?.platform || 'N/A'}</Typography>
                    <Typography><strong>Architecture:</strong> {systemMetrics?.system?.architecture || 'N/A'}</Typography>
                    <Typography><strong>CPU Cores:</strong> {systemMetrics?.system?.cpu_count || 'N/A'}</Typography>
                    <Typography><strong>Uptime:</strong> {systemMetrics?.system?.uptime_seconds ? formatUptime(systemMetrics.system.uptime_seconds) : 'N/A'}</Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" mb={2}>Resource Summary</Typography>
                  <Box display="flex" flexDirection="column" gap={1}>
                    <Typography><strong>Total Memory:</strong> {systemMetrics?.metrics?.memory_total ? formatBytes(systemMetrics.metrics.memory_total) : 'N/A'}</Typography>
                    <Typography><strong>Available Memory:</strong> {systemMetrics?.metrics?.memory_available ? formatBytes(systemMetrics.metrics.memory_available) : 'N/A'}</Typography>
                    <Typography><strong>Total Disk:</strong> {systemMetrics?.metrics?.disk_total ? formatBytes(systemMetrics.metrics.disk_total) : 'N/A'}</Typography>
                    <Typography><strong>Free Disk:</strong> {systemMetrics?.metrics?.disk_free ? formatBytes(systemMetrics.metrics.disk_free) : 'N/A'}</Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Docker Containers */}
          <Typography variant="h5" mb={2}>Docker Containers</Typography>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <ContainerIcon color="primary" />
                <Typography variant="h6" ml={1}>
                  Container Status ({systemMetrics?.docker?.total_containers || 0} total)
                </Typography>
                <Box ml="auto" display="flex" gap={1}>
                  <Chip 
                    label={`${systemMetrics?.docker?.running_containers || 0} Running`} 
                    color="success" 
                    size="small" 
                  />
                  <Chip 
                    label={`${systemMetrics?.docker?.stopped_containers || 0} Stopped`} 
                    color="error" 
                    size="small" 
                  />
                </Box>
              </Box>
              
              <TableContainer 
                component={Paper} 
                variant="outlined"
                sx={{ 
                  maxHeight: '100%', // Dynamic height - stops 70px above footer
                  overflow: 'auto'
                }}
              >
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Container</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Image</TableCell>
                      <TableCell>CPU %</TableCell>
                      <TableCell>Memory</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {systemMetrics?.docker?.containers?.map((container, index) => (
                      <TableRow key={index}>
                        <TableCell>{container.name}</TableCell>
                        <TableCell>
                          <Chip 
                            label={container.status} 
                            color={getStatusColor(container.status)} 
                            size="small" 
                          />
                        </TableCell>
                        <TableCell>{container.image}</TableCell>
                        <TableCell>
                          {container.cpu_percent ? `${container.cpu_percent}%` : 'N/A'}
                        </TableCell>
                        <TableCell>
                          {container.memory_usage ? (
                            <>
                              {formatBytes(container.memory_usage)}
                              {container.memory_percent && ` (${container.memory_percent.toFixed(1)}%)`}
                            </>
                          ) : 'N/A'}
                        </TableCell>
                      </TableRow>
                    )) || []}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </>
      )}
    </Box>
  );
};

export default InfrastructureMonitoring;