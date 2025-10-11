/**
 * Health check utility for verifying backend connectivity
 * Helps ensure reliable operation in Railway deployment
 */

/**
 * Response structure from the health check endpoint
 * Updated to match the actual backend response format
 */
export interface HealthCheckResponse {
  status: string;
  timestamp: number;
  environment: string;
  railway: boolean;
  port: string;
  service: string;
  python_version: string;
  openai_configured: boolean;
  mongodb_configured: boolean;
  error?: string;
}

/**
 * Legacy response structure for backward compatibility
 */
export interface LegacyHealthCheckResponse {
  status: string;
  version: string;
  uptime: number;
  system_info: {
    python_version: string;
    platform: string;
    timestamp: number;
    environment: string;
    railway: boolean;
  };
  api_routes: string[];
}

/**
 * Determine the correct API URL based on environment
 */
function getApiUrl(baseUrl?: string): string {
  if (baseUrl) {
    return baseUrl;
  }
  
  // Use environment variable if available
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  // Server-side rendering: use backend URL from environment
  if (typeof window === 'undefined') {
    // During SSR, use the backend URL from environment
    return process.env.BACKEND_URL || 'http://127.0.0.1:8000';
  }
  
  // Client-side: Handle localhost and 127.0.0.1 cases
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://127.0.0.1:8000';
  }
  
  // For production, try to use the same origin
  if (hostname === 'mytacoai.com') {
    return 'https://mytacoai.com';
  }
  
  // For Railway deployment
  if (hostname.includes('railway.app')) {
    return `https://${hostname}`;
  }
  
  // Default fallback for client-side
  return 'http://127.0.0.1:8000';
}

/**
 * Check if the backend API is available and healthy
 * @param baseUrl - The base URL of the backend API
 * @returns Promise with health check data or error
 */
export async function checkBackendHealth(baseUrl?: string): Promise<HealthCheckResponse> {
  const apiUrl = getApiUrl(baseUrl);
  
  // Add retry logic for better reliability
  let retries = 0;
  const maxRetries = 3;
  
  while (retries < maxRetries) {
    try {
      console.log(`[HEALTH_CHECK] Attempt ${retries + 1}/${maxRetries} to ${apiUrl}/api/health`);
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      const response = await fetch(`${apiUrl}/api/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache'
        },
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`Health check failed with status: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('[HEALTH_CHECK] Backend health check successful:', data);
      
      // Validate the response structure and provide defaults for missing fields
      const healthResponse: HealthCheckResponse = {
        status: data.status || 'unknown',
        timestamp: data.timestamp || Date.now(),
        environment: data.environment || 'unknown',
        railway: data.railway || false,
        port: data.port || '8000',
        service: data.service || 'language-tutor-backend',
        python_version: data.python_version || '3.11',
        openai_configured: data.openai_configured || false,
        mongodb_configured: data.mongodb_configured || false,
        error: data.error
      };
      
      return healthResponse;
    } catch (error) {
      console.error(`[HEALTH_CHECK] Attempt ${retries + 1} failed:`, error);
      retries++;
      
      if (retries >= maxRetries) {
        console.error('[HEALTH_CHECK] All attempts failed, throwing error');
        throw new Error(`Backend health check failed after ${maxRetries} attempts: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
      
      // Wait before retrying (exponential backoff)
      const delay = 1000 * Math.pow(2, retries - 1);
      console.log(`[HEALTH_CHECK] Waiting ${delay}ms before retry...`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  // This should never be reached due to the throw in the loop
  throw new Error('Backend health check failed');
}

/**
 * Verify that the backend is available and properly configured
 * @returns Promise that resolves when the backend is verified or rejects with an error
 */
export async function verifyBackendConnectivity(): Promise<boolean> {
  try {
    console.log('[CONNECTIVITY] Starting backend connectivity verification...');
    const health = await checkBackendHealth();
    
    // Check if the backend is healthy
    if (health.status !== 'ok') {
      console.error('[CONNECTIVITY] Backend status is not ok:', health.status);
      if (health.error) {
        console.error('[CONNECTIVITY] Backend error:', health.error);
      }
      return false;
    }
    
    // Check if we're in the expected environment
    const isProduction = typeof window !== 'undefined' && 
      window.location.hostname !== 'localhost' && 
      window.location.hostname !== '127.0.0.1';
    
    const backendIsProduction = health.environment === 'production';
    
    // Log environment information
    console.log('[CONNECTIVITY] Environment check:', {
      frontend: isProduction ? 'production' : 'development',
      backend: backendIsProduction ? 'production' : 'development',
      railway: health.railway,
      service: health.service,
      port: health.port
    });
    
    // Log a warning if there's an environment mismatch (but don't fail)
    if (isProduction !== backendIsProduction) {
      console.warn('[CONNECTIVITY] Environment mismatch detected (this is usually fine):', {
        frontend: isProduction ? 'production' : 'development',
        backend: backendIsProduction ? 'production' : 'development'
      });
    }
    
    // Check critical services
    if (!health.openai_configured) {
      console.warn('[CONNECTIVITY] OpenAI is not configured - some features may not work');
    }
    
    if (!health.mongodb_configured) {
      console.warn('[CONNECTIVITY] MongoDB is not configured - user features may not work');
    }
    
    console.log('[CONNECTIVITY] ✅ Backend connectivity verification successful');
    return true;
  } catch (error) {
    console.error('[CONNECTIVITY] ❌ Backend connectivity verification failed:', error);
    
    // Provide more detailed error information
    if (error instanceof Error) {
      if (error.message.includes('fetch')) {
        console.error('[CONNECTIVITY] Network error - backend may be down or unreachable');
      } else if (error.message.includes('timeout')) {
        console.error('[CONNECTIVITY] Timeout error - backend is responding slowly');
      } else if (error.message.includes('CORS')) {
        console.error('[CONNECTIVITY] CORS error - check backend CORS configuration');
      }
    }
    
    return false;
  }
}

/**
 * Enhanced connectivity check with fallback mechanisms
 * @param showUserFeedback - Whether to show user-facing error messages
 * @returns Promise with detailed connectivity status
 */
export async function enhancedConnectivityCheck(showUserFeedback: boolean = false): Promise<{
  connected: boolean;
  health?: HealthCheckResponse;
  error?: string;
  fallbackAvailable?: boolean;
}> {
  try {
    console.log('[ENHANCED_CONNECTIVITY] Starting enhanced connectivity check...');
    
    const health = await checkBackendHealth();
    
    return {
      connected: true,
      health,
      fallbackAvailable: false
    };
  } catch (error) {
    console.error('[ENHANCED_CONNECTIVITY] Primary connectivity check failed:', error);
    
    // Try alternative endpoints
    const fallbackEndpoints = ['/health', '/api/test'];
    
    for (const endpoint of fallbackEndpoints) {
      try {
        console.log(`[ENHANCED_CONNECTIVITY] Trying fallback endpoint: ${endpoint}`);
        
        const apiUrl = getApiUrl();
        const response = await fetch(`${apiUrl}${endpoint}`, {
          method: 'GET',
          headers: { 'Cache-Control': 'no-cache' }
        });
        
        if (response.ok) {
          console.log(`[ENHANCED_CONNECTIVITY] ✅ Fallback endpoint ${endpoint} responded`);
          return {
            connected: true,
            fallbackAvailable: true,
            error: `Primary health check failed, but ${endpoint} is responding`
          };
        }
      } catch (fallbackError) {
        console.log(`[ENHANCED_CONNECTIVITY] Fallback endpoint ${endpoint} failed:`, fallbackError);
      }
    }
    
    const errorMessage = error instanceof Error ? error.message : 'Unknown connectivity error';
    
    if (showUserFeedback) {
      // Could trigger user notification here
      console.error('[ENHANCED_CONNECTIVITY] All connectivity checks failed - user should be notified');
    }
    
    return {
      connected: false,
      error: errorMessage,
      fallbackAvailable: false
    };
  }
}
