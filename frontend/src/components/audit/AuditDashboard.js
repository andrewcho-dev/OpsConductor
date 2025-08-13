import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  Security as SecurityIcon,
  Search as SearchIcon,
  Download as DownloadIcon,
  Verified as VerifiedIcon
} from '@mui/icons-material';
import '../../styles/dashboard.css';

function AuditDashboard() {
  const [tabValue, setTabValue] = useState(0);
  const [events, setEvents] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [eventTypes, setEventTypes] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [verificationResult, setVerificationResult] = useState(null);

  const fetchAuditData = async () => {
    try {
      setLoading(true);
      
      // Fetch recent events
      const eventsResponse = await fetch('/api/v1/audit/events', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (eventsResponse.ok) {
        const eventsData = await eventsResponse.json();
        setEvents(eventsData.events || []);
      }

      // Fetch statistics
      const statsResponse = await fetch('/api/v1/audit/statistics', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStatistics(statsData);
      }

      // Fetch event types
      const typesResponse = await fetch('/api/v1/audit/event-types', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (typesResponse.ok) {
        const typesData = await typesResponse.json();
        setEventTypes(typesData.event_types || []);
      }
    } catch (error) {
      console.error('Failed to fetch audit data:', error);
    } finally {
      setLoading(false);
    }
  };

  const searchEvents = async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams();
      if (searchQuery) params.append('query', searchQuery);
      if (eventTypeFilter) params.append('event_type', eventTypeFilter);
      if (severityFilter) params.append('severity', severityFilter);
      
      const response = await fetch(`/api/v1/audit/search?${params}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: searchQuery,
          event_types: eventTypeFilter ? [eventTypeFilter] : null,
          limit: 100
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setEvents(data.events || []);
      }
    } catch (error) {
      console.error('Failed to search audit events:', error);
    } finally {
      setLoading(false);
    }
  };

  const verifyEvent = async (eventId) => {
    try {
      const response = await fetch(`/api/v1/audit/verify/${eventId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        setVerificationResult(result);
      }
    } catch (error) {
      console.error('Failed to verify event:', error);
    }
  };

  const generateComplianceReport = async () => {
    try {
      const response = await fetch('/api/v1/audit/compliance/report', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (response.ok) {
        const report = await response.json();
        // Download report as JSON
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `compliance-report-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Failed to generate compliance report:', error);
    }
  };

  useEffect(() => {
    fetchAuditData();
  }, []);

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const AuditOverview = () => (
    <Grid container spacing={3}>
      {/* Statistics Cards */}
      {statistics && (
        <>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="primary">Total Events</Typography>
                <Typography variant="h3">{statistics.total_events}</Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={9}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Event Type Distribution</Typography>
                <Grid container spacing={2}>
                  {Object.entries(statistics.event_type_distribution || {}).map(([type, count]) => (
                    <Grid item key={type}>
                      <Chip label={`${type}: ${count}`} variant="outlined" />
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </>
      )}

      {/* Recent Events */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Recent Audit Events</Typography>
              <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                onClick={generateComplianceReport}
              >
                Compliance Report
              </Button>
            </Box>
            
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Timestamp</TableCell>
                    <TableCell>Event Type</TableCell>
                    <TableCell>User</TableCell>
                    <TableCell>Resource</TableCell>
                    <TableCell>Severity</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {events.slice(0, 10).map((event, index) => (
                    <TableRow key={index}>
                      <TableCell>{formatTimestamp(event.timestamp)}</TableCell>
                      <TableCell>{event.event_type}</TableCell>
                      <TableCell>{event.user_id || 'System'}</TableCell>
                      <TableCell>{event.resource_type}:{event.resource_id}</TableCell>
                      <TableCell>
                        <Chip 
                          label={event.severity} 
                          color={getSeverityColor(event.severity)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          startIcon={<VerifiedIcon />}
                          onClick={() => {
                            setSelectedEvent(event);
                            verifyEvent(event.id);
                          }}
                        >
                          Verify
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const AuditSearch = () => (
    <Grid container spacing={3}>
      {/* Search Controls */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Search Audit Events</Typography>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Search Query"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Enter search terms..."
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Event Type</InputLabel>
                  <Select
                    value={eventTypeFilter}
                    onChange={(e) => setEventTypeFilter(e.target.value)}
                  >
                    <MenuItem value="">All Types</MenuItem>
                    {eventTypes.map((type) => (
                      <MenuItem key={type.value} value={type.value}>
                        {type.description}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Severity</InputLabel>
                  <Select
                    value={severityFilter}
                    onChange={(e) => setSeverityFilter(e.target.value)}
                  >
                    <MenuItem value="">All Severities</MenuItem>
                    <MenuItem value="low">Low</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                    <MenuItem value="critical">Critical</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={2}>
                <Button
                  fullWidth
                  variant="contained"
                  startIcon={<SearchIcon />}
                  onClick={searchEvents}
                  disabled={loading}
                >
                  Search
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>

      {/* Search Results */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Search Results ({events.length})</Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Timestamp</TableCell>
                    <TableCell>Event Type</TableCell>
                    <TableCell>Action</TableCell>
                    <TableCell>User</TableCell>
                    <TableCell>Resource</TableCell>
                    <TableCell>Severity</TableCell>
                    <TableCell>Details</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {events.map((event, index) => (
                    <TableRow key={index}>
                      <TableCell>{formatTimestamp(event.timestamp)}</TableCell>
                      <TableCell>{event.event_type}</TableCell>
                      <TableCell>{event.action}</TableCell>
                      <TableCell>{event.user_id || 'System'}</TableCell>
                      <TableCell>{event.resource_type}:{event.resource_id}</TableCell>
                      <TableCell>
                        <Chip 
                          label={event.severity} 
                          color={getSeverityColor(event.severity)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          onClick={() => setSelectedEvent(event)}
                        >
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  return (
    <div className="dashboard-container">
      {/* Page Header */}
      <div className="page-header">
        <Typography className="page-title">
          Audit & Compliance
        </Typography>
        <div className="page-actions">
          <Button
            variant="outlined"
            size="small"
            startIcon={<SecurityIcon />}
            onClick={fetchAuditData}
            disabled={loading}
          >
            Refresh
          </Button>
        </div>
      </div>

      <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
        <Tab label="Overview" />
        <Tab label="Search Events" />
      </Tabs>

      {tabValue === 0 && <AuditOverview />}
      {tabValue === 1 && <AuditSearch />}

      {/* Event Details Dialog */}
      <Dialog
        open={!!selectedEvent}
        onClose={() => setSelectedEvent(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Event Details</DialogTitle>
        <DialogContent>
          {selectedEvent && (
            <Box>
              <Typography variant="h6" gutterBottom>Event Information</Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">Event ID</Typography>
                  <Typography>{selectedEvent.id}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">Timestamp</Typography>
                  <Typography>{formatTimestamp(selectedEvent.timestamp)}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">Event Type</Typography>
                  <Typography>{selectedEvent.event_type}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">Severity</Typography>
                  <Chip 
                    label={selectedEvent.severity} 
                    color={getSeverityColor(selectedEvent.severity)}
                    size="small"
                  />
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary">Details</Typography>
                  <pre style={{ fontSize: '12px', overflow: 'auto' }}>
                    {JSON.stringify(selectedEvent.details, null, 2)}
                  </pre>
                </Grid>
              </Grid>

              {verificationResult && (
                <Box mt={2}>
                  <Typography variant="h6" gutterBottom>Integrity Verification</Typography>
                  <Alert severity={verificationResult.valid ? 'success' : 'error'}>
                    {verificationResult.valid ? 'Event integrity verified' : 'Event integrity check failed'}
                  </Alert>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedEvent(null)}>Close</Button>
        </DialogActions>
      </Dialog>
    </div>
  );
}

export default AuditDashboard;