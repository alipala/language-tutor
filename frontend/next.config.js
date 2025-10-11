/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false, // Prevent double rendering in production
  swcMinify: true,
  // Remove console logs in production for security
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production' ? {
      exclude: ['error'] // Keep console.error for critical error logging
    } : false,
  },
  // Static export disabled - using Node.js server for dynamic routes
  trailingSlash: false, // Prevent redirect loops
  // Configure basePath for Railway deployment
  basePath: '',
  // Ensure Next.js knows it's being served from the root
  assetPrefix: process.env.NODE_ENV === 'production' ? '' : undefined,
  // Disable page reloads during development
  devIndicators: {
    buildActivity: false,
  },
  // Environment variables
  env: {
    BACKEND_URL: process.env.NODE_ENV === 'production'
      ? process.env.BACKEND_URL || ''
      : 'http://localhost:8000',
    NEXT_PUBLIC_GOOGLE_CLIENT_ID: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '41687548204-0go9lqlnve4llpv3vdl48jujddlt2kp5.apps.googleusercontent.com',
  },
  // Disable image optimization since it requires a server component
  images: {
    unoptimized: true,
  },
  // Improve static generation for Railway
  poweredByHeader: false,
  // Increase the timeout for generating static pages
  staticPageGenerationTimeout: 180,
  // Compress responses for better performance
  compress: true,
  // Proxy API requests to backend
  async rewrites() {
    // In Railway, backend runs on localhost:8000, frontend on the dynamic PORT
    const backendUrl = process.env.NODE_ENV === 'production' 
      ? 'http://localhost:8000'  // Fixed backend port in production
      : (process.env.BACKEND_URL || 'http://localhost:8000')
    console.log('[NEXT_CONFIG] Proxying API routes to:', backendUrl)
    return [
      // Proxy /api/institution/* to /institution/* (strip /api prefix for institution routes)
      {
        source: '/api/institution/:path*',
        destination: `${backendUrl}/institution/:path*`,
      },
      // Proxy /api/tutor/* to /tutor/* (strip /api prefix for tutor routes)
      {
        source: '/api/tutor/:path*',
        destination: `${backendUrl}/tutor/:path*`,
      },
      // Proxy /api/* routes to backend (keep /api prefix for other API routes)
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
      // Proxy /auth/* routes to backend (for Google OAuth)
      {
        source: '/auth/:path*',
        destination: `${backendUrl}/auth/:path*`,
      },
      // Proxy /health/* routes to backend
      {
        source: '/health/:path*',
        destination: `${backendUrl}/health/:path*`,
      },
      // Proxy /institution/* routes directly (for login pages)
      {
        source: '/institution/:path*',
        destination: `${backendUrl}/institution/:path*`,
      },
      // Proxy /tutor/* routes directly (for login pages)
      {
        source: '/tutor/:path*',
        destination: `${backendUrl}/tutor/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
