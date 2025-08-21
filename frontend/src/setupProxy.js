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
      logLevel: 'info',
      onProxyReq: (proxyReq, req, res) => {
        console.log('📤 PROXY REQUEST:', req.method, req.url, '→', API_GATEWAY_TARGET + req.url);
      },
      onProxyRes: (proxyRes, req, res) => {
        console.log('📥 PROXY RESPONSE:', proxyRes.statusCode, req.url);
      },
      onError: (err, req, res) => {
        console.error('❌ PROXY ERROR:', err.message, 'for', req.url);
      }
    })
  );
  
  console.log('✅ Proxy middleware setup complete - Following port plan!');
};