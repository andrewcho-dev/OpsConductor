/**
 * Alert Demo Component
 * Demonstrates the new alert system functionality
 */
import React from 'react';
import { Button, Box, Typography } from '@mui/material';
import { useAlert } from '../layout/BottomStatusBar';

const AlertDemo = () => {
  const { addAlert } = useAlert();

  const showSuccessAlert = () => {
    addAlert('Operation completed successfully!', 'success', 3000);
  };

  const showWarningAlert = () => {
    addAlert('This is a warning message that will auto-dismiss', 'warning', 4000);
  };

  const showErrorAlert = () => {
    addAlert('This is an error message that stays until dismissed', 'error', 0);
  };

  const showInfoAlert = () => {
    addAlert('This is an informational message', 'info', 5000);
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Alert System Demo
      </Typography>
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        <Button 
          variant="contained" 
          color="success" 
          onClick={showSuccessAlert}
          size="small"
        >
          Success Alert
        </Button>
        <Button 
          variant="contained" 
          color="warning" 
          onClick={showWarningAlert}
          size="small"
        >
          Warning Alert
        </Button>
        <Button 
          variant="contained" 
          color="error" 
          onClick={showErrorAlert}
          size="small"
        >
          Error Alert
        </Button>
        <Button 
          variant="contained" 
          color="info" 
          onClick={showInfoAlert}
          size="small"
        >
          Info Alert
        </Button>
      </Box>
      <Typography variant="caption" sx={{ mt: 2, display: 'block', color: 'text.secondary' }}>
        Click the buttons above to test the alert system. Check the bottom status bar for alerts.
      </Typography>
    </Box>
  );
};

export default AlertDemo;