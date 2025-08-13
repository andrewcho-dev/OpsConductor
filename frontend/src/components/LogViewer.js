import React, { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
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
  Visibility as ViewIcon,
  FilterList as FilterIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const LogViewer = () => {
  const { token } = useAuth();
  const location = useLocation();
  
  // State
  const [searchPattern, setSearchPattern] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [results, setResults] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedRows, setExpandedRows] = useState(new Set());
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
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} ${errorText}`);
    }

    return response.json();
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
      
      setResults(response.results || []);
      setTotalPages(Math.ceil(((response.results || []).length === ITEMS_PER_PAGE ? (offset + ITEMS_PER_PAGE + 1) : offset + (response.results || []).length) / ITEMS_PER_PAGE));
      
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

  // Toggle row expansion
  const toggleRowExpansion = (id) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedRows(newExpanded);
  };

  // Show action details
  const showActionDetails = (action) => {
    setSelectedAction(action);
    setDetailsOpen(true);
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
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Log Viewer
      </Typography>
      
      {/* Search Controls */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <Autocomplete
                freeSolo
                options={patternExamples}
                value={searchPattern}
                onInputChange={(event, newValue) => setSearchPattern(newValue || '')}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Search Pattern"
                    placeholder="Enter serial pattern or search term..."
                    fullWidth
                    helperText="Examples: J20250000001, J2025*.0001.*.*, setup"
                  />
                )}
              />
            </Grid>
            
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
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
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="contained"
                  startIcon={<SearchIcon />}
                  onClick={handleSearch}
                  disabled={loading}
                >
                  Search
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={() => performSearch(searchPattern, statusFilter, page)}
                  disabled={loading}
                >
                  Refresh
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={exportResults}
                  disabled={results.length === 0}
                >
                  Export
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Stats Summary */}
      {stats && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Search Results Summary
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6} md={2}>
                <Typography variant="body2" color="textSecondary">Total Actions</Typography>
                <Typography variant="h6">{stats.total_actions.toLocaleString()}</Typography>
              </Grid>
              <Grid item xs={6} md={2}>
                <Typography variant="body2" color="textSecondary">Unique Jobs</Typography>
                <Typography variant="h6">{stats.unique_jobs.toLocaleString()}</Typography>
              </Grid>
              <Grid item xs={6} md={2}>
                <Typography variant="body2" color="textSecondary">Unique Executions</Typography>
                <Typography variant="h6">{stats.unique_executions.toLocaleString()}</Typography>
              </Grid>
              <Grid item xs={6} md={2}>
                <Typography variant="body2" color="textSecondary">Unique Branches</Typography>
                <Typography variant="h6">{stats.unique_branches.toLocaleString()}</Typography>
              </Grid>
              <Grid item xs={6} md={2}>
                <Typography variant="body2" color="textSecondary">Unique Targets</Typography>
                <Typography variant="h6">{stats.unique_targets.toLocaleString()}</Typography>
              </Grid>
              <Grid item xs={6} md={2}>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {Object.entries(stats.status_counts).map(([status, count]) => (
                    count > 0 && (
                      <Chip
                        key={status}
                        label={`${status}: ${count}`}
                        color={getStatusColor(status)}
                        size="small"
                      />
                    )
                  ))}
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Results Table */}
      <Card>
        <CardContent>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell width="50px"></TableCell>
                  <TableCell>Action Serial</TableCell>
                  <TableCell>Action Name</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Exit Code</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Job</TableCell>
                  <TableCell>Target</TableCell>
                  <TableCell>Started</TableCell>
                  <TableCell width="100px">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={10} align="center">
                      <Typography>Loading...</Typography>
                    </TableCell>
                  </TableRow>
                ) : results.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={10} align="center">
                      <Typography color="textSecondary">
                        No results found. Try adjusting your search pattern.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  results.map((result) => (
                    <React.Fragment key={result.id}>
                      <TableRow hover>
                        <TableCell>
                          <IconButton
                            size="small"
                            onClick={() => toggleRowExpansion(result.id)}
                          >
                            {expandedRows.has(result.id) ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                          </IconButton>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {result.action_serial}
                          </Typography>
                        </TableCell>
                        <TableCell>{result.action_name}</TableCell>
                        <TableCell>
                          <Chip
                            label={result.status}
                            color={getStatusColor(result.status)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={result.exit_code}
                            color={result.exit_code === 0 ? 'success' : 'error'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{formatDuration(result.execution_time_ms)}</TableCell>
                        <TableCell>
                          <Tooltip title={result.job_serial}>
                            <Typography variant="body2" noWrap>
                              {result.job_name}
                            </Typography>
                          </Tooltip>
                        </TableCell>
                        <TableCell>
                          <Tooltip title={result.target_serial}>
                            <Typography variant="body2" noWrap>
                              {result.target_name}
                            </Typography>
                          </Tooltip>
                        </TableCell>
                        <TableCell>{formatTimestamp(result.started_at)}</TableCell>
                        <TableCell>
                          <IconButton
                            size="small"
                            onClick={() => showActionDetails(result)}
                            title="View Details"
                          >
                            <ViewIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                      
                      {/* Expanded Row Content */}
                      <TableRow>
                        <TableCell colSpan={10} sx={{ py: 0 }}>
                          <Collapse in={expandedRows.has(result.id)} timeout="auto" unmountOnExit>
                            <Box sx={{ p: 2, bgcolor: 'grey.50' }}>
                              <Grid container spacing={2}>
                                <Grid item xs={12} md={6}>
                                  <Typography variant="subtitle2" gutterBottom>
                                    Command Executed:
                                  </Typography>
                                  <Typography
                                    variant="body2"
                                    fontFamily="monospace"
                                    sx={{ bgcolor: 'grey.100', p: 1, borderRadius: 1 }}
                                  >
                                    {result.command_executed || 'N/A'}
                                  </Typography>
                                </Grid>
                                <Grid item xs={12} md={6}>
                                  <Typography variant="subtitle2" gutterBottom>
                                    Context:
                                  </Typography>
                                  <Typography variant="body2">
                                    <strong>Execution:</strong> {result.execution_serial}<br />
                                    <strong>Branch:</strong> {result.branch_serial}<br />
                                    <strong>Target Type:</strong> {result.target_type}<br />
                                    <strong>Action Order:</strong> {result.action_order}
                                  </Typography>
                                </Grid>
                                {result.result_output && (
                                  <Grid item xs={12}>
                                    <Typography variant="subtitle2" gutterBottom>
                                      Output:
                                    </Typography>
                                    <Typography
                                      variant="body2"
                                      fontFamily="monospace"
                                      sx={{ 
                                        bgcolor: 'grey.100', 
                                        p: 1, 
                                        borderRadius: 1,
                                        maxHeight: 200,
                                        overflow: 'auto',
                                        whiteSpace: 'pre-wrap'
                                      }}
                                    >
                                      {result.result_output}
                                    </Typography>
                                  </Grid>
                                )}
                                {result.result_error && (
                                  <Grid item xs={12}>
                                    <Typography variant="subtitle2" gutterBottom color="error">
                                      Error:
                                    </Typography>
                                    <Typography
                                      variant="body2"
                                      fontFamily="monospace"
                                      sx={{ 
                                        bgcolor: 'error.light', 
                                        color: 'error.contrastText',
                                        p: 1, 
                                        borderRadius: 1,
                                        maxHeight: 200,
                                        overflow: 'auto',
                                        whiteSpace: 'pre-wrap'
                                      }}
                                    >
                                      {result.result_error}
                                    </Typography>
                                  </Grid>
                                )}
                              </Grid>
                            </Box>
                          </Collapse>
                        </TableCell>
                      </TableRow>
                    </React.Fragment>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
          
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
        </CardContent>
      </Card>

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
    </Box>
  );
};

export default LogViewer;