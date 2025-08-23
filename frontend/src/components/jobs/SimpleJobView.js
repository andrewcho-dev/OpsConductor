/**
 * Simple Job View - User-friendly interface for basic users
 * Clean, intuitive design focusing on essential job operations
 */
import React, { useState, useEffect } from 'react';
import { useSessionAuth } from '../../contexts/SessionAuthContext';
import { useAlert } from '../layout/BottomStatusBar';
import { apiService } from '../../services/apiService';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  Chip,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Tooltip,
  LinearProgress,
  Alert,
  Fab,
} from '@mui/material';

// Import the working job creation modal
import JobCreateModal from './JobCreateModal';
import {
  PlayArrow as PlayIcon,
  Schedule as ScheduleIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Pause as PauseIcon,
  AccessTime as AccessTimeIcon,
} from '@mui/icons-material';

const SimpleJobView = ({ jobs, onRefresh, stats }) => {
  const { token } = useSessionAuth();
  const { addAlert } = useAlert();
  
  const [selectedJob, setSelectedJob] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showScheduleDialog, setShowScheduleDialog] = useState(false);
  const [scheduleTime, setScheduleTime] = useState('');

  // Job creation handler
  const handleCreateJob = async (jobData) => {
    try {
      const response = await apiService.post(`/jobs/`, jobData);

      if (response.ok) {
        const newJob = await response.json();
        addAlert(`Job "${newJob.name}" created successfully!`, 'success', 3000);
        onRefresh(); // Refresh the job list
        return true;
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create job');
      }
    } catch (error) {
      addAlert(`Failed to create job: ${error.message}`, 'error', 5000);
      return false;
    }
  };

  // Job execution handler
  const handleExecuteJob = async (jobId) => {
    try {
      const response = await apiService.post(`/jobs/${jobId}/execute`, {});

      if (response.ok) {
        addAlert('Job execution started successfully!', 'success', 3000);
        onRefresh();
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to execute job');
      }
    } catch (error) {
      addAlert(`Failed to execute job: ${error.message}`, 'error', 5000);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'info';
      case 'failed': return 'error';
      case 'scheduled': return 'warning';
      case 'paused': return 'default';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon fontSize="small" />;
      case 'running': return <LinearProgress sx={{ width: 20, height: 4 }} />;
      case 'failed': return <ErrorIcon fontSize="small" />;
      case 'scheduled': return <AccessTimeIcon fontSize="small" />;
      case 'paused': return <PauseIcon fontSize="small" />;
      default: return null;
    }
  };

  const handleRunJob = async (job) => {
    try {
      // API call to run job immediately
      console.log('Running job:', job.name);
      onRefresh();
    } catch (error) {
      console.error('Error running job:', error);
    }
  };

  const handleScheduleJob = async () => {
    if (!selectedJob || !scheduleTime) return;
    
    try {
      // API call to schedule job
      console.log('Scheduling job:', selectedJob.name, 'for:', scheduleTime);
      setShowScheduleDialog(false);
      setSelectedJob(null);
      setScheduleTime('');
      onRefresh();
    } catch (error) {
      console.error('Error scheduling job:', error);
    }
  };



  const formatLastRun = (dateString) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    if (diffHours > 0) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffMins > 0) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    return 'Just now';
  };

  return (
    <Box sx={{ p: 2, height: '100%', overflow: 'auto' }}>
      {/* Quick Actions Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Your Jobs ({jobs.length})
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Refresh Jobs">
            <IconButton onClick={onRefresh} size="small">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setShowCreateModal(true)}
            size="small"
          >
            New Job
          </Button>
        </Box>
      </Box>

      {/* Success Rate Alert */}
      {stats.total > 0 && (
        <Alert 
          severity={stats.successRate > 80 ? 'success' : stats.successRate > 60 ? 'warning' : 'error'}
          sx={{ mb: 2 }}
        >
          <Typography variant="body2">
            <strong>{stats.successRate}% Success Rate</strong> - 
            {stats.completed} completed, {stats.failed} failed out of {stats.total} total jobs
          </Typography>
        </Alert>
      )}

      {/* Job List */}
      <Grid container spacing={2}>
        {jobs.length === 0 ? (
          <Grid item xs={12}>
            <Card sx={{ textAlign: 'center', py: 4 }}>
              <CardContent>
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  No Jobs Yet
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Create your first job to get started with automation
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => setShowCreateModal(true)}
                >
                  Create Your First Job
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ) : (
          jobs.map((job) => (
            <Grid item xs={12} sm={6} md={4} key={job.id}>
              <Card 
                sx={{ 
                  height: '100%',
                  transition: 'all 0.2s',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: 3,
                  }
                }}
              >
                <CardContent>
                  {/* Job Header */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600, mb: 0.5 }}>
                        {job.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {job.job_type?.toUpperCase()} • ID: {job.id}
                      </Typography>
                    </Box>
                    <Chip
                      icon={getStatusIcon(job.status)}
                      label={job.status}
                      color={getStatusColor(job.status)}
                      size="small"
                    />
                  </Box>

                  {/* Job Description */}
                  {job.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {job.description.length > 100 
                        ? `${job.description.substring(0, 100)}...` 
                        : job.description
                      }
                    </Typography>
                  )}

                  {/* Job Stats */}
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      Last run: {formatLastRun(job.last_execution_at)}
                    </Typography>
                    {job.scheduled_at && (
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        Next run: {(() => {
                          // Backend sends UTC times, handle them properly
                          const dateString = job.scheduled_at;
                          if (!dateString.endsWith('Z') && !dateString.includes('+') && !dateString.includes('-')) {
                            // Treat as UTC and convert to local time for display
                            const utcDate = new Date(dateString + 'Z');
                            return utcDate.toLocaleString();
                          }
                          return new Date(dateString).toLocaleString();
                        })()}
                      </Typography>
                    )}
                  </Box>

                  {/* Action Buttons */}
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Button
                      size="small"
                      variant="contained"
                      startIcon={<PlayIcon />}
                      onClick={() => handleExecuteJob(job.id)}
                      disabled={job.status === 'running'}
                      sx={{ flex: 1, minWidth: 'auto' }}
                    >
                      Run Now
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<ScheduleIcon />}
                      onClick={() => {
                        setSelectedJob(job);
                        setShowScheduleDialog(true);
                      }}
                      sx={{ flex: 1, minWidth: 'auto' }}
                    >
                      Schedule
                    </Button>
                  </Box>

                  {/* Secondary Actions */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <Tooltip title="View Details">
                        <IconButton size="small" onClick={() => setSelectedJob(job)}>
                          <ViewIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit Job">
                        <IconButton size="small">
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                    <Tooltip title="Delete Job">
                      <IconButton size="small" color="error">
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))
        )}
      </Grid>

      {/* Real Job Creation Modal with Target Selection */}
      <JobCreateModal
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreateJob={handleCreateJob}
      />

      {/* Schedule Job Dialog */}
      <Dialog open={showScheduleDialog} onClose={() => setShowScheduleDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Schedule Job: {selectedJob?.name}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <TextField
              label="Schedule Time"
              type="datetime-local"
              value={scheduleTime}
              onChange={(e) => setScheduleTime(e.target.value)}
              fullWidth
              InputLabelProps={{ shrink: true }}
              inputProps={{
                min: new Date().toISOString().slice(0, 16)
              }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowScheduleDialog(false)}>Cancel</Button>
          <Button onClick={handleScheduleJob} variant="contained">Schedule</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SimpleJobView;