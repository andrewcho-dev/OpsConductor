import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Typography, Button, IconButton, Tooltip, Box, Card, CardContent,
  Grid, Table, TableBody, TableCell, TableContainer, TableHead,
  TableRow, Paper, Chip, CircularProgress, Alert, Tabs, Tab,
  List, ListItem, ListItemIcon, ListItemText, Divider
} from '@mui/material';

// Icons
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import RefreshIcon from '@mui/icons-material/Refresh';
import PersonIcon from '@mui/icons-material/Person';
import LoginIcon from '@mui/icons-material/Login';
import LogoutIcon from '@mui/icons-material/Logout';
import SecurityIcon from '@mui/icons-material/Security';
import HistoryIcon from '@mui/icons-material/History';
import DevicesIcon from '@mui/icons-material/Devices';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';

import { enhancedUserService } from '../../services/enhancedUserService';
import '../../styles/dashboard.css';

const UserActivityDashboard = () => {
  const navigate = useNavigate();
  const { userId } = useParams();
  
  // State management
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState(null);
  const [activity, setActivity] = useState(null);
  const [currentTab, setCurrentTab] = useState(0);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (userId) {
      fetchUserData();
      fetchUserActivity();
    }
  }, [userId]);

  const fetchUserData = async () => {
    try {
      const userData = await enhancedUserService.getUserById(userId);
      setUser(userData);
    } catch (error) {
      console.error('Failed to fetch user data:', error);
      setError('Failed to load user information');
    }
  };

  const fetchUserActivity = async () => {
    setLoading(true);
    try {
      const activityData = await enhancedUserService.getUserActivity(userId, 100);
      setActivity(activityData);
      setError(null);
    } catch (error) {
      console.error('Failed to fetch user activity:', error);
      setError('Failed to load user activity');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getEventIcon = (eventType) => {
    switch (eventType) {
      case 'login': return <LoginIcon color="success" />;
      case 'logout': return <LogoutIcon color="action" />;
      case 'failed_login': return <ErrorIcon color="error" />;
      case 'password_change': return <SecurityIcon color="info" />;
      case 'account_locked': return <WarningIcon color="warning" />;
      case 'account_unlocked': return <CheckCircleIcon color="success" />;
      default: return <HistoryIcon color="action" />;
    }
  };

  const getEventColor = (eventType) => {
    switch (eventType) {
      case 'login': return 'success';
      case 'logout': return 'default';
      case 'failed_login': return 'error';
      case 'password_change': return 'info';
      case 'account_locked': return 'warning';
      case 'account_unlocked': return 'success';
      default: return 'default';
    }
  };

  const StatCard = ({ title, value, icon, color = 'primary', subtitle }) => (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box sx={{ color: `${color}.main` }}>
            {icon}
          </Box>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h4" component="div">
              {value}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {title}
            </Typography>
            {subtitle && (
              <Typography variant="caption" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  const TabPanel = ({ children, value, index, ...other }) => (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`activity-tabpanel-${index}`}
      aria-labelledby={`activity-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );

  if (error) {
    return (
      <div className="dashboard-container">
        <div className="page-header">
          <Typography className="page-title">User Activity</Typography>
          <div className="page-actions">
            <Tooltip title="Back to Users">
              <IconButton onClick={() => navigate('/users')} size="small">
                <ArrowBackIcon />
              </IconButton>
            </Tooltip>
          </div>
        </div>
        <Alert severity="error">{error}</Alert>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      {/* Page Header */}
      <div className="page-header">
        <Typography className="page-title">
          User Activity {user && `- ${user.username}`}
        </Typography>
        <div className="page-actions">
          <Tooltip title="Back to Users">
            <IconButton onClick={() => navigate('/users')} size="small">
              <ArrowBackIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Refresh Activity">
            <IconButton onClick={fetchUserActivity} disabled={loading} size="small">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </div>
      </div>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : activity ? (
        <>
          {/* User Info Card */}
          {user && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <PersonIcon sx={{ fontSize: 40, color: 'primary.main' }} />
                  <Box>
                    <Typography variant="h5">{user.username}</Typography>
                    <Typography variant="body1" color="text.secondary">
                      {user.email}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                      <Chip label={user.role?.name || user.role || 'No Role'} color="primary" size="small" />
                      <Chip 
                        label={user.is_active ? 'Active' : 'Inactive'} 
                        color={user.is_active ? 'success' : 'error'} 
                        size="small" 
                      />
                    </Box>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          )}

          {/* Activity Statistics */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Active Sessions"
                value={activity.active_sessions || 0}
                icon={<DevicesIcon />}
                color="success"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Failed Attempts"
                value={activity.failed_attempts || 0}
                icon={<ErrorIcon />}
                color="error"
                subtitle="Last 30 days"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Last Login"
                value={activity.last_login ? formatDate(activity.last_login) : 'Never'}
                icon={<AccessTimeIcon />}
                color="info"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Last IP"
                value={activity.last_login_ip || 'N/A'}
                icon={<LocationOnIcon />}
                color="default"
              />
            </Grid>
          </Grid>

          {/* Activity Tabs */}
          <Card>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={currentTab} onChange={(_, newValue) => setCurrentTab(newValue)}>
                <Tab icon={<HistoryIcon />} label="Recent Activity" />
                <Tab icon={<DevicesIcon />} label="Active Sessions" />
                <Tab icon={<SecurityIcon />} label="Security Events" />
              </Tabs>
            </Box>

            {/* Recent Activity Tab */}
            <TabPanel value={currentTab} index={0}>
              <Typography variant="h6" sx={{ mb: 2 }}>Recent Activity</Typography>
              {activity.recent_activity && activity.recent_activity.length > 0 ? (
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ backgroundColor: 'grey.100' }}>
                        <TableCell>Event</TableCell>
                        <TableCell>Description</TableCell>
                        <TableCell>IP Address</TableCell>
                        <TableCell>User Agent</TableCell>
                        <TableCell>Date</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {activity.recent_activity.map((event, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              {getEventIcon(event.event_type)}
                              <Chip
                                label={event.event_type.replace('_', ' ')}
                                color={getEventColor(event.event_type)}
                                size="small"
                              />
                            </Box>
                          </TableCell>
                          <TableCell>{event.event_description}</TableCell>
                          <TableCell>{event.ip_address || 'N/A'}</TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                              {event.user_agent || 'N/A'}
                            </Typography>
                          </TableCell>
                          <TableCell>{formatDate(event.created_at)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Alert severity="info">No recent activity found</Alert>
              )}
            </TabPanel>

            {/* Active Sessions Tab */}
            <TabPanel value={currentTab} index={1}>
              <Typography variant="h6" sx={{ mb: 2 }}>Active Sessions</Typography>
              {activity.active_sessions_details && activity.active_sessions_details.length > 0 ? (
                <Grid container spacing={2}>
                  {activity.active_sessions_details.map((session, index) => (
                    <Grid item xs={12} md={6} key={index}>
                      <Card variant="outlined">
                        <CardContent>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                            <DevicesIcon color="primary" />
                            <Typography variant="h6">Session {index + 1}</Typography>
                            <Chip label="Active" color="success" size="small" />
                          </Box>
                          <List dense>
                            <ListItem>
                              <ListItemIcon><LocationOnIcon /></ListItemIcon>
                              <ListItemText 
                                primary="IP Address" 
                                secondary={session.ip_address || 'Unknown'} 
                              />
                            </ListItem>
                            <ListItem>
                              <ListItemIcon><AccessTimeIcon /></ListItemIcon>
                              <ListItemText 
                                primary="Started" 
                                secondary={formatDate(session.created_at)} 
                              />
                            </ListItem>
                            <ListItem>
                              <ListItemIcon><HistoryIcon /></ListItemIcon>
                              <ListItemText 
                                primary="Last Activity" 
                                secondary={formatDate(session.last_activity)} 
                              />
                            </ListItem>
                          </List>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              ) : (
                <Alert severity="info">No active sessions found</Alert>
              )}
            </TabPanel>

            {/* Security Events Tab */}
            <TabPanel value={currentTab} index={2}>
              <Typography variant="h6" sx={{ mb: 2 }}>Security Events</Typography>
              {activity.security_events && activity.security_events.length > 0 ? (
                <List>
                  {activity.security_events.map((event, index) => (
                    <React.Fragment key={index}>
                      <ListItem>
                        <ListItemIcon>
                          {getEventIcon(event.event_type)}
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="body1">{event.event_description}</Typography>
                              <Chip
                                label={event.event_type.replace('_', ' ')}
                                color={getEventColor(event.event_type)}
                                size="small"
                              />
                            </Box>
                          }
                          secondary={
                            <Box>
                              <Typography variant="body2" color="text.secondary">
                                {formatDate(event.created_at)}
                              </Typography>
                              {event.ip_address && (
                                <Typography variant="body2" color="text.secondary">
                                  IP: {event.ip_address}
                                </Typography>
                              )}
                            </Box>
                          }
                        />
                      </ListItem>
                      {index < activity.security_events.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              ) : (
                <Alert severity="info">No security events found</Alert>
              )}
            </TabPanel>
          </Card>
        </>
      ) : (
        <Alert severity="info">No activity data available</Alert>
      )}
    </div>
  );
};

export default UserActivityDashboard;