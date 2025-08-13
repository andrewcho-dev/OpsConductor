import React, { useState, useEffect } from 'react';

const AlertRules = () => {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/notifications/alerts/rules');
      if (response.ok) {
        const data = await response.json();
        setRules(data);
      }
    } catch (error) {
      console.error('Error fetching alert rules:', error);
      setMessage({ type: 'error', text: 'Failed to load alert rules' });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center">
        <div className="loading-spinner"></div>
        <p>Loading alert rules...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">🚨 Alert Rules</h2>
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
                <th>Name</th>
                <th>Type</th>
                <th>Recipients</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rules.map((rule) => (
                <tr key={rule.id}>
                  <td>
                    <div>
                      <strong>{rule.name}</strong>
                      {rule.description && (
                        <div className="text-sm text-gray-600">{rule.description}</div>
                      )}
                    </div>
                  </td>
                  <td>
                    <span className="badge badge-info">{rule.alert_type}</span>
                  </td>
                  <td>
                    <div className="text-sm">
                      {rule.recipients.join(', ')}
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${rule.is_active ? 'badge-success' : 'badge-error'}`}>
                      {rule.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    <div className="flex gap-2">
                      <button className="btn btn-secondary">
                        Edit
                      </button>
                      <button className="btn btn-danger">
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {rules.length === 0 && !loading && (
          <div className="text-center py-8">
            <p className="text-gray-600">No alert rules found.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AlertRules;
