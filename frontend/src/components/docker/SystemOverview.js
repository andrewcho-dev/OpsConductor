import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  LinearProgress,
  Chip,
  Divider,
} from '@mui/material';
import {
  Computer as ComputerIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import dockerService from '../../services/dockerService';

const SystemOverview = ({ systemInfo, containers, volumes, networks }) => {
  if (!systemInfo) {
    return (
      <Card>
        <CardContent>
          <Typography>Loading system information...</Typography>
        </CardContent>
      </Card>
    );
  }

  const formatBytes = (bytes) => {
    return dockerService.formatBytes(bytes);
  };

  const formatUptime = (seconds) => {
    const days = Math.floor(seconds / (24 * 3600));
    const hours = Math.floor((seconds % (24 * 3600)) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) {
      return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  };

  const getContainerStats = () => {
    const running = containers.filter(c => c.State === 'running').length;
    const stopped = containers.filter(c => c.State === 'exited').length;
    const paused = containers.filter(c => c.State === 'paused').length;
    const other = containers.length - running - stopped - paused;
    
    return { running, stopped, paused, other, total: containers.length };
  };

  const containerStats = getContainerStats();

  return (
    <Box>
      <Grid container spacing={3}>
        {/* System Information */}
        <Grid item xs={12} lg={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ComputerIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  System Information
                </Typography>
              </Box>
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Docker Version
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {systemInfo.ServerVersion || 'N/A'}
                  </Typography>
                </Grid>
                
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    API Version
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {systemInfo.ApiVersion || 'N/A'}
                  </Typography>
                </Grid>
                
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Operating System
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {systemInfo.OperatingSystem || 'N/A'}
                  </Typography>
                </Grid>
                
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Architecture
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {systemInfo.Architecture || 'N/A'}
                  </Typography>
                </Grid>
                
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    CPUs
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {systemInfo.NCPU || 'N/A'}
                  </Typography>
                </Grid>
                
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Total Memory
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {formatBytes(systemInfo.MemTotal || 0)}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Container Statistics */}
        <Grid item xs={12} lg={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <SpeedIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Container Statistics
                </Typography>
              </Box>
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Total Containers
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main' }}>
                    {containerStats.total}
                  </Typography>
                </Grid>
                
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Running
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'success.main' }}>
                    {containerStats.running}
                  </Typography>
                </Grid>
                
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Stopped
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'error.main' }}>
                    {containerStats.stopped}
                  </Typography>
                </Grid>
                
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Paused
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'warning.main' }}>
                    {containerStats.paused}
                  </Typography>
                </Grid>
              </Grid>

              {containerStats.total > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Container Status Distribution
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={(containerStats.running / containerStats.total) * 100}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    {Math.round((containerStats.running / containerStats.total) * 100)}% running
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Storage Information */}
        <Grid item xs={12} lg={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <StorageIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Storage Information
                </Typography>
              </Box>
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Images
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main' }}>
                    {systemInfo.Images || 0}
                  </Typography>
                </Grid>
                
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Volumes
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'secondary.main' }}>
                    {volumes.length}
                  </Typography>
                </Grid>
                
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary">
                    Storage Driver
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {systemInfo.Driver || 'N/A'}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Network Information */}
        <Grid item xs={12} lg={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <MemoryIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Network & Runtime
                </Typography>
              </Box>
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Networks
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'info.main' }}>
                    {networks.length}
                  </Typography>
                </Grid>
                
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Runtime
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {systemInfo.DefaultRuntime || 'runc'}
                  </Typography>
                </Grid>
                
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary">
                    Kernel Version
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {systemInfo.KernelVersion || 'N/A'}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Registry and Security */}
        {systemInfo.RegistryConfig && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  Registry Configuration
                </Typography>
                
                {systemInfo.RegistryConfig.InsecureRegistryCIDRs && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Insecure Registries
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {systemInfo.RegistryConfig.InsecureRegistryCIDRs.map((registry, index) => (
                        <Chip key={index} label={registry} size="small" variant="outlined" />
                      ))}
                    </Box>
                  </Box>
                )}
                
                {systemInfo.RegistryConfig.IndexConfigs && (
                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Index Configs
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {Object.keys(systemInfo.RegistryConfig.IndexConfigs).map((config, index) => (
                        <Chip key={index} label={config} size="small" color="primary" variant="outlined" />
                      ))}
                    </Box>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default SystemOverview;