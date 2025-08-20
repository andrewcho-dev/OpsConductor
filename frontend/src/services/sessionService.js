/**
 * Activity-based session management service.
 * Tracks user activity and manages session timeouts.
 */

class SessionService {
  constructor() {
    // Default values (will be updated from system settings)
    this.activityTimeout = 60 * 60 * 1000; // 60 minutes default (inactivity_timeout_minutes)
    this.warningThreshold = 2 * 60 * 1000; // 2 minutes warning before timeout (warning_time_minutes)
    this.checkInterval = 5 * 1000; // Check every 5 seconds
    
    this.lastActivity = Date.now();
    this.sessionCheckTimer = null;
    this.warningShown = false;
    this.sessionId = null;
    this.settingsLoaded = false;
    
    this.listeners = {
      warning: [],
      timeout: [],
      extend: []
    };
    
    console.log('🔧 SessionService initialized with defaults');
    
    this.init();
  }
  
  init() {
    console.log('🚀 Initializing session service...');
    
    // Track various user activities
    const activityEvents = [
      'mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'
    ];
    
    // Bind the updateActivity method once to avoid memory leaks
    this._boundUpdateActivity = this.updateActivity.bind(this);
    
    activityEvents.forEach(event => {
      document.addEventListener(event, this._boundUpdateActivity, true);
    });
    
    // Fetch session settings from server immediately
    const token = localStorage.getItem('access_token');
    if (token) {
      console.log('🔑 Token found, fetching session settings...');
      this.fetchSessionSettings();
      
      // Start session monitoring
      this.startSessionMonitoring();
    } else {
      console.log('🔑 No token found, session service in standby mode');
    }
    
    // Set up a periodic refresh of session settings (every 5 minutes)
    this._settingsRefreshTimer = setInterval(() => {
      const token = localStorage.getItem('access_token');
      if (token) {
        console.log('⏰ Periodic refresh of session settings');
        this.fetchSessionSettings();
      }
    }, 5 * 60 * 1000); // 5 minutes
  }
  
  // Fetch session settings from server
  fetchSessionSettings() {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        return;
      }
      
      // Fetch system settings to get configurable timeout values
      const apiUrl = process.env.REACT_APP_API_URL || '';
      fetch(`${apiUrl}/api/system/settings`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      .then(response => {
        if (response.ok) {
          return response.json();
        } else {
          console.warn('⚠️ Failed to fetch system settings:', response.status);
          throw new Error('Failed to fetch system settings');
        }
      })
      .then(data => {
        console.log('✅ Received system settings from server:', data);
        
        const settings = data.settings || {};
        
        // Update activity timeout from inactivity_timeout_minutes
        if (settings.inactivity_timeout_minutes) {
          this.activityTimeout = settings.inactivity_timeout_minutes * 60 * 1000; // Convert minutes to ms
          console.log(`⏱️ Updated activity timeout to ${settings.inactivity_timeout_minutes} minutes from system settings`);
        }
        
        // Update warning threshold from warning_time_minutes
        if (settings.warning_time_minutes) {
          this.warningThreshold = settings.warning_time_minutes * 60 * 1000; // Convert minutes to ms
          console.log(`⚠️ Updated warning threshold to ${settings.warning_time_minutes} minutes from system settings`);
        }
        
        this.settingsLoaded = true;
        
        // Force update activity to reset the timer
        this.lastActivity = Date.now();
        console.log(`🔄 Reset activity timer at ${new Date(this.lastActivity).toLocaleTimeString()}`);
        
        // Debug log current state
        console.log(`🔍 Current session state:
          - Activity timeout: ${this.activityTimeout / 60000} minutes
          - Warning threshold: ${this.warningThreshold / 60000} minutes
          - Time until warning: ${(this.activityTimeout - this.warningThreshold) / 60000} minutes
          - Check interval: ${this.checkInterval / 1000} seconds
        `);
      })
      .catch(error => {
        console.error('❌ Error fetching session settings:', error);
      });
    } catch (error) {
      console.error('❌ Error in fetchSessionSettings:', error);
    }
  }
  
  updateActivity() {
    const now = Date.now();
    const timeSinceLastActivity = now - this.lastActivity;
    
    // Only log if it's been more than 5 seconds since the last activity
    // to avoid flooding the console with messages
    if (timeSinceLastActivity > 5000) {
      console.log('🔄 Activity detected, updating last activity timestamp');
      console.log(`⏱️ Time since last activity: ${Math.round(timeSinceLastActivity / 1000)} seconds`);
    }
    
    const wasInactive = timeSinceLastActivity > (this.activityTimeout - this.warningThreshold);
    
    // Update the timestamp
    this.lastActivity = now;
    
    // If warning was shown, clear it
    if (this.warningShown) {
      console.log('✅ User is active again, clearing warning');
      this.warningShown = false;
      this.notifyListeners('extend');
    }
    
    // If user was inactive and now active, notify listeners and extend session
    if (wasInactive) {
      console.log('🔄 User was inactive and is now active, extending session');
      this.extendSession(); // Actively extend the session on server
    } else {
      // Log activity to server periodically (every 30 seconds)
      // to avoid too many requests
      if (this._lastServerActivity === undefined || (now - this._lastServerActivity) > 30000) {
        this._lastServerActivity = now;
        this.logActivity();
      }
    }
  }
  
  // Log activity to server
  logActivity() {
    // Update the timestamp locally
    this.lastActivity = Date.now();
    console.log(`🔄 Activity logged locally at ${new Date(this.lastActivity).toLocaleTimeString()}`);
    
    // Call server endpoint to log activity
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        return;
      }
      
      // Make API call to extend session (auth service)
      const authUrl = process.env.REACT_APP_AUTH_URL || '/api/auth';
      fetch(`${authUrl}/session/extend`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      .then(response => {
        if (response.ok) {
          console.log('✅ Activity logged to server');
        } else {
          console.warn('⚠️ Failed to log activity to server:', response.status);
        }
      })
      .catch(error => {
        console.error('❌ Error logging activity to server:', error);
      });
    } catch (error) {
      console.error('❌ Error in logActivity:', error);
    }
  }
  
  startSessionMonitoring() {
    if (this.sessionCheckTimer) {
      clearInterval(this.sessionCheckTimer);
    }
    
    this.sessionCheckTimer = setInterval(() => {
      this.checkSessionStatus();
    }, this.checkInterval);
  }
  
  stopSessionMonitoring() {
    if (this.sessionCheckTimer) {
      clearInterval(this.sessionCheckTimer);
      this.sessionCheckTimer = null;
    }
  }
  
  // Client-side only session status check - no server dependency
  checkSessionStatus() {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        console.log('🔑 No token found, cannot check session status');
        return;
      }
      
      // Check time since last activity
      const now = Date.now();
      const inactiveTime = now - this.lastActivity;
      
      // Only log every 30 seconds to reduce console spam
      if (Math.round(inactiveTime / 1000) % 30 === 0 || inactiveTime < 5000) {
        console.log(`⏱️ Time since last activity: ${Math.round(inactiveTime / 1000)} seconds`);
        console.log(`⏱️ Time until warning: ${Math.round((this.activityTimeout - this.warningThreshold - inactiveTime) / 1000)} seconds`);
        console.log(`⏱️ Time until timeout: ${Math.round((this.activityTimeout - inactiveTime) / 1000)} seconds`);
      }
      
      // If inactive for longer than timeout, force logout
      if (inactiveTime > this.activityTimeout) {
        console.log('⚠️ User inactive for too long, forcing logout');
        console.log(`⏱️ Inactive time: ${Math.round(inactiveTime / 1000)} seconds`);
        console.log(`⏱️ Timeout: ${Math.round(this.activityTimeout / 1000)} seconds`);
        this.handleSessionExpired();
        return;
      }
      
      // If approaching timeout, show warning
      const warningTime = this.activityTimeout - this.warningThreshold;
      if (inactiveTime > warningTime && !this.warningShown) {
        console.log('⚠️ User approaching inactivity timeout, showing warning');
        console.log(`⏱️ Inactive time: ${Math.round(inactiveTime / 1000)} seconds`);
        console.log(`⏱️ Warning threshold: ${Math.round(warningTime / 1000)} seconds`);
        
        const timeRemaining = this.activityTimeout - inactiveTime;
        console.log(`⏱️ Time remaining: ${Math.round(timeRemaining / 1000)} seconds`);
        
        this.handleSessionWarning(timeRemaining);
        return;
      }
      
      // If warning was shown but user is now active again, clear warning
      if (this.warningShown && inactiveTime < warningTime) {
        console.log('✅ User is active again, clearing warning');
        this.warningShown = false;
        this.notifyListeners('extend');
      }
      
    } catch (error) {
      console.error('❌ Session status check failed:', error);
    }
  }
  
  handleSessionWarning(timeRemaining) {
    // Convert milliseconds to seconds for the UI
    const timeRemainingSeconds = Math.round(timeRemaining / 1000);
    
    console.log(`⏱️ Showing warning with ${timeRemainingSeconds} seconds remaining`);
    
    this.warningShown = true;
    this.notifyListeners('warning', { timeRemaining: timeRemainingSeconds });
  }
  
  handleSessionExpired() {
    console.log('🔒 Session expired, logging out user');
    this.stopSessionMonitoring();
    
    // Clear token and session data
    localStorage.removeItem('access_token');
    this.sessionId = null;
    
    // Notify listeners
    this.notifyListeners('timeout');
    
    // Force page reload to ensure user is logged out
    setTimeout(() => {
      console.log('🔄 Forcing page reload to ensure logout');
      window.location.href = '/login';
    }, 500);
  }
  
  // Extend session on server
  extendSession() {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        return false;
      }
      
      // Update locally
      console.log('🔄 Extending session locally');
      this.lastActivity = Date.now();
      this.warningShown = false;
      this.notifyListeners('extend');
      
      // Call server endpoint to extend session
      const authUrl = process.env.REACT_APP_AUTH_URL || '/api/auth';
      fetch(`${authUrl}/session/extend`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      .then(response => {
        if (response.ok) {
          console.log('✅ Session extended on server');
        } else {
          console.warn('⚠️ Failed to extend session on server:', response.status);
        }
      })
      .catch(error => {
        console.error('❌ Error extending session on server:', error);
      });
      
      return true;
    } catch (error) {
      console.error('❌ Session extend failed:', error);
      return false;
    }
  }
  
  // Event listener management
  addEventListener(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event].push(callback);
    }
  }
  
  removeEventListener(event, callback) {
    if (this.listeners[event]) {
      const index = this.listeners[event].indexOf(callback);
      if (index > -1) {
        this.listeners[event].splice(index, 1);
      }
    }
  }
  
  notifyListeners(event, data = null) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Session event listener error (${event}):`, error);
        }
      });
    }
  }
  
  // Public methods
  setSessionId(sessionId) {
    console.log(`🔑 Setting session ID: ${sessionId}`);
    this.sessionId = sessionId;
  }
  
  destroy() {
    console.log('🧹 Destroying session service');
    this.stopSessionMonitoring();
    
    // Remove all event listeners
    const activityEvents = [
      'mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'
    ];
    
    activityEvents.forEach(event => {
      document.removeEventListener(event, this.updateActivity.bind(this), true);
    });
    
    // Clear all data
    this.sessionId = null;
    this.lastActivity = null;
    this.warningShown = false;
    
    // Clear listeners
    this.listeners = {
      warning: [],
      timeout: [],
      extend: []
    };
  }
  
  getTimeUntilWarning() {
    const timeSinceActivity = Date.now() - this.lastActivity;
    const timeUntilWarning = this.activityTimeout - this.warningThreshold - timeSinceActivity;
    return Math.max(0, timeUntilWarning);
  }
  
  getTimeUntilTimeout() {
    const timeSinceActivity = Date.now() - this.lastActivity;
    const timeUntilTimeout = this.activityTimeout - timeSinceActivity;
    return Math.max(0, timeUntilTimeout);
  }
  
  isActive() {
    const timeSinceActivity = Date.now() - this.lastActivity;
    return timeSinceActivity < this.activityTimeout;
  }
  
  destroy() {
    console.log('🧹 Destroying session service...');
    
    // Stop all timers
    this.stopSessionMonitoring();
    
    if (this._settingsRefreshTimer) {
      clearInterval(this._settingsRefreshTimer);
      this._settingsRefreshTimer = null;
    }
    
    // Remove event listeners using the bound function reference
    const activityEvents = [
      'mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'
    ];
    
    if (this._boundUpdateActivity) {
      activityEvents.forEach(event => {
        document.removeEventListener(event, this._boundUpdateActivity, true);
      });
      this._boundUpdateActivity = null;
    }
    
    // Clear all state
    this.sessionId = null;
    this.lastActivity = null;
    this.warningShown = false;
    this._lastServerActivity = null;
    
    // Clear listeners
    this.listeners = { warning: [], timeout: [], extend: [] };
    
    console.log('✅ Session service destroyed');
  }
}

// Create global instance
export const sessionService = new SessionService();
export default sessionService;