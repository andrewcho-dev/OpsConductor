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
import UserManagementSimplified from './components/users/UserManagementSimplified';
import UniversalTargetDashboard from './components/targets/UniversalTargetDashboard';
import JobDashboard from './components/jobs/JobDashboard';
import CeleryMonitorPage from './components/jobs/CeleryMonitorPage';
import TestMinutesSchedule from './components/jobs/TestMinutesSchedule';
import DirectScheduleTest from './components/jobs/DirectScheduleTest';
import DebugTools from './components/debug/DebugTools';
import LogViewer from './components/LogViewer';
import LogViewerTest from './components/LogViewerTest';
import SystemSettings from './components/system/SystemSettings';
import SystemHealthDashboard from './components/system/SystemHealthDashboard';
import AuditDashboard from './components/audit/AuditDashboard';
import ProtectedRoute from './components/auth/ProtectedRoute';
import './styles/dashboard.css';

function AppContent() {
  const { isAuthenticated } = useSessionAuth();

  return (
    <Routes>
      <Route 
        path="/login" 
        element={
          isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginScreen />
        } 
      />
      <Route 
        path="/*" 
        element={
          <AppLayout>
            <Routes>
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/users" 
                element={
                  <ProtectedRoute requireAdmin>
                    <UserManagementSimplified />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/targets" 
                element={
                  <ProtectedRoute>
                    <UniversalTargetDashboard />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/jobs" 
                element={
                  <ProtectedRoute>
                    <JobDashboard />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/celery-monitor" 
                element={
                  <ProtectedRoute>
                    <CeleryMonitorPage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/test-minutes-schedule" 
                element={
                  <ProtectedRoute>
                    <TestMinutesSchedule />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/direct-schedule" 
                element={
                  <ProtectedRoute>
                    <DirectScheduleTest />
                  </ProtectedRoute>
                } 
              />


              <Route 
                path="/debug-tools" 
                element={
                  <ProtectedRoute>
                    <DebugTools />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/log-viewer" 
                element={
                  <ProtectedRoute>
                    <LogViewer />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/log-viewer-test" 
                element={
                  <ProtectedRoute>
                    <LogViewerTest />
                  </ProtectedRoute>
                } 
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
                path="/system-health" 
                element={
                  <ProtectedRoute>
                    <SystemHealthDashboard />
                  </ProtectedRoute>
                } 
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
                path="/" 
                element={<Navigate to="/dashboard" replace />} 
              />
            </Routes>
          </AppLayout>
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