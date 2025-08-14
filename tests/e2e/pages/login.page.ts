import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base.page';

export class LoginPage extends BasePage {
  readonly usernameField: Locator;
  readonly passwordField: Locator;
  readonly loginButton: Locator;
  readonly errorMessage: Locator;
  readonly title: Locator;

  constructor(page: Page) {
    super(page);
    this.usernameField = page.locator('input[type="text"], input[name="username"], input[placeholder*="username" i]').first();
    this.passwordField = page.locator('input[type="password"], input[name="password"], input[placeholder*="password" i]').first();
    this.loginButton = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")').first();
    this.errorMessage = page.locator('[role="alert"], .error, .alert-error').first();
    this.title = page.locator('h1, h2, .title').first();
  }

  async login(username: string, password: string) {
    await this.usernameField.fill(username);
    await this.passwordField.fill(password);
    await this.loginButton.click();
  }

  async expectLoginPage() {
    await expect(this.usernameField).toBeVisible();
    await expect(this.passwordField).toBeVisible();
    await expect(this.loginButton).toBeVisible();
  }

  async expectLoginError() {
    await expect(this.errorMessage).toBeVisible();
  }
}