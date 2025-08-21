const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Proxy API requests to the API gateway (use container name for Docker networking)
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://opsconductor-api-gateway:80',
      changeOrigin: true,
      secure: false,
      logLevel: 'debug'
    })
  );
  
  // Proxy WebSocket requests
  app.use(
    '/ws',
    createProxyMiddleware({
      target: 'http://opsconductor-api-gateway:80',
      changeOrigin: true,
      ws: true,
      secure: false,
      logLevel: 'debug'
    })
  );
};