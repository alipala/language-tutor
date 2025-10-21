// Function to determine the API URL based on environment
export function getApiUrl(): string {
  // Check if we're in a browser
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    // If we're on Railway or custom domain, use empty string (same domain)
    if (hostname.includes('railway.app') || hostname === 'mytacoai.com') {
      console.log(`[API_UTILS] Detected production deployment on ${hostname}, using same-origin API URL`);
      return '';
    }
    // If we're not on localhost, use the same origin for API calls
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      console.log(`[API_UTILS] Detected production hostname ${hostname}, using same-origin API URL`);
      return '';
    }
  }
  // Default to environment variable or localhost
  const fallbackUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
  console.log(`[API_UTILS] Using fallback API URL: ${fallbackUrl}`);
  return fallbackUrl;
}
