export async function shortenImageUrl(openaiImageUrl: string): Promise<string> {
  try {
    console.log('[IMAGE_SHORTENER] Shortening URL:', openaiImageUrl);
    
    // Determine the API base URL
    const apiUrl = process.env.NODE_ENV === 'production' 
      ? 'https://mytacoai.com' 
      : 'http://localhost:8000';
    
    const response = await fetch(`${apiUrl}/api/shorten-image`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        // Add CORS headers for development
        ...(process.env.NODE_ENV !== 'production' && {
          'Access-Control-Allow-Origin': '*'
        })
      },
      body: JSON.stringify({ url: openaiImageUrl })
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('[IMAGE_SHORTENER] HTTP error:', response.status, errorText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('[IMAGE_SHORTENER] ✅ Success:', data);
    
    return data.short_url;
  } catch (error) {
    console.error('[IMAGE_SHORTENER] ❌ Error shortening image URL:', error);
    // Fallback to original URL if shortening fails
    return openaiImageUrl;
  }
}

// Helper function to get API URL consistently
export function getApiUrl(): string {
  return process.env.NODE_ENV === 'production' 
    ? 'https://mytacoai.com' 
    : 'http://localhost:8000';
}
