import React from 'react';
import {
  Typography,
} from '@mui/material';
import { useAuth } from '../../contexts/AuthContext';

const Dashboard = () => {
  const { user } = useAuth();



  return (
    <div className="dashboard-container">
      {/* Page Header */}
      <div className="page-header">
        <Typography className="page-title">
          System Dashboard
        </Typography>
        <div className="page-actions">
          <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
            Welcome, {user?.username}
          </Typography>
        </div>
      </div>




    </div>
  );
};

export default Dashboard; 