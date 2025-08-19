import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../../styles/dashboard.css';
import {
  Typography,
  Button,
  IconButton,
  Tooltip,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  CircularProgress,
  Pagination
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

import { getTableCellStyle } from '../../utils/tableUtils';

const UserManagement = () => {
  const navigate = useNavigate();
  
  // State management
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    role: 'user',
    is_active: true
  });

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  
  // Sorting state
  const [sortField, setSortField] = useState('');
  const [sortDirection, setSortDirection] = useState('asc');

  // Sample user data
  const sampleUsers = [
    { id: 1, username: 'admin', email: 'admin@opsconductor.com', role: 'administrator', is_active: true, created_at: '2024-01-15T10:30:00Z' },
    { id: 2, username: 'manager1', email: 'manager1@opsconductor.com', role: 'manager', is_active: true, created_at: '2024-01-16T14:20:00Z' },
    { id: 3, username: 'user1', email: 'user1@opsconductor.com', role: 'user', is_active: true, created_at: '2024-01-17T09:15:00Z' },
    { id: 4, username: 'user2', email: 'user2@opsconductor.com', role: 'user', is_active: false, created_at: '2024-01-18T16:45:00Z' },
    { id: 5, username: 'manager2', email: 'manager2@opsconductor.com', role: 'manager', is_active: true, created_at: '2024-01-19T11:30:00Z' },
    { id: 6, username: 'user3', email: 'user3@opsconductor.com', role: 'user', is_active: true, created_at: '2024-01-20T13:25:00Z' },
    { id: 7, username: 'user4', email: 'user4@opsconductor.com', role: 'user', is_active: true, created_at: '2024-01-21T08:10:00Z' },
    { id: 8, username: 'admin2', email: 'admin2@opsconductor.com', role: 'administrator', is_active: true, created_at: '2024-01-22T15:40:00Z' },
    { id: 9, username: 'user5', email: 'user5@opsconductor.com', role: 'user', is_active: false, created_at: '2024-01-23T12:55:00Z' },
    { id: 10, username: 'manager3', email: 'manager3@opsconductor.com', role: 'manager', is_active: true, created_at: '2024-01-24T10:20:00Z' }
  ];

  useEffect(() => {
    setUsers(sampleUsers);
  }, []);

  // Sorting logic
  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Apply sorting
  const sortedUsers = [...users].sort((a, b) => {
    if (!sortField) return 0;
    
    let aValue = a[sortField];
    let bValue = b[sortField];
    
    if (typeof aValue === 'string') {
      aValue = aValue.toLowerCase();
      bValue = bValue.toLowerCase();
    }
    
    if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
    if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
    return 0;
  });

  // Calculate pagination
  const totalUsers = sortedUsers.length;
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const paginatedUsers = sortedUsers.slice(startIndex, endIndex);
  const totalPages = Math.ceil(totalUsers / pageSize);

  // Dialog handlers
  const handleOpenDialog = (user = null) => {
    if (user) {
      setEditingUser(user);
      setFormData({
        username: user.username,
        email: user.email,
        role: user.role,
        is_active: user.is_active
      });
    } else {
      setEditingUser(null);
      setFormData({
        username: '',
        email: '',
        role: 'user',
        is_active: true
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
      role: 'user',
      is_active: true
    });
  };

  const handleSaveUser = () => {
    // In a real app, this would make an API call
    console.log('Saving user:', formData);
    handleCloseDialog();
  };

  const handleEditUser = (user) => {
    handleOpenDialog(user);
  };

  const handleDeleteUser = (userId) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      setUsers(users.filter(user => user.id !== userId));
    }
  };

  const fetchUsers = () => {
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      setUsers(sampleUsers);
      setLoading(false);
    }, 1000);
  };

  // Sortable header component
  const SortableHeader = ({ field, children, sx = {} }) => (
    <TableCell 
      sx={{ 
        ...sx,
        cursor: 'pointer',
        userSelect: 'none',
        '&:hover': { backgroundColor: 'grey.200' }
      }}
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
            <span>
              <IconButton 
                className="btn-icon" 
                onClick={fetchUsers}
                disabled={loading}
                size="small"
              >
                <RefreshIcon fontSize="small" />
              </IconButton>
            </span>
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

      {/* User Management Table */}
      <div className="table-content-area">

        <TableContainer 
          component={Paper} 
          variant="outlined"
          className="standard-table-container"
        >
          <Table size="small">
            <TableHead>
              <TableRow sx={{ backgroundColor: 'grey.100' }}>
                <TableCell className="standard-table-header">ID</TableCell>
                <SortableHeader field="username" className="standard-table-header">Username</SortableHeader>
                <SortableHeader field="email" className="standard-table-header">Email</SortableHeader>
                <SortableHeader field="role" className="standard-table-header">Role</SortableHeader>
                <SortableHeader field="is_active" className="standard-table-header">Status</SortableHeader>
                <SortableHeader field="created_at" className="standard-table-header">Created</SortableHeader>
                <TableCell className="standard-table-header">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} sx={{ textAlign: 'center', py: 4 }}>
                    <CircularProgress size={24} />
                    <Typography variant="body2" sx={{ ml: 2, color: 'text.secondary' }}>
                      Loading users...
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                paginatedUsers.map((user) => (
                  <TableRow 
                    key={user.id} 
                    sx={{ 
                      '&:hover': { backgroundColor: 'action.hover' }
                    }}
                  >
                    <TableCell className="standard-table-cell">{user.id}</TableCell>
                    <TableCell className="standard-table-cell">{user.username}</TableCell>
                    <TableCell className="standard-table-cell">{user.email}</TableCell>
                    <TableCell className="standard-table-cell">{user.role}</TableCell>
                    <TableCell className="standard-table-cell">{user.is_active ? 'Active' : 'Inactive'}</TableCell>
                    <TableCell className="standard-table-cell">
                      {new Date(user.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="standard-table-cell">
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        <Tooltip title="Edit user">
                          <IconButton 
                            size="small" 
                            onClick={() => handleEditUser(user)}
                            sx={{ padding: '2px' }}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete user">
                          <IconButton 
                            size="small" 
                            onClick={() => handleDeleteUser(user.id)}
                            sx={{ padding: '2px' }}
                            color="error"
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
        
        {/* Pagination Controls */}
        <div className="standard-pagination-area">
          {/* Page Size Selector */}
          <div className="standard-page-size-selector">
            <Typography variant="body2" className="standard-pagination-info">
              Show:
            </Typography>
            <Select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1); // Reset to first page
              }}
              size="small"
              className="standard-page-size-selector"
            >
              <MenuItem value={25}>25</MenuItem>
              <MenuItem value={50}>50</MenuItem>
              <MenuItem value={100}>100</MenuItem>
              <MenuItem value={200}>200</MenuItem>
            </Select>
            <Typography variant="body2" className="standard-pagination-info">
              per page
            </Typography>
          </div>

          {/* Pagination */}
          {totalUsers > pageSize && (
            <Pagination
              count={totalPages}
              page={currentPage}
              onChange={(event, page) => {
                setCurrentPage(page);
              }}
              color="primary"
              size="small"
              variant="outlined"
              className="standard-pagination"
            />
          )}
          
          {/* Show pagination info on the right */}
          <Typography variant="body2" className="standard-pagination-info">
            Showing {startIndex + 1}-{Math.min(endIndex, totalUsers)} of {totalUsers} users
          </Typography>
        </div>
      </div>

      {/* Compact User Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ pb: 1 }}>
          {editingUser ? 'Edit User' : 'Add New User'}
          <IconButton
            onClick={handleCloseDialog}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="Username"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              fullWidth
              size="small"
            />
            <TextField
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              fullWidth
              size="small"
            />
            <FormControl fullWidth size="small">
              <InputLabel>Role</InputLabel>
              <Select
                value={formData.role}
                label="Role"
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              >
                <MenuItem value="user">User</MenuItem>
                <MenuItem value="manager">Manager</MenuItem>
                <MenuItem value="administrator">Administrator</MenuItem>
              </Select>
            </FormControl>
            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                />
              }
              label="Active"
            />
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handleCloseDialog} size="small">
            Cancel
          </Button>
          <Button onClick={handleSaveUser} variant="contained" size="small">
            {editingUser ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default UserManagement;