import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base.page';

export class DashboardPage extends BasePage {
  readonly sidebar: Locator;
  readonly header: Locator;
  readonly mainContent: Locator;
  readonly logoutButton: Locator;
  readonly userMenu: Locator;
  
  // Navigation links
  readonly dashboardLink: Locator;
  readonly targetsLink: Locator;
  readonly jobsLink: Locator;
  readonly usersLink: Locator;
  readonly systemSettingsLink: Locator;
  readonly notificationsLink: Locator;
  readonly systemHealthLink: Locator;
  readonly auditLink: Locator;

  readonly celeryMonitorLink: Locator;

  // Dashboard metrics
  readonly metricsCards: Locator;
  readonly chartsSection: Locator;
  readonly recentActivitySection: Locator;

  constructor(page: Page) {
    super(page);
    this.sidebar = page.locator('[role="navigation"], .sidebar, nav').first();
    this.header = page.locator('header, .header, .top-header').first();
    this.mainContent = page.locator('main, .main-content, [role="main"]').first();
    this.logoutButton = page.locator('button:has-text("Logout"), button:has-text("Sign out")').first();
    this.userMenu = page.locator('.user-menu, .profile-menu, [aria-label*="user" i]').first();
    
    // Navigation - using multiple possible selectors
    this.dashboardLink = page.locator('a[href="/dashboard"], a:has-text("Dashboard")').first();
    this.targetsLink = page.locator('a[href="/targets"], a:has-text("Targets")').first();
    this.jobsLink = page.locator('a[href="/jobs"], a:has-text("Jobs")').first();
    this.usersLink = page.locator('a[href="/users"], a:has-text("Users")').first();
    this.systemSettingsLink = page.locator('a[href="/system-settings"], a:has-text("System Settings")').first();
    this.notificationsLink = page.locator('a[href="/notifications"], a:has-text("Notifications")').first();
    this.systemHealthLink = page.locator('a[href="/system-health"], a:has-text("System Health")').first();
    this.auditLink = page.locator('a[href="/audit"], a:has-text("Audit")').first();

    this.celeryMonitorLink = page.locator('a[href="/celery-monitor"], a:has-text("Celery Monitor")').first();

    // Dashboard content
    this.metricsCards = page.locator('.metric-card, .stats-card, .dashboard-card');
    this.chartsSection = page.locator('.charts, .chart-section, canvas');
    this.recentActivitySection = page.locator('.recent-activity, .activity-section');
  }

  async expectDashboardPage() {
    await expect(this.sidebar).toBeVisible();
    await expect(this.mainContent).toBeVisible();
    await expect(this.dashboardLink).toBeVisible();
  }

  async navigateToTargets() {
    await this.targetsLink.click();
    await this.waitForPageLoad();
  }

  async navigateToJobs() {
    await this.jobsLink.click();
    await this.waitForPageLoad();
  }

  async navigateToUsers() {
    await this.usersLink.click();
    await this.waitForPageLoad();
  }

  async navigateToSystemSettings() {
    await this.systemSettingsLink.click();
    await this.waitForPageLoad();
  }

  async navigateToNotifications() {
    await this.notificationsLink.click();
    await this.waitForPageLoad();
  }

  async navigateToSystemHealth() {
    await this.systemHealthLink.click();
    await this.waitForPageLoad();
  }

  async navigateToAudit() {
    await this.auditLink.click();
    await this.waitForPageLoad();
  }



  async navigateToCeleryMonitor() {
    await this.celeryMonitorLink.click();
    await this.waitForPageLoad();
  }

  async logout() {
    if (await this.userMenu.isVisible()) {
      await this.userMenu.click();
    }
    await this.logoutButton.click();
    await this.waitForPageLoad();
  }
}