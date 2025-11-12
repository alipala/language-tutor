'use client';

import React, { createContext, useContext, ReactNode, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { navigationService } from './navigation-service-nextjs';

// Create the context
const NavigationContext = createContext(navigationService);

/**
 * Provider component for the navigation service
 * PERFORMANCE OPTIMIZED: Initializes Next.js router for client-side navigation
 */
export function NavigationProvider({ children }: { children: ReactNode }) {
  const router = useRouter();

  useEffect(() => {
    // Initialize the navigation service with Next.js router
    navigationService.initialize(router);
  }, [router]);

  return (
    <NavigationContext.Provider value={navigationService}>
      {children}
    </NavigationContext.Provider>
  );
}

/**
 * Hook to use the navigation service
 */
export function useNavigation() {
  return useContext(NavigationContext);
}
