/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: 'export', // Static HTML export
  distDir: '.next',
  outDir: 'out', // Explicitly set the output directory
  trailingSlash: true, // Add trailing slashes to all URLs
  // Remove the rewrites since we're handling routing in Express
  env: {
    BACKEND_URL: process.env.NODE_ENV === 'production'
      ? process.env.BACKEND_URL || ''
      : 'http://localhost:3001',
  },
  // Disable image optimization since it requires a server component
  images: {
    unoptimized: true,
  },
}

module.exports = nextConfig
