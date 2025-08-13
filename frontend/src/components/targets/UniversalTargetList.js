/**
 * Universal Target List
 * Displays targets in a table with search, filter, and action capabilities.
 */
import React, { useState, useMemo } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  Box,
  Chip,
  IconButton,
  Tooltip,
  Typography,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert
} from '@mui/material';
import {
  Search as SearchIcon,
  Edit as EditIcon,
  Visibility as VisibilityIcon,
  Computer as ComputerIcon,
  Delete as DeleteIcon,
  ArrowUpward as ArrowUpwardIcon,
  ArrowDownward as ArrowDownwardIcon
} from '@mui/icons-material';

import { deleteTarget } from '../../services/targetService';
import { useAlert } from '../layout/BottomStatusBar';

const UniversalTargetList = ({ 
  targets, 
  onEditTarget, 
  onViewTarget, 
  onDeleteTarget,
  onRefresh 
}) => {
  const { addAlert } = useAlert();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [osFilter, setOSFilter] = useState('all');
  const [environmentFilter, setEnvironmentFilter] = useState('all');
  const [sortField, setSortField] = useState('name');
  const [sortDirection, setSortDirection] = useState('asc');

  // Filter, search, and sort targets
  const filteredTargets = useMemo(() => {
    const filtered = targets.filter(target => {
      const matchesSearch = 
        target.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        target.ip_address?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        target.description?.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesStatus = statusFilter === 'all' || target.status === statusFilter;
      const matchesOS = osFilter === 'all' || target.os_type === osFilter;
      const matchesEnvironment = environmentFilter === 'all' || target.environment === environmentFilter;
      
      return matchesSearch && matchesStatus && matchesOS && matchesEnvironment;
    });

    // Sort the filtered results
    return filtered.sort((a, b) => {
      let aValue = a[sortField];
      let bValue = b[sortField];
      
      // Handle null/undefined values
      if (aValue == null) aValue = '';
      if (bValue == null) bValue = '';
      
      // Convert to strings for comparison
      aValue = String(aValue).toLowerCase();
      bValue = String(bValue).toLowerCase();
      
      if (sortDirection === 'asc') {
        return aValue.localeCompare(bValue);
      } else {
        return bValue.localeCompare(aValue);
      }
    });
  }, [targets, searchTerm, statusFilter, osFilter, environmentFilter, sortField, sortDirection]);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleDeleteTarget = async (target) => {
    if (window.confirm(`Are you sure you want to delete target "${target.name}"?`)) {
      try {
        await deleteTarget(target.id);
        onDeleteTarget();
      } catch (err) {
        addAlert(`Failed to delete target: ${err.message}`, 'error', 0);
      }
    }
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

  // Sortable header component
  const SortableHeader = ({ field, children, ...props }) => (
    <TableCell 
      {...props}
      onClick={() => handleSort(field)}
      sx={{ 
        cursor: 'pointer', 
        userSelect: 'none',
        '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.04)' }
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
        {children}
        {sortField === field && (
          sortDirection === 'asc' ? 
            <ArrowUpwardIcon sx={{ fontSize: 14 }} /> : 
            <ArrowDownwardIcon sx={{ fontSize: 14 }} />
        )}
      </Box>
    </TableCell>
  );

  return (
    <Box>
      {/* Compact Search and Filters */}
      <div className="filters-container">
        <TextField
          className="search-field form-control-compact"
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
        />
        
        <FormControl className="filter-item form-control-compact" size="small">
          <InputLabel>Status</InputLabel>
          <Select
            value={statusFilter}
            label="Status"
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <MenuItem value="all">All Status</MenuItem>
            <MenuItem value="active">Active</MenuItem>
            <MenuItem value="inactive">Inactive</MenuItem>
            <MenuItem value="maintenance">Maintenance</MenuItem>
          </Select>
        </FormControl>
        
        <FormControl className="filter-item form-control-compact" size="small">
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
        
        <FormControl className="filter-item form-control-compact" size="small">
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
      </div>

      {/* Results Summary */}
      <Typography className="results-summary">
        Showing {filteredTargets.length} of {targets.length} targets
      </Typography>

      {/* Compact Targets Table */}
      <TableContainer className="custom-scrollbar">
        <Table className="compact-table">
          <TableHead>
            <TableRow>
              <SortableHeader field="ip_address">IP Address</SortableHeader>
              <SortableHeader field="name">Name</SortableHeader>
              <SortableHeader field="target_serial">Target Serial</SortableHeader>
              <TableCell>OS</TableCell>
              <TableCell>Environment</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Health</TableCell>
              <TableCell>Method</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedTargets.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  <div className="empty-state">
                    <ComputerIcon className="empty-state-icon" />
                    <Typography variant="body2" color="text.secondary">
                      {searchTerm || statusFilter !== 'all' || osFilter !== 'all' || environmentFilter !== 'all'
                        ? 'No targets match the current filters'
                        : 'No targets found. Create your first target to get started.'}
                    </Typography>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              paginatedTargets.map((target) => (
                <TableRow key={target.id} hover>
                  <TableCell>
                    <Typography variant="body2" className="font-mono">
                      {target.ip_address || 'N/A'}
                    </Typography>
                  </TableCell>
                  
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getOSIcon(target.os_type)}
                      <Box>
                        <Typography variant="body2" className="font-weight-bold">
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
                    <Typography variant="body2" sx={{ 
                      fontFamily: 'monospace',
                      fontWeight: 600,
                      fontSize: '0.8rem',
                      color: 'primary.main'
                    }}>
                      {target.target_serial || `ID-${target.id}`}
                    </Typography>
                  </TableCell>
                  
                  <TableCell>
                    <Chip 
                      className="chip-compact"
                      label={target.os_type?.toUpperCase() || 'N/A'} 
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  
                  <TableCell>
                    <Chip 
                      className="chip-compact"
                      label={target.environment} 
                      size="small"
                      color={target.environment === 'staging' ? 'warning' : 'default'}
                    />
                  </TableCell>
                  
                  <TableCell>
                    <Chip 
                      className="chip-compact"
                      label={target.status} 
                      size="small"
                      color={getStatusColor(target.status)}
                    />
                  </TableCell>
                  
                  <TableCell>
                    <Chip 
                      className="chip-compact"
                      label={target.health_status} 
                      size="small"
                      color={getHealthColor(target.health_status)}
                    />
                  </TableCell>
                  
                  <TableCell>
                    <Typography variant="body2" className="text-uppercase">
                      {target.primary_method || 'N/A'}
                    </Typography>
                  </TableCell>
                  
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <Tooltip title="View Details">
                        <IconButton 
                          className="btn-icon"
                          size="small" 
                          onClick={() => onViewTarget(target)}
                        >
                          <VisibilityIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      
                      <Tooltip title="Edit Target">
                        <IconButton 
                          className="btn-icon"
                          size="small" 
                          onClick={() => onEditTarget(target)}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      
                      <Tooltip title="Delete Target">
                        <IconButton 
                          className="btn-icon"
                          size="small" 
                          onClick={() => handleDeleteTarget(target)}
                          color="error"
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Compact Pagination */}
      {filteredTargets.length > 0 && (
        <TablePagination
          rowsPerPageOptions={[5, 10, 25, 50]}
          component="div"
          count={filteredTargets.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          sx={{
            '& .MuiTablePagination-toolbar': {
              minHeight: '40px',
              padding: '0 8px',
            },
            '& .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows': {
              fontSize: '0.75rem',
            },
            '& .MuiTablePagination-select': {
              fontSize: '0.75rem',
            }
          }}
        />
      )}
    </Box>
  );
};

export default UniversalTargetList;