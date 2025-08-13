import React, { useState, useEffect } from 'react';
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
  Schedule as ScheduleIcon,
  ArrowUpward as ArrowUpwardIcon,
  ArrowDownward as ArrowDownwardIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { userService } from '../../services/userService';
import { useAlert } from '../layout/BottomStatusBar';
import '../../styles/dashboard.css';

const UserManagement = () => {
  const { addAlert } = useAlert();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [sortField, setSortField] = useState('username');
  const [sortDirection, setSortDirection] = useState('asc');
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role: 'user',
  });

  const navigate = useNavigate();

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Sort users
  const sortedUsers = [...users].sort((a, b) => {
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
      addAlert(err.response?.data?.detail || 'Operation failed', 'error', 0);
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

  // Calculate user statistics - 6 key metrics
  const stats = {
    total: users.length,
    active: users.filter(u => u.is_active).length,
    administrators: users.filter(u => u.role === 'administrator').length,
    managers: users.filter(u => u.role === 'manager').length,
    users: users.filter(u => u.role === 'user').length,
    recentLogins: users.filter(u => u.last_login && 
      new Date(u.last_login) > new Date(Date.now() - 24 * 60 * 60 * 1000)).length,
  };

  // Sortable header component
  const SortableHeader = ({ field, children, ...props }) => (
    <TableCell 
      {...props}
      onClick={() => handleSort(field)}
      className="sortable-header"
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
        {children}
        {sortField === field && (
          sortDirection === 'asc' ? 
            <ArrowUpwardIcon fontSize="small" /> : 
            <ArrowDownwardIcon fontSize="small" />
        )}
      </Box>
    </TableCell>
  );

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

        <div className="stat-card fade-in">
          <div className="stat-card-content">
            <div className="stat-icon success">
              <ScheduleIcon fontSize="small" />
            </div>
            <div className="stat-details">
              <h3>{stats.recentLogins}</h3>
              <p>Recent Logins</p>
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
            {users.length} users configured
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
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <SortableHeader field="username">Username</SortableHeader>
                    <SortableHeader field="email">Email</SortableHeader>
                    <SortableHeader field="role">Role</SortableHeader>
                    <TableCell>Status</TableCell>
                    <TableCell>Last Login</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {sortedUsers.map((user) => (
                    <TableRow key={user.id} hover>
                      <TableCell>
                        <Typography variant="body2">
                          {user.id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" className="font-weight-bold">
                          {user.username}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <EmailIcon fontSize="small" color="action" />
                          <Typography variant="body2">
                            {user.email}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={user.role}
                          size="small"
                          className="chip-compact"
                          color={
                            user.role === 'administrator' ? 'error' :
                            user.role === 'manager' ? 'warning' :
                            user.role === 'user' ? 'primary' : 'default'
                          }
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={user.is_active ? 'Active' : 'Inactive'}
                          size="small"
                          className="chip-compact"
                          color={user.is_active ? 'success' : 'default'}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" color="text.secondary">
                          {user.last_login
                            ? new Date(user.last_login).toLocaleDateString()
                            : 'Never'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Tooltip title="Edit user">
                            <IconButton
                              className="btn-icon"
                              size="small"
                              onClick={() => handleOpenDialog(user)}
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title={user.role === 'administrator' ? 'Cannot delete administrator' : 'Delete user'}>
                            <span>
                              <IconButton
                                className="btn-icon"
                                size="small"
                                onClick={() => handleDelete(user.id)}
                                disabled={user.role === 'administrator'}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </span>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </div>
      </div>

      {/* Compact User Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontSize: '1rem', fontWeight: 600, py: 2 }}>
          {editingUser ? 'Edit User' : 'Add New User'}
        </DialogTitle>
        <DialogContent sx={{ py: 2 }}>
          <TextField
            autoFocus
            label="Username"
            fullWidth
            variant="outlined"
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            className="form-control-compact"
            sx={{ mb: 2 }}
            size="small"
          />
          <TextField
            label="Email"
            type="email"
            fullWidth
            variant="outlined"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="form-control-compact"
            sx={{ mb: 2 }}
            size="small"
          />
          <TextField
            label="Password"
            type="password"
            fullWidth
            variant="outlined"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            className="form-control-compact"
            sx={{ mb: 2 }}
            size="small"
            helperText={editingUser ? 'Leave blank to keep current password' : ''}
          />
          <FormControl fullWidth sx={{ mb: 2 }} size="small">
            <InputLabel sx={{ fontSize: '0.875rem' }}>Role</InputLabel>
            <Select
              value={formData.role}
              label="Role"
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              className="form-control-compact"
              sx={{ fontSize: '0.875rem' }}
            >
              <MenuItem value="user" sx={{ fontSize: '0.875rem' }}>User</MenuItem>
              <MenuItem value="manager" sx={{ fontSize: '0.875rem' }}>Manager</MenuItem>
              <MenuItem value="administrator" sx={{ fontSize: '0.875rem' }}>Administrator</MenuItem>
              <MenuItem value="guest" sx={{ fontSize: '0.875rem' }}>Guest</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions sx={{ py: 2, px: 3 }}>
          <Button 
            onClick={handleCloseDialog}
            className="btn-compact"
            size="small"
          >
            Cancel
          </Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained"
            className="btn-compact"
            size="small"
          >
            {editingUser ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default UserManagement; 