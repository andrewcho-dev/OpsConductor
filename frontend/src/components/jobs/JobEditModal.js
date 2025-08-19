/**
 * Job Edit Modal - Mirrors Job Creation Modal Exactly
 * Completely rebuilt to use the same components and structure as JobCreateModal
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
  Chip,
  IconButton,
  Grid,
  Divider,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Close as CloseIcon,
  Edit as EditIcon,
  Computer as ComputerIcon,
  Code as CodeIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';

import { useSessionAuth } from '../../contexts/SessionAuthContext';
import TargetSelectionModal from './TargetSelectionModal';
import ScheduleConfigModal from './ScheduleConfigModal';
import ActionsWorkspaceModal from './ActionsWorkspaceModal';

const JobEditModal = ({ open, job, onClose, onSubmit }) => {
  console.log('🔄 NEW JobEditModal loaded - rebuilt version!', { open, job });
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
    if (open && job) {
      fetchTargets();
      fetchSystemTimezone();
      fetchFullJobDetails();
    }
  }, [open, job]);

  const fetchFullJobDetails = async () => {
    if (!job?.id) {
      console.log('❌ No job ID to fetch details');
      return;
    }

    try {
      console.log('🔍 Fetching full job details for job ID:', job.id);
      const response = await fetch(`/api/v3/jobs/${job.id}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const fullJobData = await response.json();
        console.log('📋 Full job data received:', fullJobData);
        populateFormDataWithFullJob(fullJobData);
      } else {
        console.error('❌ Failed to fetch full job details:', response.status);
        // Fallback to using the passed job data
        populateFormData();
      }
    } catch (error) {
      console.error('❌ Error fetching full job details:', error);
      // Fallback to using the passed job data
      populateFormData();
    }
  };

  const populateFormDataWithFullJob = (fullJob) => {
    console.log('🔄 Populating form data with full job:', fullJob);
    
    // Transform actions from API format to frontend format
    const transformedActions = transformActionsForFrontend(fullJob.actions);
    console.log('🔄 Transformed actions:', transformedActions);

    // Extract target IDs from targets array
    const targetIds = fullJob.targets ? fullJob.targets.map(t => t.id) : [];
    console.log('🎯 Target IDs:', targetIds);

    // Set form data
    const initialFormData = {
      name: fullJob.name || '',
      description: fullJob.description || '',
      actions: transformedActions,
      target_ids: targetIds,
      scheduled_at: fullJob.scheduled_at || null
    };

    console.log('📝 Initial form data from full job:', initialFormData);
    setFormData(initialFormData);
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
      const response = await fetch('/api/system/info', {
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

  // Transform API actions to frontend format
  const transformActionsForFrontend = (apiActions) => {
    if (!apiActions || !Array.isArray(apiActions)) return [];
    
    return apiActions.map(apiAction => ({
      id: apiAction.id?.toString() || Date.now().toString(),
      type: apiAction.action_type || 'command',
      name: apiAction.action_name || 'Unnamed Action',
      order: apiAction.action_order || 1,
      enabled: true,
      continueOnError: false,
      timeout: 30,
      conditions: [],
      parameters: {
        ...apiAction.action_parameters,
        // Ensure captureOutput is set for backward compatibility
        captureOutput: apiAction.action_parameters?.captureOutput !== undefined 
          ? apiAction.action_parameters.captureOutput 
          : true
      },
      targetCompatibility: { compatible: true, warnings: [] }
    }));
  };

  const populateFormData = async () => {
    if (!job) {
      console.log('❌ No job provided to populate');
      return;
    }

    console.log('🔄 Populating form data for job:', job);
    console.log('🔍 Job structure:', Object.keys(job));

    try {
      // Transform actions from API format to frontend format
      const transformedActions = transformActionsForFrontend(job.actions);
      console.log('🔄 Transformed actions:', transformedActions);

      // First, try to use the job data that was passed in
      console.log('📋 Using passed job data:', {
        name: job.name,
        description: job.description,
        actions: job.actions,
        target_ids: job.target_ids,
        targets: job.targets
      });

      // Set basic form data from passed job
      const initialFormData = {
        name: job.name || '',
        description: job.description || '',
        actions: transformedActions,
        target_ids: job.target_ids || [],
        scheduled_at: job.scheduled_at || null
      };

      console.log('📝 Initial form data:', initialFormData);
      setFormData(initialFormData);

      // Try to fetch more complete job details from v2 API (includes actions and targets)
      const response = await fetch(`/api/v2/jobs/${job.id}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const fullJob = await response.json();
        console.log('📋 Full job data from API:', fullJob);

        // Update with more complete data if available
        // Extract target IDs from targets array if needed
        const targetIds = fullJob.target_ids || 
                         (fullJob.targets && fullJob.targets.length > 0 ? 
                          fullJob.targets.map(t => t.id || t.target_id || t.universal_target_id) : []) ||
                         job.target_ids || [];

        console.log('🎯 Extracted target IDs:', targetIds);
        console.log('🎯 Full job targets:', fullJob.targets);

        // If no targets found, try to get them from the job targets endpoint
        let finalTargetIds = targetIds;
        if (finalTargetIds.length === 0) {
          console.log('🔍 No targets found, trying to fetch from job targets endpoint...');
          try {
            const targetsResponse = await fetch(`/api/v3/jobs/${job.id}/targets`, {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              }
            });
            if (targetsResponse.ok) {
              const targetsData = await targetsResponse.json();
              console.log('📋 Job targets from API:', targetsData);
              if (targetsData.target_ids && targetsData.target_ids.length > 0) {
                finalTargetIds = targetsData.target_ids;
                console.log('🎯 Target IDs from targets endpoint:', finalTargetIds);
              }
            }
          } catch (error) {
            console.log('⚠️ Could not fetch job targets:', error);
          }
        }

        const updatedFormData = {
          name: fullJob.name || job.name || '',
          description: fullJob.description || job.description || '',
          actions: fullJob.actions || job.actions || [],
          target_ids: finalTargetIds,
          scheduled_at: fullJob.scheduled_at || job.scheduled_at || null
        };

        console.log('📝 Updated form data:', updatedFormData);
        setFormData(updatedFormData);

        // Set schedule config if exists
        if (fullJob.schedule_config) {
          console.log('📅 Setting schedule config from API:', fullJob.schedule_config);
          setScheduleConfig(fullJob.schedule_config);
        } else if (fullJob.scheduled_at) {
          // Create a basic schedule config from scheduled_at
          console.log('📅 Creating schedule config from scheduled_at:', fullJob.scheduled_at);
          const scheduleConfig = {
            scheduleType: 'once',
            executeAt: fullJob.scheduled_at
          };
          setScheduleConfig(scheduleConfig);
          console.log('📅 Created schedule config:', scheduleConfig);
        } else {
          console.log('📅 No schedule config found');
          setScheduleConfig(null);
        }

        console.log('✅ Form populated successfully with API data');
      } else {
        console.log('⚠️ API fetch failed, using passed job data');
        // Still try to create schedule config from passed job data
        if (job.scheduled_at) {
          console.log('📅 Creating schedule config from passed job scheduled_at:', job.scheduled_at);
          const scheduleConfig = {
            scheduleType: 'once',
            executeAt: job.scheduled_at
          };
          setScheduleConfig(scheduleConfig);
        }
      }
    } catch (error) {
      console.error('❌ Error fetching job details:', error);
      console.log('🔄 Using fallback job data');
      // Still try to create schedule config from passed job data
      if (job.scheduled_at) {
        console.log('📅 Creating fallback schedule config from job scheduled_at:', job.scheduled_at);
        const scheduleConfig = {
          scheduleType: 'once',
          executeAt: job.scheduled_at
        };
        setScheduleConfig(scheduleConfig);
      }
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
    console.log('🔧 Actions configured:', actionsData);
    setFormData(prev => ({ ...prev, actions: actionsData }));
    setShowActionsModal(false);
  };

  // Transform frontend actions back to API format
  const transformActionsForAPI = (frontendActions) => {
    if (!frontendActions || !Array.isArray(frontendActions)) return [];
    
    return frontendActions.map(frontendAction => ({
      action_name: frontendAction.name,
      action_type: frontendAction.type,
      action_parameters: frontendAction.parameters || {}
    }));
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
    console.log('🎯 Edit form submission started');
    console.log('📝 Form data:', formData);
    
    if (!validateForm()) {
      console.log('❌ Form validation failed:', errors);
      return;
    }
    
    console.log('✅ Form validation passed');
    setLoading(true);
    try {
      // Prepare form data with proper datetime handling and action transformation
      const submitData = { 
        ...formData,
        actions: transformActionsForAPI(formData.actions)
      };
      
      console.log('🔄 Transformed actions for API:', submitData.actions);
      
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
      const success = await onSubmit(job.id, submitData, scheduleConfig);
      console.log('📤 Job update result:', success);
      console.log('📅 Schedule config:', scheduleConfig);
      if (success) {
        onClose();
      }
    } finally {
      setLoading(false);
    }
  };

  const selectedTargets = targets.filter(t => formData.target_ids.includes(t.id));

  return (
    <>
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
            <EditIcon fontSize="small" />
            Edit Job: {job?.name}
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

            {/* Scheduling - Optional */}
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, fontSize: '0.8rem', color: 'text.secondary' }}>
                SCHEDULING (Optional)
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
                {!scheduleConfig 
                  ? 'Configure Schedule (Run Immediately)' 
                  : `Scheduled: ${scheduleConfig.scheduleType || 'Custom'}`
                }
              </Button>

              {scheduleConfig && (
                <Box sx={{ mt: 1, p: 1.5, bgcolor: 'warning.50', borderRadius: 1, border: '1px solid', borderColor: 'warning.200' }}>
                  <Typography variant="caption" sx={{ fontWeight: 600, color: 'warning.dark' }}>
                    SCHEDULE CONFIGURED:
                  </Typography>
                  <Typography variant="body2" sx={{ fontSize: '0.75rem', mt: 0.5, color: 'warning.dark' }}>
                    Type: {scheduleConfig.scheduleType}
                  </Typography>
                  {scheduleConfig.executeAt && (
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', color: 'warning.dark' }}>
                      Execute At: {new Date(scheduleConfig.executeAt).toLocaleString()}
                    </Typography>
                  )}
                </Box>
              )}
            </Box>

          </Box>
        </DialogContent>

        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained" 
            disabled={loading}
            startIcon={loading ? <CircularProgress size={16} /> : <EditIcon />}
          >
            {loading ? 'Updating...' : 'Update Job'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Target Selection Modal */}
      <TargetSelectionModal
        open={showTargetModal}
        onClose={() => setShowTargetModal(false)}
        targets={targets}
        selectedTargetIds={formData.target_ids}
        onSelectionChange={handleTargetSelectionChange}
      />

      {/* Actions Workspace Modal */}
      <ActionsWorkspaceModal
        open={showActionsModal}
        onClose={() => setShowActionsModal(false)}
        initialActions={formData.actions}
        onActionsConfigured={handleActionsConfiguration}
      />

      {/* Schedule Configuration Modal */}
      <ScheduleConfigModal
        open={showSchedulingModal}
        onClose={() => setShowSchedulingModal(false)}
        onConfigurationComplete={handleScheduleConfiguration}
        initialConfig={scheduleConfig}
        systemTimezone={systemTimezone}
      />
    </>
  );
};

export default JobEditModal;