/**
 * API Configuration for Frontend
 * Copied from working main branch implementation (frontend/lib/api-utils.ts)
 * 
 * In production (Railway/mytacoai.com):
 * - Use empty string '' for relative paths
 * - Next.js proxy will forward /api/* to backend
 * 
 * In development:
 * - Use http://localhost:8000 for direct backend access
 */

/**
 * Get the API base URL based on the current environment
 * This function MUST be called at runtime in the browser for each request
 */
export function getApiBaseUrl(): string {
  // Check if we're in a browser
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    // If we're on Railway or custom domain, use /api prefix for Next.js proxy
    if (hostname.includes('railway.app') || hostname === 'mytacoai.com') {
      console.log(`Detected production deployment on ${hostname}, using /api prefix for Next.js proxy`);
      return '/api';
    }
    // If we're not on localhost, use /api prefix
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      console.log(`Detected production hostname ${hostname}, using /api prefix`);
      return '/api';
    }
  }
  // Default to environment variable or localhost
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
}

// For backward compatibility - but this evaluates at module load time
// Components should preferably call getApiBaseUrl() directly
export const API_BASE_URL = getApiBaseUrl();
