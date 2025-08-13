import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography,
  IconButton,
  Tooltip,
  CircularProgress,
  Tabs,
  Tab,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Refresh as RefreshIcon,
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  Email as EmailIcon,
  Warning as WarningIcon,
  List as ListIcon,
  Assessment as AssessmentIcon,
  Send as SendIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { useAlert } from '../layout/BottomStatusBar';
import EmailTargetSelector from './EmailTargetSelector';
import NotificationTemplates from './NotificationTemplates';
import AlertRules from './AlertRules';
import NotificationLogs from './NotificationLogs';
import AlertLogs from './AlertLogs';
import NotificationStats from './NotificationStats';

const NotificationCenter = () => {
  const navigate = useNavigate();
  const { addAlert } = useAlert();
  const [activeTab, setActiveTab] = useState('email-target');
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);

  const tabs = [
    { id: 'email-target', label: 'Email Target', icon: <EmailIcon fontSize="small" /> },
    { id: 'templates', label: 'Templates', icon: <EmailIcon fontSize="small" /> },
    { id: 'alerts', label: 'Alert Rules', icon: <WarningIcon fontSize="small" /> },
    { id: 'logs', label: 'Logs', icon: <ListIcon fontSize="small" /> },
    { id: 'alert-logs', label: 'Alert Logs', icon: <WarningIcon fontSize="small" /> },
    { id: 'stats', label: 'Statistics', icon: <AssessmentIcon fontSize="small" /> }
  ];

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/notifications/stats');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
        addAlert('Notification stats loaded successfully', 'success', 3000);
      } else {
        throw new Error('Failed to fetch stats');
      }
    } catch (error) {
      addAlert('Failed to load notification stats', 'error', 0);
    } finally {
      setLoading(false);
    }
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'email-target':
        return <EmailTargetSelector onConfigUpdate={fetchStats} />;
      case 'templates':
        return <NotificationTemplates />;
      case 'alerts':
        return <AlertRules />;
      case 'logs':
        return <NotificationLogs />;
      case 'alert-logs':
        return <AlertLogs />;
      case 'stats':
        return <NotificationStats stats={stats} loading={loading} onRefresh={fetchStats} />;
      default:
        return <EmailTargetSelector onConfigUpdate={fetchStats} />;
    }
  };

  // Calculate notification statistics - 6 key metrics
  const notificationStats = stats ? {
    totalSent: stats.total_sent || 0,
    successRate: stats.success_rate || 0,
    activeRules: stats.active_rules || 0,
    failedToday: stats.failed_today || 0,
    templatesCount: stats.templates_count || 0,
    avgDeliveryTime: stats.avg_delivery_time || 0,
  } : {};

  return (
    <div className="dashboard-container">
      {/* Compact Page Header */}
      <div className="page-header">
        <Typography className="page-title">
          Notification Center
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
          <Tooltip title="Refresh statistics">
            <IconButton 
              className="btn-icon" 
              onClick={fetchStats} 
              disabled={loading}
              size="small"
            >
              <RefreshIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </div>
      </div>

      {/* Compact Statistics Grid - 6 key notification metrics */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card fade-in">
            <div className="stat-card-content">
              <div className="stat-icon primary">
                <SendIcon fontSize="small" />
              </div>
              <div className="stat-details">
                <h3>{notificationStats.totalSent}</h3>
                <p>Total Sent</p>
              </div>
            </div>
          </div>
          
          <div className="stat-card fade-in">
            <div className="stat-card-content">
              <div className="stat-icon success">
                <EmailIcon fontSize="small" />
              </div>
              <div className="stat-details">
                <h3>{notificationStats.successRate}%</h3>
                <p>Success Rate</p>
              </div>
            </div>
          </div>
          
          <div className="stat-card fade-in">
            <div className="stat-card-content">
              <div className="stat-icon warning">
                <WarningIcon fontSize="small" />
              </div>
              <div className="stat-details">
                <h3>{notificationStats.activeRules}</h3>
                <p>Active Rules</p>
              </div>
            </div>
          </div>
          
          <div className="stat-card fade-in">
            <div className="stat-card-content">
              <div className="stat-icon error">
                <WarningIcon fontSize="small" />
              </div>
              <div className="stat-details">
                <h3>{notificationStats.failedToday}</h3>
                <p>Failed Today</p>
              </div>
            </div>
          </div>

          <div className="stat-card fade-in">
            <div className="stat-card-content">
              <div className="stat-icon info">
                <EmailIcon fontSize="small" />
              </div>
              <div className="stat-details">
                <h3>{notificationStats.templatesCount}</h3>
                <p>Templates</p>
              </div>
            </div>
          </div>

          <div className="stat-card fade-in">
            <div className="stat-card-content">
              <div className="stat-icon primary">
                <ScheduleIcon fontSize="small" />
              </div>
              <div className="stat-details">
                <h3>{notificationStats.avgDeliveryTime}s</h3>
                <p>Avg Delivery</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Notification Management Tabs */}
      <div className="main-content-card fade-in">
        <div className="content-card-header">
          <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
            <NotificationsIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
            NOTIFICATION MANAGEMENT
          </Typography>
        </div>
        
        <div className="content-card-body">
          {loading ? (
            <div className="loading-container">
              <CircularProgress size={24} />
              <Typography variant="body2" sx={{ ml: 2, color: 'text.secondary' }}>
                Loading notification data...
              </Typography>
            </div>
          ) : (
            <>
              <Tabs 
                value={activeTab} 
                onChange={(e, newValue) => setActiveTab(newValue)} 
                sx={{ 
                  mb: 2,
                  '& .MuiTab-root': {
                    fontSize: '0.75rem',
                    minHeight: '36px',
                    textTransform: 'none',
                  }
                }}
              >
                {tabs.map((tab) => (
                  <Tab 
                    key={tab.id}
                    value={tab.id}
                    label={tab.label} 
                    icon={tab.icon} 
                    iconPosition="start"
                  />
                ))}
              </Tabs>

              <div style={{ marginTop: '16px' }}>
                {renderTabContent()}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default NotificationCenter;
