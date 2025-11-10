'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';

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
  const [lastFetchTime, setLastFetchTime] = useState<number>(0);

  const fetchSubscriptionStatus = useCallback(async (force: boolean = false) => {
    // If not forced and we fetched within last 30 seconds, skip
    const now = Date.now();
    if (!force && subscriptionStatus && (now - lastFetchTime) < 30000) {
      console.log('[SUBSCRIPTION_CONTEXT] Using cached data, last fetch was', Math.round((now - lastFetchTime) / 1000), 'seconds ago');
      return;
    }

    try {
      setError(null);
      const token = localStorage.getItem('token');
      
      if (!token) {
        console.log('[SUBSCRIPTION_CONTEXT] No token found, skipping fetch');
        setLoading(false);
        return;
      }

      console.log('[SUBSCRIPTION_CONTEXT] 🚀 Fetching subscription status...');

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
        setLastFetchTime(now);
        console.log('[SUBSCRIPTION_CONTEXT] ✅ Subscription status fetched successfully');
      } else {
        setError('Failed to fetch subscription status');
        console.error('[SUBSCRIPTION_CONTEXT] ❌ Failed to fetch subscription status:', response.status);
      }
    } catch (error) {
      console.error('[SUBSCRIPTION_CONTEXT] ❌ Error fetching subscription status:', error);
      setError('Error fetching subscription status');
    } finally {
      setLoading(false);
    }
  }, [subscriptionStatus, lastFetchTime]);

  // Initial fetch on mount
  useEffect(() => {
    // Wait a bit for auth to be ready
    const timer = setTimeout(() => {
      fetchSubscriptionStatus();
    }, 500);

    return () => clearTimeout(timer);
  }, []);

  // Refresh function for external use
  const refreshSubscriptionStatus = useCallback(async () => {
    console.log('[SUBSCRIPTION_CONTEXT] 🔄 Manual refresh requested');
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
