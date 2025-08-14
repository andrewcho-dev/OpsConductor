/**
 * Job List - Table Format
 * Displays jobs in a table with search, filter, and action capabilities.
 * Following the same pattern as UniversalTargetList
 */
import React, { useState, useMemo, useCallback } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  Box,
  IconButton,
  Tooltip,
  Typography,
  Select,
  MenuItem,
  FormControl,
  Button,
  Checkbox,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Schedule as ScheduleIcon,
  Visibility as VisibilityIcon,
  Work as WorkIcon,
  Refresh as RefreshIcon,
  ArrowUpward as ArrowUpwardIcon,
  ArrowDownward as ArrowDownwardIcon,
  Stop as StopIcon,
  Warning as WarningIcon,
  AccessTime as LocalTimeIcon,
  Public as UtcTimeIcon
} from '@mui/icons-material';

import JobScheduleModal from './JobScheduleModal';
import JobEditModal from './JobEditModal';
import JobExecutionHistoryModal from './JobExecutionHistoryModal';
import { formatLocalDateTime, formatBothUTCAndLocal } from '../../utils/timeUtils';
import { useAuth } from '../../contexts/AuthContext';
import { useAlert } from '../layout/BottomStatusBar';
import { ViewDetailsAction, EditAction, DeleteAction, PlayAction, StopAction } from '../common/StandardActions';
import { getStatusRowStyling, getTableCellStyle } from '../../utils/tableUtils';
import { useTheme } from '@mui/material/styles';

const JobList = ({ 
    jobs, 
    onExecuteJob, 
    onScheduleJob, 
    onUpdateJob,
    onDeleteJob
}) => {
    const theme = useTheme();
    const { token } = useAuth();
    const { addAlert } = useAlert();
    const [page, setPage] = useState(0);
    const [rowsPerPage, setRowsPerPage] = useState(10);

    const [sortField, setSortField] = useState('name');
    const [sortDirection, setSortDirection] = useState('asc');
    const [showScheduleModal, setShowScheduleModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [showHistoryModal, setShowHistoryModal] = useState(false);
    const [jobToSchedule, setJobToSchedule] = useState(null);
    const [jobToEdit, setJobToEdit] = useState(null);
    const [jobToViewHistory, setJobToViewHistory] = useState(null);
    
    // New state for bulk operations and termination
    const [selectedJobs, setSelectedJobs] = useState(new Set());
    const [showTerminateDialog, setShowTerminateDialog] = useState(false);
    const [jobsToTerminate, setJobsToTerminate] = useState([]);
    const [terminateReason, setTerminateReason] = useState('');
    const [terminateLoading, setTerminateLoading] = useState(false);
    const [columnFilters, setColumnFilters] = useState({});

    // Filter jobs based on column filters and sort
    const filteredAndSortedJobs = useMemo(() => {
        // Apply column filters
        if (!jobs || !Array.isArray(jobs)) {
            return [];
        }

        const filtered = jobs.filter(job => {
            try {
                return Object.entries(columnFilters).every(([key, filterValue]) => {
                    if (!filterValue) return true;
                    
                    switch (key) {
                        case 'name':
                            return job.name?.toLowerCase().includes(filterValue.toLowerCase());
                        case 'job_serial':
                            return (job.job_serial || `ID-${job.id}`).toLowerCase().includes(filterValue.toLowerCase());
                        case 'job_type':
                            return job.job_type === filterValue;
                        case 'status':
                            return job.status === filterValue;
                        case 'created_at':
                            try {
                                const createdTime = formatDateWithBothTimezones(job.created_at);
                                return createdTime.local.toLowerCase().includes(filterValue.toLowerCase());
                            } catch (e) {
                                return true;
                            }
                        case 'last_run':
                            try {
                                const lastRunTime = job.last_execution ? formatDateWithBothTimezones(job.last_execution.started_at) : { local: 'Never run' };
                                return lastRunTime.local.toLowerCase().includes(filterValue.toLowerCase());
                            } catch (e) {
                                return true;
                            }
                        case 'scheduled_at':
                            try {
                                const scheduledTime = job.scheduled_at ? formatDateWithBothTimezones(job.scheduled_at).local : 'Not scheduled';
                                return scheduledTime.toLowerCase().includes(filterValue.toLowerCase());
                            } catch (e) {
                                return true;
                            }
                        default:
                            return true;
                    }
                });
            } catch (e) {
                return true; // Include job if there's an error
            }
        });

        // Sort the filtered results
        const sorted = filtered.sort((a, b) => {
            let aValue = a[sortField];
            let bValue = b[sortField];
            
            // Handle null/undefined values
            if (aValue == null) aValue = '';
            if (bValue == null) bValue = '';
            
            // Convert to strings for comparison
            aValue = String(aValue).toLowerCase();
            bValue = String(bValue).toLowerCase();
            
            if (sortDirection === 'asc') {
                return aValue.localeCompare(bValue);
            } else {
                return bValue.localeCompare(aValue);
            }
        });
        
        return sorted;
    }, [jobs, columnFilters, sortField, sortDirection]);

    const handleChangePage = useCallback((event, newPage) => {
        setPage(newPage);
    }, []);

    const handleChangeRowsPerPage = useCallback((event) => {
        setRowsPerPage(parseInt(event.target.value, 10));
        setPage(0);
    }, []);

    const handleSort = useCallback((field) => {
        if (sortField === field) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortDirection('asc');
        }
    }, [sortField, sortDirection]);

    const handleExecuteClick = useCallback(async (job, e) => {
        e.stopPropagation();
        await onExecuteJob(job.id);
    }, [onExecuteJob]);

    const handleScheduleClick = useCallback((job, e) => {
        e.stopPropagation();
        setJobToSchedule(job);
        setShowScheduleModal(true);
    }, []);



    const handleScheduleSubmit = useCallback(async (scheduledAt) => {
        if (jobToSchedule) {
            await onScheduleJob(jobToSchedule.id, scheduledAt);
            setShowScheduleModal(false);
            setJobToSchedule(null);
        }
    }, [jobToSchedule, onScheduleJob]);



    const handleEditClick = useCallback((job, e) => {
        e.stopPropagation();
        setJobToEdit(job);
        setShowEditModal(true);
    }, []);

    const handleEditSubmit = useCallback(async (updatedJob) => {
        await onUpdateJob(updatedJob);
        setShowEditModal(false);
        setJobToEdit(null);
    }, [onUpdateJob]);

    const handleDeleteClick = useCallback(async (job, e) => {
        e.stopPropagation();
        if (window.confirm(`Are you sure you want to delete job "${job.name}"? This action cannot be undone.`)) {
            await onDeleteJob(job.id);
        }
    }, [onDeleteJob]);

    const handleViewHistoryClick = useCallback((job, e) => {
        e.stopPropagation();
        setJobToViewHistory(job);
        setShowHistoryModal(true);
    }, []);

    // New handlers for termination and bulk operations
    const handleSelectJob = useCallback((jobId, checked) => {
        setSelectedJobs(prev => {
            const newSet = new Set(prev);
            if (checked) {
                newSet.add(jobId);
            } else {
                newSet.delete(jobId);
            }
            return newSet;
        });
    }, []);

    const handleSelectAll = useCallback((checked) => {
        if (checked) {
            const runningJobIds = filteredAndSortedJobs
                .filter(job => job.status === 'running')
                .map(job => job.id);
            setSelectedJobs(new Set(runningJobIds));
        } else {
            setSelectedJobs(new Set());
        }
    }, [filteredAndSortedJobs]);

    const handleTerminateJob = useCallback(async (job, e) => {
        e.stopPropagation();
        setJobsToTerminate([job]);
        setShowTerminateDialog(true);
        setTerminateReason('');
    }, []);

    const handleBulkTerminate = useCallback(() => {
        const jobsToTerminateList = filteredAndSortedJobs.filter(job => selectedJobs.has(job.id));
        setJobsToTerminate(jobsToTerminateList);
        setShowTerminateDialog(true);
        setTerminateReason('');
    }, [filteredAndSortedJobs, selectedJobs]);

    const executeTermination = useCallback(async () => {
        if (jobsToTerminate.length === 0) return;

        setTerminateLoading(true);
        let successCount = 0;
        let errorCount = 0;

        for (const job of jobsToTerminate) {
            const jobIdentifier = job.job_serial || job.id;
            try {
                console.log(`Attempting to terminate job ${jobIdentifier} (${job.name})`);
                
                const response = await fetch(`/api/jobs/safety/terminate/${jobIdentifier}`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        reason: terminateReason || 'Manual termination from job list' 
                    }),
                });
                console.log(`Response status for job ${jobIdentifier}:`, response.status);
                
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error(`HTTP error for job ${jobIdentifier}:`, response.status, errorText);
                    errorCount++;
                    continue;
                }

                const result = await response.json();
                console.log(`Response for job ${jobIdentifier}:`, result);
                
                if (result.success) {
                    successCount++;
                    console.log(`Successfully terminated job ${jobIdentifier}`);
                } else {
                    errorCount++;
                    console.error(`Failed to terminate job ${jobIdentifier}:`, result);
                }
            } catch (error) {
                errorCount++;
                console.error(`Error terminating job ${jobIdentifier}:`, error);
            }
        }

        setTerminateLoading(false);
        setShowTerminateDialog(false);
        setJobsToTerminate([]);
        setTerminateReason('');
        setSelectedJobs(new Set());

        // Show results
        if (successCount > 0) {
            addAlert(`Successfully terminated ${successCount} job${successCount > 1 ? 's' : ''}`, 'success', 3000);
        }
        if (errorCount > 0) {
            addAlert(`Failed to terminate ${errorCount} job${errorCount > 1 ? 's' : ''}`, 'error', 5000);
        }

        // Refresh the job list
        if (window.location.reload) {
            setTimeout(() => window.location.reload(), 1000);
        }
    }, [jobsToTerminate, terminateReason, token, addAlert]);

    const formatDate = useCallback((dateString) => {
        return formatLocalDateTime(dateString);
    }, []);

    const formatDateWithBothTimezones = useCallback((dateString) => {
        if (!dateString) return { local: 'Never', utc: 'Never' };
        
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) {
                return { local: 'Invalid Date', utc: 'Invalid Date' };
            }
            
            // Use consistent format for both local and UTC: MM/DD/YYYY HH:MM:SS AM/PM
            const formatOptions = {
                month: '2-digit',
                day: '2-digit', 
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: true
            };
            
            // Format local time
            const localFormatted = date.toLocaleString('en-US', formatOptions);
            
            // Format UTC time with same format
            const utcFormatted = date.toLocaleString('en-US', {
                ...formatOptions,
                timeZone: 'UTC'
            });
            
            return {
                local: localFormatted,
                utc: utcFormatted
            };
        } catch (error) {
            return { local: 'Invalid Date', utc: 'Invalid Date' };
        }
    }, []);



    const getJobTypeLabel = useCallback((jobType) => {
        switch (jobType) {
            case 'command': return 'Command';
            case 'script': return 'Script';
            case 'file_transfer': return 'File Transfer';
            case 'composite': return 'Composite';
            default: return jobType;
        }
    }, []);

    const handleColumnFilterChange = (columnKey, value) => {
        setColumnFilters(prev => ({
            ...prev,
            [columnKey]: value
        }));
    };

    // Paginated jobs - memoized for performance
    const paginatedJobs = useMemo(() => {
        return filteredAndSortedJobs.slice(
            page * rowsPerPage,
            page * rowsPerPage + rowsPerPage
        );
    }, [filteredAndSortedJobs, page, rowsPerPage]);

    // Computed values for bulk operations
    const runningJobs = useMemo(() => {
        return filteredAndSortedJobs.filter(job => job.status === 'running');
    }, [filteredAndSortedJobs]);

    const allRunningSelected = useMemo(() => {
        return runningJobs.length > 0 && runningJobs.every(job => selectedJobs.has(job.id));
    }, [runningJobs, selectedJobs]);

    const someRunningSelected = useMemo(() => {
        return runningJobs.some(job => selectedJobs.has(job.id));
    }, [runningJobs, selectedJobs]);

    // Sortable header component - memoized for performance
    const SortableHeader = useCallback(({ field, children, ...props }) => (
        <TableCell 
            {...props}
            className="table-header-cell"
            onClick={() => handleSort(field)}
            sx={{ 
                cursor: 'pointer', 
                userSelect: 'none',
                '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.04)' }
            }}
        >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                {children}
                {sortField === field && (
                    sortDirection === 'asc' ? 
                        <ArrowUpwardIcon sx={{ fontSize: 14 }} /> : 
                        <ArrowDownwardIcon sx={{ fontSize: 14 }} />
                )}
            </Box>
        </TableCell>
    ), [handleSort, sortField, sortDirection]);

    return (
        <Box>
            {/* Bulk Operations */}
            {selectedJobs.size > 0 && (
                <Box sx={{ mb: 2 }}>
                    <Button
                        variant="contained"
                        color="error"
                        size="small"
                        startIcon={<StopIcon fontSize="small" />}
                        onClick={handleBulkTerminate}
                    >
                        Terminate Selected ({selectedJobs.size})
                    </Button>
                </Box>
            )}

            {/* Compact Table */}
            <TableContainer className="table-container">
                <Table size="small" className="compact-table">
                    <TableHead>
                        {/* Column Headers Row */}
                        <TableRow sx={{ backgroundColor: 'grey.100' }}>
                            <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }} padding="checkbox">
                                <Tooltip title={runningJobs.length > 0 ? "Select all running jobs" : "No running jobs to select"}>
                                    <Checkbox
                                        indeterminate={someRunningSelected && !allRunningSelected}
                                        checked={allRunningSelected}
                                        onChange={(e) => handleSelectAll(e.target.checked)}
                                        disabled={runningJobs.length === 0}
                                        size="small"
                                    />
                                </Tooltip>
                            </TableCell>
                            <SortableHeader field="name" sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                                Job Name
                            </SortableHeader>
                            <SortableHeader field="job_serial" sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                                Job Serial
                            </SortableHeader>
                            <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>Type</TableCell>
                            <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>Status</TableCell>
                            <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>Created</TableCell>
                            <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>Last Run</TableCell>
                            <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>Next Scheduled</TableCell>
                            <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }} align="center">Actions</TableCell>
                        </TableRow>
                        
                        {/* Column Filters Row */}
                        <TableRow sx={{ backgroundColor: 'grey.50' }}>
                            <TableCell sx={{ padding: '4px 8px' }} padding="checkbox">
                                {/* No filter for checkbox column */}
                            </TableCell>
                            <TableCell sx={{ padding: '4px 8px' }}>
                                <TextField
                                    size="small"
                                    placeholder="Filter name..."
                                    value={columnFilters.name || ''}
                                    onChange={(e) => handleColumnFilterChange('name', e.target.value)}
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
                                    placeholder="Filter serial..."
                                    value={columnFilters.job_serial || ''}
                                    onChange={(e) => handleColumnFilterChange('job_serial', e.target.value)}
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
                                        value={columnFilters.job_type || ''}
                                        onChange={(e) => handleColumnFilterChange('job_type', e.target.value)}
                                        displayEmpty
                                        sx={{
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
                                            <em>All Types</em>
                                        </MenuItem>
                                        <MenuItem value="command" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Command</MenuItem>
                                        <MenuItem value="script" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Script</MenuItem>
                                        <MenuItem value="file_transfer" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>File Transfer</MenuItem>
                                        <MenuItem value="composite" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Composite</MenuItem>
                                    </Select>
                                </FormControl>
                            </TableCell>
                            <TableCell sx={{ padding: '4px 8px' }}>
                                <FormControl size="small" fullWidth>
                                    <Select
                                        value={columnFilters.status || ''}
                                        onChange={(e) => handleColumnFilterChange('status', e.target.value)}
                                        displayEmpty
                                        sx={{
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
                                            <em>All Status</em>
                                        </MenuItem>
                                        <MenuItem value="pending" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Pending</MenuItem>
                                        <MenuItem value="running" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Running</MenuItem>
                                        <MenuItem value="completed" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Completed</MenuItem>
                                        <MenuItem value="failed" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Failed</MenuItem>
                                        <MenuItem value="cancelled" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Cancelled</MenuItem>
                                        <MenuItem value="scheduled" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Scheduled</MenuItem>
                                    </Select>
                                </FormControl>
                            </TableCell>
                            <TableCell sx={{ padding: '4px 8px' }}>
                                <TextField
                                    size="small"
                                    placeholder="Filter created..."
                                    value={columnFilters.created_at || ''}
                                    onChange={(e) => handleColumnFilterChange('created_at', e.target.value)}
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
                                    placeholder="Filter last run..."
                                    value={columnFilters.last_run || ''}
                                    onChange={(e) => handleColumnFilterChange('last_run', e.target.value)}
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
                                    placeholder="Filter scheduled..."
                                    value={columnFilters.scheduled_at || ''}
                                    onChange={(e) => handleColumnFilterChange('scheduled_at', e.target.value)}
                                    sx={{
                                        '& .MuiInputBase-input': {
                                            fontFamily: 'monospace',
                                            fontSize: '0.75rem',
                                            padding: '2px 4px'
                                        }
                                    }}
                                />
                            </TableCell>
                            <TableCell sx={{ padding: '4px 8px' }} align="center">
                                {/* No filter for Actions column */}
                            </TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {filteredAndSortedJobs.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={9} align="center" className="no-data-cell">
                                    <Typography variant="body2" color="text.secondary">
                                        {jobs.length === 0 ? 'No jobs found. Create your first job to get started!' : 'No jobs match your search criteria.'}
                                    </Typography>
                                </TableCell>
                            </TableRow>
                        ) : (
                            paginatedJobs.map((job) => {
                                const createdTime = formatDateWithBothTimezones(job.created_at);
                                const lastRunTime = formatDateWithBothTimezones(job.last_execution?.started_at);
                                
                                return (
                                <TableRow 
                                    key={job.id} 
                                    className="table-row"
                                    sx={{ 
                                        cursor: 'pointer',
                                        ...getStatusRowStyling(job.status, theme)
                                    }}
                                >
                                    <TableCell className="table-cell" padding="checkbox">
                                        <Checkbox
                                            checked={selectedJobs.has(job.id)}
                                            onChange={(e) => handleSelectJob(job.id, e.target.checked)}
                                            disabled={job.status !== 'running'}
                                            size="small"
                                            onClick={(e) => e.stopPropagation()}
                                        />
                                    </TableCell>
                                    
                                    <TableCell sx={getTableCellStyle(true)}>
                                        {job.name}
                                    </TableCell>
                                    
                                    <TableCell sx={getTableCellStyle()}>
                                        {job.job_serial || `ID-${job.id}`}
                                    </TableCell>
                                    
                                    <TableCell sx={getTableCellStyle()}>
                                        {getJobTypeLabel(job.job_type)}
                                    </TableCell>
                                    
                                    <TableCell sx={getTableCellStyle()}>
                                        {job.status}
                                    </TableCell>
                                    
                                    <TableCell sx={getTableCellStyle()}>
                                        {createdTime.local}
                                    </TableCell>
                                    
                                    <TableCell sx={getTableCellStyle()}>
                                        {lastRunTime.local || 'Never'}
                                    </TableCell>
                                    
                                    <TableCell sx={getTableCellStyle()}>
                                        {job.scheduled_at ? formatDateWithBothTimezones(job.scheduled_at).local : 'Not scheduled'}
                                    </TableCell>
                                    
                                    <TableCell className="table-cell" align="center">
                                        <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center' }}>

                                            
                                            {/* Schedule Action */}
                                            {(job.status === 'draft' || job.status === 'failed') && (
                                                <Tooltip title="Schedule Job">
                                                    <IconButton 
                                                        className="btn-icon"
                                                        size="small" 
                                                        onClick={(e) => handleScheduleClick(job, e)}
                                                        color="warning"
                                                    >
                                                        <ScheduleIcon fontSize="small" />
                                                    </IconButton>
                                                </Tooltip>
                                            )}
                                            
                                            {/* Terminate Action for Running Jobs */}
                                            {job.status === 'running' && (
                                                <StopAction onClick={(e) => handleTerminateJob(job, e)} />
                                            )}
                                            
                                            {/* View/Edit Actions */}
                                            <ViewDetailsAction onClick={(e) => handleViewHistoryClick(job, e)} />
                                            <EditAction onClick={(e) => handleEditClick(job, e)} />
                                            <DeleteAction onClick={(e) => handleDeleteClick(job, e)} />
                                        </Box>
                                    </TableCell>
                                </TableRow>
                                );
                            })
                        )}
                    </TableBody>
                </Table>
            </TableContainer>

            {/* Compact Pagination */}
            {filteredAndSortedJobs.length > 0 && (
                <TablePagination
                    rowsPerPageOptions={[5, 10, 25, 50]}
                    component="div"
                    count={filteredAndSortedJobs.length}
                    rowsPerPage={rowsPerPage}
                    page={page}
                    onPageChange={handleChangePage}
                    onRowsPerPageChange={handleChangeRowsPerPage}
                    sx={{
                        '& .MuiTablePagination-toolbar': {
                            minHeight: '40px',
                            padding: '0 8px',
                        },
                        '& .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows': {
                            fontSize: '0.75rem',
                        },
                        '& .MuiTablePagination-select': {
                            fontSize: '0.75rem',
                        }
                    }}
                />
            )}

            {/* Termination Dialog */}
            <Dialog open={showTerminateDialog} onClose={() => setShowTerminateDialog(false)} maxWidth="sm" fullWidth>
                <DialogTitle>
                    <Box display="flex" alignItems="center">
                        <WarningIcon color="error" sx={{ mr: 1 }} />
                        Terminate Job{jobsToTerminate.length > 1 ? 's' : ''}
                    </Box>
                </DialogTitle>
                <DialogContent>
                    <Alert severity="warning" sx={{ mb: 2 }}>
                        This will forcefully terminate {jobsToTerminate.length === 1 
                            ? `job "${jobsToTerminate[0]?.name}"` 
                            : `${jobsToTerminate.length} selected jobs`}. 
                        This action cannot be undone and may leave tasks in an incomplete state.
                    </Alert>
                    
                    {jobsToTerminate.length > 1 && (
                        <Box sx={{ mb: 2 }}>
                            <Typography variant="subtitle2" sx={{ mb: 1 }}>Jobs to terminate:</Typography>
                            {jobsToTerminate.map(job => (
                                <Typography key={job.id} variant="body2" sx={{ ml: 2, color: 'text.secondary' }}>
                                    • {job.name} (Serial: {job.job_serial || `ID-${job.id}`})
                                </Typography>
                            ))}
                        </Box>
                    )}
                    
                    <TextField
                        fullWidth
                        label="Termination Reason (Optional)"
                        value={terminateReason}
                        onChange={(e) => setTerminateReason(e.target.value)}
                        placeholder="Enter reason for termination..."
                        multiline
                        rows={2}
                        sx={{ mt: 1 }}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setShowTerminateDialog(false)} disabled={terminateLoading}>
                        Cancel
                    </Button>
                    <Button
                        onClick={executeTermination}
                        color="error"
                        variant="contained"
                        disabled={terminateLoading}
                        startIcon={terminateLoading ? <CircularProgress size={16} /> : <StopIcon />}
                    >
                        {terminateLoading ? 'Terminating...' : `Terminate ${jobsToTerminate.length > 1 ? `${jobsToTerminate.length} Jobs` : 'Job'}`}
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Modals */}
            {showScheduleModal && jobToSchedule && (
                <JobScheduleModal
                    job={jobToSchedule}
                    onClose={() => {
                        setShowScheduleModal(false);
                        setJobToSchedule(null);
                    }}
                    onSubmit={handleScheduleSubmit}
                />
            )}


            
            {showEditModal && jobToEdit && (
                <JobEditModal
                    open={showEditModal}
                    job={jobToEdit}
                    onClose={() => {
                        setShowEditModal(false);
                        setJobToEdit(null);
                    }}
                    onSubmit={handleEditSubmit}
                />
            )}

            {showHistoryModal && jobToViewHistory && (
                <JobExecutionHistoryModal
                    open={showHistoryModal}
                    job={jobToViewHistory}
                    onClose={() => {
                        setShowHistoryModal(false);
                        setJobToViewHistory(null);
                    }}
                />
            )}
        </Box>
    );
};

export default React.memo(JobList);
