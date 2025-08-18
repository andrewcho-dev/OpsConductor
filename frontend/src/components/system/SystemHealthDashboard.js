import React, { useState, useEffect } from 'react';
import {
  Typography,
  Button,
  IconButton,
  CircularProgress,
  Tooltip,
  Chip,
  Box,
  Paper,
  Grid,
  LinearProgress,
  TextField,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  People as PeopleIcon,
  Security as SecurityIcon,
  Computer as ComputerIcon,
  Storage as StorageIcon,
  Memory as MemoryIcon,
  AccessTime as AccessTimeIcon,
  Settings as SettingsIcon,
  MonitorHeart as MonitorHeartIcon,
  CloudQueue as CloudQueueIcon,
} from '@mui/icons-material';
import { useAlert } from '../layout/BottomStatusBar';
import '../../styles/dashboard.css';

const SystemHealthDashboard = () => {
  const { addAlert } = useAlert();
  const [healthData, setHealthData] = useState(null);
  const [systemData, setSystemData] = useState(null);
  const [databaseData, setDatabaseData] = useState(null);
  const [applicationData, setApplicationData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    fetchAllHealthData();
    const interval = setInterval(fetchAllHealthData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAllHealthData = async () => {
    if (!refreshing) setRefreshing(true);
    
    try {
      const [overallRes, systemRes, databaseRes, applicationRes] = await Promise.all([
        fetch('/api/v2/health/', { 
          headers: { 'Content-Type': 'application/json' }
        }),
        fetch('/api/v2/health/system', { 
          headers: { 'Content-Type': 'application/json' }
        }),
        fetch('/api/v2/health/database', { 
          headers: { 'Content-Type': 'application/json' }
        }),
        fetch('/api/v2/health/application', { 
          headers: { 'Content-Type': 'application/json' }
        })
      ]);

      if (overallRes.ok) {
        const data = await overallRes.json();
        setHealthData(data);
      }

      if (systemRes.ok) {
        const data = await systemRes.json();
        setSystemData(data);
      }

      if (databaseRes.ok) {
        const data = await databaseRes.json();
        setDatabaseData(data);
      }

      if (applicationRes.ok) {
        const data = await applicationRes.json();
        setApplicationData(data);
      }

      setLastUpdated(new Date());
      
    } catch (error) {
      console.error('Failed to fetch health data:', error);
      addAlert('Failed to fetch system health data', 'error', 5000);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleServiceAction = async (serviceName, action) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        addAlert('Authentication required', 'error', 5000);
        return;
      }

      const response = await fetch(`/api/v2/health/services/${serviceName}/${action}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        addAlert(result.message, 'success', 5000);
        
        // Refresh health data after action
        setTimeout(() => {
          fetchAllHealthData();
        }, 2000);
      } else {
        const error = await response.json();
        addAlert(error.detail || `Failed to ${action} service`, 'error', 5000);
      }
    } catch (error) {
      console.error(`Service ${action} error:`, error);
      addAlert(`Failed to ${action} service: ${error.message}`, 'error', 5000);
    }
  };

  // Calculate system statistics following SystemSettings pattern
  const stats = {
    uptime: healthData?.uptime || 'Unknown',
    status: healthData?.status || 'Unknown',
    version: healthData?.version || '1.0.0',
    cpu: systemData?.cpu?.usage_percent?.toFixed(1) || 'N/A',
    memory: systemData?.memory?.usage_percent?.toFixed(1) || 'N/A',
    containers: healthData?.health_checks?.docker_containers?.details?.summary ? 
      `${healthData.health_checks.docker_containers.details.summary.running}/${healthData.health_checks.docker_containers.details.summary.total}` : 'N/A'
  };

  if (loading) {
    return (
      <div className="dashboard-container">
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
          <CircularProgress />
          <Typography variant="h6" sx={{ ml: 2 }}>Loading system health...</Typography>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      {/* Compact Page Header - Following Design Guidelines */}
      <div className="page-header">
        <Typography className="page-title">
          System Health Dashboard
        </Typography>
        <div className="page-actions">
          {lastUpdated && (
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
              Last updated: {lastUpdated.toLocaleTimeString()}
            </Typography>
          )}
          <Tooltip title="Refresh health data">
            <span>
              <IconButton 
                className="btn-icon" 
                onClick={fetchAllHealthData} 
                disabled={refreshing}
                size="small"
              >
                <RefreshIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
        </div>
      </div>

      {/* Enhanced Statistics Grid - Following Design Guidelines */}
      <div className="stats-grid">
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon primary">
              <AccessTimeIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.uptime}</h3>
              <p>System Uptime</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className={`stat-icon ${stats.status === 'healthy' ? 'success' : 'warning'}`}>
              <MonitorHeartIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.status}</h3>
              <p>Health Status</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon info">
              <SettingsIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.version}</h3>
              <p>Version</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className={`stat-icon ${parseFloat(stats.cpu) > 80 ? 'error' : parseFloat(stats.cpu) > 60 ? 'warning' : 'success'}`}>
              <ComputerIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.cpu}%</h3>
              <p>CPU Usage</p>
            </div>
          </div>
        </div>

        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className={`stat-icon ${parseFloat(stats.memory) > 85 ? 'error' : parseFloat(stats.memory) > 70 ? 'warning' : 'success'}`}>
              <MemoryIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.memory}%</h3>
              <p>Memory Usage</p>
            </div>
          </div>
        </div>

        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon success">
              <CloudQueueIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.containers}</h3>
              <p>Containers</p>
            </div>
          </div>
        </div>
      </div>

      {/* System Resources & Docker Containers - Side by Side */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 3fr', gap: '16px', marginBottom: '16px' }}>
        
        {/* System Resources Card */}
        <div className="main-content-card fade-in">
          <div className="content-card-header">
            <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
              <ComputerIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
              SYSTEM RESOURCES
            </Typography>
            {systemData && (
              <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                Real-time resource monitoring
              </Typography>
            )}
          </div>
          
          <div className="content-card-body">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
            
            {/* CPU Usage */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                <ComputerIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                CPU Performance
              </Typography>
              {systemData?.cpu ? (
                <>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                      Usage
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.8rem' }}>
                      {systemData.cpu.usage_percent?.toFixed(1)}%
                    </Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={systemData.cpu.usage_percent || 0}
                    color={systemData.cpu.usage_percent > 80 ? 'error' : systemData.cpu.usage_percent > 60 ? 'warning' : 'success'}
                    sx={{ height: 8, borderRadius: 4, mb: 1 }}
                  />
                  <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                    Cores: {systemData.cpu.cores || 'N/A'}
                  </Typography>
                </>
              ) : (
                <Typography variant="body2" sx={{ fontSize: '0.8rem', color: 'text.secondary' }}>
                  No CPU data available
                </Typography>
              )}
            </div>

            {/* Memory Usage */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                <MemoryIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                Memory Usage
              </Typography>
              {systemData?.memory ? (
                <>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                      Used
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.8rem' }}>
                      {systemData.memory.usage_percent?.toFixed(1)}%
                    </Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={systemData.memory.usage_percent || 0}
                    color={systemData.memory.usage_percent > 85 ? 'error' : systemData.memory.usage_percent > 70 ? 'warning' : 'success'}
                    sx={{ height: 8, borderRadius: 4, mb: 1 }}
                  />
                  <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                    {systemData.memory.used_gb?.toFixed(1)}GB / {systemData.memory.total_gb?.toFixed(1)}GB
                  </Typography>
                </>
              ) : (
                <Typography variant="body2" sx={{ fontSize: '0.8rem', color: 'text.secondary' }}>
                  No memory data available
                </Typography>
              )}
            </div>

            {/* Disk Usage */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                <StorageIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                Disk Storage
              </Typography>
              {systemData?.disk ? (
                <>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                      Used
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.8rem' }}>
                      {systemData.disk.usage_percent?.toFixed(1)}%
                    </Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={systemData.disk.usage_percent || 0}
                    color={systemData.disk.usage_percent > 90 ? 'error' : systemData.disk.usage_percent > 75 ? 'warning' : 'success'}
                    sx={{ height: 8, borderRadius: 4, mb: 1 }}
                  />
                  <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                    {systemData.disk.used_gb?.toFixed(1)}GB / {systemData.disk.total_gb?.toFixed(1)}GB
                  </Typography>
                </>
              ) : (
                <Typography variant="body2" sx={{ fontSize: '0.8rem', color: 'text.secondary' }}>
                  No disk data available
                </Typography>
              )}
            </div>
            </div>
          </div>
        </div>

        {/* Docker Containers Card */}
        <div className="main-content-card fade-in">
          <div className="content-card-header">
            <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
              <CloudQueueIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
              DOCKER CONTAINERS
            </Typography>
            {healthData?.health_checks?.docker_containers && (
              <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                {healthData.health_checks.docker_containers.details?.summary?.running || 0} running, {healthData.health_checks.docker_containers.details?.summary?.total || 0} total
              </Typography>
            )}
          </div>
          
          <div className="content-card-body">
            {healthData?.health_checks?.docker_containers?.details?.containers ? (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', maxHeight: '300px', overflowY: 'auto' }}>
                {Object.entries(healthData.health_checks.docker_containers.details.containers).map(([name, container]) => (
                  <div key={name} style={{ 
                    border: `1px solid ${container.healthy ? '#4caf50' : '#f44336'}`,
                    borderRadius: '6px',
                    padding: '12px',
                    backgroundColor: container.healthy ? 'rgba(76, 175, 80, 0.05)' : 'rgba(244, 67, 54, 0.05)'
                  }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Box 
                        sx={{ 
                          width: 8, 
                          height: 8, 
                          borderRadius: '50%', 
                          backgroundColor: container.healthy ? '#4caf50' : '#f44336',
                          mr: 1 
                        }} 
                      />
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
                        {name.replace('opsconductor-', '')}
                      </Typography>
                    </Box>
                    <Typography variant="body2" sx={{ fontSize: '0.7rem', mb: 0.5 }}>
                      Status: <strong>{container.status}</strong>
                    </Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.7rem', mb: 1 }}>
                      Health: <strong>{container.health_status}</strong>
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <Button
                        className="btn-compact"
                        size="small"
                        variant="outlined"
                        color="primary"
                        onClick={() => handleServiceAction(name, 'restart')}
                        sx={{ fontSize: '0.7rem', minWidth: 'auto', px: 1 }}
                      >
                        Restart
                      </Button>
                      <Button
                        className="btn-compact"
                        size="small"
                        variant="outlined"
                        color="warning"
                        onClick={() => handleServiceAction(name, 'stop')}
                        sx={{ fontSize: '0.7rem', minWidth: 'auto', px: 1 }}
                      >
                        Stop
                      </Button>
                    </Box>
                  </div>
                ))}
              </div>
            ) : (
              <Typography variant="body2" sx={{ fontSize: '0.8rem', color: 'text.secondary' }}>
                No container data available
              </Typography>
            )}
          </div>
        </div>
      </div>

      {/* System Information & Service Status - Side by Side */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 3fr', gap: '16px', marginBottom: '16px' }}>
        
        {/* System Information Card */}
        <div className="main-content-card fade-in">
          <div className="content-card-header">
            <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
              <SettingsIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
              SYSTEM INFORMATION
            </Typography>
          </div>
          
          <div className="content-card-body">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
            
            {/* Basic Info */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                <MonitorHeartIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                System Status
              </Typography>
              {healthData ? (
                <>
                  <Typography variant="body2" sx={{ fontSize: '0.8rem', mb: 0.5 }}>
                    Status: <strong>{healthData.status || 'Unknown'}</strong>
                  </Typography>
                  <Typography variant="body2" sx={{ fontSize: '0.8rem', mb: 0.5 }}>
                    Environment: <strong>{healthData.environment || 'Unknown'}</strong>
                  </Typography>
                  <Typography variant="body2" sx={{ fontSize: '0.8rem', mb: 1 }}>
                    Version: <strong>{healthData.version || 'Unknown'}</strong>
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={healthData.status === 'healthy' ? 100 : 50}
                    color={healthData.status === 'healthy' ? 'success' : 'warning'}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </>
              ) : (
                <Typography variant="body2" sx={{ fontSize: '0.8rem', color: 'text.secondary' }}>
                  No system information available
                </Typography>
              )}
            </div>

            {/* Database Info */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                <StorageIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                Database Status
              </Typography>
              {databaseData ? (
                <>
                  <Typography variant="body2" sx={{ fontSize: '0.8rem', mb: 0.5 }}>
                    Status: <strong>{databaseData.status || 'Unknown'}</strong>
                  </Typography>
                  <Typography variant="body2" sx={{ fontSize: '0.8rem', mb: 0.5 }}>
                    Connections: <strong>{databaseData.connections || 'N/A'}</strong>
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                    Database health monitoring
                  </Typography>
                </>
              ) : (
                <Typography variant="body2" sx={{ fontSize: '0.8rem', color: 'text.secondary' }}>
                  No database data available
                </Typography>
              )}
            </div>

            {/* Application Info */}
            <div>
              <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                <SecurityIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                Application Status
              </Typography>
              {applicationData ? (
                <>
                  <Typography variant="body2" sx={{ fontSize: '0.8rem', mb: 0.5 }}>
                    Status: <strong>{applicationData.status || 'Unknown'}</strong>
                  </Typography>
                  <Typography variant="body2" sx={{ fontSize: '0.8rem', mb: 0.5 }}>
                    Workers: <strong>{applicationData.workers || 'N/A'}</strong>
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                    Application health monitoring
                  </Typography>
                </>
              ) : (
                <Typography variant="body2" sx={{ fontSize: '0.8rem', color: 'text.secondary' }}>
                  No application data available
                </Typography>
              )}
            </div>
            </div>
          </div>
        </div>

        {/* Service Status Card */}
        <div className="main-content-card fade-in">
          <div className="content-card-header">
            <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
              <SecurityIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
              SERVICE STATUS
            </Typography>
          </div>
          
          <div className="content-card-body">
            {healthData?.health_checks ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                {Object.entries(healthData.health_checks).map(([service, status]) => (
                  <div key={service} style={{ 
                    border: '1px solid #e0e0e0',
                    borderRadius: '6px',
                    padding: '12px',
                    textAlign: 'center',
                    backgroundColor: status.healthy ? 'rgba(76, 175, 80, 0.05)' : 'rgba(244, 67, 54, 0.05)'
                  }}>
                    <SecurityIcon 
                      color={status.healthy ? 'success' : 'error'} 
                      fontSize="small" 
                      sx={{ mb: 0.5 }}
                    />
                    <Typography variant="caption" sx={{ fontWeight: 500, textTransform: 'capitalize', display: 'block', fontSize: '0.7rem' }}>
                      {service}
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.65rem' }}>
                      {status.status}
                    </Typography>
                  </div>
                ))}
              </div>
            ) : (
              <Typography variant="body2" sx={{ fontSize: '0.8rem', color: 'text.secondary' }}>
                No service status data available
              </Typography>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemHealthDashboard;