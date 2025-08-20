import React, { useState, useEffect } from 'react';
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  CircularProgress,
  Divider,

  Grid,
  Alert,
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

  PlayArrow as PlayArrowIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Cancel as CancelIcon,
  Assessment as AssessmentIcon,
  ExpandLess,
  ExpandMore,
  ContentCopy as CopyIcon,
  FindInPage as FindInPageIcon
} from '@mui/icons-material';
import { useSessionAuth } from '../../contexts/SessionAuthContext';
import { useNavigate } from 'react-router-dom';
import { formatLocalDateTime } from '../../utils/timeUtils';
import { getExecutionActionResults, formatExecutionTime, getActionStatusColor } from '../../services/jobService';
import ExecutionLogViewerModal from './ExecutionLogViewerModal';
import StandardDataTable from '../common/StandardDataTable';

import './JobExecutionHistoryModal.css';

const JobExecutionHistoryModal = ({ open, onClose, job }) => {
  console.log('JobExecutionHistoryModal rendered, open:', open);
  
  const { token } = useSessionAuth();
  const navigate = useNavigate();
  const [executions, setExecutions] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const [executionDetailsModal, setExecutionDetailsModal] = useState({ open: false, execution: null });
  const [selectedExecution, setSelectedExecution] = useState(null);
  const [expandedBranches, setExpandedBranches] = useState({});
  const [testExpanded, setTestExpanded] = useState(false);
  const [actionResults, setActionResults] = useState({});
  const [loadingActionResults, setLoadingActionResults] = useState({});
  const [logViewerModal, setLogViewerModal] = useState({ open: false, executionSerial: null });

  
  console.log('Current expandedBranches state in render:', expandedBranches);

  const fetchExecutions = async () => {
    if (!job) return;

    try {
      setLoading(true);
      const response = await fetch(`${process.env.REACT_APP_API_URL || ''}/jobs/${job.id}/executions`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        const executionsArray = Array.isArray(data) ? data : (data.executions || []);
        setExecutions(executionsArray);
        if (executionsArray.length > 0 && !selectedExecution) {
          setSelectedExecution(executionsArray[0]);
        }
      }
    } catch (error) {
      console.error('Error fetching executions:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open && job) {
      fetchExecutions();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, job]);

  const formatDate = (dateString) => {
    return formatLocalDateTime(dateString);
  };

  const formatDuration = (startDate, endDate) => {
    if (!startDate || !endDate) return 'N/A';
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffMs = end - start;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);

    if (diffHours > 0) {
      return `${diffHours}h ${diffMins % 60}m ${diffSecs % 60}s`;
    } else if (diffMins > 0) {
      return `${diffMins}m ${diffSecs % 60}s`;
    } else {
      return `${diffSecs}s`;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'scheduled': return 'info';
      case 'running': return 'primary';
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'cancelled': return 'secondary';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'scheduled': return <ScheduleIcon fontSize="small" />;
      case 'running': return <PlayArrowIcon fontSize="small" />;
      case 'completed': return <CheckCircleIcon fontSize="small" />;
      case 'failed': return <ErrorIcon fontSize="small" />;
      case 'cancelled': return <CancelIcon fontSize="small" />;
      default: return <ScheduleIcon fontSize="small" />;
    }
  };



  const getOverallStatus = (execution) => {
    if (!execution.branches || execution.branches.length === 0) {
      return execution.status;
    }

    const allCompleted = execution.branches.every(
      branch => branch.status === 'completed'
    );
    const anyFailed = execution.branches.some(
      branch => branch.status === 'failed'
    );
    const anyRunning = execution.branches.some(
      branch => branch.status === 'running'
    );

    if (anyRunning) return 'running';
    if (anyFailed) return 'failed';
    if (allCompleted) return 'completed';
    return execution.status;
  };

  // Show all executions, sorted by newest first
  const filteredExecutions = executions
    .sort((a, b) => new Date(b.started_at) - new Date(a.started_at));

  const handleBranchToggle = (branchId) => {
    setExpandedBranches(prev => ({
      ...prev,
      [branchId]: !prev[branchId]
    }));
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const openInLogViewer = (serial) => {
    console.log('Opening log viewer for execution serial:', serial);
    
    // Ensure the serial is in the correct format (jobId_executionNumber)
    let formattedSerial = serial;
    if (!serial.includes('_')) {
      console.warn('Serial does not contain underscore, attempting to format it');
      if (job && job.id) {
        formattedSerial = `${job.id}_${serial}`;
        console.log('Reformatted serial to:', formattedSerial);
      }
    }
    
    // Open the execution log viewer modal
    setLogViewerModal({ 
      open: true, 
      executionSerial: formattedSerial 
    });
    
    console.log('Log viewer modal state set:', { 
      open: true, 
      executionSerial: formattedSerial 
    });
  };

  const fetchActionResults = async (executionId) => {
    console.log('fetchActionResults called:', { executionId, jobId: job.id });
    
    if (actionResults[executionId]) {
      console.log('Action results already loaded for execution:', executionId);
      return; // Already loaded
    }

    try {
      setLoadingActionResults(prev => ({ ...prev, [executionId]: true }));
      console.log('Fetching action results...');
      const results = await getExecutionActionResults(job.id, executionId);
      console.log('Fetched action results:', results);
      setActionResults(prev => ({ ...prev, [executionId]: results }));
    } catch (error) {
      console.error('Error fetching action results:', error);
    } finally {
      setLoadingActionResults(prev => ({ ...prev, [executionId]: false }));
    }
  };

  const handleBranchToggleWithActionResults = (branchId, executionId) => {
    console.log('handleBranchToggleWithActionResults called:', { branchId, executionId });
    console.log('Current expandedBranches before update:', expandedBranches);
    
    const isCurrentlyExpanded = !!expandedBranches[branchId];
    console.log('isCurrentlyExpanded:', isCurrentlyExpanded);
    
    setExpandedBranches(prev => {
      const newState = {
        ...prev,
        [branchId]: !prev[branchId]
      };
      console.log('New expandedBranches state:', newState);
      return newState;
    });

    // Fetch action results when expanding
    if (!isCurrentlyExpanded) {
      console.log('Expanding branch, fetching action results...');
      fetchActionResults(executionId);
    } else {
      console.log('Collapsing branch');
    }
  };



  const ActionResults = ({ executionId, branchId }) => {
    console.log('ActionResults component rendered!', { executionId, branchId });
    
    const results = actionResults[executionId] || [];
    const loading = loadingActionResults[executionId];
    
    console.log('ActionResults Debug:', { executionId, branchId, results, loading });
    
    // Filter results for this specific branch, but if no branch_id matches, show all results
    // This handles cases where the branch_id might not match exactly
    let branchResults = results.filter(result => result.branch_id === branchId);
    if (branchResults.length === 0 && results.length > 0) {
      branchResults = results; // Show all results if no specific branch match
    }
    
    console.log('Filtered branchResults:', branchResults);

    if (loading) {
      return (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
          <LinearProgress sx={{ width: '100%' }} />
        </Box>
      );
    }

    if (branchResults.length === 0) {
      return (
        <Alert severity="info" sx={{ m: 2 }}>
          No individual action results available. This may be an older execution.
        </Alert>
      );
    }

    return (
      <Box sx={{ p: 2, bgcolor: 'grey.50', border: '1px solid red' }}>
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, color: 'primary.main' }}>
          Individual Action Results ({branchResults.length} actions)
        </Typography>
        <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
          Debug: executionId={executionId}, branchId={branchId}, results.length={results.length}
        </Typography>
        
        {branchResults.map((result, index) => (
          <Accordion key={result.id || index} sx={{ mb: 1 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                <Chip
                  icon={getStatusIcon(result.status)}
                  label={result.status}
                  color={getActionStatusColor(result.status)}
                  size="small"
                />
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                  {result.action_order}. {result.action_name}
                </Typography>
                <Box sx={{ flexGrow: 1 }} />
                <Typography variant="caption" color="text.secondary">
                  {formatExecutionTime(result.execution_time_ms)}
                </Typography>
                {result.exit_code !== null && (
                  <Chip
                    label={`Exit: ${result.exit_code}`}
                    color={result.exit_code === 0 ? 'success' : 'error'}
                    size="small"
                    variant="outlined"
                  />
                )}
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {result.command_executed && (
                  <Box>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                      Command:
                    </Typography>
                    <Paper variant="outlined" sx={{ p: 1, bgcolor: 'grey.50' }}>
                      <Typography variant="body2" component="pre" sx={{ fontFamily: 'monospace', margin: 0 }}>
                        {result.command_executed}
                      </Typography>
                    </Paper>
                  </Box>
                )}
                
                {result.result_output && (
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, color: 'success.main' }}>
                        Output:
                      </Typography>
                      <IconButton 
                        size="small" 
                        onClick={() => copyToClipboard(result.result_output)}
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
                          fontSize: '0.75rem',
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word',
                          margin: 0
                        }}
                      >
                        {result.result_output}
                      </Typography>
                    </Paper>
                  </Box>
                )}
                
                {result.result_error && (
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, color: 'error.main' }}>
                        Error:
                      </Typography>
                      <IconButton 
                        size="small" 
                        onClick={() => copyToClipboard(result.result_error)}
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
                        border: '1px solid',
                        borderColor: 'error.200',
                        maxHeight: '200px',
                        overflow: 'auto'
                      }}
                    >
                      <Typography 
                        variant="body2" 
                        component="pre" 
                        sx={{ 
                          fontFamily: 'monospace',
                          fontSize: '0.75rem',
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word',
                          margin: 0,
                          color: 'error.main'
                        }}
                      >
                        {result.result_error}
                      </Typography>
                    </Paper>
                  </Box>
                )}
                
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Started: {result.started_at ? formatDate(result.started_at) : 'N/A'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Completed: {result.completed_at ? formatDate(result.completed_at) : 'N/A'}
                  </Typography>
                </Box>
              </Box>
            </AccordionDetails>
          </Accordion>
        ))}
      </Box>
    );
  };

  const SimpleActionResults = ({ executionId }) => {
    console.log('SimpleActionResults props:', { executionId, jobId: job?.id });
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
      const fetchResults = async () => {
        console.log('🔍 Fetching action results:', { 
          jobId: job?.id, 
          executionId, 
          hasToken: !!token,
          tokenLength: token?.length 
        });
        
        if (!job?.id || !executionId || !token) {
          console.log('❌ Missing required data:', { jobId: job?.id, executionId, hasToken: !!token });
          setError('Missing required data for fetching results');
          setLoading(false);
          return;
        }
        
        try {
          setLoading(true);
          const url = `${process.env.REACT_APP_API_URL || ''}/jobs/${job.id}/executions/${executionId}/results`;
          console.log('📡 Making request to:', url);
          
          const response = await fetch(url, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });

          console.log('📡 Response status:', response.status, response.statusText);

          if (response.ok) {
            const data = await response.json();
            console.log('✅ Action results received:', data.length, 'results');
            setResults(data);
          } else {
            const errorText = await response.text();
            console.log('❌ API Error:', response.status, errorText);
            setError(`Failed to fetch action results: ${response.status} ${errorText}`);
          }
        } catch (err) {
          console.error('❌ Network Error:', err);
          setError(`Network error: ${err.message}`);
        } finally {
          setLoading(false);
        }
      };

      fetchResults();
    }, [executionId, token, job?.id]);

    if (loading) {
      return (
        <Box sx={{ p: 2, textAlign: 'center' }}>
          <CircularProgress size={20} />
          <Typography variant="body2" sx={{ mt: 1 }}>
            Loading action results for execution {executionId}...
          </Typography>
        </Box>
      );
    }

    if (error) {
      return (
        <Alert severity="error" sx={{ m: 2 }}>
          {error}
        </Alert>
      );
    }

    if (results.length === 0) {
      return (
        <Alert severity="info" sx={{ m: 2 }}>
          No action results found for execution {executionId}.
        </Alert>
      );
    }

    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Action Results for Execution {executionId}
        </Typography>
        {results.map((result, index) => (
          <Accordion key={index} sx={{ mb: 1 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                <Chip
                  label={result.status || 'Unknown'}
                  color={getActionStatusColor(result.status)}
                  size="small"
                />
                <Typography variant="subtitle2">
                  {result.action_name || `Action ${index + 1}`}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Branch ID: {result.branch_id} | {result.action_type || 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
                  {result.execution_time_ms}ms
                </Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Typography variant="body2"><strong>Command:</strong> {result.command_executed || 'N/A'}</Typography>
                  <Typography variant="body2"><strong>Exit Code:</strong> {result.exit_code !== null ? result.exit_code : 'N/A'}</Typography>
                  <Typography variant="body2"><strong>Duration:</strong> {result.execution_time_ms}ms</Typography>
                </Box>
                
                {result.result_output && (
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Output:
                    </Typography>
                    <Paper sx={{ p: 2, bgcolor: 'grey.50', fontFamily: 'monospace', fontSize: '0.875rem', maxHeight: '300px', overflow: 'auto' }}>
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{result.result_output}</pre>
                    </Paper>
                  </Box>
                )}
                
                {result.result_error && (
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Error Output:
                    </Typography>
                    <Paper sx={{ p: 2, bgcolor: 'error.light', color: 'error.contrastText', fontFamily: 'monospace', fontSize: '0.875rem', maxHeight: '300px', overflow: 'auto' }}>
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{result.result_error}</pre>
                    </Paper>
                  </Box>
                )}
                <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Started: {result.started_at ? formatDate(result.started_at) : 'N/A'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Completed: {result.completed_at ? formatDate(result.completed_at) : 'N/A'}
                  </Typography>
                </Box>
              </Box>
            </AccordionDetails>
          </Accordion>
        ))}
      </Box>
    );
  };

  const BranchDetails = ({ branches, expandedBranches = {}, handleBranchToggle, executionId }) => {
    if (!branches || branches.length === 0) {
      return (
        <Alert severity="info" sx={{ mt: 2 }}>
          No branch details available for this execution.
        </Alert>
      );
    }

    return (
      <Box>
        <TableContainer component={Paper} variant="outlined" className="standard-table-container">
          <Table size="small">
            <TableHead>
              <TableRow className="standard-header-row">
                <TableCell className="standard-table-header">Execution ID</TableCell>
                <TableCell className="standard-table-header">Target</TableCell>
                <TableCell className="standard-table-header">Status</TableCell>
                <TableCell className="standard-table-header">OS</TableCell>
                <TableCell className="standard-table-header">Started</TableCell>
                <TableCell className="standard-table-header">Duration</TableCell>
                <TableCell className="standard-table-header">Exit Code</TableCell>
                <TableCell className="standard-table-header" align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {branches.map((branch) => (
                <React.Fragment key={branch.id}>
                  <TableRow hover>
                    <TableCell className="standard-table-cell">
                      {branch.branch_serial || `${branch.branch_id}`}
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      {branch.ip_address ? `${branch.ip_address} - ${branch.target_name || `Target ${branch.target_id}`}` : (branch.target_name || `Target ${branch.target_id}`)}
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      <Chip 
                        label={branch.status} 
                        color={getStatusColor(branch.status)}
                        size="small"
                        sx={{ fontSize: '0.65rem', height: '20px' }}
                      />
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      {branch.os_type || 'N/A'}
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      {formatDate(branch.started_at)}
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      {formatDuration(branch.started_at, branch.completed_at)}
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      {branch.exit_code !== null ? branch.exit_code : 'N/A'}
                    </TableCell>
                    <TableCell className="standard-table-cell" align="center">
                      <IconButton 
                        className="btn-icon"
                        size="small" 
                        onClick={() => handleBranchToggle(branch.id, executionId)}
                        title="View individual action results"
                      >
                        {expandedBranches[branch.id] ? <ExpandLess /> : <ExpandMore />}
                      </IconButton>
                    </TableCell>
                  </TableRow>
                  
                  <TableRow>
                    <TableCell colSpan={8} sx={{ p: 0, border: 'none' }}>

                      <Collapse in={expandedBranches[branch.id]} timeout="auto" unmountOnExit>
                        <SimpleActionResults executionId={executionId} />
                      </Collapse>
                    </TableCell>
                  </TableRow>
                </React.Fragment>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    );
  };

  // Calculate paginated executions
  const totalExecutions = filteredExecutions.length;
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const paginatedExecutions = filteredExecutions.slice(startIndex, endIndex);

  const ExecutionList = () => {
    if (filteredExecutions.length === 0) {
      return (
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          flex: 1,
          textAlign: 'center',
          p: 4
        }}>
          <Box>
            <AssessmentIcon sx={{ fontSize: '4rem', color: 'text.disabled', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No Executions Found
            </Typography>
            <Typography variant="body2" color="text.disabled">
              This job has not been executed yet.
            </Typography>
          </Box>
        </Box>
      );
    }

    return (
      <StandardDataTable
        currentPage={currentPage}
        pageSize={pageSize}
        totalItems={totalExecutions}
        onPageChange={setCurrentPage}
        onPageSizeChange={setPageSize}
        itemLabel="executions"
      >
        <TableHead>
          <TableRow className="standard-header-row">
            <TableCell className="standard-table-header">Execution</TableCell>
            <TableCell className="standard-table-header">Status</TableCell>
            <TableCell className="standard-table-header">Started</TableCell>
            <TableCell className="standard-table-header">Duration</TableCell>
            <TableCell className="standard-table-header">Targets</TableCell>
            <TableCell className="standard-table-header" align="center">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {paginatedExecutions.map((execution) => {
            const overallStatus = getOverallStatus(execution);
            // Use duration_seconds from API if available, otherwise calculate from timestamps
            const duration = execution.duration_seconds 
              ? `${execution.duration_seconds.toFixed(2)}s`
              : formatDuration(execution.started_at, execution.completed_at);
            
            // Show target count only, not names
            const targetsDisplay = execution.target_names && execution.target_names.length > 0
              ? execution.target_names.length
              : (execution.total_targets || execution.branches?.length || 0);
            
            return (
              <TableRow 
                key={execution.id} 
                hover
                sx={{ cursor: 'pointer' }}
              >
                <TableCell className="standard-table-cell">
                  {execution.execution_serial || `#${execution.execution_number}`}
                </TableCell>
                <TableCell className="standard-table-cell">
                  <Chip 
                    label={overallStatus} 
                    color={getStatusColor(overallStatus)}
                    size="small"
                    sx={{ fontSize: '0.65rem', height: '20px' }}
                  />
                </TableCell>
                <TableCell className="standard-table-cell">
                  {formatDate(execution.started_at)}
                </TableCell>
                <TableCell className="standard-table-cell">
                  {duration}
                </TableCell>
                <TableCell className="standard-table-cell">
                  {targetsDisplay}
                </TableCell>
                <TableCell className="standard-table-cell" align="center">
                  <IconButton
                    className="btn-icon"
                    size="small"
                    onClick={() => openInLogViewer(`${job.id}_${execution.execution_number}`)}
                    title="View in Log Viewer"
                    sx={{ color: 'secondary.main' }}
                  >
                    <FindInPageIcon fontSize="small" />
                  </IconButton>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </StandardDataTable>
    );
  };

  const ExecutionDetailsModal = ({ open, onClose, execution }) => {
    const [expandedBranches, setExpandedBranches] = useState({});

    const handleBranchToggle = (branchId) => {
      setExpandedBranches(prev => ({
        ...prev,
        [branchId]: !prev[branchId]
      }));
    };

    if (!execution) return null;

    return (
      <Dialog 
        open={open} 
        onClose={onClose} 
        maxWidth="lg" 
        fullWidth
        PaperProps={{
          sx: { 
            height: '90vh',
            maxHeight: '1000px',
            borderRadius: 2,
            boxShadow: '0 12px 40px rgba(0,0,0,0.15)'
          }
        }}
      >
        <DialogTitle sx={{ 
          p: 3, 
          pb: 2,
          borderBottom: '1px solid',
          borderColor: 'divider',
          bgcolor: 'primary.50'
        }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ 
                p: 1.5, 
                borderRadius: 2, 
                bgcolor: 'primary.100',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <TimelineIcon sx={{ color: 'primary.main', fontSize: '1.5rem' }} />
              </Box>
              <Box>
                <Typography variant="h5" sx={{ fontWeight: 600, color: 'text.primary', mb: 0.5, fontFamily: 'monospace' }}>
                  {execution.execution_serial || `Execution #${execution.execution_number}`}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                  Target Execution Details
                </Typography>
              </Box>
            </Box>
            <Tooltip title="Close">
              <IconButton 
                onClick={onClose}
                sx={{ 
                  bgcolor: 'background.paper',
                  border: '1px solid',
                  borderColor: 'divider',
                  '&:hover': { bgcolor: 'grey.100' }
                }}
              >
                <CloseIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </DialogTitle>
        
        <DialogContent sx={{ p: 3, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <BranchDetails 
            branches={execution.branches} 
            expandedBranches={expandedBranches}
            handleBranchToggle={handleBranchToggleWithActionResults}
            executionId={execution.id}
          />
        </DialogContent>
        
        <DialogActions sx={{ 
          px: 3, 
          py: 2,
          borderTop: '1px solid',
          borderColor: 'divider',
          bgcolor: 'grey.50'
        }}>
          <Button 
            onClick={onClose} 
            variant="contained"
            sx={{ 
              px: 3,
              py: 1,
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 600
            }}
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>
    );
  };

  if (!job) return null;

  return (
    <>
      {/* Main Execution History Modal */}
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="lg" 
      fullWidth
      PaperProps={{
        sx: { 
          height: '85vh',
          maxHeight: '900px',
          borderRadius: 2,
          boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
          m: 2  // Add margin around the modal
        }
      }}
    >
      <DialogTitle className="page-header" sx={{ 
        padding: '16px 24px !important',  // Override the CSS !important rule
        paddingBottom: '16px !important'
      }}>
        {/* Use component="div" to avoid nesting heading elements */}
        <Typography variant="h4" className="page-title" component="div">
          Execution History - {job.name}
        </Typography>
        <Box className="page-actions">
          <Tooltip title="Refresh executions">
            <IconButton 
              onClick={fetchExecutions} 
              disabled={loading}
              size="small"
            >
              <RefreshIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Close">
            <IconButton 
              onClick={onClose}
              size="small"
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ px: 3, pb: 3, pt: 0, display: 'flex', flexDirection: 'column', height: '100%' }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flex: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Loading executions...
            </Typography>
          </Box>
        ) : (
          <Box className="table-content-area" sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <ExecutionList />
          </Box>
        )}
      </DialogContent>


    </Dialog>

    {/* Execution Details Modal */}
    <ExecutionDetailsModal 
      open={executionDetailsModal.open}
      onClose={() => setExecutionDetailsModal({ open: false, execution: null })}
      execution={executionDetailsModal.execution}
    />

    {/* Execution Log Viewer Modal */}
    <ExecutionLogViewerModal
      open={logViewerModal.open}
      onClose={() => setLogViewerModal({ open: false, executionSerial: null })}
      executionSerial={logViewerModal.executionSerial}
      jobName={job?.name}
    />

    </>
  );
};

export default JobExecutionHistoryModal;