import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Tooltip,
  Chip,
  Box,
  Paper,
  Grid,
  Card,
  CardContent,
  TablePagination,
  TableSortLabel,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ArrowBack as ArrowBackIcon,
  Refresh as RefreshIcon,
  People as PeopleIcon,
  Person as PersonIcon,
  AdminPanelSettings as AdminIcon,
  Security as SecurityIcon,
  Email as EmailIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { userService } from '../../services/userService';
import { useAlert } from '../layout/BottomStatusBar';
import '../../styles/dashboard.css';

const UserManagementSimplified = () => {
  const { addAlert } = useAlert();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role: 'user',
  });

  // Table state for filtering, sorting, and pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [sortField, setSortField] = useState('username');
  const [sortDirection, setSortDirection] = useState('asc');
  const [columnFilters, setColumnFilters] = useState({});

  const navigate = useNavigate();

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const response = await userService.getUsers();
      setUsers(response || []);
      addAlert(`Loaded ${response.length} users successfully`, 'success', 3000);
    } catch (err) {
      addAlert('Failed to load users', 'error', 0);
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (user = null) => {
    if (user) {
      setEditingUser(user);
      setFormData({
        username: user.username,
        email: user.email,
        password: '',
        role: user.role,
      });
    } else {
      setEditingUser(null);
      setFormData({
        username: '',
        email: '',
        password: '',
        role: 'user',
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingUser(null);
    setFormData({
      username: '',
      email: '',
      password: '',
      role: 'user',
    });
  };

  const handleSubmit = async () => {
    try {
      if (editingUser) {
        await userService.updateUser(editingUser.id, formData);
        addAlert('User updated successfully', 'success', 3000);
      } else {
        await userService.createUser(formData);
        addAlert('User created successfully', 'success', 3000);
      }
      handleCloseDialog();
      loadUsers();
    } catch (err) {
      addAlert('Failed to save user', 'error', 0);
    }
  };

  const handleDelete = async (userId) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await userService.deleteUser(userId);
        addAlert('User deleted successfully', 'success', 3000);
        loadUsers();
      } catch (err) {
        addAlert('Failed to delete user', 'error', 0);
      }
    }
  };

  // Filter and sort users based on column filters and sort
  const filteredAndSortedUsers = useMemo(() => {
    if (!users || !Array.isArray(users)) {
      return [];
    }

    const filtered = users.filter(user => {
      try {
        return Object.entries(columnFilters).every(([key, filterValue]) => {
          if (!filterValue) return true;
          
          switch (key) {
            case 'id':
              return user.id.toString().includes(filterValue);
            case 'username':
              return user.username?.toLowerCase().includes(filterValue.toLowerCase());
            case 'email':
              return user.email?.toLowerCase().includes(filterValue.toLowerCase());
            case 'role':
              return user.role === filterValue;
            case 'status':
              const isActive = user.is_active;
              return (filterValue === 'active' && isActive) || (filterValue === 'inactive' && !isActive);
            case 'last_login':
              const lastLogin = user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never';
              return lastLogin.toLowerCase().includes(filterValue.toLowerCase());
            default:
              return true;
          }
        });
      } catch (e) {
        return true; // Include user if there's an error
      }
    });

    // Sort the filtered results
    const sorted = filtered.sort((a, b) => {
      let aValue = a[sortField];
      let bValue = b[sortField];
      
      // Handle null/undefined values
      if (aValue == null) aValue = '';
      if (bValue == null) bValue = '';
      
      // Convert to strings for comparison
      aValue = aValue.toString();
      bValue = bValue.toString();
      
      if (sortDirection === 'asc') {
        return aValue.localeCompare(bValue);
      } else {
        return bValue.localeCompare(aValue);
      }
    });
    
    return sorted;
  }, [users, columnFilters, sortField, sortDirection]);

  // Paginated users - memoized for performance
  const paginatedUsers = useMemo(() => {
    return filteredAndSortedUsers.slice(
      page * rowsPerPage,
      page * rowsPerPage + rowsPerPage
    );
  }, [filteredAndSortedUsers, page, rowsPerPage]);

  // Handler functions for table interactions
  const handleChangePage = useCallback((event, newPage) => {
    setPage(newPage);
  }, []);

  const handleChangeRowsPerPage = useCallback((event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  }, []);

  const handleSort = useCallback((field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  }, [sortField, sortDirection]);

  const handleColumnFilterChange = (columnKey, value) => {
    setColumnFilters(prev => ({
      ...prev,
      [columnKey]: value
    }));
    setPage(0); // Reset to first page when filtering
  };

  // Sortable header component - memoized for performance
  const SortableHeader = useCallback(({ field, children, ...props }) => (
    <TableCell 
      {...props}
      className="table-header-cell"
      sx={{ 
        cursor: 'pointer',
        userSelect: 'none',
        fontWeight: 600,
        fontSize: '0.75rem',
        padding: '8px 12px',
        borderBottom: '2px solid #e0e0e0'
      }}
      onClick={() => handleSort(field)}
    >
      <TableSortLabel
        active={sortField === field}
        direction={sortField === field ? sortDirection : 'asc'}
        sx={{
          '& .MuiTableSortLabel-icon': {
            fontSize: '0.75rem'
          }
        }}
      >
        {children}
      </TableSortLabel>
    </TableCell>
  ), [sortField, sortDirection, handleSort]);

  // Calculate user statistics
  const stats = {
    total: users.length,
    active: users.filter(u => u.is_active).length,
    administrators: users.filter(u => u.role === 'administrator').length,
    managers: users.filter(u => u.role === 'manager').length,
    users: users.filter(u => u.role === 'user').length,
  };

  return (
    <div className="dashboard-container">
      
      {/* Compact Page Header */}
      <div className="page-header">
        <Typography className="page-title">
          User Management
        </Typography>
        <div className="page-actions">
          <Tooltip title="Back to Dashboard">
            <IconButton 
              className="btn-icon" 
              onClick={() => navigate('/dashboard')}
              size="small"
            >
              <ArrowBackIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Refresh users">
            <IconButton 
              className="btn-icon" 
              onClick={loadUsers} 
              disabled={loading}
              size="small"
            >
              <RefreshIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Button
            className="btn-compact"
            variant="contained"
            startIcon={<AddIcon fontSize="small" />}
            onClick={() => handleOpenDialog()}
            size="small"
          >
            Add User
          </Button>
        </div>
      </div>

      {/* Compact Statistics Grid - 6 key user metrics */}
      <div className="stats-grid">
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon primary">
              <PeopleIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.total}</h3>
              <p>Total Users</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon success">
              <PersonIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.active}</h3>
              <p>Active</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon error">
              <AdminIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.administrators}</h3>
              <p>Administrators</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon warning">
              <SecurityIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.managers}</h3>
              <p>Managers</p>
            </div>
          </div>
        </div>

        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon info">
              <PersonIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.users}</h3>
              <p>Regular Users</p>
            </div>
          </div>
        </div>
        
        {/* Empty slot to maintain 6-column grid */}
        <div className="stat-card" style={{ visibility: 'hidden' }}>
          <div className="stat-card-content">
            <div className="stat-icon primary">
              <PeopleIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>-</h3>
              <p>-</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Card */}
      <div className="main-content-card fade-in">
        <div className="content-card-header">
          <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
            <PeopleIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
            USER ACCOUNTS
          </Typography>
          <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
            {filteredAndSortedUsers.length} of {users.length} users {Object.keys(columnFilters).some(key => columnFilters[key]) ? 'filtered' : 'configured'}
          </Typography>
        </div>
        
        <div className="content-card-body">
          {loading ? (
            <div className="loading-container">
              <CircularProgress size={24} />
              <Typography variant="body2" sx={{ ml: 2, color: 'text.secondary' }}>
                Loading users...
              </Typography>
            </div>
          ) : (
            <TableContainer className="custom-scrollbar">
              <Table className="compact-table">
                <TableHead>
                  {/* Header Row */}
                  <TableRow>
                    <SortableHeader field="id">ID</SortableHeader>
                    <SortableHeader field="username">Username</SortableHeader>
                    <SortableHeader field="email">Email</SortableHeader>
                    <SortableHeader field="role">Role</SortableHeader>
                    <SortableHeader field="is_active">Status</SortableHeader>
                    <SortableHeader field="last_login">Last Login</SortableHeader>
                    <TableCell 
                      className="table-header-cell"
                      sx={{ 
                        fontWeight: 600,
                        fontSize: '0.75rem',
                        padding: '8px 12px',
                        borderBottom: '2px solid #e0e0e0'
                      }}
                      align="center"
                    >
                      Actions
                    </TableCell>
                  </TableRow>
                  
                  {/* Filter Row */}
                  <TableRow>
                    <TableCell sx={{ padding: '4px 8px' }}>
                      <TextField
                        size="small"
                        placeholder="Filter ID..."
                        value={columnFilters.id || ''}
                        onChange={(e) => handleColumnFilterChange('id', e.target.value)}
                        sx={{
                          '& .MuiInputBase-input': {
                            padding: '2px 4px',
                            fontSize: '0.75rem',
                            fontFamily: 'monospace'
                          }
                        }}
                      />
                    </TableCell>
                    <TableCell sx={{ padding: '4px 8px' }}>
                      <TextField
                        size="small"
                        placeholder="Filter username..."
                        value={columnFilters.username || ''}
                        onChange={(e) => handleColumnFilterChange('username', e.target.value)}
                        sx={{
                          '& .MuiInputBase-input': {
                            padding: '2px 4px',
                            fontSize: '0.75rem',
                            fontFamily: 'monospace'
                          }
                        }}
                      />
                    </TableCell>
                    <TableCell sx={{ padding: '4px 8px' }}>
                      <TextField
                        size="small"
                        placeholder="Filter email..."
                        value={columnFilters.email || ''}
                        onChange={(e) => handleColumnFilterChange('email', e.target.value)}
                        sx={{
                          '& .MuiInputBase-input': {
                            padding: '2px 4px',
                            fontSize: '0.75rem',
                            fontFamily: 'monospace'
                          }
                        }}
                      />
                    </TableCell>
                    <TableCell sx={{ padding: '4px 8px' }}>
                      <Select
                        size="small"
                        value={columnFilters.role || ''}
                        onChange={(e) => handleColumnFilterChange('role', e.target.value)}
                        displayEmpty
                        sx={{
                          minWidth: 120,
                          '& .MuiSelect-select': {
                            padding: '2px 4px',
                            fontSize: '0.75rem',
                            fontFamily: 'monospace'
                          }
                        }}
                      >
                        <MenuItem value="">All Roles</MenuItem>
                        <MenuItem value="administrator">Administrator</MenuItem>
                        <MenuItem value="manager">Manager</MenuItem>
                        <MenuItem value="user">User</MenuItem>
                      </Select>
                    </TableCell>
                    <TableCell sx={{ padding: '4px 8px' }}>
                      <Select
                        size="small"
                        value={columnFilters.status || ''}
                        onChange={(e) => handleColumnFilterChange('status', e.target.value)}
                        displayEmpty
                        sx={{
                          minWidth: 100,
                          '& .MuiSelect-select': {
                            padding: '2px 4px',
                            fontSize: '0.75rem',
                            fontFamily: 'monospace'
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
                        placeholder="Filter login..."
                        value={columnFilters.last_login || ''}
                        onChange={(e) => handleColumnFilterChange('last_login', e.target.value)}
                        sx={{
                          '& .MuiInputBase-input': {
                            padding: '2px 4px',
                            fontSize: '0.75rem',
                            fontFamily: 'monospace'
                          }
                        }}
                      />
                    </TableCell>
                    <TableCell sx={{ padding: '4px 8px' }} align="center">
                      {/* No filter for Actions column */}
                    </TableCell>
                  </TableRow>
                </TableHead>
              <TableBody>
                {filteredAndSortedUsers.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center" className="no-data-cell">
                      <Typography variant="body2" color="text.secondary">
                        {users.length === 0 ? 'No users found. Create your first user to get started!' : 'No users match your search criteria.'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  paginatedUsers.map((user) => (
                    <TableRow key={user.id} className="table-row" hover>
                      <TableCell className="table-cell">
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                          {user.id}
                        </Typography>
                      </TableCell>
                      <TableCell className="table-cell">
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem', fontWeight: 600 }}>
                          {user.username}
                        </Typography>
                      </TableCell>
                      <TableCell className="table-cell">
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <EmailIcon fontSize="small" color="action" />
                          <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                            {user.email}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell className="table-cell">
                        <Chip
                          label={user.role}
                          size="small"
                          className="chip-compact"
                          sx={{ fontSize: '0.7rem', fontFamily: 'monospace' }}
                          color={
                            user.role === 'administrator' ? 'error' :
                            user.role === 'manager' ? 'warning' :
                            user.role === 'user' ? 'primary' : 'default'
                          }
                        />
                      </TableCell>
                      <TableCell className="table-cell">
                        <Chip
                          label={user.is_active ? 'Active' : 'Inactive'}
                          size="small"
                          className="chip-compact"
                          sx={{ fontSize: '0.7rem', fontFamily: 'monospace' }}
                          color={user.is_active ? 'success' : 'default'}
                        />
                      </TableCell>
                      <TableCell className="table-cell">
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }} color="text.secondary">
                          {user.last_login
                            ? new Date(user.last_login).toLocaleDateString()
                            : 'Never'}
                        </Typography>
                      </TableCell>
                      <TableCell className="table-cell" align="center">
                        <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center' }}>
                          <Tooltip title="Edit user">
                            <IconButton
                              className="btn-icon"
                              size="small"
                              onClick={() => handleOpenDialog(user)}
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete user">
                            <IconButton
                              className="btn-icon"
                              size="small"
                              onClick={() => handleDelete(user.id)}
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
          )}
          
          {/* Pagination */}
          {!loading && filteredAndSortedUsers.length > 0 && (
            <TablePagination
              component="div"
              count={filteredAndSortedUsers.length}
              page={page}
              onPageChange={handleChangePage}
              rowsPerPage={rowsPerPage}
              onRowsPerPageChange={handleChangeRowsPerPage}
              rowsPerPageOptions={[5, 10, 25, 50]}
              sx={{
                borderTop: '1px solid #e0e0e0',
                '& .MuiTablePagination-toolbar': {
                  fontSize: '0.75rem'
                },
                '& .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows': {
                  fontSize: '0.75rem'
                }
              }}
            />
          )}
        </div>
      </div>

      {/* User Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingUser ? 'Edit User' : 'Add New User'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              autoFocus
              label="Username"
              fullWidth
              variant="outlined"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              sx={{ mb: 2 }}
            />
            <TextField
              label="Email"
              type="email"
              fullWidth
              variant="outlined"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              sx={{ mb: 2 }}
            />
            <TextField
              label="Password"
              type="password"
              fullWidth
              variant="outlined"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              sx={{ mb: 2 }}
              helperText={editingUser ? 'Leave blank to keep current password' : ''}
            />
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Role</InputLabel>
              <Select
                value={formData.role}
                label="Role"
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              >
                <MenuItem value="user">User</MenuItem>
                <MenuItem value="manager">Manager</MenuItem>
                <MenuItem value="administrator">Administrator</MenuItem>
                <MenuItem value="guest">Guest</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingUser ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default UserManagementSimplified;