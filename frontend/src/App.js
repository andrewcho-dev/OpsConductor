import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store/store';
import { SessionAuthProvider, useSessionAuth } from './contexts/SessionAuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { AlertProvider } from './components/layout/BottomStatusBar';
import AppLayout from './components/layout/AppLayout';
import LoginScreen from './components/auth/LoginScreen';


import Dashboard from './components/dashboard/Dashboard';

import EnhancedUserManagement from './components/users/EnhancedUserManagement';
import UserActivityDashboard from './components/users/UserActivityDashboard';
import AuthConfigManagement from './components/auth/AuthConfigManagement';
import UniversalTargetDashboard from './components/targets/UniversalTargetDashboard';
import JobDashboard from './components/jobs/JobDashboard';

import TestMinutesSchedule from './components/jobs/TestMinutesSchedule';
import DirectScheduleTest from './components/jobs/DirectScheduleTest';
import DebugTools from './components/debug/DebugTools';

import SystemSettings from './components/system/SystemSettings';

import AuditDashboard from './components/audit/AuditDashboard';
import ObservabilityDashboard from './components/monitoring/ObservabilityDashboard';
import DockerMonitoringDashboard from './components/docker/DockerMonitoringDashboard';

import ProtectedRoute from './components/auth/ProtectedRoute';
import './styles/dashboard.css';

function AppContent() {
  const { isAuthenticated } = useSessionAuth();

  return (
    <Routes>
      {/* Public route - Login page */}
      <Route 
        path="/login" 
        element={
          isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginScreen />
        } 
      />
      
      {/* All other routes are protected and wrapped in AppLayout */}
      <Route 
        path="/*" 
        element={
          <ProtectedRoute>
            <AppLayout>
              <Routes>
                <Route 
                  path="/dashboard" 
                  element={<Dashboard />} 
                />
                <Route 
                  path="/users" 
                  element={
                    <ProtectedRoute requireAdmin>
                      <EnhancedUserManagement />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/users/:userId/activity" 
                  element={
                    <ProtectedRoute requireAdmin>
                      <UserActivityDashboard />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/auth-config" 
                  element={
                    <ProtectedRoute requireAdmin>
                      <AuthConfigManagement />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/targets" 
                  element={<UniversalTargetDashboard />} 
                />
                <Route 
                  path="/jobs" 
                  element={<JobDashboard />} 
                />
                <Route 
                  path="/test-minutes-schedule" 
                  element={<TestMinutesSchedule />} 
                />
                <Route 
                  path="/direct-schedule" 
                  element={<DirectScheduleTest />} 
                />
                <Route 
                  path="/debug-tools" 
                  element={<DebugTools />} 
                />
                <Route 
                  path="/system-settings" 
                  element={
                    <ProtectedRoute requireAdmin>
                      <SystemSettings />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/docker-monitoring" 
                  element={<DockerMonitoringDashboard />} 
                />
                <Route 
                  path="/audit" 
                  element={
                    <ProtectedRoute requireAdmin>
                      <AuditDashboard />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/observability" 
                  element={<ObservabilityDashboard />} 
                />
                <Route 
                  path="/" 
                  element={<Navigate to="/dashboard" replace />} 
                />
                {/* Catch-all route for any unmatched paths */}
                <Route 
                  path="*" 
                  element={<Navigate to="/dashboard" replace />} 
                />
              </Routes>
            </AppLayout>
          </ProtectedRoute>
        } 
      />
    </Routes>
  );
}

function App() {
  return (
    <Provider store={store}>
      <ThemeProvider>
        <SessionAuthProvider>
          <AlertProvider>
            <AppContent />
          </AlertProvider>
        </SessionAuthProvider>
      </ThemeProvider>
    </Provider>
  );
}

export default App; 