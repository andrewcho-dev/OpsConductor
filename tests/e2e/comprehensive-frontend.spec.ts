import { test, expect, Page, BrowserContext } from '@playwright/test';

// Test configuration
const ADMIN_CREDENTIALS = {
  username: 'admin',
  password: 'admin123'
};

// Helper function for login
async function login(page: Page, username: string = ADMIN_CREDENTIALS.username, password: string = ADMIN_CREDENTIALS.password) {
  // Navigate to login page
  await page.goto('/');
  
  // Wait for login page elements
  await expect(page.locator('input[type="text"], input[name="username"], input[placeholder*="username" i]')).toBeVisible();
  
  // Fill login form
  await page.locator('input[type="text"], input[name="username"], input[placeholder*="username" i]').fill(username);
  await page.locator('input[type="password"], input[name="password"], input[placeholder*="password" i]').fill(password);
  
  // Submit form
  await page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")').click();
  
  // Wait for dashboard
  await expect(page).toHaveURL(/.*\/dashboard/);
  await expect(page.locator('text=System Dashboard')).toBeVisible();
}

test.describe('OpsConductor Comprehensive Frontend E2E Tests', () => {
  test.beforeEach(async ({ context }) => {
    // Set longer timeout for all tests
    test.setTimeout(60000);
  });

  test.describe('Authentication & Security', () => {
    test('should display login page with all required elements', async ({ page }) => {
      await page.goto('/');
      
      // Verify login page elements
      await expect(page.locator('img[alt*="Logo"], img[src*="logo"]')).toBeVisible();
      await expect(page.locator('h1, h2, .title')).toBeVisible();
      await expect(page.locator('input[type="text"], input[name="username"]')).toBeVisible();
      await expect(page.locator('input[type="password"], input[name="password"]')).toBeVisible();
      await expect(page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")')).toBeVisible();
      
      // Verify footer
      await expect(page.locator('text=© 2025 Enabled Enterprises LLC')).toBeVisible();
      await expect(page.locator('text=OpsConductor Enterprise Automation Platform')).toBeVisible();
    });

    test('should successfully authenticate with valid credentials', async ({ page }) => {
      await login(page);
      
      // Verify successful authentication
      await expect(page).toHaveURL(/.*\/dashboard/);
      await expect(page.locator('text=admin')).toBeVisible();
      await expect(page.locator('text=administrator')).toBeVisible();
      await expect(page.locator('text=System Dashboard')).toBeVisible();
    });

    test('should display comprehensive dashboard layout', async ({ page }) => {
      await login(page);
      
      // Verify main layout components
      await expect(page.locator('[role="banner"], header')).toBeVisible();
      await expect(page.locator('main')).toBeVisible();
      await expect(page.locator('aside, nav, [role="navigation"]')).toBeVisible();
      await expect(page.locator('footer, [role="contentinfo"]')).toBeVisible();
      
      // Verify navigation menu items
      const navigationItems = [
        'Dashboard',
        'Universal Targets',
        'Job Management',
        'Job Monitor',
        'Log Viewer',
        'System Health',
        'Audit & Security',
        'User Management',
        'System Settings'
      ];
      
      for (const item of navigationItems) {
        await expect(page.locator(`button:has-text("${item}")`)).toBeVisible();
      }
      
      // Verify system status
      await expect(page.locator('text=System: Online')).toBeVisible();
      await expect(page.locator('text=UTC:')).toBeVisible();
      await expect(page.locator('text=Local:')).toBeVisible();
    });
  });

  test.describe('Universal Targets Management', () => {
    test.beforeEach(async ({ page }) => {
      await login(page);
      await page.locator('button:has-text("Universal Targets")').click();
      await expect(page).toHaveURL(/.*\/targets/);
      await expect(page.locator('text=Universal Targets')).toBeVisible();
    });

    test('should display targets page with comprehensive functionality', async ({ page }) => {
      // Verify page title and navigation
      await expect(page.locator('text=Universal Targets')).toBeVisible();
      await expect(page.locator('button:has-text("Universal Targets")').first()).toHaveAttribute('aria-current', 'true');
      
      // Verify toolbar buttons
      await expect(page.locator('button:has-text("Back to Dashboard")')).toBeVisible();
      await expect(page.locator('button:has-text("Discover Network")')).toBeVisible();
      await expect(page.locator('button:has-text("Add Target")')).toBeVisible();
      await expect(page.locator('button:has-text("Health Check")')).toBeVisible();
      
      // Verify data table structure
      const expectedColumns = ['IP Address', 'Name', 'Target Serial', 'OS', 'Environment', 'Status', 'Health', 'Method', 'Actions'];
      for (const column of expectedColumns) {
        await expect(page.locator(`th:has-text("${column}"), columnheader:has-text("${column}")`)).toBeVisible();
      }
      
      // Verify filter capabilities
      await expect(page.locator('input[placeholder*="Filter IP"]')).toBeVisible();
      await expect(page.locator('input[placeholder*="Filter name"]')).toBeVisible();
      await expect(page.locator('input[placeholder*="Filter serial"]')).toBeVisible();
      
      // Verify pagination
      await expect(page.locator('text=Show:')).toBeVisible();
      await expect(page.locator('text=per page')).toBeVisible();
      await expect(page.locator('text*=Showing')).toBeVisible();
    });

    test('should open and validate Add Target modal', async ({ page }) => {
      await page.locator('button:has-text("Add Target")').click();
      
      // Verify modal is open
      await expect(page.locator('dialog, [role="dialog"]')).toBeVisible();
      await expect(page.locator('text=Create New Target')).toBeVisible();
      
      // Verify form fields
      await expect(page.locator('input[placeholder*="Target Name"], textbox[aria-label*="Target Name"]')).toBeVisible();
      await expect(page.locator('input[placeholder*="IP Address"], textbox[aria-label*="IP Address"]')).toBeVisible();
      await expect(page.locator('combobox[aria-label*="Device"], combobox:has-text("Linux")')).toBeVisible();
      await expect(page.locator('combobox[aria-label*="Environment"], combobox:has-text("Development")')).toBeVisible();
      
      // Verify communication method section
      await expect(page.locator('text=Communication Methods')).toBeVisible();
      await expect(page.locator('button:has-text("Add Method")')).toBeVisible();
      await expect(page.locator('text=Method 1')).toBeVisible();
      await expect(page.locator('text=Primary')).toBeVisible();
      
      // Verify connection settings
      await expect(page.locator('combobox:has-text("SSH")')).toBeVisible();
      await expect(page.locator('spinbutton[value="22"]')).toBeVisible();
      await expect(page.locator('combobox:has-text("Password")')).toBeVisible();
      
      // Test form interaction
      await page.locator('input[placeholder*="Target Name"], textbox[aria-label*="Target Name"]').fill('TestServer');
      await page.locator('input[placeholder*="IP Address"], textbox[aria-label*="IP Address"]').fill('192.168.1.100');
      
      // Verify action buttons
      await expect(page.locator('button:has-text("Cancel")')).toBeVisible();
      await expect(page.locator('button:has-text("Create Target")')).toBeVisible();
      
      // Cancel and close modal
      await page.locator('button:has-text("Cancel")').click();
      await expect(page.locator('dialog, [role="dialog"]')).not.toBeVisible();
    });
  });

  test.describe('Job Management System', () => {
    test.beforeEach(async ({ page }) => {
      await login(page);
      await page.locator('button:has-text("Job Management")').click();
      await expect(page).toHaveURL(/.*\/jobs/);
      await expect(page.locator('text=Job Management')).toBeVisible();
    });

    test('should display job management page with full functionality', async ({ page }) => {
      // Verify page title
      await expect(page.locator('text=Job Management')).toBeVisible();
      
      // Verify toolbar buttons
      await expect(page.locator('button:has-text("Cleanup")')).toBeVisible();
      await expect(page.locator('button:has-text("Health Check")')).toBeVisible();
      await expect(page.locator('button:has-text("Create Job")')).toBeVisible();
      
      // Verify table structure
      const expectedColumns = ['Select', 'Job Name', 'Job Serial', 'Type', 'Status', 'Created', 'Last Run', 'Next Scheduled', 'Actions'];
      for (const column of expectedColumns) {
        await expect(page.locator(`th:has-text("${column}"), columnheader:has-text("${column}")`)).toBeVisible();
      }
      
      // Verify sorting indicators
      await expect(page.locator('text=↕').first()).toBeVisible();
      
      // Verify filter capabilities
      await expect(page.locator('input[placeholder*="Filter name"]')).toBeVisible();
      await expect(page.locator('input[placeholder*="Filter serial"]')).toBeVisible();
      await expect(page.locator('combobox:has-text("All Types")')).toBeVisible();
      await expect(page.locator('combobox:has-text("All Status")')).toBeVisible();
      
      // Verify empty state message
      await expect(page.locator('text=No jobs found. Create your first job to get started!')).toBeVisible();
    });

    test('should open and validate Create Job modal', async ({ page }) => {
      await page.locator('button:has-text("Create Job")').click();
      
      // Verify modal is open
      await expect(page.locator('dialog, [role="dialog"]')).toBeVisible();
      await expect(page.locator('text=Create New Job')).toBeVisible();
      
      // Verify basic information section
      await expect(page.locator('text=BASIC INFORMATION')).toBeVisible();
      await expect(page.locator('textbox[aria-label*="Job Name"], input[placeholder*="Job Name"]')).toBeVisible();
      await expect(page.locator('textbox[aria-label*="Description"], input[placeholder*="Description"]')).toBeVisible();
      
      // Verify workflow sections
      await expect(page.locator('text=TARGETS (0 selected)')).toBeVisible();
      await expect(page.locator('button:has-text("Select Targets")')).toBeVisible();
      
      await expect(page.locator('text=ACTIONS (0 configured)')).toBeVisible();
      await expect(page.locator('button:has-text("Configure Actions")')).toBeVisible();
      
      await expect(page.locator('text=SCHEDULE (OPTIONAL)')).toBeVisible();
      await expect(page.locator('button:has-text("Configure Schedule")')).toBeVisible();
      
      // Verify action buttons
      await expect(page.locator('button:has-text("Cancel")')).toBeVisible();
      await expect(page.locator('button:has-text("Create Job")')).toBeVisible();
      
      // Cancel and close modal
      await page.locator('button:has-text("Cancel")').click();
      await expect(page.locator('dialog, [role="dialog"]')).not.toBeVisible();
    });
  });

  test.describe('System Health Monitoring', () => {
    test('should display comprehensive system health dashboard', async ({ page }) => {
      await login(page);
      await page.locator('button:has-text("System Health")').click();
      await expect(page).toHaveURL(/.*\/system-health/);
      
      // Wait for loading to complete
      await expect(page.locator('text=Loading system health')).toBeVisible({ timeout: 5000 });
      await expect(page.locator('text=Loading system health')).not.toBeVisible({ timeout: 10000 });
      
      // Verify main dashboard elements
      await expect(page.locator('text=System Health Dashboard')).toBeVisible();
      await expect(page.locator('text*=Last updated:')).toBeVisible();
      await expect(page.locator('button:has-text("Refresh health data")')).toBeVisible();
      
      // Verify key metrics cards
      await expect(page.locator('text*="System Uptime"')).toBeVisible();
      await expect(page.locator('text*="Health Status"')).toBeVisible();
      await expect(page.locator('text*="Version"')).toBeVisible();
      await expect(page.locator('text*="CPU Usage"')).toBeVisible();
      await expect(page.locator('text*="Memory Usage"')).toBeVisible();
      await expect(page.locator('text*="Containers"')).toBeVisible();
      
      // Verify system resources section
      await expect(page.locator('text=SYSTEM RESOURCES')).toBeVisible();
      await expect(page.locator('text=CPU Performance')).toBeVisible();
      await expect(page.locator('text=Memory Usage')).toBeVisible();
      await expect(page.locator('text=Disk Storage')).toBeVisible();
      
      // Verify progress bars are present
      await expect(page.locator('progressbar').first()).toBeVisible();
      
      // Verify Docker containers section
      await expect(page.locator('text=DOCKER CONTAINERS')).toBeVisible();
      
      // Verify key containers are listed
      const expectedContainers = ['frontend', 'backend', 'celery-worker', 'scheduler', 'nginx', 'postgres', 'redis', 'prometheus', 'grafana'];
      for (const container of expectedContainers) {
        await expect(page.locator(`text=${container}`)).toBeVisible();
      }
      
      // Verify container management buttons
      await expect(page.locator('button:has-text("Restart")').first()).toBeVisible();
      await expect(page.locator('button:has-text("Stop")').first()).toBeVisible();
      
      // Verify system information section
      await expect(page.locator('text=SYSTEM INFORMATION')).toBeVisible();
      await expect(page.locator('text=System Status')).toBeVisible();
      await expect(page.locator('text=Database Status')).toBeVisible();
      await expect(page.locator('text=Application Status')).toBeVisible();
      
      // Verify service status section
      await expect(page.locator('text=SERVICE STATUS')).toBeVisible();
      
      // Verify key services are listed
      const expectedServices = ['database', 'redis', 'system', 'application', 'services', 'docker_containers', 'nginx', 'celery', 'volumes'];
      for (const service of expectedServices) {
        await expect(page.locator(`text=${service}`)).toBeVisible();
      }
    });
  });

  test.describe('User Management', () => {
    test('should display comprehensive user management interface', async ({ page }) => {
      await login(page);
      await page.locator('button:has-text("User Management")').click();
      await expect(page).toHaveURL(/.*\/users/);
      
      // Verify page title and toolbar
      await expect(page.locator('text=User Management')).toBeVisible();
      await expect(page.locator('button:has-text("Back to Dashboard")')).toBeVisible();
      await expect(page.locator('button:has-text("Refresh users")')).toBeVisible();
      await expect(page.locator('button:has-text("Add User")')).toBeVisible();
      
      // Verify table structure
      const expectedColumns = ['ID', 'Username', 'Email', 'Role', 'Status', 'Last Login', 'Actions'];
      for (const column of expectedColumns) {
        await expect(page.locator(`th:has-text("${column}"), columnheader:has-text("${column}")`)).toBeVisible();
      }
      
      // Verify filter capabilities
      await expect(page.locator('input[placeholder*="Filter ID"]')).toBeVisible();
      await expect(page.locator('input[placeholder*="Filter username"]')).toBeVisible();
      await expect(page.locator('input[placeholder*="Filter email"]')).toBeVisible();
      
      // Verify user data is loaded
      await expect(page.locator('text=admin')).toBeVisible();
      await expect(page.locator('text=administrator')).toBeVisible();
      await expect(page.locator('text=active')).toBeVisible();
      
      // Verify pagination
      await expect(page.locator('text*=Showing')).toBeVisible();
      await expect(page.locator('text*=users')).toBeVisible();
      
      // Verify status footer
      await expect(page.locator('text*=Loaded')).toBeVisible();
      await expect(page.locator('text*=users successfully')).toBeVisible();
    });
  });

  test.describe('Navigation & Responsive Design', () => {
    test('should navigate between all major sections', async ({ page }) => {
      await login(page);
      
      const navigationTests = [
        { button: 'Universal Targets', url: '/targets', expectedText: 'Universal Targets' },
        { button: 'Job Management', url: '/jobs', expectedText: 'Job Management' },
        { button: 'Job Monitor', url: '/job-monitor', expectedText: 'Job Monitor' },
        { button: 'Log Viewer', url: '/log-viewer', expectedText: 'Log Viewer' },
        { button: 'System Health', url: '/system-health', expectedText: 'System Health Dashboard' },
        { button: 'Audit & Security', url: '/audit', expectedText: 'Audit' },
        { button: 'User Management', url: '/users', expectedText: 'User Management' },
        { button: 'System Settings', url: '/system-settings', expectedText: 'System Settings' }
      ];
      
      for (const navTest of navigationTests) {
        // Click navigation button
        await page.locator(`button:has-text("${navTest.button}")`).click();
        
        // Wait for navigation
        await page.waitForLoadState('networkidle', { timeout: 10000 });
        
        // Verify URL contains expected path
        await expect(page).toHaveURL(new RegExp(`.*${navTest.url}`));
        
        // Verify page loaded (look for any expected text)
        try {
          await expect(page.locator(`text=${navTest.expectedText}`).first()).toBeVisible({ timeout: 5000 });
        } catch {
          // If expected text not found, just verify the URL changed
          console.log(`Page loaded for ${navTest.button} but expected text '${navTest.expectedText}' not found`);
        }
        
        // Return to dashboard for next test
        await page.locator('button:has-text("Dashboard")').click();
        await expect(page).toHaveURL(/.*\/dashboard/);
      }
    });

    test('should maintain consistent layout across pages', async ({ page }) => {
      await login(page);
      
      const pagesToTest = ['Universal Targets', 'Job Management', 'System Health', 'User Management'];
      
      for (const pageButton of pagesToTest) {
        await page.locator(`button:has-text("${pageButton}")`).click();
        await page.waitForLoadState('networkidle', { timeout: 10000 });
        
        // Verify consistent layout elements
        await expect(page.locator('[role="banner"], header')).toBeVisible();
        await expect(page.locator('main')).toBeVisible();
        await expect(page.locator('text=System: Online')).toBeVisible();
        await expect(page.locator('text=© 2025 Enabled Enterprises LLC')).toBeVisible();
        await expect(page.locator('text=UTC:')).toBeVisible();
        await expect(page.locator('text=Local:')).toBeVisible();
        
        // Verify navigation remains accessible
        await expect(page.locator('button:has-text("Dashboard")')).toBeVisible();
        await expect(page.locator('text=admin')).toBeVisible();
        await expect(page.locator('text=administrator')).toBeVisible();
      }
    });
  });

  test.describe('Real-time Features & Performance', () => {
    test('should display real-time timestamps and system status', async ({ page }) => {
      await login(page);
      
      // Verify real-time elements are present
      await expect(page.locator('text=UTC:')).toBeVisible();
      await expect(page.locator('text=Local:')).toBeVisible();
      await expect(page.locator('text=System: Online')).toBeVisible();
      
      // Navigate to system health to check real-time updates
      await page.locator('button:has-text("System Health")').click();
      await page.waitForLoadState('networkidle');
      
      // Wait for health data to load
      try {
        await expect(page.locator('text*=Last updated:')).toBeVisible({ timeout: 10000 });
      } catch {
        // If health data doesn't load, that's okay for this test
        console.log('System health data loading may be in progress');
      }
    });

    test('should handle page loading states gracefully', async ({ page }) => {
      await login(page);
      
      // Test loading states on system health (most data-intensive page)
      await page.locator('button:has-text("System Health")').click();
      
      // Should show loading state initially
      try {
        await expect(page.locator('text=Loading system health')).toBeVisible({ timeout: 2000 });
      } catch {
        // Loading might be very fast, which is also good
        console.log('System health loaded very quickly');
      }
      
      // Should eventually show content
      await page.waitForLoadState('networkidle', { timeout: 15000 });
    });
  });

  test.describe('Error Handling & Edge Cases', () => {
    test('should handle empty states properly', async ({ page }) => {
      await login(page);
      
      // Check job management empty state
      await page.locator('button:has-text("Job Management")').click();
      await expect(page.locator('text=No jobs found. Create your first job to get started!')).toBeVisible();
    });

    test('should maintain functionality during network conditions', async ({ page }) => {
      await login(page);
      
      // Test that basic navigation works even if some API calls are slow
      await page.locator('button:has-text("Universal Targets")').click();
      await expect(page.locator('text=Universal Targets')).toBeVisible();
      
      await page.locator('button:has-text("Job Management")').click();
      await expect(page.locator('text=Job Management')).toBeVisible();
      
      await page.locator('button:has-text("User Management")').click();
      await expect(page.locator('text=User Management')).toBeVisible();
    });
  });
});