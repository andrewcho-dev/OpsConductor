const { createProxyMiddleware } = require('http-proxy-middleware');

// ✅ PORT PLAN COMPLIANCE: API Gateway runs on port 80 internally (8080:80 mapping)
const API_GATEWAY_TARGET = 'http://opsconductor-api-gateway:80';

console.log('🔧 setupProxy.js loaded - Following official port plan');
console.log('🎯 API Gateway target:', API_GATEWAY_TARGET);

module.exports = function(app) {
  console.log('🚀 Setting up proxy middleware according to port plan...');
  
  // Proxy API requests to the API gateway (port 80 internal as per port plan)
  app.use(
    '/api',
    createProxyMiddleware({
      target: API_GATEWAY_TARGET,
      changeOrigin: true,
      secure: false,
      logLevel: 'debug',
      onProxyReq: (proxyReq, req, res) => {
        console.log('📤 Proxying API request:', req.method, req.url, '→', API_GATEWAY_TARGET + req.url);
      },
      onProxyRes: (proxyRes, req, res) => {
        console.log('📥 API Proxy response:', proxyRes.statusCode, req.url);
      },
      onError: (err, req, res) => {
        console.error('❌ API Proxy error:', err.message, 'for', req.url);
      }
    })
  );
  
  // Proxy WebSocket requests to the API gateway (port 80 internal as per port plan)
  app.use(
    '/ws',
    createProxyMiddleware({
      target: API_GATEWAY_TARGET,
      changeOrigin: true,
      ws: true,
      secure: false,
      logLevel: 'debug',
      onProxyReq: (proxyReq, req, res) => {
        console.log('📤 Proxying WS request:', req.method, req.url, '→', API_GATEWAY_TARGET + req.url);
      },
      onError: (err, req, res) => {
        console.error('❌ WS Proxy error:', err.message, 'for', req.url);
      }
    })
  );
  
  console.log('✅ Proxy middleware setup complete - Following port plan!');
};