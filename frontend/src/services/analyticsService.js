/**
 * Analytics Service
 * API service for analytics and reporting functionality.
 * CRITICAL: Uses relative URLs as required by architecture.
 */

// Development backend URL
const API_BASE_URL = process.env.REACT_APP_API_URL || '';

/**
 * Get authentication headers with bearer token
 */
const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
};

/**
 * Handle API response and errors
 */
const handleResponse = async (response) => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
  return response.json();
};

/**
 * Get real-time dashboard metrics
 */
export const getDashboardMetrics = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/analytics/dashboard`, {
      method: 'GET',
      headers: getAuthHeaders()
    });
    return await handleResponse(response);
  } catch (error) {
    console.error('Error fetching dashboard metrics:', error);
    throw error;
  }
};

/**
 * Get executive summary analytics
 */
export const getExecutiveSummary = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/analytics/summary`, {
      method: 'GET',
      headers: getAuthHeaders()
    });
    return await handleResponse(response);
  } catch (error) {
    console.error('Error fetching executive summary:', error);
    throw error;
  }
};

/**
 * Get job performance analytics
 */
export const getJobPerformanceAnalytics = async (jobId = null, days = 30) => {
  try {
    const params = new URLSearchParams();
    if (jobId) params.append('job_id', jobId);
    params.append('days', days);

    const response = await fetch(`${API_BASE_URL}/analytics/jobs/performance?${params}`, {
      method: 'GET',
      headers: getAuthHeaders()
    });
    return await handleResponse(response);
  } catch (error) {
    console.error('Error fetching job performance analytics:', error);
    throw error;
  }
};

/**
 * Get target performance analytics
 */
export const getTargetPerformanceAnalytics = async (targetId = null, days = 30) => {
  try {
    const params = new URLSearchParams();
    if (targetId) params.append('target_id', targetId);
    params.append('days', days);

    const response = await fetch(`${API_BASE_URL}/analytics/targets/performance?${params}`, {
      method: 'GET',
      headers: getAuthHeaders()
    });
    return await handleResponse(response);
  } catch (error) {
    console.error('Error fetching target performance analytics:', error);
    throw error;
  }
};

/**
 * Generate executive report
 */
export const generateExecutiveReport = async (days = 30) => {
  try {
    const params = new URLSearchParams();
    params.append('days', days);

    const response = await fetch(`${API_BASE_URL}/analytics/reports/executive?${params}`, {
      method: 'GET',
      headers: getAuthHeaders()
    });
    return await handleResponse(response);
  } catch (error) {
    console.error('Error generating executive report:', error);
    throw error;
  }
};

/**
 * Get performance trends
 */
export const getPerformanceTrends = async (hours = 24) => {
  try {
    const params = new URLSearchParams();
    params.append('hours', hours);

    const response = await fetch(`${API_BASE_URL}/analytics/trends/performance?${params}`, {
      method: 'GET',
      headers: getAuthHeaders()
    });
    return await handleResponse(response);
  } catch (error) {
    console.error('Error fetching performance trends:', error);
    throw error;
  }
};

/**
 * Get error summary
 */
export const getErrorSummary = async (hours = 24) => {
  try {
    const params = new URLSearchParams();
    params.append('hours', hours);

    const response = await fetch(`${API_BASE_URL}/analytics/errors/summary?${params}`, {
      method: 'GET',
      headers: getAuthHeaders()
    });
    return await handleResponse(response);
  } catch (error) {
    console.error('Error fetching error summary:', error);
    throw error;
  }
};

/**
 * Get resource utilization
 */
export const getResourceUtilization = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/analytics/resources`, {
      method: 'GET',
      headers: getAuthHeaders()
    });
    return await handleResponse(response);
  } catch (error) {
    console.error('Error fetching resource utilization:', error);
    throw error;
  }
};

/**
 * Analytics data processing utilities
 */
export const processAnalyticsData = {
  /**
   * Calculate success rate percentage
   */
  calculateSuccessRate: (successful, total) => {
    return total > 0 ? Math.round((successful / total) * 100) : 0;
  },

  /**
   * Format duration in human-readable format
   */
  formatDuration: (seconds) => {
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    } else if (seconds < 3600) {
      return `${Math.round(seconds / 60)}m`;
    } else {
      return `${Math.round(seconds / 3600)}h`;
    }
  },

  /**
   * Format timestamp for display
   */
  formatTimestamp: (timestamp) => {
    return new Date(timestamp).toLocaleString();
  },

  /**
   * Get status color for UI components
   */
  getStatusColor: (status) => {
    switch (status) {
      case 'completed':
      case 'healthy':
        return 'success';
      case 'failed':
      case 'critical':
        return 'error';
      case 'running':
      case 'scheduled':
        return 'primary';
      case 'warning':
        return 'warning';
      case 'cancelled':
      case 'inactive':
        return 'default';
      default:
        return 'default';
    }
  },

  /**
   * Process trend data for charts
   */
  processTrendData: (trendData, metric = 'total_executions') => {
    return {
      labels: trendData.map(item => new Date(item.timestamp || item.date).toLocaleDateString()),
      data: trendData.map(item => item[metric] || 0)
    };
  },

  /**
   * Calculate performance metrics
   */
  calculatePerformanceMetrics: (data) => {
    if (!data || data.length === 0) {
      return {
        min: 0,
        max: 0,
        avg: 0,
        median: 0,
        p95: 0
      };
    }

    const sorted = [...data].sort((a, b) => a - b);
    const length = sorted.length;

    return {
      min: sorted[0],
      max: sorted[length - 1],
      avg: data.reduce((sum, val) => sum + val, 0) / length,
      median: length % 2 === 0 
        ? (sorted[length / 2 - 1] + sorted[length / 2]) / 2
        : sorted[Math.floor(length / 2)],
      p95: sorted[Math.floor(length * 0.95) - 1] || sorted[length - 1]
    };
  }
};

/**
 * Real-time analytics hooks for React components
 */
import React from 'react';

export const useRealTimeAnalytics = (refreshInterval = 30000) => {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    const fetchData = async () => {
      try {
        const dashboardData = await getDashboardMetrics();
        setData(dashboardData);
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval]);

  return { data, loading, error, refresh: () => getDashboardMetrics() };
};

/**
 * Export default analytics service object
 */
const analyticsService = {
  getDashboardMetrics,
  getExecutiveSummary,
  getJobPerformanceAnalytics,
  getTargetPerformanceAnalytics,
  generateExecutiveReport,
  getPerformanceTrends,
  getErrorSummary,
  getResourceUtilization,
  processAnalyticsData,
  useRealTimeAnalytics
};

export default analyticsService;