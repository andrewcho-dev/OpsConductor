import React, { useState, useEffect } from 'react';
import { formatLocalDateTime } from '../../utils/timeUtils';

const AlertLogs = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/notifications/alerts?limit=50');
      if (response.ok) {
        const data = await response.json();
        setAlerts(data);
      }
    } catch (error) {
      console.error('Error fetching alert logs:', error);
      setMessage({ type: 'error', text: 'Failed to load alert logs' });
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
        <p>Loading alert logs...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">⚠️ Alert Logs</h2>
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
                <th>Severity</th>
                <th>Message</th>
                <th>Status</th>
                <th>Created At</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((alert) => (
                <tr key={alert.id}>
                  <td>
                    <span className="badge badge-info">{alert.alert_type}</span>
                  </td>
                  <td>
                    <span className={`badge ${
                      alert.severity === 'critical' ? 'badge-error' :
                      alert.severity === 'error' ? 'badge-error' :
                      alert.severity === 'warning' ? 'badge-warning' :
                      'badge-info'
                    }`}>
                      {alert.severity}
                    </span>
                  </td>
                  <td>
                    <div className="text-sm">
                      {alert.message}
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${alert.is_resolved ? 'badge-success' : 'badge-warning'}`}>
                      {alert.is_resolved ? 'resolved' : 'active'}
                    </span>
                  </td>
                  <td>
                    <div className="text-sm">
                      {formatDate(alert.created_at)}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {alerts.length === 0 && !loading && (
          <div className="text-center py-8">
            <p className="text-gray-600">No alert logs found.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AlertLogs;
