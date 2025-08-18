/**
 * Job Scheduling Modal - Advanced scheduling with recurrence patterns
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
  TextField,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Select,
  MenuItem,
  InputLabel,
  Grid,
  Chip,
  Alert,
  Tabs,
  Tab,
  Card,
  CardContent,
  Switch,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Schedule as ScheduleIcon,
  Repeat as RepeatIcon,
  Event as EventIcon,
  AccessTime as TimeIcon,
  CalendarToday as CalendarIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  PlayArrow as PlayIcon,
} from '@mui/icons-material';

const JobSchedulingModal = ({ open, onClose, job, onSchedule, token }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [scheduleType, setScheduleType] = useState('once'); // once, recurring, cron
  const [scheduleData, setScheduleData] = useState({
    // One-time scheduling
    executeAt: '',
    
    // Recurring scheduling
    recurringType: 'daily', // daily, weekly, monthly
    interval: 1,
    daysOfWeek: [],
    dayOfMonth: 1,
    time: '09:00',
    
    // Cron scheduling
    cronExpression: '0 9 * * *',
    
    // Advanced options
    timezone: 'local', // Will be set to system timezone
    maxExecutions: null,
    endDate: '',
    enabled: true,
  });
  const [cronPreview, setCronPreview] = useState([]);
  const [existingSchedules, setExistingSchedules] = useState([]);
  const [systemTimezone, setSystemTimezone] = useState('UTC');

  useEffect(() => {
    if (open && job) {
      fetchExistingSchedules();
      fetchSystemTimezone();
    }
  }, [open, job]);

  useEffect(() => {
    if (scheduleType === 'cron') {
      generateCronPreview();
    }
  }, [scheduleData.cronExpression]);

  const fetchExistingSchedules = async () => {
    try {
      const response = await fetch(`/api/jobs/${job.id}/schedules`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setExistingSchedules(data.schedules || []);
      }
    } catch (error) {
      console.error('Error fetching schedules:', error);
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
        const timezoneInfo = data.timezone?.display_name || 'UTC';
        setSystemTimezone(timezoneInfo);
        // Update the schedule data to use system timezone
        setScheduleData(prev => ({
          ...prev,
          timezone: timezoneInfo
        }));
      }
    } catch (error) {
      console.error('Failed to fetch system timezone:', error);
    }
  };

  const generateCronPreview = () => {
    // This would typically use a cron parsing library
    // For now, just show a simple preview
    const previews = [
      'Next run: Today at 9:00 AM',
      'Following runs: Tomorrow at 9:00 AM',
      'Pattern: Daily at 9:00 AM',
    ];
    setCronPreview(previews);
  };

  const handleScheduleTypeChange = (event) => {
    setScheduleType(event.target.value);
  };

  const handleRecurringChange = (field, value) => {
    setScheduleData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleDayOfWeekToggle = (day) => {
    setScheduleData(prev => ({
      ...prev,
      daysOfWeek: prev.daysOfWeek.includes(day)
        ? prev.daysOfWeek.filter(d => d !== day)
        : [...prev.daysOfWeek, day]
    }));
  };

  const handleSubmit = async () => {
    try {
      let schedulePayload = {
        job_id: job.id,
        schedule_type: scheduleType,
        enabled: scheduleData.enabled,
        timezone: scheduleData.timezone,
      };

      switch (scheduleType) {
        case 'once':
          schedulePayload.execute_at = scheduleData.executeAt;
          break;
        case 'recurring':
          schedulePayload.recurring_type = scheduleData.recurringType;
          schedulePayload.interval = scheduleData.interval;
          schedulePayload.time = scheduleData.time;
          if (scheduleData.recurringType === 'weekly') {
            schedulePayload.days_of_week = scheduleData.daysOfWeek;
          } else if (scheduleData.recurringType === 'monthly') {
            schedulePayload.day_of_month = scheduleData.dayOfMonth;
          }
          break;
        case 'cron':
          schedulePayload.cron_expression = scheduleData.cronExpression;
          break;
      }

      if (scheduleData.maxExecutions) {
        schedulePayload.max_executions = scheduleData.maxExecutions;
      }
      if (scheduleData.endDate) {
        schedulePayload.end_date = scheduleData.endDate;
      }

      const response = await fetch('/api/jobs/schedules', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(schedulePayload),
      });

      if (response.ok) {
        const result = await response.json();
        onSchedule(result);
        onClose();
      } else {
        console.error('Failed to create schedule');
      }
    } catch (error) {
      console.error('Error creating schedule:', error);
    }
  };

  const deleteSchedule = async (scheduleId) => {
    try {
      const response = await fetch(`/api/jobs/schedules/${scheduleId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        fetchExistingSchedules();
      }
    } catch (error) {
      console.error('Error deleting schedule:', error);
    }
  };

  const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const commonCronExpressions = [
    { label: 'Every minute', value: '* * * * *' },
    { label: 'Every hour', value: '0 * * * *' },
    { label: 'Daily at 9 AM', value: '0 9 * * *' },
    { label: 'Weekly on Monday at 9 AM', value: '0 9 * * 1' },
    { label: 'Monthly on 1st at 9 AM', value: '0 9 1 * *' },
    { label: 'Weekdays at 9 AM', value: '0 9 * * 1-5' },
  ];

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center">
          <ScheduleIcon sx={{ mr: 1 }} />
          Schedule Job: {job?.name}
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)} sx={{ mb: 3 }}>
          <Tab label="New Schedule" icon={<AddIcon />} />
          <Tab label="Existing Schedules" icon={<EventIcon />} />
        </Tabs>

        {activeTab === 0 && (
          <Box>
            {/* Schedule Type Selection */}
            <FormControl component="fieldset" sx={{ mb: 3 }}>
              <FormLabel component="legend">Schedule Type</FormLabel>
              <RadioGroup
                value={scheduleType}
                onChange={handleScheduleTypeChange}
                row
              >
                <FormControlLabel value="once" control={<Radio />} label="One-time" />
                <FormControlLabel value="recurring" control={<Radio />} label="Recurring" />
                <FormControlLabel value="cron" control={<Radio />} label="Cron Expression" />
              </RadioGroup>
            </FormControl>

            {/* One-time Schedule */}
            {scheduleType === 'once' && (
              <Card variant="outlined" sx={{ p: 2, mb: 2 }}>
                <Typography variant="h6" gutterBottom>
                  <EventIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  One-time Execution
                </Typography>
                <TextField
                  fullWidth
                  label={`Execute At (${systemTimezone})`}
                  type="datetime-local"
                  value={scheduleData.executeAt}
                  onChange={(e) => handleRecurringChange('executeAt', e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  helperText={`Select execution time in ${systemTimezone}`}
                />
              </Card>
            )}

            {/* Recurring Schedule */}
            {scheduleType === 'recurring' && (
              <Card variant="outlined" sx={{ p: 2, mb: 2 }}>
                <Typography variant="h6" gutterBottom>
                  <RepeatIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Recurring Schedule
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth>
                      <InputLabel>Frequency</InputLabel>
                      <Select
                        value={scheduleData.recurringType}
                        onChange={(e) => handleRecurringChange('recurringType', e.target.value)}
                        label="Frequency"
                      >
                        <MenuItem value="daily">Daily</MenuItem>
                        <MenuItem value="weekly">Weekly</MenuItem>
                        <MenuItem value="monthly">Monthly</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Every"
                      type="number"
                      value={scheduleData.interval}
                      onChange={(e) => handleRecurringChange('interval', parseInt(e.target.value))}
                      InputProps={{
                        endAdornment: scheduleData.recurringType === 'daily' ? 'day(s)' : 
                                     scheduleData.recurringType === 'weekly' ? 'week(s)' : 'month(s)'
                      }}
                    />
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label={`Time (${systemTimezone})`}
                      type="time"
                      value={scheduleData.time}
                      onChange={(e) => handleRecurringChange('time', e.target.value)}
                      InputLabelProps={{ shrink: true }}
                      helperText={`Time in ${systemTimezone}`}
                    />
                  </Grid>

                  {scheduleData.recurringType === 'weekly' && (
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" gutterBottom>Days of Week</Typography>
                      <Box>
                        {daysOfWeek.map((day, index) => (
                          <Chip
                            key={day}
                            label={day}
                            onClick={() => handleDayOfWeekToggle(index)}
                            color={scheduleData.daysOfWeek.includes(index) ? 'primary' : 'default'}
                            variant={scheduleData.daysOfWeek.includes(index) ? 'filled' : 'outlined'}
                            sx={{ mr: 1, mb: 1 }}
                          />
                        ))}
                      </Box>
                    </Grid>
                  )}

                  {scheduleData.recurringType === 'monthly' && (
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Day of Month"
                        type="number"
                        value={scheduleData.dayOfMonth}
                        onChange={(e) => handleRecurringChange('dayOfMonth', parseInt(e.target.value))}
                        inputProps={{ min: 1, max: 31 }}
                      />
                    </Grid>
                  )}
                </Grid>
              </Card>
            )}

            {/* Cron Schedule */}
            {scheduleType === 'cron' && (
              <Card variant="outlined" sx={{ p: 2, mb: 2 }}>
                <Typography variant="h6" gutterBottom>
                  <TimeIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Cron Expression
                </Typography>
                
                <TextField
                  fullWidth
                  label="Cron Expression"
                  value={scheduleData.cronExpression}
                  onChange={(e) => handleRecurringChange('cronExpression', e.target.value)}
                  placeholder="0 9 * * *"
                  helperText="Format: minute hour day month day-of-week"
                  sx={{ mb: 2 }}
                />

                <Typography variant="subtitle2" gutterBottom>Common Patterns</Typography>
                <Box sx={{ mb: 2 }}>
                  {commonCronExpressions.map((expr) => (
                    <Chip
                      key={expr.value}
                      label={expr.label}
                      onClick={() => handleRecurringChange('cronExpression', expr.value)}
                      variant="outlined"
                      sx={{ mr: 1, mb: 1 }}
                    />
                  ))}
                </Box>

                {cronPreview.length > 0 && (
                  <Alert severity="info">
                    <Typography variant="subtitle2">Preview:</Typography>
                    {cronPreview.map((preview, index) => (
                      <Typography key={index} variant="body2">{preview}</Typography>
                    ))}
                  </Alert>
                )}
              </Card>
            )}

            {/* Advanced Options */}
            <Card variant="outlined" sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Advanced Options</Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Max Executions"
                    type="number"
                    value={scheduleData.maxExecutions || ''}
                    onChange={(e) => handleRecurringChange('maxExecutions', e.target.value ? parseInt(e.target.value) : null)}
                    helperText="Leave empty for unlimited"
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="End Date"
                    type="date"
                    value={scheduleData.endDate}
                    onChange={(e) => handleRecurringChange('endDate', e.target.value)}
                    InputLabelProps={{ shrink: true }}
                    helperText="Leave empty for no end date"
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Timezone"
                    value={systemTimezone}
                    InputProps={{
                      readOnly: true,
                    }}
                    helperText="All times are in system timezone"
                    variant="outlined"
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={scheduleData.enabled}
                        onChange={(e) => handleRecurringChange('enabled', e.target.checked)}
                      />
                    }
                    label="Enable Schedule"
                    sx={{ mt: 2 }}
                  />
                </Grid>
              </Grid>
            </Card>
          </Box>
        )}

        {activeTab === 1 && (
          <Box>
            <Typography variant="h6" gutterBottom>Existing Schedules</Typography>
            
            {existingSchedules.length === 0 ? (
              <Alert severity="info">No schedules found for this job.</Alert>
            ) : (
              <List>
                {existingSchedules.map((schedule) => (
                  <ListItem key={schedule.id}>
                    <ListItemIcon>
                      <ScheduleIcon color={schedule.enabled ? 'primary' : 'disabled'} />
                    </ListItemIcon>
                    <ListItemText
                      primary={`${schedule.schedule_type} - ${schedule.description || 'No description'}`}
                      secondary={`Next run: ${schedule.next_run || 'Not scheduled'} | Status: ${schedule.enabled ? 'Enabled' : 'Disabled'}`}
                    />
                    <Tooltip title="Delete Schedule">
                      <IconButton
                        edge="end"
                        onClick={() => deleteSchedule(schedule.id)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </ListItem>
                ))}
              </List>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        {activeTab === 0 && (
          <Button
            onClick={handleSubmit}
            variant="contained"
            startIcon={<ScheduleIcon />}
          >
            Create Schedule
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default JobSchedulingModal;