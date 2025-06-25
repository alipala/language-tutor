import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { getApiUrl } from '@/lib/api-utils';

const API_URL = getApiUrl();

export async function GET(req: NextRequest) {
  try {
    // Get the token from the cookies or request headers
    const cookieStore = cookies();
    const authHeader = req.headers.get('authorization');
    let token: string | null = authHeader ? authHeader.split(' ')[1] : null;
    
    // If no token in header, try to get from cookies
    if (!token) {
      const tokenCookie = cookieStore.get('token');
      token = tokenCookie ? tokenCookie.value : null;
    }
    
    if (!token) {
      return NextResponse.json(
        { error: 'You must be logged in to check subscription status' },
        { status: 401 }
      );
    }

    // Get the subscription status by calling the backend API
    const response = await fetch(`${API_URL}/api/stripe/subscription-status`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(
        { error: errorData.detail || 'Failed to fetch subscription status' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching subscription status:', error);
    return NextResponse.json(
      { error: 'An unexpected error occurred' },
      { status: 500 }
    );
  }
}
