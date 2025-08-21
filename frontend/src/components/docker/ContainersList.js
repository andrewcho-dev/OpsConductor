import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  IconButton,
  Button,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Tooltip,
  LinearProgress,
} from '@mui/material';
import {
  PlayArrow as StartIcon,
  Stop as StopIcon,
  RestartAlt as RestartIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Terminal as TerminalIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import dockerService from '../../services/dockerService';

const ContainersList = ({ containers, onRefresh, loading, onNotification }) => {
  const [selectedContainer, setSelectedContainer] = useState(null);
  const [logsDialog, setLogsDialog] = useState(false);
  const [logs, setLogs] = useState('');
  const [actionLoading, setActionLoading] = useState(null);

  const handleContainerAction = async (containerId, action) => {
    setActionLoading(containerId);
    let success = false;

    try {
      switch (action) {
        case 'start':
          success = await dockerService.startContainer(containerId);
          break;
        case 'stop':
          success = await dockerService.stopContainer(containerId);
          break;
        case 'restart':
          success = await dockerService.restartContainer(containerId);
          break;
        case 'remove':
          if (window.confirm('Are you sure you want to remove this container?')) {
            success = await dockerService.removeContainer(containerId);
          }
          break;
        default:
          break;
      }

      if (success) {
        onNotification && onNotification(`Container ${action} successful`, 'success');
        setTimeout(onRefresh, 1000); // Refresh after action
      } else {
        onNotification && onNotification(`Failed to ${action} container`, 'error');
      }
    } catch (error) {
      console.error(`Failed to ${action} container:`, error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleViewLogs = async (container) => {
    setSelectedContainer(container);
    setLogsDialog(true);
    
    try {
      const containerLogs = await dockerService.getContainerLogs(container.Id, 500);
      setLogs(containerLogs || 'No logs available');
    } catch (error) {
      setLogs('Failed to fetch logs');
    }
  };

  const getContainerStatus = (container) => {
    const state = container.State;
    return {
      color: state === 'running' ? 'success' : 
             state === 'exited' ? 'error' : 
             state === 'paused' ? 'warning' : 'default',
      label: state.toUpperCase()
    };
  };

  const formatContainerName = (names) => {
    return names[0]?.replace('/', '') || 'Unknown';
  };

  const formatUptime = (created) => {
    const now = new Date();
    const createdDate = new Date(created * 1000);
    const diffMs = now - createdDate;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    
    if (diffDays > 0) {
      return `${diffDays}d ${diffHours}h`;
    }
    return `${diffHours}h`;
  };

  if (loading) {
    return <LinearProgress />;
  }

  return (
    <Box>
      <Grid container spacing={3}>
        {containers.map((container) => {
          const status = getContainerStatus(container);
          const isLoading = actionLoading === container.Id;
          
          return (
            <Grid item xs={12} md={6} lg={4} key={container.Id}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Typography variant="h6" component="h3" sx={{ fontWeight: 600, fontSize: '1rem' }}>
                      {formatContainerName(container.Names)}
                    </Typography>
                    <Chip 
                      label={status.label} 
                      color={status.color} 
                      size="small"
                      sx={{ fontWeight: 600 }}
                    />
                  </Box>

                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    <strong>Image:</strong> {container.Image}
                  </Typography>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    <strong>Status:</strong> {container.Status}
                  </Typography>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    <strong>Created:</strong> {formatUptime(container.Created)} ago
                  </Typography>

                  {container.Ports && container.Ports.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        <strong>Ports:</strong>
                      </Typography>
                      {container.Ports.map((port, index) => (
                        <Chip
                          key={index}
                          label={`${port.PublicPort || '?'}:${port.PrivatePort}`}
                          size="small"
                          variant="outlined"
                          sx={{ mr: 0.5, mb: 0.5 }}
                        />
                      ))}
                    </Box>
                  )}

                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {container.State === 'running' ? (
                      <>
                        <Tooltip title="Stop">
                          <IconButton
                            size="small"
                            onClick={() => handleContainerAction(container.Id, 'stop')}
                            disabled={isLoading}
                            color="error"
                          >
                            <StopIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Restart">
                          <IconButton
                            size="small"
                            onClick={() => handleContainerAction(container.Id, 'restart')}
                            disabled={isLoading}
                            color="warning"
                          >
                            <RestartIcon />
                          </IconButton>
                        </Tooltip>
                      </>
                    ) : (
                      <Tooltip title="Start">
                        <IconButton
                          size="small"
                          onClick={() => handleContainerAction(container.Id, 'start')}
                          disabled={isLoading}
                          color="success"
                        >
                          <StartIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                    
                    <Tooltip title="View Logs">
                      <IconButton
                        size="small"
                        onClick={() => handleViewLogs(container)}
                        disabled={isLoading}
                      >
                        <ViewIcon />
                      </IconButton>
                    </Tooltip>
                    
                    <Tooltip title="Remove">
                      <IconButton
                        size="small"
                        onClick={() => handleContainerAction(container.Id, 'remove')}
                        disabled={isLoading || container.State === 'running'}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Logs Dialog */}
      <Dialog
        open={logsDialog}
        onClose={() => setLogsDialog(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Container Logs: {selectedContainer && formatContainerName(selectedContainer.Names)}
        </DialogTitle>
        <DialogContent>
          <TextField
            multiline
            rows={20}
            fullWidth
            value={logs}
            variant="outlined"
            InputProps={{
              readOnly: true,
              sx: { 
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                backgroundColor: '#f5f5f5'
              }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLogsDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ContainersList;