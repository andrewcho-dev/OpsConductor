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
import { authService } from '../../services/authService';
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
      const response = await authService.api.get(url.replace('/api', ''), options);
      return response.data;
    } catch (error) {
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
    if (!executionSerial) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // Parse executionSerial format: "jobId_executionNumber"
      const [jobId, executionNumber] = executionSerial.split('_');
      
      const params = new URLSearchParams({
        job_id: jobId,
        execution_number: executionNumber,
        limit: '1000', // Get all actions for this execution
        offset: '0'
      });
      
      const response = await apiCall(`/logs/entries?${params}`);
      const actionResults = response.results || [];
      
      // Sort actions by branch and action order
      const sortedActions = actionResults.sort((a, b) => {
        // First sort by branch_serial
        if (a.branch_serial !== b.branch_serial) {
          return a.branch_serial.localeCompare(b.branch_serial);
        }
        // Then by action order within branch
        if (a.action_serial && b.action_serial) {
          const aOrder = parseInt(a.action_serial.split('.').pop());
          const bOrder = parseInt(b.action_serial.split('.').pop());
          return aOrder - bOrder;
        }
        return new Date(a.started_at) - new Date(b.started_at);
      });
      
      setActions(sortedActions);
      setLastUpdated(new Date());
      
    } catch (err) {
      setError(err.message || 'Failed to load execution logs');
      setActions([]);
    } finally {
      setLoading(false);
    }
  }, [executionSerial, token]);

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
        <Typography variant="h4" className="page-title">
          Execution Logs - {executionSerial}
        </Typography>
        {jobName && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            Job: {jobName}
          </Typography>
        )}
        <Box className="page-actions">
          <Tooltip title={expandedRows.size === paginatedActions.length ? "Collapse All" : "Expand All"}>
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
              disabled={loading || paginatedActions.length === 0}
              size="small"
            >
              {expandedRows.size === paginatedActions.length ? 
                <ArrowUpIcon fontSize="small" /> : 
                <ArrowDownIcon fontSize="small" />
              }
            </IconButton>
          </Tooltip>
          <Tooltip title="Refresh">
            <IconButton 
              onClick={handleRefresh} 
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

      <DialogContent sx={{ px: 3, pb: 3, pt: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {loading && <LinearProgress />}
        
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}



        {/* Standard Datatable */}
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
                      <IconButton
                        size="small"
                        onClick={() => toggleRowExpansion(action.id)}
                        disabled={!action.result_output && !action.result_error && !action.command_executed}
                      >
                        {expandedRows.has(action.id) ? <ArrowUpIcon /> : <ArrowDownIcon />}
                      </IconButton>
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
      </DialogContent>
    </Dialog>
  );
};

export default ExecutionLogViewerModal;