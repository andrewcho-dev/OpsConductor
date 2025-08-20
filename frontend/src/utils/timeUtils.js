/**
 * Time Utilities for OpsConductor Frontend
 * Centralized timezone handling to ensure consistent local time display
 */

/**
 * Convert UTC datetime string from backend to local time for display
 * @param {string} utcDateString - UTC datetime string from backend
 * @returns {string} - Formatted local time string
 */
export const formatLocalDateTime = (utcDateString) => {
  if (!utcDateString) return 'N/A';
  
  try {
    // Parse the UTC datetime string
    let date;
    
    // Handle different UTC datetime formats from backend
    if (utcDateString.endsWith('Z')) {
      // Already has UTC indicator
      date = new Date(utcDateString);
    } else if (utcDateString.includes('+') || utcDateString.includes('T') && utcDateString.includes('-')) {
      // Has timezone offset or is ISO format
      date = new Date(utcDateString);
    } else {
      // Assume UTC if no timezone info (backend sends UTC times)
      date = new Date(utcDateString + 'Z');
    }
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      console.warn('Invalid date string:', utcDateString);
      return 'Invalid Date';
    }
    
    // Return local time string
    return date.toLocaleString();
  } catch (error) {
    console.error('Error formatting date:', utcDateString, error);
    return 'Invalid Date';
  }
};

/**
 * Convert UTC datetime string to local date only
 * @param {string} utcDateString - UTC datetime string from backend
 * @returns {string} - Formatted local date string
 */
export const formatLocalDate = (utcDateString) => {
  if (!utcDateString) return 'N/A';
  
  try {
    let date;
    
    if (utcDateString.endsWith('Z')) {
      date = new Date(utcDateString);
    } else if (utcDateString.includes('+') || utcDateString.includes('T') && utcDateString.includes('-')) {
      date = new Date(utcDateString);
    } else {
      date = new Date(utcDateString + 'Z');
    }
    
    if (isNaN(date.getTime())) {
      return 'Invalid Date';
    }
    
    return date.toLocaleDateString();
  } catch (error) {
    console.error('Error formatting date:', utcDateString, error);
    return 'Invalid Date';
  }
};

/**
 * Convert UTC datetime string to local time only
 * @param {string} utcDateString - UTC datetime string from backend
 * @returns {string} - Formatted local time string
 */
export const formatLocalTime = (utcDateString) => {
  if (!utcDateString) return 'N/A';
  
  try {
    let date;
    
    if (utcDateString.endsWith('Z')) {
      date = new Date(utcDateString);
    } else if (utcDateString.includes('+') || utcDateString.includes('T') && utcDateString.includes('-')) {
      date = new Date(utcDateString);
    } else {
      date = new Date(utcDateString + 'Z');
    }
    
    if (isNaN(date.getTime())) {
      return 'Invalid Time';
    }
    
    return date.toLocaleTimeString();
  } catch (error) {
    console.error('Error formatting time:', utcDateString, error);
    return 'Invalid Time';
  }
};

/**
 * Convert local datetime-local input value to proper format for backend
 * The backend expects local time and will convert to UTC internally
 * @param {string} localDateTimeValue - Value from datetime-local input
 * @returns {string} - ISO string representing local time (not UTC)
 */
export const formatLocalDateTimeForBackend = (localDateTimeValue) => {
  if (!localDateTimeValue) return null;
  
  try {
    // datetime-local gives us "YYYY-MM-DDTHH:mm" in local time
    // We need to treat this as UTC time for the backend
    // SIMPLE APPROACH: Just append 'Z' to make it UTC
    
    // Add seconds if not present
    let formattedValue = localDateTimeValue;
    if (formattedValue.length === 16) { // "YYYY-MM-DDTHH:mm"
      formattedValue += ':00';
    }
    
    // Validate the format
    const testDate = new Date(formattedValue + 'Z');
    if (isNaN(testDate.getTime())) {
      throw new Error('Invalid date format');
    }
    
    // Return as UTC ISO string - backend stores this directly
    return formattedValue + 'Z';
  } catch (error) {
    console.error('Error formatting datetime for backend:', localDateTimeValue, error);
    throw error;
  }
};

/**
 * Format UTC datetime to show both UTC and local time for user clarity
 * @param {string} utcDateString - UTC datetime string from backend
 * @returns {object} - Object with both UTC and local formatted strings
 */
export const formatBothUTCAndLocal = (utcDateString) => {
  if (!utcDateString) return { utc: 'N/A', local: 'N/A', combined: 'Not scheduled' };
  
  try {
    let date;
    
    if (utcDateString.endsWith('Z')) {
      date = new Date(utcDateString);
    } else if (utcDateString.includes('+') || utcDateString.includes('T') && utcDateString.includes('-')) {
      date = new Date(utcDateString);
    } else {
      date = new Date(utcDateString + 'Z');
    }
    
    if (isNaN(date.getTime())) {
      return { utc: 'Invalid Date', local: 'Invalid Date', combined: 'Invalid Date' };
    }
    
    // Format UTC time
    const utcFormatted = date.toISOString().replace('T', ' ').replace('.000Z', ' UTC');
    
    // Format local time
    const localFormatted = date.toLocaleString() + ' (Local)';
    
    // Combined format for display
    const combined = `${localFormatted}\n${utcFormatted}`;
    
    return {
      utc: utcFormatted,
      local: localFormatted,
      combined: combined
    };
  } catch (error) {
    console.error('Error formatting datetime:', utcDateString, error);
    return { utc: 'Invalid Date', local: 'Invalid Date', combined: 'Invalid Date' };
  }
};

/**
 * Get current local datetime in format suitable for datetime-local input
 * @param {number} offsetMinutes - Minutes to add to current time (default: 1)
 * @returns {string} - Formatted datetime string for datetime-local input
 */
export const getCurrentLocalDateTimeForInput = (offsetMinutes = 1) => {
  const now = new Date();
  now.setMinutes(now.getMinutes() + offsetMinutes);
  
  // Format as YYYY-MM-DDTHH:mm for datetime-local input
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  
  return `${year}-${month}-${day}T${hours}:${minutes}`;
};

/**
 * Format relative time (e.g., "in 5 minutes", "2 hours ago")
 * @param {string} utcDateString - UTC datetime string from backend
 * @returns {string} - Relative time string
 */
export const formatRelativeTime = (utcDateString) => {
  if (!utcDateString) return 'N/A';
  
  try {
    let date;
    
    if (utcDateString.endsWith('Z')) {
      date = new Date(utcDateString);
    } else if (utcDateString.includes('+') || utcDateString.includes('T') && utcDateString.includes('-')) {
      date = new Date(utcDateString);
    } else {
      date = new Date(utcDateString + 'Z');
    }
    
    if (isNaN(date.getTime())) {
      return 'Invalid Date';
    }
    
    const now = new Date();
    const diffMs = date.getTime() - now.getTime();
    const diffMinutes = Math.floor(Math.abs(diffMs) / 60000);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    const isPast = diffMs < 0;
    const suffix = isPast ? ' ago' : '';
    const prefix = isPast ? '' : 'in ';
    
    if (diffDays > 0) {
      return `${prefix}${diffDays} day${diffDays > 1 ? 's' : ''}${suffix}`;
    } else if (diffHours > 0) {
      return `${prefix}${diffHours} hour${diffHours > 1 ? 's' : ''}${suffix}`;
    } else if (diffMinutes > 0) {
      return `${prefix}${diffMinutes} minute${diffMinutes > 1 ? 's' : ''}${suffix}`;
    } else {
      return isPast ? 'just now' : 'now';
    }
  } catch (error) {
    console.error('Error formatting relative time:', utcDateString, error);
    return 'Invalid Date';
  }
};

/**
 * Validate that a datetime-local input value is in the future
 * @param {string} localDateTimeValue - Value from datetime-local input
 * @returns {boolean} - True if the datetime is in the future
 */
export const isDateTimeInFuture = (localDateTimeValue) => {
  if (!localDateTimeValue) return false;
  
  try {
    const selectedDate = new Date(localDateTimeValue);
    const now = new Date();
    
    return selectedDate > now;
  } catch (error) {
    return false;
  }
};

/**
 * Get timezone display name from system info
 * @param {string} token - Authentication token (optional)
 * @returns {Promise<string>} - Timezone display name
 */
export const getSystemTimezone = async (token = null) => {
  try {
    const headers = {
      'Content-Type': 'application/json'
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    const apiBaseUrl = process.env.REACT_APP_API_URL || '';
    const response = await fetch(`${apiBaseUrl}/api/system/info`, { headers });
    if (response.ok) {
      const data = await response.json();
      return data.timezone?.display_name || 'Local Time';
    }
  } catch (error) {
    console.error('Failed to fetch system timezone:', error);
  }
  
  // Fallback to browser timezone
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || 'Local Time';
  } catch (error) {
    return 'Local Time';
  }
};