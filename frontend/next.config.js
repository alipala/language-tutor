/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false, // Prevent double rendering in production
  swcMinify: true,
  // Disable static export due to API routes with dynamic exports
  // output: 'export', // Cannot use with API routes that have dynamic exports
  // distDir: 'out', // Use default .next directory
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
}

module.exports = nextConfig
