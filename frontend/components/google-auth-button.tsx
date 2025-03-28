'use client';

import { useEffect, useRef } from 'react';
import { useAuth } from '@/lib/auth';

interface GoogleAuthButtonProps {
  onSuccess?: () => void;
  onError?: (error: Error) => void;
  disabled?: boolean;
}

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: any) => void;
          renderButton: (element: HTMLElement, options: any) => void;
          prompt: () => void;
        };
      };
    };
  }
}

export default function GoogleAuthButton({ 
  onSuccess, 
  onError,
  disabled = false 
}: GoogleAuthButtonProps) {
  const { googleLogin } = useAuth();
  const buttonRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    // Get Google client ID from environment variable
    const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    
    if (!googleClientId) {
      console.error('Google Client ID not found in environment variables');
      return;
    }
    
    // Initialize Google Sign-In
    if (window.google && buttonRef.current) {
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: async (response: any) => {
          try {
            // Get the ID token from the response
            const { credential } = response;
            
            // Store navigation intent in sessionStorage before authentication
            sessionStorage.setItem('pendingRedirect', 'true');
            sessionStorage.setItem('redirectTarget', '/language-selection');
            sessionStorage.setItem('redirectAttemptTime', Date.now().toString());
            
            // Call the googleLogin function from auth context
            await googleLogin(credential);
            
            // Call onSuccess callback if provided
            if (onSuccess) {
              onSuccess();
            }
            
            // Force hard navigation to avoid client-side routing issues in Railway
            console.log('Google login successful, forcing navigation');
            window.location.href = '/language-selection';
            
            // Safety net: if we're still on this page after 1.5 seconds, force navigation again
            setTimeout(() => {
              if (window.location.pathname.includes('auth/login') || 
                  window.location.pathname.includes('auth/signup')) {
                console.log('Safety net navigation triggered for Google login');
                window.location.href = '/language-selection';
              }
            }, 1500);
          } catch (error) {
            console.error('Google login error:', error);
            // Call onError callback if provided
            if (onError && error instanceof Error) {
              onError(error);
            }
            
            // Clear navigation intent on error
            sessionStorage.removeItem('pendingRedirect');
            sessionStorage.removeItem('redirectTarget');
            sessionStorage.removeItem('redirectAttemptTime');
          }
        },
        auto_select: false
      });
    }
  }, [googleLogin, onSuccess, onError]);
  
  // Render the Google Sign-In button after component mounts
  useEffect(() => {
    // Check if Google SDK is loaded and button ref exists
    if (window.google && buttonRef.current) {
      // Small delay to ensure the parent width is calculated correctly
      setTimeout(() => {
        // Safe check for window.google again after timeout
        if (window.google && buttonRef.current) {
          const buttonWidth = buttonRef.current.clientWidth || 300;
          window.google.accounts.id.renderButton(buttonRef.current, {
            type: 'standard',
            theme: 'outline',
            size: 'large',
            text: 'continue_with',
            shape: 'rectangular',
            logo_alignment: 'left',
            width: buttonWidth // Match parent width
          });
        }
      }, 100);
    }
  }, []);
  
  return (
    <div 
      ref={buttonRef} 
      className={`google-login-button w-full ${disabled ? 'opacity-50 pointer-events-none' : ''}`}
      style={{ 
        display: 'flex', 
        justifyContent: 'center',
        height: '44px', // Match the height of the sign-in button
        borderRadius: '0.5rem' // Match the border radius of the sign-in button
      }}
    />
  );
}
