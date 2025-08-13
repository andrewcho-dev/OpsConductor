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
  Paper,
  Grid,
  Card,
  CardContent,
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
                    <TableCell>Username</TableCell>
                    <TableCell>Email</TableCell>
                    <TableCell>Role</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Last Login</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
              <TableBody>
                {users.map((user) => (
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
                ))}
              </TableBody>
            </Table>
          </TableContainer>
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