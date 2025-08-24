const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Use environment variables for proxy target - defaults to nginx service on Docker network
  const proxyHost = process.env.PROXY_TARGET_HOST || 'nginx';
  const proxyPort = process.env.PROXY_TARGET_PORT || '443';
  const proxyProtocol = process.env.PROXY_TARGET_PROTOCOL || 'https';
  const proxyTarget = `${proxyProtocol}://${proxyHost}:${proxyPort}`;
  
  console.log(`🔧 Setting up proxy to: ${proxyTarget}`);
  
  // Proxy API requests to nginx gateway using configurable target
  app.use(
    '/api',
    createProxyMiddleware({
      target: proxyTarget,
      changeOrigin: true,
      secure: false, // Allow self-signed certificates
      logLevel: 'debug',
      // Don't rewrite paths - preserve the original path including /api
      pathRewrite: (path, req) => {
        console.log(`🔄 Original path: ${path}`);
        console.log(`🔄 Request URL: ${req.url}`);
        // Return the original path with /api prefix
        const newPath = '/api' + path;
        console.log(`🔄 Rewritten path: ${newPath}`);
        return newPath;
      },
      onProxyReq: (proxyReq, req, res) => {
        console.log(`🔄 Proxying ${req.method} ${req.originalUrl} to ${proxyTarget}`);
      },
      onProxyRes: (proxyRes, req, res) => {
        console.log(`✅ Proxy response: ${proxyRes.statusCode} for ${req.originalUrl}`);
      },
      onError: (err, req, res) => {
        console.error('❌ Proxy error:', err.message);
        console.error('❌ Request URL:', req.originalUrl);
        console.error('❌ Target:', proxyTarget);
      }
    })
  );
};