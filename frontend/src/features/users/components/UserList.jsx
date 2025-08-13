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
  Chip,
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

// Redux selectors and actions
import {
  selectCurrentUser,
  selectIsAuthenticated,
} from '../../../store/slices/authSlice';
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

const UserList = () => {
  const dispatch = useDispatch();
  const currentUser = useSelector(selectCurrentUser);
  const filters = useSelector(selectFilters);
  const pagination = useSelector(selectPagination);
  
  // Local state for search debouncing
  const [searchTerm, setSearchTerm] = useState(filters.users.search);
  
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

  const getRoleColor = (role) => {
    switch (role) {
      case 'administrator':
        return 'error';
      case 'operator':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusColor = (isActive) => {
    return isActive ? 'success' : 'default';
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
    <Box>
      {/* Toolbar */}
      <Toolbar sx={{ pl: 0, pr: 0 }}>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          User Management
        </Typography>
        
        {currentUser?.role === 'administrator' && (
          <Button
            variant="contained"
            startIcon={<PersonAddIcon />}
            onClick={handleCreateUser}
            sx={{ ml: 2 }}
          >
            Add User
          </Button>
        )}
        
        <Tooltip title="Refresh">
          <IconButton onClick={refetch} sx={{ ml: 1 }}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Toolbar>

      {/* Filters */}
      <Box sx={{ mb: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <TextField
          size="small"
          placeholder="Search users..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ minWidth: 250 }}
        />
        
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Role</InputLabel>
          <Select
            value={filters.users.role}
            label="Role"
            onChange={handleRoleFilterChange}
          >
            <MenuItem value="">All Roles</MenuItem>
            <MenuItem value="administrator">Administrator</MenuItem>
            <MenuItem value="operator">Operator</MenuItem>
            <MenuItem value="user">User</MenuItem>
          </Select>
        </FormControl>
        
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Status</InputLabel>
          <Select
            value={filters.users.status}
            label="Status"
            onChange={handleStatusFilterChange}
          >
            <MenuItem value="">All Status</MenuItem>
            <MenuItem value="active">Active</MenuItem>
            <MenuItem value="inactive">Inactive</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Username</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Role</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Last Login</TableCell>
                <TableCell>Created</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : users.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    No users found
                  </TableCell>
                </TableRow>
              ) : (
                users.map((user) => (
                  <TableRow key={user.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {user.username}
                      </Typography>
                    </TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      <Chip
                        label={user.role}
                        color={getRoleColor(user.role)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={user.is_active ? 'Active' : 'Inactive'}
                        color={getStatusColor(user.is_active)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {user.last_login 
                        ? new Date(user.last_login).toLocaleDateString()
                        : 'Never'
                      }
                    </TableCell>
                    <TableCell>
                      {new Date(user.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Edit User">
                        <IconButton
                          size="small"
                          onClick={() => handleEditUser(user)}
                          disabled={
                            currentUser?.role !== 'administrator' && 
                            currentUser?.id !== user.id
                          }
                        >
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      
                      {currentUser?.role === 'administrator' && 
                       currentUser?.id !== user.id && (
                        <Tooltip title="Delete User">
                          <IconButton
                            size="small"
                            onClick={() => handleDeleteUser(user)}
                            color="error"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        <TablePagination
          component="div"
          count={totalCount}
          page={(pagination.users.page - 1)} // Convert to 0-based for MUI
          onPageChange={handlePageChange}
          rowsPerPage={pagination.users.pageSize}
          onRowsPerPageChange={handlePageSizeChange}
          rowsPerPageOptions={[10, 25, 50, 100]}
        />
      </Paper>
    </Box>
  );
};

export default UserList;