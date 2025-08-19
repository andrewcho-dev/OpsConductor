import React from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Button, 
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider
} from '@mui/material';
import { Link } from 'react-router-dom';
import BugReportIcon from '@mui/icons-material/BugReport';
import ScheduleIcon from '@mui/icons-material/Schedule';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import HomeIcon from '@mui/icons-material/Home';

/**
 * Debug tools navigation component
 */
const DebugTools = () => {
  const tools = [
    {
      name: 'Direct Schedule Creator',
      description: 'Create recurring schedules directly with the API',
      path: '/direct-schedule',
      icon: <ScheduleIcon />
    },
    {
      name: 'Session Timeout Test',
      description: 'Test and debug session timeout functionality (requires auth)',
      path: '/session-test',
      icon: <AccessTimeIcon />
    },
    {
      name: 'Standalone Session Test',
      description: 'Test session timeout with no server dependencies (works without login)',
      path: '/standalone-session',
      icon: <AccessTimeIcon />
    }
  ];

  return (
    <Paper sx={{ p: 3, maxWidth: 800, mx: 'auto', mt: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <BugReportIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h5">Debug Tools</Typography>
      </Box>
      
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        These tools help diagnose and fix issues with the application.
      </Typography>
      
      <List>
        {tools.map((tool, index) => (
          <React.Fragment key={tool.path}>
            {index > 0 && <Divider component="li" />}
            <ListItem 
              button 
              component={Link} 
              to={tool.path}
              sx={{ 
                py: 2,
                '&:hover': {
                  bgcolor: 'action.hover',
                }
              }}
            >
              <ListItemIcon>
                {tool.icon}
              </ListItemIcon>
              <ListItemText 
                primary={tool.name} 
                secondary={tool.description}
                primaryTypographyProps={{
                  fontWeight: 'medium'
                }}
              />
            </ListItem>
          </React.Fragment>
        ))}
      </List>
      
      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
        <Button 
          component={Link} 
          to="/" 
          startIcon={<HomeIcon />}
          variant="outlined"
        >
          Return to Dashboard
        </Button>
      </Box>
    </Paper>
  );
};

export default DebugTools;