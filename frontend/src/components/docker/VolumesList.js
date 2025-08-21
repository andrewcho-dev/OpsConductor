import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Storage as StorageIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import dockerService from '../../services/dockerService';

const VolumesList = ({ volumes, onRefresh }) => {
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getVolumeDriver = (driver) => {
    return driver || 'local';
  };

  const getVolumeMountpoint = (mountpoint) => {
    // Shorten long paths for display
    if (mountpoint && mountpoint.length > 50) {
      return '...' + mountpoint.slice(-47);
    }
    return mountpoint || 'N/A';
  };

  return (
    <Box>
      <Grid container spacing={3}>
        {volumes.map((volume) => (
          <Grid item xs={12} md={6} lg={4} key={volume.Name}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                  <StorageIcon sx={{ mr: 1, mt: 0.5, color: 'primary.main' }} />
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" component="h3" sx={{ fontWeight: 600, fontSize: '1rem' }}>
                      {volume.Name}
                    </Typography>
                  </Box>
                </Box>

                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  <strong>Driver:</strong> {getVolumeDriver(volume.Driver)}
                </Typography>

                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  <strong>Mountpoint:</strong>
                </Typography>
                <Typography 
                  variant="body2" 
                  sx={{ 
                    fontFamily: 'monospace', 
                    fontSize: '0.75rem',
                    backgroundColor: '#f5f5f5',
                    p: 1,
                    borderRadius: 1,
                    mb: 1,
                    wordBreak: 'break-all'
                  }}
                >
                  {getVolumeMountpoint(volume.Mountpoint)}
                </Typography>

                {volume.CreatedAt && (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    <strong>Created:</strong> {formatDate(volume.CreatedAt)}
                  </Typography>
                )}

                {volume.Labels && Object.keys(volume.Labels).length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      <strong>Labels:</strong>
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {Object.entries(volume.Labels).map(([key, value]) => (
                        <Chip
                          key={key}
                          label={`${key}=${value}`}
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.7rem' }}
                        />
                      ))}
                    </Box>
                  </Box>
                )}

                {volume.Options && Object.keys(volume.Options).length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      <strong>Options:</strong>
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {Object.entries(volume.Options).map(([key, value]) => (
                        <Chip
                          key={key}
                          label={`${key}=${value}`}
                          size="small"
                          variant="outlined"
                          color="secondary"
                          sx={{ fontSize: '0.7rem' }}
                        />
                      ))}
                    </Box>
                  </Box>
                )}

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
                  <Chip 
                    label={volume.Scope || 'local'} 
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                  
                  <Tooltip title="Volume Information">
                    <IconButton size="small">
                      <InfoIcon />
                    </IconButton>
                  </Tooltip>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {volumes.length === 0 && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <StorageIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              No volumes found
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Docker volumes will appear here when created
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default VolumesList;