'use client';

import { useEffect, useRef, useState } from 'react';
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
  const [googleClientId, setGoogleClientId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Fetch Google Client ID from the API
  useEffect(() => {
    async function fetchConfig() {
      try {
        setIsLoading(true);
        // Use relative URL to work in both development and production
        const response = await fetch('/api/config');
        
        if (!response.ok) {
          throw new Error(`Failed to fetch config: ${response.status}`);
        }
        
        const config = await response.json();
        console.log('Fetched config from API:', config);
        
        if (config.googleClientId) {
          setGoogleClientId(config.googleClientId);
        } else {
          setError('Google Client ID not found in API response');
        }
      } catch (err) {
        console.error('Error fetching config:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setIsLoading(false);
      }
    }
    
    fetchConfig();
  }, []);
  
  // Initialize Google Sign-In when client ID is available
  useEffect(() => {
    if (!googleClientId) {
      return;
    }
    
    // Initialize Google Sign-In
    if (window.google && buttonRef.current && googleClientId) {
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
  
  // Show loading state
  if (isLoading) {
    return (
      <div 
        className="w-full flex items-center justify-center px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-slate-700"
        style={{ height: '44px' }}
      >
        <svg className="animate-spin h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span>Loading Google Sign-In...</span>
      </div>
    );
  }
  
  // If error or no Google client ID is available, show a fallback button
  if (error || !googleClientId) {
    return (
      <div 
        className={`w-full flex items-center justify-center px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-slate-700 ${disabled ? 'opacity-50 pointer-events-none' : ''}`}
        style={{ height: '44px' }}
      >
        <svg className="h-5 w-5 mr-2" viewBox="0 0 24 24" width="24" height="24">
          <g transform="matrix(1, 0, 0, 1, 27.009001, -39.238998)">
            <path fill="#4285F4" d="M -3.264 51.509 C -3.264 50.719 -3.334 49.969 -3.454 49.239 L -14.754 49.239 L -14.754 53.749 L -8.284 53.749 C -8.574 55.229 -9.424 56.479 -10.684 57.329 L -10.684 60.329 L -6.824 60.329 C -4.564 58.239 -3.264 55.159 -3.264 51.509 Z" />
            <path fill="#34A853" d="M -14.754 63.239 C -11.514 63.239 -8.804 62.159 -6.824 60.329 L -10.684 57.329 C -11.764 58.049 -13.134 58.489 -14.754 58.489 C -17.884 58.489 -20.534 56.379 -21.484 53.529 L -25.464 53.529 L -25.464 56.619 C -23.494 60.539 -19.444 63.239 -14.754 63.239 Z" />
            <path fill="#FBBC05" d="M -21.484 53.529 C -21.734 52.809 -21.864 52.039 -21.864 51.239 C -21.864 50.439 -21.724 49.669 -21.484 48.949 L -21.484 45.859 L -25.464 45.859 C -26.284 47.479 -26.754 49.299 -26.754 51.239 C -26.754 53.179 -26.284 54.999 -25.464 56.619 L -21.484 53.529 Z" />
            <path fill="#EA4335" d="M -14.754 43.989 C -12.984 43.989 -11.404 44.599 -10.154 45.789 L -6.734 42.369 C -8.804 40.429 -11.514 39.239 -14.754 39.239 C -19.444 39.239 -23.494 41.939 -25.464 45.859 L -21.484 48.949 C -20.534 46.099 -17.884 43.989 -14.754 43.989 Z" />
          </g>
        </svg>
        <span>Google Sign-In unavailable</span>
      </div>
    );
  }
  
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
