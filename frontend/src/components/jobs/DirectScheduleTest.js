import React, { useState } from 'react';
import { 
  Button, 
  TextField, 
  Box, 
  Typography, 
  Paper, 
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import { useSessionAuth } from '../../contexts/SessionAuthContext';
import axios from 'axios';

/**
 * A direct test component to create a minutes-based recurring schedule
 * This bypasses all the complex UI components and directly calls the API
 */
const DirectScheduleTest = () => {
  const { user } = useSessionAuth();
  const token = localStorage.getItem('access_token');
  
  // Create a direct API client
  const api = axios.create({
    baseURL: process.env.REACT_APP_API_URL || '',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    }
  });
  const [jobId, setJobId] = useState('');
  const [interval, setInterval] = useState(2);
  const [recurringType, setRecurringType] = useState('minutes');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      console.log(`🧪 Creating direct schedule for job ${jobId} with ${recurringType} interval ${interval}`);
      
      // Create schedule data directly
      const scheduleData = {
        job_id: parseInt(jobId),
        schedule_type: 'recurring',
        recurring_type: recurringType,
        interval: parseInt(interval),
        enabled: true,
        timezone: 'UTC',
        description: `Direct test schedule: every ${interval} ${recurringType}`
      };
      
      // For non-minutes/hours types, add time
      if (!['minutes', 'hours'].includes(recurringType)) {
        scheduleData.time = '09:00';
      }
      
      // For weekly, add days of week
      if (recurringType === 'weekly') {
        scheduleData.days_of_week = '1,2,3,4,5'; // Mon-Fri
      }
      
      // For monthly, add day of month
      if (recurringType === 'monthly') {
        scheduleData.day_of_month = 1;
      }
      
      console.log('📤 Direct schedule data:', JSON.stringify(scheduleData, null, 2));
      
      // First, delete any existing schedules
      try {
        const existingSchedulesResponse = await api.get(`/schedules?job_id=${jobId}`);
        if (existingSchedulesResponse.data && existingSchedulesResponse.data.length > 0) {
          console.log(`🗑️ Found ${existingSchedulesResponse.data.length} existing schedules to delete`);
          
          for (const existingSchedule of existingSchedulesResponse.data) {
            console.log(`🗑️ Deleting schedule ${existingSchedule.id}`);
            await api.delete(`/schedules/${existingSchedule.id}`);
          }
        }
      } catch (deleteError) {
        console.log('⚠️ No existing schedules or delete failed:', deleteError.message);
      }
      
      // Create the new schedule
      const response = await api.post('/schedules', scheduleData);
      
      console.log('✅ Schedule created:', response.data);
      setResult(response.data);
      
      // Update the job status to show it's scheduled
      try {
        const jobResponse = await api.get(`/jobs/${jobId}`);
        const jobData = jobResponse.data;
        
        console.log('📋 Current job data:', jobData);
        
        // Update the job to show it's scheduled
        const updateResponse = await api.put(`/jobs/${jobId}`, {
          ...jobData,
          status: 'scheduled'
        });
        
        console.log('✅ Job updated to scheduled status:', updateResponse.data);
      } catch (jobError) {
        console.error('❌ Failed to update job status:', jobError);
        setError(`Schedule created but failed to update job status: ${jobError.message}`);
      }
    } catch (err) {
      console.error('❌ Schedule creation error:', err);
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper sx={{ p: 3, maxWidth: 600, mx: 'auto', mt: 4 }}>
      <Typography variant="h5" gutterBottom>
        Direct Schedule Creator
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        This tool directly creates a schedule for a job, bypassing the complex UI components.
      </Typography>
      
      <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
        <TextField
          fullWidth
          label="Job ID"
          value={jobId}
          onChange={(e) => setJobId(e.target.value)}
          margin="normal"
          required
          type="number"
        />
        
        <FormControl fullWidth margin="normal">
          <InputLabel>Recurring Type</InputLabel>
          <Select
            value={recurringType}
            label="Recurring Type"
            onChange={(e) => setRecurringType(e.target.value)}
          >
            <MenuItem value="minutes">Minutes</MenuItem>
            <MenuItem value="hours">Hours</MenuItem>
            <MenuItem value="daily">Daily</MenuItem>
            <MenuItem value="weekly">Weekly</MenuItem>
            <MenuItem value="monthly">Monthly</MenuItem>
          </Select>
        </FormControl>
        
        <TextField
          fullWidth
          label={`Interval (${recurringType})`}
          value={interval}
          onChange={(e) => setInterval(e.target.value)}
          margin="normal"
          required
          type="number"
          inputProps={{ min: 1 }}
        />
        
        <Button 
          type="submit" 
          variant="contained" 
          color="primary" 
          sx={{ mt: 2 }}
          disabled={loading}
        >
          {loading ? <CircularProgress size={24} /> : 'Create Schedule'}
        </Button>
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
      
      {result && (
        <Box sx={{ mt: 3 }}>
          <Alert severity="success" sx={{ mb: 2 }}>
            Schedule created successfully!
          </Alert>
          
          <Typography variant="subtitle1">Schedule Details:</Typography>
          <Box component="pre" sx={{ 
            p: 2, 
            bgcolor: 'grey.100', 
            borderRadius: 1,
            overflow: 'auto',
            fontSize: '0.875rem'
          }}>
            {JSON.stringify(result, null, 2)}
          </Box>
        </Box>
      )}
    </Paper>
  );
};

export default DirectScheduleTest;