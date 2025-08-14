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
  Box,
  IconButton,
  Tooltip,
  Typography,
  TextField,
  FormControl,
  Select,
  MenuItem
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

const UniversalTargetList = ({ 
  targets, 
  onEditTarget, 
  onViewTarget, 
  onDeleteTarget,
  onRefresh 
}) => {
  const theme = useTheme();
  const { addAlert } = useAlert();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const [sortField, setSortField] = useState('name');
  const [sortDirection, setSortDirection] = useState('asc');
  const [columnFilters, setColumnFilters] = useState({});

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







  const handleColumnFilterChange = (columnKey, value) => {
    setColumnFilters(prev => ({
      ...prev,
      [columnKey]: value
    }));
  };

  // Paginated targets
  const paginatedTargets = filteredAndSortedTargets.slice(
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

      {/* Compact Targets Table */}
      <TableContainer className="custom-scrollbar">
        <Table className="compact-table">
          <TableHead>
            {/* Column Headers Row */}
            <TableRow sx={{ backgroundColor: 'grey.100' }}>
              <SortableHeader field="ip_address" sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                IP Address
              </SortableHeader>
              <SortableHeader field="name" sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                Name
              </SortableHeader>
              <SortableHeader field="target_serial" sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                Target Serial
              </SortableHeader>
              <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>OS</TableCell>
              <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>Environment</TableCell>
              <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>Status</TableCell>
              <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>Health</TableCell>
              <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>Method</TableCell>
              <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>Actions</TableCell>
            </TableRow>
            
            {/* Column Filters Row */}
            <TableRow sx={{ backgroundColor: 'grey.50' }}>
              <TableCell sx={{ padding: '4px 8px' }}>
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
              <TableCell sx={{ padding: '4px 8px' }}>
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
              <TableCell sx={{ padding: '4px 8px' }}>
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
              <TableCell sx={{ padding: '4px 8px' }}>
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
              <TableCell sx={{ padding: '4px 8px' }}>
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
              <TableCell sx={{ padding: '4px 8px' }}>
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
                    <MenuItem value="active" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Active</MenuItem>
                    <MenuItem value="inactive" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Inactive</MenuItem>
                    <MenuItem value="maintenance" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Maintenance</MenuItem>
                  </Select>
                </FormControl>
              </TableCell>
              <TableCell sx={{ padding: '4px 8px' }}>
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
              <TableCell sx={{ padding: '4px 8px' }}>
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
              <TableCell sx={{ padding: '4px 8px' }}>
                {/* No filter for Actions column */}
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedTargets.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  <div className="empty-state">
                    <ComputerIcon className="empty-state-icon" />
                    <Typography variant="body2" color="text.secondary">
                      {Object.values(columnFilters).some(filter => filter)
                        ? 'No targets match the current filters'
                        : 'No targets found. Create your first target to get started.'}
                    </Typography>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              paginatedTargets.map((target) => (
                <TableRow 
                  key={target.id} 
                  hover
                  sx={getHealthRowStyling(target.health_status, theme)}
                >
                  <TableCell sx={getTableCellStyle(true)}>
                    {target.ip_address || 'N/A'}
                  </TableCell>
                  
                  <TableCell sx={getTableCellStyle()}>
                    {target.name}
                    {target.description && ` - ${target.description}`}
                  </TableCell>
                  
                  <TableCell sx={getTableCellStyle()}>
                    {target.target_serial || `ID-${target.id}`}
                  </TableCell>
                  
                  <TableCell sx={getTableCellStyle()}>
                    {target.os_type?.toUpperCase() || 'N/A'}
                  </TableCell>
                  
                  <TableCell sx={getTableCellStyle()}>
                    {target.environment}
                  </TableCell>
                  
                  <TableCell sx={getTableCellStyle()}>
                    {target.status}
                  </TableCell>
                  
                  <TableCell sx={getTableCellStyle()}>
                    {target.health_status}
                  </TableCell>
                  
                  <TableCell sx={getTableCellStyle()}>
                    {target.primary_method || 'N/A'}
                  </TableCell>
                  
                  <TableCell>
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

      {/* Compact Pagination */}
      {filteredAndSortedTargets.length > 0 && (
        <TablePagination
          rowsPerPageOptions={[5, 10, 25, 50]}
          component="div"
          count={filteredAndSortedTargets.length}
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