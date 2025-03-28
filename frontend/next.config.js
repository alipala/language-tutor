/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false, // Prevent double rendering in production
  swcMinify: true,
  output: 'standalone', // Required for proper server-side rendering on Railway
  distDir: '.next',
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
    NEXT_PUBLIC_GOOGLE_CLIENT_ID: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID,
  },
  // Disable image optimization since it requires a server component
  images: {
    unoptimized: true,
  },
  // Explicitly set the output file tracing to include the entire frontend directory
  experimental: {
    outputFileTracingRoot: require('path').join(__dirname, '../'),
  },
  // Improve static generation for Railway
  poweredByHeader: false,
  // Increase the timeout for generating static pages
  staticPageGenerationTimeout: 180,
  // Compress responses for better performance
  compress: true,
}

module.exports = nextConfig
