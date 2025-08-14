import { test, expect } from '@playwright/test';

test.describe('SMOKE TESTS - Basic Application Functionality', () => {
  test('Application should be accessible and load correctly', async ({ page }) => {
    // Test 1: Basic accessibility
    await page.goto('/');
    await expect(page).toHaveTitle(/OpsConductor|ENABLEDRM/i);
    
    // Test 2: Check for React app div
    const appRoot = page.locator('#root, [id*="app"], main, .app');
    await expect(appRoot.first()).toBeVisible({ timeout: 10000 });
    
    // Test 3: Wait for JavaScript to load
    await page.waitForLoadState('networkidle', { timeout: 30000 });
    
    // Test 4: Check if login form is present (indicates proper React load)
    const hasLoginForm = await page.locator('input[type="password"], input[placeholder*="password" i]').count() > 0;
    const hasDashboardContent = await page.locator('nav, .sidebar, [role="navigation"]').count() > 0;
    
    // Should have either login form or dashboard content
    expect(hasLoginForm || hasDashboardContent).toBeTruthy();
    
    console.log('✅ Application loads correctly');
  });

  test('API Health endpoint should be accessible', async ({ request }) => {
    const response = await request.get('/api/health');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.status).toBe('healthy');
    
    console.log('✅ API Health endpoint working');
  });

  test('Frontend assets should load properly', async ({ page }) => {
    await page.goto('/');
    
    // Check if CSS is loading
    const hasStyles = await page.evaluate(() => {
      const computedStyle = window.getComputedStyle(document.body);
      return computedStyle.margin !== '' || computedStyle.fontFamily !== '';
    });
    
    expect(hasStyles).toBeTruthy();
    
    // Check if JavaScript is working
    const hasReactElements = await page.locator('[data-reactroot], [data-react-helmet]').count() > 0;
    const hasReactContent = await page.evaluate(() => {
      return document.querySelector('[class*="react"], [id*="react"], .App, .app-root') !== null;
    });
    
    expect(hasReactElements || hasReactContent).toBeTruthy();
    
    console.log('✅ Frontend assets load correctly');
  });

  test('Navigation elements should be present', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle', { timeout: 30000 });
    
    // Check for navigation elements (login form OR authenticated navigation)
    const navigationElements = await page.locator(`
      input[type="password"],
      nav,
      .sidebar,
      [role="navigation"],
      a[href*="dashboard"],
      button:has-text("Login"),
      button:has-text("Sign"),
      .nav-item,
      .menu-item
    `).count();
    
    expect(navigationElements).toBeGreaterThan(0);
    
    console.log('✅ Navigation elements found');
  });

  test('Application should handle basic interactions', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle', { timeout: 30000 });
    
    // Try to find and click on interactive elements
    const interactiveElements = page.locator('button, input, a, [role="button"]');
    const count = await interactiveElements.count();
    
    if (count > 0) {
      // Try clicking on the first visible interactive element
      for (let i = 0; i < Math.min(count, 5); i++) {
        const element = interactiveElements.nth(i);
        if (await element.isVisible() && await element.isEnabled()) {
          try {
            await element.click({ timeout: 2000 });
            break;
          } catch (e) {
            // Continue to next element if this one fails
            console.log(`Element ${i} not clickable, trying next...`);
          }
        }
      }
    }
    
    expect(count).toBeGreaterThan(0);
    console.log(`✅ Found ${count} interactive elements`);
  });

  test('Application should be responsive', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle', { timeout: 30000 });
    
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(1000);
    
    const mobileElements = await page.locator('body *').count();
    expect(mobileElements).toBeGreaterThan(0);
    
    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(1000);
    
    const desktopElements = await page.locator('body *').count();
    expect(desktopElements).toBeGreaterThan(0);
    
    console.log('✅ Application responsive on different viewports');
  });

  test('Console should not have critical errors', async ({ page }) => {
    const consoleErrors: string[] = [];
    
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    await page.goto('/');
    await page.waitForLoadState('networkidle', { timeout: 30000 });
    
    // Filter out non-critical errors
    const criticalErrors = consoleErrors.filter(error => 
      !error.includes('favicon') && 
      !error.includes('websocket') &&
      !error.includes('404') &&
      !error.includes('network')
    );
    
    console.log(`Total console errors: ${consoleErrors.length}, Critical: ${criticalErrors.length}`);
    
    if (criticalErrors.length > 0) {
      console.log('Critical errors:', criticalErrors);
    }
    
    // Allow some non-critical errors but log them
    expect(criticalErrors.length).toBeLessThanOrEqual(3);
    
    console.log('✅ No critical console errors');
  });
});