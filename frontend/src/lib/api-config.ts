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
  // Always use the Next.js proxy — avoids CORS preflight (OPTIONS) requests
  // The proxy in next.config.js forwards /api/* and /institution/* to the backend
  return '';
}

// For backward compatibility - but this evaluates at module load time
// Components should preferably call getApiBaseUrl() directly
export const API_BASE_URL = getApiBaseUrl();
