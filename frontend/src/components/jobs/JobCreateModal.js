/**
 * Job Create Modal - Compact & Efficient Design
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Chip,
  IconButton,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Close as CloseIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  Work as WorkIcon,
  Computer as ComputerIcon,
  Code as CodeIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';

import { useSessionAuth } from '../../contexts/SessionAuthContext';
import TargetSelectionModal from './TargetSelectionModal';
import ScheduleConfigModal from './ScheduleConfigModal';
import ActionsWorkspaceModal from './ActionsWorkspaceModal';

const JobCreateModal = ({ open, onClose, onCreateJob }) => {
  const { token } = useSessionAuth();
  const [loading, setLoading] = useState(false);
  const [targets, setTargets] = useState([]);
  const [showTargetModal, setShowTargetModal] = useState(false);
  const [showActionsModal, setShowActionsModal] = useState(false);
  const [showSchedulingModal, setShowSchedulingModal] = useState(false);
  const [scheduleConfig, setScheduleConfig] = useState(null);
  const [systemTimezone, setSystemTimezone] = useState('UTC');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    actions: [],
    target_ids: [],
    scheduled_at: null
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (open) {
      fetchTargets();
      fetchSystemTimezone();
    }
  }, [open]);

  const fetchTargets = async () => {
    try {
      const apiBaseUrl = process.env.REACT_APP_API_URL || '/api/v3';
      const response = await fetch(`${apiBaseUrl}/targets/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      if (response.ok) {
        const data = await response.json();
        setTargets(data.targets || data || []);
      }
    } catch (error) {
      console.error('Failed to fetch targets:', error);
    }
  };

  const fetchSystemTimezone = async () => {
    try {
      const apiBaseUrl = process.env.REACT_APP_API_URL || '/api/v3';
      const response = await fetch(`${apiBaseUrl}/system/info`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      if (response.ok) {
        const data = await response.json();
        setSystemTimezone(data.timezone?.display_name || 'UTC');
      }
    } catch (error) {
      console.error('Failed to fetch system timezone:', error);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };



  const handleTargetSelectionChange = (selectedTargetIds) => {
    setFormData(prev => ({ ...prev, target_ids: selectedTargetIds }));
    if (errors.targets) {
      setErrors(prev => ({ ...prev, targets: null }));
    }
  };

  const handleScheduleConfiguration = (scheduleData) => {
    setScheduleConfig(scheduleData);
    // If it's a simple one-time schedule, also set the scheduled_at field for backward compatibility
    if (scheduleData && scheduleData.scheduleType === 'once' && scheduleData.executeAt) {
      setFormData(prev => ({ ...prev, scheduled_at: scheduleData.executeAt }));
    } else {
      setFormData(prev => ({ ...prev, scheduled_at: null }));
    }
    setShowSchedulingModal(false);
  };

  const handleActionsConfiguration = (actionsData) => {
    setFormData(prev => ({ ...prev, actions: actionsData }));
    setShowActionsModal(false);
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.name.trim()) newErrors.name = 'Job name is required';
    if (formData.actions.length === 0) {
      newErrors.actions = 'At least one action must be defined';
    }
    if (formData.target_ids.length === 0) {
      newErrors.targets = 'At least one target must be selected';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    console.log('🎯 Form submission started');
    console.log('📝 Form data:', formData);
    
    if (!validateForm()) {
      console.log('❌ Form validation failed:', errors);
      return;
    }
    
    console.log('✅ Form validation passed');
    setLoading(true);
    try {
      // Prepare form data with proper datetime handling
      const submitData = { ...formData };
      
      // Convert local datetime to UTC for backend
      if (submitData.scheduled_at) {
        // The datetime-local input gives us a string like "2025-08-11T14:30"
        // Parse it manually to ensure it's treated as local time
        const [datePart, timePart] = submitData.scheduled_at.split('T');
        const [year, month, day] = datePart.split('-');
        const [hour, minute] = timePart.split(':');
        
        // Create Date object with explicit local time components
        const localDateTime = new Date(year, month - 1, day, hour, minute);
        
        // Convert to ISO string (UTC) for backend
        submitData.scheduled_at = localDateTime.toISOString();
        console.log('🕐 Datetime conversion:', {
          original: formData.scheduled_at,
          parsedAsLocal: localDateTime.toString(),
          utcForBackend: submitData.scheduled_at
        });
      }
      
      // Pass both job data and schedule configuration
      const success = await onCreateJob(submitData, scheduleConfig);
      console.log('📤 Job creation result:', success);
      console.log('📅 Schedule config:', scheduleConfig);
      if (success) {
        onClose();
        // Reset form
        setFormData({
          name: '',
          description: '',
          actions: [],
          target_ids: [],
          scheduled_at: null
        });
        setErrors({});
        setScheduleConfig(null);
      }
    } finally {
      setLoading(false);
    }
  };

  const selectedTargets = targets.filter(t => formData.target_ids.includes(t.id));

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="sm" 
      fullWidth
      PaperProps={{
        sx: { 
          maxHeight: '80vh',
          width: '500px',
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
          <WorkIcon fontSize="small" />
          Create New Job
        </Box>
        <IconButton onClick={onClose} size="small">
          <CloseIcon fontSize="small" />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          
          {/* Basic Information - Compact Grid */}
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, fontSize: '0.8rem', color: 'text.secondary' }}>
              BASIC INFORMATION
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  size="small"
                  label="Job Name"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  error={!!errors.name}
                  helperText={errors.name}
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  size="small"
                  label="Description (Optional)"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  multiline
                  rows={2}
                />
              </Grid>
            </Grid>
          </Box>

          <Divider />

          {/* Targets - Modal Selection (moved up) */}
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, fontSize: '0.8rem', color: 'text.secondary' }}>
              TARGETS ({selectedTargets.length} selected)
            </Typography>
            
            <Button
              fullWidth
              variant="outlined"
              onClick={() => setShowTargetModal(true)}
              startIcon={<ComputerIcon />}
              sx={{ 
                justifyContent: 'flex-start',
                textAlign: 'left',
                py: 1.5,
                borderStyle: 'dashed',
                borderColor: 'grey.400',
                color: 'text.secondary',
                '&:hover': {
                  borderColor: 'primary.main',
                  color: 'primary.main',
                  bgcolor: 'primary.50'
                }
              }}
            >
              {selectedTargets.length === 0 
                ? 'Select Targets' 
                : `${selectedTargets.length} target${selectedTargets.length > 1 ? 's' : ''} selected`
              }
            </Button>
            
            {selectedTargets.length > 0 && (
              <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {selectedTargets.slice(0, 5).map(target => (
                  <Chip
                    key={target.id}
                    label={
                      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 0.25 }}>
                        <Typography variant="caption" sx={{ fontSize: '0.7rem', fontWeight: 500 }}>
                          {target.name}
                        </Typography>
                        <Typography variant="caption" sx={{ fontSize: '0.65rem', fontFamily: 'monospace', fontWeight: 500 }}>
                          {target.ip_address || 'No IP'}
                        </Typography>
                      </Box>
                    }
                    size="small"
                    sx={{ fontSize: '0.7rem', height: 'auto', py: 0.5 }}
                  />
                ))}
                {selectedTargets.length > 5 && (
                  <Chip
                    label={`+${selectedTargets.length - 5} more`}
                    size="small"
                    variant="outlined"
                    sx={{ fontSize: '0.7rem', height: '32px' }}
                  />
                )}
              </Box>
            )}
            
            {errors.targets && (
              <Alert severity="error" sx={{ mt: 1, fontSize: '0.75rem' }}>
                {errors.targets}
              </Alert>
            )}
          </Box>

          <Divider />

          {/* Actions Workspace */}
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, fontSize: '0.8rem', color: 'text.secondary' }}>
              ACTIONS ({formData.actions.length} configured)
            </Typography>
            
            <Button
              fullWidth
              variant="outlined"
              onClick={() => setShowActionsModal(true)}
              startIcon={<CodeIcon />}
              sx={{ 
                justifyContent: 'flex-start',
                textAlign: 'left',
                py: 1.5,
                px: 2,
                borderStyle: 'dashed',
                borderColor: 'grey.400',
                color: 'text.secondary',
                '&:hover': {
                  borderColor: 'primary.main',
                  color: 'primary.main',
                  bgcolor: 'primary.50'
                }
              }}
            >
              {formData.actions.length === 0 
                ? 'Configure Actions' 
                : `${formData.actions.length} action${formData.actions.length > 1 ? 's' : ''} configured`
              }
            </Button>

            {/* Actions Preview */}
            {formData.actions.length > 0 && (
              <Box sx={{ mt: 1, p: 1.5, bgcolor: 'info.50', borderRadius: 1, border: '1px solid', borderColor: 'info.200' }}>
                <Typography variant="caption" sx={{ fontWeight: 600, color: 'info.dark' }}>
                  ACTIONS CONFIGURED:
                </Typography>
                {formData.actions.slice(0, 3).map((action, index) => (
                  <Typography key={index} variant="body2" sx={{ fontSize: '0.75rem', mt: 0.5, color: 'info.dark' }}>
                    {index + 1}. <strong>{action.action_name || action.name}</strong> ({action.action_type || action.type})
                  </Typography>
                ))}
                {formData.actions.length > 3 && (
                  <Typography variant="body2" sx={{ fontSize: '0.75rem', mt: 0.5, color: 'info.main' }}>
                    ... and {formData.actions.length - 3} more actions
                  </Typography>
                )}
                <Typography variant="body2" sx={{ fontSize: '0.75rem', color: 'info.main', mt: 0.5 }}>
                  ✅ Workflow ready for execution
                </Typography>
              </Box>
            )}
            
            {errors.actions && (
              <Alert severity="error" sx={{ mt: 1, fontSize: '0.75rem' }}>
                {errors.actions}
              </Alert>
            )}
          </Box>

          <Divider />

          {/* Schedule Configuration */}
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, fontSize: '0.8rem', color: 'text.secondary' }}>
              SCHEDULE (OPTIONAL)
            </Typography>
            
            <Button
              fullWidth
              variant="outlined"
              onClick={() => setShowSchedulingModal(true)}
              startIcon={<ScheduleIcon />}
              sx={{ 
                justifyContent: 'flex-start',
                textAlign: 'left',
                py: 1.5,
                px: 2,
                borderStyle: 'dashed',
                borderColor: 'grey.400',
                color: 'text.secondary',
                '&:hover': {
                  borderColor: 'primary.main',
                  color: 'primary.main',
                  bgcolor: 'primary.50'
                }
              }}
            >
              {scheduleConfig ? 
                `Schedule Configured: ${scheduleConfig.scheduleType === 'once' ? 'One-time' : 
                  scheduleConfig.scheduleType === 'recurring' ? 
                    `Every ${scheduleConfig.interval} ${
                      scheduleConfig.recurringType === 'minutes' ? 'minute(s)' :
                      scheduleConfig.recurringType === 'hours' ? 'hour(s)' :
                      scheduleConfig.recurringType === 'daily' ? 'day(s)' : 
                      scheduleConfig.recurringType === 'weekly' ? 'week(s)' : 'month(s)'
                    }` : 
                  'Cron Expression'}` 
                : 'Configure Schedule'}
            </Button>

            {/* Schedule Preview */}
            {scheduleConfig && (
              <Box sx={{ mt: 1, p: 1.5, bgcolor: 'success.50', borderRadius: 1, border: '1px solid', borderColor: 'success.200' }}>
                <Typography variant="caption" sx={{ fontWeight: 600, color: 'success.dark' }}>
                  SCHEDULE CONFIGURED:
                </Typography>
                <Typography variant="body2" sx={{ fontSize: '0.75rem', mt: 0.5, color: 'success.dark' }}>
                  📅 <strong>Type:</strong> {scheduleConfig.scheduleType === 'once' ? 'One-time execution' : 
                    scheduleConfig.scheduleType === 'recurring' ? `Recurring (${scheduleConfig.recurringType})` : 
                    'Cron expression'}
                </Typography>
                {scheduleConfig.scheduleType === 'once' && scheduleConfig.executeAt && (
                  <Typography variant="body2" sx={{ fontSize: '0.75rem', mt: 0.5, color: 'success.dark' }}>
                    🕐 <strong>Execute at:</strong> {new Date(scheduleConfig.executeAt).toLocaleString()}
                  </Typography>
                )}
                {scheduleConfig.scheduleType === 'recurring' && (
                  <>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', mt: 0.5, color: 'success.dark' }}>
                      🔄 <strong>Pattern:</strong> Every {scheduleConfig.interval} {
                        scheduleConfig.recurringType === 'minutes' ? 'minute(s)' :
                        scheduleConfig.recurringType === 'hours' ? 'hour(s)' :
                        scheduleConfig.recurringType === 'daily' ? 'day(s)' : 
                        scheduleConfig.recurringType === 'weekly' ? 'week(s)' : 'month(s)'
                      } 
                      {!['minutes', 'hours'].includes(scheduleConfig.recurringType) && ` at ${scheduleConfig.time}`}
                      {scheduleConfig.recurringType === 'weekly' && scheduleConfig.daysOfWeek?.length > 0 && 
                        ` on ${scheduleConfig.daysOfWeek.map(d => ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][d-1]).join(', ')}`}
                      {scheduleConfig.recurringType === 'monthly' && ` on day ${scheduleConfig.dayOfMonth}`}
                    </Typography>
                    {scheduleConfig.startDate && (
                      <Typography variant="body2" sx={{ fontSize: '0.75rem', mt: 0.5, color: 'success.dark' }}>
                        🚀 <strong>First run:</strong> {new Date(scheduleConfig.startDate + 'T' + scheduleConfig.startTime).toLocaleString()}
                      </Typography>
                    )}
                  </>
                )}
                {scheduleConfig.scheduleType === 'cron' && (
                  <Typography variant="body2" sx={{ fontSize: '0.75rem', mt: 0.5, color: 'success.dark' }}>
                    ⚙️ <strong>Cron:</strong> {scheduleConfig.cronExpression}
                  </Typography>
                )}
                <Typography variant="body2" sx={{ fontSize: '0.75rem', color: 'success.main', mt: 0.5 }}>
                  ✅ Schedule ready to apply after job creation
                </Typography>
              </Box>
            )}
          </Box>
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose} size="small">
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading}
          startIcon={loading ? <CircularProgress size={16} /> : <WorkIcon fontSize="small" />}
          size="small"
        >
          {loading ? 'Creating...' : 'Create Job'}
        </Button>
      </DialogActions>

      {/* Target Selection Modal */}
      <TargetSelectionModal
        open={showTargetModal}
        onClose={() => setShowTargetModal(false)}
        selectedTargetIds={formData.target_ids}
        onSelectionChange={handleTargetSelectionChange}
      />

      {/* Actions Workspace Modal */}
      <ActionsWorkspaceModal
        open={showActionsModal}
        onClose={() => setShowActionsModal(false)}
        onActionsConfigured={handleActionsConfiguration}
        initialActions={formData.actions}
        selectedTargets={selectedTargets}
      />

      {/* Schedule Configuration Modal */}
      <ScheduleConfigModal
        open={showSchedulingModal}
        onClose={() => setShowSchedulingModal(false)}
        onConfigurationComplete={handleScheduleConfiguration}
        initialConfig={scheduleConfig}
      />
    </Dialog>
  );
};

export default JobCreateModal;