/**
 * Celery Monitor Page - Standalone page for comprehensive Celery monitoring
 * Provides detailed real-time monitoring of workers, queues, tasks, and metrics
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Alert,
  CircularProgress,
} from '@mui/material';
import CeleryMonitor from './CeleryMonitor';
import { useAuth } from '../../contexts/AuthContext';
import { useAlert } from '../layout/BottomStatusBar';

const CeleryMonitorPage = () => {
  const { token } = useAuth();
  const { addAlert } = useAlert();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [celeryStats, setCeleryStats] = useState({});
  const [queueStats, setQueueStats] = useState({});
  const [workerStats, setWorkerStats] = useState({});

  const fetchMonitoringData = async (isInitialLoad = false) => {
    try {
      if (isInitialLoad) {
        setLoading(true);
      } else {
        setRefreshing(true);
      }
      setError(null);

      // Fetch all monitoring data in parallel
      const [celeryResponse, queueResponse, workerResponse] = await Promise.all([
        fetch('/api/celery/stats', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }),
        fetch('/api/celery/queues', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }),
        fetch('/api/celery/workers', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })
      ]);

      // Process responses
      if (celeryResponse.ok) {
        const celeryData = await celeryResponse.json();
        setCeleryStats(celeryData);
      }

      if (queueResponse.ok) {
        const queueData = await queueResponse.json();
        setQueueStats(queueData.queues || {});
      }

      if (workerResponse.ok) {
        const workerData = await workerResponse.json();
        setWorkerStats({
          workers: Object.values(workerData.workers || {}),
          total_workers: Object.keys(workerData.workers || {}).length,
          active_workers: Object.values(workerData.workers || {}).filter(w => w.online).length,
          busy_workers: Object.values(workerData.workers || {}).filter(w => w.active_tasks > 0).length,
          avg_load: Object.values(workerData.workers || {}).reduce((sum, w) => sum + (w.load || 0), 0) / Math.max(Object.keys(workerData.workers || {}).length, 1)
        });
      }

    } catch (error) {
      console.error('Error fetching monitoring data:', error);
      setError(`Failed to load monitoring data: ${error.message}`);
      addAlert('Failed to load Celery monitoring data', 'error', 5000);
    } finally {
      if (isInitialLoad) {
        setLoading(false);
      } else {
        setRefreshing(false);
      }
    }
  };

  useEffect(() => {
    if (token) {
      fetchMonitoringData(true); // Initial load
    }
  }, [token]);

  if (loading) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '50vh',
          flexDirection: 'column',
          gap: 2
        }}
      >
        <CircularProgress />
        <Typography variant="body2" color="text.secondary">
          Loading Celery monitoring data...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Typography variant="body2" color="text.secondary">
          Please check that the Celery workers are running and the monitoring endpoints are accessible.
        </Typography>
      </Box>
    );
  }

  return (
    <Box className="dashboard-container">
      {/* Page Header */}
      <Box className="page-header">
        <Typography className="page-title">
          Celery Monitor
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          Real-time monitoring of Celery workers, queues, and task processing
        </Typography>
      </Box>

      {/* Celery Monitor Component */}
      <CeleryMonitor
        celeryStats={celeryStats}
        queueStats={queueStats}
        workerStats={workerStats}
        onRefresh={() => fetchMonitoringData(false)}
        refreshing={refreshing}
      />
    </Box>
  );
};

export default CeleryMonitorPage;