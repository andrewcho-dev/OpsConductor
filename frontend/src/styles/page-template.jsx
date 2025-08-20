/**
 * Page Template - Standardized Design System
 * Use this template for all new pages to ensure consistency
 */
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
  // Import other icons as needed
} from '@mui/icons-material';

import { useAlert } from '../layout/BottomStatusBar';

const PageTemplate = () => {
  const { addAlert } = useAlert();
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  // Load data on component mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      // Replace with actual API call
      const response = await fetch('your-endpoint');
      const result = await response.json();
      setData(result);
      addAlert(`Loaded ${result.length} items successfully`, 'success', 3000);
    } catch (err) {
      addAlert(`Failed to load data: ${err.message}`, 'error', 0);
    } finally {
      setLoading(false);
    }
  };

  // Calculate statistics for the stats grid
  const stats = {
    total: data.length,
    active: data.filter(item => item.status === 'active').length,
    // Add more stats as needed
  };

  return (
    <div className="dashboard-container">
      {/* Compact Page Header */}
      <div className="page-header">
        <Typography className="page-title">
          Your Page Title
        </Typography>
        <div className="page-actions">
          <Tooltip title="Refresh data">
            <IconButton 
              className="btn-icon" 
              onClick={loadData} 
              disabled={loading}
              size="small"
            >
              <RefreshIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Button
            className="btn-compact"
            variant="contained"
            startIcon={<AddIcon fontSize="small" />}
            onClick={() => {/* Handle create action */}}
            size="small"
          >
            Create New
          </Button>
        </div>
      </div>

      {/* Compact Statistics Grid */}
      <div className="stats-grid">
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon primary">
              <AddIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.total}</h3>
              <p>Total Items</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon success">
              <AddIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.active}</h3>
              <p>Active Items</p>
            </div>
          </div>
        </div>
        
        {/* Add more stat cards as needed */}
      </div>

      {/* Main Content Card */}
      <div className="main-content-card fade-in">
        <div className="content-card-header">
          <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
            YOUR SECTION TITLE
          </Typography>
          <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
            {data.length} items configured
          </Typography>
        </div>
        
        <div className="content-card-body">
          {loading ? (
            <div className="loading-container">
              <CircularProgress size={24} />
              <Typography variant="body2" sx={{ ml: 2, color: 'text.secondary' }}>
                Loading data...
              </Typography>
            </div>
          ) : (
            <div>
              {/* Your main content goes here */}
              {/* Use filters-container for search/filter controls */}
              {/* Use compact-table for data tables */}
              {/* Use form-control-compact for form inputs */}
            </div>
          )}
        </div>
      </div>

      {/* Additional content cards can be added with marginTop: '16px' */}
    </div>
  );
};

export default PageTemplate;