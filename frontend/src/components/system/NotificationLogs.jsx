import React, { useState, useEffect } from 'react';
import { formatLocalDateTime } from '../../utils/timeUtils';

const NotificationLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/notifications/logs?limit=50');
      if (response.ok) {
        const data = await response.json();
        setLogs(data);
      }
    } catch (error) {
      console.error('Error fetching notification logs:', error);
      setMessage({ type: 'error', text: 'Failed to load notification logs' });
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return formatLocalDateTime(dateString);
  };

  if (loading) {
    return (
      <div className="text-center">
        <div className="loading-spinner"></div>
        <p>Loading notification logs...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">📋 Notification Logs</h2>
        </div>

        {message && (
          <div className={`message ${message.type}`}>
            {message.text}
          </div>
        )}

        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Recipient</th>
                <th>Subject</th>
                <th>Status</th>
                <th>Sent At</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>
                    <span className="badge badge-info">{log.notification_type}</span>
                  </td>
                  <td>{log.recipient}</td>
                  <td>
                    <div className="text-sm">
                      {log.subject || 'No subject'}
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${
                      log.status === 'sent' ? 'badge-success' : 
                      log.status === 'failed' ? 'badge-error' : 
                      'badge-warning'
                    }`}>
                      {log.status}
                    </span>
                  </td>
                  <td>
                    <div className="text-sm">
                      {log.sent_at ? formatDate(log.sent_at) : 'Not sent'}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {logs.length === 0 && !loading && (
          <div className="text-center py-8">
            <p className="text-gray-600">No notification logs found.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default NotificationLogs;
