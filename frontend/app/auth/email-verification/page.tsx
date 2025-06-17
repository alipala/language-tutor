'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

export default function EmailVerificationPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isVerifying, setIsVerifying] = useState(true);
  const [verificationStatus, setVerificationStatus] = useState<'loading' | 'success' | 'error'>('loading');

  useEffect(() => {
    const token = searchParams.get('token');
    
    if (!token) {
      setVerificationStatus('error');
      setIsVerifying(false);
      return;
    }

    verifyEmail(token);
  }, [searchParams]);

  const verifyEmail = async (token: string) => {
    try {
      console.log('[FRONTEND] Starting email verification with token:', token.substring(0, 10) + '...');
      
      const response = await fetch('/auth/verify-email', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
      });

      console.log('[FRONTEND] Verification response status:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('[FRONTEND] Verification successful:', data);
        
        setVerificationStatus('success');
        
        // Redirect to login page after 3 seconds
        setTimeout(() => {
          router.push('/auth/login?verified=true');
        }, 3000);
      } else {
        const errorData = await response.json();
        console.error('[FRONTEND] Verification failed:', errorData);
        
        setVerificationStatus('error');
      }
    } catch (error) {
      console.error('[FRONTEND] Verification error:', error);
      setVerificationStatus('error');
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#4ECFBF] via-[#3a9e92] to-[#2d7a6e] flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md text-center">
        <div className="mb-6">
          {verificationStatus === 'loading' && (
            <>
              <div className="w-16 h-16 border-4 border-[#4ECFBF] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <h1 className="text-2xl font-bold text-gray-800 mb-2">Verifying Email</h1>
              <p className="text-gray-600">Please wait while we verify your email address...</p>
            </>
          )}
          
          {verificationStatus === 'success' && (
            <>
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-green-800 mb-2">Email Verified!</h1>
              <p className="text-gray-600">Your email has been successfully verified. Redirecting to login...</p>
            </>
          )}
          
          {verificationStatus === 'error' && (
            <>
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-red-800 mb-2">Verification Failed</h1>
              <p className="text-gray-600 mb-4">The verification link is invalid or has expired.</p>
              <button
                onClick={() => router.push('/auth/login')}
                className="bg-[#4ECFBF] text-white px-6 py-2 rounded-lg hover:bg-[#3a9e92] transition-colors"
              >
                Go to Login
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
