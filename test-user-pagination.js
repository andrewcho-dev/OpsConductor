const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  try {
    // Set viewport size
    await page.setViewportSize({ width: 1280, height: 720 });
    
    // First go to login page
    await page.goto('http://localhost/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    // Login with correct credentials
    await page.fill('#username', 'admin');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);
    
    // Navigate to user management page
    console.log('Navigating to user management...');
    await page.goto('http://localhost/users', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);
    
    console.log('PAGE LOADED SUCCESSFULLY');
    
    // Check if pagination is visible in viewport
    const paginationVisibility = await page.evaluate(() => {
      const paginationElement = document.querySelector('.MuiPagination-root');
      if (!paginationElement) return { found: false };
      
      const rect = paginationElement.getBoundingClientRect();
      const viewportHeight = window.innerHeight;
      const viewportWidth = window.innerWidth;
      
      return {
        found: true,
        isVisible: rect.top >= 0 && rect.left >= 0 && rect.bottom <= viewportHeight && rect.right <= viewportWidth,
        position: {
          top: rect.top,
          bottom: rect.bottom,
          left: rect.left,
          right: rect.right
        },
        viewport: {
          height: viewportHeight,
          width: viewportWidth
        },
        scrollPosition: {
          scrollY: window.scrollY,
          scrollX: window.scrollX
        }
      };
    });
    
    console.log('USER MANAGEMENT PAGINATION VISIBILITY:');
    console.log(JSON.stringify(paginationVisibility, null, 2));
    
    if (paginationVisibility.found && paginationVisibility.isVisible) {
      console.log('✅ SUCCESS: Pagination is visible within viewport!');
    } else if (paginationVisibility.found && !paginationVisibility.isVisible) {
      console.log('❌ ISSUE: Pagination found but not visible in viewport');
      console.log(`Pagination bottom: ${paginationVisibility.position.bottom}, Viewport height: ${paginationVisibility.viewport.height}`);
    } else {
      console.log('❌ ERROR: Pagination not found');
    }
    
  } catch (error) {
    console.error('Error:', error.message);
  }
  
  await browser.close();
})();