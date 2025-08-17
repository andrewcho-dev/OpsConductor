/**
 * Standard Page Layout Component
 * Enforces consistent page structure across the entire application
 * 
 * This component ensures:
 * - Consistent container styling
 * - Standard header formatting
 * - Proper content area structure
 * - Optional stats grid
 * - Standard loading states
 */
import React from 'react';
import { Typography, CircularProgress, Box } from '@mui/material';
import '../../styles/dashboard.css';

const StandardPageLayout = ({
  title,
  actions,
  children,
  loading = false,
  loadingText = "Loading...",
  stats = null,
  className = '',
  containerClass = 'dashboard-container',
  ...props
}) => {
  if (loading) {
    return (
      <div className={containerClass}>
        <div className="loading-container">
          <CircularProgress size={24} />
          <Typography variant="body2" sx={{ ml: 2, color: 'text.secondary' }}>
            {loadingText}
          </Typography>
        </div>
      </div>
    );
  }

  return (
    <div className={`${containerClass} ${className}`} {...props}>
      {/* Standard Page Header */}
      <div className="page-header">
        <Typography className="page-title">
          {title}
        </Typography>
        <div className="page-actions">
          {actions}
        </div>
      </div>

      {/* Optional Stats Grid */}
      {stats && (
        <div className="stats-grid">
          {stats}
        </div>
      )}

      {/* Main Content */}
      {children}
    </div>
  );
};

/**
 * Standard Content Card Component
 * For consistent main content areas
 */
export const StandardContentCard = ({
  title,
  subtitle,
  children,
  className = '',
  ...props
}) => {
  return (
    <div className={`main-content-card fade-in ${className}`} {...props}>
      {title && (
        <div className="content-card-header">
          <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
              {subtitle}
            </Typography>
          )}
        </div>
      )}
      <div className="content-card-body">
        {children}
      </div>
    </div>
  );
};

/**
 * Standard Stat Card Component
 * For consistent statistics display
 */
export const StandardStatCard = ({
  icon,
  value,
  label,
  iconColor = 'primary',
  className = '',
  ...props
}) => {
  return (
    <div className={`stat-card fade-in ${className}`} {...props}>
      <div className="stat-card-content">
        <div className={`stat-icon ${iconColor}`}>
          {icon}
        </div>
        <div className="stat-details">
          <h3>{value}</h3>
          <p>{label}</p>
        </div>
      </div>
    </div>
  );
};

export default StandardPageLayout;