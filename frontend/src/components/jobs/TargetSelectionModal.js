/**
 * Target Selection Modal - Based on UniversalTargetList but with selection capabilities
 * Reuses the same table structure and filtering as the main target screen
 */
import React, { useState, useEffect, useMemo } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  IconButton,
  Checkbox,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  CircularProgress
} from '@mui/material';
import {
  Close as CloseIcon,
  Search as SearchIcon,
  Computer as ComputerIcon
} from '@mui/icons-material';

import { useAuth } from '../../contexts/AuthContext';

const TargetSelectionModal = ({ open, onClose, selectedTargetIds = [], onSelectionChange }) => {
  const { token } = useAuth();
  const [targets, setTargets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [osFilter, setOSFilter] = useState('all');
  const [environmentFilter, setEnvironmentFilter] = useState('all');
  const [localSelectedIds, setLocalSelectedIds] = useState(selectedTargetIds);

  useEffect(() => {
    if (open) {
      fetchTargets();
      setLocalSelectedIds(selectedTargetIds);
    }
  }, [open, selectedTargetIds]);

  const fetchTargets = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/targets/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      if (response.ok) {
        const data = await response.json();
        setTargets(data.targets || data || []);
      }
    } catch (error) {
      console.error('Failed to fetch targets:', error);
    } finally {
      setLoading(false);
    }
  };

  // Filter and search targets (same as UniversalTargetList)
  const filteredTargets = useMemo(() => {
    return targets.filter(target => {
      const matchesSearch = 
        target.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        target.ip_address?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        target.description?.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesStatus = statusFilter === 'all' || target.status === statusFilter;
      const matchesOS = osFilter === 'all' || target.os_type === osFilter;
      const matchesEnvironment = environmentFilter === 'all' || target.environment === environmentFilter;
      
      return matchesSearch && matchesStatus && matchesOS && matchesEnvironment;
    });
  }, [targets, searchTerm, statusFilter, osFilter, environmentFilter]);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleTargetToggle = (targetId) => {
    const newSelection = localSelectedIds.includes(targetId)
      ? localSelectedIds.filter(id => id !== targetId)
      : [...localSelectedIds, targetId];
    
    setLocalSelectedIds(newSelection);
  };

  const handleSelectAll = () => {
    const paginatedTargets = filteredTargets.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);
    const allPageIds = paginatedTargets.map(t => t.id);
    const allPageSelected = allPageIds.every(id => localSelectedIds.includes(id));
    
    if (allPageSelected) {
      // Deselect all on current page
      setLocalSelectedIds(localSelectedIds.filter(id => !allPageIds.includes(id)));
    } else {
      // Select all on current page
      const newSelection = [...new Set([...localSelectedIds, ...allPageIds])];
      setLocalSelectedIds(newSelection);
    }
  };

  const handleConfirm = () => {
    onSelectionChange(localSelectedIds);
    onClose();
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'default';
      case 'maintenance': return 'warning';
      default: return 'default';
    }
  };

  const getHealthColor = (healthStatus) => {
    switch (healthStatus) {
      case 'healthy': return 'success';
      case 'warning': return 'warning';
      case 'critical': return 'error';
      default: return 'default';
    }
  };

  const getOSIcon = (osType) => {
    return <ComputerIcon fontSize="small" />;
  };

  // Paginated targets
  const paginatedTargets = filteredTargets.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  const selectedCount = localSelectedIds.length;
  const allPageSelected = paginatedTargets.length > 0 && paginatedTargets.every(t => localSelectedIds.includes(t.id));

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="lg" 
      fullWidth
      PaperProps={{
        sx: { 
          height: '90vh',
          maxHeight: '800px'
        }
      }}
    >
      <DialogTitle sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        pb: 1
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ComputerIcon />
          <Typography variant="h6">
            Select Targets ({selectedCount} selected)
          </Typography>
        </Box>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ p: 0 }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Box sx={{ p: 2 }}>
            {/* Compact Search and Filters - Same as UniversalTargetList */}
            <Box sx={{ 
              display: 'flex', 
              gap: 2, 
              mb: 2, 
              flexWrap: 'wrap',
              alignItems: 'center'
            }}>
              <TextField
                placeholder="Search targets..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon fontSize="small" />
                    </InputAdornment>
                  ),
                }}
                size="small"
                sx={{ minWidth: '200px', flex: 1 }}
              />
              
              <FormControl size="small" sx={{ minWidth: '120px' }}>
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  label="Status"
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <MenuItem value="all">All Status</MenuItem>
                  <MenuItem value="active">active</MenuItem>
                  <MenuItem value="inactive">inactive</MenuItem>
                  <MenuItem value="maintenance">maintenance</MenuItem>
                </Select>
              </FormControl>
              
              <FormControl size="small" sx={{ minWidth: '120px' }}>
                <InputLabel>OS Type</InputLabel>
                <Select
                  value={osFilter}
                  label="OS Type"
                  onChange={(e) => setOSFilter(e.target.value)}
                >
                  <MenuItem value="all">All OS</MenuItem>
                  <MenuItem value="linux">Linux</MenuItem>
                  <MenuItem value="windows">Windows</MenuItem>
                </Select>
              </FormControl>
              
              <FormControl size="small" sx={{ minWidth: '140px' }}>
                <InputLabel>Environment</InputLabel>
                <Select
                  value={environmentFilter}
                  label="Environment"
                  onChange={(e) => setEnvironmentFilter(e.target.value)}
                >
                  <MenuItem value="all">All Environments</MenuItem>
                  <MenuItem value="development">Development</MenuItem>
                  <MenuItem value="testing">Testing</MenuItem>
                  <MenuItem value="staging">Staging</MenuItem>
                </Select>
              </FormControl>
            </Box>

            {/* Results Summary */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Showing {filteredTargets.length} of {targets.length} targets
              </Typography>
              <Button
                size="small"
                onClick={handleSelectAll}
                disabled={paginatedTargets.length === 0}
              >
                {allPageSelected ? 'Deselect Page' : 'Select Page'} ({paginatedTargets.length})
              </Button>
            </Box>

            {/* Targets Table - Same structure as UniversalTargetList */}
            <TableContainer sx={{ maxHeight: '400px', border: '1px solid', borderColor: 'divider' }}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox">
                      <Checkbox
                        indeterminate={selectedCount > 0 && selectedCount < filteredTargets.length}
                        checked={filteredTargets.length > 0 && selectedCount === filteredTargets.length}
                        onChange={handleSelectAll}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>IP Address</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>OS</TableCell>
                    <TableCell>Environment</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Health</TableCell>
                    <TableCell>Method</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedTargets.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
                          <ComputerIcon sx={{ fontSize: 48, color: 'text.disabled' }} />
                          <Typography variant="body2" color="text.secondary">
                            {searchTerm || statusFilter !== 'all' || osFilter !== 'all' || environmentFilter !== 'all'
                              ? 'No targets match the current filters'
                              : 'No targets found. Create your first target to get started.'}
                          </Typography>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ) : (
                    paginatedTargets.map((target) => {
                      const isSelected = localSelectedIds.includes(target.id);
                      return (
                        <TableRow 
                          key={target.id} 
                          hover 
                          selected={isSelected}
                          onClick={() => handleTargetToggle(target.id)}
                          sx={{ cursor: 'pointer' }}
                        >
                          <TableCell padding="checkbox">
                            <Checkbox
                              checked={isSelected}
                              size="small"
                            />
                          </TableCell>
                          
                          <TableCell>
                            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 500 }}>
                              {target.ip_address || 'N/A'}
                            </Typography>
                          </TableCell>
                          
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              {getOSIcon(target.os_type)}
                              <Box>
                                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                  {target.name}
                                </Typography>
                                {target.description && (
                                  <Typography variant="caption" color="text.secondary">
                                    {target.description}
                                  </Typography>
                                )}
                              </Box>
                            </Box>
                          </TableCell>
                          
                          <TableCell>
                            <Chip 
                              label={target.os_type?.toUpperCase() || 'N/A'} 
                              size="small"
                              variant="outlined"
                            />
                          </TableCell>
                          
                          <TableCell>
                            <Chip 
                              label={target.environment || 'N/A'} 
                              size="small"
                              variant="outlined"
                            />
                          </TableCell>
                          
                          <TableCell>
                            <Chip 
                              label={target.status || 'Unknown'} 
                              size="small"
                              color={getStatusColor(target.status)}
                            />
                          </TableCell>
                          
                          <TableCell>
                            <Chip 
                              label={target.health_status || 'Unknown'} 
                              size="small"
                              color={getHealthColor(target.health_status)}
                            />
                          </TableCell>
                          
                          <TableCell>
                            <Typography variant="caption" color="text.secondary">
                              {target.target_type || 'N/A'}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      );
                    })
                  )}
                </TableBody>
              </Table>
            </TableContainer>

            {/* Pagination */}
            <TablePagination
              component="div"
              count={filteredTargets.length}
              page={page}
              onPageChange={handleChangePage}
              rowsPerPage={rowsPerPage}
              onRowsPerPageChange={handleChangeRowsPerPage}
              rowsPerPageOptions={[5, 10, 25, 50]}
              size="small"
            />
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
        <Button onClick={onClose}>
          Cancel
        </Button>
        <Button
          onClick={handleConfirm}
          variant="contained"
          disabled={selectedCount === 0}
        >
          Select {selectedCount} Target{selectedCount !== 1 ? 's' : ''}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default TargetSelectionModal;