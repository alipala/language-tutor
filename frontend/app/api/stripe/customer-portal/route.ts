import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { getApiUrl } from '@/lib/api-utils';

const API_URL = getApiUrl();


export async function POST(req: NextRequest) {
  try {
    console.log('[CUSTOMER-PORTAL] Starting customer portal session creation...');
    
    // Get the token from the cookies or request headers
    const cookieStore = cookies();
    const authHeader = req.headers.get('authorization');
    let token: string | null = authHeader ? authHeader.split(' ')[1] : null;
    
    // If no token in header, try to get from cookies
    if (!token) {
      const tokenCookie = cookieStore.get('token');
      token = tokenCookie ? tokenCookie.value : null;
    }
    
    console.log('[CUSTOMER-PORTAL] Token found:', !!token);
    
    if (!token) {
      console.log('[CUSTOMER-PORTAL] No token found, returning 401');
      return NextResponse.json(
        { error: 'You must be logged in to access the customer portal' },
        { status: 401 }
      );
    }

    // Parse the request body
    const body = await req.json();
    const { return_url } = body;
    
    console.log('[CUSTOMER-PORTAL] Return URL:', return_url);
    console.log('[CUSTOMER-PORTAL] Calling backend API:', `${API_URL}/api/stripe/customer-portal`);

    // Create the customer portal session by calling the backend API
    const response = await fetch(`${API_URL}/api/stripe/customer-portal`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        return_url: return_url || `${process.env.NEXT_PUBLIC_APP_URL}/profile`
      })
    });

    console.log('[CUSTOMER-PORTAL] Backend response status:', response.status);

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch (e) {
        errorData = { detail: 'Failed to parse error response' };
      }
      
      console.log('[CUSTOMER-PORTAL] Backend error:', errorData);
      
      // Provide user-friendly error messages
      let userMessage = errorData.detail || 'Failed to create customer portal session';
      
      if (response.status === 400 && errorData.detail?.includes('No subscription found')) {
        userMessage = 'You need an active subscription to access the customer portal. Please subscribe to a plan first.';
      }
      
      return NextResponse.json(
        { error: userMessage },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('[CUSTOMER-PORTAL] Success, returning portal URL');
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('[CUSTOMER-PORTAL] Error creating customer portal session:', error);
    return NextResponse.json(
      { error: 'An unexpected error occurred while creating the customer portal session' },
      { status: 500 }
    );
  }
}
