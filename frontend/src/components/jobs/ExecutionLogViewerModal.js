import React, { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Tooltip,
  LinearProgress,
  Alert,
  Paper,
  Button,

  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Collapse,
  Pagination,
  Select,
  MenuItem
} from '@mui/material';
import {
  Close as CloseIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Cancel as CancelIcon,
  ContentCopy as CopyIcon,
  Computer as ComputerIcon,
  KeyboardArrowDown as ArrowDownIcon,
  KeyboardArrowUp as ArrowUpIcon
} from '@mui/icons-material';
import { useSessionAuth } from '../../contexts/SessionAuthContext';
import { apiService } from '../../services/apiService';
import { formatLocalDateTime } from '../../utils/timeUtils';
import StandardDataTable from '../common/StandardDataTable';
import '../../styles/dashboard.css';

const ExecutionLogViewerModal = ({ open, onClose, executionSerial, jobName }) => {
  const { token } = useSessionAuth();
  
  // State management
  const [actions, setActions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  
  // Datatable state
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [expandedRows, setExpandedRows] = useState(new Set());
  
  // Page size options
  const pageSizeOptions = [25, 50, 100, 200];
  


  // API helper
  const apiCall = async (url, options = {}) => {
    try {
      console.log('Making API call to:', url);
      // Don't replace /api prefix as it might be needed
      const response = await apiService.get(`/${url}`);
      console.log('API response:', response.data);
      return response.data;
    } catch (error) {
      console.error('API call failed:', error);
      throw new Error(error.response?.data?.detail || error.message || 'API call failed');
    }
  };

  // Helper functions for datatable
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'running': return 'warning';
      case 'scheduled': return 'info';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon fontSize="small" />;
      case 'failed': return <ErrorIcon fontSize="small" />;
      case 'running': return <ScheduleIcon fontSize="small" />;
      default: return <CancelIcon fontSize="small" />;
    }
  };

  // Fetch execution data
  const fetchExecutionData = useCallback(async () => {
    if (!executionSerial) {
      console.log('No execution serial provided');
      return;
    }
    
    console.log('Fetching execution data for serial:', executionSerial);
    setLoading(true);
    setError(null);
    
    try {
      // Parse executionSerial format: "jobId_executionNumber"
      const [jobId, executionNumber] = executionSerial.split('_');
      console.log('Parsed execution serial:', { jobId, executionNumber });
      
      if (!jobId || !executionNumber) {
        throw new Error('Invalid execution serial format. Expected format: jobId_executionNumber');
      }
      
      // Use the standard API endpoint as defined in the environment
      try {
        console.log(`Fetching execution logs for job ${jobId}, execution ${executionNumber}`);
        
        // First try to get the execution details
        const executionResponse = await apiService.get(`/jobs/${jobId}/executions/${executionNumber}`);
        console.log('Execution details response:', executionResponse.data);
        
        // The execution details endpoint now exists and returns ExecutionResponse
        // Try to fetch execution results to get detailed action information
        try {
          const resultsResponse = await apiService.get(`/jobs/${jobId}/executions/${executionNumber}/results`);
          console.log('Execution results response:', resultsResponse.data);
          
          // Transform the results to match the expected action format
          if (resultsResponse.data && Array.isArray(resultsResponse.data)) {
            const actionEntries = resultsResponse.data.map(result => ({
              id: result.id,
              target_name: result.target_name,
              target_ip: result.target_id, // We don't have IP in results, using target_id as fallback
              action_name: result.action_name,
              status: result.status,
              started_at: result.started_at,
              finished_at: result.completed_at,
              exit_code: result.exit_code,
              result_output: result.output_text,
              result_error: result.error_text,
              execution_time_ms: result.execution_time_ms,
              action_type: result.action_type
            }));
            
            console.log('Processed action entries from results:', actionEntries);
            setActions(actionEntries);
            setLastUpdated(new Date());
            return;
          }
        } catch (resultsError) {
          console.error('Failed to fetch detailed results:', resultsError);
        }
        
        // If we can't get detailed results, create a summary entry from execution details
        if (executionResponse.data) {
          const executionData = executionResponse.data;
          const summaryAction = {
            id: executionData.id || `execution-${jobId}-${executionNumber}`,
            target_name: executionData.target_names?.join(', ') || 'Multiple Targets',
            target_ip: executionData.total_targets || 'N/A',
            action_name: 'Job Execution Summary',
            status: executionData.status,
            started_at: executionData.started_at,
            finished_at: executionData.completed_at,
            exit_code: null,
            result_output: `Execution completed on ${executionData.total_targets} targets. ${executionData.successful_targets} successful, ${executionData.failed_targets} failed.`,
            result_error: executionData.failed_targets > 0 ? `${executionData.failed_targets} targets failed` : null,
            execution_time_ms: executionData.duration_seconds ? Math.round(executionData.duration_seconds * 1000) : null
          };
          
          console.log('Created summary action from execution data:', summaryAction);
          setActions([summaryAction]);
          setLastUpdated(new Date());
          return;
        }
        
      } catch (executionError) {
        console.error('Failed to fetch execution details:', executionError);
        throw new Error('Could not fetch execution details');
      }
      
    } catch (err) {
      console.error('Error fetching execution data:', err);
      setError(`Failed to load execution logs: ${err.message}`);
      setActions([]);
    } finally {
      setLoading(false);
    }
  }, [executionSerial]);

  // Initialize when modal opens
  useEffect(() => {
    if (open && executionSerial) {
      fetchExecutionData();
    }
  }, [open, executionSerial, fetchExecutionData]);

  // Event handlers
  const handleRefresh = () => {
    fetchExecutionData();
  };

  const handlePageSizeChange = (newPageSize) => {
    setPageSize(newPageSize);
    setPage(1); // Reset to first page when changing page size
  };



  // Datatable functions
  const toggleRowExpansion = (actionId) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(actionId)) {
      newExpanded.delete(actionId);
    } else {
      newExpanded.add(actionId);
    }
    setExpandedRows(newExpanded);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      // Could add a toast notification here
    });
  };

  // Pagination logic
  const totalPages = Math.ceil(actions.length / pageSize);
  const startIndex = (page - 1) * pageSize;
  const paginatedActions = actions.slice(startIndex, startIndex + pageSize);

  const formatDuration = (startTime, endTime) => {
    if (!startTime || !endTime) return 'N/A';
    const duration = new Date(endTime) - new Date(startTime);
    if (duration < 1000) return `${duration}ms`;
    const seconds = Math.floor(duration / 1000);
    const minutes = Math.floor(seconds / 60);
    if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    }
    return `${seconds}s`;
  };

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="xl" 
      fullWidth
      PaperProps={{
        sx: { height: '90vh', maxHeight: '90vh' }
      }}
    >
      <DialogTitle className="page-header" sx={{ 
        padding: '16px 24px !important',
        paddingBottom: '16px !important'
      }}>
        {/* Use component="div" to avoid nesting heading elements */}
        <Typography variant="h4" className="page-title" component="div">
          Execution Logs - {executionSerial}
        </Typography>
        {jobName && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            Job: {jobName}
          </Typography>
        )}
        <Box className="page-actions">
          {/* Wrap disabled buttons in span for Tooltip */}
          <Tooltip title={expandedRows.size === paginatedActions.length ? "Collapse All" : "Expand All"}>
            {loading || paginatedActions.length === 0 ? (
              <span>
                <IconButton 
                  onClick={() => {}}
                  disabled={true}
                  size="small"
                >
                  {expandedRows.size === paginatedActions.length ? 
                    <ArrowUpIcon fontSize="small" /> : 
                    <ArrowDownIcon fontSize="small" />
                  }
                </IconButton>
              </span>
            ) : (
              <IconButton 
                onClick={() => {
                  if (expandedRows.size === paginatedActions.length) {
                    // Collapse all
                    setExpandedRows(new Set());
                  } else {
                    // Expand all
                    const allIds = new Set(paginatedActions.map(action => action.id));
                    setExpandedRows(allIds);
                  }
                }}
                size="small"
              >
                {expandedRows.size === paginatedActions.length ? 
                  <ArrowUpIcon fontSize="small" /> : 
                  <ArrowDownIcon fontSize="small" />
                }
              </IconButton>
            )}
          </Tooltip>
          <Tooltip title="Refresh">
            {loading ? (
              <span>
                <IconButton 
                  disabled={true}
                  size="small"
                >
                  <RefreshIcon fontSize="small" />
                </IconButton>
              </span>
            ) : (
              <IconButton 
                onClick={handleRefresh} 
                size="small"
              >
                <RefreshIcon fontSize="small" />
              </IconButton>
            )}
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

      <DialogContent sx={{ px: 3, pb: 3, pt: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {loading && <LinearProgress />}
        
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {!loading && actions.length === 0 && !error && (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No execution logs found
            </Typography>
            <Typography variant="body2" color="text.secondary">
              There are no logs available for this execution. This could be because:
            </Typography>
            <Box component="ul" sx={{ textAlign: 'left', display: 'inline-block', mt: 2 }}>
              <Typography component="li" variant="body2" color="text.secondary">
                The execution is still pending or scheduled
              </Typography>
              <Typography component="li" variant="body2" color="text.secondary">
                The execution did not generate any logs
              </Typography>
              <Typography component="li" variant="body2" color="text.secondary">
                The logs have been purged from the system
              </Typography>
            </Box>
            <Box sx={{ mt: 3 }}>
              <Button 
                variant="outlined" 
                color="primary" 
                onClick={handleRefresh}
                startIcon={<RefreshIcon />}
              >
                Refresh Logs
              </Button>
            </Box>
          </Box>
        )}

        {!loading && actions.length > 0 && (
          /* Standard Datatable */
          <StandardDataTable
            currentPage={page}
            pageSize={pageSize}
            totalItems={actions.length}
            onPageChange={setPage}
            onPageSizeChange={handlePageSizeChange}
            itemLabel="actions"
            className="execution-log-table"
          >
            <TableHead>
              <TableRow className="standard-header-row">
                <TableCell className="standard-table-header" sx={{ width: 40 }}>
                  {/* Expand column */}
                </TableCell>
                <TableCell className="standard-table-header" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>IP Address</TableCell>
                <TableCell className="standard-table-header" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>Target</TableCell>
                <TableCell className="standard-table-header" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>Action</TableCell>
                <TableCell className="standard-table-header" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>Status</TableCell>
                <TableCell className="standard-table-header" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>Started</TableCell>
                <TableCell className="standard-table-header" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>Duration</TableCell>
                <TableCell className="standard-table-header" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>Exit Code</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {!loading && paginatedActions.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                    <Typography color="text.secondary">
                      No execution logs found.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
              
              {paginatedActions.map((action) => (
                <React.Fragment key={action.id}>
                  <TableRow 
                    hover 
                    className="standard-table-row"
                    sx={{ 
                      '&:hover': { backgroundColor: 'action.hover' },
                      borderLeft: 3,
                      borderLeftColor: `${getStatusColor(action.status)}.main`
                    }}
                  >
                    <TableCell className="standard-table-cell">
                      {(!action.result_output && !action.result_error && !action.command_executed) ? (
                        <span>
                          <IconButton
                            size="small"
                            disabled={true}
                          >
                            <ArrowDownIcon />
                          </IconButton>
                        </span>
                      ) : (
                        <IconButton
                          size="small"
                          onClick={() => toggleRowExpansion(action.id)}
                        >
                          {expandedRows.has(action.id) ? <ArrowUpIcon /> : <ArrowDownIcon />}
                        </IconButton>
                      )}
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {action.target_ip || action.ip_address || action.host || 'N/A'}
                      </Typography>
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 500 }}>
                        {action.target_name}
                      </Typography>
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 500 }}>
                        {action.action_name}
                      </Typography>
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      <Chip 
                        label={action.status} 
                        size="small" 
                        color={getStatusColor(action.status)} 
                        icon={getStatusIcon(action.status)}
                      />
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {action.started_at ? formatLocalDateTime(action.started_at) : 'N/A'}
                      </Typography>
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {formatDuration(action.started_at, action.finished_at)}
                      </Typography>
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {(action.exit_code !== null && action.exit_code !== undefined) ? action.exit_code : 
                         (action.return_code !== null && action.return_code !== undefined) ? action.return_code : 'N/A'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                  
                  {/* Expandable row for results */}
                  <TableRow>
                    <TableCell colSpan={8} sx={{ p: 0, border: 0 }}>
                      <Collapse in={expandedRows.has(action.id)} timeout="auto" unmountOnExit>
                        <Box sx={{ p: 2, bgcolor: 'grey.50', borderTop: 1, borderColor: 'divider' }}>
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            
                            {/* Command */}
                            {action.command_executed && (
                              <Box>
                                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                                  Command:
                                </Typography>
                                <Paper variant="outlined" sx={{ p: 1, bgcolor: 'background.paper' }}>
                                  <Typography 
                                    variant="body2" 
                                    component="pre" 
                                    sx={{ 
                                      fontFamily: 'monospace', 
                                      margin: 0,
                                      whiteSpace: 'pre-wrap',
                                      wordBreak: 'break-all'
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
                                    maxHeight: '300px',
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
                                    bgcolor: 'error.light',
                                    maxHeight: '300px',
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
                        </Box>
                      </Collapse>
                    </TableCell>
                  </TableRow>
                </React.Fragment>
              ))}
            </TableBody>
          </StandardDataTable>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default ExecutionLogViewerModal;