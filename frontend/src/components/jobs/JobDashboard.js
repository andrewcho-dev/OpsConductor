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
} from '@mui/icons-material';

import JobCreateModal from './JobCreateModal';
import JobList from './JobList';
import JobSafetyControls from './JobSafetyControls';
import { useAuth } from '../../contexts/AuthContext';
import { useAlert } from '../layout/BottomStatusBar';
import { authService } from '../../services/authService';
import '../../styles/dashboard.css';

const JobDashboard = () => {
    const { addAlert } = useAlert();
    const [jobs, setJobs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [workerStats, setWorkerStats] = useState({ active: 0, total: 0 });
    const { token } = useAuth();

    useEffect(() => {
        if (token) {
            fetchJobs();
            fetchWorkerStats();
        }
    }, [token]);

    const fetchJobs = async () => {
        try {
            setLoading(true);
            
            const response = await authService.api.get('/v2/jobs/');
            setJobs(response.data.jobs || []);
            addAlert(`Loaded ${response.data.jobs?.length || 0} jobs successfully`, 'success', 3000);
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

    const handleCreateJob = async (jobData, scheduleConfig) => {
        try {
            // First create the job
            const response = await authService.api.post('/v2/jobs/', jobData);
            const newJob = response.data;
            setJobs(prevJobs => [newJob, ...prevJobs]);
            
            // If there's advanced schedule configuration, create the schedule
            if (scheduleConfig && scheduleConfig.scheduleType !== 'once') {
                try {
                    const scheduleData = {
                        job_id: newJob.id,
                        schedule_type: scheduleConfig.scheduleType,
                        enabled: true,
                        timezone: scheduleConfig.timezone || 'UTC',
                        description: `Auto-created schedule for job: ${newJob.name}`,
                        ...scheduleConfig
                    };
                    
                    await authService.api.post('/api/schedules', scheduleData);
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
            const response = await authService.api.post(`/v2/jobs/${jobId}/execute`, { target_ids: targetIds });
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
            const response = await authService.api.post(`/v2/jobs/${jobId}/schedule`, { scheduled_at: scheduledAt });
            fetchJobs(); // Refresh job list
            return true;
        } catch (error) {
            addAlert(`Failed to schedule job: ${error.response?.data?.detail || error.message}`, 'error', 0);
            return false;
        }
    };



    const handleUpdateJob = async (updatedJobData) => {
        console.log('🔄 Starting job update...', updatedJobData);
        try {
            const jobData = {
                name: updatedJobData.name,
                description: updatedJobData.description,
                job_type: updatedJobData.job_type,
                actions: updatedJobData.actions,
                target_ids: updatedJobData.target_ids,
                scheduled_at: updatedJobData.scheduled_at,
                priority: updatedJobData.priority,
                timeout: updatedJobData.timeout,
                retry_count: updatedJobData.retry_count
            };
            console.log('📤 Sending job data:', jobData);
            console.log('🎯 API endpoint:', `/v2/jobs/${updatedJobData.id || updatedJobData.job_id}`);
            
            const response = await authService.api.put(`/v2/jobs/${updatedJobData.id || updatedJobData.job_id}`, jobData);
            console.log('✅ API response:', response);
            
            const updatedJob = response.data;
            // Update the job in the local state
            setJobs(prevJobs => 
                prevJobs.map(job => 
                    job.id === updatedJob.id ? updatedJob : job
                )
            );
            addAlert('Job updated successfully!', 'success');
            fetchJobs(); // Refresh the job list to get latest data
            return true;
        } catch (error) {
            console.error('❌ Job update failed:', error);
            console.error('❌ Error response:', error.response);
            console.error('❌ Error status:', error.response?.status);
            console.error('❌ Error data:', error.response?.data);
            addAlert(`Failed to update job: ${error.response?.data?.detail || error.message}`, 'error');
            return false;
        }
    };

    const handleDeleteJob = async (jobId) => {
        try {
            await authService.api.delete(`/v2/jobs/${jobId}`);
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
                    <Tooltip title="Refresh jobs">
                        <span>
                            <IconButton 
                                className="btn-icon" 
                                onClick={() => { fetchJobs(); fetchWorkerStats(); }} 
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
