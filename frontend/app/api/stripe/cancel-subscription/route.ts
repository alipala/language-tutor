import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { getApiUrl } from '@/lib/api-utils';

const API_URL = getApiUrl();


export async function POST(req: NextRequest) {
  try {
    console.log('[CANCEL-SUBSCRIPTION] Starting subscription cancellation...');
    
    // Get the token from the cookies or request headers
    const cookieStore = cookies();
    const authHeader = req.headers.get('authorization');
    let token: string | null = authHeader ? authHeader.split(' ')[1] : null;
    
    // If no token in header, try to get from cookies
    if (!token) {
      const tokenCookie = cookieStore.get('token');
      token = tokenCookie ? tokenCookie.value : null;
    }
    
    console.log('[CANCEL-SUBSCRIPTION] Token found:', !!token);
    
    if (!token) {
      console.log('[CANCEL-SUBSCRIPTION] No token found, returning 401');
      return NextResponse.json(
        { error: 'You must be logged in to cancel your subscription' },
        { status: 401 }
      );
    }

    console.log('[CANCEL-SUBSCRIPTION] Calling backend API:', `${API_URL}/api/stripe/cancel-subscription`);

    // Cancel the subscription by calling the backend API
    const response = await fetch(`${API_URL}/api/stripe/cancel-subscription`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });

    console.log('[CANCEL-SUBSCRIPTION] Backend response status:', response.status);

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch (e) {
        errorData = { detail: 'Failed to parse error response' };
      }
      
      console.log('[CANCEL-SUBSCRIPTION] Backend error:', errorData);
      
      return NextResponse.json(
        { error: errorData.detail || 'Failed to cancel subscription' },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('[CANCEL-SUBSCRIPTION] Success');
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('[CANCEL-SUBSCRIPTION] Error canceling subscription:', error);
    return NextResponse.json(
      { error: 'An unexpected error occurred while canceling the subscription' },
      { status: 500 }
    );
  }
}
