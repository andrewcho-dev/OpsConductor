import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Pagination
} from '@mui/material';
import {
  Search as SearchIcon,
  Save as SaveIcon
} from '@mui/icons-material';

import { ViewDetailsAction, CloseAction, DownloadAction, RefreshAction } from '../common/StandardActions';
import { getSeverityRowStyling, getTableCellStyle } from '../../utils/tableUtils';
import { useTheme } from '@mui/material/styles';
import auditService from '../../services/auditService';
import '../../styles/dashboard.css';

function AuditDashboard() {
  const theme = useTheme();
  const [events, setEvents] = useState([]);
  const [enrichedEvents, setEnrichedEvents] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [enriching, setEnriching] = useState(false);
  const [error, setError] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [eventTypes, setEventTypes] = useState([]);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(100);
  
  // Filter state
  const [columnFilters, setColumnFilters] = useState({});
  
  // Sort state
  const [sortField, setSortField] = useState('timestamp');
  const [sortDirection, setSortDirection] = useState('desc');

  // Fetch audit data
  const fetchAuditData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch events with pagination
      const eventsResponse = await fetch(`/api/v1/audit/events?page=${currentPage}&limit=${pageSize}&sort=${sortField}&order=${sortDirection}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (eventsResponse.ok) {
        const eventsData = await eventsResponse.json();
        
        const rawEvents = eventsData.events || [];
        setEvents(rawEvents);
        setTotalCount(eventsData.total || rawEvents.length || 0);

        // Start enrichment process
        if (rawEvents.length > 0) {
          setEnriching(true);
          try {
            const enriched = await auditService.enrichAuditEvents(rawEvents);
            setEnrichedEvents(enriched);
          } catch (enrichError) {
            console.error('Enrichment failed:', enrichError);
            setEnrichedEvents(rawEvents); // Fallback to raw events
          } finally {
            setEnriching(false);
          }
        } else {
          setEnrichedEvents([]);
          setEnriching(false);
        }
      } else {
        throw new Error(`Failed to fetch events: ${eventsResponse.statusText}`);
      }

      // Fetch event types for filtering
      const typesResponse = await fetch('/api/v1/audit/event-types', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (typesResponse.ok) {
        const typesData = await typesResponse.json();
        const eventTypesArray = typesData.event_types || [];
        setEventTypes(eventTypesArray);
      }
    } catch (error) {
      console.error('Failed to fetch audit data:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditData();
  }, [currentPage, pageSize, sortField, sortDirection]);

  // Handle column filters
  const handleColumnFilterChange = (columnKey, value) => {
    setColumnFilters(prev => ({
      ...prev,
      [columnKey]: value
    }));
    // Reset to first page when filters change
    setCurrentPage(1);
  };

  // Handle sort change
  const handleSortChange = (field, direction) => {
    setSortField(field);
    setSortDirection(direction);
    setCurrentPage(1); // Reset to first page when sorting changes
  };

  // Handle export
  const handleExport = async (format) => {
    try {
      const response = await fetch(`/api/v1/audit/export?format=${format}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `audit_events.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        throw new Error(`Export failed: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Export failed:', error);
      setError(`Export failed: ${error.message}`);
    }
  };

  // Format timestamp
  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  // Generate 200 sample events for testing
  const generateSampleEvents = () => {
    const eventTypes = [
      'user_login', 'user_logout', 'user_created', 'user_updated', 'user_deleted',
      'target_created', 'target_updated', 'target_deleted', 'target_connection_test',
      'job_created', 'job_updated', 'job_deleted', 'job_executed', 'bulk_operation'
    ];
    
    const severities = ['low', 'medium', 'high', 'critical'];
    
    const users = [
      'John Doe', 'Jane Smith', 'Admin User', 'Bob Johnson', 'Alice Brown',
      'Charlie Wilson', 'Diana Prince', 'Edward Norton', 'Fiona Green', 'George Miller',
      'Helen Davis', 'Ivan Petrov', 'Julia Roberts', 'Kevin Hart', 'Linda Johnson',
      'Michael Scott', 'Nancy Drew', 'Oscar Wilde', 'Patricia Moore', 'Quincy Jones',
      'Rachel Green', 'Steve Jobs', 'Tina Turner', 'Ulysses Grant', 'Victoria Beckham',
      'William Shakespeare', 'Xena Warrior', 'Yoda Master', 'Zoe Saldana'
    ];
    
    const resources = [
      'Production Server', 'Development Environment', 'Database Cluster', 'Web Application',
      'API Gateway', 'Load Balancer', 'File Server', 'Backup System', 'Monitoring Dashboard',
      'User Account', 'Admin Panel', 'Configuration File', 'Security Policy', 'Network Device',
      'Docker Container', 'Kubernetes Pod', 'CI/CD Pipeline', 'Test Environment', 'Staging Server',
      'Mail Server', 'DNS Server', 'Firewall Rules', 'SSL Certificate', 'Authentication Service',
      'Payment Gateway', 'Analytics Platform', 'Content Management', 'Mobile App', 'Desktop Client'
    ];
    
    const actions = {
      'user_login': ['login', 'authenticate', 'sign_in'],
      'user_logout': ['logout', 'sign_out', 'session_end'],
      'user_created': ['create', 'register', 'add_user'],
      'user_updated': ['update', 'modify', 'edit_profile'],
      'user_deleted': ['delete', 'remove', 'deactivate'],
      'target_created': ['create', 'provision', 'deploy'],
      'target_updated': ['update', 'configure', 'modify'],
      'target_deleted': ['delete', 'destroy', 'remove'],
      'target_connection_test': ['test', 'ping', 'verify_connection'],
      'job_created': ['create', 'schedule', 'define'],
      'job_updated': ['update', 'reschedule', 'modify'],
      'job_deleted': ['delete', 'cancel', 'remove'],
      'job_executed': ['execute', 'run', 'process'],
      'bulk_operation': ['bulk_import', 'mass_update', 'batch_process']
    };
    
    const events = [];
    const now = Date.now();
    
    for (let i = 0; i < 200; i++) {
      const eventType = eventTypes[Math.floor(Math.random() * eventTypes.length)];
      const severity = severities[Math.floor(Math.random() * severities.length)];
      const user = users[Math.floor(Math.random() * users.length)];
      const resource = resources[Math.floor(Math.random() * resources.length)];
      const action = actions[eventType][Math.floor(Math.random() * actions[eventType].length)];
      
      // Generate timestamps spread over the last 30 days
      const daysAgo = Math.floor(Math.random() * 30);
      const hoursAgo = Math.floor(Math.random() * 24);
      const minutesAgo = Math.floor(Math.random() * 60);
      const timestamp = new Date(now - (daysAgo * 24 * 60 * 60 * 1000) - (hoursAgo * 60 * 60 * 1000) - (minutesAgo * 60 * 1000));
      
      events.push({
        id: `sample-${i + 1}`,
        timestamp: timestamp.toISOString(),
        event_type: eventType,
        action: action,
        user_display_name: user,
        resource_display_name: resource,
        severity: severity,
        details: {
          ip_address: `192.168.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
          user_agent: Math.random() > 0.5 ? 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
          session_id: `sess_${Math.random().toString(36).substr(2, 9)}`,
          duration_ms: Math.floor(Math.random() * 5000) + 100
        }
      });
    }
    
    // Sort by timestamp (newest first)
    return events.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  };

  const sampleEvents = generateSampleEvents();

  // Use sample data if no real data is available (for testing)
  // TEMPORARY: Always use sample data for testing
  const eventsToDisplay = sampleEvents;

  // Debug: Log key information
  console.log('Sample Events Generated:', sampleEvents.length);
  console.log('Events To Display:', eventsToDisplay.length);

  // Filter and sort events based on column filters
  const filteredAndSortedEvents = eventsToDisplay
    .filter(event => {
      return Object.entries(columnFilters).every(([key, filterValue]) => {
        if (!filterValue) return true;
        
        switch (key) {
          case 'timestamp_start':
            if (!filterValue) return true;
            const eventDate = new Date(event.timestamp);
            const startDate = new Date(filterValue);
            return !isNaN(startDate.getTime()) && eventDate >= startDate;
          case 'timestamp_end':
            if (!filterValue) return true;
            const eventDateEnd = new Date(event.timestamp);
            const endDate = new Date(filterValue);
            return !isNaN(endDate.getTime()) && eventDateEnd <= endDate;
          case 'event_type':
            return !filterValue || event.event_type === filterValue;
          case 'action':
            return !filterValue || event.action.toLowerCase().includes(filterValue.toLowerCase());
          case 'user_id':
            return !filterValue || (event.user_display_name && event.user_display_name.toLowerCase().includes(filterValue.toLowerCase()));
          case 'resource':
            return !filterValue || (event.resource_display_name && event.resource_display_name.toLowerCase().includes(filterValue.toLowerCase()));
          case 'severity':
            return !filterValue || event.severity === filterValue;
          default:
            return true;
        }
      });
    })
    .sort((a, b) => {
      if (!sortField) return 0;
      
      let aValue = a[sortField];
      let bValue = b[sortField];
      
      // Handle timestamp sorting
      if (sortField === 'timestamp') {
        aValue = new Date(aValue);
        bValue = new Date(bValue);
      }
      
      // Handle string sorting
      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }
      
      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

  // Calculate pagination
  const totalFilteredRecords = filteredAndSortedEvents.length;
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const paginatedEvents = filteredAndSortedEvents.slice(startIndex, endIndex);
  const totalPages = Math.ceil(totalFilteredRecords / pageSize);

  // Debug pagination
  console.log('Pagination:', { 
    currentPage, 
    pageSize, 
    totalFilteredRecords, 
    totalPages, 
    startIndex, 
    endIndex, 
    paginatedEventsLength: paginatedEvents.length 
  });

  // TEMPORARY: Skip loading and error screens to show sample data
  // if (loading && events.length === 0) {
  //   return (
  //     <div className="dashboard-container">
  //       <Typography>Loading audit data...</Typography>
  //     </div>
  //   );
  // }

  // if (error) {
  //   return (
  //     <div className="dashboard-container">
  //       <Alert severity="error" sx={{ mb: 2 }}>
  //         {error}
  //       </Alert>
  //     </div>
  //   );
  // }

  return (
    <div className="dashboard-container" style={{ 
      height: 'calc(100vh - 92px)', // Account for header (64px) + footer (28px)
      minHeight: 'calc(100vh - 92px)', 
      maxHeight: 'calc(100vh - 92px)', 
      overflow: 'hidden', 
      display: 'flex', 
      flexDirection: 'column',
      padding: '12px'
    }}>


      {/* Page Header */}
      <div className="page-header">
        <Typography className="page-title">
          Audit & Compliance
        </Typography>
        <div className="page-actions">
          {/* Record Count */}
          <Typography 
            variant="body2" 
            color="textSecondary" 
            sx={{ 
              marginRight: 2,
              fontSize: '0.875rem',
              fontWeight: 500
            }}
          >
            {paginatedEvents.length} of {totalFilteredRecords} records {totalFilteredRecords > pageSize ? `(Page ${currentPage} of ${totalPages})` : ''}
            {enriching && <span style={{ marginLeft: '8px', color: '#1976d2' }}>• Enriching...</span>}
            <span style={{ marginLeft: '8px', color: '#ff9800' }}>• Sample Data (200 events)</span>
          </Typography>
          
          {/* Export/Save Actions */}
          <DownloadAction 
            onClick={() => handleExport('csv')} 
            disabled={loading || filteredAndSortedEvents.length === 0}
            title="Export to CSV"
          />
          <IconButton
            size="small"
            onClick={() => handleExport('json')}
            disabled={loading || filteredAndSortedEvents.length === 0}
            title="Export to JSON"
            sx={{ 
              marginRight: 1,
              color: 'primary.main',
              '&:hover': { backgroundColor: 'primary.light' }
            }}
          >
            <SaveIcon sx={{ fontSize: 18 }} />
          </IconButton>
          
          <RefreshAction onClick={fetchAuditData} disabled={loading} />
        </div>
      </div>

      {/* Audit Events Table */}
      <Box sx={{ 
        mt: 2, 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'column',
        minHeight: 0 // Important for flex child to shrink
      }}>

        <TableContainer 
          component={Paper} 
          variant="outlined"
          sx={{ 
            flex: 1, // Take up remaining space in flex container
            minHeight: '400px',
            overflow: 'auto', // Only the table scrolls, not the page
            border: '1px solid', 
            borderColor: 'divider',
            borderRadius: 1
          }}
        >
          <Table size="small">
            <TableHead>
              {/* Column Headers */}
              <TableRow sx={{ backgroundColor: 'grey.100' }}>
                <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                  Timestamp
                </TableCell>
                <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                  Event Type
                </TableCell>
                <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                  Action
                </TableCell>
                <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                  User
                </TableCell>
                <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                  Resource
                </TableCell>
                <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                  Severity
                </TableCell>
                <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                  Actions
                </TableCell>
              </TableRow>
              
              {/* Filter Row */}
              <TableRow sx={{ backgroundColor: 'grey.50' }}>
                <TableCell sx={{ padding: '4px 8px' }}>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    <TextField
                      size="small"
                      fullWidth
                      type="datetime-local"
                      value={columnFilters.timestamp_start || ''}
                      onChange={(e) => handleColumnFilterChange('timestamp_start', e.target.value)}
                      sx={{ '& .MuiInputBase-input': { fontSize: '0.75rem', padding: '2px 4px' } }}
                    />
                    <TextField
                      size="small"
                      fullWidth
                      type="datetime-local"
                      value={columnFilters.timestamp_end || ''}
                      onChange={(e) => handleColumnFilterChange('timestamp_end', e.target.value)}
                      sx={{ '& .MuiInputBase-input': { fontSize: '0.75rem', padding: '2px 4px' } }}
                    />
                  </Box>
                </TableCell>
                <TableCell sx={{ padding: '4px 8px' }}>
                  <Select
                    size="small"
                    fullWidth
                    value={columnFilters.event_type || ''}
                    onChange={(e) => handleColumnFilterChange('event_type', e.target.value)}
                    sx={{ 
                      '& .MuiSelect-select': { 
                        fontSize: '0.75rem', 
                        padding: '2px 4px',
                        fontFamily: 'monospace'
                      }
                    }}
                    MenuProps={{
                      PaperProps: {
                        sx: {
                          '& .MuiMenuItem-root': {
                            fontFamily: 'monospace',
                            fontSize: '0.75rem'
                          }
                        }
                      }
                    }}
                  >
                    <MenuItem value="">all events</MenuItem>
                    <MenuItem value="user_login">user_login</MenuItem>
                    <MenuItem value="user_logout">user_logout</MenuItem>
                    <MenuItem value="user_created">user_created</MenuItem>
                    <MenuItem value="user_updated">user_updated</MenuItem>
                    <MenuItem value="user_deleted">user_deleted</MenuItem>
                    <MenuItem value="target_created">target_created</MenuItem>
                    <MenuItem value="target_updated">target_updated</MenuItem>
                    <MenuItem value="target_deleted">target_deleted</MenuItem>
                    <MenuItem value="job_created">job_created</MenuItem>
                    <MenuItem value="job_updated">job_updated</MenuItem>
                    <MenuItem value="job_deleted">job_deleted</MenuItem>
                    <MenuItem value="job_executed">job_executed</MenuItem>
                  </Select>
                </TableCell>
                <TableCell sx={{ padding: '4px 8px' }}>
                  <TextField
                    size="small"
                    fullWidth
                    placeholder="Filter action..."
                    value={columnFilters.action || ''}
                    onChange={(e) => handleColumnFilterChange('action', e.target.value)}
                    sx={{ '& .MuiInputBase-input': { fontSize: '0.75rem', padding: '2px 4px' } }}
                  />
                </TableCell>
                <TableCell sx={{ padding: '4px 8px' }}>
                  <TextField
                    size="small"
                    fullWidth
                    placeholder="Filter user..."
                    value={columnFilters.user_id || ''}
                    onChange={(e) => handleColumnFilterChange('user_id', e.target.value)}
                    sx={{ '& .MuiInputBase-input': { fontSize: '0.75rem', padding: '2px 4px' } }}
                  />
                </TableCell>
                <TableCell sx={{ padding: '4px 8px' }}>
                  <TextField
                    size="small"
                    fullWidth
                    placeholder="Filter resource..."
                    value={columnFilters.resource || ''}
                    onChange={(e) => handleColumnFilterChange('resource', e.target.value)}
                    sx={{ '& .MuiInputBase-input': { fontSize: '0.75rem', padding: '2px 4px' } }}
                  />
                </TableCell>
                <TableCell sx={{ padding: '4px 8px' }}>
                  <Select
                    size="small"
                    fullWidth
                    value={columnFilters.severity || ''}
                    onChange={(e) => handleColumnFilterChange('severity', e.target.value)}
                    sx={{ 
                      '& .MuiSelect-select': { 
                        fontSize: '0.75rem', 
                        padding: '2px 4px',
                        fontFamily: 'monospace'
                      }
                    }}
                    MenuProps={{
                      PaperProps: {
                        sx: {
                          '& .MuiMenuItem-root': {
                            fontFamily: 'monospace',
                            fontSize: '0.75rem'
                          }
                        }
                      }
                    }}
                  >
                    <MenuItem value="">all</MenuItem>
                    <MenuItem value="low">low</MenuItem>
                    <MenuItem value="medium">medium</MenuItem>
                    <MenuItem value="high">high</MenuItem>
                    <MenuItem value="critical">critical</MenuItem>
                  </Select>
                </TableCell>
                <TableCell sx={{ padding: '4px 8px' }}>
                  {/* Empty cell for actions column */}
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedEvents.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4, width: '100%' }}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
                      <SearchIcon sx={{ fontSize: 48, color: 'text.disabled' }} />
                      <Typography variant="body2" color="text.secondary">
                        {totalFilteredRecords === 0 ? 'No events match your filter criteria' : 'No audit events found'}
                      </Typography>
                    </Box>
                  </TableCell>
                </TableRow>
              ) : (
                paginatedEvents.map((event, index) => (
                  <TableRow 
                    key={event.id || index} 
                    sx={getSeverityRowStyling(event.severity, theme)}
                  >
                    <TableCell sx={getTableCellStyle()}>
                      {formatTimestamp(event.timestamp)}
                    </TableCell>
                    <TableCell sx={getTableCellStyle()}>
                      {event.event_type}
                    </TableCell>
                    <TableCell sx={getTableCellStyle()}>
                      {event.action}
                    </TableCell>
                    <TableCell sx={getTableCellStyle()}>
                      {auditService.getEnrichedUserDisplay(event)}
                    </TableCell>
                    <TableCell sx={getTableCellStyle()}>
                      {auditService.getEnrichedResourceDisplay(event)}
                    </TableCell>
                    <TableCell sx={getTableCellStyle()}>
                      {event.severity}
                    </TableCell>
                    <TableCell sx={{ padding: '4px 8px' }}>
                      <ViewDetailsAction
                        onClick={() => setSelectedEvent(event)}
                      />
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        {/* Pagination Controls */}
        <Box 
          sx={{ 
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mt: 1, // Reduced margin
            py: 1, // Reduced padding
            px: 1,
            flexShrink: 0 // Don't shrink this area
          }}
        >
          {/* Page Size Selector */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2" sx={{ fontSize: '0.75rem', color: 'text.secondary' }}>
              Show:
            </Typography>
            <Select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1); // Reset to first page
              }}
              size="small"
              sx={{ 
                minWidth: '70px',
                '& .MuiSelect-select': {
                  fontSize: '0.75rem',
                  py: 0.5
                }
              }}
            >
              <MenuItem value={25}>25</MenuItem>
              <MenuItem value={50}>50</MenuItem>
              <MenuItem value={100}>100</MenuItem>
              <MenuItem value={200}>200</MenuItem>
              <MenuItem value={500}>500</MenuItem>
            </Select>
            <Typography variant="body2" sx={{ fontSize: '0.75rem', color: 'text.secondary' }}>
              per page
            </Typography>
          </Box>

          {/* Pagination */}
          {totalFilteredRecords > pageSize && (
            <Pagination
              count={totalPages}
              page={currentPage}
              onChange={(event, page) => {
                setCurrentPage(page);
              }}
              color="primary"
              size="small"
              variant="outlined"
              sx={{ 
                '& .MuiPaginationItem-root': {
                  fontSize: '0.75rem',
                  minWidth: '28px',
                  height: '28px',
                  margin: '0 2px',
                  border: '1px solid #e0e0e0',
                  color: '#666',
                  '&:hover': {
                    backgroundColor: '#f5f5f5',
                    borderColor: '#ccc'
                  },
                  '&.Mui-selected': {
                    backgroundColor: '#1976d2',
                    color: 'white',
                    borderColor: '#1976d2',
                    '&:hover': {
                      backgroundColor: '#1565c0'
                    }
                  }
                }
              }}
            />
          )}
          
          {/* Show pagination info on the right */}
          <Typography variant="body2" sx={{ fontSize: '0.75rem', color: 'text.secondary' }}>
            Showing {startIndex + 1}-{Math.min(endIndex, totalFilteredRecords)} of {totalFilteredRecords} results (sample data)
          </Typography>
        </Box>
      </Box>

      {/* Event Details Dialog */}
      <Dialog
        open={!!selectedEvent}
        onClose={() => setSelectedEvent(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Event Details
          <CloseAction onClick={() => setSelectedEvent(null)} />
        </DialogTitle>
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
                  <Typography variant="body2" color="textSecondary">Action</Typography>
                  <Typography>{selectedEvent.action}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary">Details</Typography>
                  <Typography component="pre" sx={{ whiteSpace: 'pre-wrap', fontSize: '0.875rem' }}>
                    {JSON.stringify(selectedEvent.details || {}, null, 2)}
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default AuditDashboard;