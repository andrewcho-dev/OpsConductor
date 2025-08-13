/**
 * Celery Monitor - Real-time monitoring of Celery workers, queues, and tasks
 * Provides comprehensive visibility into the Celery infrastructure
 */
import React, { useState, useEffect } from 'react';
import MetricsChart from './MetricsChart';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  LinearProgress,
  Alert,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
  Badge,
  Divider,
  CircularProgress,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Computer as ComputerIcon,
  Queue as QueueIcon,
  Speed as SpeedIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Timeline as TimelineIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Settings as SettingsIcon,
  Visibility as ViewIcon,
  Group as GroupIcon,
  Work as WorkIcon,
  Timer as TimerIcon,
  DataObject as DataObjectIcon,
  ToggleOn as ToggleOnIcon,
  ToggleOff as ToggleOffIcon,
} from '@mui/icons-material';

const CeleryMonitor = ({ celeryStats, queueStats, workerStats, onRefresh, refreshing = false }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [selectedWorker, setSelectedWorker] = useState(null);
  const [selectedQueue, setSelectedQueue] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [metricsHistory, setMetricsHistory] = useState(null);
  const [loadingMetrics, setLoadingMetrics] = useState(false);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(onRefresh, 10000); // Increased from 3s to 10s
      return () => clearInterval(interval);
    }
  }, [autoRefresh, onRefresh]);

  useEffect(() => {
    // Fetch metrics history when metrics tab is active
    if (activeTab === 3) {
      fetchMetricsHistory();
    }
  }, [activeTab]);

  const fetchMetricsHistory = async () => {
    setLoadingMetrics(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/celery/metrics/history?hours=24', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setMetricsHistory(data);
      } else {
        console.error('Failed to fetch metrics history');
      }
    } catch (error) {
      console.error('Error fetching metrics history:', error);
    } finally {
      setLoadingMetrics(false);
    }
  };

  const getWorkerStatus = (worker) => {
    if (!worker.online) return { status: 'offline', color: 'error' };
    if (worker.active_tasks > worker.pool_size * 0.8) return { status: 'busy', color: 'warning' };
    return { status: 'online', color: 'success' };
  };

  const getQueueHealth = (queue) => {
    if (queue.pending > 100) return { status: 'overloaded', color: 'error' };
    if (queue.pending > 50) return { status: 'busy', color: 'warning' };
    return { status: 'healthy', color: 'success' };
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDuration = (seconds) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  const renderWorkersTab = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Worker Status</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            size="small"
            variant={autoRefresh ? "contained" : "outlined"}
            startIcon={autoRefresh ? <ToggleOnIcon /> : <ToggleOffIcon />}
            onClick={() => setAutoRefresh(!autoRefresh)}
            color={autoRefresh ? "success" : "primary"}
          >
            Auto-refresh {autoRefresh ? 'ON' : 'OFF'}
          </Button>
          <Button
            size="small"
            startIcon={refreshing ? <CircularProgress size={16} /> : <RefreshIcon />}
            onClick={onRefresh}
            disabled={refreshing}
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
        </Box>
      </Box>

      <div className="stats-grid">
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon primary">
              <ComputerIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{workerStats.total_workers || 0}</h3>
              <p>Total Workers</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon success">
              <CheckCircleIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{workerStats.active_workers || 0}</h3>
              <p>Active Workers</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon info">
              <WorkIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{workerStats.busy_workers || 0}</h3>
              <p>Busy Workers</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon warning">
              <SpeedIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{workerStats.avg_load || 0}%</h3>
              <p>Avg Load</p>
            </div>
          </div>
        </div>
        
        {/* Empty slots to maintain 6-column grid */}
        <div className="stat-card" style={{ visibility: 'hidden' }}>
          <div className="stat-card-content">
            <div className="stat-icon primary">
              <ComputerIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>-</h3>
              <p>-</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card" style={{ visibility: 'hidden' }}>
          <div className="stat-card-content">
            <div className="stat-icon primary">
              <ComputerIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>-</h3>
              <p>-</p>
            </div>
          </div>
        </div>
      </div>

      {/* Worker Details Table */}
      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Worker Details</Typography>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Worker</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Active Tasks</TableCell>
                  <TableCell>Pool Size</TableCell>
                  <TableCell>Load</TableCell>
                  <TableCell>Memory</TableCell>
                  <TableCell>Uptime</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(workerStats.workers || []).map((worker) => {
                  const status = getWorkerStatus(worker);
                  return (
                    <TableRow key={worker.name} hover>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {worker.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {worker.hostname}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={status.status} 
                          color={status.color} 
                          size="small"
                          icon={status.status === 'online' ? <CheckCircleIcon /> : <ErrorIcon />}
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2">
                            {worker.active_tasks || 0}
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={(worker.active_tasks / worker.pool_size) * 100}
                            sx={{ width: 50, height: 4 }}
                          />
                        </Box>
                      </TableCell>
                      <TableCell>{worker.pool_size || 0}</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2">
                            {worker.load_avg || 0}%
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={worker.load_avg || 0}
                            sx={{ width: 50, height: 4 }}
                            color={worker.load_avg > 80 ? 'error' : worker.load_avg > 60 ? 'warning' : 'primary'}
                          />
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatBytes(worker.memory_usage || 0)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatDuration(worker.uptime || 0)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Tooltip title="View Details">
                            <IconButton size="small" onClick={() => setSelectedWorker(worker)}>
                              <ViewIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Restart Worker">
                            <IconButton size="small" color="warning">
                              <RefreshIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );

  const renderQueuesTab = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Queue Status</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            size="small"
            variant={autoRefresh ? "contained" : "outlined"}
            startIcon={autoRefresh ? <ToggleOnIcon /> : <ToggleOffIcon />}
            onClick={() => setAutoRefresh(!autoRefresh)}
            color={autoRefresh ? "success" : "primary"}
          >
            Auto-refresh {autoRefresh ? 'ON' : 'OFF'}
          </Button>
          <Button
            size="small"
            startIcon={refreshing ? <CircularProgress size={16} /> : <RefreshIcon />}
            onClick={onRefresh}
            disabled={refreshing}
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
        </Box>
      </Box>

      <div className="stats-grid">
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon primary">
              <QueueIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{Object.keys(queueStats).length}</h3>
              <p>Total Queues</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon warning">
              <TimerIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{Object.values(queueStats).reduce((sum, q) => sum + (q.pending || 0), 0)}</h3>
              <p>Pending Tasks</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon success">
              <TrendingUpIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{Object.values(queueStats).reduce((sum, q) => sum + (q.processed || 0), 0)}</h3>
              <p>Processed Today</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon info">
              <WorkIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{Object.values(queueStats).reduce((sum, q) => sum + (q.processing || 0), 0)}</h3>
              <p>Processing Now</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon error">
              <ErrorIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{Object.values(queueStats).reduce((sum, q) => sum + (q.failed || 0), 0)}</h3>
              <p>Failed Tasks</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon secondary">
              <SpeedIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{Object.values(queueStats).length > 0 ? Math.round(Object.values(queueStats).reduce((sum, q) => sum + (q.avg_time || 0), 0) / Object.values(queueStats).length) : 0}s</h3>
              <p>Avg Process Time</p>
            </div>
          </div>
        </div>
      </div>

      {/* Queue Details */}
      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Queue Details</Typography>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Queue Name</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Pending</TableCell>
                  <TableCell>Processing</TableCell>
                  <TableCell>Processed</TableCell>
                  <TableCell>Failed</TableCell>
                  <TableCell>Avg Time</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {Object.entries(queueStats).map(([queueName, queue]) => {
                  const health = getQueueHealth(queue);
                  return (
                    <TableRow key={queueName} hover>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {queueName}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={health.status} 
                          color={health.color} 
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Badge badgeContent={queue.pending || 0} color="warning">
                          <QueueIcon fontSize="small" />
                        </Badge>
                      </TableCell>
                      <TableCell>{queue.processing || 0}</TableCell>
                      <TableCell>{queue.processed || 0}</TableCell>
                      <TableCell>
                        <Typography variant="body2" color="error">
                          {queue.failed || 0}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {queue.avg_time ? `${queue.avg_time}s` : 'N/A'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Tooltip title="View Queue">
                            <IconButton size="small" onClick={() => setSelectedQueue({...queue, name: queueName})}>
                              <ViewIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Purge Queue">
                            <IconButton size="small" color="error">
                              <StopIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );

  const renderTasksTab = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Active Tasks</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            size="small"
            variant={autoRefresh ? "contained" : "outlined"}
            startIcon={autoRefresh ? <ToggleOnIcon /> : <ToggleOffIcon />}
            onClick={() => setAutoRefresh(!autoRefresh)}
            color={autoRefresh ? "success" : "primary"}
          >
            Auto-refresh {autoRefresh ? 'ON' : 'OFF'}
          </Button>
          <Button
            size="small"
            startIcon={refreshing ? <CircularProgress size={16} /> : <RefreshIcon />}
            onClick={onRefresh}
            disabled={refreshing}
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
        </Box>
      </Box>

      <div className="stats-grid">
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon primary">
              <WorkIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{celeryStats.active_tasks || 0}</h3>
              <p>Active Tasks</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon info">
              <SpeedIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{celeryStats.tasks_per_minute || 0}</h3>
              <p>Tasks/Min</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon success">
              <TimelineIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{celeryStats.avg_task_time || 0}s</h3>
              <p>Avg Duration</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon error">
              <ErrorIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{celeryStats.failed_tasks || 0}</h3>
              <p>Failed Tasks</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon warning">
              <TimerIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{celeryStats.pending_tasks || 0}</h3>
              <p>Pending Tasks</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon secondary">
              <TrendingUpIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{celeryStats.completed_tasks || 0}</h3>
              <p>Completed Today</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Tasks Table */}
      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Recent Tasks</Typography>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Task Name</TableCell>
                  <TableCell>Task ID</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Worker</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Started</TableCell>
                  <TableCell>Queue</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(celeryStats.recent_tasks || []).map((task, index) => (
                  <TableRow key={index} hover>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {task.name || 'Unknown Task'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {task.args ? `Args: ${JSON.stringify(task.args).substring(0, 50)}...` : 'No args'}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                        {task.id ? task.id.substring(0, 8) + '...' : 'N/A'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={task.status || 'UNKNOWN'} 
                        size="small" 
                        color={
                          task.status === 'SUCCESS' ? 'success' : 
                          task.status === 'FAILURE' ? 'error' : 
                          task.status === 'PENDING' ? 'warning' :
                          task.status === 'STARTED' ? 'info' : 'default'
                        }
                        icon={
                          task.status === 'SUCCESS' ? <CheckCircleIcon /> :
                          task.status === 'FAILURE' ? <ErrorIcon /> :
                          task.status === 'STARTED' ? <PlayIcon /> : undefined
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {task.worker || 'Unknown'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {task.duration ? `${task.duration}s` : 'N/A'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {task.started ? new Date(task.started).toLocaleTimeString() : 'N/A'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {task.queue || 'default'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Tooltip title="View Task Details">
                        <IconButton size="small" onClick={() => setSelectedWorker(task)}>
                          <ViewIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
                {(!celeryStats.recent_tasks || celeryStats.recent_tasks.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={8} align="center">
                      <Typography variant="body2" color="text.secondary">
                        No recent tasks found
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );

  const renderMetricsTab = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Performance Metrics (Last 24 Hours)</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            size="small"
            variant={autoRefresh ? "contained" : "outlined"}
            startIcon={autoRefresh ? <ToggleOnIcon /> : <ToggleOffIcon />}
            onClick={() => setAutoRefresh(!autoRefresh)}
            color={autoRefresh ? "success" : "primary"}
          >
            Auto-refresh {autoRefresh ? 'ON' : 'OFF'}
          </Button>
          <Button
            size="small"
            startIcon={loadingMetrics ? <CircularProgress size={16} /> : <RefreshIcon />}
            onClick={fetchMetricsHistory}
            disabled={loadingMetrics}
          >
            {loadingMetrics ? 'Loading...' : 'Refresh Charts'}
          </Button>
        </Box>
      </Box>

      <div className="stats-grid">
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon primary">
              <TrendingUpIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{metricsHistory?.summary?.peak_throughput || 0}</h3>
              <p>Peak Throughput/Min</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon warning">
              <SpeedIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{metricsHistory?.summary?.avg_load || 0}%</h3>
              <p>Avg Worker Load</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon success">
              <CheckCircleIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{metricsHistory?.summary?.success_rate || 0}%</h3>
              <p>Success Rate</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon info">
              <TimelineIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{metricsHistory?.summary?.avg_duration || 0}s</h3>
              <p>Avg Task Duration</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon error">
              <ErrorIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{metricsHistory?.summary?.total_failures || 0}</h3>
              <p>Total Failures</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon secondary">
              <MemoryIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{metricsHistory?.summary?.peak_memory || 0}MB</h3>
              <p>Peak Memory Usage</p>
            </div>
          </div>
        </div>
      </div>
      
      {loadingMetrics ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={2} sx={{ mt: 2 }}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Task Throughput</Typography>
                <MetricsChart
                  title="Tasks per Minute"
                  data={metricsHistory ? {
                    timestamps: metricsHistory.timestamps,
                    values: metricsHistory.metrics.tasks_per_minute
                  } : null}
                  color="rgb(75, 192, 192)"
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Worker Load</Typography>
                <MetricsChart
                  title="Average Worker Load %"
                  data={metricsHistory ? {
                    timestamps: metricsHistory.timestamps,
                    values: metricsHistory.metrics.worker_loads
                  } : null}
                  color="rgb(255, 99, 132)"
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Active Tasks</Typography>
                <MetricsChart
                  title="Active Tasks"
                  data={metricsHistory ? {
                    timestamps: metricsHistory.timestamps,
                    values: metricsHistory.metrics.active_tasks
                  } : null}
                  color="rgb(54, 162, 235)"
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Task Success vs Failures</Typography>
                <MetricsChart
                  title="Completed Tasks"
                  data={metricsHistory ? {
                    timestamps: metricsHistory.timestamps,
                    values: metricsHistory.metrics.completed_tasks
                  } : null}
                  color="rgb(75, 192, 75)"
                />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );

  return (
    <Box sx={{ height: '100%', overflow: 'auto' }}>
      <Paper sx={{ mb: 2 }}>
        <Tabs
          value={activeTab}
          onChange={(e, newValue) => setActiveTab(newValue)}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label="Workers" />
          <Tab label="Queues" />
          <Tab label="Tasks" />
          <Tab label="Metrics" />
        </Tabs>
      </Paper>

      <Box sx={{ p: 2 }}>
        {activeTab === 0 && renderWorkersTab()}
        {activeTab === 1 && renderQueuesTab()}
        {activeTab === 2 && renderTasksTab()}
        {activeTab === 3 && renderMetricsTab()}
      </Box>

      {/* Worker Details Modal */}
      <Dialog
        open={!!selectedWorker}
        onClose={() => setSelectedWorker(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ComputerIcon />
            Worker Details: {selectedWorker?.name}
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedWorker && (
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Basic Information</Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Name:</Typography>
                        <Typography variant="body2">{selectedWorker.name}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Hostname:</Typography>
                        <Typography variant="body2">{selectedWorker.hostname}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Status:</Typography>
                        <Chip 
                          label={getWorkerStatus(selectedWorker).status} 
                          color={getWorkerStatus(selectedWorker).color} 
                          size="small"
                        />
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Uptime:</Typography>
                        <Typography variant="body2">{formatDuration(selectedWorker.uptime || 0)}</Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Performance</Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Active Tasks:</Typography>
                        <Typography variant="body2">{selectedWorker.active_tasks || 0}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Pool Size:</Typography>
                        <Typography variant="body2">{selectedWorker.pool_size || 0}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Load Average:</Typography>
                        <Typography variant="body2">{selectedWorker.load_avg || 0}%</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Memory Usage:</Typography>
                        <Typography variant="body2">{formatBytes(selectedWorker.memory_usage || 0)}</Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Configuration</Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Queues:</Typography>
                        <Typography variant="body2">
                          {selectedWorker.queues ? selectedWorker.queues.join(', ') : 'N/A'}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Prefetch Count:</Typography>
                        <Typography variant="body2">{selectedWorker.prefetch_count || 'N/A'}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Software Version:</Typography>
                        <Typography variant="body2">{selectedWorker.sw_ver || 'N/A'}</Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedWorker(null)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Queue Details Modal */}
      <Dialog
        open={!!selectedQueue}
        onClose={() => setSelectedQueue(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <QueueIcon />
            Queue Details: {selectedQueue?.name || 'Queue'}
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedQueue && (
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Queue Status</Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Health:</Typography>
                        <Chip 
                          label={getQueueHealth(selectedQueue).status} 
                          color={getQueueHealth(selectedQueue).color} 
                          size="small"
                        />
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Pending Tasks:</Typography>
                        <Typography variant="body2">{selectedQueue.pending || 0}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Processing:</Typography>
                        <Typography variant="body2">{selectedQueue.processing || 0}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Processed Today:</Typography>
                        <Typography variant="body2">{selectedQueue.processed || 0}</Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Performance Metrics</Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Failed Tasks:</Typography>
                        <Typography variant="body2" color="error">{selectedQueue.failed || 0}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Average Time:</Typography>
                        <Typography variant="body2">
                          {selectedQueue.avg_time ? `${selectedQueue.avg_time}s` : 'N/A'}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Success Rate:</Typography>
                        <Typography variant="body2">
                          {selectedQueue.processed && selectedQueue.failed 
                            ? `${((selectedQueue.processed / (selectedQueue.processed + selectedQueue.failed)) * 100).toFixed(1)}%`
                            : 'N/A'
                          }
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedQueue(null)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CeleryMonitor;