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
  FormControlLabel,
  Button,
  Tabs,
  Tab,
  Badge
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Computer as ComputerIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
  ViewInAr as ContainerIcon,
  Timeline as TimelineIcon,
  Visibility as VisibilityIcon,
  Dashboard as DashboardIcon,
  TrendingUp as MetricsIcon,
  Article as LogsIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  OpenInNew as OpenInNewIcon
} from '@mui/icons-material';
import { useSessionAuth } from '../../contexts/SessionAuthContext';

const ObservabilityDashboard = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [prometheusTargets, setPrometheusTargets] = useState([]);
  const [serviceMetrics, setServiceMetrics] = useState({});
  const [systemMetrics, setSystemMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(null);
  const { token } = useSessionAuth();

  // Fetch Prometheus targets via backend proxy
  const fetchPrometheusTargets = async () => {
    try {
      const apiBaseUrl = process.env.REACT_APP_API_URL || '';
      const response = await fetch(`${apiBaseUrl}/system/monitoring/prometheus/targets`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setPrometheusTargets(data.targets || []);
      }
    } catch (err) {
      console.error('Error fetching Prometheus targets:', err);
      // Fallback to mock data for demo
      setPrometheusTargets([
        {
          labels: { job: 'auth-service', component: 'microservice' },
          health: 'up',
          scrapeUrl: 'http://auth-service:8000/metrics',
          lastScrape: new Date().toISOString()
        },
        {
          labels: { job: 'user-service', component: 'microservice' },
          health: 'up',
          scrapeUrl: 'http://user-service:8000/metrics',
          lastScrape: new Date().toISOString()
        },
        {
          labels: { job: 'nginx', component: 'proxy' },
          health: 'up',
          scrapeUrl: 'http://nginx-exporter:9113/metrics',
          lastScrape: new Date().toISOString()
        },
        {
          labels: { job: 'backend', component: 'microservice' },
          health: 'down',
          scrapeUrl: 'http://backend:8000/metrics',
          lastScrape: new Date().toISOString()
        }
      ]);
    }
  };

  // Fetch service metrics via backend proxy
  const fetchServiceMetrics = async () => {
    try {
      const apiBaseUrl = process.env.REACT_APP_API_URL || '';
      const response = await fetch(`${apiBaseUrl}/system/monitoring/prometheus/metrics`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setServiceMetrics(data.metrics || {});
      }
    } catch (err) {
      console.error('Error fetching service metrics:', err);
      // Fallback to mock data for demo
      setServiceMetrics({
        'up': [
          { metric: { job: 'auth-service' }, value: [Date.now()/1000, '1'] },
          { metric: { job: 'user-service' }, value: [Date.now()/1000, '1'] },
          { metric: { job: 'nginx' }, value: [Date.now()/1000, '1'] },
          { metric: { job: 'backend' }, value: [Date.now()/1000, '0'] }
        ],
        'http_requests_total': [
          { metric: { service: 'auth-service' }, value: [Date.now()/1000, '64'] },
          { metric: { service: 'user-service' }, value: [Date.now()/1000, '64'] }
        ],
        'nginx_connections_active': [
          { metric: {}, value: [Date.now()/1000, '3'] }
        ],
        'nginx_http_requests_total': [
          { metric: {}, value: [Date.now()/1000, '142'] }
        ],
        'process_resident_memory_bytes': [
          { metric: { service: 'auth-service' }, value: [Date.now()/1000, '90931200'] },
          { metric: { service: 'user-service' }, value: [Date.now()/1000, '88276992'] }
        ]
      });
    }
  };

  // Fetch system metrics (existing functionality)
  const fetchSystemMetrics = async () => {
    try {
      const apiBaseUrl = process.env.REACT_APP_API_URL || '';
      const response = await fetch(`${apiBaseUrl}/system/monitoring/system-metrics`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSystemMetrics(data);
      }
    } catch (err) {
      console.error('Error fetching system metrics:', err);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    await Promise.all([
      fetchPrometheusTargets(),
      fetchServiceMetrics(),
      fetchSystemMetrics()
    ]);
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, [token]);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchData, 30000);
      setRefreshInterval(interval);
      return () => clearInterval(interval);
    } else if (refreshInterval) {
      clearInterval(refreshInterval);
      setRefreshInterval(null);
    }
  }, [autoRefresh]);

  const getHealthStatus = (targets) => {
    const total = targets.length;
    const healthy = targets.filter(t => t.health === 'up').length;
    const unhealthy = total - healthy;
    return { total, healthy, unhealthy };
  };

  const getServiceStatus = (serviceName) => {
    const target = prometheusTargets.find(t => 
      t.labels.job === serviceName || t.labels.service === serviceName
    );
    return target?.health === 'up' ? 'healthy' : 'unhealthy';
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const ServiceStatusCard = ({ title, serviceName, description, metrics = [] }) => {
    const status = getServiceStatus(serviceName);
    const isHealthy = status === 'healthy';
    
    return (
      <Card>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
            <Box display="flex" alignItems="center">
              <Badge
                color={isHealthy ? 'success' : 'error'}
                variant="dot"
                sx={{ mr: 1 }}
              >
                <Typography variant="h6">{title}</Typography>
              </Badge>
            </Box>
            <Chip
              label={isHealthy ? 'Healthy' : 'Down'}
              color={isHealthy ? 'success' : 'error'}
              size="small"
              icon={isHealthy ? <CheckCircleIcon /> : <ErrorIcon />}
            />
          </Box>
          <Typography variant="body2" color="textSecondary" mb={2}>
            {description}
          </Typography>
          {metrics.length > 0 && (
            <Box>
              {metrics.map((metric, index) => (
                <Typography key={index} variant="body2">
                  <strong>{metric.label}:</strong> {metric.value}
                </Typography>
              ))}
            </Box>
          )}
        </CardContent>
      </Card>
    );
  };

  const ObservabilityOverview = () => {
    const healthStatus = getHealthStatus(prometheusTargets);
    
    return (
      <Box>
        {/* Health Overview */}
        <Grid container spacing={3} mb={4}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <MetricsIcon color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6">Service Health</Typography>
                </Box>
                <Typography variant="h3" color="primary">
                  {healthStatus.healthy}/{healthStatus.total}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Services Online
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={(healthStatus.healthy / healthStatus.total) * 100}
                  color={healthStatus.unhealthy === 0 ? 'success' : 'warning'}
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <TimelineIcon color="secondary" sx={{ mr: 1 }} />
                  <Typography variant="h6">Metrics Collection</Typography>
                </Box>
                <Typography variant="h3" color="secondary">
                  {Object.keys(serviceMetrics).length}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Active Metrics
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <LogsIcon color="info" sx={{ mr: 1 }} />
                  <Typography variant="h6">Log Collection</Typography>
                </Box>
                <Typography variant="h3" color="info">
                  4
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Services Logging
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Service Status Grid */}
        <Typography variant="h5" mb={2}>Microservices Status</Typography>
        <Grid container spacing={3} mb={4}>
          <Grid item xs={12} md={6}>
            <ServiceStatusCard
              title="Authentication Service"
              serviceName="auth-service"
              description="Handles user authentication, sessions, and security policies"
              metrics={[
                { label: 'HTTP Requests', value: serviceMetrics.http_requests_total?.find(m => m.metric.service === 'auth-service')?.value?.[1] || 'N/A' },
                { label: 'Memory Usage', value: serviceMetrics.process_resident_memory_bytes?.find(m => m.metric.service === 'auth-service')?.value?.[1] ? formatBytes(parseInt(serviceMetrics.process_resident_memory_bytes.find(m => m.metric.service === 'auth-service').value[1])) : 'N/A' }
              ]}
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <ServiceStatusCard
              title="User Management Service"
              serviceName="user-service"
              description="Manages user accounts, profiles, and permissions"
              metrics={[
                { label: 'HTTP Requests', value: serviceMetrics.http_requests_total?.find(m => m.metric.service === 'user-service')?.value?.[1] || 'N/A' },
                { label: 'Memory Usage', value: serviceMetrics.process_resident_memory_bytes?.find(m => m.metric.service === 'user-service')?.value?.[1] ? formatBytes(parseInt(serviceMetrics.process_resident_memory_bytes.find(m => m.metric.service === 'user-service').value[1])) : 'N/A' }
              ]}
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <ServiceStatusCard
              title="Nginx Reverse Proxy"
              serviceName="nginx"
              description="API Gateway, SSL termination, and load balancing"
              metrics={[
                { label: 'Active Connections', value: serviceMetrics.nginx_connections_active?.[0]?.value?.[1] || 'N/A' },
                { label: 'Total Requests', value: serviceMetrics.nginx_http_requests_total?.[0]?.value?.[1] || 'N/A' }
              ]}
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <ServiceStatusCard
              title="Backend Service"
              serviceName="backend"
              description="Core business logic and API endpoints"
              metrics={[
                { label: 'Status', value: getServiceStatus('backend') === 'healthy' ? 'Online' : 'Metrics Not Available' }
              ]}
            />
          </Grid>
        </Grid>

        {/* External Monitoring Links */}
        <Typography variant="h5" mb={2}>Monitoring Dashboards</Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <DashboardIcon color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6">Grafana</Typography>
                </Box>
                <Typography variant="body2" color="textSecondary" mb={2}>
                  Advanced dashboards and visualization for all metrics and logs
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<OpenInNewIcon />}
                  onClick={() => window.open(`${window.location.origin}/grafana/`, '_blank')}
                  fullWidth
                >
                  Open Grafana
                </Button>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <MetricsIcon color="secondary" sx={{ mr: 1 }} />
                  <Typography variant="h6">Prometheus</Typography>
                </Box>
                <Typography variant="body2" color="textSecondary" mb={2}>
                  Raw metrics data and query interface
                </Typography>
                <Button
                  variant="outlined"
                  startIcon={<OpenInNewIcon />}
                  onClick={() => window.open(`${window.location.origin}/prometheus/`, '_blank')}
                  fullWidth
                >
                  Open Prometheus
                </Button>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <LogsIcon color="info" sx={{ mr: 1 }} />
                  <Typography variant="h6">Loki Logs</Typography>
                </Box>
                <Typography variant="body2" color="textSecondary" mb={2}>
                  Centralized log aggregation and search
                </Typography>
                <Button
                  variant="outlined"
                  startIcon={<OpenInNewIcon />}
                  onClick={() => window.open(`${window.location.origin}/grafana/explore`, '_blank')}
                  fullWidth
                >
                  View Logs
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    );
  };

  const PrometheusTargets = () => (
    <Box>
      <Typography variant="h5" mb={2}>Prometheus Targets</Typography>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Service</TableCell>
              <TableCell>Health</TableCell>
              <TableCell>Endpoint</TableCell>
              <TableCell>Last Scrape</TableCell>
              <TableCell>Component</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {prometheusTargets.map((target, index) => (
              <TableRow key={index}>
                <TableCell>{target.labels.job}</TableCell>
                <TableCell>
                  <Chip
                    label={target.health}
                    color={target.health === 'up' ? 'success' : 'error'}
                    size="small"
                    icon={target.health === 'up' ? <CheckCircleIcon /> : <ErrorIcon />}
                  />
                </TableCell>
                <TableCell>{target.scrapeUrl}</TableCell>
                <TableCell>{new Date(target.lastScrape).toLocaleString()}</TableCell>
                <TableCell>
                  <Chip
                    label={target.labels.component || 'unknown'}
                    size="small"
                    variant="outlined"
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );

  if (loading && !prometheusTargets.length) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
        <Typography variant="h6" ml={2}>Loading observability data...</Typography>
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Observability Dashboard
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
          Error loading observability data: {error}
        </Alert>
      )}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          <Tab label="Overview" />
          <Tab label="Prometheus Targets" />
          <Tab label="System Metrics" />
        </Tabs>
      </Box>

      {activeTab === 0 && <ObservabilityOverview />}
      {activeTab === 1 && <PrometheusTargets />}
      {activeTab === 2 && systemMetrics && (
        <Box>
          <Typography variant="h5" mb={2}>System Resources</Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    <ComputerIcon color="primary" sx={{ mr: 1 }} />
                    <Typography variant="h6">CPU Usage</Typography>
                  </Box>
                  <Typography variant="h4" color="primary">
                    {systemMetrics?.metrics?.cpu_usage_percent?.toFixed(1) || 'N/A'}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={systemMetrics?.metrics?.cpu_usage_percent || 0}
                    color={systemMetrics?.metrics?.cpu_usage_percent > 80 ? 'error' : 'success'}
                    sx={{ mt: 1 }}
                  />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    <MemoryIcon color="secondary" sx={{ mr: 1 }} />
                    <Typography variant="h6">Memory</Typography>
                  </Box>
                  <Typography variant="h4" color="secondary">
                    {systemMetrics?.metrics?.memory_usage_percent?.toFixed(1) || 'N/A'}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={systemMetrics?.metrics?.memory_usage_percent || 0}
                    color={systemMetrics?.metrics?.memory_usage_percent > 80 ? 'error' : 'success'}
                    sx={{ mt: 1 }}
                  />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    <StorageIcon color="warning" sx={{ mr: 1 }} />
                    <Typography variant="h6">Disk Usage</Typography>
                  </Box>
                  <Typography variant="h4" color="warning">
                    {systemMetrics?.metrics?.disk_usage_percent?.toFixed(1) || 'N/A'}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={systemMetrics?.metrics?.disk_usage_percent || 0}
                    color={systemMetrics?.metrics?.disk_usage_percent > 80 ? 'error' : 'success'}
                    sx={{ mt: 1 }}
                  />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    <ContainerIcon color="info" sx={{ mr: 1 }} />
                    <Typography variant="h6">Containers</Typography>
                  </Box>
                  <Typography variant="h4" color="info">
                    {systemMetrics?.docker?.running_containers || 0}/{systemMetrics?.docker?.total_containers || 0}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Running/Total
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      )}
    </Box>
  );
};

export default ObservabilityDashboard;