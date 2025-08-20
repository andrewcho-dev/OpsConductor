import React, { useState, useEffect } from 'react';
import {
  Box, Typography, LinearProgress, Alert, List, ListItem, ListItemIcon,
  ListItemText, Chip, Paper
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Info as InfoIcon
} from '@mui/icons-material';

import { enhancedUserService } from '../../services/enhancedUserService';

const PasswordPolicyValidator = ({ password, onValidationChange }) => {
  const [validation, setValidation] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (password && password.length > 0) {
      validatePassword(password);
    } else {
      setValidation(null);
      if (onValidationChange) {
        onValidationChange({ valid: false, score: 0 });
      }
    }
  }, [password]);

  const validatePassword = async (pwd) => {
    setLoading(true);
    try {
      const result = await enhancedUserService.validatePassword(pwd);
      setValidation(result);
      if (onValidationChange) {
        onValidationChange(result);
      }
    } catch (error) {
      console.error('Password validation failed:', error);
      setValidation({
        valid: false,
        score: 0,
        strength: 'unknown',
        violations: ['Unable to validate password'],
        suggestions: []
      });
    } finally {
      setLoading(false);
    }
  };

  const getStrengthColor = (strength) => {
    switch (strength) {
      case 'very_weak': return 'error';
      case 'weak': return 'error';
      case 'fair': return 'warning';
      case 'good': return 'info';
      case 'strong': return 'success';
      default: return 'default';
    }
  };

  const getStrengthLabel = (strength) => {
    switch (strength) {
      case 'very_weak': return 'Very Weak';
      case 'weak': return 'Weak';
      case 'fair': return 'Fair';
      case 'good': return 'Good';
      case 'strong': return 'Strong';
      default: return 'Unknown';
    }
  };

  if (!password || password.length === 0) {
    return null;
  }

  if (loading) {
    return (
      <Box sx={{ mt: 1 }}>
        <Typography variant="body2" color="text.secondary">
          Validating password...
        </Typography>
        <LinearProgress size="small" sx={{ mt: 0.5 }} />
      </Box>
    );
  }

  if (!validation) {
    return null;
  }

  return (
    <Paper variant="outlined" sx={{ p: 2, mt: 1 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <Typography variant="subtitle2">Password Strength:</Typography>
        <Chip
          label={getStrengthLabel(validation.strength)}
          color={getStrengthColor(validation.strength)}
          size="small"
        />
        <Box sx={{ flexGrow: 1, mx: 1 }}>
          <LinearProgress
            variant="determinate"
            value={validation.score}
            color={getStrengthColor(validation.strength)}
            sx={{ height: 6, borderRadius: 3 }}
          />
        </Box>
        <Typography variant="body2" color="text.secondary">
          {validation.score}%
        </Typography>
      </Box>

      {validation.violations && validation.violations.length > 0 && (
        <Alert severity="error" sx={{ mb: 1 }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Policy Violations:
          </Typography>
          <List dense>
            {validation.violations.map((violation, index) => (
              <ListItem key={index} sx={{ py: 0 }}>
                <ListItemIcon sx={{ minWidth: 32 }}>
                  <CancelIcon color="error" fontSize="small" />
                </ListItemIcon>
                <ListItemText
                  primary={violation}
                  primaryTypographyProps={{ variant: 'body2' }}
                />
              </ListItem>
            ))}
          </List>
        </Alert>
      )}

      {validation.requirements && validation.requirements.length > 0 && (
        <Box sx={{ mb: 1 }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Requirements:
          </Typography>
          <List dense>
            {validation.requirements.map((req, index) => (
              <ListItem key={index} sx={{ py: 0 }}>
                <ListItemIcon sx={{ minWidth: 32 }}>
                  {req.met ? (
                    <CheckCircleIcon color="success" fontSize="small" />
                  ) : (
                    <CancelIcon color="error" fontSize="small" />
                  )}
                </ListItemIcon>
                <ListItemText
                  primary={req.description}
                  primaryTypographyProps={{
                    variant: 'body2',
                    color: req.met ? 'text.primary' : 'error.main'
                  }}
                />
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      {validation.suggestions && validation.suggestions.length > 0 && (
        <Alert severity="info" sx={{ mt: 1 }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Suggestions:
          </Typography>
          <List dense>
            {validation.suggestions.map((suggestion, index) => (
              <ListItem key={index} sx={{ py: 0 }}>
                <ListItemIcon sx={{ minWidth: 32 }}>
                  <InfoIcon color="info" fontSize="small" />
                </ListItemIcon>
                <ListItemText
                  primary={suggestion}
                  primaryTypographyProps={{ variant: 'body2' }}
                />
              </ListItem>
            ))}
          </List>
        </Alert>
      )}

      {validation.valid && (
        <Alert severity="success" sx={{ mt: 1 }}>
          <Typography variant="body2">
            ✓ Password meets all policy requirements
          </Typography>
        </Alert>
      )}
    </Paper>
  );
};

export default PasswordPolicyValidator;