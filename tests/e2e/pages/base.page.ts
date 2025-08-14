import { Page, Locator, expect } from '@playwright/test';

export class BasePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto(path: string = '') {
    await this.page.goto(path);
  }

  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
  }

  async takeScreenshot(name: string) {
    await this.page.screenshot({ path: `./test-results/${name}.png`, fullPage: true });
  }

  async checkErrorAlert() {
    const errorAlert = this.page.locator('[role="alert"]').filter({ hasText: /error|failed|invalid/i });
    if (await errorAlert.count() > 0) {
      const errorText = await errorAlert.first().textContent();
      throw new Error(`Error alert detected: ${errorText}`);
    }
  }
}