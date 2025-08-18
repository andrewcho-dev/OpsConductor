import React, { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Chip,
  IconButton,
  Tooltip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
  Alert,
  Paper,
  Divider,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Collapse
} from '@mui/material';
import {
  Close as CloseIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Search as SearchIcon,
  PlayArrow as PlayArrowIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Cancel as CancelIcon,
  ContentCopy as CopyIcon,
  Computer as ComputerIcon,
  Work as WorkIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
  Info as InfoIcon,
  UnfoldMore as ExpandAllIcon,
  UnfoldLess as CollapseAllIcon,
  ArrowBack as ArrowBackIcon
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { authService } from '../../services/authService';
import { formatLocalDateTime } from '../../utils/timeUtils';

const ExecutionLogViewerModal = ({ open, onClose, executionSerial, jobName }) => {
  const { token } = useAuth();
  
  // State management
  const [results, setResults] = useState([]);
  const [hierarchicalData, setHierarchicalData] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  
  // Expansion state
  const [expandedBranches, setExpandedBranches] = useState(new Set());
  const [expandedActions, setExpandedActions] = useState(new Set());
  
  // Filter state
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  // API helper
  const apiCall = async (url, options = {}) => {
    try {
      const response = await authService.api.get(url.replace('/api', ''), options);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || error.message || 'API call failed');
    }
  };

  // Transform flat results into hierarchical structure for this specific execution
  const transformToHierarchical = (flatResults) => {
    const branchMap = new Map();
    
    flatResults.forEach(action => {
      const branchKey = action.branch_serial;
      
      // Initialize branch
      if (!branchMap.has(branchKey)) {
        branchMap.set(branchKey, {
          id: branchKey,
          branch_serial: action.branch_serial,
          target_serial: action.target_serial,
          target_name: action.target_name,
          target_type: action.target_type,
          actions: [],
          stats: { total: 0, completed: 0, failed: 0, running: 0 }
        });
      }
      
      const branch = branchMap.get(branchKey);
      branch.stats.total++;
      if (action.status === 'completed') branch.stats.completed++;
      else if (action.status === 'failed') branch.stats.failed++;
      else if (action.status === 'running') branch.stats.running++;
      
      // Add action
      branch.actions.push(action);
    });
    
    // Convert to array and sort actions within each branch
    return Array.from(branchMap.values()).map(branch => ({
      ...branch,
      actions: branch.actions.sort((a, b) => {
        // Sort by action order if available, otherwise by started_at
        if (a.action_serial && b.action_serial) {
          const aOrder = parseInt(a.action_serial.split('.').pop());
          const bOrder = parseInt(b.action_serial.split('.').pop());
          return aOrder - bOrder;
        }
        return new Date(a.started_at) - new Date(b.started_at);
      })
    }));
  };

  // Search function for this specific execution
  const performSearch = useCallback(async (status = 'all') => {
    if (!executionSerial) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams({
        pattern: executionSerial,
        status,
        limit: '1000', // Get all actions for this execution
        offset: '0'
      });
      
      const response = await apiCall(`/api/v2/log-viewer/search?${params}`);
      const flatResults = response.results || [];
      
      setResults(flatResults);
      setHierarchicalData(transformToHierarchical(flatResults));
      setLastUpdated(new Date());
      
      // Calculate stats for this execution
      const executionStats = {
        total_actions: flatResults.length,
        completed: flatResults.filter(r => r.status === 'completed').length,
        failed: flatResults.filter(r => r.status === 'failed').length,
        running: flatResults.filter(r => r.status === 'running').length,
        branches: new Set(flatResults.map(r => r.branch_serial)).size
      };
      setStats(executionStats);
      
    } catch (err) {
      setError(err.message || 'Failed to load execution logs');
      setResults([]);
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, [executionSerial, token]);

  // Initialize when modal opens
  useEffect(() => {
    if (open && executionSerial) {
      performSearch(statusFilter);
    }
  }, [open, executionSerial, statusFilter, performSearch]);

  // Event handlers
  const handleRefresh = () => {
    performSearch(statusFilter);
  };

  const handleStatusFilterChange = (event) => {
    setStatusFilter(event.target.value);
  };

  // Toggle functions (kept for individual action toggling)
  const toggleBranch = (branchId) => {
    handleBranchToggle(branchId);
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

  // Expand/Collapse all functions
  const expandAll = () => {
    const allBranchIds = new Set(hierarchicalData.map(branch => branch.id));
    const allActionIds = new Set();
    hierarchicalData.forEach(branch => {
      branch.actions.forEach(action => {
        allActionIds.add(action.id);
      });
    });
    setExpandedBranches(allBranchIds);
    setExpandedActions(allActionIds);
  };

  // Auto-expand actions with results when branch is expanded
  const handleBranchToggle = (branchId) => {
    const newExpandedBranches = new Set(expandedBranches);
    const isExpanding = !newExpandedBranches.has(branchId);
    
    if (isExpanding) {
      newExpandedBranches.add(branchId);
      
      // Auto-expand actions that have output or errors
      const branch = hierarchicalData.find(b => b.id === branchId);
      if (branch) {
        const newExpandedActions = new Set(expandedActions);
        branch.actions.forEach(action => {
          if (action.result_output || action.result_error) {
            newExpandedActions.add(action.id);
          }
        });
        setExpandedActions(newExpandedActions);
      }
    } else {
      newExpandedBranches.delete(branchId);
      
      // Collapse all actions in this branch
      const branch = hierarchicalData.find(b => b.id === branchId);
      if (branch) {
        const newExpandedActions = new Set(expandedActions);
        branch.actions.forEach(action => {
          newExpandedActions.delete(action.id);
        });
        setExpandedActions(newExpandedActions);
      }
    }
    
    setExpandedBranches(newExpandedBranches);
  };

  const collapseAll = () => {
    setExpandedBranches(new Set());
    setExpandedActions(new Set());
  };

  // Keyboard shortcuts - defined after expandAll and collapseAll
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (!open) return;
      
      // Ctrl/Cmd + E = Expand All
      if ((event.ctrlKey || event.metaKey) && event.key === 'e') {
        event.preventDefault();
        expandAll();
      }
      
      // Ctrl/Cmd + Shift + E = Collapse All
      if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'E') {
        event.preventDefault();
        collapseAll();
      }
      
      // Escape = Close modal
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose();
      }
    };

    if (open) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [open, onClose]); // Removed expandAll and collapseAll from dependencies to avoid stale closures

  // Utility functions
  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'running': return 'primary';
      case 'scheduled': return 'info';
      case 'cancelled': return 'secondary';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed': return <CheckCircleIcon fontSize="small" />;
      case 'failed': return <ErrorIcon fontSize="small" />;
      case 'running': return <PlayArrowIcon fontSize="small" />;
      case 'scheduled': return <ScheduleIcon fontSize="small" />;
      case 'cancelled': return <CancelIcon fontSize="small" />;
      default: return <InfoIcon fontSize="small" />;
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const formatDuration = (timeMs) => {
    if (!timeMs) return 'N/A';
    if (timeMs < 1000) return `${timeMs}ms`;
    const seconds = Math.floor(timeMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  // Filter hierarchical data based on search term and status
  const filteredData = hierarchicalData.filter(branch => {
    const matchesSearch = !searchTerm || 
      branch.target_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      branch.target_serial.toLowerCase().includes(searchTerm.toLowerCase()) ||
      branch.actions.some(action => 
        action.action_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        action.command_executed?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    
    const matchesStatus = statusFilter === 'all' || 
      branch.actions.some(action => action.status === statusFilter);
    
    return matchesSearch && matchesStatus;
  });

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="lg" 
      fullWidth
      PaperProps={{
        sx: { height: '90vh', maxHeight: '90vh' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Tooltip title="Back to Execution History">
              <Button
                startIcon={<ArrowBackIcon />}
                onClick={onClose}
                variant="outlined"
                size="small"
                sx={{ textTransform: 'none' }}
              >
                Back
              </Button>
            </Tooltip>
            <Box>
              <Typography variant="h6" component="div">
                Execution Logs: {executionSerial}
              </Typography>
              {jobName && (
                <Typography variant="body2" color="text.secondary">
                  Job: {jobName}
                </Typography>
              )}
            </Box>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip title="Expand All (Ctrl+E)">
              <IconButton onClick={expandAll} disabled={loading || hierarchicalData.length === 0}>
                <ExpandAllIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Collapse All (Ctrl+Shift+E)">
              <IconButton onClick={collapseAll} disabled={loading || hierarchicalData.length === 0}>
                <CollapseAllIcon />
              </IconButton>
            </Tooltip>
            <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
            <Tooltip title="Refresh">
              <IconButton onClick={handleRefresh} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <IconButton onClick={onClose}>
              <CloseIcon />
            </IconButton>
          </Box>
        </Box>
      </DialogTitle>

      <DialogContent dividers sx={{ p: 0 }}>
        {/* Controls */}
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                size="small"
                placeholder="Search actions, commands, targets..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  label="Status"
                  onChange={handleStatusFilterChange}
                >
                  <MenuItem value="all">All Statuses</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="failed">Failed</MenuItem>
                  <MenuItem value="running">Running</MenuItem>
                  <MenuItem value="scheduled">Scheduled</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {stats && (
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Chip 
                      size="small" 
                      label={`${stats.total_actions} actions`} 
                      color="primary" 
                      variant="outlined" 
                    />
                    <Chip 
                      size="small" 
                      label={`${stats.branches} branches`} 
                      color="info" 
                      variant="outlined" 
                    />
                  </Box>
                )}
                <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                  Ctrl+E: Expand All • Ctrl+Shift+E: Collapse All
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Box>

        {/* Content */}
        <Box sx={{ p: 2 }}>
          {loading && <LinearProgress sx={{ mb: 2 }} />}
          
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {!loading && !error && filteredData.length === 0 && (
            <Alert severity="info">
              No execution logs found for {executionSerial}
            </Alert>
          )}

          {!loading && !error && filteredData.length > 0 && (
            <Alert severity="info" sx={{ mb: 2 }}>
              <strong>💡 Tip:</strong> Expand branches to see action results. Actions with output/errors will auto-expand and show "Output" or "Error" badges.
            </Alert>
          )}

          {!loading && !error && filteredData.length > 0 && (
            <Box>
              {filteredData.map((branch) => (
                <Accordion 
                  key={branch.id}
                  expanded={expandedBranches.has(branch.id)}
                  onChange={() => toggleBranch(branch.id)}
                  sx={{ mb: 1 }}
                >
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                      <ComputerIcon color="primary" />
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                          {branch.target_name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {branch.target_serial} • {branch.target_type}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Chip
                          size="small"
                          label={`${branch.stats.completed}/${branch.stats.total}`}
                          color={branch.stats.failed > 0 ? 'error' : 'success'}
                          variant="outlined"
                        />
                        {branch.stats.running > 0 && (
                          <Chip
                            size="small"
                            label={`${branch.stats.running} running`}
                            color="primary"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box sx={{ pl: 2 }}>
                      {branch.actions.map((action, index) => (
                        <Accordion
                          key={action.id}
                          expanded={expandedActions.has(action.id)}
                          onChange={() => toggleAction(action.id)}
                          sx={{ mb: 1, boxShadow: 1 }}
                        >
                          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                              <Chip
                                icon={getStatusIcon(action.status)}
                                label={action.status}
                                color={getStatusColor(action.status)}
                                size="small"
                              />
                              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                                {index + 1}. {action.action_name}
                              </Typography>
                              <Box sx={{ flexGrow: 1 }} />
                              {/* Result indicators */}
                              {action.result_output && (
                                <Chip
                                  label="Output"
                                  size="small"
                                  color="success"
                                  variant="outlined"
                                  sx={{ fontSize: '0.7rem', height: '20px' }}
                                />
                              )}
                              {action.result_error && (
                                <Chip
                                  label="Error"
                                  size="small"
                                  color="error"
                                  variant="outlined"
                                  sx={{ fontSize: '0.7rem', height: '20px', ml: 0.5 }}
                                />
                              )}
                              <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                                {formatDuration(action.execution_time_ms)}
                              </Typography>
                              {action.exit_code !== null && (
                                <Chip
                                  label={`Exit: ${action.exit_code}`}
                                  color={action.exit_code === 0 ? 'success' : 'error'}
                                  size="small"
                                  variant="outlined"
                                />
                              )}
                            </Box>
                          </AccordionSummary>
                          <AccordionDetails>
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                              {/* Action Details */}
                              <Box>
                                <Typography variant="body2" color="text.secondary" gutterBottom>
                                  <strong>Started:</strong> {formatLocalDateTime(action.started_at)}
                                  {action.completed_at && (
                                    <>
                                      {' • '}
                                      <strong>Completed:</strong> {formatLocalDateTime(action.completed_at)}
                                    </>
                                  )}
                                </Typography>
                              </Box>

                              {/* Command */}
                              {action.command_executed && (
                                <Box>
                                  <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                                    Command:
                                  </Typography>
                                  <Paper variant="outlined" sx={{ p: 1, bgcolor: 'grey.50', overflow: 'hidden' }}>
                                    <Typography 
                                      variant="body2" 
                                      component="pre" 
                                      sx={{ 
                                        fontFamily: 'monospace', 
                                        margin: 0,
                                        whiteSpace: 'pre-wrap',
                                        wordBreak: 'break-all',
                                        overflowWrap: 'break-word'
                                      }}
                                    >
                                      {action.command_executed}
                                    </Typography>
                                  </Paper>
                                </Box>
                              )}
                              
                              {/* Output */}
                              {action.result_output && (
                                <Box>
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                    <Typography variant="subtitle2" sx={{ fontWeight: 600, color: 'success.main' }}>
                                      Output:
                                    </Typography>
                                    <IconButton 
                                      size="small" 
                                      onClick={() => copyToClipboard(action.result_output)}
                                      title="Copy output"
                                    >
                                      <CopyIcon fontSize="small" />
                                    </IconButton>
                                  </Box>
                                  <Paper 
                                    variant="outlined" 
                                    sx={{ 
                                      p: 2, 
                                      bgcolor: 'background.paper',
                                      maxHeight: '200px',
                                      overflow: 'auto'
                                    }}
                                  >
                                    <Typography 
                                      variant="body2" 
                                      component="pre" 
                                      sx={{ 
                                        fontFamily: 'monospace',
                                        fontSize: '0.875rem',
                                        whiteSpace: 'pre-wrap',
                                        wordBreak: 'break-word',
                                        margin: 0
                                      }}
                                    >
                                      {action.result_output}
                                    </Typography>
                                  </Paper>
                                </Box>
                              )}

                              {/* Error */}
                              {action.result_error && (
                                <Box>
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                    <Typography variant="subtitle2" sx={{ fontWeight: 600, color: 'error.main' }}>
                                      Error:
                                    </Typography>
                                    <IconButton 
                                      size="small" 
                                      onClick={() => copyToClipboard(action.result_error)}
                                      title="Copy error"
                                    >
                                      <CopyIcon fontSize="small" />
                                    </IconButton>
                                  </Box>
                                  <Paper 
                                    variant="outlined" 
                                    sx={{ 
                                      p: 2, 
                                      bgcolor: 'error.50',
                                      maxHeight: '200px',
                                      overflow: 'auto'
                                    }}
                                  >
                                    <Typography 
                                      variant="body2" 
                                      component="pre" 
                                      sx={{ 
                                        fontFamily: 'monospace',
                                        fontSize: '0.875rem',
                                        whiteSpace: 'pre-wrap',
                                        wordBreak: 'break-word',
                                        margin: 0,
                                        color: 'error.main'
                                      }}
                                    >
                                      {action.result_error}
                                    </Typography>
                                  </Paper>
                                </Box>
                              )}
                            </Box>
                          </AccordionDetails>
                        </Accordion>
                      ))}
                    </Box>
                  </AccordionDetails>
                </Accordion>
              ))}
            </Box>
          )}

          {lastUpdated && (
            <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
              Last updated: {formatLocalDateTime(lastUpdated)}
            </Typography>
          )}
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default ExecutionLogViewerModal;