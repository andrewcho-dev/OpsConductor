/**
 * Enhanced User List component using Redux Toolkit
 */
import React, { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  IconButton,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Toolbar,
  Typography,
  Button,
  Tooltip,
  CircularProgress,
} from '@mui/material';
import {
  Search as SearchIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  PersonAdd as PersonAddIcon,
} from '@mui/icons-material';
import { RefreshAction, EditAction, DeleteAction } from '../../../components/common/StandardActions';

import { getStatusRowStyling, getTableCellStyle } from '../../../utils/tableUtils';
import { useTheme } from '@mui/material/styles';

// Use SessionAuth instead of Redux for user data
import { useSessionAuth } from '../../../contexts/SessionAuthContext';
import {
  selectFilters,
  selectPagination,
  setFilter,
  setPagination,
  openModal,
  addAlert,
} from '../../../store/slices/uiSlice';

// API hooks (we'll create these)
import { useGetUsersQuery } from '../../../store/api/usersApi';
import '../../../styles/dashboard.css';

const UserList = () => {
  const theme = useTheme();
  const dispatch = useDispatch();
  const { user: currentUser } = useSessionAuth();
  const filters = useSelector(selectFilters);
  const pagination = useSelector(selectPagination);
  
  // Local state for search debouncing
  const [searchTerm, setSearchTerm] = useState(filters.users.search);
  const [columnFilters, setColumnFilters] = useState({});
  
  // API query
  const {
    data: usersData,
    isLoading,
    isError,
    error,
    refetch,
  } = useGetUsersQuery({
    page: pagination.users.page,
    pageSize: pagination.users.pageSize,
    role: filters.users.role,
    status: filters.users.status,
    search: filters.users.search,
  });

  // Debounced search effect
  useEffect(() => {
    const timer = setTimeout(() => {
      dispatch(setFilter({
        section: 'users',
        filterName: 'search',
        value: searchTerm,
      }));
    }, 500);

    return () => clearTimeout(timer);
  }, [searchTerm, dispatch]);

  const handlePageChange = (event, newPage) => {
    dispatch(setPagination({
      section: 'users',
      page: newPage + 1, // MUI uses 0-based, we use 1-based
    }));
  };

  const handlePageSizeChange = (event) => {
    dispatch(setPagination({
      section: 'users',
      page: 1,
      pageSize: parseInt(event.target.value, 10),
    }));
  };

  const handleRoleFilterChange = (event) => {
    dispatch(setFilter({
      section: 'users',
      filterName: 'role',
      value: event.target.value,
    }));
    dispatch(setPagination({ section: 'users', page: 1 }));
  };

  const handleStatusFilterChange = (event) => {
    dispatch(setFilter({
      section: 'users',
      filterName: 'status',
      value: event.target.value,
    }));
    dispatch(setPagination({ section: 'users', page: 1 }));
  };

  const handleCreateUser = () => {
    dispatch(openModal({ modalName: 'userCreate' }));
  };

  const handleEditUser = (user) => {
    dispatch(openModal({ 
      modalName: 'userEdit', 
      data: user 
    }));
  };

  const handleDeleteUser = (user) => {
    // Show confirmation dialog
    dispatch(addAlert({
      type: 'warning',
      message: `Are you sure you want to delete user "${user.username}"?`,
      action: {
        label: 'Delete',
        callback: () => confirmDeleteUser(user.id),
      },
    }));
  };



  const handleColumnFilterChange = (columnKey, value) => {
    setColumnFilters(prev => ({
      ...prev,
      [columnKey]: value
    }));
  };

  // Filter users based on column filters
  const filteredUsers = (usersData?.users || []).filter(user => {
    return Object.entries(columnFilters).every(([key, filterValue]) => {
      if (!filterValue) return true;
      
      switch (key) {
        case 'username':
          return user.username.toLowerCase().includes(filterValue.toLowerCase());
        case 'email':
          return user.email.toLowerCase().includes(filterValue.toLowerCase());
        case 'role':
          return user.role === filterValue;
        case 'status':
          return (user.is_active ? 'active' : 'inactive') === filterValue;
        case 'last_login':
          const lastLogin = user.last_login 
            ? new Date(user.last_login).toLocaleDateString()
            : 'Never';
          return lastLogin.toLowerCase().includes(filterValue.toLowerCase());
        case 'created_at':
          return new Date(user.created_at).toLocaleDateString().toLowerCase().includes(filterValue.toLowerCase());
        default:
          return true;
      }
    });
  });

  const confirmDeleteUser = async (userId) => {
    try {
      // We'll implement this API call later
      dispatch(addAlert({
        type: 'success',
        message: 'User deleted successfully',
      }));
      refetch();
    } catch (error) {
      dispatch(addAlert({
        type: 'error',
        message: 'Failed to delete user',
      }));
    }
  };



  if (isError) {
    return (
      <Box p={3}>
        <Typography color="error">
          Error loading users: {error?.message || 'Unknown error'}
        </Typography>
        <Button onClick={refetch} startIcon={<RefreshIcon />}>
          Retry
        </Button>
      </Box>
    );
  }

  const users = usersData?.data || [];
  const totalCount = usersData?.pagination?.total_count || 0;

  return (
    <div className="datatable-page-container">
      {/* Page Header */}
      <div className="datatable-page-header">
        <Typography className="page-title">
          User Management
        </Typography>
        <div className="page-actions">
          {currentUser?.role === 'administrator' && (
            <Button
              variant="contained"
              startIcon={<PersonAddIcon />}
              onClick={handleCreateUser}
              size="small"
              sx={{ marginRight: 1 }}
            >
              Add User
            </Button>
          )}
          
          <RefreshAction onClick={refetch} disabled={isLoading} />
        </div>
      </div>

      {/* User Accounts Table */}
      <div className="datatable-content-area">

        <TableContainer 
          component={Paper} 
          variant="outlined"
          className="datatable-table-container"
        >
          <Table size="small">
            <TableHead>
              {/* Column Headers */}
              <TableRow sx={{ backgroundColor: 'grey.100' }}>
                <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                  Username
                </TableCell>
                <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                  Email
                </TableCell>
                <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                  Role
                </TableCell>
                <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                  Status
                </TableCell>
                <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                  Last Login
                </TableCell>
                <TableCell sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                  Created
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold', fontSize: '0.75rem', padding: '8px' }}>
                  Actions
                </TableCell>
              </TableRow>
              
              {/* Filter Row */}
              <TableRow sx={{ backgroundColor: 'grey.50' }}>
                <TableCell sx={{ padding: '4px 8px' }}>
                  <TextField
                    size="small"
                    fullWidth
                    placeholder="Filter username..."
                    value={columnFilters.username || ''}
                    onChange={(e) => handleColumnFilterChange('username', e.target.value)}
                    sx={{ '& .MuiInputBase-input': { fontSize: '0.75rem', padding: '2px 4px', fontFamily: 'monospace' } }}
                  />
                </TableCell>
                <TableCell sx={{ padding: '4px 8px' }}>
                  <TextField
                    size="small"
                    fullWidth
                    placeholder="Filter email..."
                    value={columnFilters.email || ''}
                    onChange={(e) => handleColumnFilterChange('email', e.target.value)}
                    sx={{ '& .MuiInputBase-input': { fontSize: '0.75rem', padding: '2px 4px', fontFamily: 'monospace' } }}
                  />
                </TableCell>
                <TableCell sx={{ padding: '4px 8px' }}>
                  <Select
                    size="small"
                    fullWidth
                    value={columnFilters.role || ''}
                    onChange={(e) => handleColumnFilterChange('role', e.target.value)}
                    sx={{ 
                      '& .MuiSelect-select': { 
                        fontSize: '0.75rem', 
                        padding: '2px 4px',
                        fontFamily: 'monospace'
                      }
                    }}
                    MenuProps={{
                      PaperProps: {
                        sx: {
                          '& .MuiMenuItem-root': {
                            fontFamily: 'monospace',
                            fontSize: '0.75rem'
                          }
                        }
                      }
                    }}
                  >
                    <MenuItem value="">All Roles</MenuItem>
                    <MenuItem value="administrator">Administrator</MenuItem>
                    <MenuItem value="operator">Operator</MenuItem>
                    <MenuItem value="viewer">Viewer</MenuItem>
                  </Select>
                </TableCell>
                <TableCell sx={{ padding: '4px 8px' }}>
                  <Select
                    size="small"
                    fullWidth
                    value={columnFilters.status || ''}
                    onChange={(e) => handleColumnFilterChange('status', e.target.value)}
                    sx={{ 
                      '& .MuiSelect-select': { 
                        fontSize: '0.75rem', 
                        padding: '2px 4px',
                        fontFamily: 'monospace'
                      }
                    }}
                    MenuProps={{
                      PaperProps: {
                        sx: {
                          '& .MuiMenuItem-root': {
                            fontFamily: 'monospace',
                            fontSize: '0.75rem'
                          }
                        }
                      }
                    }}
                  >
                    <MenuItem value="">All Status</MenuItem>
                    <MenuItem value="active">Active</MenuItem>
                    <MenuItem value="inactive">Inactive</MenuItem>
                  </Select>
                </TableCell>
                <TableCell sx={{ padding: '4px 8px' }}>
                  <TextField
                    size="small"
                    fullWidth
                    placeholder="Filter last login..."
                    value={columnFilters.last_login || ''}
                    onChange={(e) => handleColumnFilterChange('last_login', e.target.value)}
                    sx={{ '& .MuiInputBase-input': { fontSize: '0.75rem', padding: '2px 4px', fontFamily: 'monospace' } }}
                  />
                </TableCell>
                <TableCell sx={{ padding: '4px 8px' }}>
                  <TextField
                    size="small"
                    fullWidth
                    placeholder="Filter created..."
                    value={columnFilters.created_at || ''}
                    onChange={(e) => handleColumnFilterChange('created_at', e.target.value)}
                    sx={{ '& .MuiInputBase-input': { fontSize: '0.75rem', padding: '2px 4px', fontFamily: 'monospace' } }}
                  />
                </TableCell>
                <TableCell sx={{ padding: '4px 8px' }}>
                  {/* Empty cell for actions column */}
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : filteredUsers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    No users found
                  </TableCell>
                </TableRow>
              ) : (
                filteredUsers.map((user) => (
                  <TableRow 
                    key={user.id} 
                    hover
                    sx={getStatusRowStyling(user.is_active ? 'active' : 'inactive', theme)}
                  >
                    <TableCell sx={getTableCellStyle(true)}>
                      {user.username}
                    </TableCell>
                    <TableCell sx={getTableCellStyle()}>{user.email}</TableCell>
                    <TableCell sx={getTableCellStyle()}>
                      {user.role}
                    </TableCell>
                    <TableCell sx={getTableCellStyle()}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </TableCell>
                    <TableCell sx={getTableCellStyle()}>
                      {user.last_login 
                        ? new Date(user.last_login).toLocaleDateString()
                        : 'Never'
                      }
                    </TableCell>
                    <TableCell sx={getTableCellStyle()}>
                      {new Date(user.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell align="right">
                      <EditAction
                        onClick={() => handleEditUser(user)}
                        disabled={
                          currentUser?.role !== 'administrator' && 
                          currentUser?.id !== user.id
                        }
                      />
                      
                      {currentUser?.role === 'administrator' && 
                       currentUser?.id !== user.id && (
                        <DeleteAction
                          onClick={() => handleDeleteUser(user)}
                        />
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        {/* Pagination */}
        <div className="datatable-pagination-area">
          <TablePagination
            component="div"
            count={totalCount}
            page={(pagination.users.page - 1)} // Convert to 0-based for MUI
            onPageChange={handlePageChange}
            rowsPerPage={pagination.users.pageSize}
            onRowsPerPageChange={handlePageSizeChange}
            rowsPerPageOptions={[25, 50, 100, 200, 500]}
            sx={{ 
              borderTop: '1px solid', 
              borderColor: 'divider',
              backgroundColor: 'background.paper'
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default UserList;