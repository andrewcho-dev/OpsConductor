/**
 * WebSocket hook for real-time updates
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { selectCurrentToken } from '../store/slices/authSlice';
import { 
  updateExecutionProgress, 
  addExecutionLog,
  updateExecution 
} from '../store/slices/jobsSlice';
import { addAlert } from '../store/slices/uiSlice';

const useWebSocket = (room = null) => {
  const dispatch = useDispatch();
  const token = useSelector(selectCurrentToken);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000;

  const connect = useCallback(() => {
    if (!token) {
      console.warn('No token available for WebSocket connection');
      return;
    }

    try {
      const baseWsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
      const apiPath = process.env.REACT_APP_API_URL ? `${process.env.REACT_APP_API_URL}/websocket/connect` : '/api/v3/websocket/connect';
      const wsUrl = `${baseWsUrl}${apiPath}/${token}${room ? `?room=${room}` : ''}`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionError(null);
        reconnectAttempts.current = 0;

        // Send initial ping
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        
        // Attempt to reconnect if not a normal closure
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          scheduleReconnect();
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionError('WebSocket connection error');
      };

    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      setConnectionError('Failed to create WebSocket connection');
    }
  }, [token, room]);

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    reconnectTimeoutRef.current = setTimeout(() => {
      reconnectAttempts.current += 1;
      console.log(`Attempting to reconnect (${reconnectAttempts.current}/${maxReconnectAttempts})`);
      connect();
    }, reconnectDelay);
  }, [connect]);

  const handleMessage = useCallback((message) => {
    switch (message.type) {
      case 'pong':
        // Handle ping response
        break;

      case 'job_execution_started':
        dispatch(addAlert({
          type: 'info',
          message: `Job execution started: ${message.data.job_name}`,
          duration: 5000,
        }));
        break;

      case 'job_execution_progress':
        dispatch(updateExecutionProgress({
          executionId: message.data.execution_id,
          progress: {
            percentage: message.data.progress_percentage,
            currentTarget: message.data.current_target,
            completedTargets: message.data.completed_targets,
            totalTargets: message.data.total_targets,
          },
        }));
        break;

      case 'job_execution_completed':
        dispatch(updateExecution({
          id: message.data.execution_id,
          status: 'completed',
          completed_at: new Date().toISOString(),
          result: message.data.result,
        }));
        
        dispatch(addAlert({
          type: 'success',
          message: `Job execution completed successfully`,
          duration: 5000,
        }));
        break;

      case 'job_execution_failed':
        dispatch(updateExecution({
          id: message.data.execution_id,
          status: 'failed',
          completed_at: new Date().toISOString(),
          error_message: message.data.error_message,
        }));
        
        dispatch(addAlert({
          type: 'error',
          message: `Job execution failed: ${message.data.error_message}`,
          duration: 8000,
        }));
        break;

      case 'job_execution_log':
        dispatch(addExecutionLog({
          executionId: message.data.execution_id,
          log: message.data.log,
        }));
        break;

      case 'system_alert':
        dispatch(addAlert({
          type: message.data.level || 'info',
          message: message.data.message,
          duration: message.data.duration || 5000,
        }));
        break;

      case 'error':
        console.error('WebSocket error message:', message.message);
        setConnectionError(message.message);
        break;

      default:
        console.log('Unknown WebSocket message type:', message.type);
    }
  }, [dispatch]);

  const sendMessage = useCallback((message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  const subscribe = useCallback((roomName) => {
    sendMessage({ type: 'subscribe', room: roomName });
  }, [sendMessage]);

  const unsubscribe = useCallback((roomName) => {
    sendMessage({ type: 'unsubscribe', room: roomName });
  }, [sendMessage]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'User initiated disconnect');
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setConnectionError(null);
  }, []);

  // Connect on mount and when token changes
  useEffect(() => {
    if (token) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [token, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  // Ping interval to keep connection alive
  useEffect(() => {
    if (isConnected) {
      const pingInterval = setInterval(() => {
        sendMessage({ type: 'ping' });
      }, 30000); // Ping every 30 seconds

      return () => clearInterval(pingInterval);
    }
  }, [isConnected, sendMessage]);

  return {
    isConnected,
    connectionError,
    sendMessage,
    subscribe,
    unsubscribe,
    disconnect,
    reconnect: connect,
  };
};

export default useWebSocket;