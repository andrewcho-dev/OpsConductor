/**
 * Table Utilities
 * Standardized utilities for consistent table formatting across the system
 */

/**
 * Get row styling based on status/severity
 * Returns background color and text color for entire table row
 */
export const getRowStyling = (status, theme) => {
  if (!status) return {};
  
  const statusLower = status.toLowerCase();
  
  // ONLY Critical/Error/Failed states get RED coloring - truly significant problems
  if (['critical', 'error', 'failed', 'terminated'].includes(statusLower)) {
    return {
      backgroundColor: theme.palette.error.light,
      color: theme.palette.error.contrastText,
      '& .MuiTableCell-root': {
        color: theme.palette.error.contrastText,
        fontFamily: 'monospace',
        padding: '4px 8px'
      },
      '&:hover': {
        backgroundColor: theme.palette.error.contrastText,
        color: theme.palette.error.light,
        '& .MuiTableCell-root': {
          color: theme.palette.error.light,
          backgroundColor: 'transparent'
        }
      }
    };
  }
  
  // ONLY High severity warnings get YELLOW coloring - significant issues requiring attention
  if (['high'].includes(statusLower)) {
    return {
      backgroundColor: theme.palette.warning.light,
      color: theme.palette.warning.contrastText,
      '& .MuiTableCell-root': {
        color: theme.palette.warning.contrastText,
        fontFamily: 'monospace',
        padding: '4px 8px'
      },
      '&:hover': {
        backgroundColor: theme.palette.warning.contrastText,
        color: theme.palette.warning.light,
        '& .MuiTableCell-root': {
          color: theme.palette.warning.light,
          backgroundColor: 'transparent'
        }
      }
    };
  }
  
  // ALL OTHER STATES: No coloring - normal operations should be neutral
  // This includes: low, medium, info, success, completed, active, healthy, 
  // online, offline, pending, scheduled, paused, degraded, running, executing, processing, etc.
  
  // Default - no background color, just monospace font for all normal operations
  return {
    '& .MuiTableCell-root': {
      fontFamily: 'monospace',
      padding: '4px 8px'
    }
  };
};

/**
 * Standard table cell styling for monospace font
 */
export const getTableCellStyle = (isFirstColumn = false) => ({
  fontFamily: 'monospace',
  fontSize: '0.75rem',
  padding: '4px 8px' // Match header and filter padding
});

/**
 * Get severity-based row styling (for audit events, etc.)
 */
export const getSeverityRowStyling = (severity, theme) => {
  return getRowStyling(severity, theme);
};

/**
 * Get status-based row styling (for jobs, targets, etc.)
 */
export const getStatusRowStyling = (status, theme) => {
  return getRowStyling(status, theme);
};

/**
 * Get health-based row styling (for system health, etc.)
 */
export const getHealthRowStyling = (health, theme) => {
  return getRowStyling(health, theme);
};