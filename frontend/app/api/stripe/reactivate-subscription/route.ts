import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { getApiUrl } from '@/lib/api-utils';

const API_URL = getApiUrl();


export async function POST(req: NextRequest) {
  try {
    console.log('[REACTIVATE-SUBSCRIPTION] Starting subscription reactivation...');
    
    // Get the token from the cookies or request headers
    const cookieStore = cookies();
    const authHeader = req.headers.get('authorization');
    let token: string | null = authHeader ? authHeader.split(' ')[1] : null;
    
    // If no token in header, try to get from cookies
    if (!token) {
      const tokenCookie = cookieStore.get('token');
      token = tokenCookie ? tokenCookie.value : null;
    }
    
    console.log('[REACTIVATE-SUBSCRIPTION] Token found:', !!token);
    
    if (!token) {
      console.log('[REACTIVATE-SUBSCRIPTION] No token found, returning 401');
      return NextResponse.json(
        { error: 'You must be logged in to reactivate your subscription' },
        { status: 401 }
      );
    }

    console.log('[REACTIVATE-SUBSCRIPTION] Calling backend API:', `${API_URL}/api/stripe/reactivate-subscription`);

    // Reactivate the subscription by calling the backend API
    const response = await fetch(`${API_URL}/api/stripe/reactivate-subscription`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });

    console.log('[REACTIVATE-SUBSCRIPTION] Backend response status:', response.status);

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch (e) {
        errorData = { detail: 'Failed to parse error response' };
      }
      
      console.log('[REACTIVATE-SUBSCRIPTION] Backend error:', errorData);
      
      return NextResponse.json(
        { error: errorData.detail || 'Failed to reactivate subscription' },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('[REACTIVATE-SUBSCRIPTION] Success');
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('[REACTIVATE-SUBSCRIPTION] Error reactivating subscription:', error);
    return NextResponse.json(
      { error: 'An unexpected error occurred while reactivating the subscription' },
      { status: 500 }
    );
  }
}
