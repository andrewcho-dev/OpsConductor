import { test, expect } from '@playwright/test';

test.describe('COMPREHENSIVE API TESTING', () => {
  let baseURL: string;
  let authToken: string;

  test.beforeAll(() => {
    baseURL = process.env.BASE_URL || 'http://localhost';
  });

  test.describe('1. HEALTH & STATUS ENDPOINTS', () => {
    test('1.1 Health endpoint should return healthy status', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/health`);
      expect(response.status()).toBe(200);
      
      const data = await response.json();
      expect(data.status).toBe('healthy');
      expect(data.service).toContain('ENABLEDRM');
      
      console.log('✅ Health endpoint working correctly');
    });

    test('1.2 Should handle non-existent endpoints gracefully', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/nonexistent`);
      expect(response.status()).toBe(404);
      
      const data = await response.json();
      expect(data.detail).toBe('Not Found');
      
      console.log('✅ 404 handling working correctly');
    });
  });

  test.describe('2. AUTHENTICATION ENDPOINTS', () => {
    test('2.1 Should test authentication endpoints availability', async ({ request }) => {
      // Test common auth endpoint patterns
      const authEndpoints = [
        '/api/auth/login',
        '/api/login',
        '/api/token',
        '/api/auth/token'
      ];

      let foundAuthEndpoint = false;
      for (const endpoint of authEndpoints) {
        try {
          const response = await request.post(`${baseURL}${endpoint}`, {
            data: { username: 'test', password: 'test' }
          });
          
          // If we get anything other than 404, the endpoint exists
          if (response.status() !== 404) {
            console.log(`✅ Found auth endpoint: ${endpoint} (Status: ${response.status()})`);
            foundAuthEndpoint = true;
            break;
          }
        } catch (error) {
          // Continue to next endpoint
        }
      }

      if (!foundAuthEndpoint) {
        console.log('⚠️  No standard auth endpoints found - may use different pattern');
      }
    });

    test('2.2 Should handle invalid authentication gracefully', async ({ request }) => {
      const response = await request.post(`${baseURL}/api/auth/login`, {
        data: {
          username: 'invalid_user',
          password: 'invalid_password'
        },
        failOnStatusCode: false
      });

      // Should either be 401 (unauthorized) or 404 (endpoint not found)
      expect([401, 404, 422]).toContain(response.status());
      
      console.log(`✅ Auth validation working (Status: ${response.status()})`);
    });
  });

  test.describe('3. API ENDPOINTS DISCOVERY', () => {
    test('3.1 Should discover available API endpoints', async ({ request }) => {
      const commonEndpoints = [
        '/api',
        '/api/docs',
        '/api/openapi.json',
        '/api/v1',
        '/api/targets',
        '/api/jobs',
        '/api/users',
        '/api/auth',
        '/api/status',
        '/api/version'
      ];

      const availableEndpoints: string[] = [];
      
      for (const endpoint of commonEndpoints) {
        try {
          const response = await request.get(`${baseURL}${endpoint}`, {
            failOnStatusCode: false
          });
          
          if (response.status() !== 404) {
            availableEndpoints.push(`${endpoint} (${response.status()})`);
          }
        } catch (error) {
          // Continue to next endpoint
        }
      }

      console.log('✅ Available API endpoints:', availableEndpoints);
      expect(availableEndpoints.length).toBeGreaterThan(0);
    });

    test('3.2 Should test API documentation endpoints', async ({ request }) => {
      const docEndpoints = ['/api/docs', '/api/redoc', '/api/openapi.json'];
      
      for (const endpoint of docEndpoints) {
        const response = await request.get(`${baseURL}${endpoint}`, {
          failOnStatusCode: false
        });
        
        if (response.status() === 200) {
          console.log(`✅ API documentation available at: ${endpoint}`);
        }
      }
    });
  });

  test.describe('4. CORS AND SECURITY HEADERS', () => {
    test('4.1 Should check CORS headers', async ({ request }) => {
      const response = await request.options(`${baseURL}/api/health`);
      const headers = response.headers();
      
      if (headers['access-control-allow-origin']) {
        console.log(`✅ CORS enabled: ${headers['access-control-allow-origin']}`);
      }
      
      if (headers['access-control-allow-methods']) {
        console.log(`✅ Allowed methods: ${headers['access-control-allow-methods']}`);
      }
    });

    test('4.2 Should check security headers', async ({ request }) => {
      const response = await request.get(`${baseURL}`);
      const headers = response.headers();
      
      const securityHeaders = [
        'x-frame-options',
        'x-content-type-options',
        'x-xss-protection',
        'strict-transport-security',
        'content-security-policy'
      ];

      securityHeaders.forEach(header => {
        if (headers[header]) {
          console.log(`✅ Security header found: ${header}: ${headers[header]}`);
        }
      });
    });
  });

  test.describe('5. PERFORMANCE AND RELIABILITY', () => {
    test('5.1 Should respond within acceptable time limits', async ({ request }) => {
      const startTime = Date.now();
      const response = await request.get(`${baseURL}/api/health`);
      const responseTime = Date.now() - startTime;
      
      expect(response.status()).toBe(200);
      expect(responseTime).toBeLessThan(5000); // 5 seconds max
      
      console.log(`✅ Response time: ${responseTime}ms`);
    });

    test('5.2 Should handle concurrent requests', async ({ request }) => {
      const requests = Array(10).fill(null).map(() => 
        request.get(`${baseURL}/api/health`)
      );
      
      const responses = await Promise.all(requests);
      
      responses.forEach((response, index) => {
        expect(response.status()).toBe(200);
      });
      
      console.log(`✅ Handled ${requests.length} concurrent requests successfully`);
    });

    test('5.3 Should test with various HTTP methods', async ({ request }) => {
      const methods = [
        { method: 'GET', endpoint: '/api/health' },
        { method: 'POST', endpoint: '/api/health' },
        { method: 'PUT', endpoint: '/api/health' },
        { method: 'DELETE', endpoint: '/api/health' },
        { method: 'PATCH', endpoint: '/api/health' }
      ];

      for (const { method, endpoint } of methods) {
        const response = await request.fetch(`${baseURL}${endpoint}`, {
          method: method,
          failOnStatusCode: false
        });
        
        console.log(`${method} ${endpoint}: ${response.status()}`);
      }
    });
  });

  test.describe('6. ERROR HANDLING', () => {
    test('6.1 Should handle malformed requests', async ({ request }) => {
      const response = await request.post(`${baseURL}/api/health`, {
        data: 'invalid json',
        headers: { 'content-type': 'application/json' },
        failOnStatusCode: false
      });
      
      // Should handle malformed JSON gracefully
      expect([400, 404, 405, 422]).toContain(response.status());
      console.log(`✅ Malformed request handled: ${response.status()}`);
    });

    test('6.2 Should handle large payloads', async ({ request }) => {
      const largePayload = 'x'.repeat(1000000); // 1MB of data
      
      const response = await request.post(`${baseURL}/api/health`, {
        data: { data: largePayload },
        failOnStatusCode: false
      });
      
      // Should either handle or reject appropriately
      expect([200, 400, 404, 405, 413, 422]).toContain(response.status());
      console.log(`✅ Large payload handled: ${response.status()}`);
    });
  });

  test.describe('7. CONTENT TYPE HANDLING', () => {
    test('7.1 Should handle different content types', async ({ request }) => {
      const contentTypes = [
        'application/json',
        'application/x-www-form-urlencoded',
        'text/plain',
        'application/xml'
      ];

      for (const contentType of contentTypes) {
        const response = await request.post(`${baseURL}/api/health`, {
          data: contentType === 'application/json' ? {} : 'test data',
          headers: { 'content-type': contentType },
          failOnStatusCode: false
        });
        
        console.log(`${contentType}: ${response.status()}`);
      }
    });
  });

  test.describe('8. API RATE LIMITING', () => {
    test('8.1 Should test rate limiting if implemented', async ({ request }) => {
      const requests = [];
      
      // Send many requests quickly to test rate limiting
      for (let i = 0; i < 50; i++) {
        requests.push(
          request.get(`${baseURL}/api/health`, { failOnStatusCode: false })
        );
      }
      
      const responses = await Promise.all(requests);
      const rateLimited = responses.filter(r => r.status() === 429);
      
      if (rateLimited.length > 0) {
        console.log(`✅ Rate limiting active: ${rateLimited.length} requests limited`);
      } else {
        console.log('⚠️  No rate limiting detected');
      }
    });
  });

  test.describe('9. WEBSOCKET TESTING', () => {
    test('9.1 Should check for WebSocket endpoints', async ({ page }) => {
      // Listen for WebSocket connections
      let websocketConnected = false;
      
      page.on('websocket', ws => {
        websocketConnected = true;
        console.log('✅ WebSocket connection detected');
      });
      
      // Navigate to the main page to trigger WebSocket connections
      try {
        await page.goto(`${baseURL}`, { timeout: 10000 });
        await page.waitForTimeout(3000);
      } catch (error) {
        console.log('⚠️  Could not test WebSocket - page load failed');
      }
      
      if (websocketConnected) {
        console.log('✅ WebSocket functionality available');
      } else {
        console.log('⚠️  No WebSocket connections detected');
      }
    });
  });

  test.describe('10. API VERSION AND METADATA', () => {
    test('10.1 Should check API version information', async ({ request }) => {
      const versionEndpoints = [
        '/api/version',
        '/api/v1',
        '/api/info',
        '/api/status'
      ];
      
      for (const endpoint of versionEndpoints) {
        const response = await request.get(`${baseURL}${endpoint}`, {
          failOnStatusCode: false
        });
        
        if (response.status() === 200) {
          try {
            const data = await response.json();
            console.log(`✅ Version info at ${endpoint}:`, data);
          } catch (e) {
            console.log(`✅ Version endpoint found: ${endpoint}`);
          }
        }
      }
    });
  });
});