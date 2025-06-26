'use client';

import { useState, useEffect, useCallback } from 'react';

interface SubscriptionStatus {
  status: string;
  plan: string;
  limits?: {
    sessions_remaining: number;
    assessments_remaining: number;
    sessions_limit: number;
    assessments_limit: number;
  };
}

export const useSubscriptionStatus = () => {
  const [subscriptionStatus, setSubscriptionStatus] = useState<SubscriptionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSubscriptionStatus = useCallback(async () => {
    try {
      setError(null);
      const token = localStorage.getItem('token');
      if (!token) {
        setLoading(false);
        return;
      }

      const response = await fetch('/api/stripe/subscription-status', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        // Add cache busting to ensure fresh data
        cache: 'no-cache'
      });

      if (response.ok) {
        const data = await response.json();
        setSubscriptionStatus(data);
      } else {
        setError('Failed to fetch subscription status');
      }
    } catch (error) {
      console.error('Error fetching subscription status:', error);
      setError('Error fetching subscription status');
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchSubscriptionStatus();
  }, [fetchSubscriptionStatus]);

  // Refresh function for external use
  const refreshSubscriptionStatus = useCallback(() => {
    setLoading(true);
    fetchSubscriptionStatus();
  }, [fetchSubscriptionStatus]);

  return {
    subscriptionStatus,
    loading,
    error,
    refreshSubscriptionStatus
  };
};
