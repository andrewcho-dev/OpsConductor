const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ 
    headless: true,
    args: ['--ignore-certificate-errors', '--ignore-ssl-errors', '--allow-running-insecure-content']
  });
  const page = await browser.newPage();
  await page.setExtraHTTPHeaders({
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
  });
  
  try {
    // First go to login page
    await page.goto('http://localhost/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    // Login with correct credentials
    await page.fill('#username', 'admin');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);
    
    // Now navigate to audit page
    await page.goto('http://localhost/audit', { waitUntil: 'networkidle' });
    await page.waitForTimeout(5000); // Wait for React to render
    
    // Get all the page content first
    const pageContent = await page.content();
    console.log('PAGE LOADED SUCCESSFULLY');
    
    // Look for any table or grid elements
    const tableElements = await page.evaluate(() => {
      const tables = document.querySelectorAll('table, [class*="Table"], [class*="Grid"], [class*="DataGrid"]');
      return Array.from(tables).map(table => ({
        tagName: table.tagName,
        className: table.className,
        innerHTML: table.innerHTML.substring(0, 1000)
      }));
    });
    
    console.log('TABLE ELEMENTS:');
    console.log(JSON.stringify(tableElements, null, 2));
    
    // Look for pagination specifically
    const paginationElements = await page.evaluate(() => {
      const selectors = [
        '[class*="pagination"]', 
        '[class*="Pagination"]', 
        '.MuiPagination-root', 
        '.MuiTablePagination-root',
        '[class*="page"]',
        'button[aria-label*="page"]',
        'button[aria-label*="next"]',
        'button[aria-label*="previous"]'
      ];
      
      let found = [];
      selectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
          found.push({
            selector: selector,
            tagName: el.tagName,
            className: el.className,
            textContent: el.textContent,
            innerHTML: el.innerHTML.substring(0, 500),
            outerHTML: el.outerHTML.substring(0, 800)
          });
        });
      });
      return found;
    });
    
    console.log('PAGINATION ELEMENTS FOUND:');
    console.log(JSON.stringify(paginationElements, null, 2));
    
    // Get the entire body content to see what's actually there
    const bodyContent = await page.evaluate(() => {
      return document.body.innerHTML.substring(0, 2000);
    });
    
    console.log('BODY CONTENT:');
    console.log(bodyContent);
    
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
    
    console.log('PAGINATION VISIBILITY:');
    console.log(JSON.stringify(paginationVisibility, null, 2));
    
  } catch (error) {
    console.error('Error:', error.message);
  }
  
  await browser.close();
})();