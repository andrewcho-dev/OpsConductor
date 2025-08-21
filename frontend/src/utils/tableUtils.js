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
  
  // ONLY Critical/Error/Failed states get MORE DISTINCTIVE RED coloring - truly significant problems
  if (['critical', 'error', 'failed', 'terminated'].includes(statusLower)) {
    return {
      backgroundColor: 'rgba(244, 67, 54, 0.22)', // More distinctive red tint
      color: 'inherit', // Keep normal text color
      '& .MuiTableCell-root': {
        color: 'inherit',
        fontFamily: 'monospace',
        padding: '4px 8px'
      },
      '&:hover': {
        backgroundColor: 'rgba(244, 67, 54, 0.28)', // More visible on hover
        '& .MuiTableCell-root': {
          backgroundColor: 'transparent'
        }
      }
    };
  }
  
  // ONLY High severity warnings get MORE DISTINCTIVE ORANGE coloring - significant issues requiring attention
  if (['high'].includes(statusLower)) {
    return {
      backgroundColor: 'rgba(255, 152, 0, 0.18)', // More distinctive orange tint
      color: 'inherit', // Keep normal text color
      '& .MuiTableCell-root': {
        color: 'inherit',
        fontFamily: 'monospace',
        padding: '4px 8px'
      },
      '&:hover': {
        backgroundColor: 'rgba(255, 152, 0, 0.25)', // More visible on hover
        '& .MuiTableCell-root': {
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

