/**
 * Advanced Job View - Power user interface with full Celery features
 * Exposes advanced scheduling, retry logic, priorities, and monitoring
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useAlert } from '../layout/BottomStatusBar';
import JobCreateModal from './JobCreateModal';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  Chip,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  Badge,
  LinearProgress,
  Alert,
  Tabs,
  Tab,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Slider,
  Checkbox,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  PlayArrow as PlayIcon,
  Schedule as ScheduleIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  PriorityHigh as PriorityIcon,
  Repeat as RepeatIcon,
  Timer as TimerIcon,
  Speed as SpeedIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Timeline as TimelineIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Queue as QueueIcon,
  Group as GroupIcon,
  Code as CodeIcon,
  DataObject as DataObjectIcon,
} from '@mui/icons-material';

const AdvancedJobView = ({ jobs, onRefresh, stats, celeryStats }) => {
  const [selectedJobs, setSelectedJobs] = useState([]);
  const [showAdvancedCreate, setShowAdvancedCreate] = useState(false);
  const [showBulkActions, setShowBulkActions] = useState(false);
  const [viewMode, setViewMode] = useState('table'); // 'table', 'cards', 'timeline'
  const [filterStatus, setFilterStatus] = useState('all');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  
  const [advancedJob, setAdvancedJob] = useState({
    name: '',
    job_type: 'shell',
    commands: '',
    description: '',
    priority: 5,
    max_retries: 3,
    retry_delay: 60,
    timeout: 300,
    queue: 'default',
    routing_key: '',
    expires: '',
    eta: '',
    countdown: '',
    soft_time_limit: 0,
    time_limit: 0,
    rate_limit: '',
    ignore_result: false,
    store_errors_even_if_ignored: false,
    serializer: 'json',
    compression: 'none',
    bind: false,
    autoretry_for: [],
    retry_kwargs: {},
    retry_jitter: true,
    retry_backoff: false,
    retry_backoff_max: 600,
    acks_late: false,
    reject_on_worker_lost: false,
    trail: true,
    send_events: true,
    task_track_started: true,
    task_publish_retry: true,
    task_publish_retry_policy: {},
    worker_prefetch_multiplier: 1,
    task_inherit_parent_priority: true,
    task_default_priority: 5,
    task_default_queue: 'celery',
    task_default_exchange: 'celery',
    task_default_exchange_type: 'direct',
    task_default_routing_key: 'celery',
    task_default_delivery_mode: 2,
    task_compression: 'none',
    task_serializer: 'json',
    result_serializer: 'json',
    accept_content: ['json'],
    result_accept_content: ['json'],
    result_compression: 'none',
    result_expires: 3600,
    result_persistent: false,
    result_backend_transport_options: {},
    cache_backend_options: {},
    task_send_sent_event: false,
    worker_send_task_events: false,
    task_send_events: false,
    monitor_events: false,
    worker_hijack_root_logger: true,
    worker_log_color: false,
    worker_log_format: '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format: '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
    worker_timer_precision: 1.0,
    worker_enable_remote_control: true,
    worker_send_task_events: false,
    worker_prefetch_multiplier: 1,
    worker_max_tasks_per_child: 1000,
    worker_max_memory_per_child: 0,
    worker_disable_rate_limits: false,
    worker_state_db: '',
    worker_timer_precision: 1.0,
    worker_enable_remote_control: true,
    beat_schedule: {},
    beat_scheduler: 'celery.beat:PersistentScheduler',
    beat_schedule_filename: 'celerybeat-schedule',
    beat_sync_every: 0,
    beat_max_loop_interval: 0,
    timezone: 'UTC',
    enable_utc: true,
  });

  const filteredJobs = jobs.filter(job => {
    if (filterStatus === 'all') return true;
    return job.status === filterStatus;
  });

  const sortedJobs = [...filteredJobs].sort((a, b) => {
    const aVal = a[sortBy];
    const bVal = b[sortBy];
    const order = sortOrder === 'asc' ? 1 : -1;
    
    if (aVal < bVal) return -1 * order;
    if (aVal > bVal) return 1 * order;
    return 0;
  });

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'info';
      case 'failed': return 'error';
      case 'scheduled': return 'warning';
      case 'paused': return 'default';
      case 'retrying': return 'warning';
      case 'revoked': return 'error';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority) => {
    if (priority >= 8) return 'error';
    if (priority >= 6) return 'warning';
    if (priority >= 4) return 'info';
    return 'success';
  };

  const handleBulkAction = (action) => {
    console.log(`Bulk ${action} for jobs:`, selectedJobs);
    // Implement bulk actions
  };

  const handleAdvancedSchedule = (job) => {
    // Open advanced scheduling dialog
    console.log('Advanced schedule for:', job);
  };

  const handleCloneJob = (job) => {
    setAdvancedJob({ ...job, name: `${job.name} (Copy)` });
    setShowAdvancedCreate(true);
  };

  const renderTableView = () => (
    <TableContainer component={Paper}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell padding="checkbox">
              <Checkbox
                indeterminate={selectedJobs.length > 0 && selectedJobs.length < jobs.length}
                checked={jobs.length > 0 && selectedJobs.length === jobs.length}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedJobs(jobs.map(j => j.id));
                  } else {
                    setSelectedJobs([]);
                  }
                }}
              />
            </TableCell>
            <TableCell>Name</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Priority</TableCell>
            <TableCell>Queue</TableCell>
            <TableCell>Last Run</TableCell>
            <TableCell>Next Run</TableCell>
            <TableCell>Success Rate</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {sortedJobs.map((job) => (
            <TableRow key={job.id} hover>
              <TableCell padding="checkbox">
                <Checkbox
                  checked={selectedJobs.includes(job.id)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedJobs([...selectedJobs, job.id]);
                    } else {
                      setSelectedJobs(selectedJobs.filter(id => id !== job.id));
                    }
                  }}
                />
              </TableCell>
              <TableCell>
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    {job.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    ID: {job.id}
                  </Typography>
                </Box>
              </TableCell>
              <TableCell>
                <Chip label={job.job_type} size="small" variant="outlined" />
              </TableCell>
              <TableCell>
                <Chip 
                  label={job.status} 
                  color={getStatusColor(job.status)} 
                  size="small" 
                />
              </TableCell>
              <TableCell>
                <Chip 
                  label={job.priority || 5} 
                  color={getPriorityColor(job.priority || 5)} 
                  size="small"
                  icon={<PriorityIcon fontSize="small" />}
                />
              </TableCell>
              <TableCell>
                <Chip label={job.queue || 'default'} size="small" variant="outlined" />
              </TableCell>
              <TableCell>
                <Typography variant="caption">
                  {job.last_execution_at ? new Date(job.last_execution_at).toLocaleString() : 'Never'}
                </Typography>
              </TableCell>
              <TableCell>
                <Typography variant="caption">
                  {job.next_run_at ? new Date(job.next_run_at).toLocaleString() : 'Not scheduled'}
                </Typography>
              </TableCell>
              <TableCell>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LinearProgress 
                    variant="determinate" 
                    value={job.success_rate || 0} 
                    sx={{ width: 40, height: 4 }}
                  />
                  <Typography variant="caption">
                    {job.success_rate || 0}%
                  </Typography>
                </Box>
              </TableCell>
              <TableCell>
                <Box sx={{ display: 'flex', gap: 0.5 }}>
                  <Tooltip title="Run Now">
                    <IconButton size="small" color="primary">
                      <PlayIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Advanced Schedule">
                    <IconButton size="small" onClick={() => handleAdvancedSchedule(job)}>
                      <ScheduleIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Clone Job">
                    <IconButton size="small" onClick={() => handleCloneJob(job)}>
                      <CodeIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="View Details">
                    <IconButton size="small">
                      <ViewIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  const renderAdvancedCreateDialog = () => (
    <Dialog open={showAdvancedCreate} onClose={() => setShowAdvancedCreate(false)} maxWidth="lg" fullWidth>
      <DialogTitle>Advanced Job Configuration</DialogTitle>
      <DialogContent>
        <Tabs value={0} sx={{ mb: 2 }}>
          <Tab label="Basic" />
          <Tab label="Execution" />
          <Tab label="Retry Logic" />
          <Tab label="Scheduling" />
          <Tab label="Performance" />
          <Tab label="Monitoring" />
        </Tabs>
        
        <Grid container spacing={3}>
          {/* Basic Configuration */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>Basic Configuration</Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <TextField
                    label="Job Name"
                    value={advancedJob.name}
                    onChange={(e) => setAdvancedJob({ ...advancedJob, name: e.target.value })}
                    fullWidth
                    required
                  />
                  <TextField
                    label="Job Type"
                    select
                    value={advancedJob.job_type}
                    onChange={(e) => setAdvancedJob({ ...advancedJob, job_type: e.target.value })}
                    fullWidth
                  >
                    <MenuItem value="shell">Shell Command</MenuItem>
                    <MenuItem value="python">Python Script</MenuItem>
                    <MenuItem value="sql">SQL Query</MenuItem>
                    <MenuItem value="api">API Call</MenuItem>
                    <MenuItem value="custom">Custom Task</MenuItem>
                  </TextField>
                  <TextField
                    label="Commands"
                    multiline
                    rows={4}
                    value={advancedJob.commands}
                    onChange={(e) => setAdvancedJob({ ...advancedJob, commands: e.target.value })}
                    fullWidth
                    required
                  />
                  <TextField
                    label="Description"
                    multiline
                    rows={2}
                    value={advancedJob.description}
                    onChange={(e) => setAdvancedJob({ ...advancedJob, description: e.target.value })}
                    fullWidth
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Execution Configuration */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>Execution Settings</Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box>
                    <Typography gutterBottom>Priority: {advancedJob.priority}</Typography>
                    <Slider
                      value={advancedJob.priority}
                      onChange={(e, value) => setAdvancedJob({ ...advancedJob, priority: value })}
                      min={1}
                      max={10}
                      marks
                      valueLabelDisplay="auto"
                    />
                  </Box>
                  <TextField
                    label="Queue"
                    value={advancedJob.queue}
                    onChange={(e) => setAdvancedJob({ ...advancedJob, queue: e.target.value })}
                    fullWidth
                    helperText="Celery queue name"
                  />
                  <TextField
                    label="Routing Key"
                    value={advancedJob.routing_key}
                    onChange={(e) => setAdvancedJob({ ...advancedJob, routing_key: e.target.value })}
                    fullWidth
                    helperText="Custom routing key"
                  />
                  <TextField
                    label="Timeout (seconds)"
                    type="number"
                    value={advancedJob.timeout}
                    onChange={(e) => setAdvancedJob({ ...advancedJob, timeout: parseInt(e.target.value) })}
                    fullWidth
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Retry Configuration */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>Retry Logic</Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <TextField
                    label="Max Retries"
                    type="number"
                    value={advancedJob.max_retries}
                    onChange={(e) => setAdvancedJob({ ...advancedJob, max_retries: parseInt(e.target.value) })}
                    fullWidth
                  />
                  <TextField
                    label="Retry Delay (seconds)"
                    type="number"
                    value={advancedJob.retry_delay}
                    onChange={(e) => setAdvancedJob({ ...advancedJob, retry_delay: parseInt(e.target.value) })}
                    fullWidth
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={advancedJob.retry_jitter}
                        onChange={(e) => setAdvancedJob({ ...advancedJob, retry_jitter: e.target.checked })}
                      />
                    }
                    label="Retry Jitter"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={advancedJob.retry_backoff}
                        onChange={(e) => setAdvancedJob({ ...advancedJob, retry_backoff: e.target.checked })}
                      />
                    }
                    label="Exponential Backoff"
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Performance Configuration */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>Performance Settings</Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <TextField
                    label="Rate Limit"
                    value={advancedJob.rate_limit}
                    onChange={(e) => setAdvancedJob({ ...advancedJob, rate_limit: e.target.value })}
                    fullWidth
                    helperText="e.g., 100/m for 100 tasks per minute"
                  />
                  <TextField
                    label="Soft Time Limit (seconds)"
                    type="number"
                    value={advancedJob.soft_time_limit}
                    onChange={(e) => setAdvancedJob({ ...advancedJob, soft_time_limit: parseInt(e.target.value) })}
                    fullWidth
                  />
                  <TextField
                    label="Hard Time Limit (seconds)"
                    type="number"
                    value={advancedJob.time_limit}
                    onChange={(e) => setAdvancedJob({ ...advancedJob, time_limit: parseInt(e.target.value) })}
                    fullWidth
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={advancedJob.acks_late}
                        onChange={(e) => setAdvancedJob({ ...advancedJob, acks_late: e.target.checked })}
                      />
                    }
                    label="Acknowledge Late"
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setShowAdvancedCreate(false)}>Cancel</Button>
        <Button variant="contained">Create Advanced Job</Button>
      </DialogActions>
    </Dialog>
  );

  return (
    <Box sx={{ p: 2, height: '100%', overflow: 'auto' }}>
      {/* Advanced Controls Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Advanced Job Management
          </Typography>
          {selectedJobs.length > 0 && (
            <Chip 
              label={`${selectedJobs.length} selected`} 
              color="primary" 
              size="small"
              onDelete={() => setSelectedJobs([])}
            />
          )}
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          {/* Filters */}
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              label="Status"
            >
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="running">Running</MenuItem>
              <MenuItem value="completed">Completed</MenuItem>
              <MenuItem value="failed">Failed</MenuItem>
              <MenuItem value="scheduled">Scheduled</MenuItem>
              <MenuItem value="paused">Paused</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Sort By</InputLabel>
            <Select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              label="Sort By"
            >
              <MenuItem value="created_at">Created</MenuItem>
              <MenuItem value="name">Name</MenuItem>
              <MenuItem value="status">Status</MenuItem>
              <MenuItem value="priority">Priority</MenuItem>
              <MenuItem value="last_execution_at">Last Run</MenuItem>
            </Select>
          </FormControl>

          <Tooltip title="Refresh">
            <IconButton onClick={onRefresh} size="small">
              <RefreshIcon />
            </IconButton>
          </Tooltip>

          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setShowAdvancedCreate(true)}
            size="small"
          >
            Advanced Job
          </Button>
        </Box>
      </Box>

      {/* Bulk Actions */}
      {selectedJobs.length > 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2">
              {selectedJobs.length} job{selectedJobs.length > 1 ? 's' : ''} selected
            </Typography>
            <Button size="small" onClick={() => handleBulkAction('run')}>Run All</Button>
            <Button size="small" onClick={() => handleBulkAction('pause')}>Pause All</Button>
            <Button size="small" onClick={() => handleBulkAction('delete')} color="error">Delete All</Button>
          </Box>
        </Alert>
      )}

      {/* Job Table */}
      {renderTableView()}

      {/* Advanced Create Dialog */}
      {renderAdvancedCreateDialog()}
    </Box>
  );
};

export default AdvancedJobView;