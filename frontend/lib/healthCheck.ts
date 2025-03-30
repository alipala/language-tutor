/**
 * Health check utility for verifying backend connectivity
 * Helps ensure reliable operation in Railway deployment
 */

/**
 * Response structure from the health check endpoint
 */
export interface HealthCheckResponse {
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
 * Check if the backend API is available and healthy
 * @param baseUrl - The base URL of the backend API
 * @returns Promise with health check data or error
 */
export async function checkBackendHealth(baseUrl?: string): Promise<HealthCheckResponse> {
  // Determine the API URL based on the environment
  let apiUrl = baseUrl || '';
  
  // Handle localhost and 127.0.0.1 cases
  if (typeof window !== 'undefined') {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      apiUrl = 'http://localhost:8001';
    }
  }
  
  // Use environment variable if available
  if (process.env.NEXT_PUBLIC_API_URL) {
    apiUrl = process.env.NEXT_PUBLIC_API_URL;
  }
  
  // Add retry logic for better reliability
  let retries = 0;
  const maxRetries = 3;
  
  while (retries < maxRetries) {
    try {
      console.log(`Health check attempt ${retries + 1}/${maxRetries} to ${apiUrl}/api/health`);
      
      const response = await fetch(`${apiUrl}/api/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Health check failed with status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Backend health check successful:', data);
      return data as HealthCheckResponse;
    } catch (error) {
      console.error(`Health check attempt ${retries + 1} failed:`, error);
      retries++;
      
      if (retries >= maxRetries) {
        throw new Error('Backend health check failed after multiple attempts');
      }
      
      // Wait before retrying (exponential backoff)
      await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, retries)));
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
    const health = await checkBackendHealth();
    
    // Check if we're in the expected environment
    const isProduction = typeof window !== 'undefined' && 
      window.location.hostname !== 'localhost' && 
      window.location.hostname !== '127.0.0.1';
    
    const backendIsProduction = health.system_info.environment === 'production';
    
    // Log a warning if there's an environment mismatch
    if (isProduction !== backendIsProduction) {
      console.warn('Environment mismatch detected:', {
        frontend: isProduction ? 'production' : 'development',
        backend: backendIsProduction ? 'production' : 'development'
      });
    }
    
    return true;
  } catch (error) {
    console.error('Backend connectivity verification failed:', error);
    return false;
  }
}
