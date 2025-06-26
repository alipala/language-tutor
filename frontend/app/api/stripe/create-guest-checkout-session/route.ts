import { NextRequest, NextResponse } from 'next/server';
import { getApiUrl } from '@/lib/api-utils';

const API_URL = getApiUrl();

// Force dynamic rendering for this route
export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    console.log('[GUEST-CHECKOUT] Starting guest checkout session creation...');
    
    // Parse the request body
    const body = await req.json();
    const { price_id, success_url, cancel_url } = body;

    console.log('[GUEST-CHECKOUT] Request data:', { price_id, success_url, cancel_url });

    if (!price_id) {
      console.log('[GUEST-CHECKOUT] Missing price_id');
      return NextResponse.json(
        { error: 'Price ID is required' },
        { status: 400 }
      );
    }

    const backendUrl = `${API_URL}/api/stripe/create-guest-checkout-session`;
    console.log('[GUEST-CHECKOUT] Calling backend API:', backendUrl);

    // Ensure URLs have proper schemes for Stripe
    const baseUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
    const defaultSuccessUrl = `${baseUrl}/auth/signup?checkout=success`;
    const defaultCancelUrl = `${baseUrl}/#pricing`;

    // Create the guest checkout session by calling the backend API
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        price_id,
        success_url: success_url || defaultSuccessUrl,
        cancel_url: cancel_url || defaultCancelUrl
      })
    });

    console.log('[GUEST-CHECKOUT] Backend response status:', response.status);

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch (e) {
        errorData = { detail: 'Failed to parse error response' };
      }
      
      console.log('[GUEST-CHECKOUT] Backend error:', errorData);
      
      return NextResponse.json(
        { error: errorData.detail || 'Failed to create guest checkout session' },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('[GUEST-CHECKOUT] Success, returning checkout URL');
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('[GUEST-CHECKOUT] Error creating guest checkout session:', error);
    return NextResponse.json(
      { error: 'An unexpected error occurred' },
      { status: 500 }
    );
  }
}
