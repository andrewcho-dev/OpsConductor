/**
 * Job Schedule Modal - Compact & Efficient Design
 * Redesigned to be space-efficient and well-organized
 */
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  IconButton,
  Alert,
  CircularProgress,
  Chip,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  Close as CloseIcon,
  Schedule as ScheduleIcon,
  Work as WorkIcon,
  AccessTime as AccessTimeIcon
} from '@mui/icons-material';
import { 
  formatLocalDateTimeForBackend, 
  getCurrentLocalDateTimeForInput, 
  isDateTimeInFuture,
  getSystemTimezone 
} from '../../utils/timeUtils';

const JobScheduleModal = ({ job, onClose, onSubmit }) => {
  const [scheduledAt, setScheduledAt] = useState('');
  const [scheduleType, setScheduleType] = useState('once'); // 'once', 'recurring'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [systemTimezone, setSystemTimezone] = useState('UTC');

  useEffect(() => {
    // Fetch system timezone on component mount
    const fetchSystemTimezone = async () => {
      const timezone = await getSystemTimezone();
      setSystemTimezone(timezone);
    };
    
    fetchSystemTimezone();
  }, []);

  const handleSubmit = async () => {
    if (!scheduledAt) {
      setError('Please select a schedule time');
      return;
    }

    if (!isDateTimeInFuture(scheduledAt)) {
      setError('Schedule time must be in the future');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      // Convert local datetime to proper format for backend
      const backendDateTime = formatLocalDateTimeForBackend(scheduledAt);
      await onSubmit(backendDateTime);
      onClose();
    } catch (error) {
      setError('Failed to schedule job. Please try again.');
      console.error('Error scheduling job:', error);
    } finally {
      setLoading(false);
    }
  };

  const getMinDateTime = () => {
    return getCurrentLocalDateTimeForInput(1);
  };

  const getQuickScheduleOptions = () => {
    const now = new Date();
    
    const formatForInput = (date) => {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      return `${year}-${month}-${day}T${hours}:${minutes}`;
    };
    
    return [
      {
        label: 'In 5 minutes',
        value: formatForInput(new Date(now.getTime() + 5 * 60000))
      },
      {
        label: 'In 15 minutes',
        value: formatForInput(new Date(now.getTime() + 15 * 60000))
      },
      {
        label: 'In 1 hour',
        value: formatForInput(new Date(now.getTime() + 60 * 60000))
      },
      {
        label: 'Tomorrow 9 AM',
        value: (() => {
          const tomorrow = new Date(now);
          tomorrow.setDate(tomorrow.getDate() + 1);
          tomorrow.setHours(9, 0, 0, 0);
          return formatForInput(tomorrow);
        })()
      }
    ];
  };

  const quickOptions = getQuickScheduleOptions();

  return (
    <Dialog 
      open={true} 
      onClose={onClose} 
      maxWidth="sm" 
      fullWidth
      PaperProps={{
        sx: { 
          '& .MuiDialogContent-root': {
            padding: '16px 24px',
          }
        }
      }}
    >
      <DialogTitle sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        pb: 1,
        fontSize: '1.1rem',
        fontWeight: 600
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ScheduleIcon fontSize="small" />
          Schedule Job
        </Box>
        <IconButton onClick={onClose} size="small">
          <CloseIcon fontSize="small" />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          
          {/* Job Information */}
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, fontSize: '0.8rem', color: 'text.secondary' }}>
              JOB DETAILS
            </Typography>
            <Box sx={{ 
              p: 2, 
              bgcolor: 'background.default', 
              borderRadius: 1,
              border: '1px solid',
              borderColor: 'divider'
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <WorkIcon fontSize="small" color="primary" />
                <Typography variant="body2" sx={{ fontWeight: 500, fontSize: '0.85rem' }}>
                  {job.name}
                </Typography>
              </Box>
              <Typography variant="caption" sx={{ fontSize: '0.75rem', color: 'text.secondary' }}>
                Job Type: {job.job_type} • Status: {job.status}
              </Typography>
            </Box>
          </Box>

          {/* Quick Schedule Options */}
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, fontSize: '0.8rem', color: 'text.secondary' }}>
              QUICK SCHEDULE
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {quickOptions.map((option, index) => (
                <Chip
                  key={index}
                  label={option.label}
                  onClick={() => setScheduledAt(option.value)}
                  variant={scheduledAt === option.value ? 'filled' : 'outlined'}
                  color={scheduledAt === option.value ? 'primary' : 'default'}
                  size="small"
                  sx={{ fontSize: '0.75rem' }}
                />
              ))}
            </Box>
          </Box>

          {/* Custom Schedule Time */}
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, fontSize: '0.8rem', color: 'text.secondary' }}>
              CUSTOM SCHEDULE TIME
            </Typography>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  size="small"
                  type="datetime-local"
                  label={`Schedule Time (${systemTimezone})`}
                  value={scheduledAt}
                  onChange={(e) => {
                    setScheduledAt(e.target.value);
                    setError('');
                  }}
                  InputLabelProps={{ shrink: true }}
                  inputProps={{
                    min: getMinDateTime()
                  }}
                  helperText={`Select when the job should be executed in ${systemTimezone}`}
                />
              </Grid>
            </Grid>
          </Box>

          {/* Schedule Preview */}
          {scheduledAt && (
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, fontSize: '0.8rem', color: 'text.secondary' }}>
                SCHEDULE PREVIEW
              </Typography>
              <Box sx={{ 
                p: 2, 
                bgcolor: 'success.light', 
                color: 'success.contrastText',
                borderRadius: 1,
                display: 'flex',
                alignItems: 'flex-start',
                gap: 1
              }}>
                <AccessTimeIcon fontSize="small" sx={{ mt: 0.2 }} />
                <Box sx={{ flex: 1 }}>
                  {/* Local Time Display */}
                  <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.85rem', mb: 0.5 }}>
                    📍 LOCAL TIME: {(() => {
                      const date = new Date(scheduledAt);
                      const year = date.getFullYear();
                      const month = String(date.getMonth() + 1).padStart(2, '0');
                      const day = String(date.getDate()).padStart(2, '0');
                      const hours = String(date.getHours()).padStart(2, '0');
                      const minutes = String(date.getMinutes()).padStart(2, '0');
                      const seconds = String(date.getSeconds()).padStart(2, '0');
                      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
                    })()}
                  </Typography>
                  
                  {/* UTC Time Display */}
                  <Typography variant="body2" sx={{ fontWeight: 500, fontSize: '0.8rem', mb: 1, opacity: 0.9 }}>
                    🌍 UTC TIME: {(() => {
                      const utcTime = new Date(scheduledAt).toISOString().replace('T', ' ').replace('.000Z', '');
                      return `${utcTime}`;
                    })()}
                  </Typography>
                  
                  {/* Time Until Execution */}
                  <Typography variant="caption" sx={{ fontSize: '0.7rem', opacity: 0.8, fontStyle: 'italic' }}>
                    {(() => {
                      const diff = new Date(scheduledAt) - new Date();
                      const minutes = Math.floor(diff / 60000);
                      const hours = Math.floor(minutes / 60);
                      const days = Math.floor(hours / 24);
                      
                      if (days > 0) return `⏰ Executes in ${days} day${days > 1 ? 's' : ''} and ${hours % 24} hour${hours % 24 !== 1 ? 's' : ''}`;
                      if (hours > 0) return `⏰ Executes in ${hours} hour${hours > 1 ? 's' : ''} and ${minutes % 60} minute${minutes % 60 !== 1 ? 's' : ''}`;
                      return `⏰ Executes in ${minutes} minute${minutes !== 1 ? 's' : ''}`;
                    })()}
                  </Typography>
                </Box>
              </Box>
            </Box>
          )}

          {/* Error Display */}
          {error && (
            <Alert severity="error" sx={{ fontSize: '0.8rem' }}>
              {error}
            </Alert>
          )}
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose} size="small">
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading || !scheduledAt}
          startIcon={loading ? <CircularProgress size={16} /> : <ScheduleIcon fontSize="small" />}
          size="small"
        >
          {loading ? 'Scheduling...' : 'Schedule Job'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default JobScheduleModal;