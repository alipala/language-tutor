/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false, // Changed to false to prevent double rendering in production
  swcMinify: true,
  // Changed from 'export' to standalone to support proper routing in Railway
  output: 'standalone',
  distDir: '.next',
  // Removed outDir as it's not compatible with standalone output
  trailingSlash: false, // Changed to false to prevent redirect loops
  // Remove the rewrites since we're handling routing in Express
  env: {
    BACKEND_URL: process.env.NODE_ENV === 'production'
      ? process.env.BACKEND_URL || ''
      : 'http://localhost:8001',
  },
  // Disable image optimization since it requires a server component
  images: {
    unoptimized: true,
  },
}

module.exports = nextConfig
