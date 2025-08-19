/**
 * Celery Monitor Page - Consolidated single-page monitoring with visual balancing
 * Consolidates all tabs into sections following SystemSettings visual pattern
 */
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
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
  Work as WorkIcon,
  Timer as TimerIcon,
  Settings as SettingsIcon,
  Visibility as ViewIcon,
  Group as GroupIcon,
  ToggleOn as ToggleOnIcon,
  ToggleOff as ToggleOffIcon,
  MonitorHeart as MonitorHeartIcon,
  DataObject as DataObjectIcon,
} from '@mui/icons-material';
import { useSessionAuth } from '../../contexts/SessionAuthContext';
import { useAlert } from '../layout/BottomStatusBar';
import MetricsChart from './MetricsChart';
import '../../styles/dashboard.css';

const CeleryMonitorPage = () => {
  const { token } = useSessionAuth();
  const { addAlert } = useAlert();
  
  // State management
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  
  // Data state
  const [celeryStats, setCeleryStats] = useState({});
  const [queueStats, setQueueStats] = useState({});
  const [workerStats, setWorkerStats] = useState({});
  const [metricsHistory, setMetricsHistory] = useState(null);
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  
  // Modal state
  const [selectedWorker, setSelectedWorker] = useState(null);
  const [selectedQueue, setSelectedQueue] = useState(null);

  // Auto-refresh effect
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => fetchMonitoringData(false), 10000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  // Initial data fetch
  useEffect(() => {
    if (token) {
      fetchMonitoringData(true);
      fetchMetricsHistory();
    }
  }, [token]);

  const fetchMonitoringData = async (isInitialLoad = false) => {
    try {
      if (isInitialLoad) {
        setLoading(true);
      } else {
        setRefreshing(true);
      }
      setError(null);

      // Fetch all monitoring data in parallel
      const [celeryResponse, queueResponse, workerResponse] = await Promise.all([
        fetch('/api/v3/celery/stats', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }),
        fetch('/api/v3/celery/queues', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }),
        fetch('/api/v3/celery/workers', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })
      ]);

      // Process responses
      if (celeryResponse.ok) {
        const celeryData = await celeryResponse.json();
        setCeleryStats(celeryData);
      }

      if (queueResponse.ok) {
        const queueData = await queueResponse.json();
        setQueueStats(queueData.queues || {});
      }

      if (workerResponse.ok) {
        const workerData = await workerResponse.json();
        // Convert workers object to array
        const workersObj = workerData.workers || {};
        const workers = Object.values(workersObj);
        setWorkerStats({
          workers: workers,
          total_workers: workers.length,
          active_workers: workers.filter(w => w.status === "online").length,
          busy_workers: workers.filter(w => w.active_tasks > 0).length,
          avg_load: workers.reduce((sum, w) => sum + (w.load_avg || 0), 0) / Math.max(workers.length, 1)
        });
      }

      setLastUpdated(new Date());
      
    } catch (error) {
      console.error('Error fetching monitoring data:', error);
      setError(`Failed to load monitoring data: ${error.message}`);
      addAlert('Failed to load Celery monitoring data', 'error', 5000);
    } finally {
      if (isInitialLoad) {
        setLoading(false);
      } else {
        setRefreshing(false);
      }
    }
  };

  const fetchMetricsHistory = async () => {
    setLoadingMetrics(true);
    try {
      const response = await fetch('/api/v3/celery/metrics/history?hours=24', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('📊 Raw metrics data:', data);
        
        // Transform data for MetricsChart component
        if (data.metrics && data.metrics.length > 0) {
          const transformedData = {
            ...data,
            // Add chart-ready data for completed tasks
            completedTasksChart: {
              timestamps: data.metrics.map(m => m.timestamp),
              values: data.metrics.map(m => m.completed_tasks || 0)
            },
            // Add chart-ready data for failed tasks  
            failedTasksChart: {
              timestamps: data.metrics.map(m => m.timestamp),
              values: data.metrics.map(m => m.failed_tasks || 0)
            },
            // Add summary statistics
            summary: {
              total_completed: data.metrics.reduce((sum, m) => sum + (m.completed_tasks || 0), 0),
              total_failed: data.metrics.reduce((sum, m) => sum + (m.failed_tasks || 0), 0),
              avg_load: data.metrics.reduce((sum, m) => sum + (m.success_rate || 0), 0) / data.metrics.length
            }
          };
          console.log('📈 Transformed metrics data:', transformedData);
          setMetricsHistory(transformedData);
        } else {
          console.log('⚠️ No metrics data available');
          setMetricsHistory(data);
        }
      } else {
        console.error('Failed to fetch metrics history');
      }
    } catch (error) {
      console.error('Error fetching metrics history:', error);
    } finally {
      setLoadingMetrics(false);
    }
  };

  // Helper functions
  const getWorkerStatus = (worker) => {
    if (worker.status !== "online") return { status: 'offline', color: 'error' };
    if (worker.active_tasks > 10) return { status: 'busy', color: 'warning' }; // Simplified threshold
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

  // Calculate comprehensive statistics for the 6-column grid
  const stats = {
    // Workers
    total_workers: workerStats.total_workers || 0,
    active_workers: workerStats.active_workers || 0,
    // Queues
    total_queues: Object.keys(queueStats).length || 0,
    pending_tasks: Object.values(queueStats).reduce((sum, q) => sum + (q.pending || 0), 0),
    // Tasks
    active_tasks: celeryStats.active_tasks || 0,
    completed_tasks: celeryStats.completed_tasks || 0
  };

  if (loading) {
    return (
      <div className="dashboard-container">
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
          <CircularProgress />
          <Typography variant="h6" sx={{ ml: 2 }}>Loading Celery monitoring data...</Typography>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-container">
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Typography variant="body2" color="text.secondary">
          Please check that the Celery workers are running and the monitoring endpoints are accessible.
        </Typography>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      {/* Compact Page Header - Following Design Guidelines */}
      <div className="page-header">
        <Typography className="page-title">
          Celery Monitor
        </Typography>
        <div className="page-actions">
          {lastUpdated && (
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
              Last updated: {lastUpdated.toLocaleTimeString()}
            </Typography>
          )}
          <Button
            className="btn-compact"
            size="small"
            variant={autoRefresh ? "contained" : "outlined"}
            startIcon={autoRefresh ? <ToggleOnIcon fontSize="small" /> : <ToggleOffIcon fontSize="small" />}
            onClick={() => setAutoRefresh(!autoRefresh)}
            color={autoRefresh ? "success" : "primary"}
          >
            Auto-refresh {autoRefresh ? 'ON' : 'OFF'}
          </Button>
          <Tooltip title="Refresh monitoring data">
            <IconButton 
              className="btn-icon" 
              onClick={() => fetchMonitoringData(false)} 
              disabled={refreshing}
              size="small"
            >
              <RefreshIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </div>
      </div>

      {/* Enhanced Statistics Grid - Following Design Guidelines */}
      <div className="stats-grid">
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon primary">
              <ComputerIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.total_workers}</h3>
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
              <h3>{stats.active_workers}</h3>
              <p>Active Workers</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon info">
              <QueueIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.total_queues}</h3>
              <p>Total Queues</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className={`stat-icon ${stats.pending_tasks > 100 ? 'error' : stats.pending_tasks > 50 ? 'warning' : 'success'}`}>
              <TimerIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.pending_tasks}</h3>
              <p>Pending Tasks</p>
            </div>
          </div>
        </div>

        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon warning">
              <WorkIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.active_tasks}</h3>
              <p>Active Tasks</p>
            </div>
          </div>
        </div>

        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon secondary">
              <TrendingUpIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.completed_tasks}</h3>
              <p>Completed Today</p>
            </div>
          </div>
        </div>
      </div>

      {/* Workers & Queues - Side by Side */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 3fr', gap: '16px', marginBottom: '16px' }}>
        
        {/* Workers Section */}
        <div className="main-content-card fade-in">
          <div className="content-card-header">
            <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
              <ComputerIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
              WORKER STATUS
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
              {workerStats.active_workers || 0} active, {workerStats.busy_workers || 0} busy
            </Typography>
          </div>
          
          <div className="content-card-body">
            {workerStats.workers && workerStats.workers.length > 0 ? (
              <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ fontSize: '0.75rem', fontWeight: 600 }}>Worker</TableCell>
                        <TableCell sx={{ fontSize: '0.75rem', fontWeight: 600 }}>Status</TableCell>
                        <TableCell sx={{ fontSize: '0.75rem', fontWeight: 600 }}>Tasks</TableCell>
                        <TableCell sx={{ fontSize: '0.75rem', fontWeight: 600 }}>Load</TableCell>
                        <TableCell sx={{ fontSize: '0.75rem', fontWeight: 600 }}>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {workerStats.workers.map((worker) => {
                        const status = getWorkerStatus(worker);
                        return (
                          <TableRow key={worker.name} hover>
                            <TableCell>
                              <Box>
                                <Typography variant="body2" sx={{ fontWeight: 500, fontSize: '0.75rem' }}>
                                  {worker.name}
                                </Typography>
                                <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.65rem' }}>
                                  {worker.hostname}
                                </Typography>
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Chip 
                                label={status.status} 
                                color={status.color} 
                                size="small"
                                sx={{ fontSize: '0.65rem', height: '20px' }}
                              />
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                                {worker.active_tasks || 0}/{worker.pool_size || 0}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                                  {worker.load_avg || 0}%
                                </Typography>
                                <LinearProgress
                                  variant="determinate"
                                  value={worker.load_avg || 0}
                                  sx={{ width: 30, height: 4 }}
                                  color={worker.load_avg > 80 ? 'error' : worker.load_avg > 60 ? 'warning' : 'primary'}
                                />
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Tooltip title="View Details">
                                <IconButton size="small" onClick={() => setSelectedWorker(worker)}>
                                  <ViewIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>
              </div>
            ) : (
              <Typography variant="body2" sx={{ fontSize: '0.8rem', color: 'text.secondary' }}>
                No worker data available
              </Typography>
            )}
          </div>
        </div>

        {/* Queues Section */}
        <div className="main-content-card fade-in">
          <div className="content-card-header">
            <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
              <QueueIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
              QUEUE STATUS
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
              {Object.keys(queueStats).length} queues, {stats.pending_tasks} pending
            </Typography>
          </div>
          
          <div className="content-card-body">
            {Object.keys(queueStats).length > 0 ? (
              <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ fontSize: '0.75rem', fontWeight: 600 }}>Queue</TableCell>
                        <TableCell sx={{ fontSize: '0.75rem', fontWeight: 600 }}>Health</TableCell>
                        <TableCell sx={{ fontSize: '0.75rem', fontWeight: 600 }}>Pending</TableCell>
                        <TableCell sx={{ fontSize: '0.75rem', fontWeight: 600 }}>Processing</TableCell>
                        <TableCell sx={{ fontSize: '0.75rem', fontWeight: 600 }}>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(queueStats).map(([name, queue]) => {
                        const health = getQueueHealth(queue);
                        return (
                          <TableRow key={name} hover>
                            <TableCell>
                              <Typography variant="body2" sx={{ fontWeight: 500, fontSize: '0.75rem' }}>
                                {name}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip 
                                label={health.status} 
                                color={health.color} 
                                size="small"
                                sx={{ fontSize: '0.65rem', height: '20px' }}
                              />
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                                {queue.pending || 0}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                                {queue.processing || 0}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Tooltip title="View Details">
                                <IconButton size="small" onClick={() => setSelectedQueue({ name, ...queue })}>
                                  <ViewIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>
              </div>
            ) : (
              <Typography variant="body2" sx={{ fontSize: '0.8rem', color: 'text.secondary' }}>
                No queue data available
              </Typography>
            )}
          </div>
        </div>
      </div>

      {/* Task Monitoring & Performance Metrics - Side by Side */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 3fr', gap: '16px', marginBottom: '16px' }}>
        
        {/* Task Monitoring Section */}
        <div className="main-content-card fade-in">
          <div className="content-card-header">
            <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
              <WorkIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
              TASK MONITORING
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
              Real-time task processing statistics
            </Typography>
          </div>
          
          <div className="content-card-body">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
            
            {/* Active Tasks */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                <WorkIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                Active Tasks
              </Typography>
              <Typography variant="h4" sx={{ fontSize: '1.5rem', fontWeight: 600, mb: 0.5 }}>
                {celeryStats.active_tasks || 0}
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                Currently processing
              </Typography>
            </div>

            {/* Tasks per Minute */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                <SpeedIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                Throughput
              </Typography>
              <Typography variant="h4" sx={{ fontSize: '1.5rem', fontWeight: 600, mb: 0.5 }}>
                {celeryStats.tasks_per_minute || 0}
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                Tasks per minute
              </Typography>
            </div>

            {/* Average Duration */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                <TimelineIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                Avg Duration
              </Typography>
              <Typography variant="h4" sx={{ fontSize: '1.5rem', fontWeight: 600, mb: 0.5 }}>
                {celeryStats.avg_task_time || 0}s
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                Average task time
              </Typography>
            </div>
            </div>

            {/* Task Status Summary */}
            <div style={{ marginTop: '16px', padding: '12px', backgroundColor: 'rgba(0,0,0,0.02)', borderRadius: '6px' }}>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                Task Status Summary
              </Typography>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                <div style={{ textAlign: 'center' }}>
                  <Typography variant="body2" sx={{ fontSize: '0.8rem', fontWeight: 600, color: 'success.main' }}>
                    {celeryStats.completed_tasks || 0}
                  </Typography>
                  <Typography variant="caption" sx={{ fontSize: '0.65rem' }}>Completed</Typography>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <Typography variant="body2" sx={{ fontSize: '0.8rem', fontWeight: 600, color: 'error.main' }}>
                    {celeryStats.failed_tasks || 0}
                  </Typography>
                  <Typography variant="caption" sx={{ fontSize: '0.65rem' }}>Failed</Typography>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <Typography variant="body2" sx={{ fontSize: '0.8rem', fontWeight: 600, color: 'warning.main' }}>
                    {celeryStats.pending_tasks || 0}
                  </Typography>
                  <Typography variant="caption" sx={{ fontSize: '0.65rem' }}>Pending</Typography>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Performance Metrics Section */}
        <div className="main-content-card fade-in">
          <div className="content-card-header">
            <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
              <TrendingUpIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
              PERFORMANCE METRICS
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
              24-hour performance overview
            </Typography>
          </div>
          
          <div className="content-card-body">
            {loadingMetrics ? (
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px' }}>
                <CircularProgress size={24} />
                <Typography variant="body2" sx={{ ml: 2, fontSize: '0.8rem' }}>Loading metrics...</Typography>
              </div>
            ) : metricsHistory ? (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
              
              {/* Peak Throughput */}
              <div>
                <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                  <TrendingUpIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Peak Throughput
                </Typography>
                <Typography variant="h4" sx={{ fontSize: '1.5rem', fontWeight: 600, mb: 0.5 }}>
                  {metricsHistory.summary?.peak_throughput || 0}
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                  Tasks per minute
                </Typography>
              </div>

              {/* Success Rate */}
              <div>
                <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                  <CheckCircleIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Success Rate
                </Typography>
                <Typography variant="h4" sx={{ fontSize: '1.5rem', fontWeight: 600, mb: 0.5 }}>
                  {metricsHistory.summary?.success_rate || 0}%
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                  Task success rate
                </Typography>
              </div>

              {/* Average Load */}
              <div>
                <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                  <SpeedIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Avg Load
                </Typography>
                <Typography variant="h4" sx={{ fontSize: '1.5rem', fontWeight: 600, mb: 0.5 }}>
                  {metricsHistory.summary?.avg_load || 0}%
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                  Worker load average
                </Typography>
              </div>
              </div>
            ) : (
              <Typography variant="body2" sx={{ fontSize: '0.8rem', color: 'text.secondary' }}>
                No metrics data available
              </Typography>
            )}

            {/* Metrics Chart */}
            {metricsHistory && metricsHistory.completedTasksChart && (
              <div style={{ marginTop: '16px' }}>
                <MetricsChart 
                  title="Completed Tasks" 
                  data={metricsHistory.completedTasksChart} 
                  color="rgb(75, 192, 192)"
                />
              </div>
            )}
            
            {/* Failed Tasks Chart */}
            {metricsHistory && metricsHistory.failedTasksChart && (
              <div style={{ marginTop: '8px' }}>
                <MetricsChart 
                  title="Failed Tasks" 
                  data={metricsHistory.failedTasksChart} 
                  color="rgb(255, 99, 132)"
                />
              </div>
            )}
          </div>
        </div>
      </div>

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
                <Paper sx={{ p: 2 }}>
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
                </Paper>
              </Grid>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>Performance Metrics</Typography>
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
                </Paper>
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
                <Paper sx={{ p: 2 }}>
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
                </Paper>
              </Grid>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2 }}>
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
                </Paper>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedQueue(null)}>Close</Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default CeleryMonitorPage;