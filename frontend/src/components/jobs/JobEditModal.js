/**
 * Job Edit Modal - Compact & Efficient Design
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
  Edit as EditIcon,
  Computer as ComputerIcon,
  Code as CodeIcon
} from '@mui/icons-material';

import { useAuth } from '../../contexts/AuthContext';
import TargetSelectionModal from './TargetSelectionModal';

const JobEditModal = ({ open, job, onClose, onSubmit }) => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [targets, setTargets] = useState([]);
  const [showTargetModal, setShowTargetModal] = useState(false);
  const [systemTimezone, setSystemTimezone] = useState('UTC');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    job_type: 'command',
    actions: [],
    target_ids: [],
    scheduled_at: null,
    schedule_type: 'once',
    recurring_type: 'daily',
    interval: 1,
    time: '09:00',
    days_of_week: [],
    day_of_month: 1,
    max_executions: null,
    cron_expression: '',
    priority: 5,
    timeout: null,
    retry_count: 0
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (open && job) {
      // Clear errors
      setErrors({});
      
      // Populate form immediately with job data (fallback while API loads)
      let jobActions;
      if (job.actions && Array.isArray(job.actions) && job.actions.length > 0) {
        // Use existing actions - handle multiple possible structures
        jobActions = job.actions.map((action, index) => {
          // Try to extract command from various possible locations
          let command = '';
          
          if (action.action_parameters?.command) {
            command = action.action_parameters.command;
          } else if (action.action_parameters?.script_content) {
            command = action.action_parameters.script_content;
          } else if (action.action_parameters?.content) {
            // For file operations, show the content
            command = action.action_parameters.content;
          } else if (action.action_parameters?.operation) {
            // For complex operations, create a descriptive command
            const params = action.action_parameters;
            if (params.operation === 'create' && params.destination_path) {
              command = `# File Operation: ${params.operation}\n# Destination: ${params.destination_path}\n${params.content || ''}`;
            } else {
              command = JSON.stringify(params, null, 2);
            }
          } else if (action.command) {
            command = action.command;
          } else if (action.parameters?.command) {
            command = action.parameters.command;
          } else if (action.parameters?.script_content) {
            command = action.parameters.script_content;
          } else if (action.action_data?.command) {
            command = action.action_data.command;
          } else if (action.config?.command) {
            command = action.config.command;
          } else if (action.details?.command) {
            command = action.details.command;
          } else if (action.script) {
            command = action.script;
          } else if (action.cmd) {
            command = action.cmd;
          } else if (action.exec) {
            command = action.exec;
          } else if (typeof action === 'string') {
            command = action;
          }
          
          return {
            action_order: action.action_order || index + 1,
            action_type: action.action_type || 'command',
            action_name: action.action_name || action.name || `Action ${index + 1}`,
            action_parameters: { 
              command: command
            }
          };
        });
      } else {
        // Create default action
        jobActions = [{
          action_order: 1,
          action_type: 'command',
          action_name: 'Execute Command',
          action_parameters: { command: '' }
        }];
      }
      
      // Convert UTC scheduled_at to local datetime string for datetime-local input
      let initialScheduledAt = null;
      if (job.scheduled_at) {
        // job.scheduled_at is UTC string like "2025-08-17T15:30:00Z"
        // new Date() automatically converts UTC to local time
        const utcDate = new Date(job.scheduled_at);
        
        // Extract local time components (getHours() returns local time after UTC conversion)
        const year = utcDate.getFullYear();
        const month = String(utcDate.getMonth() + 1).padStart(2, '0');
        const day = String(utcDate.getDate()).padStart(2, '0');
        const hours = String(utcDate.getHours()).padStart(2, '0');
        const minutes = String(utcDate.getMinutes()).padStart(2, '0');
        initialScheduledAt = `${year}-${month}-${day}T${hours}:${minutes}`;
        

      }
      
      // Extract target IDs from targets array
      const targetIds = job.targets ? job.targets.map(target => target.id) : [];
      
      const initialFormData = {
        name: job.name || '',
        description: job.description || '',
        job_type: job.job_type || 'command',
        actions: jobActions,
        target_ids: targetIds,
        scheduled_at: initialScheduledAt,
        schedule_type: job.schedule_type || (initialScheduledAt ? 'once' : 'once'),
        recurring_type: job.recurring_type || 'daily',
        interval: job.interval || 1,
        time: job.time || '09:00',
        days_of_week: job.days_of_week || [],
        day_of_month: job.day_of_month || 1,
        max_executions: job.max_executions || null,
        cron_expression: job.cron_expression || '',
        priority: job.priority || 5,
        timeout: job.timeout || null,
        retry_count: job.retry_count || 0
      };
      

      setFormData(initialFormData);
      
      // Fetch additional data in parallel
      const fetchPromises = [
        fetchTargets(),
        fetchSystemTimezone()
      ];
      
      // Always fetch full job details since JobList only provides basic info
      if (job.id) {
        fetchPromises.push(fetchJobDetails());
      }
      
      // Wait for all data to be fetched
      Promise.all(fetchPromises).catch(error => {
        console.error('Error fetching job edit data:', error);
      });
    }
  }, [open, job, token]);

  const fetchJobDetails = async () => {
    try {
      const jobResponse = await fetch(`/api/v2/jobs/${job.id}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (jobResponse.ok) {
        const jobWithExecutions = await jobResponse.json();
        // Extract job data from the response
        const jobData = jobWithExecutions.job || jobWithExecutions;
        
        // Extract target IDs from targets array
        const apiTargetIds = jobData.targets ? jobData.targets.map(target => target.id) : [];
        
        // Process actions from API response
        let apiActions = [];
        if (jobData.actions && Array.isArray(jobData.actions) && jobData.actions.length > 0) {
          apiActions = jobData.actions.map((action, index) => {
            // Extract command from action_parameters or action_config
            let command = '';
            if (action.action_parameters?.command) {
              command = action.action_parameters.command;
            } else if (action.action_parameters?.script_content) {
              command = action.action_parameters.script_content;
            } else if (action.action_parameters?.content) {
              // For file operations, show the content
              command = action.action_parameters.content;
            } else if (action.action_parameters?.operation) {
              // For complex operations, create a descriptive command
              const params = action.action_parameters;
              if (params.operation === 'create' && params.destination_path) {
                command = `# File Operation: ${params.operation}\n# Destination: ${params.destination_path}\n${params.content || ''}`;
              } else {
                command = JSON.stringify(params, null, 2);
              }
            } else if (action.action_config?.command) {
              command = action.action_config.command;
            } else if (action.action_parameters) {
              // Look for command in any parameter field
              const params = action.action_parameters;
              command = params.command || params.script_content || params.script || params.cmd || params.exec || '';
            }
            
            return {
              action_order: action.action_order || index + 1,
              action_type: action.action_type || 'command',
              action_name: action.action_name || `Action ${index + 1}`,
              action_parameters: { 
                command: command
              }
            };
          });
        }
        
        // Convert UTC scheduled_at to local datetime string for datetime-local input
        let localScheduledAt = null;
        if (jobData.scheduled_at) {
          // jobData.scheduled_at is UTC string like "2025-08-17T15:30:00Z"
          // new Date() automatically converts UTC to local time
          const utcDate = new Date(jobData.scheduled_at);
          
          // Extract local time components (getHours() returns local time after UTC conversion)
          const year = utcDate.getFullYear();
          const month = String(utcDate.getMonth() + 1).padStart(2, '0');
          const day = String(utcDate.getDate()).padStart(2, '0');
          const hours = String(utcDate.getHours()).padStart(2, '0');
          const minutes = String(utcDate.getMinutes()).padStart(2, '0');
          localScheduledAt = `${year}-${month}-${day}T${hours}:${minutes}`;
        }
        
        // Update form data with API data
        const updatedFormData = {
          name: jobData.name || '',
          description: jobData.description || '',
          job_type: jobData.job_type || 'command',
          actions: apiActions.length > 0 ? apiActions : [{
            action_order: 1,
            action_type: 'command',
            action_name: 'Execute Command',
            action_parameters: { command: '' }
          }],
          target_ids: apiTargetIds,
          scheduled_at: localScheduledAt,
          schedule_type: jobData.schedule_type || (localScheduledAt ? 'once' : 'once'),
          recurring_type: jobData.recurring_type || 'daily',
          interval: jobData.interval || 1,
          time: jobData.time || '09:00',
          days_of_week: jobData.days_of_week || [],
          day_of_month: jobData.day_of_month || 1,
          max_executions: jobData.max_executions || null,
          cron_expression: jobData.cron_expression || '',
          priority: jobData.priority || 5,
          timeout: jobData.timeout || null,
          retry_count: jobData.retry_count || 0
        };
        
        setFormData(updatedFormData);
      } else {
        console.error('Failed to fetch fresh job details - Response not OK');
        console.log('Response status:', jobResponse.status);
      }
    } catch (error) {
      console.error('Failed to fetch fresh job details:', error);
      console.log('Keeping existing form data from job prop');
    }
  };

  const fetchTargets = async () => {
    try {
      const response = await fetch('/api/targets/', {
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
      // Try the v2 system health endpoint first
      const response = await fetch('/api/v2/system/health', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      if (response.ok) {
        const data = await response.json();
        const timezone = data.timezone || data.system?.timezone || 'UTC';
        // Convert long timezone names to shorter, more user-friendly format
        const shortTimezone = timezone.replace('America/', '').replace('Europe/', '').replace('_', ' ');
        setSystemTimezone(shortTimezone);
      } else {
        // Fallback to browser timezone
        const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        const shortTimezone = browserTimezone.replace('America/', '').replace('Europe/', '').replace('_', ' ');
        setSystemTimezone(shortTimezone);
      }
    } catch (error) {
      // Fallback to browser timezone
      const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const shortTimezone = browserTimezone.replace('America/', '').replace('Europe/', '').replace('_', ' ');
      setSystemTimezone(shortTimezone);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  const handleActionChange = (index, field, value) => {
    const updatedActions = [...formData.actions];
    if (field === 'command') {
      updatedActions[index].action_parameters.command = value;
    } else {
      updatedActions[index][field] = value;
    }
    setFormData(prev => ({ ...prev, actions: updatedActions }));
  };

  const addAction = () => {
    const newAction = {
      action_order: formData.actions.length + 1,
      action_type: 'command',
      action_name: `Action ${formData.actions.length + 1}`,
      action_parameters: { command: '' }
    };
    setFormData(prev => ({
      ...prev,
      actions: [...prev.actions, newAction]
    }));
  };

  const removeAction = (index) => {
    if (formData.actions.length > 1) {
      const updatedActions = formData.actions.filter((_, i) => i !== index);
      updatedActions.forEach((action, i) => {
        action.action_order = i + 1;
      });
      setFormData(prev => ({ ...prev, actions: updatedActions }));
    }
  };

  const handleTargetSelectionChange = (selectedTargetIds) => {
    setFormData(prev => ({ ...prev, target_ids: selectedTargetIds }));
    if (errors.targets) {
      setErrors(prev => ({ ...prev, targets: null }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.name.trim()) newErrors.name = 'Job name is required';
    if (formData.actions.some(action => !action.action_parameters?.command?.trim())) {
      newErrors.actions = 'All actions must have a command';
    }
    if (formData.target_ids.length === 0) {
      newErrors.targets = 'At least one target must be selected';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;
    
    setLoading(true);
    try {
      // Prepare form data with proper datetime handling
      const submitData = { ...formData, id: job.id };
      
      console.log('🔄 JobEditModal: Starting job update...', {
        jobId: job.id,
        originalScheduledAt: formData.scheduled_at,
        formData: submitData
      });
      
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
        
        console.log('🕐 JobEditModal: Datetime conversion', {
          original: formData.scheduled_at,
          localDateTime: localDateTime.toString(),
          utcIsoString: submitData.scheduled_at
        });
      }
      
      console.log('📤 JobEditModal: Calling onSubmit with data:', submitData);
      const success = await onSubmit(submitData);
      console.log('📥 JobEditModal: onSubmit returned:', success);
      
      if (success) {
        console.log('✅ JobEditModal: Update successful, closing modal');
        onClose();
        setErrors({});
      } else {
        console.log('❌ JobEditModal: Update failed, keeping modal open');
        setErrors({ submit: 'Failed to update job. Please try again.' });
      }
    } catch (error) {
      console.error('❌ JobEditModal: Exception during submit:', error);
      setErrors({ submit: `Update failed: ${error.message}` });
    } finally {
      setLoading(false);
    }
  };

  const selectedTargets = targets.filter(t => formData.target_ids.includes(t.id));



  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="md" 
      fullWidth
      PaperProps={{
        sx: { 
          maxHeight: '90vh',
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
          <EditIcon fontSize="small" />
          Edit Job: {job?.name}

        </Box>
        <IconButton onClick={onClose} size="small">
          <CloseIcon fontSize="small" />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>
        {/* Submit Error Display */}
        {errors.submit && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {errors.submit}
          </Alert>
        )}
        
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          
          {/* Basic Information - Compact Grid */}
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, fontSize: '0.8rem', color: 'text.secondary' }}>
              BASIC INFORMATION
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={8}>
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
              <Grid item xs={12} sm={4}>
                <FormControl fullWidth size="small">
                  <InputLabel>Job Type</InputLabel>
                  <Select
                    value={formData.job_type}
                    label="Job Type"
                    onChange={(e) => handleInputChange('job_type', e.target.value)}
                  >
                    <MenuItem value="command">Command</MenuItem>
                    <MenuItem value="script">Script</MenuItem>
                    <MenuItem value="file_transfer">File Transfer</MenuItem>
                    <MenuItem value="composite">Composite</MenuItem>
                  </Select>
                </FormControl>
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

          {/* Actions - Compact Accordion */}
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.8rem', color: 'text.secondary' }}>
                ACTIONS ({formData.actions.length})
              </Typography>
              <Button
                size="small"
                startIcon={<AddIcon fontSize="small" />}
                onClick={addAction}
                sx={{ fontSize: '0.75rem' }}
              >
                Add Action
              </Button>
            </Box>
            
            {formData.actions.map((action, index) => (
                <Accordion key={index} sx={{ mb: 1, '&:before': { display: 'none' } }}>
                  <AccordionSummary 
                    expandIcon={<ExpandMoreIcon fontSize="small" />}
                    sx={{ 
                      minHeight: '40px',
                      '& .MuiAccordionSummary-content': { 
                        margin: '8px 0',
                        alignItems: 'center'
                      }
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
                      <CodeIcon fontSize="small" color="primary" />
                      <Typography variant="body2" sx={{ fontWeight: 500, fontSize: '0.8rem' }}>
                        {action.action_name || `Action ${index + 1}`}
                      </Typography>
                    {formData.actions.length > 1 && (
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          removeAction(index);
                        }}
                        sx={{ ml: 'auto', mr: 1 }}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    )}
                  </Box>
                </AccordionSummary>
                <AccordionDetails sx={{ pt: 0 }}>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Action Name"
                        value={action.action_name}
                        onChange={(e) => handleActionChange(index, 'action_name', e.target.value)}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Command"
                        value={action.action_parameters?.command || ''}
                        onChange={(e) => handleActionChange(index, 'command', e.target.value)}
                        multiline
                        rows={3}
                        required
                        placeholder="Enter command to execute..."
                      />
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            ))}
            
            {errors.actions && (
              <Alert severity="error" sx={{ mt: 1, fontSize: '0.75rem' }}>
                {errors.actions}
              </Alert>
            )}
          </Box>

          <Divider />

          {/* Targets - Modal Selection */}
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
                fontSize: '0.8rem'
              }}
            >
              {selectedTargets.length === 0 
                ? 'Select Targets...' 
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

          {/* Schedule - Enhanced with Recurring Options */}
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, fontSize: '0.8rem', color: 'text.secondary' }}>
              SCHEDULE (OPTIONAL)
            </Typography>
            
            {/* Schedule Type Selection */}
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Schedule Type</InputLabel>
                  <Select
                    value={formData.schedule_type || 'once'}
                    onChange={(e) => handleInputChange('schedule_type', e.target.value)}
                    label="Schedule Type"
                  >
                    <MenuItem value="once">Run Once</MenuItem>
                    <MenuItem value="recurring">Recurring</MenuItem>
                    <MenuItem value="cron">Advanced (Cron)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              {/* One-time Schedule */}
              {(!formData.schedule_type || formData.schedule_type === 'once') && (
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    size="small"
                    type="datetime-local"
                    label={`Schedule Time (${systemTimezone})`}
                    value={formData.scheduled_at || ''}
                    onChange={(e) => handleInputChange('scheduled_at', e.target.value || null)}
                    InputLabelProps={{ shrink: true }}
                    inputProps={{
                      min: (() => {
                        const now = new Date();
                        now.setMinutes(now.getMinutes() + 1);
                        const year = now.getFullYear();
                        const month = String(now.getMonth() + 1).padStart(2, '0');
                        const day = String(now.getDate()).padStart(2, '0');
                        const hours = String(now.getHours()).padStart(2, '0');
                        const minutes = String(now.getMinutes()).padStart(2, '0');
                        return `${year}-${month}-${day}T${hours}:${minutes}`;
                      })()
                    }}
                  />
                </Grid>
              )}
            </Grid>
            
            {/* Recurring Schedule Options */}
            {formData.schedule_type === 'recurring' && (
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={12} sm={4}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Repeat Every</InputLabel>
                    <Select
                      value={formData.recurring_type || 'daily'}
                      onChange={(e) => handleInputChange('recurring_type', e.target.value)}
                      label="Repeat Every"
                    >
                      <MenuItem value="hourly">Hour</MenuItem>
                      <MenuItem value="daily">Day</MenuItem>
                      <MenuItem value="weekly">Week</MenuItem>
                      <MenuItem value="monthly">Month</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    size="small"
                    type="number"
                    label="Interval"
                    value={formData.interval || 1}
                    onChange={(e) => handleInputChange('interval', parseInt(e.target.value) || 1)}
                    inputProps={{ min: 1, max: 365 }}
                    helperText="Every N units"
                  />
                </Grid>
                
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    size="small"
                    type="time"
                    label="Time"
                    value={formData.time || '09:00'}
                    onChange={(e) => handleInputChange('time', e.target.value)}
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
                
                {/* Days of Week for Weekly */}
                {formData.recurring_type === 'weekly' && (
                  <Grid item xs={12}>
                    <Typography variant="caption" sx={{ display: 'block', mb: 1 }}>
                      Days of Week:
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, index) => (
                        <Chip
                          key={day}
                          label={day}
                          variant={formData.days_of_week?.includes(index + 1) ? 'filled' : 'outlined'}
                          color={formData.days_of_week?.includes(index + 1) ? 'primary' : 'default'}
                          size="small"
                          onClick={() => {
                            const currentDays = formData.days_of_week || [];
                            const dayNum = index + 1;
                            const newDays = currentDays.includes(dayNum)
                              ? currentDays.filter(d => d !== dayNum)
                              : [...currentDays, dayNum].sort();
                            handleInputChange('days_of_week', newDays);
                          }}
                        />
                      ))}
                    </Box>
                  </Grid>
                )}
                
                {/* Day of Month for Monthly */}
                {formData.recurring_type === 'monthly' && (
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      size="small"
                      type="number"
                      label="Day of Month"
                      value={formData.day_of_month || 1}
                      onChange={(e) => handleInputChange('day_of_month', parseInt(e.target.value) || 1)}
                      inputProps={{ min: 1, max: 31 }}
                      helperText="1-31 (or last day of month)"
                    />
                  </Grid>
                )}
                
                {/* Max Executions */}
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    size="small"
                    type="number"
                    label="Max Executions (Optional)"
                    value={formData.max_executions || ''}
                    onChange={(e) => handleInputChange('max_executions', e.target.value ? parseInt(e.target.value) : null)}
                    inputProps={{ min: 1 }}
                    helperText="Leave empty for unlimited"
                  />
                </Grid>
              </Grid>
            )}
            
            {/* Cron Expression */}
            {formData.schedule_type === 'cron' && (
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    size="small"
                    label="Cron Expression"
                    value={formData.cron_expression || ''}
                    onChange={(e) => handleInputChange('cron_expression', e.target.value)}
                    placeholder="0 9 * * 1-5"
                    helperText="Format: minute hour day month day-of-week (e.g., '0 9 * * 1-5' = 9 AM weekdays)"
                  />
                </Grid>
                <Grid item xs={12}>
                  <Box sx={{ p: 1, bgcolor: 'background.default', borderRadius: 1, fontSize: '0.75rem' }}>
                    <Typography variant="caption" sx={{ fontWeight: 600 }}>Common Examples:</Typography><br />
                    <Typography variant="caption">• 0 9 * * * = Every day at 9:00 AM</Typography><br />
                    <Typography variant="caption">• 0 9 * * 1-5 = Weekdays at 9:00 AM</Typography><br />
                    <Typography variant="caption">• 0 */6 * * * = Every 6 hours</Typography><br />
                    <Typography variant="caption">• 0 9 1 * * = First day of every month at 9:00 AM</Typography>
                  </Box>
                </Grid>
              </Grid>
            )}
            
            {/* Schedule Preview */}
            {(formData.scheduled_at || formData.schedule_type === 'recurring' || formData.schedule_type === 'cron') && (
              <Alert severity="info" sx={{ fontSize: '0.75rem' }}>
                <Typography variant="caption" sx={{ fontWeight: 600 }}>Schedule Preview:</Typography><br />
                {formData.schedule_type === 'recurring' && formData.recurring_type && (
                  <Typography variant="caption">
                    Runs {formData.recurring_type} at {formData.time || '09:00'}
                    {formData.interval > 1 && ` (every ${formData.interval} ${formData.recurring_type.slice(0, -2)}s)`}
                    {formData.max_executions && ` for maximum ${formData.max_executions} executions`}
                  </Typography>
                )}
                {formData.schedule_type === 'cron' && formData.cron_expression && (
                  <Typography variant="caption">
                    Cron: {formData.cron_expression}
                  </Typography>
                )}
                {(!formData.schedule_type || formData.schedule_type === 'once') && formData.scheduled_at && (
                  <Typography variant="caption">
                    One-time execution: {new Date(formData.scheduled_at).toLocaleString()}
                  </Typography>
                )}
              </Alert>
            )}
            
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
              Leave schedule empty to keep job as draft. All times are in {systemTimezone}.
            </Typography>
          </Box>

          <Divider />

          {/* Advanced Options - Compact Grid */}
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, fontSize: '0.8rem', color: 'text.secondary' }}>
              ADVANCED OPTIONS
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  size="small"
                  type="number"
                  label="Priority"
                  value={formData.priority}
                  onChange={(e) => handleInputChange('priority', parseInt(e.target.value) || 5)}
                  inputProps={{ min: 1, max: 10 }}
                  helperText="1 (lowest) to 10 (highest)"
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  size="small"
                  type="number"
                  label="Timeout (seconds)"
                  value={formData.timeout || ''}
                  onChange={(e) => handleInputChange('timeout', e.target.value ? parseInt(e.target.value) : null)}
                  inputProps={{ min: 1 }}
                  helperText="Leave empty for no timeout"
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  size="small"
                  type="number"
                  label="Retry Count"
                  value={formData.retry_count}
                  onChange={(e) => handleInputChange('retry_count', parseInt(e.target.value) || 0)}
                  inputProps={{ min: 0, max: 5 }}
                  helperText="0 to 5 retries"
                />
              </Grid>
            </Grid>
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
          startIcon={loading ? <CircularProgress size={16} /> : <EditIcon fontSize="small" />}
          size="small"
        >
          {loading ? 'Updating...' : 'Update Job'}
        </Button>
      </DialogActions>

      {/* Target Selection Modal */}
      <TargetSelectionModal
        open={showTargetModal}
        onClose={() => setShowTargetModal(false)}
        selectedTargetIds={formData.target_ids}
        onSelectionChange={handleTargetSelectionChange}
      />
    </Dialog>
  );
};

export default JobEditModal;