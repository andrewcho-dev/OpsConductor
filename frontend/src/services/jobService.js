/**
 * Job Service
 * API service for Job management and execution results
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
 * Get individual action results for a job execution
 */
export const getExecutionActionResults = async (jobId, executionId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/executions/${executionId}/action-results`, {
      method: 'GET',
      headers: getAuthHeaders()
    });
    return await handleResponse(response);
  } catch (error) {
    console.error('Error fetching action results:', error);
    throw error;
  }
};

/**
 * Format execution time for display
 */
export const formatExecutionTime = (milliseconds) => {
  if (!milliseconds) return 'N/A';
  
  if (milliseconds < 1000) {
    return `${milliseconds}ms`;
  } else if (milliseconds < 60000) {
    return `${(milliseconds / 1000).toFixed(1)}s`;
  } else {
    const minutes = Math.floor(milliseconds / 60000);
    const seconds = ((milliseconds % 60000) / 1000).toFixed(1);
    return `${minutes}m ${seconds}s`;
  }
};

/**
 * Get status color for action results
 */
export const getActionStatusColor = (status) => {
  switch (status?.toLowerCase()) {
    case 'completed':
      return 'success';
    case 'failed':
      return 'error';
    case 'running':
      return 'warning';
    case 'scheduled':
      return 'info';
    default:
      return 'default';
  }
};

/**
 * Get status icon for action results
 */
export const getActionStatusIcon = (status) => {
  switch (status?.toLowerCase()) {
    case 'completed':
      return 'CheckCircle';
    case 'failed':
      return 'Error';
    case 'running':
      return 'PlayArrow';
    case 'scheduled':
      return 'Schedule';
    default:
      return 'Help';
  }
};