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
 * This function MUST be called at runtime (not during build)
 */
function getApiBaseUrl(): string {
  // Only evaluate in browser context
  if (typeof window === 'undefined') {
    return ''; // SSR context: use relative paths
  }
  
  // Check if we're in production (not localhost)
  const isProduction = window.location.hostname !== 'localhost' && 
                       window.location.hostname !== '127.0.0.1';
  
  if (isProduction) {
    return ''; // Production: use relative paths through Next.js proxy
  }
  
  // Development: direct backend access
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
}

// Export as a getter to ensure runtime evaluation
export const API_BASE_URL = getApiBaseUrl();

// Log only in browser
if (typeof window !== 'undefined') {
  console.log('[API_CONFIG] Environment:', window.location.hostname);
  console.log('[API_CONFIG] Using API_BASE_URL:', API_BASE_URL || '(relative paths)');
}
