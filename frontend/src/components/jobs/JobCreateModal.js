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
  Code as CodeIcon
} from '@mui/icons-material';

import { useAuth } from '../../contexts/AuthContext';
import TargetSelectionModal from './TargetSelectionModal';

const JobCreateModal = ({ open, onClose, onCreateJob }) => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [targets, setTargets] = useState([]);
  const [showTargetModal, setShowTargetModal] = useState(false);
  const [systemTimezone, setSystemTimezone] = useState('UTC');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    job_type: 'command',
    actions: [{
      action_order: 1,
      action_type: 'command',
      action_name: 'Execute Command',
      action_parameters: { command: '' }
    }],
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
      const response = await fetch('/api/system/info');
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
      // Reorder action_order
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
    if (formData.actions.some(action => !action.action_parameters.command.trim())) {
      newErrors.actions = 'All actions must have a command';
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
      
      const success = await onCreateJob(submitData);
      console.log('📤 Job creation result:', success);
      if (success) {
        onClose();
        // Reset form
        setFormData({
          name: '',
          description: '',
          job_type: 'command',
          actions: [{
            action_order: 1,
            action_type: 'command',
            action_name: 'Execute Command',
            action_parameters: { command: '' }
          }],
          target_ids: [],
          scheduled_at: null
        });
        setErrors({});
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
                        value={action.action_parameters.command}
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

          {/* Schedule - Compact */}
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, fontSize: '0.8rem', color: 'text.secondary' }}>
              SCHEDULE (OPTIONAL)
            </Typography>
            <TextField
              size="small"
              type="datetime-local"
              label={`Schedule Time (${systemTimezone})`}
              value={formData.scheduled_at || ''}
              onChange={(e) => handleInputChange('scheduled_at', e.target.value || null)}
              InputLabelProps={{ shrink: true }}
              helperText={`Leave empty to create as draft. Time will be in ${systemTimezone}`}
              inputProps={{
                min: (() => {
                  // Get current local time for min attribute
                  const now = new Date();
                  // Add 1 minute to avoid immediate past time issues
                  now.setMinutes(now.getMinutes() + 1);
                  // Format as local datetime string for datetime-local input
                  const year = now.getFullYear();
                  const month = String(now.getMonth() + 1).padStart(2, '0');
                  const day = String(now.getDate()).padStart(2, '0');
                  const hours = String(now.getHours()).padStart(2, '0');
                  const minutes = String(now.getMinutes()).padStart(2, '0');
                  return `${year}-${month}-${day}T${hours}:${minutes}`;
                })()
              }}
            />
            
            {/* SIMPLE PREVIEW - Just show the raw numbers */}
            {formData.scheduled_at && (
              <Box sx={{ mt: 1, p: 1, bgcolor: 'grey.50', borderRadius: 1, border: '1px solid', borderColor: 'grey.300' }}>
                <Typography variant="caption" sx={{ fontWeight: 600, color: 'text.secondary' }}>
                  SCHEDULE PREVIEW:
                </Typography>
                <Typography variant="body2" sx={{ fontSize: '0.75rem', mt: 0.5 }}>
                  📅 <strong>Date:</strong> {formData.scheduled_at.split('T')[0]}
                </Typography>
                <Typography variant="body2" sx={{ fontSize: '0.75rem', mt: 0.5 }}>
                  🕐 <strong>Time:</strong> {formData.scheduled_at.split('T')[1]} (24-hour format)
                </Typography>
                <Typography variant="body2" sx={{ fontSize: '0.75rem', mt: 0.5 }}>
                  🕐 <strong>Time in 12-hour:</strong> {(() => {
                    const timePart = formData.scheduled_at.split('T')[1];
                    const [hourStr, minuteStr] = timePart.split(':');
                    const hour = parseInt(hourStr);
                    const minute = minuteStr;
                    
                    if (hour === 0) return `12:${minute} AM`;
                    if (hour < 12) return `${hour}:${minute} AM`;
                    if (hour === 12) return `12:${minute} PM`;
                    return `${hour - 12}:${minute} PM`;
                  })()}
                </Typography>
                <Typography variant="body2" sx={{ fontSize: '0.75rem', color: 'success.main' }}>
                  ✅ This is exactly what you selected!
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
    </Dialog>
  );
};

export default JobCreateModal;