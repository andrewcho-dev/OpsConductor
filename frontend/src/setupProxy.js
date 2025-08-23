const { createProxyMiddleware } = require('http-proxy-middleware');

// ✅ Use nginx as the API gateway
const API_GATEWAY_TARGET = 'http://opsconductor-nginx:80';

console.log('🔧 setupProxy.js loaded - Following official port plan');
console.log('🎯 API Gateway target:', API_GATEWAY_TARGET);

module.exports = function(app) {
  console.log('🚀 Setting up proxy middleware according to port plan...');
  
  // Proxy service requests to nginx (which routes to microservices)
  const services = ['/auth', '/users', '/targets', '/jobs', '/execution', '/audit', '/notifications'];
  
  services.forEach(service => {
    app.use(
      service,
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
  });
  
  console.log('✅ Proxy middleware setup complete - Following port plan!');
};