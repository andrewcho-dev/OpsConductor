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
  Box,
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  NetworkCheck as NetworkCheckIcon,
  Devices as DevicesIcon,
  ArrowBack as ArrowBackIcon,
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
import { useSessionAuth } from '../../contexts/SessionAuthContext';
import '../../styles/dashboard.css';

const UniversalTargetDashboard = () => {
  const navigate = useNavigate();
  const { user, logout } = useSessionAuth();
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
        
        // Refresh the target list to show newly imported targets
        if (discoveryResult.imported_count && discoveryResult.imported_count > 0) {
          console.log('Refreshing target list after importing', discoveryResult.imported_count, 'targets');
          // Add a small delay to ensure backend has processed the import
          setTimeout(() => {
            loadTargets();
          }, 500);
        }
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
          Universal Targets
        </Typography>
        <div className="page-actions">
          <Tooltip title="Back to Dashboard">
            <IconButton 
              className="btn-icon" 
              onClick={() => navigate('/dashboard')}
              size="small"
            >
              <ArrowBackIcon fontSize="small" />
            </IconButton>
          </Tooltip>
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



      {/* Direct Table Display */}
      {loading ? (
        <div className="table-content-area">
          <div className="loading-container">
            <CircularProgress size={24} />
            <Typography variant="body2" sx={{ ml: 2, color: 'text.secondary' }}>
              Loading targets...
            </Typography>
          </div>
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