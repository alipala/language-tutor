'use client';

import React, { createContext, useContext, ReactNode } from 'react';
import { navigationService } from './navigation-service';

// Create the context
const NavigationContext = createContext(navigationService);

/**
 * Provider component for the navigation service
 */
export function NavigationProvider({ children }: { children: ReactNode }) {
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
