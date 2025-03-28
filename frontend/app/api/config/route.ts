import { NextResponse } from 'next/server';

export async function GET() {
  // Get environment variables
  const config = {
    googleClientId: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || process.env.GOOGLE_CLIENT_ID || '',
  };
  
  // Log for debugging
  console.log('API Config endpoint called, returning:', config);
  
  // Return the configuration
  return NextResponse.json(config);
}
