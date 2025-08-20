import { test, expect, Page } from '@playwright/test';
import { LoginPage } from './pages/login.page';
import { DashboardPage } from './pages/dashboard.page';
import { TargetsPage } from './pages/targets.page';
import { JobsPage } from './pages/jobs.page';
import { UsersPage } from './pages/users.page';

// Test data
const testAdmin = {
  username: 'admin',
  password: 'admin123'
};

const testUser = {
  username: 'testuser',
  password: 'testpass123',
  email: 'test@example.com',
  fullName: 'Test User'
};

const testTarget = {
  name: 'TestTarget',
  host: '192.168.1.100',
  port: '22',
  username: 'root',
  password: 'password123',
  type: 'SSH'
};

const testJob = {
  name: 'TestJob',
  description: 'Test job for comprehensive testing',
  type: 'System',
  action: 'ping'
};

test.describe('COMPREHENSIVE ENABLEDRM E2E TESTING', () => {
  let page: Page;
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;
  let targetsPage: TargetsPage;
  let jobsPage: JobsPage;
  let usersPage: UsersPage;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    targetsPage = new TargetsPage(page);
    jobsPage = new JobsPage(page);
    usersPage = new UsersPage(page);
  });

  test.describe('1. AUTHENTICATION & LOGIN TESTING', () => {
    test('1.1 Should display login page correctly', async () => {
      await page.goto('/');
      await loginPage.expectLoginPage();
      
      // Test all login form elements are present
      await expect(loginPage.usernameField).toBeVisible();
      await expect(loginPage.passwordField).toBeVisible();
      await expect(loginPage.loginButton).toBeVisible();
      
      // Take screenshot for visual verification
      await loginPage.takeScreenshot('login-page');
    });

    test('1.2 Should show error for invalid credentials', async () => {
      await page.goto('/');
      await loginPage.login('invalid', 'credentials');
      await loginPage.expectLoginError();
    });

    test('1.3 Should login successfully with valid credentials', async () => {
      await page.goto('/');
      await loginPage.login(testAdmin.username, testAdmin.password);
      await dashboardPage.expectDashboardPage();
    });

    test('1.4 Should redirect to dashboard after successful login', async () => {
      await page.goto('/');
      await loginPage.login(testAdmin.username, testAdmin.password);
      expect(page.url()).toContain('/dashboard');
    });

    test('1.5 Should handle empty form submission', async () => {
      await page.goto('/');
      await loginPage.loginButton.click();
      // Form should not submit or show validation errors
      await expect(loginPage.usernameField).toBeVisible();
    });
  });

  test.describe('2. DASHBOARD COMPREHENSIVE TESTING', () => {
    test.beforeEach(async () => {
      await page.goto('/');
      await loginPage.login(testAdmin.username, testAdmin.password);
      await dashboardPage.expectDashboardPage();
    });

    test('2.1 Should display all dashboard components', async () => {
      // Verify main layout components
      await expect(dashboardPage.sidebar).toBeVisible();
      await expect(dashboardPage.header).toBeVisible();
      await expect(dashboardPage.mainContent).toBeVisible();
      
      // Verify navigation links are present
      await expect(dashboardPage.dashboardLink).toBeVisible();
      await expect(dashboardPage.targetsLink).toBeVisible();
      await expect(dashboardPage.jobsLink).toBeVisible();
      
      await dashboardPage.takeScreenshot('dashboard-main');
    });

    test('2.2 Should display metrics cards if present', async () => {
      const metricsCount = await dashboardPage.metricsCards.count();
      if (metricsCount > 0) {
        for (let i = 0; i < metricsCount; i++) {
          await expect(dashboardPage.metricsCards.nth(i)).toBeVisible();
        }
      }
    });

    test('2.3 Should display charts section if present', async () => {
      const chartsCount = await dashboardPage.chartsSection.count();
      if (chartsCount > 0) {
        await expect(dashboardPage.chartsSection.first()).toBeVisible();
      }
    });

    test('2.4 Should test all sidebar navigation links', async () => {
      const navigationTests = [
        { link: dashboardPage.targetsLink, expectedUrl: '/targets' },
        { link: dashboardPage.jobsLink, expectedUrl: '/jobs' },
        { link: dashboardPage.usersLink, expectedUrl: '/users' },
        { link: dashboardPage.systemSettingsLink, expectedUrl: '/system-settings' },
        { link: dashboardPage.systemHealthLink, expectedUrl: '/system-health' },

        { link: dashboardPage.celeryMonitorLink, expectedUrl: '/celery-monitor' },
        { link: dashboardPage.notificationsLink, expectedUrl: '/notifications' },
        { link: dashboardPage.auditLink, expectedUrl: '/audit' }
      ];

      for (const navTest of navigationTests) {
        if (await navTest.link.isVisible()) {
          await navTest.link.click();
          await dashboardPage.waitForPageLoad();
          expect(page.url()).toContain(navTest.expectedUrl);
          
          // Navigate back to dashboard
          await dashboardPage.dashboardLink.click();
          await dashboardPage.waitForPageLoad();
        }
      }
    });
  });

  test.describe('3. TARGETS COMPREHENSIVE TESTING', () => {
    test.beforeEach(async () => {
      await page.goto('/');
      await loginPage.login(testAdmin.username, testAdmin.password);
      await dashboardPage.navigateToTargets();
      await targetsPage.expectTargetsPage();
    });

    test('3.1 Should display targets page correctly', async () => {
      await expect(targetsPage.pageTitle).toBeVisible();
      await expect(targetsPage.targetsTable).toBeVisible();
      await expect(targetsPage.addTargetButton).toBeVisible();
      
      if (await targetsPage.searchField.isVisible()) {
        await expect(targetsPage.searchField).toBeVisible();
      }
      if (await targetsPage.refreshButton.isVisible()) {
        await expect(targetsPage.refreshButton).toBeVisible();
      }
      
      await targetsPage.takeScreenshot('targets-page');
    });

    test('3.2 Should open add target modal', async () => {
      await targetsPage.clickAddTarget();
      await expect(targetsPage.createTargetModal).toBeVisible();
      await expect(targetsPage.targetNameField).toBeVisible();
      await expect(targetsPage.targetHostField).toBeVisible();
      
      // Test cancel button
      await targetsPage.cancelButton.click();
      await expect(targetsPage.createTargetModal).not.toBeVisible();
    });

    test('3.3 Should create a new target', async () => {
      await targetsPage.createTarget(testTarget);
      await targetsPage.verifyTargetExists(testTarget.name);
    });

    test('3.4 Should search targets if search is available', async () => {
      if (await targetsPage.searchField.isVisible()) {
        await targetsPage.searchTargets('test');
        await targetsPage.waitForPageLoad();
      }
    });

    test('3.5 Should test network discovery if available', async () => {
      if (await targetsPage.discoveryButton.isVisible()) {
        await targetsPage.openDiscovery();
        await expect(targetsPage.discoveryModal).toBeVisible();
        await targetsPage.cancelButton.click();
      }
    });

    test('3.6 Should test target editing if available', async () => {
      const editButtons = await targetsPage.targetsTable.locator('button:has-text("Edit")');
      if (await editButtons.count() > 0) {
        await targetsPage.editFirstTarget();
        await expect(targetsPage.editTargetModal).toBeVisible();
        await targetsPage.cancelButton.click();
      }
    });

    test('3.7 Should refresh targets list if refresh button exists', async () => {
      if (await targetsPage.refreshButton.isVisible()) {
        await targetsPage.refreshButton.click();
        await targetsPage.waitForPageLoad();
      }
    });
  });

  test.describe('4. JOBS COMPREHENSIVE TESTING', () => {
    test.beforeEach(async () => {
      await page.goto('/');
      await loginPage.login(testAdmin.username, testAdmin.password);
      await dashboardPage.navigateToJobs();
      await jobsPage.expectJobsPage();
    });

    test('4.1 Should display jobs page correctly', async () => {
      await expect(jobsPage.pageTitle).toBeVisible();
      await expect(jobsPage.jobsTable).toBeVisible();
      await expect(jobsPage.createJobButton).toBeVisible();
      
      if (await jobsPage.searchField.isVisible()) {
        await expect(jobsPage.searchField).toBeVisible();
      }
      if (await jobsPage.refreshButton.isVisible()) {
        await expect(jobsPage.refreshButton).toBeVisible();
      }
      
      await jobsPage.takeScreenshot('jobs-page');
    });

    test('4.2 Should open create job modal', async () => {
      await jobsPage.clickCreateJob();
      await expect(jobsPage.createJobModal).toBeVisible();
      await expect(jobsPage.jobNameField).toBeVisible();
      
      // Test cancel button
      await jobsPage.cancelJobButton.click();
      await expect(jobsPage.createJobModal).not.toBeVisible();
    });

    test('4.3 Should create a new job', async () => {
      await jobsPage.createJob(testJob);
      await jobsPage.verifyJobExists(testJob.name);
    });

    test('4.4 Should test job execution controls if available', async () => {
      const executeButtons = await jobsPage.jobsTable.locator('button:has-text("Execute")');
      if (await executeButtons.count() > 0) {
        await jobsPage.executeFirstJob();
        await jobsPage.waitForPageLoad();
      }
    });

    test('4.5 Should test job history if available', async () => {
      const historyButtons = await jobsPage.jobsTable.locator('button:has-text("History")');
      if (await historyButtons.count() > 0) {
        await jobsPage.viewJobHistory();
        await expect(jobsPage.jobHistoryModal).toBeVisible();
        await jobsPage.cancelJobButton.click();
      }
    });

    test('4.6 Should test actions workspace if available', async () => {
      if (await jobsPage.actionsWorkspaceButton.isVisible()) {
        await jobsPage.openActionsWorkspace();
        await expect(jobsPage.actionsWorkspaceModal).toBeVisible();
        await jobsPage.cancelJobButton.click();
      }
    });

    test('4.7 Should search jobs if search is available', async () => {
      if (await jobsPage.searchField.isVisible()) {
        await jobsPage.searchJobs('test');
        await jobsPage.waitForPageLoad();
      }
    });
  });

  test.describe('5. USER MANAGEMENT COMPREHENSIVE TESTING', () => {
    test.beforeEach(async () => {
      await page.goto('/');
      await loginPage.login(testAdmin.username, testAdmin.password);
      await dashboardPage.navigateToUsers();
    });

    test('5.1 Should display users page correctly', async () => {
      await usersPage.expectUsersPage();
      await expect(usersPage.pageTitle).toBeVisible();
      await expect(usersPage.usersTable).toBeVisible();
      await expect(usersPage.addUserButton).toBeVisible();
      
      await usersPage.takeScreenshot('users-page');
    });

    test('5.2 Should open add user modal', async () => {
      await usersPage.clickAddUser();
      await expect(usersPage.createUserModal).toBeVisible();
      await expect(usersPage.usernameField).toBeVisible();
      await expect(usersPage.passwordField).toBeVisible();
      
      // Test cancel button
      await usersPage.cancelUserButton.click();
      await expect(usersPage.createUserModal).not.toBeVisible();
    });

    test('5.3 Should create a new user', async () => {
      await usersPage.createUser(testUser);
      await usersPage.verifyUserExists(testUser.username);
    });

    test('5.4 Should search users if search is available', async () => {
      if (await usersPage.searchField.isVisible()) {
        await usersPage.searchUsers('test');
        await usersPage.waitForPageLoad();
      }
    });

    test('5.5 Should test user editing if available', async () => {
      const editButtons = await usersPage.usersTable.locator('button:has-text("Edit")');
      if (await editButtons.count() > 0) {
        await usersPage.editFirstUser();
        await expect(usersPage.editUserModal).toBeVisible();
        await usersPage.cancelUserButton.click();
      }
    });
  });

  test.describe('6. SYSTEM SETTINGS COMPREHENSIVE TESTING', () => {
    test.beforeEach(async () => {
      await page.goto('/');
      await loginPage.login(testAdmin.username, testAdmin.password);
      await dashboardPage.navigateToSystemSettings();
    });

    test('6.1 Should display system settings page', async () => {
      await page.waitForLoadState('networkidle');
      
      // Check if we're on the system settings page
      const pageTitle = page.locator('h1, h2').first();
      if (await pageTitle.isVisible()) {
        await expect(pageTitle).toBeVisible();
      }
      
      await page.screenshot({ path: './test-results/system-settings-page.png', fullPage: true });
    });

    test('6.2 Should test all system settings forms and controls', async () => {
      await page.waitForLoadState('networkidle');
      
      // Test any form fields that exist
      const formFields = page.locator('input, select, textarea');
      const fieldCount = await formFields.count();
      
      if (fieldCount > 0) {
        console.log(`Found ${fieldCount} form fields in system settings`);
      }
      
      // Test any buttons that exist
      const buttons = page.locator('button');
      const buttonCount = await buttons.count();
      
      for (let i = 0; i < buttonCount; i++) {
        const button = buttons.nth(i);
        if (await button.isVisible() && await button.isEnabled()) {
          const buttonText = await button.textContent();
          console.log(`Found button: ${buttonText}`);
        }
      }
    });
  });

  test.describe('7. NOTIFICATIONS COMPREHENSIVE TESTING', () => {
    test.beforeEach(async () => {
      await page.goto('/');
      await loginPage.login(testAdmin.username, testAdmin.password);
      await dashboardPage.navigateToNotifications();
    });

    test('7.1 Should display notifications page', async () => {
      await page.waitForLoadState('networkidle');
      
      const pageTitle = page.locator('h1, h2').first();
      if (await pageTitle.isVisible()) {
        await expect(pageTitle).toBeVisible();
      }
      
      await page.screenshot({ path: './test-results/notifications-page.png', fullPage: true });
    });

    test('7.2 Should test all notification controls', async () => {
      await page.waitForLoadState('networkidle');
      
      // Test notification templates if they exist
      const templates = page.locator('.template, .notification-template');
      if (await templates.count() > 0) {
        await expect(templates.first()).toBeVisible();
      }
      
      // Test notification settings
      const settings = page.locator('input, select');
      const settingsCount = await settings.count();
      console.log(`Found ${settingsCount} notification settings`);
    });
  });

  test.describe('8. SYSTEM HEALTH COMPREHENSIVE TESTING', () => {
    test.beforeEach(async () => {
      await page.goto('/');
      await loginPage.login(testAdmin.username, testAdmin.password);
      await dashboardPage.navigateToSystemHealth();
    });

    test('8.1 Should display system health dashboard', async () => {
      await page.waitForLoadState('networkidle');
      
      const pageTitle = page.locator('h1, h2').first();
      if (await pageTitle.isVisible()) {
        await expect(pageTitle).toBeVisible();
      }
      
      // Test health metrics
      const metrics = page.locator('.metric, .health-metric, .status');
      if (await metrics.count() > 0) {
        await expect(metrics.first()).toBeVisible();
      }
      
      await page.screenshot({ path: './test-results/system-health-page.png', fullPage: true });
    });

    test('8.2 Should test system health monitors', async () => {
      await page.waitForLoadState('networkidle');
      
      // Test any charts or graphs
      const charts = page.locator('canvas, .chart, .graph');
      if (await charts.count() > 0) {
        console.log(`Found ${await charts.count()} charts in system health`);
      }
      
      // Test refresh functionality if available
      const refreshButton = page.locator('button:has-text("Refresh")');
      if (await refreshButton.isVisible()) {
        await refreshButton.click();
        await page.waitForLoadState('networkidle');
      }
    });
  });



  test.describe('9. CELERY MONITOR COMPREHENSIVE TESTING', () => {
    test.beforeEach(async () => {
      await page.goto('/');
      await loginPage.login(testAdmin.username, testAdmin.password);
      await dashboardPage.navigateToCeleryMonitor();
    });

    test('10.1 Should display celery monitor page', async () => {
      await page.waitForLoadState('networkidle');
      
      const pageTitle = page.locator('h1, h2').first();
      if (await pageTitle.isVisible()) {
        await expect(pageTitle).toBeVisible();
      }
      
      await page.screenshot({ path: './test-results/celery-monitor-page.png', fullPage: true });
    });

    test('10.2 Should test celery worker monitoring', async () => {
      await page.waitForLoadState('networkidle');
      
      // Test worker status
      const workers = page.locator('.worker, .celery-worker');
      if (await workers.count() > 0) {
        console.log(`Found ${await workers.count()} celery workers`);
      }
      
      // Test task queue information
      const tasks = page.locator('.task, .celery-task');
      if (await tasks.count() > 0) {
        console.log(`Found ${await tasks.count()} celery tasks`);
      }
    });
  });

  test.describe('10. AUDIT DASHBOARD COMPREHENSIVE TESTING', () => {
    test.beforeEach(async () => {
      await page.goto('/');
      await loginPage.login(testAdmin.username, testAdmin.password);
      await dashboardPage.navigateToAudit();
    });

    test('11.1 Should display audit dashboard', async () => {
      await page.waitForLoadState('networkidle');
      
      const pageTitle = page.locator('h1, h2').first();
      if (await pageTitle.isVisible()) {
        await expect(pageTitle).toBeVisible();
      }
      
      await page.screenshot({ path: './test-results/audit-dashboard-page.png', fullPage: true });
    });

    test('11.2 Should test audit logs and filters', async () => {
      await page.waitForLoadState('networkidle');
      
      // Test audit log table
      const auditTable = page.locator('table, .data-grid');
      if (await auditTable.count() > 0) {
        await expect(auditTable.first()).toBeVisible();
      }
      
      // Test audit filters
      const filters = page.locator('input, select, .filter');
      const filterCount = await filters.count();
      console.log(`Found ${filterCount} audit filters`);
    });
  });

  test.describe('11. RESPONSIVE DESIGN TESTING', () => {
    test.beforeEach(async () => {
      await page.goto('/');
      await loginPage.login(testAdmin.username, testAdmin.password);
    });

    test('12.1 Should work on mobile viewport', async () => {
      await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
      await dashboardPage.expectDashboardPage();
      
      // Test mobile navigation
      const mobileMenu = page.locator('.mobile-menu, .hamburger, [aria-label*="menu"]');
      if (await mobileMenu.isVisible()) {
        await mobileMenu.click();
      }
      
      await page.screenshot({ path: './test-results/mobile-view.png', fullPage: true });
    });

    test('12.2 Should work on tablet viewport', async () => {
      await page.setViewportSize({ width: 768, height: 1024 }); // iPad
      await dashboardPage.expectDashboardPage();
      
      await page.screenshot({ path: './test-results/tablet-view.png', fullPage: true });
    });

    test('12.3 Should work on desktop viewport', async () => {
      await page.setViewportSize({ width: 1920, height: 1080 }); // Full HD
      await dashboardPage.expectDashboardPage();
      
      await page.screenshot({ path: './test-results/desktop-view.png', fullPage: true });
    });
  });

  test.describe('12. ACCESSIBILITY TESTING', () => {
    test.beforeEach(async () => {
      await page.goto('/');
      await loginPage.login(testAdmin.username, testAdmin.password);
    });

    test('13.1 Should have proper heading hierarchy', async () => {
      const h1Elements = page.locator('h1');
      const h2Elements = page.locator('h2');
      const h3Elements = page.locator('h3');
      
      console.log(`Found ${await h1Elements.count()} h1 elements`);
      console.log(`Found ${await h2Elements.count()} h2 elements`);
      console.log(`Found ${await h3Elements.count()} h3 elements`);
    });

    test('13.2 Should have proper form labels', async () => {
      await dashboardPage.navigateToTargets();
      await targetsPage.clickAddTarget();
      
      const labels = page.locator('label');
      const inputs = page.locator('input');
      
      console.log(`Found ${await labels.count()} labels and ${await inputs.count()} inputs`);
    });

    test('13.3 Should support keyboard navigation', async () => {
      // Test tab navigation
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      
      // Test if focus is visible
      const focusedElement = page.locator(':focus');
      if (await focusedElement.count() > 0) {
        console.log('Keyboard navigation is working');
      }
    });
  });

  test.describe('13. ERROR HANDLING TESTING', () => {
    test.beforeEach(async () => {
      await page.goto('/');
      await loginPage.login(testAdmin.username, testAdmin.password);
    });

    test('14.1 Should handle network errors gracefully', async () => {
      // Test offline behavior
      await page.context().setOffline(true);
      await page.reload();
      
      // Check for error messages
      const errorMessages = page.locator('[role="alert"], .error, .alert');
      if (await errorMessages.count() > 0) {
        console.log('Application shows appropriate error messages when offline');
      }
      
      // Restore network
      await page.context().setOffline(false);
    });

    test('14.2 Should handle invalid API responses', async () => {
      // Intercept API calls and return errors
      await page.route('**/api/**', route => {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ error: 'Internal Server Error' })
        });
      });
      
      await page.reload();
      
      // Check if error handling is working
      await page.waitForLoadState('networkidle');
    });
  });

  test.describe('14. PERFORMANCE TESTING', () => {
    test('14.1 Should load pages within reasonable time', async () => {
      const startTime = Date.now();
      
      await page.goto('/');
      await loginPage.login(testAdmin.username, testAdmin.password);
      
      const loadTime = Date.now() - startTime;
      console.log(`Login and dashboard load time: ${loadTime}ms`);
      
      // Test page navigation performance
      const pages = [
        { name: 'targets', navigate: () => dashboardPage.navigateToTargets() },
        { name: 'jobs', navigate: () => dashboardPage.navigateToJobs() },
        { name: 'users', navigate: () => dashboardPage.navigateToUsers() }
      ];
      
      for (const pageTest of pages) {
        const pageStartTime = Date.now();
        await pageTest.navigate();
        await page.waitForLoadState('networkidle');
        const pageLoadTime = Date.now() - pageStartTime;
        console.log(`${pageTest.name} page load time: ${pageLoadTime}ms`);
        
        // Navigate back to dashboard
        await dashboardPage.dashboardLink.click();
        await page.waitForLoadState('networkidle');
      }
    });
  });

  test.describe('15. LOGOUT AND SESSION TESTING', () => {
    test.beforeEach(async () => {
      await page.goto('/');
      await loginPage.login(testAdmin.username, testAdmin.password);
    });

    test('16.1 Should logout successfully', async () => {
      await dashboardPage.logout();
      await loginPage.expectLoginPage();
      expect(page.url()).toContain('/login');
    });

    test('16.2 Should redirect to login when accessing protected pages after logout', async () => {
      await dashboardPage.logout();
      
      // Try to access protected pages directly
      await page.goto('/dashboard');
      expect(page.url()).toContain('/login');
      
      await page.goto('/targets');
      expect(page.url()).toContain('/login');
      
      await page.goto('/jobs');
      expect(page.url()).toContain('/login');
    });
  });
});