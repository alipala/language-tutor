'use client';

import { useSubscriptionContext } from '@/contexts/SubscriptionContext';

/**
 * Hook to access subscription status from centralized context
 * This replaces the previous implementation that made individual API calls
 * 
 * PERFORMANCE OPTIMIZATION: This now uses a shared context that makes
 * only ONE API call per session instead of multiple duplicate calls
 */
export const useSubscriptionStatus = () => {
  return useSubscriptionContext();
};
