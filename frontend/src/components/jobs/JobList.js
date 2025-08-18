/**
 * Job List - Standardized Data Table
 * Displays jobs using standardized pagination and scrolling patterns.
 * Follows the same approach as other transformed data tables in the system.
 */
import React, { useState, useMemo, useCallback } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  TableHead,
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  Paper,
  Pagination,
  TextField,
  IconButton,
  FormControl,
  Select,
  MenuItem
} from '@mui/material';
import {
  Schedule as ScheduleIcon,
  Stop as StopIcon,
  Warning as WarningIcon,
  ArrowUpward as ArrowUpwardIcon,
  ArrowDownward as ArrowDownwardIcon
} from '@mui/icons-material';

import JobScheduleModal from './JobScheduleModal';
import JobEditModal from './JobEditModal';
import JobExecutionHistoryModal from './JobExecutionHistoryModal';
import { formatLocalDateTime } from '../../utils/timeUtils';
import { useAuth } from '../../contexts/AuthContext';
import { useAlert } from '../layout/BottomStatusBar';
import { ViewDetailsAction, EditAction, DeleteAction, PlayAction, StopAction } from '../common/StandardActions';
import { getStatusRowStyling, getTableCellStyle } from '../../utils/tableUtils';
import { useTheme } from '@mui/material/styles';
import '../../styles/dashboard.css';

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
    
    // State for filtering, sorting, and pagination
    const [columnFilters, setColumnFilters] = useState({});
    const [sortField, setSortField] = useState('scheduled_at');
    const [sortDirection, setSortDirection] = useState('desc');
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(25);

    // Modal states
    const [showScheduleModal, setShowScheduleModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [showHistoryModal, setShowHistoryModal] = useState(false);
    const [jobToSchedule, setJobToSchedule] = useState(null);
    const [jobToEdit, setJobToEdit] = useState(null);
    const [jobToViewHistory, setJobToViewHistory] = useState(null);
    
    // Termination states
    const [showTerminateDialog, setShowTerminateDialog] = useState(false);
    const [jobsToTerminate, setJobsToTerminate] = useState([]);
    const [terminateReason, setTerminateReason] = useState('');
    const [terminateLoading, setTerminateLoading] = useState(false);

    // Helper functions
    const formatJobStatus = useCallback((status) => {
        if (!status) return 'Unknown';
        // Remove "JobStatus." prefix if present
        return status.replace(/^JobStatus\./, '');
    }, []);

    const formatDateWithBothTimezones = useCallback((dateString) => {
        if (!dateString) return { local: 'Never', utc: 'Never' };
        
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) {
                return { local: 'Invalid Date', utc: 'Invalid Date' };
            }
            
            const formatOptions = {
                month: '2-digit',
                day: '2-digit', 
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: true
            };
            
            const localFormatted = date.toLocaleString('en-US', formatOptions);
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

    // Filter and sort jobs
    const filteredAndSortedJobs = useMemo(() => {
        if (!jobs || !Array.isArray(jobs)) {
            return [];
        }

        // Apply column filters
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
                return true;
            }
        });

        // Sort the filtered results with multi-level sorting
        const sorted = filtered.sort((a, b) => {
            // If user clicked a column header, use single-field sorting
            if (sortField !== 'scheduled_at' || sortDirection !== 'desc') {
                return applySingleFieldSort(a, b, sortField, sortDirection);
            }
            
            // Default multi-level sorting: scheduled_at (desc) then last_execution (desc)
            
            // Primary sort: Scheduled At (descending - most recent scheduled time first)
            const aScheduled = a.scheduled_at;
            const bScheduled = b.scheduled_at;
            
            // Handle null scheduled dates (put unscheduled jobs at the end)
            if (!aScheduled && !bScheduled) {
                // Both unscheduled, sort by last run (descending - most recent first)
                return sortByLastExecution(a, b, 'desc');
            }
            if (!aScheduled) return 1; // a goes to end
            if (!bScheduled) return -1; // b goes to end
            
            const aScheduledDate = new Date(aScheduled);
            const bScheduledDate = new Date(bScheduled);
            
            // Handle invalid scheduled dates
            if (isNaN(aScheduledDate.getTime()) && isNaN(bScheduledDate.getTime())) {
                return sortByLastExecution(a, b, 'desc');
            }
            if (isNaN(aScheduledDate.getTime())) return 1;
            if (isNaN(bScheduledDate.getTime())) return -1;
            
            // Compare scheduled dates (descending - most recent first)
            const scheduledDiff = bScheduledDate - aScheduledDate;
            if (scheduledDiff !== 0) return scheduledDiff;
            
            // Secondary sort: Last Run (descending - most recent first)
            return sortByLastExecution(a, b, 'desc');
        });
        
        // Helper function for single field sorting (when user clicks column headers)
        function applySingleFieldSort(a, b, field, direction) {
            let aValue = a[field];
            let bValue = b[field];
            
            // Handle null/undefined values
            if (aValue == null && bValue == null) return 0;
            if (aValue == null) return direction === 'asc' ? 1 : -1;
            if (bValue == null) return direction === 'asc' ? -1 : 1;
            
            // Handle date fields
            if (field === 'created_at' || field === 'updated_at' || field === 'scheduled_at') {
                const aDate = new Date(aValue);
                const bDate = new Date(bValue);
                
                // Handle invalid dates
                if (isNaN(aDate.getTime()) && isNaN(bDate.getTime())) return 0;
                if (isNaN(aDate.getTime())) return direction === 'asc' ? 1 : -1;
                if (isNaN(bDate.getTime())) return direction === 'asc' ? -1 : 1;
                
                return direction === 'asc' ? aDate - bDate : bDate - aDate;
            }
            
            // Handle last_execution field (nested object)
            if (field === 'last_execution') {
                return sortByLastExecution(a, b, direction);
            }
            
            // Handle numeric fields
            if (field === 'priority' || field === 'timeout' || field === 'retry_count') {
                const aNum = Number(aValue);
                const bNum = Number(bValue);
                return direction === 'asc' ? aNum - bNum : bNum - aNum;
            }
            
            // Handle string fields
            const aStr = String(aValue).toLowerCase();
            const bStr = String(bValue).toLowerCase();
            
            if (direction === 'asc') {
                return aStr.localeCompare(bStr);
            } else {
                return bStr.localeCompare(aStr);
            }
        }
        
        // Helper function for sorting by last execution
        function sortByLastExecution(a, b, direction) {
            const aExec = a.last_execution?.started_at;
            const bExec = b.last_execution?.started_at;
            
            // Handle null executions
            if (!aExec && !bExec) return 0;
            if (!aExec) return direction === 'asc' ? 1 : -1;
            if (!bExec) return direction === 'asc' ? -1 : 1;
            
            const aDate = new Date(aExec);
            const bDate = new Date(bExec);
            
            return direction === 'asc' ? aDate - bDate : bDate - aDate;
        }
        
        return sorted;
    }, [jobs, columnFilters, sortField, sortDirection, formatDateWithBothTimezones]);

    // Pagination
    const paginatedJobs = useMemo(() => {
        const startIndex = (currentPage - 1) * pageSize;
        return filteredAndSortedJobs.slice(startIndex, startIndex + pageSize);
    }, [filteredAndSortedJobs, currentPage, pageSize]);

    const totalPages = Math.ceil(filteredAndSortedJobs.length / pageSize);

    // Event handlers
    const handleColumnFilterChange = useCallback((columnKey, value) => {
        setColumnFilters(prev => ({
            ...prev,
            [columnKey]: value
        }));
        setCurrentPage(1); // Reset to first page when filtering
    }, []);

    const handleSort = (field) => {
        if (sortField === field) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortDirection('asc');
        }
    };

    const handlePageChange = useCallback((event, page) => {
        setCurrentPage(page);
    }, []);

    // Job action handlers
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



    // Termination handlers
    const handleTerminateJob = useCallback(async (job, e) => {
        e.stopPropagation();
        setJobsToTerminate([job]);
        setShowTerminateDialog(true);
        setTerminateReason('');
    }, []);



    const executeTermination = useCallback(async () => {
        setTerminateLoading(true);
        let successCount = 0;
        let errorCount = 0;

        for (const job of jobsToTerminate) {
            try {
                const response = await fetch(`/api/v2/jobs/${job.id}/terminate`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`,
                    },
                    body: JSON.stringify({
                        reason: terminateReason || 'Manual termination'
                    })
                });

                if (response.ok) {
                    successCount++;
                } else {
                    errorCount++;
                }
            } catch (error) {
                errorCount++;
            }
        }

        setTerminateLoading(false);
        setShowTerminateDialog(false);
        setJobsToTerminate([]);
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

    // Computed values
    const runningJobs = useMemo(() => {
        return filteredAndSortedJobs.filter(job => job.status === 'running');
    }, [filteredAndSortedJobs]);

    // Sortable header component
    const SortableHeader = ({ field, children, ...props }) => (
        <TableCell 
            {...props}
            onClick={() => handleSort(field)}
            sx={{ 
                cursor: 'pointer', 
                userSelect: 'none',
                position: 'relative',
                '&:hover': { 
                    backgroundColor: 'rgba(0, 0, 0, 0.04)',
                    '& .sort-hint': { opacity: 0.3 }
                }
            }}
        >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                {children}
                {sortField === field ? (
                    sortDirection === 'asc' ? 
                        <ArrowUpwardIcon sx={{ fontSize: 14, color: 'primary.main' }} /> : 
                        <ArrowDownwardIcon sx={{ fontSize: 14, color: 'primary.main' }} />
                ) : (
                    <Box 
                        className="sort-hint"
                        sx={{ 
                            opacity: 0, 
                            fontSize: 12, 
                            color: 'text.secondary',
                            transition: 'opacity 0.2s'
                        }}
                    >
                        ↕
                    </Box>
                )}
            </Box>
        </TableCell>
    );

    // Calculate pagination
    const totalJobs = filteredAndSortedJobs.length;
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;

    return (
        <div className="table-content-area">


            <TableContainer 
                component={Paper} 
                variant="outlined"
                className="standard-table-container"
            >
                <Table size="small">
                    <TableHead>
                        {/* Column Headers Row */}
                        <TableRow sx={{ backgroundColor: 'grey.100' }}>
                            <SortableHeader field="name" className="standard-table-header">Job Name</SortableHeader>
                            <SortableHeader field="job_serial" className="standard-table-header">Job Serial</SortableHeader>
                            <SortableHeader field="job_type" className="standard-table-header">Type</SortableHeader>
                            <SortableHeader field="status" className="standard-table-header">Status</SortableHeader>
                            <SortableHeader field="created_at" className="standard-table-header">Created</SortableHeader>
                            <SortableHeader field="last_execution" className="standard-table-header">Last Run</SortableHeader>
                            <SortableHeader field="scheduled_at" className="standard-table-header">Next Scheduled</SortableHeader>
                            <TableCell className="standard-table-header">Actions</TableCell>
                        </TableRow>
                        
                        {/* Column Filters Row */}
                        <TableRow sx={{ backgroundColor: 'grey.50' }}>
                            <TableCell className="standard-filter-cell">
                                <TextField
                                    size="small"
                                    placeholder="Filter name..."
                                    value={columnFilters.name || ''}
                                    onChange={(e) => handleColumnFilterChange('name', e.target.value)}
                                    className="standard-filter-input"
                                />
                            </TableCell>
                            <TableCell className="standard-filter-cell">
                                <TextField
                                    size="small"
                                    placeholder="Filter serial..."
                                    value={columnFilters.job_serial || ''}
                                    onChange={(e) => handleColumnFilterChange('job_serial', e.target.value)}
                                    className="standard-filter-input"
                                />
                            </TableCell>
                            <TableCell className="standard-filter-cell">
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
                                        <MenuItem value="">
                                            <em>All Types</em>
                                        </MenuItem>
                                        <MenuItem value="command">Command</MenuItem>
                                        <MenuItem value="script">Script</MenuItem>
                                        <MenuItem value="file_transfer">File Transfer</MenuItem>
                                        <MenuItem value="composite">Composite</MenuItem>
                                    </Select>
                                </FormControl>
                            </TableCell>
                            <TableCell className="standard-filter-cell">
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
                                        <MenuItem value="">
                                            <em>All Status</em>
                                        </MenuItem>
                                        <MenuItem value="pending">Pending</MenuItem>
                                        <MenuItem value="running">Running</MenuItem>
                                        <MenuItem value="completed">Completed</MenuItem>
                                        <MenuItem value="failed">Failed</MenuItem>
                                        <MenuItem value="cancelled">Cancelled</MenuItem>
                                        <MenuItem value="scheduled">Scheduled</MenuItem>
                                    </Select>
                                </FormControl>
                            </TableCell>
                            <TableCell className="standard-filter-cell">
                                <TextField
                                    size="small"
                                    placeholder="Filter created..."
                                    value={columnFilters.created_at || ''}
                                    onChange={(e) => handleColumnFilterChange('created_at', e.target.value)}
                                    className="standard-filter-input"
                                />
                            </TableCell>
                            <TableCell className="standard-filter-cell">
                                <TextField
                                    size="small"
                                    placeholder="Filter last run..."
                                    value={columnFilters.last_run || ''}
                                    onChange={(e) => handleColumnFilterChange('last_run', e.target.value)}
                                    className="standard-filter-input"
                                />
                            </TableCell>
                            <TableCell className="standard-filter-cell">
                                <TextField
                                    size="small"
                                    placeholder="Filter scheduled..."
                                    value={columnFilters.scheduled_at || ''}
                                    onChange={(e) => handleColumnFilterChange('scheduled_at', e.target.value)}
                                    className="standard-filter-input"
                                />
                            </TableCell>
                            <TableCell className="standard-filter-cell"></TableCell>
                        </TableRow>
                        
                        {/* Data Rows */}
                        {filteredAndSortedJobs.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={9} align="center" sx={{ 
                                    padding: '40px',
                                    fontFamily: 'monospace',
                                    fontSize: '0.75rem',
                                    color: 'text.secondary'
                                }}>
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
                                        sx={{ 
                                            cursor: 'pointer',
                                            ...getStatusRowStyling(job.status, theme),
                                            '&:hover': {
                                                backgroundColor: theme.palette.action.hover
                                            }
                                        }}
                                    >
                                        {/* Job Name */}
                                        <TableCell className="standard-table-cell" sx={{ fontWeight: 'bold' }}>
                                            {job.name}
                                        </TableCell>
                                        
                                        {/* Job Serial */}
                                        <TableCell className="standard-table-cell">
                                            {job.job_serial || `ID-${job.id}`}
                                        </TableCell>
                                        
                                        {/* Type */}
                                        <TableCell className="standard-table-cell">
                                            {getJobTypeLabel(job.job_type)}
                                        </TableCell>
                                        
                                        {/* Status */}
                                        <TableCell className="standard-table-cell">
                                            {formatJobStatus(job.status)}
                                        </TableCell>
                                        
                                        {/* Created */}
                                        <TableCell className="standard-table-cell">
                                            {createdTime.local}
                                        </TableCell>
                                        
                                        {/* Last Run */}
                                        <TableCell className="standard-table-cell">
                                            {lastRunTime.local || 'Never'}
                                        </TableCell>
                                        
                                        {/* Next Scheduled */}
                                        <TableCell className="standard-table-cell">
                                            {job.scheduled_at ? formatDateWithBothTimezones(job.scheduled_at).local : 'Not scheduled'}
                                        </TableCell>
                                        
                                        {/* Actions */}
                                        <TableCell className="standard-table-cell" align="center">
                                            <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center' }}>
                                                {/* Execute Action */}
                                                {(job.status === 'draft' || job.status === 'failed') && (
                                                    <PlayAction onClick={(e) => handleExecuteClick(job, e)} />
                                                )}
                                                
                                                {/* Schedule Action */}
                                                {(job.status === 'draft' || job.status === 'failed') && (
                                                    <StopAction 
                                                        icon={<ScheduleIcon fontSize="small" />}
                                                        tooltip="Schedule Job"
                                                        onClick={(e) => handleScheduleClick(job, e)}
                                                        color="warning"
                                                    />
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
                    </TableHead>
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
                            setCurrentPage(1);
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
                {filteredAndSortedJobs.length > pageSize && (
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
                
                {/* Show pagination info */}
                <Typography variant="body2" className="standard-pagination-info">
                    Showing {startIndex + 1}-{Math.min(endIndex, totalJobs)} of {totalJobs} jobs
                </Typography>
            </div>

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
                        {terminateLoading ? 'Terminating...' : 'Terminate'}
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
        </div>
    );
};

export default React.memo(JobList);