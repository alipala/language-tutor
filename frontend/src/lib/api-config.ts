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

export const API_BASE_URL = 
  typeof window !== 'undefined' && window.location.hostname !== 'localhost'
    ? '' // Production: use relative paths through Next.js proxy
    : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'); // Development: direct backend

console.log('[API_CONFIG] Using API_BASE_URL:', API_BASE_URL || '(relative paths)');
