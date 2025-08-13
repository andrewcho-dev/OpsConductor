import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { formatLocalDateTime, formatLocalTime, formatLocalDate } from '../../utils/timeUtils';

const TimezoneTest = () => {
  // Test with various UTC datetime strings that might come from backend
  const testDates = [
    '2024-01-15T14:30:00Z',           // UTC with Z
    '2024-01-15T14:30:00',            // UTC without Z (backend format)
    '2024-01-15T14:30:00.123456Z',    // UTC with microseconds
    '2024-01-15T14:30:00+00:00',      // UTC with offset
    new Date().toISOString(),         // Current time in UTC
  ];

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Timezone Conversion Test
      </Typography>
      
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Testing conversion of UTC datetime strings from backend to local time display
      </Typography>

      {testDates.map((utcString, index) => (
        <Paper key={index} sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle2" color="primary">
            Test {index + 1}:
          </Typography>
          <Typography variant="body2" sx={{ fontFamily: 'monospace', mb: 1 }}>
            <strong>UTC Input:</strong> {utcString}
          </Typography>
          <Typography variant="body2">
            <strong>Local DateTime:</strong> {formatLocalDateTime(utcString)}
          </Typography>
          <Typography variant="body2">
            <strong>Local Date:</strong> {formatLocalDate(utcString)}
          </Typography>
          <Typography variant="body2">
            <strong>Local Time:</strong> {formatLocalTime(utcString)}
          </Typography>
        </Paper>
      ))}

      <Paper sx={{ p: 2, mt: 3, bgcolor: 'info.light' }}>
        <Typography variant="subtitle2" color="info.contrastText">
          Browser Info:
        </Typography>
        <Typography variant="body2" color="info.contrastText">
          <strong>Timezone:</strong> {Intl.DateTimeFormat().resolvedOptions().timeZone}
        </Typography>
        <Typography variant="body2" color="info.contrastText">
          <strong>Locale:</strong> {Intl.DateTimeFormat().resolvedOptions().locale}
        </Typography>
        <Typography variant="body2" color="info.contrastText">
          <strong>Current Local Time:</strong> {new Date().toLocaleString()}
        </Typography>
        <Typography variant="body2" color="info.contrastText">
          <strong>Current UTC Time:</strong> {new Date().toISOString()}
        </Typography>
      </Paper>
    </Box>
  );
};

export default TimezoneTest;