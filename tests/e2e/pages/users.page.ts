import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base.page';

export class UsersPage extends BasePage {
  readonly pageTitle: Locator;
  readonly addUserButton: Locator;
  readonly usersTable: Locator;
  readonly searchField: Locator;
  readonly filterButtons: Locator;
  readonly refreshButton: Locator;
  
  // User creation modal
  readonly createUserModal: Locator;
  readonly usernameField: Locator;
  readonly passwordField: Locator;
  readonly confirmPasswordField: Locator;
  readonly emailField: Locator;
  readonly fullNameField: Locator;
  readonly roleSelect: Locator;
  readonly isActiveCheckbox: Locator;
  readonly isAdminCheckbox: Locator;
  readonly saveUserButton: Locator;
  readonly cancelUserButton: Locator;
  
  // User edit modal
  readonly editUserModal: Locator;
  readonly deleteUserButton: Locator;
  readonly confirmDeleteButton: Locator;
  readonly resetPasswordButton: Locator;
  readonly newPasswordField: Locator;
  readonly savePasswordButton: Locator;

  constructor(page: Page) {
    super(page);
    this.pageTitle = page.locator('h1:has-text("Users"), h2:has-text("User Management")').first();
    this.addUserButton = page.locator('button:has-text("Add User"), button:has-text("Create User"), button:has-text("New User")').first();
    this.usersTable = page.locator('table, [role="grid"], .data-grid').first();
    this.searchField = page.locator('input[placeholder*="search" i], input[type="search"]').first();
    this.filterButtons = page.locator('button:has-text("Filter"), .filter-button');
    this.refreshButton = page.locator('button[aria-label*="refresh" i], button:has-text("Refresh")').first();
    
    // User creation
    this.createUserModal = page.locator('[role="dialog"]:has-text("Create User"), [role="dialog"]:has-text("Add User")').first();
    this.usernameField = page.locator('input[name="username"], input[placeholder*="username" i]').first();
    this.passwordField = page.locator('input[name="password"], input[placeholder*="password" i]').first();
    this.confirmPasswordField = page.locator('input[name="confirmPassword"], input[placeholder*="confirm" i]').first();
    this.emailField = page.locator('input[name="email"], input[type="email"]').first();
    this.fullNameField = page.locator('input[name="fullName"], input[name="name"]').first();
    this.roleSelect = page.locator('select[name="role"], [role="combobox"]').first();
    this.isActiveCheckbox = page.locator('input[name="isActive"], input[type="checkbox"]:near(:text("Active"))').first();
    this.isAdminCheckbox = page.locator('input[name="isAdmin"], input[type="checkbox"]:near(:text("Admin"))').first();
    this.saveUserButton = page.locator('button:has-text("Save"), button:has-text("Create"), button[type="submit"]').first();
    this.cancelUserButton = page.locator('button:has-text("Cancel")').first();
    
    // User editing
    this.editUserModal = page.locator('[role="dialog"]:has-text("Edit User")').first();
    this.deleteUserButton = page.locator('button:has-text("Delete User"), button:has-text("Delete")').first();
    this.confirmDeleteButton = page.locator('button:has-text("Confirm"), button:has-text("Yes")').first();
    this.resetPasswordButton = page.locator('button:has-text("Reset Password")').first();
    this.newPasswordField = page.locator('input[name="newPassword"]').first();
    this.savePasswordButton = page.locator('button:has-text("Save Password")').first();
  }

  async expectUsersPage() {
    await expect(this.pageTitle).toBeVisible();
    await expect(this.usersTable).toBeVisible();
    await expect(this.addUserButton).toBeVisible();
  }

  async clickAddUser() {
    await this.addUserButton.click();
    await expect(this.createUserModal).toBeVisible();
  }

  async createUser(userData: {
    username: string;
    password: string;
    email?: string;
    fullName?: string;
    role?: string;
    isActive?: boolean;
    isAdmin?: boolean;
  }) {
    await this.clickAddUser();
    
    await this.usernameField.fill(userData.username);
    await this.passwordField.fill(userData.password);
    await this.confirmPasswordField.fill(userData.password);
    
    if (userData.email) {
      await this.emailField.fill(userData.email);
    }
    if (userData.fullName) {
      await this.fullNameField.fill(userData.fullName);
    }
    if (userData.role) {
      await this.roleSelect.selectOption(userData.role);
    }
    if (userData.isActive !== undefined) {
      if (userData.isActive) {
        await this.isActiveCheckbox.check();
      } else {
        await this.isActiveCheckbox.uncheck();
      }
    }
    if (userData.isAdmin !== undefined) {
      if (userData.isAdmin) {
        await this.isAdminCheckbox.check();
      } else {
        await this.isAdminCheckbox.uncheck();
      }
    }
    
    await this.saveUserButton.click();
    await this.waitForPageLoad();
  }

  async searchUsers(searchTerm: string) {
    await this.searchField.fill(searchTerm);
    await this.waitForPageLoad();
  }

  async editFirstUser() {
    const firstEditButton = this.usersTable.locator('button:has-text("Edit"), [aria-label*="edit" i]').first();
    await firstEditButton.click();
    await expect(this.editUserModal).toBeVisible();
  }

  async deleteFirstUser() {
    const firstDeleteButton = this.usersTable.locator('button:has-text("Delete"), [aria-label*="delete" i]').first();
    await firstDeleteButton.click();
    await this.confirmDeleteButton.click();
    await this.waitForPageLoad();
  }

  async resetUserPassword(newPassword: string) {
    await this.editFirstUser();
    await this.resetPasswordButton.click();
    await this.newPasswordField.fill(newPassword);
    await this.savePasswordButton.click();
    await this.waitForPageLoad();
  }

  async verifyUserExists(username: string) {
    await expect(this.usersTable.locator(`text="${username}"`)).toBeVisible();
  }
}