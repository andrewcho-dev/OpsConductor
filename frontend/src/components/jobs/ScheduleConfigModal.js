/**
 * Schedule Configuration Modal - For configuring schedules during job creation
 * This is a simplified version that just collects schedule data without making API calls
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
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Schedule as ScheduleIcon,
  Repeat as RepeatIcon,
  Event as EventIcon,
  AccessTime as TimeIcon,
  CalendarToday as CalendarIcon,
  Close as CloseIcon,
} from '@mui/icons-material';

const ScheduleConfigModal = ({ open, onClose, onConfigurationComplete, initialConfig = null }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [scheduleType, setScheduleType] = useState('once'); // once, recurring, cron
  const [scheduleData, setScheduleData] = useState({
    // One-time scheduling
    executeAt: '',
    
    // Recurring scheduling
    recurringType: 'daily', // minutes, hours, daily, weekly, monthly
    interval: 1,
    daysOfWeek: [],
    dayOfMonth: 1,
    time: '09:00',
    startDate: '', // First occurrence date
    startTime: '09:00', // First occurrence time
    
    // Cron scheduling
    cronExpression: '0 9 * * *',
    
    // Advanced options
    timezone: 'local', // Will be set to system timezone
    maxExecutions: null,
    endDate: '',
    enabled: true,
  });
  const [systemTimezone, setSystemTimezone] = useState('UTC');

  useEffect(() => {
    if (open) {
      fetchSystemTimezone();
      // Load initial configuration if provided
      if (initialConfig) {
        setScheduleType(initialConfig.scheduleType || 'once');
        setScheduleData(prev => ({ ...prev, ...initialConfig }));
      }
    }
  }, [open, initialConfig]);

  const fetchSystemTimezone = async () => {
    try {
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      setSystemTimezone(timezone);
      setScheduleData(prev => ({ ...prev, timezone }));
    } catch (error) {
      console.error('Failed to get system timezone:', error);
    }
  };

  const handleScheduleDataChange = (field, value) => {
    setScheduleData(prev => ({ ...prev, [field]: value }));
  };

  const handleDayOfWeekToggle = (day) => {
    setScheduleData(prev => ({
      ...prev,
      daysOfWeek: prev.daysOfWeek.includes(day)
        ? prev.daysOfWeek.filter(d => d !== day)
        : [...prev.daysOfWeek, day]
    }));
  };

  const handleSubmit = () => {
    const configData = {
      scheduleType,
      ...scheduleData,
    };
    onConfigurationComplete(configData);
  };

  const handleCancel = () => {
    onClose();
  };

  const getMinDateTime = () => {
    const now = new Date();
    now.setMinutes(now.getMinutes() + 1);
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  const renderOneTimeScheduling = () => (
    <Box sx={{ mt: 2 }}>
      <TextField
        fullWidth
        type="datetime-local"
        label={`Execute At (${systemTimezone})`}
        value={scheduleData.executeAt}
        onChange={(e) => handleScheduleDataChange('executeAt', e.target.value)}
        InputLabelProps={{ shrink: true }}
        inputProps={{ min: getMinDateTime() }}
        helperText="Select when this job should be executed"
      />
    </Box>
  );

  const renderRecurringScheduling = () => (
    <Box sx={{ mt: 2 }}>
      <Grid container spacing={2}>
        {/* Recurring Pattern */}
        <Grid item xs={12}>
          <Typography variant="subtitle2" sx={{ mb: 2, color: 'text.secondary' }}>
            RECURRENCE PATTERN
          </Typography>
        </Grid>
        
        <Grid item xs={12} sm={4}>
          <FormControl fullWidth>
            <InputLabel>Recurring Type</InputLabel>
            <Select
              value={scheduleData.recurringType}
              label="Recurring Type"
              onChange={(e) => handleScheduleDataChange('recurringType', e.target.value)}
            >
              <MenuItem value="minutes">Minutes</MenuItem>
              <MenuItem value="hours">Hours</MenuItem>
              <MenuItem value="daily">Daily</MenuItem>
              <MenuItem value="weekly">Weekly</MenuItem>
              <MenuItem value="monthly">Monthly</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} sm={4}>
          <TextField
            fullWidth
            type="number"
            label={`Every X ${scheduleData.recurringType === 'minutes' ? 'Minutes' :
                              scheduleData.recurringType === 'hours' ? 'Hours' :
                              scheduleData.recurringType === 'daily' ? 'Days' : 
                              scheduleData.recurringType === 'weekly' ? 'Weeks' : 'Months'}`}
            value={scheduleData.interval}
            onChange={(e) => handleScheduleDataChange('interval', Math.max(1, parseInt(e.target.value) || 1))}
            inputProps={{ 
              min: 1, 
              max: scheduleData.recurringType === 'minutes' ? 1440 : // Max 1440 minutes (24 hours)
                   scheduleData.recurringType === 'hours' ? 168 : // Max 168 hours (1 week)
                   365 // Max 365 for days/weeks/months
            }}
            helperText={`Run every ${scheduleData.interval} ${
              scheduleData.recurringType === 'minutes' ? 'minute(s)' :
              scheduleData.recurringType === 'hours' ? 'hour(s)' :
              scheduleData.recurringType === 'daily' ? 'day(s)' : 
              scheduleData.recurringType === 'weekly' ? 'week(s)' : 'month(s)'
            }`}
          />
        </Grid>
        
        {/* Time field only for daily, weekly, monthly */}
        {!['minutes', 'hours'].includes(scheduleData.recurringType) && (
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              type="time"
              label="Time"
              value={scheduleData.time}
              onChange={(e) => handleScheduleDataChange('time', e.target.value)}
              InputLabelProps={{ shrink: true }}
              helperText="Time of day to run"
            />
          </Grid>
        )}
        
        {/* Weekly specific options */}
        {scheduleData.recurringType === 'weekly' && (
          <Grid item xs={12}>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>Days of Week</Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map((day, index) => (
                <Chip
                  key={day}
                  label={day}
                  onClick={() => handleDayOfWeekToggle(index + 1)}
                  variant={scheduleData.daysOfWeek.includes(index + 1) ? 'filled' : 'outlined'}
                  color={scheduleData.daysOfWeek.includes(index + 1) ? 'primary' : 'default'}
                />
              ))}
            </Box>
            {scheduleData.daysOfWeek.length === 0 && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Select at least one day of the week
              </Typography>
            )}
          </Grid>
        )}
        
        {/* Monthly specific options */}
        {scheduleData.recurringType === 'monthly' && (
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              type="number"
              label="Day of Month"
              value={scheduleData.dayOfMonth}
              onChange={(e) => handleScheduleDataChange('dayOfMonth', parseInt(e.target.value))}
              inputProps={{ min: 1, max: 31 }}
              helperText="Day of the month (1-31)"
            />
          </Grid>
        )}
        
        {/* First Occurrence */}
        <Grid item xs={12}>
          <Typography variant="subtitle2" sx={{ mb: 2, mt: 2, color: 'text.secondary' }}>
            FIRST OCCURRENCE
          </Typography>
        </Grid>
        
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            type="date"
            label="Start Date"
            value={scheduleData.startDate}
            onChange={(e) => handleScheduleDataChange('startDate', e.target.value)}
            InputLabelProps={{ shrink: true }}
            inputProps={{ 
              min: (() => {
                const today = new Date();
                return today.toISOString().split('T')[0];
              })()
            }}
            helperText="Date of first execution"
          />
        </Grid>
        
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            type="time"
            label="Start Time"
            value={scheduleData.startTime}
            onChange={(e) => handleScheduleDataChange('startTime', e.target.value)}
            InputLabelProps={{ shrink: true }}
            helperText="Time of first execution"
          />
        </Grid>
        
        {/* Recurrence Preview */}
        {scheduleData.startDate && (
          <Grid item xs={12}>
            <Card variant="outlined" sx={{ bgcolor: 'info.50', borderColor: 'info.200' }}>
              <CardContent sx={{ py: 1.5 }}>
                <Typography variant="subtitle2" sx={{ color: 'info.dark', mb: 1 }}>
                  📅 RECURRENCE PREVIEW
                </Typography>
                <Typography variant="body2" sx={{ color: 'info.dark' }}>
                  <strong>Pattern:</strong> Every {scheduleData.interval} {
                    scheduleData.recurringType === 'minutes' ? 'minute(s)' :
                    scheduleData.recurringType === 'hours' ? 'hour(s)' :
                    scheduleData.recurringType === 'daily' ? 'day(s)' : 
                    scheduleData.recurringType === 'weekly' ? 'week(s)' : 'month(s)'
                  } 
                  {scheduleData.recurringType === 'weekly' && scheduleData.daysOfWeek.length > 0 && 
                    ` on ${scheduleData.daysOfWeek.map(d => ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][d-1]).join(', ')}`}
                  {scheduleData.recurringType === 'monthly' && ` on day ${scheduleData.dayOfMonth}`}
                  <br/>
                  <strong>First run:</strong> {new Date(scheduleData.startDate + 'T' + scheduleData.startTime).toLocaleString()}
                  <br/>
                  {!['minutes', 'hours'].includes(scheduleData.recurringType) && (
                    <><strong>Time:</strong> {scheduleData.time} daily<br/></>
                  )}
                  {['minutes', 'hours'].includes(scheduleData.recurringType) && (
                    <><strong>Note:</strong> Runs continuously every {scheduleData.interval} {scheduleData.recurringType}<br/></>
                  )}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );

  const renderCronScheduling = () => (
    <Box sx={{ mt: 2 }}>
      <TextField
        fullWidth
        label="Cron Expression"
        value={scheduleData.cronExpression}
        onChange={(e) => handleScheduleDataChange('cronExpression', e.target.value)}
        helperText="Format: minute hour day month day-of-week (e.g., '0 9 * * *' for daily at 9 AM)"
        placeholder="0 9 * * *"
      />
      <Alert severity="info" sx={{ mt: 1 }}>
        <Typography variant="body2">
          Common patterns:<br/>
          • <code>0 9 * * *</code> - Daily at 9:00 AM<br/>
          • <code>0 9 * * 1-5</code> - Weekdays at 9:00 AM<br/>
          • <code>0 0 1 * *</code> - First day of every month at midnight
        </Typography>
      </Alert>
    </Box>
  );

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ScheduleIcon />
          Configure Schedule
        </Box>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 2, color: 'text.secondary' }}>
            SCHEDULE TYPE
          </Typography>
          <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
            <Tab 
              label="One-time" 
              icon={<EventIcon />} 
              onClick={() => setScheduleType('once')}
            />
            <Tab 
              label="Recurring" 
              icon={<RepeatIcon />} 
              onClick={() => setScheduleType('recurring')}
            />
            <Tab 
              label="Cron Expression" 
              icon={<TimeIcon />} 
              onClick={() => setScheduleType('cron')}
            />
          </Tabs>
        </Box>

        {activeTab === 0 && renderOneTimeScheduling()}
        {activeTab === 1 && renderRecurringScheduling()}
        {activeTab === 2 && renderCronScheduling()}

        {/* Advanced Options */}
        <Divider sx={{ my: 3 }} />
        <Typography variant="subtitle2" sx={{ mb: 2, color: 'text.secondary' }}>
          ADVANCED OPTIONS (OPTIONAL)
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              type="number"
              label="Max Executions"
              value={scheduleData.maxExecutions || ''}
              onChange={(e) => handleScheduleDataChange('maxExecutions', e.target.value ? parseInt(e.target.value) : null)}
              helperText="Leave empty for unlimited"
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              type="date"
              label="End Date"
              value={scheduleData.endDate}
              onChange={(e) => handleScheduleDataChange('endDate', e.target.value)}
              InputLabelProps={{ shrink: true }}
              helperText="Leave empty for no end date"
            />
          </Grid>
        </Grid>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleCancel}>Cancel</Button>
        <Button onClick={handleSubmit} variant="contained" startIcon={<ScheduleIcon />}>
          Apply Schedule Configuration
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ScheduleConfigModal;