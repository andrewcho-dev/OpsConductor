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
  Stop as StopIcon,
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

  const handlePruneVolumes = async () => {
    try {
      setRefreshing(true);
      const token = localStorage.getItem('access_token');
      if (!token) {
        addAlert('Authentication required', 'error', 5000);
        return;
      }
      
      const response = await fetch('/api/v2/health/volumes/prune', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        addAlert(data.message || 'Volumes pruned successfully', 'success', 3000);
        // Refresh health data to show updated volumes
        fetchAllHealthData();
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to prune volumes');
      }
    } catch (error) {
      console.error('Error pruning volumes:', error);
      addAlert(error.message || 'Failed to prune volumes', 'error', 5000);
    } finally {
      setRefreshing(false);
    }
  };
  
  const handleServiceAction = async (serviceName, action) => {
    try {
      const token = localStorage.getItem('access_token');
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
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '8px', maxHeight: '300px', overflowY: 'auto' }}>
                {Object.entries(healthData.health_checks.docker_containers.details.containers).map(([name, container]) => (
                  <div key={name} style={{ 
                    border: `1px solid ${container.healthy ? '#4caf50' : '#f44336'}`,
                    borderRadius: '4px',
                    padding: '6px',
                    backgroundColor: container.healthy ? 'rgba(76, 175, 80, 0.05)' : 'rgba(244, 67, 54, 0.05)'
                  }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', maxWidth: '75%' }}>
                        <Box 
                          sx={{ 
                            width: 6, 
                            height: 6, 
                            borderRadius: '50%', 
                            backgroundColor: container.healthy ? '#4caf50' : '#f44336',
                            mr: 0.5,
                            flexShrink: 0
                          }} 
                        />
                        <Tooltip title={name.replace('opsconductor-', '')}>
                          <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.7rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {name.replace('opsconductor-', '')}
                          </Typography>
                        </Tooltip>
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box>
                        <Typography variant="body2" sx={{ fontSize: '0.65rem', lineHeight: 1.1 }}>
                          {container.status}
                        </Typography>
                        <Typography variant="body2" sx={{ fontSize: '0.65rem', lineHeight: 1.1 }}>
                          {container.health_status}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        <Tooltip title="Restart container">
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => handleServiceAction(name, 'restart')}
                            sx={{ p: 0.3 }}
                          >
                            <RefreshIcon sx={{ fontSize: '0.8rem' }} />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Stop container">
                          <IconButton
                            size="small"
                            color="warning"
                            onClick={() => handleServiceAction(name, 'stop')}
                            sx={{ p: 0.3 }}
                          >
                            <StopIcon sx={{ fontSize: '0.8rem' }} />
                          </IconButton>
                        </Tooltip>
                      </Box>
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

      {/* System Information & Docker Volumes - Side by Side */}
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
        
        {/* Docker Volumes Card */}
        <div className="main-content-card fade-in">
          <div className="content-card-header">
            <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
              <StorageIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
              DOCKER VOLUMES
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Button 
                size="small" 
                variant="outlined" 
                color="primary" 
                onClick={handlePruneVolumes}
                disabled={refreshing}
                sx={{ fontSize: '0.7rem', py: 0.3, px: 1, minWidth: 'auto' }}
              >
                {refreshing ? <CircularProgress size={16} /> : 'Prune'}
              </Button>
              {healthData?.health_checks?.volumes && (
                <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                  {healthData.health_checks.volumes.details?.volumes_count || 0} volumes, 
                  {healthData.health_checks.volumes.healthy ? ' all healthy' : ' issues detected'}
                </Typography>
              )}
            </Box>
          </div>
          
          <div className="content-card-body">
            {healthData?.health_checks?.volumes?.details?.volumes ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', maxHeight: '200px', overflowY: 'auto' }}>
                {Object.entries(healthData.health_checks.volumes.details.volumes).map(([name, volume]) => {
                  // All volumes are considered healthy unless the overall volumes check is unhealthy
                  const isHealthy = healthData.health_checks.volumes.healthy !== false;
                  
                  return (
                    <div key={name} style={{ 
                      border: `1px solid ${isHealthy ? '#4caf50' : '#f44336'}`,
                      borderRadius: '4px',
                      padding: '6px',
                      backgroundColor: isHealthy ? 'rgba(76, 175, 80, 0.05)' : 'rgba(244, 67, 54, 0.05)'
                    }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                        <Box 
                          sx={{ 
                            width: 6, 
                            height: 6, 
                            borderRadius: '50%', 
                            backgroundColor: isHealthy ? '#4caf50' : '#f44336',
                            mr: 0.5 
                          }} 
                        />
                        <Tooltip title={name}>
                          <Typography variant="subtitle2" sx={{ 
                            fontWeight: 600, 
                            fontSize: '0.7rem', 
                            whiteSpace: 'nowrap', 
                            overflow: 'hidden', 
                            textOverflow: 'ellipsis',
                            width: '160px' // Wider to show more of the name
                          }}>
                            {name.length > 30 ? name.substring(0, 30) + '...' : name}
                          </Typography>
                        </Tooltip>
                      </Box>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: '2px', mt: 1 }}>
                        <Typography variant="body2" sx={{ fontSize: '0.75rem', fontWeight: 500 }}>
                          {volume.stats || `${volume.size_mb || 0}MB / ${volume.used_mb || 0}MB / ${volume.percent || 0}%`}
                        </Typography>
                      </Box>
                    </div>
                  );
                })}
            </div>
            ) : (
              <Typography variant="body2" sx={{ fontSize: '0.8rem', color: 'text.secondary' }}>
                No volume data available
              </Typography>
            )}
          </div>
        </div>
      </div>

      {/* Application Status & Service Status - Side by Side (SWITCHED ORDER) */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 3fr', gap: '16px', marginBottom: '16px' }}>
        
        {/* Application Status Card */}
        <div className="main-content-card fade-in">
          <div className="content-card-header">
            <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
              <ComputerIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
              APPLICATION STATUS
            </Typography>
            {applicationData && (
              <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                Application health monitoring
              </Typography>
            )}
          </div>
          
          <div className="content-card-body">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
              {/* API Status */}
              <div>
                <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                  <ComputerIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                  API Status
                </Typography>
                {applicationData ? (
                  <>
                    <Typography variant="body2" sx={{ fontSize: '0.8rem', mb: 0.5 }}>
                      Status: <strong>{applicationData.status || 'Unknown'}</strong>
                    </Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.8rem', mb: 0.5 }}>
                      Response Time: <strong>{applicationData.response_time_ms || 'N/A'} ms</strong>
                    </Typography>
                  </>
                ) : (
                  <Typography variant="body2" sx={{ fontSize: '0.8rem', color: 'text.secondary' }}>
                    No API data available
                  </Typography>
                )}
              </div>
              
              {/* Database Status */}
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
                  </>
                ) : (
                  <Typography variant="body2" sx={{ fontSize: '0.8rem', color: 'text.secondary' }}>
                    No database data available
                  </Typography>
                )}
              </div>
              
              {/* Cache Status */}
              <div>
                <Typography variant="subtitle2" sx={{ fontSize: '0.75rem', fontWeight: 600, mb: 1 }}>
                  <MemoryIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Cache Status
                </Typography>
                {applicationData?.cache ? (
                  <>
                    <Typography variant="body2" sx={{ fontSize: '0.8rem', mb: 0.5 }}>
                      Status: <strong>{applicationData.cache?.status || 'Unknown'}</strong>
                    </Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.8rem', mb: 0.5 }}>
                      Hit Rate: <strong>{applicationData.cache?.hit_rate || 'N/A'}%</strong>
                    </Typography>
                  </>
                ) : (
                  <Typography variant="body2" sx={{ fontSize: '0.8rem', color: 'text.secondary' }}>
                    No cache data available
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
            {healthData?.health_checks && (
              <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                Specific service health monitoring
              </Typography>
            )}
          </div>
          
          <div className="content-card-body">
            {healthData?.health_checks ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', maxHeight: '300px', overflowY: 'auto' }}>
                {/* Core Services */}
                {[
                  { id: 'api', name: 'API Service', icon: <ComputerIcon fontSize="small" /> },
                  { id: 'scheduler', name: 'Job Scheduler', icon: <AccessTimeIcon fontSize="small" /> },
                  { id: 'worker', name: 'Task Worker', icon: <MemoryIcon fontSize="small" /> },
                  { id: 'database', name: 'PostgreSQL', icon: <StorageIcon fontSize="small" /> },
                  { id: 'redis', name: 'Redis Cache', icon: <StorageIcon fontSize="small" /> },
                  { id: 'nginx', name: 'Nginx Proxy', icon: <CloudQueueIcon fontSize="small" /> },
                  { id: 'auth', name: 'Auth Service', icon: <SecurityIcon fontSize="small" /> },
                  { id: 'monitoring', name: 'Prometheus', icon: <MonitorHeartIcon fontSize="small" /> }
                ].map((service) => {
                  // Use the actual health data from the API
                  // If no data is available for a service, assume it's healthy until proven otherwise
                  const serviceData = healthData.health_checks[service.id] || 
                                     (healthData.health_checks.services?.details?.services && 
                                      healthData.health_checks.services.details.services[service.id]);
                  
                  const isHealthy = serviceData?.healthy !== false; // Only show as unhealthy if explicitly set to false
                  const status = serviceData?.status || 'running';
                  
                  return (
                    <div key={service.id} style={{ 
                      border: `1px solid ${isHealthy ? '#4caf50' : '#f44336'}`,
                      borderRadius: '4px',
                      padding: '6px',
                      backgroundColor: isHealthy ? 'rgba(76, 175, 80, 0.05)' : 'rgba(244, 67, 54, 0.05)'
                    }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                        <Box 
                          sx={{ 
                            width: 6, 
                            height: 6, 
                            borderRadius: '50%', 
                            backgroundColor: isHealthy ? '#4caf50' : '#f44336',
                            mr: 0.5 
                          }} 
                        />
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.7rem' }}>
                          {service.name}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.65rem', textTransform: 'capitalize' }}>
                          {status}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Tooltip title="Restart service">
                            <IconButton
                              size="small"
                              color="primary"
                              onClick={() => handleServiceAction(service.id, 'restart')}
                              sx={{ p: 0.3 }}
                            >
                              <RefreshIcon sx={{ fontSize: '0.8rem' }} />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </Box>
                    </div>
                  );
                })}
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