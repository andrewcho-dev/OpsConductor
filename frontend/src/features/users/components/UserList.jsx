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
import ColumnFilters from '../../../components/common/ColumnFilters';
import { getStatusRowStyling, getTableCellStyle } from '../../../utils/tableUtils';
import { useTheme } from '@mui/material/styles';

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
  const theme = useTheme();
  const dispatch = useDispatch();
  const currentUser = useSelector(selectCurrentUser);
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

  // Column configuration for filters
  const userColumns = [
    {
      key: 'username',
      label: 'Username',
      width: 1.5,
      filterable: true,
      filterType: 'text'
    },
    {
      key: 'email',
      label: 'Email',
      width: 2,
      filterable: true,
      filterType: 'text'
    },
    {
      key: 'role',
      label: 'Role',
      width: 1,
      filterable: true,
      filterType: 'select',
      options: [
        { value: 'administrator', label: 'Administrator' },
        { value: 'operator', label: 'Operator' },
        { value: 'viewer', label: 'Viewer' }
      ]
    },
    {
      key: 'status',
      label: 'Status',
      width: 1,
      filterable: true,
      filterType: 'select',
      options: [
        { value: 'active', label: 'Active' },
        { value: 'inactive', label: 'Inactive' }
      ]
    },
    {
      key: 'last_login',
      label: 'Last Login',
      width: 1.5,
      filterable: true,
      filterType: 'text'
    },
    {
      key: 'created_at',
      label: 'Created',
      width: 1.5,
      filterable: true,
      filterType: 'text'
    },
    {
      key: 'actions',
      label: 'Actions',
      width: 1,
      filterable: false
    }
  ];

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
        
        <RefreshAction onClick={refetch} sx={{ ml: 1 }} />
      </Toolbar>



      {/* Table */}
      <Paper>
        <TableContainer>
          {/* Column Filters */}
          <ColumnFilters
            columns={userColumns}
            filters={columnFilters}
            onFilterChange={handleColumnFilterChange}
          />
          
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