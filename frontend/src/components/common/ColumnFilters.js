/**
 * Enhanced Column-Based Filters Component
 * Provides headers, sorting, and filter inputs for each table column
 */
import React from 'react';
import {
  TextField,
  Select,
  MenuItem,
  FormControl,
  Box,
  Typography,
  IconButton,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Paper
} from '@mui/material';
import {
  ArrowUpward as ArrowUpIcon,
  ArrowDownward as ArrowDownIcon,
  UnfoldMore as UnfoldMoreIcon
} from '@mui/icons-material';

const ColumnFilters = ({ 
  columns, 
  filters, 
  onFilterChange, 
  sortField, 
  sortDirection, 
  onSortChange 
}) => {
  // Calculate column width percentages based on column.width values
  const getColumnWidthPercent = (column) => {
    const totalWidth = columns.reduce((sum, col) => sum + (col.width || 1), 0);
    return `${((column.width || 1) / totalWidth) * 100}%`;
  };

  const handleFilterChange = (columnKey, value) => {
    onFilterChange(columnKey, value);
  };

  const handleSortClick = (columnKey) => {
    if (onSortChange) {
      if (sortField === columnKey) {
        // Toggle direction
        const newDirection = sortDirection === 'asc' ? 'desc' : 'asc';
        onSortChange(columnKey, newDirection);
      } else {
        // New column, start with asc
        onSortChange(columnKey, 'asc');
      }
    }
  };

  const getSortIcon = (columnKey) => {
    if (sortField !== columnKey) {
      return <UnfoldMoreIcon sx={{ fontSize: 14, color: 'text.disabled' }} />;
    }
    return sortDirection === 'asc' ? 
      <ArrowUpIcon sx={{ fontSize: 14, color: 'primary.main' }} /> : 
      <ArrowDownIcon sx={{ fontSize: 14, color: 'primary.main' }} />;
  };

  return (
    <Paper variant="outlined" sx={{ 
      border: '1px solid', 
      borderColor: 'divider',
      borderRadius: 1,
      borderBottomLeftRadius: 0,
      borderBottomRightRadius: 0,
      borderBottom: 'none'
    }}>
      <Table size="small" sx={{ tableLayout: 'fixed', width: '100%' }}>
        <TableHead>
          {/* Column Headers Row */}
          <TableRow sx={{ backgroundColor: 'grey.100' }}>
            {columns.map((column) => (
              <TableCell
                key={`header-${column.key}`}
                sx={{
                  fontWeight: 'bold',
                  fontSize: '0.75rem',
                  padding: '8px',
                  borderRight: '1px solid',
                  borderColor: 'divider',
                  width: getColumnWidthPercent(column),
                  minWidth: getColumnWidthPercent(column),
                  maxWidth: getColumnWidthPercent(column),
                  '&:last-child': {
                    borderRight: 'none'
                  }
                }}
              >
                <Box sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'space-between' 
                }}>
                  <Typography variant="body2" sx={{ fontWeight: 'bold', fontSize: '0.75rem' }}>
                    {column.label}
                  </Typography>
                  {column.sortable && (
                    <IconButton
                      size="small"
                      onClick={() => handleSortClick(column.key)}
                      sx={{ padding: '2px', marginLeft: '4px' }}
                    >
                      {getSortIcon(column.key)}
                    </IconButton>
                  )}
                </Box>
              </TableCell>
            ))}
          </TableRow>
          
          {/* Filters Row */}
          <TableRow sx={{ backgroundColor: 'grey.50' }}>
            {columns.map((column) => (
              <TableCell
                key={`filter-${column.key}`}
                sx={{
                  padding: '4px 8px',
                  borderRight: '1px solid',
                  borderColor: 'divider',
                  minHeight: '50px',
                  verticalAlign: 'middle',
                  width: getColumnWidthPercent(column),
                  minWidth: getColumnWidthPercent(column),
                  maxWidth: getColumnWidthPercent(column),
                  '&:last-child': {
                    borderRight: 'none'
                  }
                }}
              >
            {column.filterable && (
              <>
                {column.key === 'timestamp' ? (
                  // Special timestamp range filter with two stacked fields
                  <Box sx={{ 
                    width: '100%', 
                    maxWidth: '100%',
                    display: 'flex', 
                    flexDirection: 'column', 
                    gap: '2px',
                    overflow: 'hidden'
                  }}>
                    <TextField
                      size="small"
                      fullWidth
                      type="datetime-local"
                      value={filters[`${column.key}_start`] || ''}
                      onChange={(e) => handleFilterChange(`${column.key}_start`, e.target.value)}
                      sx={{
                        '& .MuiInputBase-input': {
                          fontFamily: 'monospace',
                          fontSize: '0.75rem',
                          padding: '1px 2px',
                          height: '14px'
                        },
                        '& .MuiOutlinedInput-root': {
                          '& fieldset': {
                            borderColor: 'grey.300'
                          }
                        }
                      }}
                    />
                    <TextField
                      size="small"
                      fullWidth
                      type="datetime-local"
                      value={filters[`${column.key}_end`] || ''}
                      onChange={(e) => handleFilterChange(`${column.key}_end`, e.target.value)}
                      sx={{
                        '& .MuiInputBase-input': {
                          fontFamily: 'monospace',
                          fontSize: '0.75rem',
                          padding: '1px 2px',
                          height: '14px'
                        },
                        '& .MuiOutlinedInput-root': {
                          '& fieldset': {
                            borderColor: 'grey.300'
                          }
                        }
                      }}
                    />
                  </Box>
                ) : column.filterType === 'select' ? (
                  <FormControl size="small" fullWidth>
                    <Select
                      value={filters[column.key] || ''}
                      onChange={(e) => handleFilterChange(column.key, e.target.value)}
                      displayEmpty
                      sx={{
                        fontFamily: 'monospace',
                        fontSize: '0.75rem',
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
                        <em>All {column.label}</em>
                      </MenuItem>
                      {column.options?.map((option) => (
                        <MenuItem 
                          key={option.value} 
                          value={option.value}
                          sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}
                        >
                          {option.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                ) : (
                  <TextField
                    size="small"
                    fullWidth
                    placeholder={`Filter ${column.label}...`}
                    value={filters[column.key] || ''}
                    onChange={(e) => handleFilterChange(column.key, e.target.value)}
                    sx={{
                      '& .MuiInputBase-input': {
                        fontFamily: 'monospace',
                        fontSize: '0.75rem',
                        padding: '2px 4px'
                      },
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': {
                          borderColor: 'grey.300'
                        }
                      }
                    }}
                  />
                )}
              </>
            )}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
      </Table>
    </Paper>
  );
};

export default ColumnFilters;