/**
 * Job Control Center - Real-time job monitoring and control
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  LinearProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  Schedule as ScheduleIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Timer as TimerIcon,
} from '@mui/icons-material';

import JobSchedulingModal from './JobSchedulingModal';

const JobControlCenter = ({ jobs, onRefresh, token }) => {
  const [selectedJob, setSelectedJob] = useState(null);
  const [jobDetails, setJobDetails] = useState(null);
  const [detailsDialog, setDetailsDialog] = useState(false);
  const [schedulingDialog, setSchedulingDialog] = useState(false);
  const [celeryTasks, setCeleryTasks] = useState([]);

  // Real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      fetchCeleryTasks();
    }, 3000); // Update every 3 seconds
    
    return () => clearInterval(interval);
  }, [token]);

  const fetchCeleryTasks = async () => {
    try {
      const response = await fetch('/api/v3/celery/active-tasks', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setCeleryTasks(data.active_tasks || []);
      }
    } catch (error) {
      console.error('Error fetching Celery tasks:', error);
    }
  };

  const fetchJobDetails = async (jobId) => {
    try {
      const response = await fetch(`/api/jobs/${jobId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setJobDetails(data);
        setDetailsDialog(true);
      }
    } catch (error) {
      console.error('Error fetching job details:', error);
    }
  };

  const getJobStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'running': return 'primary';
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'cancelled': return 'warning';
      case 'scheduled': return 'info';
      default: return 'default';
    }
  };

  const getJobStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'running': return <PlayIcon />;
      case 'completed': return <CheckCircleIcon />;
      case 'failed': return <ErrorIcon />;
      case 'cancelled': return <StopIcon />;
      case 'scheduled': return <ScheduleIcon />;
      default: return <TimerIcon />;
    }
  };

  const formatDuration = (startTime, endTime) => {
    if (!startTime) return 'N/A';
    
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = Math.floor((end - start) / 1000); // seconds
    
    if (duration < 60) return `${duration}s`;
    if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`;
    return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`;
  };

  const runningJobs = jobs.filter(job => job.status === 'running');
  const recentJobs = jobs.slice(0, 10); // Last 10 jobs

  return (
    <Box>
      {/* Status Overview */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="primary">
                {jobs.filter(j => j.status === 'running').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Running Jobs
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="success.main">
                {jobs.filter(j => j.status === 'completed').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Completed Today
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="error.main">
                {jobs.filter(j => j.status === 'failed').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Failed Jobs
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="info.main">
                {celeryTasks.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Active Celery Tasks
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Running Jobs Alert */}
      {runningJobs.length > 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="subtitle2">
            {runningJobs.length} job(s) currently running
          </Typography>
          {runningJobs.map(job => (
            <Chip
              key={job.id}
              label={`${job.name} (${formatDuration(job.started_at)})`}
              size="small"
              sx={{ mr: 1, mt: 1 }}
            />
          ))}
        </Alert>
      )}

      {/* Job Control Table */}
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Job Control Center</Typography>
            <Button
              startIcon={<RefreshIcon />}
              onClick={onRefresh}
              variant="outlined"
              size="small"
            >
              Refresh
            </Button>
          </Box>

          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Job</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Started</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {recentJobs.map((job) => (
                  <TableRow key={job.id}>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight="medium">
                          {job.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          ID: {job.id}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        icon={getJobStatusIcon(job.status)}
                        label={job.status}
                        color={getJobStatusColor(job.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {formatDuration(job.started_at, job.completed_at)}
                      </Typography>
                      {job.status === 'running' && (
                        <LinearProgress size="small" sx={{ mt: 0.5, width: 60 }} />
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {job.started_at ? new Date(job.started_at).toLocaleString() : 'Not started'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Tooltip title="View Details">
                        <IconButton
                          size="small"
                          onClick={() => fetchJobDetails(job.id)}
                        >
                          <ViewIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Schedule Job">
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => {
                            setSelectedJob(job);
                            setSchedulingDialog(true);
                          }}
                        >
                          <ScheduleIcon />
                        </IconButton>
                      </Tooltip>
                      {job.status === 'running' && (
                        <Tooltip title="Stop Job">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => {
                              // This would call the safety service to terminate
                              console.log('Stop job', job.id);
                            }}
                          >
                            <StopIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Job Details Dialog */}
      <Dialog
        open={detailsDialog}
        onClose={() => setDetailsDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Job Details</DialogTitle>
        <DialogContent>
          {jobDetails && (
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">Name</Typography>
                  <Typography variant="body2" gutterBottom>{jobDetails.name}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">Status</Typography>
                  <Chip
                    label={jobDetails.status}
                    color={getJobStatusColor(jobDetails.status)}
                    size="small"
                  />
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2">Description</Typography>
                  <Typography variant="body2" gutterBottom>
                    {jobDetails.description || 'No description'}
                  </Typography>
                </Grid>
                {jobDetails.executions && jobDetails.executions.length > 0 && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2">Recent Executions</Typography>
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Execution</TableCell>
                            <TableCell>Status</TableCell>
                            <TableCell>Started</TableCell>
                            <TableCell>Duration</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {jobDetails.executions.slice(0, 5).map((execution) => (
                            <TableRow key={execution.id}>
                              <TableCell>#{execution.execution_number}</TableCell>
                              <TableCell>
                                <Chip
                                  label={execution.status}
                                  color={getJobStatusColor(execution.status)}
                                  size="small"
                                />
                              </TableCell>
                              <TableCell>
                                {execution.started_at ? 
                                  new Date(execution.started_at).toLocaleString() : 
                                  'Not started'
                                }
                              </TableCell>
                              <TableCell>
                                {formatDuration(execution.started_at, execution.completed_at)}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Job Scheduling Modal */}
      <JobSchedulingModal
        open={schedulingDialog}
        onClose={() => {
          setSchedulingDialog(false);
          setSelectedJob(null);
        }}
        job={selectedJob}
        onSchedule={(schedule) => {
          console.log('Schedule created:', schedule);
          if (onRefresh) onRefresh();
        }}
        token={token}
      />
    </Box>
  );
};

export default JobControlCenter;