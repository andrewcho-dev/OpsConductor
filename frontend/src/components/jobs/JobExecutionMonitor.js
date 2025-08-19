import React, { useState, useEffect } from 'react';
import { useSessionAuth } from '../../contexts/SessionAuthContext';
import { formatLocalDateTime } from '../../utils/timeUtils';
import './JobExecutionMonitor.css';

const JobExecutionMonitor = ({ job, activeExecution, onExecutionComplete }) => {
    const { token } = useSessionAuth();
    const [executions, setExecutions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [selectedExecution, setSelectedExecution] = useState(null);

    useEffect(() => {
        if (job) {
            fetchExecutions();
        }
    }, [job]);

    useEffect(() => {
        if (activeExecution) {
            setSelectedExecution(activeExecution);
            // Poll for updates every 5 seconds (reduced from 2s)
            const interval = setInterval(() => {
                fetchExecutions();
            }, 5000);

            return () => clearInterval(interval);
        }
    }, [activeExecution]);

    const fetchExecutions = async () => {
        if (!job) return;

        try {
            setLoading(true);
            const response = await fetch(`/api/jobs/${job.id}/executions`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                setExecutions(data);
                
                // Check if active execution is complete
                if (activeExecution) {
                    const currentExecution = data.find(e => e.id === activeExecution.id);
                    if (currentExecution && 
                        ['completed', 'failed', 'cancelled'].includes(currentExecution.status)) {
                        onExecutionComplete();
                    }
                }
            }
        } catch (error) {
            console.error('Error fetching executions:', error);
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateString) => {
        return formatLocalDateTime(dateString);
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'scheduled': return 'scheduled';
            case 'running': return 'running';
            case 'completed': return 'completed';
            case 'failed': return 'failed';
            case 'cancelled': return 'cancelled';
            default: return 'scheduled';
        }
    };

    const getProgressPercentage = (execution) => {
        if (!execution.branches || execution.branches.length === 0) {
            return 0;
        }

        const completedBranches = execution.branches.filter(
            branch => ['completed', 'failed', 'cancelled'].includes(branch.status)
        ).length;

        return Math.round((completedBranches / execution.branches.length) * 100);
    };

    const getOverallStatus = (execution) => {
        if (!execution.branches || execution.branches.length === 0) {
            return execution.status;
        }

        const allCompleted = execution.branches.every(
            branch => branch.status === 'completed'
        );
        const anyFailed = execution.branches.some(
            branch => branch.status === 'failed'
        );
        const anyRunning = execution.branches.some(
            branch => branch.status === 'running'
        );

        if (anyRunning) return 'running';
        if (anyFailed) return 'failed';
        if (allCompleted) return 'completed';
        return execution.status;
    };

    if (!job) {
        return (
            <div className="execution-monitor">
                <div className="no-job-selected">
                    <p>Select a job to view execution details</p>
                </div>
            </div>
        );
    }

    return (
        <div className="execution-monitor">
            <div className="execution-monitor-header">
                <h2>Execution History</h2>
                <button 
                    className="btn btn-secondary btn-sm"
                    onClick={fetchExecutions}
                    disabled={loading}
                >
                    {loading ? 'Refreshing...' : 'Refresh'}
                </button>
            </div>

            <div className="execution-list">
                {executions.length === 0 ? (
                    <div className="no-executions">
                        <p>No executions found for this job</p>
                    </div>
                ) : (
                    executions.map((execution) => {
                        const progress = getProgressPercentage(execution);
                        const overallStatus = getOverallStatus(execution);
                        
                        return (
                            <div
                                key={execution.id}
                                className={`execution-item ${selectedExecution?.id === execution.id ? 'selected' : ''}`}
                                onClick={() => setSelectedExecution(execution)}
                            >
                                <div className="execution-header">
                                    <div className="execution-number">
                                        {execution.execution_serial || `Execution #${execution.execution_number}`}
                                    </div>
                                    <div className={`execution-status ${getStatusColor(overallStatus)}`}>
                                        {overallStatus}
                                    </div>
                                </div>

                                <div className="execution-details">
                                    <div className="execution-time">
                                        Started: {formatDate(execution.started_at)}
                                    </div>
                                    {execution.completed_at && (
                                        <div className="execution-time">
                                            Completed: {formatDate(execution.completed_at)}
                                        </div>
                                    )}
                                    <div className="execution-branches">
                                        Branches: {execution.branches?.length || 0}
                                    </div>
                                </div>

                                {execution.branches && execution.branches.length > 0 && (
                                    <div className="execution-progress">
                                        <div className="progress-bar">
                                            <div 
                                                className="progress-fill"
                                                style={{ width: `${progress}%` }}
                                            ></div>
                                        </div>
                                        <div className="progress-text">
                                            {progress}% Complete
                                        </div>
                                    </div>
                                )}

                                {selectedExecution?.id === execution.id && (
                                    <div className="execution-branches-detail">
                                        <h4>Branch Details</h4>
                                        {execution.branches?.map((branch) => (
                                            <div key={branch.id} className="branch-item">
                                                <div className="branch-header">
                                                    <span className="branch-id">Branch {branch.branch_id}</span>
                                                    <span className={`branch-status ${getStatusColor(branch.status)}`}>
                                                        {branch.status}
                                                    </span>
                                                </div>
                                                <div className="branch-details">
                                                    <div>Target: {branch.target_name || 'ID ' + branch.target_id} {branch.ip_address ? `(${branch.ip_address})` : ''} {branch.os_type ? `- ${branch.os_type}` : ''}</div>
                                                    {branch.started_at && (
                                                        <div>Started: {formatDate(branch.started_at)}</div>
                                                    )}
                                                    {branch.completed_at && (
                                                        <div>Completed: {formatDate(branch.completed_at)}</div>
                                                    )}
                                                    {branch.exit_code !== null && (
                                                        <div>Exit Code: {branch.exit_code}</div>
                                                    )}
                                                </div>
                                                {branch.result_output && (
                                                    <div className="branch-output">
                                                        <strong>Output:</strong>
                                                        <pre>{branch.result_output}</pre>
                                                    </div>
                                                )}
                                                {branch.result_error && (
                                                    <div className="branch-error">
                                                        <strong>Error:</strong>
                                                        <pre>{branch.result_error}</pre>
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
};

export default JobExecutionMonitor;
