/**
 * API Configuration for Frontend
 * 
 * In production (Railway):
 * - Use empty string '' for relative paths
 * - Next.js proxy will forward /api/* to backend
 * 
 * In development:
 * - Use http://localhost:8000 for direct backend access
 */

/**
 * Get the API base URL based on the current environment
 * This function MUST be called at runtime in the browser for each request
 * IMPORTANT: Do NOT use process.env as it's baked in at build time!
 */
export function getApiBaseUrl(): string {
  // Only evaluate in browser context
  if (typeof window === 'undefined') {
    return ''; // SSR context: use relative paths
  }
  
  // Check if we're in production (not localhost)
  const isProduction = window.location.hostname !== 'localhost' && 
                       window.location.hostname !== '127.0.0.1';
  
  if (isProduction) {
    console.log('[API_CONFIG] Production detected, using relative paths through Next.js proxy');
    return ''; // Production: use relative paths through Next.js proxy
  }
  
  // Development: direct backend access - hardcoded, no env vars!
  console.log('[API_CONFIG] Development detected, using: http://localhost:8000');
  return 'http://localhost:8000';
}

// For backward compatibility - but this evaluates at module load time
// Components should preferably call getApiBaseUrl() directly
export const API_BASE_URL = getApiBaseUrl();
