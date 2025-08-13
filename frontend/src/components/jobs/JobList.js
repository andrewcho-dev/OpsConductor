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
  Chip,
  IconButton,
  Tooltip,
  Typography,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
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
  Search as SearchIcon,
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

const JobList = ({ 
    jobs, 
    onExecuteJob, 
    onScheduleJob, 
    onUpdateJob,
    onDeleteJob
}) => {
    const { token } = useAuth();
    const { addAlert } = useAlert();
    const [page, setPage] = useState(0);
    const [rowsPerPage, setRowsPerPage] = useState(10);
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [typeFilter, setTypeFilter] = useState('all');
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

    // Filtering, search, and sort logic
    const filteredJobs = useMemo(() => {
        const filtered = jobs.filter(job => {
            const matchesSearch = job.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                                job.job_type.toLowerCase().includes(searchTerm.toLowerCase());
            const matchesStatus = statusFilter === 'all' || job.status === statusFilter;
            const matchesType = typeFilter === 'all' || job.job_type === typeFilter;
            
            return matchesSearch && matchesStatus && matchesType;
        });

        // Sort the filtered results
        return filtered.sort((a, b) => {
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
    }, [jobs, searchTerm, statusFilter, typeFilter, sortField, sortDirection]);

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
            const runningJobIds = filteredJobs
                .filter(job => job.status === 'running')
                .map(job => job.id);
            setSelectedJobs(new Set(runningJobIds));
        } else {
            setSelectedJobs(new Set());
        }
    }, [filteredJobs]);

    const handleTerminateJob = useCallback(async (job, e) => {
        e.stopPropagation();
        setJobsToTerminate([job]);
        setShowTerminateDialog(true);
        setTerminateReason('');
    }, []);

    const handleBulkTerminate = useCallback(() => {
        const jobsToTerminateList = filteredJobs.filter(job => selectedJobs.has(job.id));
        setJobsToTerminate(jobsToTerminateList);
        setShowTerminateDialog(true);
        setTerminateReason('');
    }, [filteredJobs, selectedJobs]);

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

    const getStatusColor = useCallback((status) => {
        switch (status) {
            case 'draft': return 'default';
            case 'scheduled': return 'info';
            case 'running': return 'primary';
            case 'completed': return 'success';
            case 'failed': return 'error';
            case 'cancelled': return 'secondary';
            case 'paused': return 'warning';
            default: return 'default';
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

    // Paginated jobs - memoized for performance
    const paginatedJobs = useMemo(() => {
        return filteredJobs.slice(
            page * rowsPerPage,
            page * rowsPerPage + rowsPerPage
        );
    }, [filteredJobs, page, rowsPerPage]);

    // Computed values for bulk operations
    const runningJobs = useMemo(() => {
        return filteredJobs.filter(job => job.status === 'running');
    }, [filteredJobs]);

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
            {/* Compact Search and Filters */}
            <div className="filters-container">
                <TextField
                    className="search-field form-control-compact"
                    placeholder="Search jobs..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    InputProps={{
                        startAdornment: (
                            <InputAdornment position="start">
                                <SearchIcon fontSize="small" />
                            </InputAdornment>
                        ),
                    }}
                    size="small"
                />
                
                <FormControl className="filter-item form-control-compact" size="small">
                    <InputLabel>Status</InputLabel>
                    <Select
                        value={statusFilter}
                        label="Status"
                        onChange={(e) => setStatusFilter(e.target.value)}
                    >
                        <MenuItem value="all">All Status</MenuItem>
                        <MenuItem value="draft">Draft</MenuItem>
                        <MenuItem value="scheduled">Scheduled</MenuItem>
                        <MenuItem value="running">Running</MenuItem>
                        <MenuItem value="completed">Completed</MenuItem>
                        <MenuItem value="failed">Failed</MenuItem>
                        <MenuItem value="cancelled">Cancelled</MenuItem>
                        <MenuItem value="paused">Paused</MenuItem>
                    </Select>
                </FormControl>
                
                <FormControl className="filter-item form-control-compact" size="small">
                    <InputLabel>Type</InputLabel>
                    <Select
                        value={typeFilter}
                        label="Type"
                        onChange={(e) => setTypeFilter(e.target.value)}
                    >
                        <MenuItem value="all">All Types</MenuItem>
                        <MenuItem value="command">Command</MenuItem>
                        <MenuItem value="script">Script</MenuItem>
                        <MenuItem value="file_transfer">File Transfer</MenuItem>
                        <MenuItem value="composite">Composite</MenuItem>
                    </Select>
                </FormControl>

                {/* Bulk Terminate Button */}
                {selectedJobs.size > 0 && (
                    <Button
                        variant="contained"
                        color="error"
                        size="small"
                        startIcon={<StopIcon fontSize="small" />}
                        onClick={handleBulkTerminate}
                        sx={{ ml: 2 }}
                    >
                        Terminate Selected ({selectedJobs.size})
                    </Button>
                )}
            </div>

            {/* Compact Table */}
            <TableContainer className="table-container">
                <Table size="small" className="compact-table">
                    <TableHead>
                        <TableRow className="table-header-row">
                            <TableCell className="table-header-cell" padding="checkbox">
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
                            <SortableHeader field="name">Job Name</SortableHeader>
                            <SortableHeader field="job_serial">Job Serial</SortableHeader>
                            <TableCell className="table-header-cell">Type</TableCell>
                            <TableCell className="table-header-cell">Status</TableCell>
                            <TableCell className="table-header-cell">Created</TableCell>
                            <TableCell className="table-header-cell">Last Run</TableCell>
                            <TableCell className="table-header-cell">Next Scheduled</TableCell>
                            <TableCell className="table-header-cell" align="center">Actions</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {filteredJobs.length === 0 ? (
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
                                    sx={{ cursor: 'pointer' }}
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
                                    
                                    <TableCell className="table-cell">
                                        <Typography variant="body2" sx={{ fontWeight: 500, fontSize: '0.75rem' }}>
                                            {job.name}
                                        </Typography>
                                    </TableCell>
                                    
                                    <TableCell className="table-cell">
                                        <Typography variant="body2" sx={{ 
                                            fontWeight: 600, 
                                            fontSize: '0.8rem',
                                            fontFamily: 'monospace',
                                            color: 'primary.main'
                                        }}>
                                            {job.job_serial || `ID-${job.id}`}
                                        </Typography>
                                    </TableCell>
                                    
                                    <TableCell className="table-cell">
                                        <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                                            {getJobTypeLabel(job.job_type)}
                                        </Typography>
                                    </TableCell>
                                    
                                    <TableCell className="table-cell">
                                        <Chip 
                                            label={job.status} 
                                            color={getStatusColor(job.status)}
                                            size="small"
                                            sx={{ fontSize: '0.65rem', height: '20px' }}
                                        />
                                    </TableCell>
                                    
                                    <TableCell className="table-cell">
                                        <Box>
                                            <Typography variant="body2" sx={{ fontSize: '0.7rem', fontWeight: 600, color: 'primary.main', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                                <LocalTimeIcon sx={{ fontSize: 12 }} />
                                                {createdTime.local}
                                            </Typography>
                                            <Typography variant="body2" sx={{ fontSize: '0.7rem', fontWeight: 500, color: 'text.secondary', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                                <UtcTimeIcon sx={{ fontSize: 12 }} />
                                                {createdTime.utc} UTC
                                            </Typography>
                                        </Box>
                                    </TableCell>
                                    
                                    <TableCell className="table-cell">
                                        <Box>
                                            <Typography variant="body2" sx={{ fontSize: '0.7rem', fontWeight: 600, color: 'primary.main', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                                <LocalTimeIcon sx={{ fontSize: 12 }} />
                                                {lastRunTime.local}
                                            </Typography>
                                            <Typography variant="body2" sx={{ fontSize: '0.7rem', fontWeight: 500, color: 'text.secondary', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                                <UtcTimeIcon sx={{ fontSize: 12 }} />
                                                {lastRunTime.utc} UTC
                                            </Typography>
                                        </Box>
                                    </TableCell>
                                    
                                    <TableCell className="table-cell">
                                        {job.scheduled_at ? (
                                            <Box>
                                                <Typography variant="body2" sx={{ fontSize: '0.7rem', fontWeight: 600, color: 'primary.main', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                                    <LocalTimeIcon sx={{ fontSize: 12 }} />
                                                    {formatDateWithBothTimezones(job.scheduled_at).local}
                                                </Typography>
                                                <Typography variant="body2" sx={{ fontSize: '0.7rem', fontWeight: 500, color: 'text.secondary', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                                    <UtcTimeIcon sx={{ fontSize: 12 }} />
                                                    {formatDateWithBothTimezones(job.scheduled_at).utc} UTC
                                                </Typography>
                                            </Box>
                                        ) : (
                                            <Typography variant="body2" sx={{ fontSize: '0.7rem', color: 'text.secondary' }}>
                                                Not scheduled
                                            </Typography>
                                        )}
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
                                                <Tooltip title="Terminate Running Job">
                                                    <IconButton 
                                                        className="btn-icon"
                                                        size="small" 
                                                        onClick={(e) => handleTerminateJob(job, e)}
                                                        color="error"
                                                    >
                                                        <StopIcon fontSize="small" />
                                                    </IconButton>
                                                </Tooltip>
                                            )}
                                            
                                            {/* View/Edit Actions */}
                                            <Tooltip title="View Execution History">
                                                <IconButton 
                                                    className="btn-icon"
                                                    size="small" 
                                                    onClick={(e) => handleViewHistoryClick(job, e)}
                                                    color="info"
                                                >
                                                    <VisibilityIcon fontSize="small" />
                                                </IconButton>
                                            </Tooltip>
                                            
                                            <Tooltip title="Edit Job">
                                                <IconButton 
                                                    className="btn-icon"
                                                    size="small" 
                                                    onClick={(e) => handleEditClick(job, e)}
                                                    color="primary"
                                                >
                                                    <EditIcon fontSize="small" />
                                                </IconButton>
                                            </Tooltip>
                                            
                                            <Tooltip title="Delete Job">
                                                <IconButton 
                                                    className="btn-icon"
                                                    size="small" 
                                                    onClick={(e) => handleDeleteClick(job, e)}
                                                    color="error"
                                                >
                                                    <DeleteIcon fontSize="small" />
                                                </IconButton>
                                            </Tooltip>
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
            {filteredJobs.length > 0 && (
                <TablePagination
                    rowsPerPageOptions={[5, 10, 25, 50]}
                    component="div"
                    count={filteredJobs.length}
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
