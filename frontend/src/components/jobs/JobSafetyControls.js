/**
 * Job Safety Controls - Emergency controls for job management
 */
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Chip,
  Grid,
  CircularProgress,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Stop as StopIcon,
  CleaningServices as CleanupIcon,
  Security as SecurityIcon,
  HealthAndSafety as HealthIcon,
} from '@mui/icons-material';

const JobSafetyControls = ({ onRefresh, token }) => {
  const [loading, setLoading] = useState(false);
  const [terminateDialog, setTerminateDialog] = useState({ open: false, jobId: null });
  const [terminateReason, setTerminateReason] = useState('');
  const [healthStatus, setHealthStatus] = useState(null);
  const [lastCleanup, setLastCleanup] = useState(null);

  const handleCleanupStaleJobs = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/jobs/safety/cleanup-stale', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      const result = await response.json();
      
      if (result.success) {
        setLastCleanup(result.data);
        if (onRefresh) onRefresh();
        
        // Show success message
        console.log('Cleanup completed:', result.data);
      } else {
        console.error('Cleanup failed:', result);
      }
    } catch (error) {
      console.error('Error during cleanup:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTerminateJob = async () => {
    if (!terminateDialog.jobId) return;

    try {
      setLoading(true);
      const response = await fetch(`/api/jobs/safety/terminate/${terminateDialog.jobId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ reason: terminateReason || 'Manual termination' }),
      });

      const result = await response.json();
      
      if (result.success) {
        setTerminateDialog({ open: false, jobId: null });
        setTerminateReason('');
        if (onRefresh) onRefresh();
        console.log('Job terminated successfully');
      } else {
        console.error('Termination failed:', result);
      }
    } catch (error) {
      console.error('Error terminating job:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGetHealthStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/jobs/safety/health', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      const result = await response.json();
      
      if (result.success) {
        setHealthStatus(result.data);
      } else {
        console.error('Health check failed:', result);
      }
    } catch (error) {
      console.error('Error getting health status:', error);
    } finally {
      setLoading(false);
    }
  };

  const openTerminateDialog = (jobId) => {
    setTerminateDialog({ open: true, jobId });
    setTerminateReason('');
  };

  return (
    <>
      <Box display="flex" gap={1} alignItems="center">
        <Button
          variant="outlined"
          color="warning"
          startIcon={<CleanupIcon fontSize="small" />}
          onClick={handleCleanupStaleJobs}
          disabled={loading}
          size="small"
          sx={{ fontSize: '0.75rem', minWidth: 'auto' }}
        >
          {loading ? <CircularProgress size={16} /> : 'Cleanup'}
        </Button>
        
        <Button
          variant="outlined"
          color="info"
          startIcon={<HealthIcon fontSize="small" />}
          onClick={handleGetHealthStatus}
          disabled={loading}
          size="small"
          sx={{ fontSize: '0.75rem', minWidth: 'auto' }}
        >
          Health Check
        </Button>
        
        <Tooltip title="Use checkboxes in the job table to terminate specific jobs">
          <Button
            variant="outlined"
            color="info"
            startIcon={<SecurityIcon fontSize="small" />}
            disabled={true}
            size="small"
            sx={{ fontSize: '0.75rem', minWidth: 'auto', opacity: 0.6 }}
          >
            Use Table Actions
          </Button>
        </Tooltip>
        
        {healthStatus && (
          <Chip
            label={healthStatus.health_status}
            color={healthStatus.health_status === 'healthy' ? 'success' : 'warning'}
            size="small"
            sx={{ fontSize: '0.7rem', height: '24px' }}
          />
        )}
      </Box>

      {/* Terminate Job Dialog */}
      <Dialog open={terminateDialog.open} onClose={() => setTerminateDialog({ open: false, jobId: null })}>
        <DialogTitle>
          <Box display="flex" alignItems="center">
            <WarningIcon color="error" sx={{ mr: 1 }} />
            Force Terminate Job
          </Box>
        </DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            This will forcefully terminate Job ID {terminateDialog.jobId}. This action cannot be undone.
          </Alert>
          <TextField
            fullWidth
            label="Termination Reason"
            value={terminateReason}
            onChange={(e) => setTerminateReason(e.target.value)}
            placeholder="Enter reason for termination..."
            multiline
            rows={2}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTerminateDialog({ open: false, jobId: null })}>
            Cancel
          </Button>
          <Button
            onClick={handleTerminateJob}
            color="error"
            variant="contained"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={16} /> : <StopIcon />}
          >
            Force Terminate
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default JobSafetyControls;