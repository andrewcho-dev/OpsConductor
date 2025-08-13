/**
 * Enhanced Dashboard with real-time analytics
 */
import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  CardHeader,
  Chip,
  LinearProgress,
  Alert,
  IconButton,
  Tooltip,
  CircularProgress,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

// API hooks
import { useGetDashboardMetricsQuery, useGetSystemHealthReportQuery } from '../../../store/api/analyticsApi';
import { useGetJobStatisticsQuery } from '../../../store/api/jobsApi';
import { useGetTargetStatisticsQuery } from '../../../store/api/targetsApi';

// WebSocket hook
import useWebSocket from '../../../hooks/useWebSocket';

// Chart components (you'd need to install react-chartjs-2 and chart.js)
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement,
  BarElement,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement,
  BarElement
);

const EnhancedDashboard = () => {
  const [refreshKey, setRefreshKey] = useState(0);
  
  // API queries
  const {
    data: dashboardMetrics,
    isLoading: metricsLoading,
    error: metricsError,
    refetch: refetchMetrics,
  } = useGetDashboardMetricsQuery(undefined, {
    pollingInterval: 30000, // Refresh every 30 seconds
  });

  const {
    data: healthReport,
    isLoading: healthLoading,
    refetch: refetchHealth,
  } = useGetSystemHealthReportQuery(undefined, {
    pollingInterval: 60000, // Refresh every minute
  });

  // WebSocket for real-time updates
  const { isConnected } = useWebSocket('dashboard');

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
    refetchMetrics();
    refetchHealth();
  };

  if (metricsLoading || healthLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (metricsError) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Error loading dashboard data: {metricsError.message}
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Dashboard
        </Typography>
        <Box display="flex" alignItems="center" gap={2}>
          <Chip
            icon={isConnected ? <CheckCircleIcon /> : <ErrorIcon />}
            label={isConnected ? 'Connected' : 'Disconnected'}
            color={isConnected ? 'success' : 'error'}
            size="small"
          />
          <Tooltip title="Refresh Dashboard">
            <IconButton onClick={handleRefresh}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* System Health Alert */}
      {healthReport && healthReport.health_score < 80 && (
        <Alert 
          severity={healthReport.status === 'critical' ? 'error' : 'warning'} 
          sx={{ mb: 3 }}
          icon={<WarningIcon />}
        >
          System Health Score: {healthReport.health_score}% - {healthReport.issues.length} issues detected
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Overview Cards */}
        <Grid item xs={12}>
          <OverviewCards metrics={dashboardMetrics?.overview} />
        </Grid>

        {/* Charts Row 1 */}
        <Grid item xs={12} md={6}>
          <JobStatusChart data={dashboardMetrics?.job_metrics} />
        </Grid>
        <Grid item xs={12} md={6}>
          <TargetStatusChart data={dashboardMetrics?.target_metrics} />
        </Grid>

        {/* Charts Row 2 */}
        <Grid item xs={12} md={8}>
          <ExecutionTrendsChart data={dashboardMetrics?.trends} />
        </Grid>
        <Grid item xs={12} md={4}>
          <SystemHealthCard healthReport={healthReport} />
        </Grid>

        {/* Performance Metrics */}
        <Grid item xs={12}>
          <PerformanceMetrics data={dashboardMetrics?.performance_metrics} />
        </Grid>
      </Grid>
    </Box>
  );
};

const OverviewCards = ({ metrics }) => {
  if (!metrics) return null;

  const cards = [
    {
      title: 'Total Jobs',
      value: metrics.totals?.jobs || 0,
      active: metrics.active?.jobs || 0,
      color: 'primary',
      icon: <InfoIcon />,
    },
    {
      title: 'Total Targets',
      value: metrics.totals?.targets || 0,
      active: metrics.active?.targets || 0,
      color: 'secondary',
      icon: <InfoIcon />,
    },
    {
      title: 'Total Users',
      value: metrics.totals?.users || 0,
      active: metrics.active?.users || 0,
      color: 'success',
      icon: <InfoIcon />,
    },
    {
      title: 'Recent Executions',
      value: metrics.recent_activity?.executions_24h || 0,
      subtitle: 'Last 24 hours',
      color: 'warning',
      icon: <TrendingUpIcon />,
    },
  ];

  return (
    <Grid container spacing={2}>
      {cards.map((card, index) => (
        <Grid item xs={12} sm={6} md={3} key={index}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    {card.title}
                  </Typography>
                  <Typography variant="h4" component="div">
                    {card.value}
                  </Typography>
                  {card.active !== undefined && (
                    <Typography variant="body2" color="textSecondary">
                      {card.active} active
                    </Typography>
                  )}
                  {card.subtitle && (
                    <Typography variant="body2" color="textSecondary">
                      {card.subtitle}
                    </Typography>
                  )}
                </Box>
                <Box color={`${card.color}.main`}>
                  {card.icon}
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

const JobStatusChart = ({ data }) => {
  if (!data?.execution_status_distribution) return null;

  const chartData = {
    labels: Object.keys(data.execution_status_distribution),
    datasets: [
      {
        data: Object.values(data.execution_status_distribution),
        backgroundColor: [
          '#4caf50', // completed
          '#ff9800', // running
          '#f44336', // failed
          '#2196f3', // pending
        ],
        borderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'bottom',
      },
      title: {
        display: true,
        text: 'Job Execution Status',
      },
    },
  };

  return (
    <Paper sx={{ p: 2, height: 400 }}>
      <Doughnut data={chartData} options={options} />
    </Paper>
  );
};

const TargetStatusChart = ({ data }) => {
  if (!data?.status_distribution) return null;

  const chartData = {
    labels: Object.keys(data.status_distribution),
    datasets: [
      {
        label: 'Targets',
        data: Object.values(data.status_distribution),
        backgroundColor: '#2196f3',
        borderColor: '#1976d2',
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: 'Target Status Distribution',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return (
    <Paper sx={{ p: 2, height: 400 }}>
      <Bar data={chartData} options={options} />
    </Paper>
  );
};

const ExecutionTrendsChart = ({ data }) => {
  if (!data?.daily_executions_30d) return null;

  const chartData = {
    labels: data.daily_executions_30d.map(item => item.day),
    datasets: [
      {
        label: 'Successful',
        data: data.daily_executions_30d.map(item => item.successful),
        borderColor: '#4caf50',
        backgroundColor: 'rgba(76, 175, 80, 0.1)',
        tension: 0.1,
      },
      {
        label: 'Failed',
        data: data.daily_executions_30d.map(item => item.failed),
        borderColor: '#f44336',
        backgroundColor: 'rgba(244, 67, 54, 0.1)',
        tension: 0.1,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Execution Trends (30 Days)',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return (
    <Paper sx={{ p: 2, height: 400 }}>
      <Line data={chartData} options={options} />
    </Paper>
  );
};

const SystemHealthCard = ({ healthReport }) => {
  if (!healthReport) return null;

  const getHealthColor = (score) => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  return (
    <Paper sx={{ p: 2, height: 400 }}>
      <CardHeader title="System Health" />
      <CardContent>
        <Box textAlign="center" mb={2}>
          <Typography variant="h2" color={`${getHealthColor(healthReport.health_score)}.main`}>
            {healthReport.health_score}%
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Health Score
          </Typography>
        </Box>
        
        <LinearProgress
          variant="determinate"
          value={healthReport.health_score}
          color={getHealthColor(healthReport.health_score)}
          sx={{ mb: 2, height: 8, borderRadius: 4 }}
        />

        <Typography variant="h6" gutterBottom>
          Issues ({healthReport.issues?.length || 0})
        </Typography>
        
        {healthReport.issues?.slice(0, 3).map((issue, index) => (
          <Alert 
            key={index} 
            severity={issue.severity} 
            sx={{ mb: 1 }}
            variant="outlined"
          >
            {issue.message}
          </Alert>
        ))}
        
        {healthReport.issues?.length > 3 && (
          <Typography variant="body2" color="textSecondary">
            +{healthReport.issues.length - 3} more issues
          </Typography>
        )}
      </CardContent>
    </Paper>
  );
};

const PerformanceMetrics = ({ data }) => {
  if (!data?.hourly_executions_24h) return null;

  const chartData = {
    labels: data.hourly_executions_24h.map(item => 
      new Date(item.hour).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    ),
    datasets: [
      {
        label: 'Executions',
        data: data.hourly_executions_24h.map(item => item.count),
        borderColor: '#2196f3',
        backgroundColor: 'rgba(33, 150, 243, 0.1)',
        tension: 0.1,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: 'Hourly Execution Activity (24 Hours)',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return (
    <Paper sx={{ p: 2 }}>
      <Line data={chartData} options={options} />
    </Paper>
  );
};

export default EnhancedDashboard;