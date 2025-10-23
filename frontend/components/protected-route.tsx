'use client';

import { useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import SoundWaveLoader from '@/components/sound-wave-loader';

interface ProtectedRouteProps {
  children: ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [showLoader, setShowLoader] = useState(false);

  useEffect(() => {
    // Only check after auth has loaded
    if (!loading) {
      if (!user) {
        // User is not authenticated, redirect to login
        console.log('User not authenticated, redirecting to login');
        
        // Use direct window.location.href for reliable navigation in Railway
        const fullUrl = `${window.location.origin}/auth/login`;
        window.location.href = fullUrl;
      }
    }
  }, [user, loading, router]);

  // Delay showing loader to avoid flash for fast auth checks
  useEffect(() => {
    if (loading) {
      // Only show loader if loading takes more than 100ms
      const timer = setTimeout(() => {
        setShowLoader(true);
      }, 100);
      
      return () => clearTimeout(timer);
    } else {
      setShowLoader(false);
    }
  }, [loading]);

  // Show loading state only if it's taking a while
  if (loading && showLoader) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
        <SoundWaveLoader 
          size="lg"
          color="#4ECFBF"
          text="Authenticating..."
          subtext="Verifying your account access"
        />
      </div>
    );
  }

  // If not authenticated, show nothing (will redirect)
  if (!user && !loading) {
    return null;
  }

  // User is authenticated, render children
  return <>{children}</>;
}
