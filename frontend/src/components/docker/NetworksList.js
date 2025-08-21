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
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  NetworkCheck as NetworkIcon,
  ExpandMore as ExpandMoreIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

const NetworksList = ({ networks, onRefresh }) => {
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getNetworkDriver = (driver) => {
    return driver || 'bridge';
  };

  const getNetworkScope = (scope) => {
    return scope || 'local';
  };

  const getDriverColor = (driver) => {
    switch (driver) {
      case 'bridge':
        return 'primary';
      case 'host':
        return 'secondary';
      case 'overlay':
        return 'success';
      case 'none':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatIPAM = (ipam) => {
    if (!ipam || !ipam.Config || ipam.Config.length === 0) {
      return 'No IPAM configuration';
    }
    
    return ipam.Config.map((config, index) => (
      <Box key={index} sx={{ mb: 1 }}>
        {config.Subnet && (
          <Typography variant="body2">
            <strong>Subnet:</strong> {config.Subnet}
          </Typography>
        )}
        {config.Gateway && (
          <Typography variant="body2">
            <strong>Gateway:</strong> {config.Gateway}
          </Typography>
        )}
        {config.IPRange && (
          <Typography variant="body2">
            <strong>IP Range:</strong> {config.IPRange}
          </Typography>
        )}
      </Box>
    ));
  };

  return (
    <Box>
      <Grid container spacing={3}>
        {networks.map((network) => (
          <Grid item xs={12} md={6} lg={4} key={network.Id}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                  <NetworkIcon sx={{ mr: 1, mt: 0.5, color: 'primary.main' }} />
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" component="h3" sx={{ fontWeight: 600, fontSize: '1rem' }}>
                      {network.Name}
                    </Typography>
                  </Box>
                </Box>

                <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                  <Chip 
                    label={getNetworkDriver(network.Driver)} 
                    size="small"
                    color={getDriverColor(network.Driver)}
                  />
                  <Chip 
                    label={getNetworkScope(network.Scope)} 
                    size="small"
                    variant="outlined"
                  />
                </Box>

                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  <strong>ID:</strong> {network.Id.substring(0, 12)}...
                </Typography>

                {network.Created && (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    <strong>Created:</strong> {formatDate(network.Created)}
                  </Typography>
                )}

                {/* Connected Containers */}
                {network.Containers && Object.keys(network.Containers).length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      <strong>Connected Containers:</strong>
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {Object.entries(network.Containers).map(([containerId, containerInfo]) => (
                        <Chip
                          key={containerId}
                          label={containerInfo.Name || containerId.substring(0, 8)}
                          size="small"
                          variant="outlined"
                          color="success"
                          sx={{ fontSize: '0.7rem' }}
                        />
                      ))}
                    </Box>
                  </Box>
                )}

                {/* IPAM Configuration */}
                {network.IPAM && (
                  <Accordion sx={{ mt: 2 }}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        IPAM Configuration
                      </Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        <strong>Driver:</strong> {network.IPAM.Driver || 'default'}
                      </Typography>
                      {formatIPAM(network.IPAM)}
                    </AccordionDetails>
                  </Accordion>
                )}

                {/* Labels */}
                {network.Labels && Object.keys(network.Labels).length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      <strong>Labels:</strong>
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {Object.entries(network.Labels).map(([key, value]) => (
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

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
                  <Chip 
                    label={network.Internal ? 'Internal' : 'External'} 
                    size="small"
                    color={network.Internal ? 'warning' : 'success'}
                    variant="outlined"
                  />
                  
                  <Tooltip title="Network Information">
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

      {networks.length === 0 && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <NetworkIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              No networks found
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Docker networks will appear here when created
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default NetworksList;