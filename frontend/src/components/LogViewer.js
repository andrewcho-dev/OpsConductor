import React, { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Paper,
  Chip,
  IconButton,
  Collapse,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Pagination,
  Alert,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Autocomplete
} from '@mui/material';
import {
  Search as SearchIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  FilterList as FilterIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
  ContentCopy as CopyIcon,
  Save as SaveIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { authService } from '../services/authService';
import '../styles/dashboard.css';

const LogViewer = () => {
  const { token } = useAuth();
  const location = useLocation();
  
  // State
  const [searchPattern, setSearchPattern] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [results, setResults] = useState([]);
  const [hierarchicalData, setHierarchicalData] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedJobs, setExpandedJobs] = useState(new Set());
  const [expandedExecutions, setExpandedExecutions] = useState(new Set());
  const [expandedTargets, setExpandedTargets] = useState(new Set());
  const [expandedActions, setExpandedActions] = useState(new Set());
  const [selectedAction, setSelectedAction] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  const ITEMS_PER_PAGE = 50;

  // Pattern suggestions
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

  // API call helper
  const apiCall = async (url, options = {}) => {
    try {
      const response = await authService.api.get(url.replace('/api', ''), options);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || error.message || 'API call failed');
    }
  };

  // Transform flat results into hierarchical structure
  const transformToHierarchical = (flatResults) => {
    const jobMap = new Map();
    
    flatResults.forEach(action => {
      const jobKey = action.job_serial;
      const executionKey = `${jobKey}.${action.execution_serial}`;
      const targetKey = `${executionKey}.${action.target_serial}`;
      
      // Initialize job if not exists
      if (!jobMap.has(jobKey)) {
        jobMap.set(jobKey, {
          id: jobKey,
          job_serial: action.job_serial,
          job_name: action.job_name,
          executions: new Map(),
          totalActions: 0,
          completedActions: 0,
          failedActions: 0,
          runningActions: 0
        });
      }
      
      const job = jobMap.get(jobKey);
      job.totalActions++;
      if (action.status === 'completed') job.completedActions++;
      else if (action.status === 'failed') job.failedActions++;
      else if (action.status === 'running') job.runningActions++;
      
      // Initialize execution if not exists
      if (!job.executions.has(executionKey)) {
        job.executions.set(executionKey, {
          id: executionKey,
          execution_serial: action.execution_serial,
          targets: new Map(),
          totalActions: 0,
          completedActions: 0,
          failedActions: 0,
          runningActions: 0
        });
      }
      
      const execution = job.executions.get(executionKey);
      execution.totalActions++;
      if (action.status === 'completed') execution.completedActions++;
      else if (action.status === 'failed') execution.failedActions++;
      else if (action.status === 'running') execution.runningActions++;
      
      // Initialize target if not exists
      if (!execution.targets.has(targetKey)) {
        execution.targets.set(targetKey, {
          id: targetKey,
          target_serial: action.target_serial,
          target_name: action.target_name,
          target_type: action.target_type,
          actions: [],
          totalActions: 0,
          completedActions: 0,
          failedActions: 0,
          runningActions: 0
        });
      }
      
      const target = execution.targets.get(targetKey);
      target.totalActions++;
      if (action.status === 'completed') target.completedActions++;
      else if (action.status === 'failed') target.failedActions++;
      else if (action.status === 'running') target.runningActions++;
      
      // Add action to target
      target.actions.push(action);
    });
    
    // Convert Maps to Arrays for easier rendering
    const hierarchical = Array.from(jobMap.values()).map(job => ({
      ...job,
      executions: Array.from(job.executions.values()).map(execution => ({
        ...execution,
        targets: Array.from(execution.targets.values())
      }))
    }));
    
    return hierarchical;
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
      
      const response = await apiCall(`/api/log-viewer/search?${params}`);
      
      const flatResults = response.results || [];
      setResults(flatResults);
      setHierarchicalData(transformToHierarchical(flatResults));
      setTotalPages(Math.ceil(((flatResults).length === ITEMS_PER_PAGE ? (offset + ITEMS_PER_PAGE + 1) : offset + (flatResults).length) / ITEMS_PER_PAGE));
      
      // Get stats
      const statsParams = pattern.trim() ? `?pattern=${encodeURIComponent(pattern.trim())}` : '';
      try {
        const statsResponse = await apiCall(`/api/log-viewer/stats${statsParams}`);
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

  // Handle navigation state and initial load
  useEffect(() => {
    const state = location.state;
    if (state?.searchPattern) {
      setSearchPattern(state.searchPattern);
      performSearch(state.searchPattern, 'all', 1);
    } else {
      performSearch('', 'all', 1);
    }
  }, [location.state]);

  // Handle search
  const handleSearch = () => {
    setPage(1);
    performSearch(searchPattern, statusFilter, 1);
  };

  // Handle page change
  const handlePageChange = (event, value) => {
    setPage(value);
    performSearch(searchPattern, statusFilter, value);
  };

  // Toggle functions for each level
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

  const toggleTarget = (targetId) => {
    const newExpanded = new Set(expandedTargets);
    if (newExpanded.has(targetId)) {
      newExpanded.delete(targetId);
    } else {
      newExpanded.add(targetId);
    }
    setExpandedTargets(newExpanded);
  };

  const toggleAction = (actionId) => {
    const newExpanded = new Set(expandedActions);
    if (newExpanded.has(actionId)) {
      newExpanded.delete(actionId);
    } else {
      newExpanded.add(actionId);
    }
    setExpandedActions(newExpanded);
  };



  // Get status color
  const getStatusColor = (status) => {
    switch (status.toLowerCase()) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'running': return 'warning';
      case 'scheduled': return 'info';
      default: return 'default';
    }
  };

  // Format duration
  const formatDuration = (ms) => {
    if (!ms) return 'N/A';
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  // Format timestamp
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleString();
  };

  // Copy text to clipboard
  const copyToClipboard = async (text, type = 'text') => {
    try {
      await navigator.clipboard.writeText(text);
      console.log(`${type} copied to clipboard`);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  // Save text as file
  const saveAsFile = (content, filename, type = 'text/plain') => {
    const blob = new Blob([content], { type });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  // Export results
  const exportResults = () => {
    const csv = [
      // Header
      'Action Serial,Action Name,Status,Exit Code,Duration,Job,Execution,Branch,Target,Started At,Completed At',
      // Data
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
    a.download = `log-viewer-results-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="dashboard-container">
      {/* Page Header */}
      <div className="page-header">
        <Typography className="page-title">
          Log Viewer
        </Typography>
        <div className="page-actions">
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => performSearch(searchPattern, statusFilter, page)}
            disabled={loading}
            size="small"
          >
            Refresh
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={exportResults}
            disabled={results.length === 0}
            size="small"
          >
            Export
          </Button>
        </div>
      </div>
      
      {/* Search Controls */}
      <div className="filters-container">
        <Autocomplete
          freeSolo
          options={patternExamples}
          value={searchPattern}
          onInputChange={(event, newValue) => setSearchPattern(newValue || '')}
          className="search-field"
          renderInput={(params) => (
            <TextField
              {...params}
              label="Search Pattern"
              placeholder="Enter serial pattern or search term..."
              size="small"
            />
          )}
        />
        
        <FormControl className="filter-item" size="small">
          <InputLabel>Status</InputLabel>
          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            label="Status"
          >
            <MenuItem value="all">All</MenuItem>
            <MenuItem value="completed">Completed</MenuItem>
            <MenuItem value="failed">Failed</MenuItem>
            <MenuItem value="running">Running</MenuItem>
            <MenuItem value="scheduled">Scheduled</MenuItem>
          </Select>
        </FormControl>
        
        <Button
          variant="contained"
          startIcon={<SearchIcon />}
          onClick={handleSearch}
          disabled={loading}
          size="small"
        >
          Search
        </Button>
      </div>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Hierarchical Results View */}
      <Card>
        <CardContent>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <Typography>Loading...</Typography>
            </Box>
          ) : hierarchicalData.length === 0 ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <Typography color="textSecondary">
                No results found. Try adjusting your search pattern.
              </Typography>
            </Box>
          ) : (
            <Box>
              {hierarchicalData.map((job) => (
                <Box key={job.id} sx={{ mb: 1 }}>
                  {/* Job Level */}
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      p: 1,
                      bgcolor: 'grey.100',
                      borderRadius: 1,
                      cursor: 'pointer',
                      '&:hover': { bgcolor: 'grey.200' }
                    }}
                    onClick={() => toggleJob(job.id)}
                  >
                    <IconButton size="small" sx={{ mr: 1 }}>
                      {expandedJobs.has(job.id) ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                    </IconButton>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 'bold', mr: 2 }}>
                      {job.job_serial}
                    </Typography>
                    <Typography variant="body2" sx={{ mr: 2, color: 'text.secondary' }}>
                      {job.job_name}
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                      ({job.executions.length} executions)
                    </Typography>
                  </Box>

                  {/* Executions Level */}
                  <Collapse in={expandedJobs.has(job.id)}>
                    <Box sx={{ ml: 2, mt: 0.5 }}>
                      {job.executions.map((execution) => (
                        <Box key={execution.id} sx={{ mb: 0.5 }}>
                          <Box
                            sx={{
                              display: 'flex',
                              alignItems: 'center',
                              p: 0.75,
                              bgcolor: 'grey.50',
                              borderRadius: 1,
                              cursor: 'pointer',
                              '&:hover': { bgcolor: 'grey.100' }
                            }}
                            onClick={() => toggleExecution(execution.id)}
                          >
                            <IconButton size="small" sx={{ mr: 1 }}>
                              {expandedExecutions.has(execution.id) ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                            </IconButton>
                            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 'bold', mr: 2 }}>
                              {execution.execution_serial}
                            </Typography>
                            <Typography variant="body2" sx={{ mr: 2, color: 'text.secondary' }}>
                              {execution.targets.length > 0 && execution.targets[0].actions.length > 0 
                                ? formatTimestamp(execution.targets[0].actions[0].started_at)
                                : 'N/A'}
                            </Typography>
                            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                              ({execution.totalActions} actions)
                            </Typography>
                          </Box>

                          {/* Targets Level */}
                          <Collapse in={expandedExecutions.has(execution.id)}>
                            <Box sx={{ ml: 2, mt: 0.5 }}>
                              {execution.targets.map((target) => (
                                <Box key={target.id} sx={{ mb: 0.5 }}>
                                  <Box
                                    sx={{
                                      display: 'flex',
                                      alignItems: 'center',
                                      p: 0.75,
                                      bgcolor: 'background.paper',
                                      border: '1px solid',
                                      borderColor: 'divider',
                                      borderRadius: 1,
                                      cursor: 'pointer',
                                      '&:hover': { bgcolor: 'grey.50' }
                                    }}
                                    onClick={() => toggleTarget(target.id)}
                                  >
                                    <IconButton size="small" sx={{ mr: 1 }}>
                                      {expandedTargets.has(target.id) ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                                    </IconButton>
                                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 'bold', mr: 2 }}>
                                      {target.target_serial}
                                    </Typography>
                                    <Typography variant="body2" sx={{ mr: 2, color: 'text.secondary' }}>
                                      {target.target_name}
                                    </Typography>
                                    <Chip 
                                      label={target.failedActions > 0 ? 'Failed' : target.completedActions > 0 ? 'Success' : 'Running'} 
                                      size="small" 
                                      color={target.failedActions > 0 ? 'error' : target.completedActions > 0 ? 'success' : 'default'}
                                      variant="outlined"
                                    />
                                  </Box>

                                  {/* Action Results Level */}
                                  <Collapse in={expandedTargets.has(target.id)}>
                                    <Box sx={{ ml: 2, mt: 0.5, p: 1.5, bgcolor: 'grey.50', borderRadius: 1 }}>
                                      {target.actions.map((action, index) => (
                                        <Box key={action.id} sx={{ mb: index < target.actions.length - 1 ? 2 : 0 }}>
                                          <Box sx={{ mb: 1 }}>
                                            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 'bold', mb: 0.5 }}>
                                              {action.action_serial} - {action.action_name}
                                            </Typography>
                                            <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                                              <Chip
                                                label={action.status}
                                                color={getStatusColor(action.status)}
                                                size="small"
                                                variant="outlined"
                                              />
                                              <Chip
                                                label={`Exit: ${action.exit_code}`}
                                                color={action.exit_code === 0 ? 'success' : 'error'}
                                                size="small"
                                                variant="outlined"
                                              />
                                              <Typography variant="caption" sx={{ alignSelf: 'center', color: 'text.secondary' }}>
                                                {formatDuration(action.execution_time_ms)}
                                              </Typography>
                                            </Box>
                                          </Box>
                                          
                                          {action.command_executed && (
                                            <Box sx={{ mb: 1 }}>
                                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                                                <Typography variant="caption" sx={{ fontWeight: 'bold', color: 'text.secondary' }}>
                                                  Command:
                                                </Typography>
                                                <Box sx={{ display: 'flex', gap: 0.5 }}>
                                                  <IconButton
                                                    size="small"
                                                    onClick={() => copyToClipboard(action.command_executed, 'Command')}
                                                    title="Copy command"
                                                  >
                                                    <CopyIcon fontSize="small" />
                                                  </IconButton>
                                                  <IconButton
                                                    size="small"
                                                    onClick={() => saveAsFile(action.command_executed, `${action.action_serial}-command.txt`)}
                                                    title="Save command as file"
                                                  >
                                                    <SaveIcon fontSize="small" />
                                                  </IconButton>
                                                </Box>
                                              </Box>
                                              <Typography
                                                variant="body2"
                                                sx={{ 
                                                  fontFamily: 'monospace', 
                                                  bgcolor: 'background.paper', 
                                                  p: 1, 
                                                  borderRadius: 1,
                                                  border: '1px solid',
                                                  borderColor: 'divider'
                                                }}
                                              >
                                                {action.command_executed}
                                              </Typography>
                                            </Box>
                                          )}
                                          
                                          {action.result_output && (
                                            <Box sx={{ mb: 1 }}>
                                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                                                <Typography variant="caption" sx={{ fontWeight: 'bold', color: 'text.secondary' }}>
                                                  Output:
                                                </Typography>
                                                <Box sx={{ display: 'flex', gap: 0.5 }}>
                                                  <IconButton
                                                    size="small"
                                                    onClick={() => copyToClipboard(action.result_output, 'Output')}
                                                    title="Copy output"
                                                  >
                                                    <CopyIcon fontSize="small" />
                                                  </IconButton>
                                                  <IconButton
                                                    size="small"
                                                    onClick={() => saveAsFile(action.result_output, `${action.action_serial}-output.txt`)}
                                                    title="Save output as file"
                                                  >
                                                    <SaveIcon fontSize="small" />
                                                  </IconButton>
                                                </Box>
                                              </Box>
                                              <Typography
                                                variant="body2"
                                                sx={{
                                                  fontFamily: 'monospace',
                                                  bgcolor: 'background.paper',
                                                  p: 1,
                                                  borderRadius: 1,
                                                  border: '1px solid',
                                                  borderColor: 'divider',
                                                  maxHeight: 150,
                                                  overflow: 'auto',
                                                  whiteSpace: 'pre-wrap'
                                                }}
                                              >
                                                {action.result_output}
                                              </Typography>
                                            </Box>
                                          )}
                                          
                                          {action.result_error && (
                                            <Box sx={{ mb: 1 }}>
                                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                                                <Typography variant="caption" sx={{ fontWeight: 'bold', color: 'error.main' }}>
                                                  Error:
                                                </Typography>
                                                <Box sx={{ display: 'flex', gap: 0.5 }}>
                                                  <IconButton
                                                    size="small"
                                                    onClick={() => copyToClipboard(action.result_error, 'Error')}
                                                    title="Copy error"
                                                  >
                                                    <CopyIcon fontSize="small" />
                                                  </IconButton>
                                                  <IconButton
                                                    size="small"
                                                    onClick={() => saveAsFile(action.result_error, `${action.action_serial}-error.txt`)}
                                                    title="Save error as file"
                                                  >
                                                    <SaveIcon fontSize="small" />
                                                  </IconButton>
                                                </Box>
                                              </Box>
                                              <Typography
                                                variant="body2"
                                                sx={{
                                                  fontFamily: 'monospace',
                                                  bgcolor: 'error.light',
                                                  color: 'error.contrastText',
                                                  p: 1,
                                                  borderRadius: 1,
                                                  maxHeight: 150,
                                                  overflow: 'auto',
                                                  whiteSpace: 'pre-wrap'
                                                }}
                                              >
                                                {action.result_error}
                                              </Typography>
                                            </Box>
                                          )}
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
                  </Collapse>
                </Box>
              ))}
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {results.length > 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <Pagination
            count={totalPages}
            page={page}
            onChange={handlePageChange}
            color="primary"
          />
        </Box>
      )}

      {/* Action Details Dialog */}
      <Dialog
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Action Details: {selectedAction?.action_serial}
        </DialogTitle>
        <DialogContent>
          {selectedAction && (
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>Basic Information</Typography>
                <Typography><strong>Action Name:</strong> {selectedAction.action_name}</Typography>
                <Typography><strong>Action Type:</strong> {selectedAction.action_type}</Typography>
                <Typography><strong>Action Order:</strong> {selectedAction.action_order}</Typography>
                <Typography><strong>Status:</strong> <Chip label={selectedAction.status} color={getStatusColor(selectedAction.status)} size="small" /></Typography>
                <Typography><strong>Exit Code:</strong> {selectedAction.exit_code}</Typography>
                <Typography><strong>Duration:</strong> {formatDuration(selectedAction.execution_time_ms)}</Typography>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>Context</Typography>
                <Typography><strong>Job:</strong> {selectedAction.job_name} ({selectedAction.job_serial})</Typography>
                <Typography><strong>Execution:</strong> {selectedAction.execution_serial}</Typography>
                <Typography><strong>Branch:</strong> {selectedAction.branch_serial}</Typography>
                <Typography><strong>Target:</strong> {selectedAction.target_name} ({selectedAction.target_serial})</Typography>
                <Typography><strong>Target Type:</strong> {selectedAction.target_type}</Typography>
              </Grid>
              
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>Timing</Typography>
                <Typography><strong>Started:</strong> {formatTimestamp(selectedAction.started_at)}</Typography>
                <Typography><strong>Completed:</strong> {formatTimestamp(selectedAction.completed_at)}</Typography>
                <Typography><strong>Created:</strong> {formatTimestamp(selectedAction.created_at)}</Typography>
              </Grid>
              
              {selectedAction.command_executed && (
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>Command</Typography>
                  <Typography
                    fontFamily="monospace"
                    sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1, whiteSpace: 'pre-wrap' }}
                  >
                    {selectedAction.command_executed}
                  </Typography>
                </Grid>
              )}
              
              {selectedAction.result_output && (
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>Output</Typography>
                  <Typography
                    fontFamily="monospace"
                    sx={{ 
                      bgcolor: 'grey.100', 
                      p: 2, 
                      borderRadius: 1, 
                      maxHeight: 300, 
                      overflow: 'auto',
                      whiteSpace: 'pre-wrap'
                    }}
                  >
                    {selectedAction.result_output}
                  </Typography>
                </Grid>
              )}
              
              {selectedAction.result_error && (
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom color="error">Error</Typography>
                  <Typography
                    fontFamily="monospace"
                    sx={{ 
                      bgcolor: 'error.light', 
                      color: 'error.contrastText',
                      p: 2, 
                      borderRadius: 1, 
                      maxHeight: 300, 
                      overflow: 'auto',
                      whiteSpace: 'pre-wrap'
                    }}
                  >
                    {selectedAction.result_error}
                  </Typography>
                </Grid>
              )}
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default LogViewer;