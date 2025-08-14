/**
 * Standardized Search Card Component
 * Provides a compact, consistent search interface across the system
 */
import React from 'react';
import {
  Card,
  CardContent,
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Box
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';

const SearchCard = ({
  searchValue,
  onSearchChange,
  searchPlaceholder = "Search...",
  filters = [],
  actions = [],
  children,
  ...props
}) => {
  return (
    <Card variant="outlined" {...props}>
      <CardContent sx={{ py: 2, '&:last-child': { pb: 2 } }}>
        <Grid container spacing={2} alignItems="center">
          {/* Search Field */}
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              size="small"
              placeholder={searchPlaceholder}
              value={searchValue}
              onChange={(e) => onSearchChange(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
              }}
            />
          </Grid>
          
          {/* Filters */}
          {filters.map((filter, index) => (
            <Grid item xs={12} md={filter.width || 2} key={index}>
              <FormControl fullWidth size="small">
                <InputLabel>{filter.label}</InputLabel>
                <Select
                  value={filter.value}
                  onChange={filter.onChange}
                  label={filter.label}
                >
                  {filter.options.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          ))}
          
          {/* Actions */}
          {actions.map((action, index) => (
            <Grid item xs={12} md={action.width || 2} key={index}>
              <Button
                fullWidth
                size="small"
                variant={action.variant || "contained"}
                startIcon={action.icon}
                onClick={action.onClick}
                disabled={action.disabled}
                color={action.color}
              >
                {action.label}
              </Button>
            </Grid>
          ))}
          
          {/* Custom children */}
          {children}
        </Grid>
      </CardContent>
    </Card>
  );
};

export default SearchCard;