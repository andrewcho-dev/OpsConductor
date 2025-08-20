/**
 * SIMPLE TARGET RESULTS MODAL - JUST SHOW THE FUCKING SERIALIZATION DATA!
 * No complex bullshit - just display the hierarchy tree using the serial numbers
 */
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  IconButton,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Paper,
  Divider
} from '@mui/material';
import {
  Close as CloseIcon,
  Computer as ComputerIcon,
  ExpandMore as ExpandMoreIcon
} from '@mui/icons-material';

import { useSessionAuth } from '../../contexts/SessionAuthContext';

const SimpleTargetResultsModal = ({ open, onClose, executionSerial }) => {
  const { token } = useSessionAuth();
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && executionSerial) {
      fetchTargetResults();
    }
  }, [open, executionSerial]);

  const fetchTargetResults = async () => {
    setLoading(true);
    try {
      // Parse executionSerial format: "jobId_executionNumber"
      const [jobId, executionNumber] = executionSerial.split('_');
      
      if (!jobId || !executionNumber) {
        console.error('Invalid execution serial format. Expected format: jobId_executionNumber');
        return;
      }
      
      // Get execution results using the correct API endpoint
      const response = await fetch(`${process.env.REACT_APP_API_URL || ''}/jobs/${jobId}/executions/${executionNumber}/results`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Target results:', data);
        setResults(data || []);
      } else {
        console.error('Failed to fetch target results');
      }
    } catch (error) {
      console.error('Error fetching target results:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'running': return 'info';
      case 'scheduled': return 'default';
      default: return 'default';
    }
  };

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="lg" 
      fullWidth
      PaperProps={{
        sx: { 
          height: '80vh',
          maxHeight: '600px'
        }
      }}
    >
      <DialogTitle sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        pb: 1
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ComputerIcon />
          <Typography variant="h6">
            Target Results for {executionSerial}
          </Typography>
        </Box>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ p: 0 }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Box sx={{ p: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Complete execution hierarchy showing all target results with their serial numbers
            </Typography>

            <TableContainer sx={{ maxHeight: '400px', border: '1px solid', borderColor: 'divider' }}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Branch Serial</TableCell>
                    <TableCell>Target Serial</TableCell>
                    <TableCell>Target Name</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Exit Code</TableCell>
                    <TableCell>Action Results</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {results.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
                          <ComputerIcon sx={{ fontSize: 48, color: 'text.disabled' }} />
                          <Typography variant="body2" color="text.secondary">
                            No target results found for this execution
                          </Typography>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ) : (
                    results.map((result) => (
                      <TableRow key={result.branch_serial} hover>
                        <TableCell>
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              fontFamily: 'monospace', 
                              fontWeight: 600,
                              color: 'primary.main'
                            }}
                          >
                            {result.branch_serial}
                          </Typography>
                        </TableCell>
                        
                        <TableCell>
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              fontFamily: 'monospace', 
                              fontWeight: 500,
                              color: 'secondary.main'
                            }}
                          >
                            {result.target_serial_ref || 'N/A'}
                          </Typography>
                        </TableCell>
                        
                        <TableCell>
                          <Typography variant="body2">
                            {result.target?.name || 'Unknown Target'}
                          </Typography>
                          {result.target?.ip_address && (
                            <Typography variant="caption" color="text.secondary" display="block">
                              {result.target.ip_address}
                            </Typography>
                          )}
                        </TableCell>
                        
                        <TableCell>
                          <Chip 
                            label={result.status} 
                            size="small"
                            color={getStatusColor(result.status)}
                          />
                        </TableCell>
                        
                        <TableCell>
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              fontFamily: 'monospace',
                              color: result.exit_code === 0 ? 'success.main' : 'error.main'
                            }}
                          >
                            {result.exit_code !== null ? result.exit_code : 'N/A'}
                          </Typography>
                        </TableCell>
                        
                        <TableCell>
                          {result.action_results && result.action_results.length > 0 ? (
                            <Box>
                              {result.action_results.map((action, actionIndex) => (
                                <Accordion key={actionIndex} sx={{ mb: 1, boxShadow: 1 }}>
                                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                                      <Chip
                                        label={action.status || 'Unknown'}
                                        color={getStatusColor(action.status)}
                                        size="small"
                                      />
                                      <Typography variant="subtitle2">
                                        {action.action_name || `Action ${actionIndex + 1}`}
                                      </Typography>
                                      <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
                                        {action.execution_time_ms}ms
                                      </Typography>
                                    </Box>
                                  </AccordionSummary>
                                  <AccordionDetails>
                                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                                        <Typography variant="body2"><strong>Command:</strong> {action.command_executed || 'N/A'}</Typography>
                                        <Typography variant="body2"><strong>Exit Code:</strong> {action.exit_code !== null ? action.exit_code : 'N/A'}</Typography>
                                        <Typography variant="body2"><strong>Duration:</strong> {action.execution_time_ms}ms</Typography>
                                      </Box>
                                      
                                      {action.result_output && (
                                        <Box>
                                          <Typography variant="subtitle2" gutterBottom>
                                            Output:
                                          </Typography>
                                          <Paper sx={{ p: 2, bgcolor: 'grey.50', fontFamily: 'monospace', fontSize: '0.875rem', maxHeight: '300px', overflow: 'auto' }}>
                                            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{action.result_output}</pre>
                                          </Paper>
                                        </Box>
                                      )}
                                      
                                      {action.result_error && (
                                        <Box>
                                          <Typography variant="subtitle2" gutterBottom>
                                            Error Output:
                                          </Typography>
                                          <Paper sx={{ p: 2, bgcolor: 'error.light', color: 'error.contrastText', fontFamily: 'monospace', fontSize: '0.875rem', maxHeight: '300px', overflow: 'auto' }}>
                                            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{action.result_error}</pre>
                                          </Paper>
                                        </Box>
                                      )}
                                    </Box>
                                  </AccordionDetails>
                                </Accordion>
                              ))}
                            </Box>
                          ) : (
                            <Typography variant="body2" color="text.secondary">
                              No detailed action results available
                            </Typography>
                          )}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>

            {results.length > 0 && (
              <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  <strong>Serialization Hierarchy:</strong><br/>
                  • Job Serial: {executionSerial ? executionSerial.split('.')[0] : 'N/A'}<br/>
                  • Execution Serial: {executionSerial || 'N/A'}<br/>
                  • Branch Serials: {results.map(r => r.branch_serial).join(', ')}
                </Typography>
              </Box>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
        <Button onClick={onClose} variant="contained">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SimpleTargetResultsModal;