import { NextRequest, NextResponse } from 'next/server';
import { getApiUrl } from '@/lib/api-utils';

const API_URL = getApiUrl();

export async function POST(req: NextRequest) {
  try {
    // Get the Stripe signature from the request headers
    const signature = req.headers.get('stripe-signature');
    
    if (!signature) {
      return NextResponse.json(
        { error: 'Stripe signature is missing' },
        { status: 400 }
      );
    }

    // Get the raw request body
    const rawBody = await req.text();

    // Forward the webhook to the backend API
    const response = await fetch(`${API_URL}/api/stripe/webhook`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'stripe-signature': signature
      },
      body: rawBody
    });

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(
        { error: errorData.detail || 'Failed to process webhook' },
        { status: response.status }
      );
    }

    return NextResponse.json({ received: true });
  } catch (error) {
    console.error('Error processing webhook:', error);
    return NextResponse.json(
      { error: 'An unexpected error occurred' },
      { status: 500 }
    );
  }
}

// Configure the API route to accept raw body
export const config = {
  api: {
    bodyParser: false,
  },
};
