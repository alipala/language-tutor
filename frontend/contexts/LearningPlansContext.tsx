'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getUserLearningPlans, LearningPlan } from '@/lib/learning-api';
import { useAuth } from '@/lib/auth';

interface LearningPlansContextType {
  learningPlans: LearningPlan[];
  loading: boolean;
  error: string | null;
  refreshLearningPlans: () => Promise<void>;
}

const LearningPlansContext = createContext<LearningPlansContextType | undefined>(undefined);

export function LearningPlansProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [learningPlans, setLearningPlans] = useState<LearningPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastFetchTime, setLastFetchTime] = useState<number>(0);

  // Stale time: 2 minutes (120000ms)
  const STALE_TIME = 120000;

  const fetchLearningPlans = useCallback(async (force: boolean = false) => {
    if (!user) {
      setLearningPlans([]);
      setLoading(false);
      return;
    }

    // Check if data is still fresh (unless force refresh)
    const now = Date.now();
    if (!force && lastFetchTime && (now - lastFetchTime) < STALE_TIME) {
      console.log('[LEARNING_PLANS_CONTEXT] Using cached data (still fresh)');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('[LEARNING_PLANS_CONTEXT] Fetching learning plans...');
      const plans = await getUserLearningPlans();
      setLearningPlans(plans);
      setLastFetchTime(Date.now());
      console.log('[LEARNING_PLANS_CONTEXT] ✅ Learning plans loaded:', plans.length);
    } catch (err: any) {
      console.error('[LEARNING_PLANS_CONTEXT] ❌ Error fetching learning plans:', err);
      setError(err.message || 'Failed to load learning plans');
    } finally {
      setLoading(false);
    }
  }, [user, lastFetchTime]);

  // Refresh function that forces a new fetch
  const refreshLearningPlans = useCallback(async () => {
    console.log('[LEARNING_PLANS_CONTEXT] Force refreshing learning plans...');
    await fetchLearningPlans(true);
  }, [fetchLearningPlans]);

  // Initial fetch when user changes
  useEffect(() => {
    fetchLearningPlans(false);
  }, [user]);

  const value: LearningPlansContextType = {
    learningPlans,
    loading,
    error,
    refreshLearningPlans
  };

  return (
    <LearningPlansContext.Provider value={value}>
      {children}
    </LearningPlansContext.Provider>
  );
}

export function useLearningPlans() {
  const context = useContext(LearningPlansContext);
  if (context === undefined) {
    throw new Error('useLearningPlans must be used within a LearningPlansProvider');
  }
  return context;
}
