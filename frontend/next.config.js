/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false, // Prevent double rendering in production
  swcMinify: true,
  output: 'standalone',
  distDir: '.next',
  trailingSlash: false, // Prevent redirect loops
  // Configure basePath for Railway deployment
  basePath: '',
  // Ensure Next.js knows it's being served from the root
  assetPrefix: process.env.NODE_ENV === 'production' ? '' : undefined,
  // Environment variables
  env: {
    BACKEND_URL: process.env.NODE_ENV === 'production'
      ? process.env.BACKEND_URL || ''
      : 'http://localhost:8001',
  },
  // Disable image optimization since it requires a server component
  images: {
    unoptimized: true,
  },
  // Explicitly set the output file tracing to include the entire frontend directory
  experimental: {
    outputFileTracingRoot: require('path').join(__dirname, '../'),
  },
}

module.exports = nextConfig
