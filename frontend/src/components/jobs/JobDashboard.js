import React, { useState, useEffect } from 'react';
import {
  Typography,
  Button,
  IconButton,
  Tooltip,
  CircularProgress,
  Box,
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Work as WorkIcon,
  Schedule as ScheduleIcon,
  PlayArrow as PlayArrowIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Pause as PauseIcon,
  Autorenew as AutorenewIcon,
  PauseCircleOutline as PauseAutoIcon,
} from '@mui/icons-material';

import JobCreateModal from './JobCreateModal';
import JobList from './JobList';
import JobSafetyControls from './JobSafetyControls';
import { useSessionAuth } from '../../contexts/SessionAuthContext';
import { useAlert } from '../layout/BottomStatusBar';
import { apiService } from '../../services/apiService';
import '../../styles/dashboard.css';

const JobDashboard = () => {
    const { addAlert } = useAlert();
    const [jobs, setJobs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [workerStats, setWorkerStats] = useState({ active: 0, total: 0 });
    const [autoRefresh, setAutoRefresh] = useState(true);
    const [refreshInterval, setRefreshInterval] = useState(30000); // 30 seconds
    const [countdown, setCountdown] = useState(30); // Countdown in seconds
    const { token } = useSessionAuth();

    useEffect(() => {
        if (token) {
            fetchJobs();
            fetchWorkerStats();
        }
    }, [token]);

    const fetchJobs = async () => {
        try {
            setLoading(true);
            
            const response = await apiService.get('/jobs/');
            setJobs(response.data || []);
            addAlert(`Loaded ${response.data?.length || 0} jobs successfully`, 'success', 3000);
        } catch (error) {
            console.error('Error fetching jobs:', error);
            if (error.response?.status === 401) {
                addAlert('Authentication failed - please log in again', 'error', 0);
            } else {
                addAlert(`Error fetching jobs: ${error.message}`, 'error', 0);
            }
        } finally {
            setLoading(false);
        }
    };

    const fetchWorkerStats = async () => {
        try {
            // TODO: Update to use v2 system health endpoint when available
            // const response = await authService.api.get('/v2/system/health');
            // For now, set default worker stats
            setWorkerStats({ active: 1, total: 1 });
        } catch (error) {
            // Silently fail - monitoring is optional
            console.log('Worker stats unavailable:', error.message);
            setWorkerStats({ active: 0, total: 0 });
        }
    };

    // Gentle refresh - only updates changed data without showing loading state
    const gentleRefresh = async () => {
        try {
            const response = await apiService.get('/jobs/');
            const newJobs = response.data || [];
            
            // Only update if data has actually changed
            setJobs(prevJobs => {
                const hasChanges = JSON.stringify(prevJobs) !== JSON.stringify(newJobs);
                return hasChanges ? newJobs : prevJobs;
            });
            
            // Also refresh worker stats silently
            fetchWorkerStats();
        } catch (error) {
            // Silently fail for gentle refresh - don't show error alerts
            console.log('Gentle refresh failed:', error.message);
        }
    };

    // Auto-refresh effect
    useEffect(() => {
        if (!autoRefresh || !token) {
            setCountdown(0);
            return;
        }

        // Reset countdown when autoRefresh starts
        setCountdown(Math.floor(refreshInterval / 1000));

        const refreshIntervalId = setInterval(() => {
            gentleRefresh();
            setCountdown(Math.floor(refreshInterval / 1000)); // Reset countdown after refresh
        }, refreshInterval);

        return () => clearInterval(refreshIntervalId);
    }, [autoRefresh, refreshInterval, token]);

    // Countdown effect - runs every second when autoRefresh is enabled
    useEffect(() => {
        if (!autoRefresh || countdown <= 0) return;

        const countdownIntervalId = setInterval(() => {
            setCountdown(prev => Math.max(0, prev - 1));
        }, 1000);

        return () => clearInterval(countdownIntervalId);
    }, [autoRefresh, countdown]);

    const handleCreateJob = async (jobData, scheduleConfig) => {
        try {
            // First create the job
            const response = await apiService.post('/jobs/', jobData);
            const newJob = response.data;
            setJobs(prevJobs => [newJob, ...prevJobs]);
            
            // If there's advanced schedule configuration, create the schedule
            if (scheduleConfig && scheduleConfig.scheduleType !== 'once') {
                try {
                    // Create new schedule - transform frontend format to API format
                    // IMPORTANT: The backend API expects camelCase field names for the request body
                    const scheduleData = {
                        job_id: newJob.id,
                        schedule_type: scheduleConfig.scheduleType,
                        enabled: true,
                        timezone: scheduleConfig.timezone || 'UTC',
                        description: `Auto-created schedule for job: ${newJob.name}`
                    };
                    
                    // Add schedule-specific fields based on schedule type
                    if (scheduleConfig.scheduleType === 'once' && scheduleConfig.executeAt) {
                        // Backend expects executeAt (camelCase)
                        scheduleData.executeAt = scheduleConfig.executeAt;
                    } 
                    else if (scheduleConfig.scheduleType === 'recurring') {
                        // Backend expects recurringType (camelCase)
                        scheduleData.recurringType = scheduleConfig.recurringType;
                        scheduleData.interval = scheduleConfig.interval || 1;
                        
                        if (scheduleConfig.startDate) {
                            // Combine startDate and startTime for the first occurrence
                            const startDate = scheduleConfig.startDate;
                            const startTime = scheduleConfig.startTime || '00:00';
                            
                            // Create a proper ISO string for the backend
                            const dateTimeStr = `${startDate}T${startTime}`;
                            const dateObj = new Date(dateTimeStr);
                            scheduleData.executeAt = dateObj.toISOString();
                        }
                        
                        if (!['minutes', 'hours'].includes(scheduleConfig.recurringType)) {
                            scheduleData.time = scheduleConfig.time || '09:00';
                        }
                        
                        if (scheduleConfig.recurringType === 'weekly' && scheduleConfig.daysOfWeek) {
                            // Backend expects daysOfWeek (camelCase)
                            scheduleData.daysOfWeek = Array.isArray(scheduleConfig.daysOfWeek) 
                                ? scheduleConfig.daysOfWeek.join(',') 
                                : scheduleConfig.daysOfWeek;
                        }
                        
                        if (scheduleConfig.recurringType === 'monthly' && scheduleConfig.dayOfMonth) {
                            // Backend expects dayOfMonth (camelCase)
                            scheduleData.dayOfMonth = scheduleConfig.dayOfMonth;
                        }
                        
                        // Advanced options
                        if (scheduleConfig.maxExecutions) {
                            // Backend expects maxExecutions (camelCase)
                            scheduleData.maxExecutions = scheduleConfig.maxExecutions;
                        }
                        
                        if (scheduleConfig.endDate) {
                            // Backend expects endDate (camelCase)
                            scheduleData.endDate = scheduleConfig.endDate;
                        }
                    }
                    else if (scheduleConfig.scheduleType === 'cron' && scheduleConfig.cronExpression) {
                        // Backend expects cronExpression (camelCase)
                        scheduleData.cronExpression = scheduleConfig.cronExpression;
                    }
                    
                    console.log('📅 JobDashboard: Sending schedule data to API:', scheduleData);
                    
                    console.log('📤 Creating new schedule');
                    try {
                        // The baseURL already includes /api, so we don't need to include it again
                        const scheduleResponse = await apiService.post('/schedules', scheduleData);
                        console.log('✅ Schedule creation response:', scheduleResponse.status, scheduleResponse.data);
                    } catch (error) {
                        console.error('❌ Schedule creation error:', error);
                        console.error('❌ Error response:', error.response);
                        console.error('❌ Error data:', error.response?.data);
                        throw error; // Re-throw to be caught by the outer catch
                    }
                    addAlert(`Job "${newJob.name}" created with ${scheduleConfig.scheduleType} schedule!`, 'success', 3000);
                } catch (scheduleError) {
                    console.error('Failed to create schedule:', scheduleError);
                    addAlert(`Job "${newJob.name}" created, but schedule setup failed. You can configure it later.`, 'warning', 5000);
                }
            } else {
                addAlert(`Job "${newJob.name}" created successfully!`, 'success', 3000);
            }
            
            setShowCreateModal(false);
            return true;
        } catch (error) {
            addAlert(`Failed to create job: ${error.response?.data?.detail || error.message}`, 'error', 5000);
            return false;
        }
    };

    const handleExecuteJob = async (jobId, targetIds = null) => {
        try {
            const response = await apiService.post(`/jobs/${jobId}/execute`, { target_ids: targetIds });
            fetchJobs(); // Refresh job list
            addAlert(`Job execution started successfully`, 'success', 3000);
            return true;
        } catch (error) {
            addAlert(`Failed to execute job: ${error.response?.data?.detail || error.message}`, 'error', 0);
            return false;
        }
    };

    const handleScheduleJob = async (jobId, scheduledAt) => {
        try {
            // Note: Scheduling moved to separate schedule service in v3
            const response = await apiService.post(`/jobs/${jobId}/schedule`, { scheduled_at: scheduledAt });
            fetchJobs(); // Refresh job list
            return true;
        } catch (error) {
            addAlert(`Failed to schedule job: ${error.response?.data?.detail || error.message}`, 'error', 0);
            return false;
        }
    };



    const handleUpdateJob = async (jobId, updatedJobData, scheduleConfig) => {
        console.log('🔄 JobDashboard: Starting job update...', { jobId, updatedJobData, scheduleConfig });
        try {
            // Separate basic job data from schedule data
            const jobData = {
                name: updatedJobData.name,
                description: updatedJobData.description,
                actions: updatedJobData.actions,
                target_ids: updatedJobData.target_ids,
                scheduled_at: updatedJobData.scheduled_at
            };
            console.log('📤 JobDashboard: Sending job data:', jobData);
            
            // Update the basic job first
            const response = await apiService.put(`/jobs/${jobId}`, jobData);
            console.log('✅ JobDashboard: Job API response:', response.status, response.data);
            
            if (response.status === 200 && response.data) {
                const updatedJob = response.data;
                
                // Handle schedule configuration if present
                console.log('📅 JobDashboard: Schedule config received:', scheduleConfig);
                if (scheduleConfig && scheduleConfig.scheduleType !== 'once') {
                    try {
                        console.log('📅 JobDashboard: Processing schedule config:', scheduleConfig);
                        
                        // First, disable any existing schedules for this job
                        try {
                            console.log('🔍 Fetching schedules for job:', updatedJob.id);
                            // The baseURL already includes /api, so we don't need to include it again
                            const existingSchedulesResponse = await apiService.get(`/schedules?job_id=${updatedJob.id}`);
                            if (existingSchedulesResponse.data && existingSchedulesResponse.data.length > 0) {
                                for (const existingSchedule of existingSchedulesResponse.data) {
                                    console.log('🗑️ Deleting schedule:', existingSchedule.id);
                                    // The baseURL already includes /api, so we don't need to include it again
                                    await apiService.delete(`/schedules/${existingSchedule.id}`);
                                    console.log('🗑️ JobDashboard: Deleted existing schedule:', existingSchedule.id);
                                }
                            }
                        } catch (deleteError) {
                            console.log('⚠️ JobDashboard: No existing schedules to delete or delete failed:', deleteError.message);
                        }
                        
                        // Create new schedule - transform frontend format to API format
                        // IMPORTANT: The backend API expects camelCase field names for the request body
                        console.log('📅 JobDashboard: Creating schedule with config:', JSON.stringify(scheduleConfig, null, 2));
                        
                        const scheduleData = {
                            job_id: updatedJob.id,
                            schedule_type: scheduleConfig.scheduleType,
                            enabled: true,
                            timezone: scheduleConfig.timezone || 'UTC',
                            description: `Updated schedule for job: ${updatedJob.name}`
                        };
                        
                        console.log('📅 JobDashboard: Basic schedule data created:', JSON.stringify(scheduleData, null, 2));
                        
                        // Add schedule-specific fields based on schedule type
                        if (scheduleConfig.scheduleType === 'once' && scheduleConfig.executeAt) {
                            // Backend expects executeAt (camelCase)
                            scheduleData.executeAt = scheduleConfig.executeAt;
                        } 
                        else if (scheduleConfig.scheduleType === 'recurring') {
                            // Backend expects recurringType (camelCase)
                            console.log('🔄 JobDashboard: Processing recurring schedule type:', scheduleConfig.recurringType);
                            
                            // CRITICAL FIX: Ensure recurringType is set correctly
                            if (!scheduleConfig.recurringType) {
                                console.error('❌ Missing recurringType in schedule config!');
                                throw new Error('Missing recurringType in schedule config');
                            }
                            
                            scheduleData.recurringType = scheduleConfig.recurringType;
                            scheduleData.interval = scheduleConfig.interval || 1;
                            
                            console.log('🔄 JobDashboard: Set recurring type to:', scheduleData.recurringType);
                            console.log('🔄 JobDashboard: Set interval to:', scheduleData.interval);
                            
                            // For debugging
                            console.log('🔍 Full schedule config:', JSON.stringify(scheduleConfig, null, 2));
                            
                            if (scheduleConfig.startDate) {
                                // Combine startDate and startTime for the first occurrence
                                const startDate = scheduleConfig.startDate;
                                const startTime = scheduleConfig.startTime || '00:00';
                                
                                // Create a proper ISO string for the backend
                                const dateTimeStr = `${startDate}T${startTime}`;
                                const dateObj = new Date(dateTimeStr);
                                scheduleData.executeAt = dateObj.toISOString();
                            }
                            
                            if (!['minutes', 'hours'].includes(scheduleConfig.recurringType)) {
                                scheduleData.time = scheduleConfig.time || '09:00';
                                console.log('⏰ JobDashboard: Set time to:', scheduleData.time);
                            } else {
                                console.log('⏰ JobDashboard: No time needed for minutes/hours recurring type');
                                // For minutes and hours, we don't need to set time
                                // Make sure it's not set in the request
                                delete scheduleData.time;
                                
                                // Also make sure startTime is not set
                                delete scheduleData.startTime;
                                
                                // Log the final schedule data for minutes/hours
                                console.log('⏱️ Final minutes/hours schedule data:', JSON.stringify(scheduleData, null, 2));
                            }
                            
                            if (scheduleConfig.recurringType === 'weekly' && scheduleConfig.daysOfWeek) {
                                // Backend expects daysOfWeek (camelCase) as a comma-separated string
                                // The service expects a string like "0,1,2" for Sunday, Monday, Tuesday
                                // 0 = Sunday, 1 = Monday, 2 = Tuesday, etc.
                                console.log('🔍 daysOfWeek before processing:', scheduleConfig.daysOfWeek);
                                
                                if (Array.isArray(scheduleConfig.daysOfWeek)) {
                                    // Convert array to comma-separated string
                                    scheduleData.daysOfWeek = scheduleConfig.daysOfWeek.join(',');
                                } else if (typeof scheduleConfig.daysOfWeek === 'string') {
                                    // If it's already a string, use it directly
                                    scheduleData.daysOfWeek = scheduleConfig.daysOfWeek;
                                } else {
                                    console.error('❌ Invalid daysOfWeek format:', scheduleConfig.daysOfWeek);
                                }
                                
                                console.log('✅ Processed daysOfWeek:', scheduleData.daysOfWeek);
                            }
                            
                            if (scheduleConfig.recurringType === 'monthly' && scheduleConfig.dayOfMonth) {
                                // Backend expects dayOfMonth (camelCase)
                                scheduleData.dayOfMonth = scheduleConfig.dayOfMonth;
                            }
                            
                            // Advanced options
                            if (scheduleConfig.maxExecutions) {
                                // Backend expects maxExecutions (camelCase)
                                scheduleData.maxExecutions = scheduleConfig.maxExecutions;
                            }
                            
                            if (scheduleConfig.endDate) {
                                // Backend expects endDate (camelCase)
                                scheduleData.endDate = scheduleConfig.endDate;
                            }
                        }
                        else if (scheduleConfig.scheduleType === 'cron' && scheduleConfig.cronExpression) {
                            // Backend expects cronExpression (camelCase)
                            scheduleData.cronExpression = scheduleConfig.cronExpression;
                        }
                        
                        console.log('📅 JobDashboard: Sending schedule data to API:', JSON.stringify(scheduleData, null, 2));
                        
                        // Validate schedule data before sending
                        if (!scheduleData.job_id) {
                            console.error('❌ Missing job_id in schedule data!');
                        }
                        if (!scheduleData.schedule_type) {
                            console.error('❌ Missing schedule_type in schedule data!');
                        }
                        
                        // For recurring schedules, check required fields
                        if (scheduleData.schedule_type === 'recurring') {
                            if (!scheduleData.recurringType) {
                                console.error('❌ Missing recurringType for recurring schedule!');
                                throw new Error('Missing recurringType for recurring schedule');
                            }
                            
                            // For minutes and hours, we don't need time
                            if (['minutes', 'hours'].includes(scheduleData.recurringType)) {
                                console.log('⏱️ Minutes/hours schedule - time field not required');
                                // Make sure time is not set
                                delete scheduleData.time;
                            } 
                            // For other recurring types, time is required
                            else if (!scheduleData.time) {
                                console.error('❌ Missing time for recurring schedule!');
                                throw new Error(`Missing time for ${scheduleData.recurringType} recurring schedule`);
                            }
                        }
                        
                        console.log('📤 Creating new schedule');
                        try {
                            // The baseURL already includes /api, so we don't need to include it again
                            console.log('🔍 Request URL:', '/schedules');
                            console.log('🔍 Request method:', 'POST');
                            console.log('🔍 Request data:', JSON.stringify(scheduleData, null, 2));
                            
                            // For minutes and hours, make sure time is not set
                            if (scheduleData.schedule_type === 'recurring') {
                                // CRITICAL FIX: Ensure recurringType is set
                                if (!scheduleData.recurringType) {
                                    console.error('❌ Missing recurringType in schedule data!');
                                    scheduleData.recurringType = 'minutes';
                                    scheduleData.interval = scheduleData.interval || 2;
                                    console.log('⚠️ Forced recurringType to minutes with interval:', scheduleData.interval);
                                }
                                
                                if (['minutes', 'hours'].includes(scheduleData.recurringType)) {
                                    console.log('⏱️ Ensuring time is not set for minutes/hours schedule');
                                    delete scheduleData.time;
                                    delete scheduleData.startTime;
                                }
                            }
                            
                            // Final check of the data being sent
                            console.log('📤 Final schedule data being sent:', JSON.stringify(scheduleData, null, 2));
                            
                            const scheduleResponse = await apiService.post('/schedules', scheduleData);
                            console.log('✅ Schedule creation response status:', scheduleResponse.status);
                            console.log('✅ Schedule creation response data:', JSON.stringify(scheduleResponse.data, null, 2));
                        } catch (error) {
                            console.error('❌ Schedule creation error:', error.message);
                            if (error.response) {
                                console.error('❌ Error status:', error.response.status);
                                console.error('❌ Error data:', JSON.stringify(error.response.data, null, 2));
                            } else if (error.request) {
                                console.error('❌ No response received. Request:', error.request);
                            } else {
                                console.error('❌ Error setting up request:', error.message);
                            }
                            throw error; // Re-throw to be caught by the outer catch
                        }
                        console.log('✅ JobDashboard: Schedule created/updated successfully');
                        addAlert(`Job "${updatedJob.name}" updated with ${scheduleConfig.scheduleType} schedule!`, 'success');
                    } catch (scheduleError) {
                        console.error('❌ JobDashboard: Failed to update schedule:', scheduleError);
                        addAlert(`Job "${updatedJob.name}" updated, but schedule setup failed. You can configure it later.`, 'warning', 5000);
                    }
                } else {
                    // No recurring schedule, just basic job update
                    addAlert('Job updated successfully!', 'success');
                }
                
                // Update the job in the local state
                setJobs(prevJobs => 
                    prevJobs.map(job => 
                        job.id === updatedJob.id ? updatedJob : job
                    )
                );
                fetchJobs(); // Refresh the job list to get latest data
                console.log('✅ JobDashboard: Job update completed successfully');
                return true;
            } else {
                console.log('❌ JobDashboard: Unexpected response status:', response.status);
                addAlert(`Failed to update job: Unexpected response status ${response.status}`, 'error');
                return false;
            }
        } catch (error) {
            console.error('❌ JobDashboard: Job update failed:', error);
            console.error('❌ JobDashboard: Error response:', error.response);
            console.error('❌ JobDashboard: Error status:', error.response?.status);
            console.error('❌ JobDashboard: Error data:', error.response?.data);
            
            let errorMessage = 'Unknown error occurred';
            if (error.response?.data?.detail) {
                errorMessage = error.response.data.detail;
            } else if (error.response?.data?.message) {
                errorMessage = error.response.data.message;
            } else if (error.message) {
                errorMessage = error.message;
            }
            
            addAlert(`Failed to update job: ${errorMessage}`, 'error');
            return false;
        }
    };

    const handleDeleteJob = async (jobId) => {
        try {
            await apiService.delete(`/jobs/${jobId}`);
            // Remove the job from the local state
            setJobs(prevJobs => prevJobs.filter(job => job.id !== jobId));
            addAlert(`Job deleted successfully`, 'success', 3000);
        } catch (error) {
            addAlert(`Failed to delete job: ${error.response?.data?.detail || error.message}`, 'error', 0);
        }
    };

    // Calculate job statistics
    const stats = {
        total: jobs.length,
        running: jobs.filter(j => j.status === 'running').length,
        completed: jobs.filter(j => j.status === 'completed').length,
        failed: jobs.filter(j => j.status === 'failed').length,
        scheduled: jobs.filter(j => j.status === 'scheduled').length,
        paused: jobs.filter(j => j.status === 'paused').length,
    };

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
            {/* Compact Page Header */}
            <div className="page-header">
                <Typography className="page-title">
                    Job Management
                </Typography>
                <div className="page-actions">
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Tooltip title={autoRefresh ? "Disable auto-refresh" : "Enable auto-refresh"}>
                            <IconButton 
                                className="btn-icon" 
                                onClick={() => setAutoRefresh(!autoRefresh)}
                                size="small"
                                sx={{ 
                                    color: autoRefresh ? 'success.main' : 'text.secondary',
                                    '&:hover': { 
                                        backgroundColor: autoRefresh ? 'success.light' : 'action.hover',
                                        opacity: 0.1
                                    }
                                }}
                            >
                                {autoRefresh ? <AutorenewIcon fontSize="small" /> : <PauseAutoIcon fontSize="small" />}
                            </IconButton>
                        </Tooltip>
                        {autoRefresh && countdown > 0 && (
                            <Typography 
                                variant="caption" 
                                sx={{ 
                                    color: 'success.main',
                                    fontFamily: 'monospace',
                                    fontSize: '0.75rem',
                                    minWidth: '20px',
                                    textAlign: 'center'
                                }}
                            >
                                {countdown}s
                            </Typography>
                        )}
                    </Box>
                    <Tooltip title="Manual refresh">
                        <span>
                            <IconButton 
                                className="btn-icon" 
                                onClick={() => { 
                                    fetchJobs(); 
                                    fetchWorkerStats(); 
                                    if (autoRefresh) {
                                        setCountdown(Math.floor(refreshInterval / 1000)); // Reset countdown on manual refresh
                                    }
                                }} 
                                disabled={loading}
                                size="small"
                            >
                                <RefreshIcon fontSize="small" />
                            </IconButton>
                        </span>
                    </Tooltip>
                    
                    {/* Job Safety Controls - Administrative Functions */}
                    <JobSafetyControls onRefresh={fetchJobs} token={token} />
                    
                    <Button
                        className="btn-compact"
                        variant="contained"
                        startIcon={<AddIcon fontSize="small" />}
                        onClick={() => setShowCreateModal(true)}
                        size="small"
                    >
                        Create Job
                    </Button>
                </div>
            </div>

            {/* Direct Table Display */}
            {loading ? (
                <div className="table-content-area">
                    <div className="loading-container">
                        <CircularProgress size={24} />
                        <Typography variant="body2" sx={{ ml: 2, color: 'text.secondary' }}>
                            Loading jobs...
                        </Typography>
                    </div>
                </div>
            ) : (
                <JobList
                    jobs={jobs}
                    onExecuteJob={handleExecuteJob}
                    onScheduleJob={handleScheduleJob}
                    onUpdateJob={handleUpdateJob}
                    onDeleteJob={handleDeleteJob}
                />
            )}

            {/* Create Job Modal */}
            <JobCreateModal
                open={showCreateModal}
                onClose={() => setShowCreateModal(false)}
                onCreateJob={handleCreateJob}
            />
        </div>
    );
};

export default JobDashboard;
