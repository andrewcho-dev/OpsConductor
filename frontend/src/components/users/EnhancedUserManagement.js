import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography, Button, IconButton, Tooltip, Box, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Chip, Dialog, DialogTitle,
  DialogContent, DialogActions, TextField, Select, MenuItem, FormControl,
  InputLabel, Switch, FormControlLabel, CircularProgress, Pagination,
  Card, CardContent, Grid, Tabs, Tab, Checkbox, Alert, Snackbar,
  Menu, ListItemIcon, ListItemText, Divider, Badge, LinearProgress
} from '@mui/material';

// Icons
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import RefreshIcon from '@mui/icons-material/Refresh';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import CloseIcon from '@mui/icons-material/Close';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import SearchIcon from '@mui/icons-material/Search';
import FilterListIcon from '@mui/icons-material/FilterList';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import PersonIcon from '@mui/icons-material/Person';
import GroupIcon from '@mui/icons-material/Group';
import SecurityIcon from '@mui/icons-material/Security';
import HistoryIcon from '@mui/icons-material/History';
import LockIcon from '@mui/icons-material/Lock';
import LockOpenIcon from '@mui/icons-material/LockOpen';
import VisibilityIcon from '@mui/icons-material/Visibility';
import PasswordIcon from '@mui/icons-material/Password';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';

import { enhancedUserService } from '../../services/enhancedUserService';
import '../../styles/dashboard.css';

const EnhancedUserManagement = () => {
  const navigate = useNavigate();
  
  // State management
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({});
  const [roles, setRoles] = useState([]);
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [currentTab, setCurrentTab] = useState(0);
  
  // Dialog states
  const [openDialog, setOpenDialog] = useState(false);
  const [openActivityDialog, setOpenActivityDialog] = useState(false);
  const [openBulkDialog, setOpenBulkDialog] = useState(false);
  const [openPasswordDialog, setOpenPasswordDialog] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [viewingActivity, setViewingActivity] = useState(null);
  const [userActivity, setUserActivity] = useState(null);
  
  // Form data
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    role_id: null,
    first_name: '',
    last_name: '',
    phone: '',
    department: '',
    is_active: true,
    is_verified: false,
    must_change_password: false
  });

  // Password change form data
  const [passwordData, setPasswordData] = useState({
    newPassword: '',
    confirmPassword: ''
  });
  
  // Filters and search
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortDesc, setSortDesc] = useState(true);
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [totalUsers, setTotalUsers] = useState(0);
  
  // Bulk operations
  const [bulkAction, setBulkAction] = useState('');
  const [bulkReason, setBulkReason] = useState('');
  
  // Notifications
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });
  
  // Menu state
  const [anchorEl, setAnchorEl] = useState(null);
  const [menuUser, setMenuUser] = useState(null);

  useEffect(() => {
    fetchUsers();
    fetchStats();
    fetchRoles();
  }, [currentPage, pageSize, searchTerm, roleFilter, statusFilter, sortBy, sortDesc]);

  const fetchRoles = async () => {
    try {
      const rolesData = await enhancedUserService.getRoles();
      setRoles(rolesData || []);
    } catch (error) {
      console.error('Failed to fetch roles:', error);
      showNotification('Failed to load roles', 'error');
    }
  };

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const params = {
        skip: (currentPage - 1) * pageSize,
        limit: pageSize,
        sort_by: sortBy,
        sort_desc: sortDesc
      };
      
      if (searchTerm) params.search = searchTerm;
      if (roleFilter) params.role = roleFilter;
      if (statusFilter === 'active') params.active_only = true;
      
      const data = await enhancedUserService.getUsers(params);
      
      setUsers(data.users || []);
      setTotalUsers(data.total || 0);
    } catch (error) {
      console.error('Failed to fetch users:', error);
      showNotification('Failed to load users', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const data = await enhancedUserService.getUserStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch user stats:', error);
    }
  };

  const fetchUserActivity = async (userId) => {
    try {
      const data = await enhancedUserService.getUserActivity(userId);
      setUserActivity(data);
    } catch (error) {
      console.error('Failed to fetch user activity:', error);
      showNotification('Failed to load user activity', 'error');
    }
  };

  const showNotification = (message, severity = 'info') => {
    setNotification({ open: true, message, severity });
  };

  const validatePasswords = (password, confirmPassword) => {
    if (!password || !confirmPassword) {
      showNotification('Both password fields are required', 'error');
      return false;
    }
    if (password !== confirmPassword) {
      showNotification('Passwords do not match', 'error');
      return false;
    }
    if (password.length < 8) {
      showNotification('Password must be at least 8 characters long', 'error');
      return false;
    }
    return true;
  };

  const handleCreateUser = async () => {
    try {
      // Validate passwords for new users
      if (!validatePasswords(formData.password, formData.confirmPassword)) {
        return;
      }
      
      // Remove confirmPassword from the data sent to API
      const { confirmPassword, ...userData } = formData;
      await enhancedUserService.createUser(userData);
      showNotification('User created successfully', 'success');
      handleCloseDialog();
      fetchUsers();
      fetchStats();
    } catch (error) {
      showNotification(error.message || 'Failed to create user', 'error');
    }
  };

  const handleUpdateUser = async () => {
    try {
      // For updates, only validate password if it's being changed
      if (formData.password && !validatePasswords(formData.password, formData.confirmPassword)) {
        return;
      }
      
      // Remove confirmPassword and empty password from the data sent to API
      const { confirmPassword, ...userData } = formData;
      if (!userData.password) {
        delete userData.password;
      }
      
      await enhancedUserService.updateUser(editingUser.id, userData);
      showNotification('User updated successfully', 'success');
      handleCloseDialog();
      fetchUsers();
    } catch (error) {
      showNotification(error.message || 'Failed to update user', 'error');
    }
  };

  const handleOpenPasswordDialog = (user) => {
    setEditingUser(user);
    setPasswordData({
      newPassword: '',
      confirmPassword: ''
    });
    setOpenPasswordDialog(true);
    handleMenuClose();
  };

  const handleClosePasswordDialog = () => {
    setOpenPasswordDialog(false);
    setEditingUser(null);
    setPasswordData({
      newPassword: '',
      confirmPassword: ''
    });
  };

  const handleChangePassword = async () => {
    try {
      if (!validatePasswords(passwordData.newPassword, passwordData.confirmPassword)) {
        return;
      }

      await enhancedUserService.changeUserPassword(editingUser.id, {
        new_password: passwordData.newPassword
      });
      
      showNotification('Password changed successfully', 'success');
      handleClosePasswordDialog();
    } catch (error) {
      showNotification(error.message || 'Failed to change password', 'error');
    }
  };

  const handleDeleteUser = async (userId) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await enhancedUserService.deleteUser(userId);
        showNotification('User deleted successfully', 'success');
        fetchUsers();
        fetchStats();
      } catch (error) {
        showNotification(error.message || 'Failed to delete user', 'error');
      }
    }
  };

  const handleBulkAction = async () => {
    if (selectedUsers.length === 0) {
      showNotification('Please select users first', 'warning');
      return;
    }

    try {
      const result = await enhancedUserService.bulkUserAction({
        user_ids: selectedUsers,
        action: bulkAction,
        reason: bulkReason
      });
      
      showNotification(
        `Bulk action completed: ${result.success_count} successful, ${result.failed_count} failed`,
        'success'
      );
      setOpenBulkDialog(false);
      setSelectedUsers([]);
      setBulkAction('');
      setBulkReason('');
      fetchUsers();
      fetchStats();
    } catch (error) {
      showNotification(error.message || 'Bulk action failed', 'error');
    }
  };

  const handleOpenDialog = (user = null) => {
    if (user) {
      setEditingUser(user);
      // Find role_id from role name
      const userRoleName = user.role?.name || user.role;
      const userRole = roles.find(role => role.name === userRoleName);
      setFormData({
        username: user.username,
        email: user.email,
        password: '',
        confirmPassword: '',
        role_id: userRole ? userRole.id : null,
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        phone: user.phone || '',
        department: user.department || '',
        is_active: user.is_active,
        is_verified: user.is_verified,
        must_change_password: user.must_change_password
      });
    } else {
      setEditingUser(null);
      // Default to 'user' role
      const defaultRole = roles.find(role => role.name === 'user');
      setFormData({
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
        role_id: defaultRole ? defaultRole.id : null,
        first_name: '',
        last_name: '',
        phone: '',
        department: '',
        is_active: true,
        is_verified: false,
        must_change_password: false
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingUser(null);
  };

  const handleViewActivity = (user) => {
    navigate(`/users/${user.id}/activity`);
  };

  const handleMenuOpen = (event, user) => {
    setAnchorEl(event.currentTarget);
    setMenuUser(user);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setMenuUser(null);
  };

  const handleSelectUser = (userId) => {
    setSelectedUsers(prev => 
      prev.includes(userId) 
        ? prev.filter(id => id !== userId)
        : [...prev, userId]
    );
  };

  const handleSelectAll = () => {
    if (selectedUsers.length === users.length) {
      setSelectedUsers([]);
    } else {
      setSelectedUsers(users.map(user => user.id));
    }
  };

  const getStatusChip = (user) => {
    if (!user.is_active) {
      return <Chip label="Inactive" color="error" size="small" />;
    }
    if (user.is_locked) {
      return <Chip label="Locked" color="warning" size="small" icon={<LockIcon />} />;
    }
    if (!user.is_verified) {
      return <Chip label="Unverified" color="info" size="small" />;
    }
    if (user.must_change_password) {
      return <Chip label="Password Reset Required" color="warning" size="small" />;
    }
    return <Chip label="Active" color="success" size="small" />;
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'super_admin': return 'error';
      case 'admin': return 'warning';
      case 'operator': return 'info';
      case 'viewer': return 'secondary';
      case 'user': return 'default';
      default: return 'default';
    }
  };

  // Statistics Cards
  const StatCard = ({ title, value, icon, color = 'primary' }) => (
    <Card>
      <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Box sx={{ color: `${color}.main` }}>
          {icon}
        </Box>
        <Box>
          <Typography variant="h4" component="div">
            {value}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {title}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <div className="dashboard-container">
      {/* Page Header */}
      <div className="page-header">
        <Typography className="page-title">
          Enhanced User Management
        </Typography>
        <div className="page-actions">
          <Tooltip title="Back to Dashboard">
            <IconButton onClick={() => navigate('/dashboard')} size="small">
              <ArrowBackIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Refresh">
            <IconButton onClick={fetchUsers} disabled={loading} size="small">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
            size="small"
          >
            Add User
          </Button>
        </div>
      </div>

      {/* Statistics Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Users"
            value={stats.total_users || 0}
            icon={<GroupIcon />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Users"
            value={stats.active_users || 0}
            icon={<CheckCircleIcon />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Inactive Users"
            value={stats.inactive_users || 0}
            icon={<LockIcon />}
            color="warning"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Recent Signups"
            value={stats.recent_signups || 0}
            icon={<HistoryIcon />}
            color="info"
          />
        </Grid>
      </Grid>

      {/* Filters and Search */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                size="small"
                placeholder="Search users..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
                }}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Role</InputLabel>
                <Select
                  value={roleFilter}
                  label="Role"
                  onChange={(e) => setRoleFilter(e.target.value)}
                >
                  <MenuItem value="">All Roles</MenuItem>
                  {roles.map((role) => (
                    <MenuItem key={role.id} value={role.name}>
                      {role.display_name || role.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  label="Status"
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <MenuItem value="">All Status</MenuItem>
                  <MenuItem value="active">Active Only</MenuItem>
                  <MenuItem value="inactive">Inactive</MenuItem>
                  <MenuItem value="locked">Locked</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                {selectedUsers.length > 0 && (
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setOpenBulkDialog(true)}
                  >
                    Bulk Actions ({selectedUsers.length})
                  </Button>
                )}
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Users Table */}
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow sx={{ backgroundColor: 'grey.100' }}>
              <TableCell padding="checkbox">
                <Checkbox
                  checked={selectedUsers.length === users.length && users.length > 0}
                  indeterminate={selectedUsers.length > 0 && selectedUsers.length < users.length}
                  onChange={handleSelectAll}
                />
              </TableCell>
              <TableCell>ID</TableCell>
              <TableCell>Username</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={9} sx={{ textAlign: 'center', py: 4 }}>
                  <CircularProgress size={24} />
                  <Typography variant="body2" sx={{ ml: 2, color: 'text.secondary' }}>
                    Loading users...
                  </Typography>
                </TableCell>
              </TableRow>
            ) : users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body2" color="text.secondary">
                    No users found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              users.map((user) => (
                <TableRow key={user.id} sx={{ '&:hover': { backgroundColor: 'action.hover' } }}>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selectedUsers.includes(user.id)}
                      onChange={() => handleSelectUser(user.id)}
                    />
                  </TableCell>
                  <TableCell>{user.id}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <PersonIcon fontSize="small" color="action" />
                      {user.username}
                    </Box>
                  </TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>
                    {user.first_name || user.last_name 
                      ? `${user.first_name || ''} ${user.last_name || ''}`.trim()
                      : '-'
                    }
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={user.role?.name || user.role || 'No Role'} 
                      color={getRoleColor(user.role?.name || user.role)} 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell>{getStatusChip(user)}</TableCell>
                  <TableCell>
                    {new Date(user.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <IconButton
                      size="small"
                      onClick={(e) => handleMenuOpen(e, user)}
                    >
                      <MoreVertIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body2">Show:</Typography>
          <Select
            value={pageSize}
            onChange={(e) => setPageSize(Number(e.target.value))}
            size="small"
          >
            <MenuItem value={25}>25</MenuItem>
            <MenuItem value={50}>50</MenuItem>
            <MenuItem value={100}>100</MenuItem>
          </Select>
          <Typography variant="body2">per page</Typography>
        </Box>
        
        <Pagination
          count={Math.ceil(totalUsers / pageSize)}
          page={currentPage}
          onChange={(_, page) => setCurrentPage(page)}
          color="primary"
          size="small"
        />
        
        <Typography variant="body2">
          Showing {((currentPage - 1) * pageSize) + 1}-{Math.min(currentPage * pageSize, totalUsers)} of {totalUsers}
        </Typography>
      </Box>

      {/* User Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => { handleOpenDialog(menuUser); handleMenuClose(); }}>
          <ListItemIcon><EditIcon /></ListItemIcon>
          <ListItemText>Edit User</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleOpenPasswordDialog(menuUser)}>
          <ListItemIcon><PasswordIcon /></ListItemIcon>
          <ListItemText>Change Password</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => { handleViewActivity(menuUser); handleMenuClose(); }}>
          <ListItemIcon><HistoryIcon /></ListItemIcon>
          <ListItemText>View Activity</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem onClick={() => { handleDeleteUser(menuUser.id); handleMenuClose(); }}>
          <ListItemIcon><DeleteIcon color="error" /></ListItemIcon>
          <ListItemText>Delete User</ListItemText>
        </MenuItem>
      </Menu>

      {/* User Form Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingUser ? 'Edit User' : 'Create New User'}
          <IconButton
            onClick={handleCloseDialog}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Username"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={editingUser ? "New Password (leave blank to keep current)" : "Password"}
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required={!editingUser}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Confirm Password"
                type="password"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                required={!editingUser && Boolean(formData.password)}
                error={Boolean(formData.password && formData.confirmPassword && formData.password !== formData.confirmPassword)}
                helperText={formData.password && formData.confirmPassword && formData.password !== formData.confirmPassword ? "Passwords do not match" : ""}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="First Name"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Last Name"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Phone"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Department"
                value={formData.department}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Role</InputLabel>
                <Select
                  value={formData.role_id || ''}
                  label="Role"
                  onChange={(e) => setFormData({ ...formData, role_id: e.target.value })}
                >
                  {roles.map((role) => (
                    <MenuItem key={role.id} value={role.id}>
                      {role.display_name || role.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={8}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    />
                  }
                  label="Active"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.is_verified}
                      onChange={(e) => setFormData({ ...formData, is_verified: e.target.checked })}
                    />
                  }
                  label="Verified"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.must_change_password}
                      onChange={(e) => setFormData({ ...formData, must_change_password: e.target.checked })}
                    />
                  }
                  label="Must Change Password"
                />
              </Box>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={editingUser ? handleUpdateUser : handleCreateUser}
            variant="contained"
          >
            {editingUser ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* User Activity Dialog */}
      <Dialog open={openActivityDialog} onClose={() => setOpenActivityDialog(false)} maxWidth="lg" fullWidth>
        <DialogTitle>
          User Activity - {viewingActivity?.username}
          <IconButton
            onClick={() => setOpenActivityDialog(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {userActivity ? (
            <Box>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={12} md={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6">{userActivity.active_sessions}</Typography>
                      <Typography variant="body2" color="text.secondary">Active Sessions</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6">{userActivity.failed_attempts}</Typography>
                      <Typography variant="body2" color="text.secondary">Failed Attempts</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6">
                        {userActivity.last_login ? new Date(userActivity.last_login).toLocaleDateString() : 'Never'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">Last Login</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6">{userActivity.last_login_ip || 'N/A'}</Typography>
                      <Typography variant="body2" color="text.secondary">Last IP</Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
              
              <Typography variant="h6" sx={{ mb: 2 }}>Recent Activity</Typography>
              <TableContainer component={Paper}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Event</TableCell>
                      <TableCell>Description</TableCell>
                      <TableCell>IP Address</TableCell>
                      <TableCell>Date</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {userActivity.recent_activity?.map((activity, index) => (
                      <TableRow key={index}>
                        <TableCell>{activity.event_type}</TableCell>
                        <TableCell>{activity.event_description}</TableCell>
                        <TableCell>{activity.ip_address || 'N/A'}</TableCell>
                        <TableCell>{new Date(activity.created_at).toLocaleString()}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          ) : (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          )}
        </DialogContent>
      </Dialog>

      {/* Bulk Actions Dialog */}
      <Dialog open={openBulkDialog} onClose={() => setOpenBulkDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Bulk Actions</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Selected {selectedUsers.length} users
          </Typography>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Action</InputLabel>
            <Select
              value={bulkAction}
              label="Action"
              onChange={(e) => setBulkAction(e.target.value)}
            >
              <MenuItem value="activate">Activate</MenuItem>
              <MenuItem value="deactivate">Deactivate</MenuItem>
              <MenuItem value="lock">Lock</MenuItem>
              <MenuItem value="unlock">Unlock</MenuItem>
              <MenuItem value="force_password_change">Force Password Change</MenuItem>
              <MenuItem value="delete">Delete</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            label="Reason (optional)"
            multiline
            rows={3}
            value={bulkReason}
            onChange={(e) => setBulkReason(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenBulkDialog(false)}>Cancel</Button>
          <Button onClick={handleBulkAction} variant="contained" disabled={!bulkAction}>
            Execute
          </Button>
        </DialogActions>
      </Dialog>

      {/* Password Change Dialog */}
      <Dialog open={openPasswordDialog} onClose={handleClosePasswordDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          Change Password for {editingUser?.username}
          <IconButton
            onClick={handleClosePasswordDialog}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="New Password"
                type="password"
                value={passwordData.newPassword}
                onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Confirm New Password"
                type="password"
                value={passwordData.confirmPassword}
                onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                required
                error={Boolean(passwordData.newPassword && passwordData.confirmPassword && passwordData.newPassword !== passwordData.confirmPassword)}
                helperText={passwordData.newPassword && passwordData.confirmPassword && passwordData.newPassword !== passwordData.confirmPassword ? "Passwords do not match" : ""}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClosePasswordDialog}>Cancel</Button>
          <Button 
            onClick={handleChangePassword} 
            variant="contained"
            disabled={!passwordData.newPassword || !passwordData.confirmPassword || passwordData.newPassword !== passwordData.confirmPassword}
          >
            Change Password
          </Button>
        </DialogActions>
      </Dialog>

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={() => setNotification({ ...notification, open: false })}
      >
        <Alert
          onClose={() => setNotification({ ...notification, open: false })}
          severity={notification.severity}
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </div>
  );
};

export default EnhancedUserManagement;