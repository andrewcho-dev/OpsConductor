/**
 * Network Discovery Dashboard
 * Main dashboard for network discovery management
 */

import React, { useState, useEffect } from 'react';
import discoveryService from '../../services/discoveryService';
import QuickScanModal from './QuickScanModal';
import NewDiscoveryJobModal from './NewDiscoveryJobModal';
import DiscoveryJobsTab from './DiscoveryJobsTab';
import DiscoveredDevicesTab from './DiscoveredDevicesTab';
import DiscoveryTemplatesTab from './DiscoveryTemplatesTab';
import './discovery.css';

const DiscoveryDashboard = () => {
  const [stats, setStats] = useState(null);
  const [recentJobs, setRecentJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [showQuickScan, setShowQuickScan] = useState(false);
  const [showNewJob, setShowNewJob] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [statsData, jobsData] = await Promise.all([
        discoveryService.getDiscoveryStats(),
        discoveryService.getDiscoveryJobs({ limit: 10 })
      ]);
      
      setStats(statsData);
      setRecentJobs(jobsData);
    } catch (err) {
      console.error('Error loading dashboard data:', err);
      setError('Failed to load discovery dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickScan = () => {
    setShowQuickScan(true);
  };

  const handleNewJob = () => {
    setShowNewJob(true);
  };

  const handleScanComplete = (results) => {
    console.log('Scan completed:', results);
    // Optionally refresh dashboard data
  };

  const handleJobCreated = (job) => {
    console.log('Job created:', job);
    // Refresh dashboard data
    loadDashboardData();
  };

  if (loading) {
    return (
      <div className="discovery-dashboard">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading discovery dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="discovery-dashboard">
        <div className="error-container">
          <div className="error-icon">⚠️</div>
          <h3>Error Loading Dashboard</h3>
          <p>{error}</p>
          <button onClick={loadDashboardData} className="btn btn-primary">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="discovery-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-content">
          <div className="header-text">
            <h1>🔍 Network Discovery</h1>
            <p>Discover and manage devices on your network</p>
          </div>
          <div className="header-actions">
            <button onClick={handleQuickScan} className="btn btn-secondary">
              ⚡ Quick Scan
            </button>
            <button onClick={handleNewJob} className="btn btn-primary">
              ➕ New Discovery Job
            </button>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="dashboard-tabs">
        <button 
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          📊 Overview
        </button>
        <button 
          className={`tab ${activeTab === 'jobs' ? 'active' : ''}`}
          onClick={() => setActiveTab('jobs')}
        >
          🔄 Discovery Jobs
        </button>
        <button 
          className={`tab ${activeTab === 'devices' ? 'active' : ''}`}
          onClick={() => setActiveTab('devices')}
        >
          📱 Discovered Devices
        </button>
        <button 
          className={`tab ${activeTab === 'templates' ? 'active' : ''}`}
          onClick={() => setActiveTab('templates')}
        >
          📋 Templates
        </button>
      </div>

      {/* Tab Content */}
      <div className="dashboard-content">
        {activeTab === 'overview' && (
          <OverviewTab stats={stats} recentJobs={recentJobs} />
        )}
        {activeTab === 'jobs' && (
          <DiscoveryJobsTab />
        )}
        {activeTab === 'devices' && (
          <DiscoveredDevicesTab />
        )}
        {activeTab === 'templates' && (
          <DiscoveryTemplatesTab />
        )}
      </div>

      {/* Modals */}
      <QuickScanModal
        isOpen={showQuickScan}
        onClose={() => setShowQuickScan(false)}
        onScanComplete={handleScanComplete}
      />
      
      <NewDiscoveryJobModal
        isOpen={showNewJob}
        onClose={() => setShowNewJob(false)}
        onJobCreated={handleJobCreated}
      />
    </div>
  );
};

// Overview Tab Component
const OverviewTab = ({ stats, recentJobs }) => {
  if (!stats) return <div>No statistics available</div>;

  return (
    <div className="overview-tab">
      {/* Statistics Cards */}
      <div className="stats-grid">
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon primary">
              <span style={{ fontSize: '16px' }}>🔄</span>
            </div>
            <div className="stat-details">
              <h3>{stats.total_jobs}</h3>
              <p>Total Jobs</p>
            </div>
          </div>
        </div>

        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon info">
              <span style={{ fontSize: '16px' }}>📱</span>
            </div>
            <div className="stat-details">
              <h3>{stats.total_devices_discovered}</h3>
              <p>Devices Discovered</p>
            </div>
          </div>
        </div>

        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon success">
              <span style={{ fontSize: '16px' }}>✅</span>
            </div>
            <div className="stat-details">
              <h3>{stats.devices_imported}</h3>
              <p>Devices Imported</p>
            </div>
          </div>
        </div>

        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon warning">
              <span style={{ fontSize: '16px' }}>🏷️</span>
            </div>
            <div className="stat-details">
              <h3>{Object.keys(stats.device_type_counts).length}</h3>
              <p>Device Types</p>
            </div>
          </div>
        </div>
        
        {/* Empty slots to maintain 6-column grid */}
        <div className="stat-card" style={{ visibility: 'hidden' }}>
          <div className="stat-card-content">
            <div className="stat-icon primary">
              <span style={{ fontSize: '16px' }}>🔄</span>
            </div>
            <div className="stat-details">
              <h3>-</h3>
              <p>-</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card" style={{ visibility: 'hidden' }}>
          <div className="stat-card-content">
            <div className="stat-icon primary">
              <span style={{ fontSize: '16px' }}>🔄</span>
            </div>
            <div className="stat-details">
              <h3>-</h3>
              <p>-</p>
            </div>
          </div>
        </div>
      </div>

      {/* Device Types Chart */}
      <div className="dashboard-section">
        <h2>Device Types Distribution</h2>
        <div className="device-types-chart">
          {Object.entries(stats.device_type_counts).map(([type, count]) => (
            <div key={type} className="device-type-item">
              <div className="device-type-info">
                <span className="device-icon">
                  {discoveryService.getDeviceTypeIcon(type)}
                </span>
                <span className="device-name">{type}</span>
              </div>
              <div className="device-count">
                <span className="count">{count}</span>
                <div 
                  className="count-bar"
                  style={{
                    width: `${(count / Math.max(...Object.values(stats.device_type_counts))) * 100}%`,
                    backgroundColor: discoveryService.getDeviceTypeColor(type)
                  }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Jobs */}
      <div className="dashboard-section">
        <h2>Recent Discovery Jobs</h2>
        <div className="recent-jobs">
          {recentJobs.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📭</div>
              <p>No discovery jobs yet</p>
              <button className="btn btn-primary">Create First Job</button>
            </div>
          ) : (
            <div className="jobs-list">
              {recentJobs.map(job => (
                <div key={job.id} className="job-item">
                  <div className="job-info">
                    <h4>{job.name}</h4>
                    <p>Created {discoveryService.formatDiscoveryTime(job.created_at)}</p>
                  </div>
                  <div className="job-stats">
                    <span className="devices-found">{job.devices_discovered} devices</span>
                    <span 
                      className={`job-status ${job.status}`}
                      style={{ color: discoveryService.getStatusColor(job.status) }}
                    >
                      {job.status}
                    </span>
                  </div>
                  <div className="job-progress">
                    <div className="progress-bar">
                      <div 
                        className="progress-fill"
                        style={{ width: `${job.progress}%` }}
                      ></div>
                    </div>
                    <span className="progress-text">{job.progress}%</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};



export default DiscoveryDashboard;