/**
 * Universal Target Dashboard - Redesigned
 * Compact, modern, efficient control dashboard style
 * Standardized design for all function pages
 */
import React, { useState, useEffect } from 'react';
import {
  Typography,
  Button,
  CircularProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  Computer as ComputerIcon,
  Storage as StorageIcon,
  Security as SecurityIcon,
  NetworkCheck as NetworkCheckIcon,
  Dashboard as DashboardIcon,
  Devices as DevicesIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  DesktopWindows as DesktopWindowsIcon,
} from '@mui/icons-material';

import { getAllTargets } from '../../services/targetService';
import { useAlert } from '../layout/BottomStatusBar';
import UniversalTargetList from './UniversalTargetList';
import UniversalTargetCreateModal from './UniversalTargetCreateModal';
import UniversalTargetEditModal from './UniversalTargetEditModal';
import UniversalTargetDetailModal from './UniversalTargetDetailModal';
import SimpleNetworkDiscoveryModal from './SimpleNetworkDiscoveryModal';
import discoveryService from '../../services/discoveryService';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const UniversalTargetDashboard = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { addAlert } = useAlert();
  const [targets, setTargets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [discoveryModalOpen, setDiscoveryModalOpen] = useState(false);
  const [selectedTarget, setSelectedTarget] = useState(null);

  // Load targets on component mount
  useEffect(() => {
    loadTargets();
  }, []);

  const loadTargets = async () => {
    try {
      setLoading(true);
      const targetsData = await getAllTargets();
      setTargets(targetsData);
      addAlert(`Loaded ${targetsData.length} targets successfully`, 'success', 3000);
    } catch (err) {
      addAlert(`Failed to load targets: ${err.message}`, 'error', 0);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTarget = () => {
    setCreateModalOpen(true);
  };

  const handleEditTarget = (target) => {
    setSelectedTarget(target);
    setEditModalOpen(true);
  };

  const handleViewTarget = (target) => {
    setSelectedTarget(target);
    setDetailModalOpen(true);
  };

  const handleTargetCreated = () => {
    setCreateModalOpen(false);
    addAlert('Target created successfully', 'success', 3000);
    loadTargets();
  };

  const handleTargetUpdated = () => {
    setEditModalOpen(false);
    setSelectedTarget(null);
    addAlert('Target updated successfully', 'success', 3000);
    loadTargets();
  };

  const handleTargetDeleted = () => {
    setSelectedTarget(null);
    addAlert('Target deleted successfully', 'success', 3000);
    loadTargets();
  };

  const handleBackToDashboard = () => {
    navigate('/dashboard');
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleHealthCheck = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch('/api/targets/health-check-batch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const result = await response.json();
        const { results } = result;
        
        addAlert(
          `Health check completed: ${results.checked} targets checked, ${results.status_changes} status changes`,
          'success',
          5000
        );
        
        // Refresh targets to show updated health status
        loadTargets();
      } else {
        throw new Error('Health check failed');
      }
    } catch (error) {
      console.error('Health check error:', error);
      addAlert('Failed to run health check', 'error', 5000);
    } finally {
      setLoading(false);
    }
  };

  const handleDiscoveryStarted = (discoveryResult) => {
    console.log('handleDiscoveryStarted called with:', discoveryResult);
    
    try {
      // Handle both discovery job start and import completion
      if (discoveryResult && discoveryResult.message) {
        // This is an import completion result
        addAlert(discoveryResult.message, 'success', 5000);
      } else if (discoveryResult) {
        // This is a discovery job start
        const jobName = discoveryResult.name || `Job ${discoveryResult.id}` || 'Network Discovery';
        addAlert(
          `Network discovery started: ${jobName}`,
          'success',
          5000
        );
      } else {
        // Fallback for undefined/null result
        addAlert('Network discovery started', 'success', 5000);
      }
    } catch (error) {
      console.error('Error in handleDiscoveryStarted:', error);
      addAlert('Network discovery started', 'success', 5000);
    }
    // Optionally navigate to discovery dashboard to see progress
    // navigate('/discovery');
  };

  // Calculate dashboard statistics - 6 key metrics that fit on one line
  const stats = {
    total: targets.length,
    active: targets.filter(t => t.status === 'active').length,
    linux: targets.filter(t => t.os_type === 'linux').length,
    windows: targets.filter(t => t.os_type === 'windows').length,
    healthy: targets.filter(t => t.health_status === 'healthy').length,
    critical: targets.filter(t => t.health_status === 'critical').length,
  };

  return (
    <div className="dashboard-container">
      {/* Compact Page Header */}
      <div className="page-header">
        <Typography className="page-title">
          Universal Targets
        </Typography>
        <div className="page-actions">
          <Tooltip title="Refresh targets">
            <span>
              <IconButton 
                className="btn-icon" 
                onClick={loadTargets} 
                disabled={loading}
                size="small"
              >
                <RefreshIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
          <Button
            className="btn-compact"
            variant="outlined"
            startIcon={<SearchIcon fontSize="small" />}
            onClick={() => setDiscoveryModalOpen(true)}
            size="small"
            sx={{ mr: 1 }}
          >
            Discover Network
          </Button>
          <Button
            className="btn-compact"
            variant="contained"
            startIcon={<AddIcon fontSize="small" />}
            onClick={handleCreateTarget}
            size="small"
            sx={{ mr: 1 }}
          >
            Add Target
          </Button>
          <Button
            className="btn-compact"
            variant="outlined"
            startIcon={<NetworkCheckIcon fontSize="small" />}
            onClick={handleHealthCheck}
            size="small"
          >
            Health Check
          </Button>
        </div>
      </div>

      {/* Compact Statistics Grid - 6 key metrics that fit on one line */}
      <div className="stats-grid">
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon primary">
              <DevicesIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.total}</h3>
              <p>Total Targets</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon success">
              <CheckCircleIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.active}</h3>
              <p>Active</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon info">
              <ComputerIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.linux}</h3>
              <p>Linux</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon info">
              <DesktopWindowsIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.windows}</h3>
              <p>Windows</p>
            </div>
          </div>
        </div>

        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon success">
              <CheckCircleIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.healthy}</h3>
              <p>Healthy</p>
            </div>
          </div>
        </div>

        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon error">
              <ErrorIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.critical}</h3>
              <p>Critical</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Card */}
      <div className="main-content-card fade-in">
        <div className="content-card-header">
          <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
            TARGET MANAGEMENT
          </Typography>
          <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
            {targets.length} targets configured
          </Typography>
        </div>
        
        <div className="content-card-body">
          {loading ? (
            <div className="loading-container">
              <CircularProgress size={24} />
              <Typography variant="body2" sx={{ ml: 2, color: 'text.secondary' }}>
                Loading targets...
              </Typography>
            </div>
          ) : (
            <UniversalTargetList
              targets={targets}
              onEditTarget={handleEditTarget}
              onViewTarget={handleViewTarget}
              onDeleteTarget={handleTargetDeleted}
              onRefresh={loadTargets}
            />
          )}
        </div>
      </div>

      {/* Modals */}
      <SimpleNetworkDiscoveryModal
        open={discoveryModalOpen}
        onClose={() => setDiscoveryModalOpen(false)}
        onDiscoveryStarted={handleDiscoveryStarted}
      />
      
      <UniversalTargetCreateModal
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onTargetCreated={handleTargetCreated}
      />

      {selectedTarget && (
        <>
          <UniversalTargetEditModal
            open={editModalOpen}
            target={selectedTarget}
            onClose={() => {
              setEditModalOpen(false);
              setSelectedTarget(null);
            }}
            onTargetUpdated={handleTargetUpdated}
          />
          
          <UniversalTargetDetailModal
            open={detailModalOpen}
            target={selectedTarget}
            onClose={() => {
              setDetailModalOpen(false);
              setSelectedTarget(null);
            }}
            onEditTarget={() => {
              setDetailModalOpen(false);
              setEditModalOpen(true);
            }}
            onDeleteTarget={handleTargetDeleted}
          />
        </>
      )}
    </div>
  );
};

export default UniversalTargetDashboard;