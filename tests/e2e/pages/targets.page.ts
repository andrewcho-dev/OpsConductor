import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base.page';

export class TargetsPage extends BasePage {
  readonly pageTitle: Locator;
  readonly addTargetButton: Locator;
  readonly targetsTable: Locator;
  readonly searchField: Locator;
  readonly filterButtons: Locator;
  readonly discoveryButton: Locator;
  readonly bulkActionsButton: Locator;
  readonly refreshButton: Locator;
  
  // Target modal elements
  readonly createTargetModal: Locator;
  readonly editTargetModal: Locator;
  readonly targetNameField: Locator;
  readonly targetHostField: Locator;
  readonly targetPortField: Locator;
  readonly targetUsernameField: Locator;
  readonly targetPasswordField: Locator;
  readonly targetTypeSelect: Locator;
  readonly saveTargetButton: Locator;
  readonly cancelButton: Locator;
  readonly deleteTargetButton: Locator;
  readonly confirmDeleteButton: Locator;
  
  // Discovery modal elements
  readonly discoveryModal: Locator;
  readonly networkRangeField: Locator;
  readonly startDiscoveryButton: Locator;
  readonly discoveryResults: Locator;
  readonly selectDiscoveredDevices: Locator;
  readonly addSelectedDevicesButton: Locator;

  constructor(page: Page) {
    super(page);
    this.pageTitle = page.locator('h1:has-text("Targets"), h2:has-text("Targets")').first();
    this.addTargetButton = page.locator('button:has-text("Add Target"), button:has-text("Create Target"), button:has-text("New Target")').first();
    this.targetsTable = page.locator('table, [role="grid"], .data-grid').first();
    this.searchField = page.locator('input[placeholder*="search" i], input[type="search"]').first();
    this.filterButtons = page.locator('button:has-text("Filter"), .filter-button');
    this.discoveryButton = page.locator('button:has-text("Discovery"), button:has-text("Network Discovery")').first();
    this.bulkActionsButton = page.locator('button:has-text("Bulk Actions")').first();
    this.refreshButton = page.locator('button[aria-label*="refresh" i], button:has-text("Refresh")').first();
    
    // Modals
    this.createTargetModal = page.locator('[role="dialog"]:has-text("Create Target"), [role="dialog"]:has-text("Add Target")').first();
    this.editTargetModal = page.locator('[role="dialog"]:has-text("Edit Target")').first();
    this.targetNameField = page.locator('input[name="name"], input[placeholder*="name" i]').first();
    this.targetHostField = page.locator('input[name="host"], input[name="hostname"], input[placeholder*="host" i]').first();
    this.targetPortField = page.locator('input[name="port"], input[placeholder*="port" i]').first();
    this.targetUsernameField = page.locator('input[name="username"], input[placeholder*="username" i]').first();
    this.targetPasswordField = page.locator('input[name="password"], input[placeholder*="password" i]').first();
    this.targetTypeSelect = page.locator('select[name="type"], [role="combobox"]').first();
    this.saveTargetButton = page.locator('button:has-text("Save"), button:has-text("Create"), button[type="submit"]').first();
    this.cancelButton = page.locator('button:has-text("Cancel")').first();
    this.deleteTargetButton = page.locator('button:has-text("Delete")').first();
    this.confirmDeleteButton = page.locator('button:has-text("Confirm"), button:has-text("Yes")').first();
    
    // Discovery
    this.discoveryModal = page.locator('[role="dialog"]:has-text("Discovery"), [role="dialog"]:has-text("Network Discovery")').first();
    this.networkRangeField = page.locator('input[placeholder*="network" i], input[placeholder*="range" i]').first();
    this.startDiscoveryButton = page.locator('button:has-text("Start Discovery"), button:has-text("Scan")').first();
    this.discoveryResults = page.locator('.discovery-results, .scan-results').first();
    this.selectDiscoveredDevices = page.locator('input[type="checkbox"]');
    this.addSelectedDevicesButton = page.locator('button:has-text("Add Selected")').first();
  }

  async expectTargetsPage() {
    await expect(this.pageTitle).toBeVisible();
    await expect(this.targetsTable).toBeVisible();
    await expect(this.addTargetButton).toBeVisible();
  }

  async clickAddTarget() {
    await this.addTargetButton.click();
    await expect(this.createTargetModal).toBeVisible();
  }

  async createTarget(targetData: {
    name: string;
    host: string;
    port?: string;
    username?: string;
    password?: string;
    type?: string;
  }) {
    await this.clickAddTarget();
    await this.targetNameField.fill(targetData.name);
    await this.targetHostField.fill(targetData.host);
    
    if (targetData.port) {
      await this.targetPortField.fill(targetData.port);
    }
    if (targetData.username) {
      await this.targetUsernameField.fill(targetData.username);
    }
    if (targetData.password) {
      await this.targetPasswordField.fill(targetData.password);
    }
    if (targetData.type) {
      await this.targetTypeSelect.selectOption(targetData.type);
    }
    
    await this.saveTargetButton.click();
    await this.waitForPageLoad();
  }

  async searchTargets(searchTerm: string) {
    await this.searchField.fill(searchTerm);
    await this.waitForPageLoad();
  }

  async openDiscovery() {
    await this.discoveryButton.click();
    await expect(this.discoveryModal).toBeVisible();
  }

  async startNetworkDiscovery(networkRange: string) {
    await this.openDiscovery();
    await this.networkRangeField.fill(networkRange);
    await this.startDiscoveryButton.click();
    // Wait for discovery to complete
    await this.page.waitForTimeout(5000);
  }

  async editFirstTarget() {
    const firstEditButton = this.targetsTable.locator('button:has-text("Edit"), [aria-label*="edit" i]').first();
    await firstEditButton.click();
    await expect(this.editTargetModal).toBeVisible();
  }

  async deleteFirstTarget() {
    const firstDeleteButton = this.targetsTable.locator('button:has-text("Delete"), [aria-label*="delete" i]').first();
    await firstDeleteButton.click();
    await this.confirmDeleteButton.click();
    await this.waitForPageLoad();
  }

  async verifyTargetExists(targetName: string) {
    await expect(this.targetsTable.locator(`text="${targetName}"`)).toBeVisible();
  }
}