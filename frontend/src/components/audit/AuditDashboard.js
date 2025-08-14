import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
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
  Pagination,
  Stack
} from '@mui/material';
import {
  Search as SearchIcon,
  ArrowUpward as ArrowUpwardIcon,
  ArrowDownward as ArrowDownwardIcon,
  UnfoldMore as UnfoldMoreIcon,
  Save as SaveIcon
} from '@mui/icons-material';
import SearchCard from '../common/SearchCard';
import ColumnFilters from '../common/ColumnFilters';
import { ViewDetailsAction, CloseAction, DownloadAction, RefreshAction } from '../common/StandardActions';
import { getSeverityRowStyling, getTableCellStyle } from '../../utils/tableUtils';
import { useTheme } from '@mui/material/styles';
import '../../styles/dashboard.css';

function AuditDashboard() {
  const theme = useTheme();
  const [events, setEvents] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [columnFilters, setColumnFilters] = useState({});
  const [sortField, setSortField] = useState('timestamp');
  const [sortDirection, setSortDirection] = useState('desc');
  const [eventTypes, setEventTypes] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [verificationResult, setVerificationResult] = useState(null);

  const fetchAuditData = async () => {
    try {
      setLoading(true);
      
      // Fetch recent events with pagination
      const eventsResponse = await fetch(`/api/v1/audit/events?page=${currentPage}&limit=${pageSize}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (eventsResponse.ok) {
        const eventsData = await eventsResponse.json();
        console.log('Audit events data:', JSON.stringify(eventsData, null, 2));
        console.log('Events array:', eventsData.events);
        console.log('Total count:', eventsData.total);
        setEvents(eventsData.events || []);
        setTotalCount(eventsData.total || eventsData.events?.length || 0);
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
      params.append('query', searchQuery || '');
      params.append('page', currentPage);
      params.append('limit', pageSize);
      if (eventTypeFilter) params.append('event_types', eventTypeFilter);
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
          page: currentPage,
          limit: pageSize
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Search events data:', data);
        setEvents(data.events || []);
        setTotalCount(data.total || data.events?.length || 0);
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
  }, [currentPage, pageSize]);

  useEffect(() => {
    if (searchQuery || eventTypeFilter || severityFilter) {
      searchEvents();
    } else {
      fetchAuditData();
    }
  }, [currentPage, pageSize, searchQuery, eventTypeFilter, severityFilter]);



  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  // Export functionality
  const handleExport = (format) => {
    if (filteredAndSortedEvents.length === 0) return;

    const exportData = filteredAndSortedEvents.map(event => ({
      timestamp: formatTimestamp(event.timestamp),
      event_type: event.event_type,
      action: event.action,
      user_id: event.user_id || 'System',
      resource: `${event.resource_type}:${event.resource_id}`,
      severity: event.severity,
      details: event.details || ''
    }));

    if (format === 'csv') {
      exportToCSV(exportData);
    } else if (format === 'json') {
      exportToJSON(exportData);
    }
  };

  const exportToCSV = (data) => {
    const headers = ['Timestamp', 'Event Type', 'Action', 'User', 'Resource', 'Severity', 'Details'];
    const csvContent = [
      headers.join(','),
      ...data.map(row => [
        `"${row.timestamp}"`,
        `"${row.event_type}"`,
        `"${row.action}"`,
        `"${row.user_id}"`,
        `"${row.resource}"`,
        `"${row.severity}"`,
        `"${row.details.replace(/"/g, '""')}"`
      ].join(','))
    ].join('\n');

    downloadFile(csvContent, 'audit-events.csv', 'text/csv');
  };

  const exportToJSON = (data) => {
    const jsonContent = JSON.stringify(data, null, 2);
    downloadFile(jsonContent, 'audit-events.json', 'application/json');
  };

  const downloadFile = (content, filename, contentType) => {
    const blob = new Blob([content], { type: contentType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  // Column configuration for filters
  const auditColumns = [
    {
      key: 'timestamp',
      label: 'Timestamp',
      width: 2,
      filterable: true,
      filterType: 'text',
      sortable: true
    },
    {
      key: 'event_type',
      label: 'Event Type',
      width: 1.5,
      filterable: true,
      filterType: 'select',
      sortable: true,
      options: eventTypes.map(type => ({ value: type.value, label: type.description }))
    },
    {
      key: 'action',
      label: 'Action',
      width: 1.5,
      filterable: true,
      filterType: 'text',
      sortable: true
    },
    {
      key: 'user_id',
      label: 'User',
      width: 1,
      filterable: true,
      filterType: 'text',
      sortable: true
    },
    {
      key: 'resource',
      label: 'Resource',
      width: 2,
      filterable: true,
      filterType: 'text',
      sortable: true
    },
    {
      key: 'severity',
      label: 'Severity',
      width: 1,
      filterable: true,
      filterType: 'select',
      sortable: true,
      options: [
        { value: 'low', label: 'Low' },
        { value: 'medium', label: 'Medium' },
        { value: 'high', label: 'High' },
        { value: 'critical', label: 'Critical' }
      ]
    },
    {
      key: 'actions',
      label: 'Actions',
      width: 0.5,
      filterable: false,
      sortable: false
    }
  ];

  const handleColumnFilterChange = (columnKey, value) => {
    setColumnFilters(prev => ({
      ...prev,
      [columnKey]: value
    }));
  };

  const handleSortChange = (columnKey, direction) => {
    setSortField(columnKey);
    setSortDirection(direction);
  };

  // Filter and sort events based on column filters and sort settings
  const filteredAndSortedEvents = events
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
          case 'timestamp':
            return formatTimestamp(event.timestamp).toLowerCase().includes(filterValue.toLowerCase());
          case 'event_type':
            return event.event_type === filterValue;
          case 'action':
            return event.action.toLowerCase().includes(filterValue.toLowerCase());
          case 'user_id':
            return (event.user_id || 'System').toLowerCase().includes(filterValue.toLowerCase());
          case 'resource':
            return `${event.resource_type}:${event.resource_id}`.toLowerCase().includes(filterValue.toLowerCase());
          case 'severity':
            return event.severity === filterValue;
          default:
            return true;
        }
      });
    })
    .sort((a, b) => {
      let aValue, bValue;
      
      switch (sortField) {
        case 'timestamp':
          aValue = new Date(a.timestamp);
          bValue = new Date(b.timestamp);
          break;
        case 'event_type':
          aValue = a.event_type || '';
          bValue = b.event_type || '';
          break;
        case 'action':
          aValue = a.action || '';
          bValue = b.action || '';
          break;
        case 'user_id':
          aValue = a.user_id || 'System';
          bValue = b.user_id || 'System';
          break;
        case 'resource':
          aValue = `${a.resource_type}:${a.resource_id}`;
          bValue = `${b.resource_type}:${b.resource_id}`;
          break;
        case 'severity':
          const severityOrder = { low: 1, medium: 2, high: 3, critical: 4 };
          aValue = severityOrder[a.severity] || 0;
          bValue = severityOrder[b.severity] || 0;
          break;
        default:
          return 0;
      }
      
      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });





  return (
    <div className="dashboard-container" style={{ marginBottom: '80px' }}>
      {/* Page Header */}
      <div className="page-header">
        <Typography className="page-title">
          Audit & Compliance
        </Typography>
        <div className="page-actions">
          {/* Record Count */}
          <Typography 
            variant="body2" 
            sx={{ 
              fontFamily: 'monospace',
              fontSize: '0.75rem',
              color: 'text.secondary',
              marginRight: 2,
              display: 'flex',
              alignItems: 'center'
            }}
          >
            {events.length} of {totalCount} records (Page {currentPage})
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
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card sx={{ 
            height: 'calc(100vh - 200px)', // Full height minus header and margins
            display: 'flex',
            flexDirection: 'column'
          }}>
            <CardContent sx={{ 
              py: 2, 
              '&:last-child': { pb: 2 },
              flex: 1,
              display: 'flex',
              flexDirection: 'column'
            }}>
              <TableContainer 
                component={Paper} 
                variant="outlined"
                sx={{ 
                  flex: 1, // Take up remaining space in the card
                  minHeight: '400px', // Minimum height for usability
                  border: '1px solid', 
                  borderColor: 'divider' 
                }}
              >
                <Table stickyHeader size="small">
                  {/* Column Headers Row */}
                  <TableHead>
                    <TableRow sx={{ backgroundColor: 'grey.100' }}>
                      <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold', fontSize: '0.75rem' }}>
                            Timestamp
                          </Typography>
                          <IconButton
                            size="small"
                            onClick={() => handleSortChange('timestamp', sortField === 'timestamp' && sortDirection === 'asc' ? 'desc' : 'asc')}
                            sx={{ padding: '2px', marginLeft: '4px' }}
                          >
                            {sortField === 'timestamp' ? 
                              (sortDirection === 'asc' ? 
                                <ArrowUpwardIcon sx={{ fontSize: 14, color: 'primary.main' }} /> : 
                                <ArrowDownwardIcon sx={{ fontSize: 14, color: 'primary.main' }} />
                              ) : 
                              <UnfoldMoreIcon sx={{ fontSize: 14, color: 'text.disabled' }} />
                            }
                          </IconButton>
                        </Box>
                      </TableCell>
                      <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold', fontSize: '0.75rem' }}>
                            Event Type
                          </Typography>
                          <IconButton
                            size="small"
                            onClick={() => handleSortChange('event_type', sortField === 'event_type' && sortDirection === 'asc' ? 'desc' : 'asc')}
                            sx={{ padding: '2px', marginLeft: '4px' }}
                          >
                            {sortField === 'event_type' ? 
                              (sortDirection === 'asc' ? 
                                <ArrowUpwardIcon sx={{ fontSize: 14, color: 'primary.main' }} /> : 
                                <ArrowDownwardIcon sx={{ fontSize: 14, color: 'primary.main' }} />
                              ) : 
                              <UnfoldMoreIcon sx={{ fontSize: 14, color: 'text.disabled' }} />
                            }
                          </IconButton>
                        </Box>
                      </TableCell>
                      <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold', fontSize: '0.75rem' }}>
                            Action
                          </Typography>
                          <IconButton
                            size="small"
                            onClick={() => handleSortChange('action', sortField === 'action' && sortDirection === 'asc' ? 'desc' : 'asc')}
                            sx={{ padding: '2px', marginLeft: '4px' }}
                          >
                            {sortField === 'action' ? 
                              (sortDirection === 'asc' ? 
                                <ArrowUpwardIcon sx={{ fontSize: 14, color: 'primary.main' }} /> : 
                                <ArrowDownwardIcon sx={{ fontSize: 14, color: 'primary.main' }} />
                              ) : 
                              <UnfoldMoreIcon sx={{ fontSize: 14, color: 'text.disabled' }} />
                            }
                          </IconButton>
                        </Box>
                      </TableCell>
                      <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold', fontSize: '0.75rem' }}>
                            User
                          </Typography>
                          <IconButton
                            size="small"
                            onClick={() => handleSortChange('user_id', sortField === 'user_id' && sortDirection === 'asc' ? 'desc' : 'asc')}
                            sx={{ padding: '2px', marginLeft: '4px' }}
                          >
                            {sortField === 'user_id' ? 
                              (sortDirection === 'asc' ? 
                                <ArrowUpwardIcon sx={{ fontSize: 14, color: 'primary.main' }} /> : 
                                <ArrowDownwardIcon sx={{ fontSize: 14, color: 'primary.main' }} />
                              ) : 
                              <UnfoldMoreIcon sx={{ fontSize: 14, color: 'text.disabled' }} />
                            }
                          </IconButton>
                        </Box>
                      </TableCell>
                      <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold', fontSize: '0.75rem' }}>
                            Resource
                          </Typography>
                          <IconButton
                            size="small"
                            onClick={() => handleSortChange('resource', sortField === 'resource' && sortDirection === 'asc' ? 'desc' : 'asc')}
                            sx={{ padding: '2px', marginLeft: '4px' }}
                          >
                            {sortField === 'resource' ? 
                              (sortDirection === 'asc' ? 
                                <ArrowUpwardIcon sx={{ fontSize: 14, color: 'primary.main' }} /> : 
                                <ArrowDownwardIcon sx={{ fontSize: 14, color: 'primary.main' }} />
                              ) : 
                              <UnfoldMoreIcon sx={{ fontSize: 14, color: 'text.disabled' }} />
                            }
                          </IconButton>
                        </Box>
                      </TableCell>
                      <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold', fontSize: '0.75rem' }}>
                            Severity
                          </Typography>
                          <IconButton
                            size="small"
                            onClick={() => handleSortChange('severity', sortField === 'severity' && sortDirection === 'asc' ? 'desc' : 'asc')}
                            sx={{ padding: '2px', marginLeft: '4px' }}
                          >
                            {sortField === 'severity' ? 
                              (sortDirection === 'asc' ? 
                                <ArrowUpwardIcon sx={{ fontSize: 14, color: 'primary.main' }} /> : 
                                <ArrowDownwardIcon sx={{ fontSize: 14, color: 'primary.main' }} />
                              ) : 
                              <UnfoldMoreIcon sx={{ fontSize: 14, color: 'text.disabled' }} />
                            }
                          </IconButton>
                        </Box>
                      </TableCell>
                      <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                        Actions
                      </TableCell>
                    </TableRow>
                    
                    {/* Filters Row */}
                    <TableRow sx={{ backgroundColor: 'grey.50' }}>
                      <TableCell sx={{ padding: '4px 8px', minHeight: '50px' }}>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                          <TextField
                            size="small"
                            fullWidth
                            type="datetime-local"
                            value={columnFilters.timestamp_start || ''}
                            onChange={(e) => handleColumnFilterChange('timestamp_start', e.target.value)}
                            sx={{
                              '& .MuiInputBase-input': {
                                fontFamily: 'monospace',
                                fontSize: '0.75rem',
                                padding: '1px 2px',
                                height: '14px'
                              }
                            }}
                          />
                          <TextField
                            size="small"
                            fullWidth
                            type="datetime-local"
                            value={columnFilters.timestamp_end || ''}
                            onChange={(e) => handleColumnFilterChange('timestamp_end', e.target.value)}
                            sx={{
                              '& .MuiInputBase-input': {
                                fontFamily: 'monospace',
                                fontSize: '0.75rem',
                                padding: '1px 2px',
                                height: '14px'
                              }
                            }}
                          />
                        </Box>
                      </TableCell>
                      <TableCell sx={{ padding: '4px 8px' }}>
                        <FormControl size="small" fullWidth>
                          <Select
                            value={columnFilters.event_type || ''}
                            onChange={(e) => handleColumnFilterChange('event_type', e.target.value)}
                            displayEmpty
                            sx={{
                              fontFamily: 'monospace',
                              fontSize: '0.75rem',
                              '& .MuiSelect-select': {
                                padding: '2px 4px',
                                fontFamily: 'monospace',
                                fontSize: '0.75rem'
                              }
                            }}
                            MenuProps={{
                              PaperProps: {
                                sx: {
                                  '& .MuiMenuItem-root': {
                                    fontFamily: 'monospace',
                                    fontSize: '0.75rem',
                                    minHeight: 'auto',
                                    padding: '4px 8px'
                                  }
                                }
                              }
                            }}
                          >
                            <MenuItem value="" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                              <em>All Event Types</em>
                            </MenuItem>
                            {eventTypes.map((type) => (
                              <MenuItem 
                                key={type.value} 
                                value={type.value}
                                sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}
                              >
                                {type.description}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      </TableCell>
                      <TableCell sx={{ padding: '4px 8px' }}>
                        <TextField
                          size="small"
                          fullWidth
                          placeholder="Filter Action..."
                          value={columnFilters.action || ''}
                          onChange={(e) => handleColumnFilterChange('action', e.target.value)}
                          sx={{
                            '& .MuiInputBase-input': {
                              fontFamily: 'monospace',
                              fontSize: '0.75rem',
                              padding: '2px 4px'
                            }
                          }}
                        />
                      </TableCell>
                      <TableCell sx={{ padding: '4px 8px' }}>
                        <TextField
                          size="small"
                          fullWidth
                          placeholder="Filter User..."
                          value={columnFilters.user_id || ''}
                          onChange={(e) => handleColumnFilterChange('user_id', e.target.value)}
                          sx={{
                            '& .MuiInputBase-input': {
                              fontFamily: 'monospace',
                              fontSize: '0.75rem',
                              padding: '2px 4px'
                            }
                          }}
                        />
                      </TableCell>
                      <TableCell sx={{ padding: '4px 8px' }}>
                        <TextField
                          size="small"
                          fullWidth
                          placeholder="Filter Resource..."
                          value={columnFilters.resource || ''}
                          onChange={(e) => handleColumnFilterChange('resource', e.target.value)}
                          sx={{
                            '& .MuiInputBase-input': {
                              fontFamily: 'monospace',
                              fontSize: '0.75rem',
                              padding: '2px 4px'
                            }
                          }}
                        />
                      </TableCell>
                      <TableCell sx={{ padding: '4px 8px' }}>
                        <FormControl size="small" fullWidth>
                          <Select
                            value={columnFilters.severity || ''}
                            onChange={(e) => handleColumnFilterChange('severity', e.target.value)}
                            displayEmpty
                            sx={{
                              fontFamily: 'monospace',
                              fontSize: '0.75rem',
                              '& .MuiSelect-select': {
                                padding: '2px 4px',
                                fontFamily: 'monospace',
                                fontSize: '0.75rem'
                              }
                            }}
                            MenuProps={{
                              PaperProps: {
                                sx: {
                                  '& .MuiMenuItem-root': {
                                    fontFamily: 'monospace',
                                    fontSize: '0.75rem',
                                    minHeight: 'auto',
                                    padding: '4px 8px'
                                  }
                                }
                              }
                            }}
                          >
                            <MenuItem value="" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                              <em>All Severities</em>
                            </MenuItem>
                            <MenuItem value="low" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Low</MenuItem>
                            <MenuItem value="medium" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Medium</MenuItem>
                            <MenuItem value="high" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>High</MenuItem>
                            <MenuItem value="critical" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Critical</MenuItem>
                          </Select>
                        </FormControl>
                      </TableCell>
                      <TableCell sx={{ padding: '4px 8px' }}>
                        {/* No filter for Actions column */}
                      </TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredAndSortedEvents.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
                            <SearchIcon sx={{ fontSize: 48, color: 'text.disabled' }} />
                            <Typography variant="body2" color="text.secondary">
                              {events.length === 0 ? 'No audit events found' : 'No events match your filter criteria'}
                            </Typography>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredAndSortedEvents.map((event, index) => (
                        <TableRow 
                          key={index} 
                          hover
                          sx={getSeverityRowStyling(event.severity, theme)}
                        >
                          <TableCell sx={getTableCellStyle(true)}>
                            {formatTimestamp(event.timestamp)}
                          </TableCell>
                          <TableCell sx={getTableCellStyle()}>
                            {event.event_type}
                          </TableCell>
                          <TableCell sx={getTableCellStyle()}>
                            {event.action}
                          </TableCell>
                          <TableCell sx={getTableCellStyle()}>
                            {event.user_id || 'System'}
                          </TableCell>
                          <TableCell sx={getTableCellStyle()}>
                            {event.resource_type}:{event.resource_id}
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
              
              {/* Pagination Controls - ALWAYS VISIBLE */}
              <Stack 
                direction="row" 
                justifyContent="space-between" 
                alignItems="center" 
                sx={{ 
                  mt: 2, 
                  px: 2, 
                  pb: 2,
                  backgroundColor: '#f5f5f5',
                  borderRadius: 1,
                  border: '2px solid red' // DEBUG: Make it visible
                }}
              >
                <Typography variant="body2" color="textSecondary">
                  Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalCount)} of {totalCount} entries
                  <br />
                  DEBUG: currentPage={currentPage}, pageSize={pageSize}, totalCount={totalCount}, pageCount={Math.ceil(totalCount / pageSize)}
                </Typography>
                <Pagination
                  count={Math.max(1, Math.ceil(totalCount / pageSize))}
                  page={currentPage}
                  onChange={(event, page) => {
                    console.log('Pagination change:', { page, totalCount, pageSize });
                    setCurrentPage(page);
                  }}
                  color="primary"
                  size="small"
                  showFirstButton
                  showLastButton
                  sx={{ 
                    border: '2px solid blue' // DEBUG: Make pagination visible
                  }}
                />
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

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
                  <Typography variant="body2" color="textSecondary">Severity</Typography>
                  <Typography sx={{ fontFamily: 'monospace' }}>{selectedEvent.severity}</Typography>
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
      </Dialog>
    </div>
  );
}

export default AuditDashboard;