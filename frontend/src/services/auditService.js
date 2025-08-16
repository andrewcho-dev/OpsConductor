/**
 * Audit Service for handling audit-related API calls and data enrichment
 */

class AuditService {
  constructor() {
    this.userLookupCache = new Map();
    this.targetLookupCache = new Map();
    this.cacheExpiry = 5 * 60 * 1000; // 5 minutes
  }

  /**
   * Get authorization headers
   */
  getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  /**
   * Fetch user lookup data from API
   */
  async fetchUserLookups(userIds = null) {
    try {
      const url = userIds 
        ? `/api/v1/audit/lookups/users?user_ids=${userIds.join(',')}`
        : '/api/v1/audit/lookups/users';
      
      const response = await fetch(url, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch user lookups: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Cache the results
      const cacheEntry = {
        data: data.users,
        timestamp: Date.now()
      };
      
      if (userIds) {
        // Cache specific users
        userIds.forEach(id => {
          if (data.users[id]) {
            this.userLookupCache.set(id, cacheEntry);
          }
        });
      } else {
        // Cache all users
        Object.keys(data.users).forEach(id => {
          this.userLookupCache.set(parseInt(id), cacheEntry);
        });
      }

      return data.users;
    } catch (error) {
      console.error('Error fetching user lookups:', error);
      return {};
    }
  }

  /**
   * Fetch target lookup data from API
   */
  async fetchTargetLookups(targetIds = null) {
    try {
      const url = targetIds 
        ? `/api/v1/audit/lookups/targets?target_ids=${targetIds.join(',')}`
        : '/api/v1/audit/lookups/targets';
      
      const response = await fetch(url, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch target lookups: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Cache the results
      const cacheEntry = {
        data: data.targets,
        timestamp: Date.now()
      };
      
      if (targetIds) {
        // Cache specific targets
        targetIds.forEach(id => {
          if (data.targets[id]) {
            this.targetLookupCache.set(id.toString(), cacheEntry);
          }
        });
      } else {
        // Cache all targets
        Object.keys(data.targets).forEach(id => {
          this.targetLookupCache.set(id, cacheEntry);
        });
      }

      return data.targets;
    } catch (error) {
      console.error('Error fetching target lookups:', error);
      // Return empty object on error so enrichment can continue
      return {};
    }
  }

  /**
   * Get user display name from cache or fetch if needed
   */
  async getUserDisplayName(userId) {
    if (!userId) return 'System';

    // Check cache first
    const cached = this.userLookupCache.get(userId);
    if (cached && (Date.now() - cached.timestamp) < this.cacheExpiry) {
      return cached.data.display_name || `User ${userId}`;
    }

    // Fetch from API
    try {
      const users = await this.fetchUserLookups([userId]);
      if (users[userId]) {
        return users[userId].display_name;
      }
    } catch (error) {
      console.error('Error getting user display name:', error);
    }

    return `User ${userId}`;
  }

  /**
   * Get target display name from cache or fetch if needed
   */
  async getTargetDisplayName(targetId) {
    if (!targetId) return 'Unknown Target';

    // Check cache first
    const cached = this.targetLookupCache.get(targetId.toString());
    if (cached && (Date.now() - cached.timestamp) < this.cacheExpiry) {
      return cached.data.display_name || `Target ${targetId}`;
    }

    // Fetch from API
    try {
      const targets = await this.fetchTargetLookups([targetId]);
      if (targets[targetId]) {
        return targets[targetId].display_name;
      }
    } catch (error) {
      console.error('Error getting target display name:', error);
    }

    return `Target ${targetId}`;
  }

  /**
   * Enrich audit events with user and target names
   */
  async enrichAuditEvents(events) {
    if (!events || events.length === 0) return events;

    // Collect unique user IDs and target IDs
    const userIds = new Set();
    const targetIds = new Set();

    events.forEach(event => {
      if (event.user_id) {
        userIds.add(event.user_id);
      }
      if (event.resource_type === 'target' && event.resource_id) {
        targetIds.add(event.resource_id);
      }
    });

    // Fetch lookup data in bulk
    const [users, targets] = await Promise.all([
      userIds.size > 0 ? this.fetchUserLookups(Array.from(userIds)) : Promise.resolve({}),
      targetIds.size > 0 ? this.fetchTargetLookups(Array.from(targetIds)) : Promise.resolve({})
    ]);

    // Enrich events
    const enrichedEvents = events.map(event => ({
      ...event,
      user_display_name: event.user_id && users[event.user_id] 
        ? users[event.user_id].display_name 
        : (event.user_id ? `User ${event.user_id}` : 'System'),
      resource_display_name: event.resource_type === 'target' && event.resource_id && targets[event.resource_id]
        ? targets[event.resource_id].display_name
        : `${event.resource_type}:${event.resource_id}`
    }));

    return enrichedEvents;
  }

  /**
   * Get enriched user display for table cell
   */
  getEnrichedUserDisplay(event) {
    if (!event.user_id) return 'System';
    
    if (event.user_display_name && event.user_display_name !== `User ${event.user_id}`) {
      return `${event.user_display_name} (${event.user_id})`;
    }
    
    return event.user_id.toString();
  }

  /**
   * Get enriched resource display for table cell
   */
  getEnrichedResourceDisplay(event) {
    const baseDisplay = `${event.resource_type}:${event.resource_id}`;
    
    if (event.resource_display_name && event.resource_display_name !== baseDisplay) {
      return `${event.resource_display_name} (${baseDisplay})`;
    }
    
    return baseDisplay;
  }

  /**
   * Clear lookup caches
   */
  clearCache() {
    this.userLookupCache.clear();
    this.targetLookupCache.clear();
  }

  /**
   * Preload lookup data for better performance
   */
  async preloadLookupData() {
    try {
      await Promise.all([
        this.fetchUserLookups(),
        this.fetchTargetLookups()
      ]);
      console.log('Audit lookup data preloaded successfully');
    } catch (error) {
      console.error('Error preloading lookup data:', error);
    }
  }
}

// Create singleton instance
const auditService = new AuditService();

export default auditService;