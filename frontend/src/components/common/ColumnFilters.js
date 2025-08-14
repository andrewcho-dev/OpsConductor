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
  IconButton
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
    <Box sx={{ width: '100%' }}>
      {/* Column Headers Row */}
      <Box sx={{ 
        display: 'flex', 
        width: '100%',
        borderBottom: '1px solid',
        borderColor: 'divider',
        backgroundColor: 'grey.100'
      }}>
        {columns.map((column, index) => (
          <Box
            key={`header-${column.key}`}
            sx={{
              flex: column.width || 1,
              minWidth: 0, // Allow flex items to shrink below content size
              maxWidth: `${((column.width || 1) / columns.reduce((sum, col) => sum + (col.width || 1), 0)) * 100}%`,
              padding: '8px',
              borderRight: index < columns.length - 1 ? '1px solid' : 'none',
              borderColor: 'divider',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              minHeight: '40px',
              overflow: 'hidden'
            }}
          >
            <Typography 
              variant="body2" 
              sx={{ 
                fontWeight: 'bold',
                fontSize: '0.75rem',
                textAlign: 'left',
                flex: 1
              }}
            >
              {column.label}
            </Typography>
            {column.sortable && (
              <IconButton
                size="small"
                onClick={() => handleSortClick(column.key)}
                sx={{ 
                  padding: '2px',
                  marginLeft: '4px'
                }}
              >
                {getSortIcon(column.key)}
              </IconButton>
            )}
          </Box>
        ))}
      </Box>

      {/* Filters Row */}
      <Box sx={{ 
        display: 'flex', 
        width: '100%',
        borderBottom: '1px solid',
        borderColor: 'divider',
        backgroundColor: 'grey.50'
      }}>
        {columns.map((column, index) => (
          <Box
            key={`filter-${column.key}`}
            sx={{
              flex: column.width || 1,
              minWidth: 0, // Allow flex items to shrink below content size
              maxWidth: `${((column.width || 1) / columns.reduce((sum, col) => sum + (col.width || 1), 0)) * 100}%`,
              padding: '4px 8px',
              borderRight: index < columns.length - 1 ? '1px solid' : 'none',
              borderColor: 'divider',
              minHeight: '50px',
              display: 'flex',
              alignItems: 'center',
              overflow: 'hidden'
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
          </Box>
        ))}
      </Box>
    </Box>
  );
};

export default ColumnFilters;