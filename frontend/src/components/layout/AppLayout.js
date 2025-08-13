import React from 'react';
import { Box } from '@mui/material';
import TopHeader from './TopHeader';
import BottomStatusBar from './BottomStatusBar';
import Sidebar from './Sidebar';

const AppLayout = ({ children }) => {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* Left Sidebar */}
      <Sidebar />
      
      {/* Main Layout Container */}
      <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
        {/* Fixed Top Header */}
        <TopHeader />
        
        {/* Main Content Area */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            mt: '64px', // Height of the top header
            mb: '28px', // Height of the bottom status bar
            overflow: 'auto',
            backgroundColor: '#f8f9fa',
          }}
        >
          {children}
        </Box>
        
        {/* Fixed Bottom Status Bar */}
        <BottomStatusBar />
      </Box>
    </Box>
  );
};

export default AppLayout;