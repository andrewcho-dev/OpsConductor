import React from 'react';

const NotificationStats = ({ stats, loading, onRefresh }) => {
  if (loading) {
    return (
      <div className="text-center">
        <div className="loading-spinner"></div>
        <p>Loading statistics...</p>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-center">
        <p>No statistics available.</p>
        <button className="btn btn-primary mt-2" onClick={onRefresh}>
          Refresh
        </button>
      </div>
    );
  }

  const statCards = [
    {
      title: 'Total Notifications',
      value: stats.total_notifications,
      icon: '📧',
      color: 'blue'
    },
    {
      title: 'Sent Notifications',
      value: stats.sent_notifications,
      icon: '✅',
      color: 'green'
    },
    {
      title: 'Failed Notifications',
      value: stats.failed_notifications,
      icon: '❌',
      color: 'red'
    },
    {
      title: 'Pending Notifications',
      value: stats.pending_notifications,
      icon: '⏳',
      color: 'yellow'
    },
    {
      title: 'Total Alerts',
      value: stats.total_alerts,
      icon: '🚨',
      color: 'orange'
    },
    {
      title: 'Active Alerts',
      value: stats.active_alerts,
      icon: '⚠️',
      color: 'red'
    },
    {
      title: 'Resolved Alerts',
      value: stats.resolved_alerts,
      icon: '✅',
      color: 'green'
    }
  ];

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">📊 Notification Statistics</h2>
          <button className="btn btn-primary" onClick={onRefresh}>
            Refresh
          </button>
        </div>

        <div className="grid grid-4">
          {statCards.map((stat, index) => (
            <div key={index} className="card">
              <div className="text-center">
                <div className="text-3xl mb-2">{stat.icon}</div>
                <div className="text-2xl font-bold text-gray-800">{stat.value}</div>
                <div className="text-sm text-gray-600">{stat.title}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-2 mt-4">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">📈 Notification Success Rate</h3>
          </div>
          <div className="text-center">
            {stats.total_notifications > 0 ? (
              <div>
                <div className="text-3xl font-bold text-green-600">
                  {Math.round((stats.sent_notifications / stats.total_notifications) * 100)}%
                </div>
                <div className="text-sm text-gray-600">
                  {stats.sent_notifications} of {stats.total_notifications} notifications sent successfully
                </div>
              </div>
            ) : (
              <div className="text-gray-600">No notifications sent yet</div>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">🚨 Alert Resolution Rate</h3>
          </div>
          <div className="text-center">
            {stats.total_alerts > 0 ? (
              <div>
                <div className="text-3xl font-bold text-blue-600">
                  {Math.round((stats.resolved_alerts / stats.total_alerts) * 100)}%
                </div>
                <div className="text-sm text-gray-600">
                  {stats.resolved_alerts} of {stats.total_alerts} alerts resolved
                </div>
              </div>
            ) : (
              <div className="text-gray-600">No alerts created yet</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationStats;
