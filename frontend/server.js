const { createServer } = require('http');
const { parse } = require('url');
const next = require('next');
const httpProxy = require('http-proxy');

const dev = process.env.NODE_ENV !== 'production';
const hostname = 'localhost';
const port = parseInt(process.env.PORT || '3001', 10);

const app = next({ dev, hostname, port });
const handle = app.getRequestHandler();

// Create proxy with extended timeout
const proxy = httpProxy.createProxyServer({
  target: 'http://localhost:8000',
  changeOrigin: true,
  timeout: 120000, // 120 seconds (2 minutes)
  proxyTimeout: 120000,
  ws: true, // Enable WebSocket support
});

// Handle proxy errors
proxy.on('error', (err, req, res) => {
  console.error('[PROXY_ERROR]', err.message);
  if (!res.headersSent) {
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Proxy error', message: err.message }));
  }
});

// Log proxy requests
proxy.on('proxyReq', (proxyReq, req) => {
  console.log(`[PROXY] ${req.method} ${req.url} -> http://localhost:8000${req.url}`);
});

app.prepare().then(() => {
  createServer(async (req, res) => {
    try {
      const parsedUrl = parse(req.url, true);
      const { pathname } = parsedUrl;

      // Proxy API routes to backend with extended timeout
      if (
        pathname.startsWith('/api/') ||
        pathname.startsWith('/auth/') ||
        pathname.startsWith('/health/')
      ) {
        proxy.web(req, res);
        return;
      }

      // Handle all other requests with Next.js
      await handle(req, res, parsedUrl);
    } catch (err) {
      console.error('Error occurred handling', req.url, err);
      res.statusCode = 500;
      res.end('Internal server error');
    }
  })
    .once('error', (err) => {
      console.error(err);
      process.exit(1);
    })
    .listen(port, () => {
      console.log(`> Ready on http://${hostname}:${port}`);
      console.log(`> Proxying /api/*, /auth/*, /health/* to http://localhost:8000 with 120s timeout`);
    });
});
