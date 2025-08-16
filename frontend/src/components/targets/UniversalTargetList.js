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
  Box,
  IconButton,
  Tooltip,
  Typography,
  TextField,
  FormControl,
  Select,
  MenuItem,
  Paper,
  Pagination
} from '@mui/material';
import {
  Edit as EditIcon,
  Visibility as VisibilityIcon,
  Computer as ComputerIcon,
  Delete as DeleteIcon,
  ArrowUpward as ArrowUpwardIcon,
  ArrowDownward as ArrowDownwardIcon
} from '@mui/icons-material';

import { deleteTarget } from '../../services/targetService';
import { useAlert } from '../layout/BottomStatusBar';
import { ViewDetailsAction, EditAction, DeleteAction } from '../common/StandardActions';
import { getStatusRowStyling, getHealthRowStyling, getTableCellStyle } from '../../utils/tableUtils';
import { useTheme } from '@mui/material/styles';
import '../../styles/dashboard.css';

const UniversalTargetList = ({ 
  targets, 
  onEditTarget, 
  onViewTarget, 
  onDeleteTarget,
  onRefresh 
}) => {
  const theme = useTheme();
  const { addAlert } = useAlert();
  const [sortField, setSortField] = useState('name');
  const [sortDirection, setSortDirection] = useState('asc');
  const [columnFilters, setColumnFilters] = useState({});
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  // Filter targets based on column filters and sort
  const filteredAndSortedTargets = useMemo(() => {
    // Apply column filters
    const filtered = targets.filter(target => {
      return Object.entries(columnFilters).every(([key, filterValue]) => {
        if (!filterValue) return true;
        
        switch (key) {
          case 'ip_address':
            return (target.ip_address || 'N/A').toLowerCase().includes(filterValue.toLowerCase());
          case 'name':
            const nameDesc = `${target.name}${target.description ? ` - ${target.description}` : ''}`;
            return nameDesc.toLowerCase().includes(filterValue.toLowerCase());
          case 'target_serial':
            return (target.target_serial || `ID-${target.id}`).toLowerCase().includes(filterValue.toLowerCase());
          case 'os_type':
            return target.os_type === filterValue;
          case 'environment':
            return target.environment === filterValue;
          case 'status':
            return target.status === filterValue;
          case 'health_status':
            return target.health_status === filterValue;
          case 'primary_method':
            return (target.primary_method || 'N/A').toLowerCase().includes(filterValue.toLowerCase());
          default:
            return true;
        }
      });
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
  }, [targets, columnFilters, sortField, sortDirection]);

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







  const handleColumnFilterChange = (columnKey, value) => {
    setColumnFilters(prev => ({
      ...prev,
      [columnKey]: value
    }));
  };

  // Calculate pagination
  const totalTargets = filteredAndSortedTargets.length;
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const paginatedTargets = filteredAndSortedTargets.slice(startIndex, endIndex);
  const totalPages = Math.ceil(totalTargets / pageSize);

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
    <div className="table-content-area">
      <TableContainer 
        component={Paper} 
        variant="outlined"
        className="standard-table-container"
      >
        <Table size="small">
          <TableHead>
            {/* Column Headers Row */}
            <TableRow sx={{ backgroundColor: 'grey.100' }}>
              <TableCell className="standard-table-header">
                IP Address
              </TableCell>
              <TableCell className="standard-table-header">
                Name
              </TableCell>
              <TableCell className="standard-table-header">
                Target Serial
              </TableCell>
              <TableCell className="standard-table-header">OS</TableCell>
              <TableCell className="standard-table-header">Environment</TableCell>
              <TableCell className="standard-table-header">Status</TableCell>
              <TableCell className="standard-table-header">Health</TableCell>
              <TableCell className="standard-table-header">Method</TableCell>
              <TableCell className="standard-table-header">Actions</TableCell>
            </TableRow>
            
            {/* Column Filters Row */}
            <TableRow sx={{ backgroundColor: 'grey.50' }}>
              <TableCell className="standard-filter-cell">
                <TextField
                  size="small"
                  placeholder="Filter IP..."
                  value={columnFilters.ip_address || ''}
                  onChange={(e) => handleColumnFilterChange('ip_address', e.target.value)}
                  sx={{
                    '& .MuiInputBase-input': {
                      fontFamily: 'monospace',
                      fontSize: '0.75rem',
                      padding: '2px 4px'
                    }
                  }}
                />
              </TableCell>
              <TableCell className="standard-filter-cell">
                <TextField
                  size="small"
                  placeholder="Filter name..."
                  value={columnFilters.name || ''}
                  onChange={(e) => handleColumnFilterChange('name', e.target.value)}
                  sx={{
                    '& .MuiInputBase-input': {
                      fontFamily: 'monospace',
                      fontSize: '0.75rem',
                      padding: '2px 4px'
                    }
                  }}
                />
              </TableCell>
              <TableCell className="standard-filter-cell">
                <TextField
                  size="small"
                  placeholder="Filter serial..."
                  value={columnFilters.target_serial || ''}
                  onChange={(e) => handleColumnFilterChange('target_serial', e.target.value)}
                  sx={{
                    '& .MuiInputBase-input': {
                      fontFamily: 'monospace',
                      fontSize: '0.75rem',
                      padding: '2px 4px'
                    }
                  }}
                />
              </TableCell>
              <TableCell className="standard-filter-cell">
                <FormControl size="small" fullWidth>
                  <Select
                    value={columnFilters.os_type || ''}
                    onChange={(e) => handleColumnFilterChange('os_type', e.target.value)}
                    displayEmpty
                    sx={{
                      '& .MuiSelect-select': {
                        padding: '2px 4px',
                        fontFamily: 'monospace',
                        fontSize: '0.75rem'
                      }
                    }}
                    MenuProps={{
                      PaperProps: {
                        sx: {
                          '& .MuiMenuItem-root': {
                            fontFamily: 'monospace',
                            fontSize: '0.75rem',
                            minHeight: 'auto',
                            padding: '4px 8px'
                          }
                        }
                      }
                    }}
                  >
                    <MenuItem value="" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                      <em>All OS</em>
                    </MenuItem>
                    <MenuItem value="windows" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Windows</MenuItem>
                    <MenuItem value="linux" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Linux</MenuItem>
                    <MenuItem value="macos" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>macOS</MenuItem>
                    <MenuItem value="unix" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Unix</MenuItem>
                  </Select>
                </FormControl>
              </TableCell>
              <TableCell className="standard-filter-cell">
                <FormControl size="small" fullWidth>
                  <Select
                    value={columnFilters.environment || ''}
                    onChange={(e) => handleColumnFilterChange('environment', e.target.value)}
                    displayEmpty
                    sx={{
                      '& .MuiSelect-select': {
                        padding: '2px 4px',
                        fontFamily: 'monospace',
                        fontSize: '0.75rem'
                      }
                    }}
                    MenuProps={{
                      PaperProps: {
                        sx: {
                          '& .MuiMenuItem-root': {
                            fontFamily: 'monospace',
                            fontSize: '0.75rem',
                            minHeight: 'auto',
                            padding: '4px 8px'
                          }
                        }
                      }
                    }}
                  >
                    <MenuItem value="" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                      <em>All Environments</em>
                    </MenuItem>
                    <MenuItem value="production" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Production</MenuItem>
                    <MenuItem value="staging" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Staging</MenuItem>
                    <MenuItem value="development" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Development</MenuItem>
                    <MenuItem value="testing" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Testing</MenuItem>
                  </Select>
                </FormControl>
              </TableCell>
              <TableCell className="standard-filter-cell">
                <FormControl size="small" fullWidth>
                  <Select
                    value={columnFilters.status || ''}
                    onChange={(e) => handleColumnFilterChange('status', e.target.value)}
                    displayEmpty
                    sx={{
                      '& .MuiSelect-select': {
                        padding: '2px 4px',
                        fontFamily: 'monospace',
                        fontSize: '0.75rem'
                      }
                    }}
                    MenuProps={{
                      PaperProps: {
                        sx: {
                          '& .MuiMenuItem-root': {
                            fontFamily: 'monospace',
                            fontSize: '0.75rem',
                            minHeight: 'auto',
                            padding: '4px 8px'
                          }
                        }
                      }
                    }}
                  >
                    <MenuItem value="" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                      <em>All Status</em>
                    </MenuItem>
                    <MenuItem value="active" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>active</MenuItem>
                    <MenuItem value="inactive" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>inactive</MenuItem>
                    <MenuItem value="maintenance" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>maintenance</MenuItem>
                  </Select>
                </FormControl>
              </TableCell>
              <TableCell className="standard-filter-cell">
                <FormControl size="small" fullWidth>
                  <Select
                    value={columnFilters.health_status || ''}
                    onChange={(e) => handleColumnFilterChange('health_status', e.target.value)}
                    displayEmpty
                    sx={{
                      '& .MuiSelect-select': {
                        padding: '2px 4px',
                        fontFamily: 'monospace',
                        fontSize: '0.75rem'
                      }
                    }}
                    MenuProps={{
                      PaperProps: {
                        sx: {
                          '& .MuiMenuItem-root': {
                            fontFamily: 'monospace',
                            fontSize: '0.75rem',
                            minHeight: 'auto',
                            padding: '4px 8px'
                          }
                        }
                      }
                    }}
                  >
                    <MenuItem value="" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                      <em>All Health</em>
                    </MenuItem>
                    <MenuItem value="healthy" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Healthy</MenuItem>
                    <MenuItem value="degraded" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Degraded</MenuItem>
                    <MenuItem value="unhealthy" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Unhealthy</MenuItem>
                  </Select>
                </FormControl>
              </TableCell>
              <TableCell className="standard-filter-cell">
                <TextField
                  size="small"
                  placeholder="Filter method..."
                  value={columnFilters.primary_method || ''}
                  onChange={(e) => handleColumnFilterChange('primary_method', e.target.value)}
                  sx={{
                    '& .MuiInputBase-input': {
                      fontFamily: 'monospace',
                      fontSize: '0.75rem',
                      padding: '2px 4px'
                    }
                  }}
                />
              </TableCell>
              <TableCell className="standard-filter-cell">
                {/* No filter for Actions column */}
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedTargets.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} align="center" sx={{ py: 4 }}>
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
                    <ComputerIcon sx={{ fontSize: 48, color: 'text.disabled' }} />
                    <Typography variant="body2" color="text.secondary">
                      {Object.values(columnFilters).some(filter => filter)
                        ? 'No targets match the current filters'
                        : 'No targets found. Create your first target to get started.'}
                    </Typography>
                  </Box>
                </TableCell>
              </TableRow>
            ) : (
              paginatedTargets.map((target) => (
                <TableRow 
                  key={target.id} 
                  hover
                  sx={getHealthRowStyling(target.health_status, theme)}
                >
                  <TableCell className="standard-table-cell">
                    {target.ip_address || 'N/A'}
                  </TableCell>
                  
                  <TableCell className="standard-table-cell">
                    {target.name}
                    {target.description && ` - ${target.description}`}
                  </TableCell>
                  
                  <TableCell className="standard-table-cell">
                    {target.target_serial || `ID-${target.id}`}
                  </TableCell>
                  
                  <TableCell className="standard-table-cell">
                    {target.os_type?.toUpperCase() || 'N/A'}
                  </TableCell>
                  
                  <TableCell className="standard-table-cell">
                    {target.environment}
                  </TableCell>
                  
                  <TableCell className="standard-table-cell">
                    {target.status}
                  </TableCell>
                  
                  <TableCell className="standard-table-cell">
                    {target.health_status}
                  </TableCell>
                  
                  <TableCell className="standard-table-cell">
                    {target.primary_method || 'N/A'}
                  </TableCell>
                  
                  <TableCell className="standard-table-cell">
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <ViewDetailsAction onClick={() => onViewTarget(target)} />
                      <EditAction onClick={() => onEditTarget(target)} />
                      <DeleteAction onClick={() => handleDeleteTarget(target)} />
                    </Box>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
      
      {/* Pagination Controls */}
      <div className="standard-pagination-area">
        {/* Page Size Selector */}
        <div className="standard-page-size-selector">
          <Typography variant="body2" className="standard-pagination-info">
            Show:
          </Typography>
          <Select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setCurrentPage(1);
            }}
            size="small"
            className="standard-page-size-selector"
          >
            <MenuItem value={25}>25</MenuItem>
            <MenuItem value={50}>50</MenuItem>
            <MenuItem value={100}>100</MenuItem>
            <MenuItem value={200}>200</MenuItem>
          </Select>
          <Typography variant="body2" className="standard-pagination-info">
            per page
          </Typography>
        </div>

        {/* Pagination */}
        {totalTargets > pageSize && (
          <Pagination
            count={totalPages}
            page={currentPage}
            onChange={(event, page) => {
              setCurrentPage(page);
            }}
            color="primary"
            size="small"
            variant="outlined"
            className="standard-pagination"
          />
        )}
        
        {/* Show pagination info */}
        <Typography variant="body2" className="standard-pagination-info">
          Showing {startIndex + 1}-{Math.min(endIndex, totalTargets)} of {totalTargets} targets
        </Typography>
      </div>
    </div>
  );
};

export default UniversalTargetList;