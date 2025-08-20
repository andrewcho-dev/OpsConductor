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
      const baseUrl = process.env.REACT_APP_API_URL || '';
      const eventsResponse = await fetch(`${baseUrl}/audit/events?page=${currentPage}&limit=${pageSize}&sort=${sortField}&order=${sortDirection}`, {
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
      const typesResponse = await fetch(`${baseUrl}/audit/event-types`, {
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
      const baseUrl = process.env.REACT_APP_API_URL || '';
      const response = await fetch(`${baseUrl}/audit/export?format=${format}`, {
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

  // Use real API data only - NO MORE MOCK DATA
  const eventsToDisplay = enrichedEvents.length > 0 ? enrichedEvents : events;

  // Debug: Log key information
  console.log('Real Events from API:', events.length);
  console.log('Enriched Events:', enrichedEvents.length);
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
    <div className="datatable-page-container">


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
              fontSize: '0.75rem',
              fontWeight: 500,
              height: '32px',
              display: 'flex',
              alignItems: 'center'
            }}
          >
            {paginatedEvents.length} of {totalFilteredRecords} records {totalFilteredRecords > pageSize ? `(Page ${currentPage} of ${totalPages})` : ''}
            {enriching && <span style={{ marginLeft: '8px', color: '#1976d2' }}>• Enriching...</span>}
          </Typography>
          
          {/* Export/Save Actions */}
          <DownloadAction 
            onClick={() => handleExport('csv')} 
            disabled={loading || filteredAndSortedEvents.length === 0}
            title="Export to CSV"
          />
          <IconButton
            className="btn-icon"
            size="small"
            onClick={() => handleExport('json')}
            disabled={loading || filteredAndSortedEvents.length === 0}
            title="Export to JSON"
          >
            <SaveIcon fontSize="small" />
          </IconButton>
          
          <RefreshAction onClick={fetchAuditData} disabled={loading} />
        </div>
      </div>

      {/* Audit Events Table */}
      <div className="table-content-area">

        <TableContainer 
          component={Paper} 
          variant="outlined"
          className="standard-table-container"
        >
          <Table size="small">
            <TableHead>
              {/* Column Headers */}
              <TableRow sx={{ backgroundColor: 'grey.100' }}>
                <TableCell className="standard-table-header">
                  Timestamp
                </TableCell>
                <TableCell className="standard-table-header">
                  Event Type
                </TableCell>
                <TableCell className="standard-table-header">
                  Action
                </TableCell>
                <TableCell className="standard-table-header">
                  User
                </TableCell>
                <TableCell className="standard-table-header">
                  Resource
                </TableCell>
                <TableCell className="standard-table-header">
                  Severity
                </TableCell>
                <TableCell className="standard-table-header">
                  Actions
                </TableCell>
              </TableRow>
              
              {/* Filter Row */}
              <TableRow sx={{ backgroundColor: 'grey.50' }}>
                <TableCell className="standard-filter-cell">
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    <TextField
                      size="small"
                      fullWidth
                      type="datetime-local"
                      value={columnFilters.timestamp_start || ''}
                      onChange={(e) => handleColumnFilterChange('timestamp_start', e.target.value)}
                      className="standard-filter-input"
                    />
                    <TextField
                      size="small"
                      fullWidth
                      type="datetime-local"
                      value={columnFilters.timestamp_end || ''}
                      onChange={(e) => handleColumnFilterChange('timestamp_end', e.target.value)}
                      className="standard-filter-input"
                    />
                  </Box>
                </TableCell>
                <TableCell className="standard-filter-cell">
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
                <TableCell className="standard-filter-cell">
                  <TextField
                    size="small"
                    fullWidth
                    placeholder="Filter action..."
                    value={columnFilters.action || ''}
                    onChange={(e) => handleColumnFilterChange('action', e.target.value)}
                    className="standard-filter-input"
                  />
                </TableCell>
                <TableCell className="standard-filter-cell">
                  <TextField
                    size="small"
                    fullWidth
                    placeholder="Filter user..."
                    value={columnFilters.user_id || ''}
                    onChange={(e) => handleColumnFilterChange('user_id', e.target.value)}
                    className="standard-filter-input"
                  />
                </TableCell>
                <TableCell className="standard-filter-cell">
                  <TextField
                    size="small"
                    fullWidth
                    placeholder="Filter resource..."
                    value={columnFilters.resource || ''}
                    onChange={(e) => handleColumnFilterChange('resource', e.target.value)}
                    className="standard-filter-input"
                  />
                </TableCell>
                <TableCell className="standard-filter-cell">
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
                <TableCell className="standard-filter-cell">
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
                    <TableCell className="standard-table-cell">
                      {formatTimestamp(event.timestamp)}
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      {event.event_type}
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      {event.action}
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      {auditService.getEnrichedUserDisplay(event)}
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      {auditService.getEnrichedResourceDisplay(event)}
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      {event.severity}
                    </TableCell>
                    <TableCell className="standard-table-cell">
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
        <div className="standard-pagination-area">
          {/* Page Size Selector */}
          <div className="standard-page-size-selector">
            <Typography variant="body2" className="standard-pagination-info">
              Show:
            </Typography>
            <Select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1); // Reset to first page
              }}
              size="small"
              className="standard-page-size-selector"
            >
              <MenuItem value={25}>25</MenuItem>
              <MenuItem value={50}>50</MenuItem>
              <MenuItem value={100}>100</MenuItem>
              <MenuItem value={200}>200</MenuItem>
            </Select>
            <Typography variant="body2" className="standard-pagination-info">
              per page
            </Typography>
          </div>

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
              className="standard-pagination"
            />
          )}
          
          {/* Show pagination info on the right */}
          <Typography variant="body2" className="standard-pagination-info">
            Showing {startIndex + 1}-{Math.min(endIndex, totalFilteredRecords)} of {totalFilteredRecords} results
          </Typography>
        </div>
      </div>

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