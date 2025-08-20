// Test data configuration for E2E tests
export const testData = {
  admin: {
    username: 'admin',
    password: 'admin123'
  },
  
  testUser: {
    username: 'testuser' + Date.now(),
    password: 'testpass123',
    email: 'test@example.com',
    fullName: 'Test User'
  },
  
  testTarget: {
    name: 'TestTarget' + Date.now(),
    host: '192.168.1.100',
    port: '22',
    username: 'root',
    password: 'password123',
    type: 'SSH'
  },
  
  testJob: {
    name: 'TestJob' + Date.now(),
    description: 'Test job for comprehensive testing',
    type: 'System',
    action: 'ping'
  },
  
  networkDiscovery: {
    range: '192.168.1.0/24',
    timeout: 30000
  },
  
  scheduleTest: {
    type: 'cron',
    cronExpression: '0 0 * * *',
    interval: '3600'
  }
};

export const urls = {
  login: '/',
  dashboard: '/dashboard',
  targets: '/targets',
  jobs: '/jobs',
  users: '/users',
  systemSettings: '/system-settings',
  notifications: '/notifications',
  systemHealth: '/system-health',

  celeryMonitor: '/celery-monitor',
  audit: '/audit'
};

export const testTimeouts = {
  short: 5000,
  medium: 10000,
  long: 30000,
  veryLong: 60000
};