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
  Pagination,
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
  const navigate = useNavigate();
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

  // Pagination state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Column filters state
  const [columnFilters, setColumnFilters] = useState({});

  // Sorting state
  const [sortField, setSortField] = useState('id');
  const [sortDirection, setSortDirection] = useState('asc');

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const response = await userService.getUsers();
      setUsers(response);
      addAlert(`Loaded ${response.length} users successfully`, 'success', 3000);
    } catch (err) {
      addAlert('Failed to load users', 'error', 0);
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
      addAlert(editingUser ? 'Failed to update user' : 'Failed to create user', 'error', 0);
    }
  };

  const handleDeleteUser = async (userId) => {
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

  const handleColumnFilterChange = (columnKey, value) => {
    setColumnFilters(prev => ({
      ...prev,
      [columnKey]: value
    }));
    setPage(0); // Reset to first page when filtering
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Filter and sort users
  const filteredAndSortedUsers = useMemo(() => {
    let filtered = users.filter(user => {
      return Object.entries(columnFilters).every(([key, filterValue]) => {
        if (!filterValue) return true;
        
        switch (key) {
          case 'id':
            return user.id.toString().includes(filterValue);
          case 'username':
            return user.username.toLowerCase().includes(filterValue.toLowerCase());
          case 'email':
            return user.email.toLowerCase().includes(filterValue.toLowerCase());
          case 'role':
            return user.role === filterValue;
          case 'is_active':
            return user.is_active.toString() === filterValue;
          case 'last_login':
            const lastLogin = user.last_login 
              ? new Date(user.last_login).toLocaleDateString()
              : 'Never';
            return lastLogin.toLowerCase().includes(filterValue.toLowerCase());
          default:
            return true;
        }
      });
    });

    // Sort
    filtered.sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];
      
      if (sortField === 'last_login') {
        aVal = a.last_login ? new Date(a.last_login) : new Date(0);
        bVal = b.last_login ? new Date(b.last_login) : new Date(0);
      }
      
      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [users, columnFilters, sortField, sortDirection]);

  // Paginate users
  const paginatedUsers = useMemo(() => {
    const startIndex = page * rowsPerPage;
    return filteredAndSortedUsers.slice(startIndex, startIndex + rowsPerPage);
  }, [filteredAndSortedUsers, page, rowsPerPage]);

  return (
    <div className="datatable-page-container">
      {/* Page Header */}
      <div className="datatable-page-header">
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

      {/* User Accounts Table */}
      <div className="table-content-area">

        <TableContainer 
          component={Paper} 
          variant="outlined"
          className="standard-table-container"
          sx={{ 
            height: 'auto !important',
            '& .MuiPaper-root': { height: 'auto !important' },
            '& .MuiTable-root': { height: 'auto !important' }
          }}
        >
          <Table size="small">
            <TableHead>
              {/* Column Headers */}
              <TableRow sx={{ backgroundColor: 'grey.100' }}>
                <TableCell className="standard-table-header">
                  ID
                </TableCell>
                <TableCell className="standard-table-header">
                  Username
                </TableCell>
                <TableCell className="standard-table-header">
                  Email
                </TableCell>
                <TableCell className="standard-table-header">
                  Role
                </TableCell>
                <TableCell className="standard-table-header">
                  Status
                </TableCell>
                <TableCell className="standard-table-header">
                  Last Login
                </TableCell>
                <TableCell className="standard-table-header">
                  Actions
                </TableCell>
              </TableRow>
              
              {/* Filter Row */}
              <TableRow sx={{ backgroundColor: 'grey.50' }}>
                <TableCell className="standard-filter-cell">
                  <TextField
                    size="small"
                    fullWidth
                    placeholder="Filter ID..."
                    value={columnFilters.id || ''}
                    onChange={(e) => handleColumnFilterChange('id', e.target.value)}
                    sx={{ '& .MuiInputBase-input': { fontSize: '0.75rem', padding: '2px 4px', fontFamily: 'monospace' } }}
                  />
                </TableCell>
                <TableCell className="standard-filter-cell">
                  <TextField
                    size="small"
                    fullWidth
                    placeholder="Filter username..."
                    value={columnFilters.username || ''}
                    onChange={(e) => handleColumnFilterChange('username', e.target.value)}
                    sx={{ '& .MuiInputBase-input': { fontSize: '0.75rem', padding: '2px 4px', fontFamily: 'monospace' } }}
                  />
                </TableCell>
                <TableCell className="standard-filter-cell">
                  <TextField
                    size="small"
                    fullWidth
                    placeholder="Filter email..."
                    value={columnFilters.email || ''}
                    onChange={(e) => handleColumnFilterChange('email', e.target.value)}
                    sx={{ '& .MuiInputBase-input': { fontSize: '0.75rem', padding: '2px 4px', fontFamily: 'monospace' } }}
                  />
                </TableCell>
                <TableCell className="standard-filter-cell">
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
                    <MenuItem value="">all roles</MenuItem>
                    <MenuItem value="administrator">administrator</MenuItem>
                    <MenuItem value="manager">manager</MenuItem>
                    <MenuItem value="user">user</MenuItem>
                    <MenuItem value="guest">guest</MenuItem>
                  </Select>
                </TableCell>
                <TableCell className="standard-filter-cell">
                  <Select
                    size="small"
                    fullWidth
                    value={columnFilters.is_active || ''}
                    onChange={(e) => handleColumnFilterChange('is_active', e.target.value)}
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
                    <MenuItem value="">all status</MenuItem>
                    <MenuItem value="true">active</MenuItem>
                    <MenuItem value="false">inactive</MenuItem>
                  </Select>
                </TableCell>
                <TableCell className="standard-filter-cell">
                  <TextField
                    size="small"
                    fullWidth
                    placeholder="Filter last login..."
                    value={columnFilters.last_login || ''}
                    onChange={(e) => handleColumnFilterChange('last_login', e.target.value)}
                    sx={{ '& .MuiInputBase-input': { fontSize: '0.75rem', padding: '2px 4px', fontFamily: 'monospace' } }}
                  />
                </TableCell>
                <TableCell className="standard-filter-cell">
                  {/* Empty cell for actions column */}
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                    <CircularProgress size={24} />
                    <Typography variant="body2" sx={{ ml: 2, color: 'text.secondary' }}>
                      Loading users...
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : filteredAndSortedUsers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                    <Typography variant="body2" color="text.secondary">
                      {users.length === 0 ? 'No users found. Create your first user to get started!' : 'No users match your search criteria.'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                paginatedUsers.map((user) => (
                  <TableRow key={user.id} hover>
                    <TableCell className="standard-table-cell">
                      {user.id}
                    </TableCell>
                    <TableCell className="standard-table-cell" sx={{ fontWeight: 600 }}>
                      {user.username}
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      {user.email}
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      {user.role}
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      {user.is_active ? 'active' : 'inactive'}
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      {user.last_login 
                        ? new Date(user.last_login).toLocaleDateString()
                        : 'never'
                      }
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(user)}
                        sx={{ padding: '2px', marginRight: 0.5 }}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteUser(user.id)}
                        color="error"
                        sx={{ padding: '2px' }}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
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
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2" sx={{ fontSize: '0.75rem', color: 'text.secondary' }}>
              Show:
            </Typography>
            <Select
              value={rowsPerPage}
              onChange={(e) => {
                setRowsPerPage(Number(e.target.value));
                setPage(0); // Reset to first page
              }}
              size="small"
              sx={{ 
                minWidth: '70px',
                '& .MuiSelect-select': {
                  fontSize: '0.75rem',
                  py: 0.5
                }
              }}
            >
              <MenuItem value={25}>25</MenuItem>
              <MenuItem value={50}>50</MenuItem>
              <MenuItem value={100}>100</MenuItem>
              <MenuItem value={200}>200</MenuItem>
              <MenuItem value={500}>500</MenuItem>
            </Select>
            <Typography variant="body2" sx={{ fontSize: '0.75rem', color: 'text.secondary' }}>
              per page
            </Typography>
          </Box>

          {/* Pagination */}
          {filteredAndSortedUsers.length > rowsPerPage && (
            <Pagination
              count={Math.ceil(filteredAndSortedUsers.length / rowsPerPage)}
              page={page + 1}
              onChange={(event, newPage) => {
                setPage(newPage - 1);
              }}
              color="primary"
              size="small"
              variant="outlined"
              sx={{ 
                '& .MuiPaginationItem-root': {
                  fontSize: '0.75rem',
                  minWidth: '28px',
                  height: '28px',
                  margin: '0 2px',
                  border: '1px solid #e0e0e0',
                  color: '#666',
                  '&:hover': {
                    backgroundColor: '#f5f5f5',
                    borderColor: '#ccc'
                  },
                  '&.Mui-selected': {
                    backgroundColor: '#1976d2',
                    color: 'white',
                    borderColor: '#1976d2',
                    '&:hover': {
                      backgroundColor: '#1565c0'
                    }
                  }
                }
              }}
            />
          )}
          
          {/* Show pagination info on the right */}
          <Typography variant="body2" sx={{ fontSize: '0.75rem', color: 'text.secondary' }}>
            Showing {page * rowsPerPage + 1}-{Math.min((page + 1) * rowsPerPage, filteredAndSortedUsers.length)} of {filteredAndSortedUsers.length} users
          </Typography>
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
                <MenuItem value="user">user</MenuItem>
                <MenuItem value="manager">manager</MenuItem>
                <MenuItem value="administrator">administrator</MenuItem>
                <MenuItem value="guest">guest</MenuItem>
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