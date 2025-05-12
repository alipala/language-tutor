'use client';

import { ReactNode, useState, useEffect } from 'react';
import { AuthProvider } from '@/lib/auth';
import { NotificationProvider } from '@/components/ui/notification';

export default function AuthProviderWrapper({ children }: { children: ReactNode }) {
  const [error, setError] = useState<string | null>(null);
  const [isRailway, setIsRailway] = useState(false);
  
  // Add error handling for Railway deployment
  useEffect(() => {
    // Check if we're in Railway environment
    const hostname = typeof window !== 'undefined' ? window.location.hostname : '';
    const isRailwayEnv = hostname.includes('railway.app');
    setIsRailway(isRailwayEnv);
    
    console.log('Auth Provider Wrapper mounted in environment:', isRailwayEnv ? 'Railway' : 'Local');
    
    // Add global error handler
    const handleError = (event: ErrorEvent) => {
      console.error('Global error caught:', event.error);
      setError(event.message || 'An unexpected error occurred');
      
      // Prevent the white screen by showing at least an error message
      if (isRailwayEnv && document.body.innerHTML.trim() === '') {
        const errorDiv = document.createElement('div');
        errorDiv.style.padding = '20px';
        errorDiv.style.margin = '20px';
        errorDiv.style.backgroundColor = '#f8d7da';
        errorDiv.style.color = '#721c24';
        errorDiv.style.borderRadius = '4px';
        errorDiv.innerHTML = `
          <h2>Your Smart Language Coach - Error Recovery</h2>
          <p>We encountered an error while loading the application.</p>
          <p>Error: ${event.message || 'Unknown error'}</p>
          <button onclick="window.location.href='/'">Try Again</button>
        `;
        document.body.appendChild(errorDiv);
      }
      
      return false;
    };
    
    window.addEventListener('error', handleError);
    
    return () => {
      window.removeEventListener('error', handleError);
    };
  }, []);
  
  // Render error fallback if there's an error
  if (error && isRailway) {
    return (
      <div style={{
        padding: '20px',
        margin: '20px',
        backgroundColor: '#f8d7da',
        color: '#721c24',
        borderRadius: '4px'
      }}>
        <h2>Your Smart Language Coach - Error Recovery</h2>
        <p>We encountered an error while loading the application.</p>
        <p>Error: {error}</p>
        <button onClick={() => window.location.href = '/'}>Try Again</button>
      </div>
    );
  }
  
  // Normal rendering path
  return (
    <AuthProvider>
      <NotificationProvider>
        {children}
      </NotificationProvider>
    </AuthProvider>
  );
}
