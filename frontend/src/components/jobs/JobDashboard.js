import React, { useState, useEffect } from 'react';
import {
  Typography,
  Button,
  IconButton,
  Tooltip,
  CircularProgress,
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
            
            // Add timeout to prevent hanging
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
            
            const response = await fetch(`/api/jobs/`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (response.ok) {
                const data = await response.json();
                setJobs(data.jobs || []);
                addAlert(`Loaded ${data.jobs?.length || 0} jobs successfully`, 'success', 3000);
            } else {
                addAlert('Failed to fetch jobs', 'error', 0);
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                addAlert('Request timed out - please try again', 'error', 5000);
            } else {
                addAlert(`Error fetching jobs: ${error.message}`, 'error', 0);
            }
        } finally {
            setLoading(false);
        }
    };

    const fetchWorkerStats = async () => {
        try {
            // Add timeout to prevent hanging
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
            
            const response = await fetch('/api/celery/workers', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (response.ok) {
                const data = await response.json();
                const activeWorkers = data.workers ? data.workers.length : 0;
                setWorkerStats({ active: activeWorkers, total: activeWorkers });
            }
        } catch (error) {
            // Silently fail - monitoring is optional
            console.log('Worker stats unavailable:', error.name);
        }
    };

    const handleCreateJob = async (jobData) => {
        try {
            const response = await fetch(`/api/jobs/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(jobData)
            });

            if (response.ok) {
                const newJob = await response.json();
                setJobs(prevJobs => [newJob, ...prevJobs]);
                setShowCreateModal(false);
                addAlert(`Job "${newJob.name}" created successfully!`, 'success', 3000);
                return true;
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create job');
            }
        } catch (error) {
            addAlert(`Failed to create job: ${error.message}`, 'error', 5000);
            return false;
        }
    };

    const handleExecuteJob = async (jobId, targetIds = null) => {
        try {
            const response = await fetch(`/api/jobs/${jobId}/execute`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ target_ids: targetIds })
            });

            if (response.ok) {
                const execution = await response.json();
                fetchJobs(); // Refresh job list
                addAlert(`Job execution started successfully`, 'success', 3000);
                return true;
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to execute job');
            }
        } catch (error) {
            addAlert(`Failed to execute job: ${error.message}`, 'error', 0);
            return false;
        }
    };

    const handleScheduleJob = async (jobId, scheduledAt) => {
        try {
            const response = await fetch(`/api/jobs/${jobId}/schedule`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ scheduled_at: scheduledAt })
            });

            if (response.ok) {
                fetchJobs(); // Refresh job list
                return true;
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to schedule job');
            }
        } catch (error) {
            addAlert(`Failed to schedule job: ${error.message}`, 'error', 0);
            return false;
        }
    };



    const handleUpdateJob = async (updatedJobData) => {
        try {
            const response = await fetch(`/api/jobs/${updatedJobData.id || updatedJobData.job_id}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: updatedJobData.name,
                    description: updatedJobData.description,
                    job_type: updatedJobData.job_type,
                    actions: updatedJobData.actions,
                    target_ids: updatedJobData.target_ids,
                    scheduled_at: updatedJobData.scheduled_at
                })
            });

            if (response.ok) {
                const updatedJob = await response.json();
                // Update the job in the local state
                setJobs(prevJobs => 
                    prevJobs.map(job => 
                        job.id === updatedJob.id ? updatedJob : job
                    )
                );
                addAlert('Job updated successfully!', 'success');
                fetchJobs(); // Refresh the job list to get latest data
                return true;
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to update job');
            }
        } catch (error) {
            addAlert(`Failed to update job: ${error.message}`, 'error');
            return false;
        }
    };

    const handleDeleteJob = async (jobId) => {
        try {
            const response = await fetch(`/api/jobs/${jobId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                // Remove the job from the local state
                setJobs(prevJobs => prevJobs.filter(job => job.id !== jobId));
                addAlert(`Job deleted successfully`, 'success', 3000);
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete job');
            }
        } catch (error) {
            addAlert(`Failed to delete job: ${error.message}`, 'error', 0);
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
        <div className="dashboard-container">
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

            {/* Compact Statistics Grid - Key Metrics Only */}
            <div className="stats-grid">
                <div className="stat-card fade-in">
                    <div className="stat-card-content">
                        <div className="stat-icon primary">
                            <WorkIcon fontSize="small" />
                        </div>
                        <div className="stat-details">
                            <h3>{stats.total}</h3>
                            <p>Total Jobs</p>
                        </div>
                    </div>
                </div>
                
                <div className="stat-card fade-in">
                    <div className="stat-card-content">
                        <div className="stat-icon info">
                            <PlayArrowIcon fontSize="small" />
                        </div>
                        <div className="stat-details">
                            <h3>{stats.running}</h3>
                            <p>Running</p>
                        </div>
                    </div>
                </div>
                
                <div className="stat-card fade-in">
                    <div className="stat-card-content">
                        <div className="stat-icon success">
                            <CheckCircleIcon fontSize="small" />
                        </div>
                        <div className="stat-details">
                            <h3>{stats.completed}</h3>
                            <p>Completed</p>
                        </div>
                    </div>
                </div>
                
                <div className="stat-card fade-in">
                    <div className="stat-card-content">
                        <div className="stat-icon error">
                            <ErrorIcon fontSize="small" />
                        </div>
                        <div className="stat-details">
                            <h3>{stats.failed}</h3>
                            <p>Failed</p>
                        </div>
                    </div>
                </div>
                
                <div className="stat-card fade-in">
                    <div className="stat-card-content">
                        <div className="stat-icon warning">
                            <WorkIcon fontSize="small" />
                        </div>
                        <div className="stat-details">
                            <h3>{workerStats.active}</h3>
                            <p>Workers</p>
                        </div>
                    </div>
                </div>
                
                {/* Empty slot to maintain 6-column grid */}
                <div className="stat-card" style={{ visibility: 'hidden' }}>
                    <div className="stat-card-content">
                        <div className="stat-icon primary">
                            <WorkIcon fontSize="small" />
                        </div>
                        <div className="stat-details">
                            <h3>-</h3>
                            <p>-</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content Card */}
            <div className="main-content-card fade-in">
                <div className="content-card-header">
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
                        JOB MANAGEMENT
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                        {jobs.length} jobs configured
                    </Typography>
                </div>
                
                <div className="content-card-body">
                    {loading ? (
                        <div className="loading-container">
                            <CircularProgress size={24} />
                            <Typography variant="body2" sx={{ ml: 2, color: 'text.secondary' }}>
                                Loading jobs...
                            </Typography>
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
                </div>
            </div>

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
