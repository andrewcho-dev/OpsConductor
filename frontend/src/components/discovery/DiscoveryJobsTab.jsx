/**
 * Discovery Jobs Tab Component
 * Manages discovery jobs with full CRUD operations
 */

import React, { useState, useEffect } from 'react';
import discoveryService from '../../services/discoveryService';

const DiscoveryJobsTab = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedJob, setSelectedJob] = useState(null);
  const [showJobDetails, setShowJobDetails] = useState(false);
  const [filters, setFilters] = useState({
    status: '',
    search: ''
  });

  useEffect(() => {
    loadJobs();
  }, [filters]);

  const loadJobs = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = {};
      if (filters.status) params.status = filters.status;
      
      const jobsData = await discoveryService.getDiscoveryJobs(params);
      
      // Filter by search term if provided
      let filteredJobs = jobsData;
      if (filters.search) {
        const searchTerm = filters.search.toLowerCase();
        filteredJobs = jobsData.filter(job => 
          job.name.toLowerCase().includes(searchTerm) ||
          (job.description && job.description.toLowerCase().includes(searchTerm)) ||
          job.network_ranges.some(range => range.includes(searchTerm))
        );
      }
      
      setJobs(filteredJobs);
    } catch (err) {
      console.error('Error loading jobs:', err);
      setError('Failed to load discovery jobs');
    } finally {
      setLoading(false);
    }
  };

  const handleRunJob = async (jobId) => {
    try {
      await discoveryService.runDiscoveryJob(jobId);
      loadJobs(); // Refresh to show updated status
    } catch (err) {
      console.error('Error running job:', err);
      setError('Failed to start discovery job');
    }
  };

  const handleCancelJob = async (jobId) => {
    try {
      await discoveryService.cancelDiscoveryJob(jobId);
      loadJobs(); // Refresh to show updated status
    } catch (err) {
      console.error('Error cancelling job:', err);
      setError('Failed to cancel discovery job');
    }
  };

  const handleDeleteJob = async (jobId) => {
    if (!window.confirm('Are you sure you want to delete this discovery job? This action cannot be undone.')) {
      return;
    }

    try {
      await discoveryService.deleteDiscoveryJob(jobId);
      loadJobs(); // Refresh list
    } catch (err) {
      console.error('Error deleting job:', err);
      setError('Failed to delete discovery job');
    }
  };

  const handleViewDetails = async (job) => {
    try {
      const fullJob = await discoveryService.getDiscoveryJob(job.id);
      setSelectedJob(fullJob);
      setShowJobDetails(true);
    } catch (err) {
      console.error('Error loading job details:', err);
      setError('Failed to load job details');
    }
  };

  const getJobStatusIcon = (status) => {
    const icons = {
      'pending': '⏳',
      'running': '🔄',
      'completed': '✅',
      'failed': '❌',
      'cancelled': '⏹️'
    };
    return icons[status] || '❓';
  };

  const canRunJob = (job) => {
    return ['pending', 'completed', 'failed', 'cancelled'].includes(job.status);
  };

  const canCancelJob = (job) => {
    return job.status === 'running';
  };

  if (loading) {
    return (
      <div className="jobs-tab">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading discovery jobs...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="jobs-tab">
      {/* Header */}
      <div className="tab-header">
        <div className="header-content">
          <h2>Discovery Jobs</h2>
          <p>Manage and monitor network discovery jobs</p>
        </div>
      </div>

      {/* Filters */}
      <div className="jobs-filters">
        <div className="filter-group">
          <input
            type="text"
            placeholder="Search jobs..."
            value={filters.search}
            onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
            className="search-input"
          />
        </div>
        <div className="filter-group">
          <select
            value={filters.status}
            onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
            className="status-filter"
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
        <button onClick={loadJobs} className="btn btn-secondary">
          🔄 Refresh
        </button>
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}

      {/* Jobs List */}
      <div className="jobs-list">
        {jobs.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <h3>No Discovery Jobs</h3>
            <p>Create your first discovery job to start scanning your network.</p>
          </div>
        ) : (
          <div className="jobs-grid">
            {jobs.map(job => (
              <div key={job.id} className="job-card">
                <div className="job-header">
                  <div className="job-info">
                    <h3>{job.name}</h3>
                    {job.description && (
                      <p className="job-description">{job.description}</p>
                    )}
                  </div>
                  <div className="job-status">
                    <span 
                      className={`status-badge ${job.status}`}
                      style={{ color: discoveryService.getStatusColor(job.status) }}
                    >
                      {getJobStatusIcon(job.status)} {job.status}
                    </span>
                  </div>
                </div>

                <div className="job-details">
                  <div className="detail-item">
                    <span className="detail-label">Networks:</span>
                    <span className="detail-value">
                      {job.network_ranges.slice(0, 2).join(', ')}
                      {job.network_ranges.length > 2 && ` +${job.network_ranges.length - 2} more`}
                    </span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Ports:</span>
                    <span className="detail-value">
                      {job.common_ports.length > 0 
                        ? `${job.common_ports.slice(0, 5).join(', ')}${job.common_ports.length > 5 ? '...' : ''}`
                        : 'Default ports'
                      }
                    </span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Created:</span>
                    <span className="detail-value">
                      {discoveryService.formatDiscoveryTime(job.created_at)}
                    </span>
                  </div>
                </div>

                {job.status === 'running' && (
                  <div className="job-progress">
                    <div className="progress-info">
                      <span>Progress: {job.progress}%</span>
                      <span>{job.devices_discovered} devices found</span>
                    </div>
                    <div className="progress-bar">
                      <div 
                        className="progress-fill"
                        style={{ width: `${job.progress}%` }}
                      ></div>
                    </div>
                  </div>
                )}

                {job.status === 'completed' && (
                  <div className="job-results">
                    <div className="result-stats">
                      <span className="stat">
                        📱 {job.devices_discovered} devices
                      </span>
                      <span className="stat">
                        🌐 {job.total_ips_scanned} IPs scanned
                      </span>
                      <span className="stat">
                        ⏱️ {job.completed_at ? 
                          Math.round((new Date(job.completed_at) - new Date(job.started_at)) / 1000) + 's'
                          : 'Unknown'
                        }
                      </span>
                    </div>
                  </div>
                )}

                <div className="job-actions">
                  <button 
                    onClick={() => handleViewDetails(job)}
                    className="btn btn-secondary"
                  >
                    👁️ Details
                  </button>
                  
                  {canRunJob(job) && (
                    <button 
                      onClick={() => handleRunJob(job.id)}
                      className="btn btn-success"
                    >
                      ▶️ Run
                    </button>
                  )}
                  
                  {canCancelJob(job) && (
                    <button 
                      onClick={() => handleCancelJob(job.id)}
                      className="btn btn-warning"
                    >
                      ⏹️ Cancel
                    </button>
                  )}
                  
                  {job.status !== 'running' && (
                    <button 
                      onClick={() => handleDeleteJob(job.id)}
                      className="btn btn-danger"
                    >
                      🗑️ Delete
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Job Details Modal */}
      {showJobDetails && selectedJob && (
        <JobDetailsModal
          job={selectedJob}
          onClose={() => {
            setShowJobDetails(false);
            setSelectedJob(null);
          }}
        />
      )}
    </div>
  );
};

// Job Details Modal Component
const JobDetailsModal = ({ job, onClose }) => {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content job-details-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>📋 Job Details: {job.name}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          <div className="job-details-content">
            {/* Basic Information */}
            <div className="details-section">
              <h3>Basic Information</h3>
              <div className="details-grid">
                <div className="detail-item">
                  <label>Name:</label>
                  <span>{job.name}</span>
                </div>
                <div className="detail-item">
                  <label>Status:</label>
                  <span 
                    className={`status-badge ${job.status}`}
                    style={{ color: discoveryService.getStatusColor(job.status) }}
                  >
                    {job.status}
                  </span>
                </div>
                <div className="detail-item">
                  <label>Description:</label>
                  <span>{job.description || 'No description'}</span>
                </div>
                <div className="detail-item">
                  <label>Created:</label>
                  <span>{new Date(job.created_at).toLocaleString()}</span>
                </div>
                {job.started_at && (
                  <div className="detail-item">
                    <label>Started:</label>
                    <span>{new Date(job.started_at).toLocaleString()}</span>
                  </div>
                )}
                {job.completed_at && (
                  <div className="detail-item">
                    <label>Completed:</label>
                    <span>{new Date(job.completed_at).toLocaleString()}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Network Configuration */}
            <div className="details-section">
              <h3>Network Configuration</h3>
              <div className="details-grid">
                <div className="detail-item">
                  <label>Network Ranges:</label>
                  <div className="network-ranges">
                    {job.network_ranges.map((range, index) => (
                      <span key={index} className="network-range">{range}</span>
                    ))}
                  </div>
                </div>
                <div className="detail-item">
                  <label>Common Ports:</label>
                  <div className="ports-list">
                    {job.common_ports.map(port => (
                      <span key={port} className="port-badge">{port}</span>
                    ))}
                  </div>
                </div>
                <div className="detail-item">
                  <label>Timeout:</label>
                  <span>{job.timeout}s</span>
                </div>
                <div className="detail-item">
                  <label>Max Concurrent:</label>
                  <span>{job.max_concurrent}</span>
                </div>
              </div>
            </div>

            {/* Discovery Options */}
            <div className="details-section">
              <h3>Discovery Options</h3>
              <div className="options-grid">
                <div className="option-item">
                  <span className={job.enable_service_detection ? 'enabled' : 'disabled'}>
                    {job.enable_service_detection ? '✅' : '❌'} Service Detection
                  </span>
                </div>
                <div className="option-item">
                  <span className={job.enable_hostname_resolution ? 'enabled' : 'disabled'}>
                    {job.enable_hostname_resolution ? '✅' : '❌'} Hostname Resolution
                  </span>
                </div>
                <div className="option-item">
                  <span className={job.enable_snmp ? 'enabled' : 'disabled'}>
                    {job.enable_snmp ? '✅' : '❌'} SNMP Discovery
                  </span>
                </div>
              </div>
              {job.enable_snmp && job.snmp_communities.length > 0 && (
                <div className="detail-item">
                  <label>SNMP Communities:</label>
                  <span>{job.snmp_communities.join(', ')}</span>
                </div>
              )}
            </div>

            {/* Results */}
            {job.status === 'completed' && (
              <div className="details-section">
                <h3>Results</h3>
                <div className="results-stats">
                  <div className="stat-card">
                    <div className="stat-value">{job.total_ips_scanned}</div>
                    <div className="stat-label">IPs Scanned</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">{job.devices_discovered}</div>
                    <div className="stat-label">Devices Found</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">{job.progress}%</div>
                    <div className="stat-label">Progress</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="modal-footer">
          <button onClick={onClose} className="btn btn-primary">
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default DiscoveryJobsTab;