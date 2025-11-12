'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, useRef, ReactNode } from 'react';
import { useAuth } from '@/lib/auth';

// Helper for development-only logging
const isDev = process.env.NODE_ENV === 'development';
const devLog = (message: string, ...args: any[]) => {
  if (isDev) {
    console.log(message, ...args);
  }
};

interface SubscriptionLimits {
  sessions_remaining: number;
  assessments_remaining: number;
  sessions_limit: number;
  assessments_limit: number;
  minutes_remaining?: number;
  sessions_used?: number;
  is_unlimited?: boolean;
}

interface SubscriptionStatus {
  status: string;
  plan: string;
  period?: string;
  limits?: SubscriptionLimits;
  is_in_trial?: boolean;
  trial_end_date?: string;
  trial_days_remaining?: number;
}

interface SubscriptionContextType {
  subscriptionStatus: SubscriptionStatus | null;
  loading: boolean;
  error: string | null;
  refreshSubscriptionStatus: () => Promise<void>;
}

const SubscriptionContext = createContext<SubscriptionContextType | undefined>(undefined);

interface SubscriptionProviderProps {
  children: ReactNode;
}

export const SubscriptionProvider: React.FC<SubscriptionProviderProps> = ({ children }) => {
  const [subscriptionStatus, setSubscriptionStatus] = useState<SubscriptionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Use ref to track last fetch time to avoid triggering re-renders
  const lastFetchTimeRef = useRef<number>(0);
  const isFetchingRef = useRef<boolean>(false);

  const { user } = useAuth();

  const fetchSubscriptionStatus = useCallback(async (force: boolean = false) => {
    // Prevent concurrent fetches
    if (isFetchingRef.current && !force) {
      devLog('[SUBSCRIPTION_CONTEXT] Fetch already in progress, skipping');
      return;
    }

    // If not forced and we fetched within last 30 seconds, skip
    const now = Date.now();
    if (!force && (now - lastFetchTimeRef.current) < 30000) {
      devLog('[SUBSCRIPTION_CONTEXT] Using cached data, last fetch was', Math.round((now - lastFetchTimeRef.current) / 1000), 'seconds ago');
      return;
    }

    try {
      isFetchingRef.current = true;
      setError(null);
      const token = localStorage.getItem('token');
      
      if (!token) {
        devLog('[SUBSCRIPTION_CONTEXT] No token found, skipping fetch');
        setLoading(false);
        return;
      }

      devLog('[SUBSCRIPTION_CONTEXT] 🚀 Fetching subscription status...');

      const response = await fetch('/api/stripe/subscription-status', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        cache: 'no-store',
      });

      if (response.ok) {
        const data = await response.json();
        setSubscriptionStatus(data);
        lastFetchTimeRef.current = now;
        devLog('[SUBSCRIPTION_CONTEXT] ✅ Subscription status fetched successfully');
      } else {
        setError('Failed to fetch subscription status');
        console.error('[SUBSCRIPTION_CONTEXT] ❌ Failed to fetch subscription status:', response.status);
      }
    } catch (error) {
      console.error('[SUBSCRIPTION_CONTEXT] ❌ Error fetching subscription status:', error);
      setError('Error fetching subscription status');
    } finally {
      setLoading(false);
      isFetchingRef.current = false;
    }
  }, []); // Empty dependencies - stable function

  // Fetch when user logs in or changes
  useEffect(() => {
    if (user) {
      devLog('[SUBSCRIPTION_CONTEXT] 👤 User detected, fetching subscription status');
      fetchSubscriptionStatus(true); // Force fetch on user change
    } else {
      devLog('[SUBSCRIPTION_CONTEXT] 🚫 No user, clearing subscription status');
      setSubscriptionStatus(null);
      setLoading(false);
    }
  }, [user?._id, fetchSubscriptionStatus]); // Only depend on user ID to avoid re-fetching on user object changes

  // Refresh function for external use
  const refreshSubscriptionStatus = useCallback(async () => {
    devLog('[SUBSCRIPTION_CONTEXT] 🔄 Manual refresh requested');
    setLoading(true);
    await fetchSubscriptionStatus(true); // Force refresh
  }, [fetchSubscriptionStatus]);

  const value: SubscriptionContextType = {
    subscriptionStatus,
    loading,
    error,
    refreshSubscriptionStatus,
  };

  return (
    <SubscriptionContext.Provider value={value}>
      {children}
    </SubscriptionContext.Provider>
  );
};

// Custom hook to use the subscription context
export const useSubscriptionContext = () => {
  const context = useContext(SubscriptionContext);
  if (context === undefined) {
    throw new Error('useSubscriptionContext must be used within a SubscriptionProvider');
  }
  return context;
};
