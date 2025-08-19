/**
 * Activity-based session management service.
 * Tracks user activity and manages session timeouts.
 */

class SessionService {
  constructor() {
    this.activityTimeout = 60 * 60 * 1000; // 1 hour in milliseconds
    this.warningThreshold = 2 * 60 * 1000; // 2 minutes in milliseconds
    this.checkInterval = 30 * 1000; // Check every 30 seconds
    
    this.lastActivity = Date.now();
    this.sessionCheckTimer = null;
    this.warningShown = false;
    this.sessionId = null;
    
    this.listeners = {
      warning: [],
      timeout: [],
      extend: []
    };
    
    this.init();
  }
  
  init() {
    // Track various user activities
    const activityEvents = [
      'mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'
    ];
    
    activityEvents.forEach(event => {
      document.addEventListener(event, this.updateActivity.bind(this), true);
    });
    
    // Start session monitoring
    this.startSessionMonitoring();
  }
  
  updateActivity() {
    const now = Date.now();
    const wasInactive = (now - this.lastActivity) > this.warningThreshold;
    
    this.lastActivity = now;
    this.warningShown = false;
    
    // If user was inactive and now active, notify listeners
    if (wasInactive) {
      this.notifyListeners('extend');
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
  
  async checkSessionStatus() {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        return;
      }
      
      const response = await fetch('/auth/session/status', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          this.handleSessionExpired();
        }
        return;
      }
      
      const status = await response.json();
      
      if (status.expired) {
        this.handleSessionExpired();
      } else if (status.warning && !this.warningShown) {
        this.handleSessionWarning(status.time_remaining);
      }
      
    } catch (error) {
      console.error('Session status check failed:', error);
    }
  }
  
  handleSessionWarning(timeRemaining) {
    this.warningShown = true;
    this.notifyListeners('warning', { timeRemaining });
  }
  
  handleSessionExpired() {
    this.stopSessionMonitoring();
    this.notifyListeners('timeout');
  }
  
  async extendSession() {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        return false;
      }
      
      const response = await fetch('/auth/session/extend', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        this.warningShown = false;
        this.updateActivity();
        this.notifyListeners('extend');
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Session extend failed:', error);
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
    this.sessionId = sessionId;
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
    this.stopSessionMonitoring();
    
    // Remove event listeners
    const activityEvents = [
      'mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'
    ];
    
    activityEvents.forEach(event => {
      document.removeEventListener(event, this.updateActivity.bind(this), true);
    });
    
    // Clear listeners
    this.listeners = { warning: [], timeout: [], extend: [] };
  }
}

// Create global instance
export const sessionService = new SessionService();
export default sessionService;