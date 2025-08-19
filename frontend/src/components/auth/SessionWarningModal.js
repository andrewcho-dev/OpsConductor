import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  LinearProgress,
  Alert,
  IconButton
} from '@mui/material';
import {
  Warning as WarningIcon,
  AccessTime as TimeIcon,
  Close as CloseIcon
} from '@mui/icons-material';

const SessionWarningModal = ({ 
  open, 
  timeRemaining, 
  onExtend, 
  onLogout, 
  onClose 
}) => {
  const [countdown, setCountdown] = useState(timeRemaining);
  const [extending, setExtending] = useState(false);

  useEffect(() => {
    // timeRemaining is already in seconds from the session service
    console.log(`Modal received timeRemaining: ${timeRemaining} seconds`);
    setCountdown(timeRemaining);
  }, [timeRemaining]);

  useEffect(() => {
    if (!open || countdown <= 0) return;

    const timer = setInterval(() => {
      setCountdown(prev => {
        const newValue = prev - 1;
        if (newValue <= 0) {
          clearInterval(timer);
          onLogout();
        }
        return newValue;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [open, countdown, onLogout]);

  const handleExtend = async () => {
    setExtending(true);
    try {
      const success = await onExtend();
      if (success) {
        onClose();
      }
    } catch (error) {
      console.error('Failed to extend session:', error);
    } finally {
      setExtending(false);
    }
  };

  const formatTime = (seconds) => {
    // Make sure we have a valid number
    const validSeconds = Math.max(0, Math.round(seconds));
    
    const mins = Math.floor(validSeconds / 60);
    const secs = validSeconds % 60;
    
    // Format as MM:SS
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const progressValue = (countdown / timeRemaining) * 100;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      disableEscapeKeyDown
      PaperProps={{
        sx: {
          borderRadius: 2,
          border: '2px solid #ff9800',
        }
      }}
    >
      <DialogTitle sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: 1,
        backgroundColor: '#fff3e0',
        color: '#e65100',
        position: 'relative'
      }}>
        <WarningIcon />
        <Typography variant="h6" component="span" sx={{ fontWeight: 600 }}>
          Session Timeout Warning
        </Typography>
        <IconButton
          onClick={onClose}
          sx={{
            position: 'absolute',
            right: 8,
            top: 8,
            color: '#e65100',
          }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ pt: 3 }}>
        <Alert 
          severity="warning" 
          sx={{ mb: 3 }}
          icon={<TimeIcon />}
        >
          Your session will expire due to inactivity
        </Alert>

        <Box sx={{ textAlign: 'center', mb: 3 }}>
          <Typography variant="h4" sx={{ 
            fontWeight: 'bold', 
            color: countdown <= 30 ? '#d32f2f' : '#ff9800',
            fontFamily: 'monospace'
          }}>
            {formatTime(countdown)}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Time remaining until automatic logout
          </Typography>
        </Box>

        <Box sx={{ mb: 3 }}>
          <LinearProgress 
            variant="determinate" 
            value={progressValue}
            sx={{
              height: 8,
              borderRadius: 4,
              backgroundColor: '#ffecb3',
              '& .MuiLinearProgress-bar': {
                backgroundColor: countdown <= 30 ? '#d32f2f' : '#ff9800',
                borderRadius: 4,
              }
            }}
          />
        </Box>

        <Typography variant="body1" sx={{ mb: 2 }}>
          You've been inactive for a while. To continue your session:
        </Typography>

        <Box component="ul" sx={{ pl: 2, mb: 2 }}>
          <Typography component="li" variant="body2" sx={{ mb: 1 }}>
            Click "Stay Logged In" to extend your session
          </Typography>
          <Typography component="li" variant="body2" sx={{ mb: 1 }}>
            Move your mouse or press any key to reset the timer
          </Typography>
          <Typography component="li" variant="body2">
            Or click "Logout" to end your session safely
          </Typography>
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 3, gap: 1 }}>
        <Button
          onClick={onLogout}
          variant="outlined"
          color="error"
          disabled={extending}
        >
          Logout Now
        </Button>
        <Button
          onClick={handleExtend}
          variant="contained"
          color="warning"
          disabled={extending}
          sx={{
            minWidth: 140,
            backgroundColor: '#ff9800',
            '&:hover': {
              backgroundColor: '#f57c00',
            }
          }}
        >
          {extending ? 'Extending...' : 'Stay Logged In'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SessionWarningModal;