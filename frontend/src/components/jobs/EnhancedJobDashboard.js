/**
 * Enhanced Job Dashboard - Modern Celery Interface
 * Features both Simple and Advanced modes for different user types
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
  Card,
  CardContent,
  Grid,
  Chip,
  LinearProgress,
  Alert,
  Fab,
  Badge,
  Divider,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Schedule as ScheduleIcon,
  Visibility as ViewIcon,
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Timeline as TimelineIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Queue as QueueIcon,
  Work as WorkIcon,
  Group as GroupIcon,
  Analytics as AnalyticsIcon,
} from '@mui/icons-material';

import { useSessionAuth } from '../../contexts/SessionAuthContext';
import { apiService } from '../../services/apiService';
import { useAlert } from '../layout/BottomStatusBar';

// Import sub-components
import SimpleJobView from './SimpleJobView';
import AdvancedJobView from './AdvancedJobView';
import CeleryMonitor from './CeleryMonitor';
import JobSafetyControls from './JobSafetyControls';
import JobControlCenter from './JobControlCenter';
// import JobWorkflowBuilder from './JobWorkflowBuilder'; // TODO: Create this component
// import JobAnalytics from './JobAnalytics'; // TODO: Create this component

const EnhancedJobDashboard = () => {
  const { token } = useSessionAuth();
  const { addAlert } = useAlert();
  
  // State management
  const [isAdvancedMode, setIsAdvancedMode] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [jobs, setJobs] = useState([]);
  const [celeryStats, setCeleryStats] = useState({});
  const [queueStats, setQueueStats] = useState({});
  const [workerStats, setWorkerStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [realTimeUpdates, setRealTimeUpdates] = useState(true);

  // Real-time updates
  useEffect(() => {
    if (realTimeUpdates) {
      const interval = setInterval(() => {
        fetchAllData();
      }, 5000); // Update every 5 seconds
      
      return () => clearInterval(interval);
    }
  }, [realTimeUpdates, token]);

  useEffect(() => {
    if (token) {
      fetchAllData();
    }
  }, [token]);

  const fetchAllData = async () => {
    await Promise.all([
      fetchJobs(),
      fetchCeleryStats(),
      fetchQueueStats(),
      fetchWorkerStats(),
    ]);
  };

  const fetchJobs = async () => {
    try {
      const response = await apiService.get('/api/v3/jobs/');
      if (response.ok) {
        const data = await response.json();
        setJobs(data || []);
      } else {
        console.error('Failed to fetch jobs:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Error fetching jobs:', error);
      // If it's an authentication error, the apiService will handle logout
      // Just log the error here and let the auth system handle the redirect
    }
  };

  const fetchCeleryStats = async () => {
    try {
      const response = await apiService.get('/api/celery/stats');
      if (response.ok) {
        const data = await response.json();
        setCeleryStats(data);
      }
    } catch (error) {
      console.error('Error fetching Celery stats:', error);
    }
  };

  const fetchQueueStats = async () => {
    try {
      const response = await apiService.get('/api/celery/queues');
      if (response.ok) {
        const data = await response.json();
        setQueueStats(data);
      }
    } catch (error) {
      console.error('Error fetching queue stats:', error);
    }
  };

  const fetchWorkerStats = async () => {
    try {
      const response = await apiService.get('/api/celery/workers');
      if (response.ok) {
        const data = await response.json();
        setWorkerStats(data);
      }
    } catch (error) {
      console.error('Error fetching worker stats:', error);
    } finally {
      setLoading(false);
    }
  };

  // Calculate comprehensive statistics
  const getJobStats = () => {
    const stats = {
      total: jobs.length,
      running: jobs.filter(j => j.status === 'running').length,
      completed: jobs.filter(j => j.status === 'completed').length,
      failed: jobs.filter(j => j.status === 'failed').length,
      scheduled: jobs.filter(j => j.status === 'scheduled').length,
      paused: jobs.filter(j => j.status === 'paused').length,
    };
    
    stats.successRate = stats.total > 0 ? 
      Math.round(((stats.completed) / (stats.completed + stats.failed)) * 100) || 0 : 0;
    
    return stats;
  };

  const getCeleryHealth = () => {
    const activeWorkers = workerStats.active_workers || 0;
    const totalQueues = Object.keys(queueStats).length;
    const pendingTasks = Object.values(queueStats).reduce((sum, queue) => sum + (queue.pending || 0), 0);
    
    return {
      status: activeWorkers > 0 ? 'healthy' : 'warning',
      activeWorkers,
      totalQueues,
      pendingTasks,
      avgTaskTime: celeryStats.avg_task_time || 0,
      taskThroughput: celeryStats.tasks_per_minute || 0,
    };
  };

  const stats = getJobStats();
  const health = getCeleryHealth();

  const tabLabels = isAdvancedMode ? 
    ['Jobs', 'Control Center', 'Monitor', 'Workflows', 'Analytics', 'Settings'] :
    ['Jobs', 'Control Center', 'History', 'Settings'];

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Enhanced Header */}
      <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="h5" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
              <WorkIcon color="primary" />
              Job Management
            </Typography>
            
            {/* Real-time Health Indicator */}
            <Chip
              icon={health.status === 'healthy' ? <CheckCircleIcon /> : <WarningIcon />}
              label={`${health.activeWorkers} Workers Active`}
              color={health.status === 'healthy' ? 'success' : 'warning'}
              size="small"
            />
            
            {/* Pending Tasks Indicator */}
            {health.pendingTasks > 0 && (
              <Badge badgeContent={health.pendingTasks} color="primary">
                <QueueIcon color="action" />
              </Badge>
            )}
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {/* Real-time Updates Toggle */}
            <FormControlLabel
              control={
                <Switch
                  checked={realTimeUpdates}
                  onChange={(e) => setRealTimeUpdates(e.target.checked)}
                  size="small"
                />
              }
              label="Live Updates"
              sx={{ fontSize: '0.8rem' }}
            />
            
            {/* Simple/Advanced Mode Toggle */}
            <FormControlLabel
              control={
                <Switch
                  checked={isAdvancedMode}
                  onChange={(e) => setIsAdvancedMode(e.target.checked)}
                />
              }
              label="Advanced Mode"
            />
            
            <Tooltip title="Refresh All Data">
              <IconButton onClick={fetchAllData} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Quick Stats Row */}
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={2}>
            <Card variant="outlined" sx={{ textAlign: 'center', p: 1 }}>
              <Typography variant="h6" color="primary">{stats.total}</Typography>
              <Typography variant="caption">Total Jobs</Typography>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Card variant="outlined" sx={{ textAlign: 'center', p: 1 }}>
              <Typography variant="h6" color="info.main">{stats.running}</Typography>
              <Typography variant="caption">Running</Typography>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Card variant="outlined" sx={{ textAlign: 'center', p: 1 }}>
              <Typography variant="h6" color="success.main">{stats.completed}</Typography>
              <Typography variant="caption">Completed</Typography>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Card variant="outlined" sx={{ textAlign: 'center', p: 1 }}>
              <Typography variant="h6" color="error.main">{stats.failed}</Typography>
              <Typography variant="caption">Failed</Typography>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Card variant="outlined" sx={{ textAlign: 'center', p: 1 }}>
              <Typography variant="h6" color="warning.main">{stats.scheduled}</Typography>
              <Typography variant="caption">Scheduled</Typography>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Card variant="outlined" sx={{ textAlign: 'center', p: 1 }}>
              <Typography variant="h6" color="success.main">{stats.successRate}%</Typography>
              <Typography variant="caption">Success Rate</Typography>
            </Card>
          </Grid>
        </Grid>

        {/* Advanced Stats (only in advanced mode) */}
        {isAdvancedMode && (
          <Box sx={{ mt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={3}>
                <Card variant="outlined" sx={{ p: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <SpeedIcon color="primary" fontSize="small" />
                    <Typography variant="subtitle2">Throughput</Typography>
                  </Box>
                  <Typography variant="h6">{health.taskThroughput}</Typography>
                  <Typography variant="caption" color="text.secondary">tasks/minute</Typography>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card variant="outlined" sx={{ p: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <TimelineIcon color="primary" fontSize="small" />
                    <Typography variant="subtitle2">Avg Task Time</Typography>
                  </Box>
                  <Typography variant="h6">{health.avgTaskTime}s</Typography>
                  <Typography variant="caption" color="text.secondary">average duration</Typography>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card variant="outlined" sx={{ p: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <QueueIcon color="primary" fontSize="small" />
                    <Typography variant="subtitle2">Queue Depth</Typography>
                  </Box>
                  <Typography variant="h6">{health.pendingTasks}</Typography>
                  <Typography variant="caption" color="text.secondary">pending tasks</Typography>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card variant="outlined" sx={{ p: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <GroupIcon color="primary" fontSize="small" />
                    <Typography variant="subtitle2">Worker Pool</Typography>
                  </Box>
                  <Typography variant="h6">{health.activeWorkers}</Typography>
                  <Typography variant="caption" color="text.secondary">active workers</Typography>
                </Card>
              </Grid>
            </Grid>
          </Box>
        )}
      </Paper>

      {/* Navigation Tabs */}
      <Paper elevation={1} sx={{ mb: 2 }}>
        <Tabs
          value={activeTab}
          onChange={(e, newValue) => setActiveTab(newValue)}
          variant="scrollable"
          scrollButtons="auto"
        >
          {tabLabels.map((label, index) => (
            <Tab key={index} label={label} />
          ))}
        </Tabs>
      </Paper>

      {/* Job Safety Controls */}
      <JobSafetyControls onRefresh={fetchAllData} token={token} />

      {/* Tab Content */}
      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        {/* Simple Mode Tabs */}
        {!isAdvancedMode && (
          <>
            {activeTab === 0 && (
              <SimpleJobView 
                jobs={jobs}
                onRefresh={fetchJobs}
                stats={stats}
              />
            )}
            {activeTab === 1 && (
              <JobControlCenter 
                jobs={jobs}
                onRefresh={fetchAllData}
                token={token}
              />
            )}
            {activeTab === 2 && (
              <Box sx={{ p: 2 }}>
                <Typography variant="h6">Job History</Typography>
                {/* Job history component */}
              </Box>
            )}
            {activeTab === 3 && (
              <Box sx={{ p: 2 }}>
                <Typography variant="h6">Settings</Typography>
                {/* Settings component */}
              </Box>
            )}
          </>
        )}

        {/* Advanced Mode Tabs */}
        {isAdvancedMode && (
          <>
            {activeTab === 0 && (
              <AdvancedJobView 
                jobs={jobs}
                onRefresh={fetchJobs}
                stats={stats}
                celeryStats={celeryStats}
              />
            )}
            {activeTab === 1 && (
              <JobControlCenter 
                jobs={jobs}
                onRefresh={fetchAllData}
                token={token}
              />
            )}
            {activeTab === 2 && (
              <CeleryMonitor 
                celeryStats={celeryStats}
                queueStats={queueStats}
                workerStats={workerStats}
                onRefresh={fetchAllData}
              />
            )}
            {activeTab === 3 && (
              <Box sx={{ p: 3, textAlign: 'center' }}>
                <WorkIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
                <Typography variant="h5" gutterBottom>
                  Job Workflow Builder
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                  Advanced job workflow and dependency management coming soon!
                </Typography>
                <Alert severity="info">
                  This feature will allow you to create complex job workflows with dependencies, 
                  conditional execution, and advanced scheduling patterns.
                </Alert>
              </Box>
            )}
            {activeTab === 4 && (
              <Box sx={{ p: 3, textAlign: 'center' }}>
                <AnalyticsIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
                <Typography variant="h5" gutterBottom>
                  Job Analytics
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                  Comprehensive job performance analytics and reporting coming soon!
                </Typography>
                <Alert severity="info">
                  This feature will provide detailed insights into job performance, 
                  success rates, execution patterns, and resource utilization.
                </Alert>
              </Box>
            )}
            {activeTab === 5 && (
              <Box sx={{ p: 2 }}>
                <Typography variant="h6">Advanced Settings</Typography>
                {/* Advanced settings component */}
              </Box>
            )}
          </>
        )}
      </Box>

      {/* Floating Action Button */}
      <Fab
        color="primary"
        aria-label="add job"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={() => {
          // Open job creation modal
        }}
      >
        <AddIcon />
      </Fab>
    </Box>
  );
};

export default EnhancedJobDashboard;