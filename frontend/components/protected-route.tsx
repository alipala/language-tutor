'use client';

import { useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';

interface ProtectedRouteProps {
  children: ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const router = useRouter();
  const { user, loading } = useAuth();

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

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
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
