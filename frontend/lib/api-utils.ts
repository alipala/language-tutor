// Function to determine the API URL based on environment
export function getApiUrl(): string {
  // Check if we're in a browser
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    // If we're on Railway or custom domain, use empty string (same domain)
    if (hostname.includes('railway.app') || hostname === 'mytacoai.com') {
      console.log(`Detected production deployment on ${hostname}, using same-origin API URL`);
      return '';
    }
    // If we're not on localhost, use the same origin for API calls
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      console.log(`Detected production hostname ${hostname}, using same-origin API URL`);
      return window.location.origin;
    }
  }
  // Default to environment variable or localhost
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
}
