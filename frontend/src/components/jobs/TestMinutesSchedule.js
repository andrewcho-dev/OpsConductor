import React, { useState } from 'react';
import { 
  Button, 
  TextField, 
  Box, 
  Typography, 
  Paper, 
  Alert,
  CircularProgress
} from '@mui/material';
import { useSessionAuth } from '../../contexts/SessionAuthContext';
import { apiService } from '../../services/apiService';

const TestMinutesSchedule = () => {
  const { user } = useSessionAuth();
  const [jobId, setJobId] = useState('');
  const [interval, setInterval] = useState(2);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      console.log(`🧪 Testing minutes schedule for job ${jobId} with interval ${interval}`);
      
      // Call the test endpoint
      const response = await apiService.post(
        `${process.env.REACT_APP_API_URL || ''}/schedules/test-minutes?job_id=${jobId}&interval=${interval}`
      );
      
      console.log('✅ Test response:', response.data);
      setResult(response.data);
    } catch (err) {
      console.error('❌ Test error:', err);
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper sx={{ p: 3, maxWidth: 600, mx: 'auto', mt: 4 }}>
      <Typography variant="h5" gutterBottom>
        Test Minutes-Based Schedule
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
        
        <TextField
          fullWidth
          label="Interval (minutes)"
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
          {loading ? <CircularProgress size={24} /> : 'Create Test Schedule'}
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

export default TestMinutesSchedule;