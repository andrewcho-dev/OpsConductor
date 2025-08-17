/**
 * Log Viewer - Ultra-compact, space-efficient job execution monitoring
 * Follows SystemSettings visual pattern with maximum information density
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Typography,
  Button,
  IconButton,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Autocomplete,
  Chip,
  Box,
  Tooltip,
  Collapse,
  LinearProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Pagination,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  ContentCopy as CopyIcon,
  Save as SaveIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  PlayArrow as PlayArrowIcon,
  Computer as ComputerIcon,
  Work as WorkIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { authService } from '../services/authService';
import '../styles/dashboard.css';

const LogViewer = () => {
  const { token } = useAuth();
  const location = useLocation();
  
  // State management
  const [searchPattern, setSearchPattern] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [results, setResults] = useState([]);
  const [hierarchicalData, setHierarchicalData] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  
  // Expansion state - ultra-compact management
  const [expandedJobs, setExpandedJobs] = useState(new Set());
  const [expandedExecutions, setExpandedExecutions] = useState(new Set());
  const [expandedBranches, setExpandedBranches] = useState(new Set());
  const [expandedActions, setExpandedActions] = useState(new Set());
  
  // Modal state
  const [selectedAction, setSelectedAction] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  
  // Pagination
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const ITEMS_PER_PAGE = 100; // Increased for dense display

  // Pattern suggestions for autocomplete
  const patternExamples = [
    'J20250000001 - Specific job',
    'J20250000001.0001 - Specific execution',
    'J20250000001.0001.0001 - Specific branch',
    'J20250000001.0001.0001.0001 - Specific action',
    'J2025* - All 2025 jobs',
    '*.0001 - All first executions',
    '*.*.0001 - All first branches',
    'T20250000001 - By target serial',
    'setup - Text search'
  ];

  // API helper
  const apiCall = async (url, options = {}) => {
    try {
      const response = await authService.api.get(url.replace('/api', ''), options);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || error.message || 'API call failed');
    }
  };

  // Transform flat results into ultra-compact hierarchical structure
  const transformToHierarchical = (flatResults) => {
    const jobMap = new Map();
    
    flatResults.forEach(action => {
      const jobKey = action.job_serial;
      const executionKey = `${jobKey}.${action.execution_serial}`;
      const branchKey = `${executionKey}.${action.branch_serial}`;
      
      // Initialize job
      if (!jobMap.has(jobKey)) {
        jobMap.set(jobKey, {
          id: jobKey,
          job_serial: action.job_serial,
          job_name: action.job_name,
          executions: new Map(),
          stats: { total: 0, completed: 0, failed: 0, running: 0 },
          lastExecution: null
        });
      }
      
      const job = jobMap.get(jobKey);
      job.stats.total++;
      if (action.status === 'completed') job.stats.completed++;
      else if (action.status === 'failed') job.stats.failed++;
      else if (action.status === 'running') job.stats.running++;
      
      // Initialize execution
      if (!job.executions.has(executionKey)) {
        job.executions.set(executionKey, {
          id: executionKey,
          execution_serial: action.execution_serial,
          branches: new Map(),
          stats: { total: 0, completed: 0, failed: 0, running: 0 },
          started_at: action.started_at,
          completed_at: action.completed_at
        });
      }
      
      const execution = job.executions.get(executionKey);
      execution.stats.total++;
      if (action.status === 'completed') execution.stats.completed++;
      else if (action.status === 'failed') execution.stats.failed++;
      else if (action.status === 'running') execution.stats.running++;
      
      // Update job's last execution
      if (!job.lastExecution || new Date(action.started_at) > new Date(job.lastExecution)) {
        job.lastExecution = action.started_at;
      }
      
      // Initialize branch
      if (!execution.branches.has(branchKey)) {
        execution.branches.set(branchKey, {
          id: branchKey,
          branch_serial: action.branch_serial,
          target_serial: action.target_serial,
          target_name: action.target_name,
          target_type: action.target_type,
          actions: [],
          stats: { total: 0, completed: 0, failed: 0, running: 0 }
        });
      }
      
      const branch = execution.branches.get(branchKey);
      branch.stats.total++;
      if (action.status === 'completed') branch.stats.completed++;
      else if (action.status === 'failed') branch.stats.failed++;
      else if (action.status === 'running') branch.stats.running++;
      
      // Add action
      branch.actions.push(action);
    });
    
    // Convert to arrays and sort
    return Array.from(jobMap.values()).map(job => ({
      ...job,
      executions: Array.from(job.executions.values()).map(execution => ({
        ...execution,
        branches: Array.from(execution.branches.values())
      })).sort((a, b) => new Date(b.started_at) - new Date(a.started_at))
    })).sort((a, b) => new Date(b.lastExecution) - new Date(a.lastExecution));
  };

  // Search function
  const performSearch = useCallback(async (pattern = '', status = 'all', pageNum = 1) => {
    setLoading(true);
    setError(null);
    
    try {
      const offset = (pageNum - 1) * ITEMS_PER_PAGE;
      const params = new URLSearchParams({
        limit: ITEMS_PER_PAGE.toString(),
        offset: offset.toString(),
        status
      });
      
      if (pattern.trim()) {
        params.append('pattern', pattern.trim());
      }
      
      const response = await apiCall(`/api/v2/log-viewer/search?${params}`);
      const flatResults = response.results || [];
      
      setResults(flatResults);
      setHierarchicalData(transformToHierarchical(flatResults));
      setTotalPages(Math.ceil(response.total_count / ITEMS_PER_PAGE));
      setLastUpdated(new Date());
      
      // Get comprehensive stats
      try {
        const statsParams = pattern.trim() ? `?pattern=${encodeURIComponent(pattern.trim())}` : '';
        const statsResponse = await apiCall(`/api/v2/log-viewer/stats${statsParams}`);
        setStats(statsResponse.stats);
      } catch (statsError) {
        console.warn('Stats API not available:', statsError);
        setStats(null);
      }
      
    } catch (err) {
      setError(err.message || 'Search failed');
      setResults([]);
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, [token]);

  // Initialize
  useEffect(() => {
    const state = location.state;
    if (state?.searchPattern) {
      setSearchPattern(state.searchPattern);
      performSearch(state.searchPattern, 'all', 1);
    } else {
      performSearch('', 'all', 1);
    }
  }, [location.state, performSearch]);

  // Event handlers
  const handleSearch = () => {
    setPage(1);
    performSearch(searchPattern, statusFilter, 1);
  };

  const handlePageChange = (event, value) => {
    setPage(value);
    performSearch(searchPattern, statusFilter, value);
  };

  // Toggle functions for ultra-compact expansion
  const toggleJob = (jobId) => {
    const newExpanded = new Set(expandedJobs);
    if (newExpanded.has(jobId)) {
      newExpanded.delete(jobId);
    } else {
      newExpanded.add(jobId);
    }
    setExpandedJobs(newExpanded);
  };

  const toggleExecution = (executionId) => {
    const newExpanded = new Set(expandedExecutions);
    if (newExpanded.has(executionId)) {
      newExpanded.delete(executionId);
    } else {
      newExpanded.add(executionId);
    }
    setExpandedExecutions(newExpanded);
  };

  const toggleBranch = (branchId) => {
    const newExpanded = new Set(expandedBranches);
    if (newExpanded.has(branchId)) {
      newExpanded.delete(branchId);
    } else {
      newExpanded.add(branchId);
    }
    setExpandedBranches(newExpanded);
  };

  // Utility functions
  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'running': return 'warning';
      case 'scheduled': return 'info';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed': return <CheckCircleIcon fontSize="inherit" />;
      case 'failed': return <ErrorIcon fontSize="inherit" />;
      case 'running': return <PlayArrowIcon fontSize="inherit" />;
      case 'scheduled': return <ScheduleIcon fontSize="inherit" />;
      default: return <InfoIcon fontSize="inherit" />;
    }
  };

  const formatDuration = (ms) => {
    if (!ms) return 'N/A';
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const exportResults = () => {
    const csv = [
      'Action Serial,Action Name,Status,Exit Code,Duration,Job,Execution,Branch,Target,Started At,Completed At',
      ...results.map(result => [
        result.action_serial,
        result.action_name,
        result.status,
        result.exit_code,
        formatDuration(result.execution_time_ms),
        result.job_name,
        result.execution_serial,
        result.branch_serial,
        result.target_name,
        formatTimestamp(result.started_at),
        formatTimestamp(result.completed_at)
      ].join(','))
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `log-viewer-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Calculate comprehensive stats
  const overallStats = {
    total_jobs: hierarchicalData.length,
    total_executions: hierarchicalData.reduce((sum, job) => sum + job.executions.length, 0),
    total_actions: results.length,
    completed_actions: results.filter(r => r.status === 'completed').length,
    failed_actions: results.filter(r => r.status === 'failed').length,
    running_actions: results.filter(r => r.status === 'running').length
  };

  if (loading && hierarchicalData.length === 0) {
    return (
      <div className="dashboard-container">
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
          <Typography variant="h6">Loading execution logs...</Typography>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      {/* Compact Page Header - Following Design Guidelines */}
      <div className="page-header">
        <Typography className="page-title">
          Execution Log Viewer
        </Typography>
        <div className="page-actions">
          {lastUpdated && (
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
              Updated: {lastUpdated.toLocaleTimeString()}
            </Typography>
          )}
          <Button
            className="btn-compact"
            size="small"
            variant="outlined"
            startIcon={<RefreshIcon fontSize="small" />}
            onClick={() => performSearch(searchPattern, statusFilter, page)}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            className="btn-compact"
            size="small"
            variant="outlined"
            startIcon={<DownloadIcon fontSize="small" />}
            onClick={exportResults}
            disabled={results.length === 0}
          >
            Export
          </Button>
        </div>
      </div>

      {/* Enhanced Statistics Grid - Following Design Guidelines */}
      <div className="stats-grid">
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon primary">
              <WorkIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{overallStats.total_jobs}</h3>
              <p>Total Jobs</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon info">
              <TimelineIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{overallStats.total_executions}</h3>
              <p>Executions</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon secondary">
              <AssessmentIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{overallStats.total_actions}</h3>
              <p>Total Actions</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon success">
              <CheckCircleIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{overallStats.completed_actions}</h3>
              <p>Completed</p>
            </div>
          </div>
        </div>

        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon error">
              <ErrorIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{overallStats.failed_actions}</h3>
              <p>Failed</p>
            </div>
          </div>
        </div>

        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon warning">
              <PlayArrowIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{overallStats.running_actions}</h3>
              <p>Running</p>
            </div>
          </div>
        </div>
      </div>

      {/* Search Controls - Ultra-compact */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr auto', gap: '12px', marginBottom: '16px' }}>
        <Autocomplete
          freeSolo
          options={patternExamples}
          value={searchPattern}
          onInputChange={(event, newValue) => setSearchPattern(newValue || '')}
          size="small"
          renderInput={(params) => (
            <TextField
              {...params}
              label="Search Pattern"
              placeholder="Enter serial pattern or search term..."
              size="small"
              sx={{ '& .MuiInputBase-input': { fontSize: '0.8rem' } }}
            />
          )}
        />
        
        <FormControl size="small">
          <InputLabel sx={{ fontSize: '0.8rem' }}>Status</InputLabel>
          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            label="Status"
            sx={{ fontSize: '0.8rem' }}
          >
            <MenuItem value="all" sx={{ fontSize: '0.8rem' }}>All</MenuItem>
            <MenuItem value="completed" sx={{ fontSize: '0.8rem' }}>Completed</MenuItem>
            <MenuItem value="failed" sx={{ fontSize: '0.8rem' }}>Failed</MenuItem>
            <MenuItem value="running" sx={{ fontSize: '0.8rem' }}>Running</MenuItem>
            <MenuItem value="scheduled" sx={{ fontSize: '0.8rem' }}>Scheduled</MenuItem>
          </Select>
        </FormControl>
        
        <Button
          variant="contained"
          startIcon={<SearchIcon fontSize="small" />}
          onClick={handleSearch}
          disabled={loading}
          size="small"
          sx={{ fontSize: '0.8rem' }}
        >
          Search
        </Button>
      </div>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 2, fontSize: '0.8rem' }}>
          {error}
        </Alert>
      )}

      {/* Ultra-Compact Hierarchical Results */}
      <div className="main-content-card fade-in">
        <div className="content-card-header">
          <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
            <StorageIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
            EXECUTION LOGS
          </Typography>
          <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
            {hierarchicalData.length} jobs, {overallStats.total_executions} executions, {overallStats.total_actions} actions
          </Typography>
        </div>
        
        <div className="content-card-body" style={{ padding: '8px' }}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
              <LinearProgress sx={{ width: '100%' }} />
            </Box>
          ) : hierarchicalData.length === 0 ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <Typography color="textSecondary" sx={{ fontSize: '0.8rem' }}>
                No results found. Try adjusting your search pattern.
              </Typography>
            </Box>
          ) : (
            <Box sx={{ maxHeight: '600px', overflowY: 'auto' }}>
              {hierarchicalData.map((job) => (
                <Box key={job.id} sx={{ mb: 0.5 }}>
                  {/* Job Level - Ultra-compact */}
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      p: 0.5,
                      bgcolor: 'grey.100',
                      borderRadius: 0.5,
                      cursor: 'pointer',
                      minHeight: '24px',
                      '&:hover': { bgcolor: 'grey.200' }
                    }}
                    onClick={() => toggleJob(job.id)}
                  >
                    <IconButton size="small" sx={{ p: 0.25, mr: 0.5 }}>
                      {expandedJobs.has(job.id) ? 
                        <ExpandLessIcon sx={{ fontSize: '16px' }} /> : 
                        <ExpandMoreIcon sx={{ fontSize: '16px' }} />
                      }
                    </IconButton>
                    
                    <Typography variant="body2" sx={{ 
                      fontFamily: 'monospace', 
                      fontWeight: 'bold', 
                      fontSize: '0.7rem',
                      mr: 1,
                      minWidth: '120px'
                    }}>
                      {job.job_serial}
                    </Typography>
                    
                    <Typography variant="body2" sx={{ 
                      fontSize: '0.7rem', 
                      mr: 1,
                      flex: 1,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {job.job_name}
                    </Typography>
                    
                    <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
                      <Chip 
                        label={`${job.stats.completed}/${job.stats.total}`}
                        size="small" 
                        color={job.stats.failed > 0 ? 'error' : job.stats.completed === job.stats.total ? 'success' : 'warning'}
                        sx={{ fontSize: '0.65rem', height: '18px' }}
                      />
                      <Typography variant="caption" sx={{ fontSize: '0.65rem', color: 'text.secondary' }}>
                        {formatTimestamp(job.lastExecution)}
                      </Typography>
                    </Box>
                  </Box>

                  {/* Executions Level - Ultra-compact */}
                  <Collapse in={expandedJobs.has(job.id)}>
                    <Box sx={{ ml: 1, mt: 0.25 }}>
                      {job.executions.map((execution) => (
                        <Box key={execution.id} sx={{ mb: 0.25 }}>
                          <Box
                            sx={{
                              display: 'flex',
                              alignItems: 'center',
                              p: 0.5,
                              bgcolor: 'grey.50',
                              borderRadius: 0.5,
                              cursor: 'pointer',
                              minHeight: '22px',
                              '&:hover': { bgcolor: 'grey.100' }
                            }}
                            onClick={() => toggleExecution(execution.id)}
                          >
                            <IconButton size="small" sx={{ p: 0.25, mr: 0.5 }}>
                              {expandedExecutions.has(execution.id) ? 
                                <ExpandLessIcon sx={{ fontSize: '14px' }} /> : 
                                <ExpandMoreIcon sx={{ fontSize: '14px' }} />
                              }
                            </IconButton>
                            
                            <Typography variant="body2" sx={{ 
                              fontFamily: 'monospace', 
                              fontWeight: 'bold', 
                              fontSize: '0.65rem',
                              mr: 1,
                              minWidth: '80px'
                            }}>
                              .{execution.execution_serial.split('.').pop()}
                            </Typography>
                            
                            <Typography variant="body2" sx={{ 
                              fontSize: '0.65rem', 
                              mr: 1,
                              flex: 1
                            }}>
                              {formatTimestamp(execution.started_at)}
                            </Typography>
                            
                            <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
                              <Chip 
                                label={`${execution.stats.completed}/${execution.stats.total}`}
                                size="small" 
                                color={execution.stats.failed > 0 ? 'error' : execution.stats.completed === execution.stats.total ? 'success' : 'warning'}
                                sx={{ fontSize: '0.6rem', height: '16px' }}
                              />
                              <Typography variant="caption" sx={{ fontSize: '0.6rem', color: 'text.secondary' }}>
                                {execution.branches.length} targets
                              </Typography>
                            </Box>
                          </Box>

                          {/* Branches Level - Ultra-compact */}
                          <Collapse in={expandedExecutions.has(execution.id)}>
                            <Box sx={{ ml: 1, mt: 0.25 }}>
                              {execution.branches.map((branch) => (
                                <Box key={branch.id} sx={{ mb: 0.25 }}>
                                  <Box
                                    sx={{
                                      display: 'flex',
                                      alignItems: 'center',
                                      p: 0.5,
                                      bgcolor: 'background.paper',
                                      border: '1px solid',
                                      borderColor: 'divider',
                                      borderRadius: 0.5,
                                      cursor: 'pointer',
                                      minHeight: '20px',
                                      '&:hover': { bgcolor: 'grey.50' }
                                    }}
                                    onClick={() => toggleBranch(branch.id)}
                                  >
                                    <IconButton size="small" sx={{ p: 0.25, mr: 0.5 }}>
                                      {expandedBranches.has(branch.id) ? 
                                        <ExpandLessIcon sx={{ fontSize: '12px' }} /> : 
                                        <ExpandMoreIcon sx={{ fontSize: '12px' }} />
                                      }
                                    </IconButton>
                                    
                                    <Typography variant="body2" sx={{ 
                                      fontFamily: 'monospace', 
                                      fontWeight: 'bold', 
                                      fontSize: '0.6rem',
                                      mr: 1,
                                      minWidth: '60px'
                                    }}>
                                      .{branch.branch_serial.split('.').pop()}
                                    </Typography>
                                    
                                    <Typography variant="body2" sx={{ 
                                      fontSize: '0.6rem', 
                                      mr: 1,
                                      flex: 1,
                                      overflow: 'hidden',
                                      textOverflow: 'ellipsis',
                                      whiteSpace: 'nowrap'
                                    }}>
                                      {branch.target_name}
                                    </Typography>
                                    
                                    <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
                                      <Chip 
                                        label={branch.stats.failed > 0 ? 'Failed' : branch.stats.completed > 0 ? 'Success' : 'Running'} 
                                        size="small" 
                                        color={branch.stats.failed > 0 ? 'error' : branch.stats.completed > 0 ? 'success' : 'warning'}
                                        sx={{ fontSize: '0.55rem', height: '14px' }}
                                      />
                                      <Typography variant="caption" sx={{ fontSize: '0.55rem', color: 'text.secondary' }}>
                                        {branch.actions.length} actions
                                      </Typography>
                                    </Box>
                                  </Box>

                                  {/* Actions Level - Ultra-compact table */}
                                  <Collapse in={expandedBranches.has(branch.id)}>
                                    <Box sx={{ ml: 1, mt: 0.25, p: 0.5, bgcolor: 'grey.50', borderRadius: 0.5 }}>
                                      <TableContainer component={Paper} sx={{ boxShadow: 'none' }}>
                                        <Table size="small" sx={{ minWidth: 'auto' }}>
                                          <TableHead>
                                            <TableRow>
                                              <TableCell sx={{ fontSize: '0.6rem', fontWeight: 600, p: 0.5 }}>Action</TableCell>
                                              <TableCell sx={{ fontSize: '0.6rem', fontWeight: 600, p: 0.5 }}>Status</TableCell>
                                              <TableCell sx={{ fontSize: '0.6rem', fontWeight: 600, p: 0.5 }}>Exit</TableCell>
                                              <TableCell sx={{ fontSize: '0.6rem', fontWeight: 600, p: 0.5 }}>Duration</TableCell>
                                              <TableCell sx={{ fontSize: '0.6rem', fontWeight: 600, p: 0.5 }}>Actions</TableCell>
                                            </TableRow>
                                          </TableHead>
                                          <TableBody>
                                            {branch.actions.map((action) => (
                                              <TableRow key={action.id} hover sx={{ height: '24px' }}>
                                                <TableCell sx={{ fontSize: '0.6rem', p: 0.5, fontFamily: 'monospace' }}>
                                                  <Tooltip title={action.action_name}>
                                                    <span>{action.action_serial.split('.').pop()} - {action.action_name.substring(0, 20)}...</span>
                                                  </Tooltip>
                                                </TableCell>
                                                <TableCell sx={{ p: 0.5 }}>
                                                  <Chip
                                                    icon={getStatusIcon(action.status)}
                                                    label={action.status}
                                                    color={getStatusColor(action.status)}
                                                    size="small"
                                                    sx={{ fontSize: '0.55rem', height: '16px' }}
                                                  />
                                                </TableCell>
                                                <TableCell sx={{ fontSize: '0.6rem', p: 0.5 }}>
                                                  <Chip
                                                    label={action.exit_code ?? 'N/A'}
                                                    color={action.exit_code === 0 ? 'success' : action.exit_code > 0 ? 'error' : 'default'}
                                                    size="small"
                                                    sx={{ fontSize: '0.55rem', height: '16px' }}
                                                  />
                                                </TableCell>
                                                <TableCell sx={{ fontSize: '0.6rem', p: 0.5 }}>
                                                  {formatDuration(action.execution_time_ms)}
                                                </TableCell>
                                                <TableCell sx={{ p: 0.5 }}>
                                                  <Tooltip title="View Details">
                                                    <IconButton 
                                                      size="small" 
                                                      onClick={() => {
                                                        setSelectedAction(action);
                                                        setDetailsOpen(true);
                                                      }}
                                                      sx={{ p: 0.25 }}
                                                    >
                                                      <InfoIcon sx={{ fontSize: '12px' }} />
                                                    </IconButton>
                                                  </Tooltip>
                                                </TableCell>
                                              </TableRow>
                                            ))}
                                          </TableBody>
                                        </Table>
                                      </TableContainer>
                                    </Box>
                                  </Collapse>
                                </Box>
                              ))}
                            </Box>
                          </Collapse>
                        </Box>
                      ))}
                    </Box>
                  </Collapse>
                </Box>
              ))}
            </Box>
          )}
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <Pagination
            count={totalPages}
            page={page}
            onChange={handlePageChange}
            color="primary"
            size="small"
          />
        </Box>
      )}

      {/* Action Details Modal */}
      <Dialog
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ fontSize: '0.9rem', fontWeight: 600 }}>
          Action Details: {selectedAction?.action_serial}
        </DialogTitle>
        <DialogContent>
          {selectedAction && (
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
              <Box>
                <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                  Basic Information
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                  <Typography variant="body2" sx={{ fontSize: '0.7rem' }}>
                    <strong>Name:</strong> {selectedAction.action_name}
                  </Typography>
                  <Typography variant="body2" sx={{ fontSize: '0.7rem' }}>
                    <strong>Status:</strong> {selectedAction.status}
                  </Typography>
                  <Typography variant="body2" sx={{ fontSize: '0.7rem' }}>
                    <strong>Exit Code:</strong> {selectedAction.exit_code ?? 'N/A'}
                  </Typography>
                  <Typography variant="body2" sx={{ fontSize: '0.7rem' }}>
                    <strong>Duration:</strong> {formatDuration(selectedAction.execution_time_ms)}
                  </Typography>
                </Box>
              </Box>
              <Box>
                <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                  Execution Details
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                  <Typography variant="body2" sx={{ fontSize: '0.7rem' }}>
                    <strong>Started:</strong> {formatTimestamp(selectedAction.started_at)}
                  </Typography>
                  <Typography variant="body2" sx={{ fontSize: '0.7rem' }}>
                    <strong>Completed:</strong> {formatTimestamp(selectedAction.completed_at)}
                  </Typography>
                  <Typography variant="body2" sx={{ fontSize: '0.7rem' }}>
                    <strong>Target:</strong> {selectedAction.target_name}
                  </Typography>
                </Box>
              </Box>
              {selectedAction.command_executed && (
                <Box sx={{ gridColumn: '1 / -1' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600 }}>
                      Command Executed
                    </Typography>
                    <IconButton
                      size="small"
                      onClick={() => copyToClipboard(selectedAction.command_executed)}
                      title="Copy command"
                    >
                      <CopyIcon fontSize="small" />
                    </IconButton>
                  </Box>
                  <Paper sx={{ p: 1, bgcolor: 'grey.100', fontFamily: 'monospace', fontSize: '0.7rem' }}>
                    {selectedAction.command_executed}
                  </Paper>
                </Box>
              )}
              {selectedAction.result_output && (
                <Box sx={{ gridColumn: '1 / -1' }}>
                  <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                    Output
                  </Typography>
                  <Paper sx={{ p: 1, bgcolor: 'grey.100', fontFamily: 'monospace', fontSize: '0.7rem', maxHeight: '200px', overflowY: 'auto' }}>
                    {selectedAction.result_output}
                  </Paper>
                </Box>
              )}
              {selectedAction.result_error && (
                <Box sx={{ gridColumn: '1 / -1' }}>
                  <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1, color: 'error.main' }}>
                    Error Output
                  </Typography>
                  <Paper sx={{ p: 1, bgcolor: 'error.50', fontFamily: 'monospace', fontSize: '0.7rem', maxHeight: '200px', overflowY: 'auto' }}>
                    {selectedAction.result_error}
                  </Paper>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)} size="small">Close</Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default LogViewer;