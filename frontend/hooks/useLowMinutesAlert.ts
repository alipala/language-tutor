'use client';

import { useState, useEffect } from 'react';
import { fetchLowMinutesCheck } from '@/lib/api-service';

export interface LowMinutesStatus {
  has_low_minutes: boolean;
  minutes_remaining: number | null;
  minutes_used?: number;
  minutes_limit?: number;
  is_unlimited: boolean;
  message: string | null;
  severity?: 'info' | 'warning' | 'critical';
  period?: string;
  plan?: string;
}

export function useLowMinutesAlert() {
  const [lowMinutesStatus, setLowMinutesStatus] = useState<LowMinutesStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkLowMinutes = async (isInitialLoad = false) => {
    try {
      // Only show loading state on initial load, not on background refreshes
      if (isInitialLoad) {
        setLoading(true);
      }
      setError(null);

      // Use centralized API service with caching - much faster!
      const data = await fetchLowMinutesCheck();
      
      if (data.success && data.data) {
        setLowMinutesStatus(data.data);
      } else if (data.has_low_minutes !== undefined) {
        // Handle direct response format
        setLowMinutesStatus(data as LowMinutesStatus);
      }
    } catch (err) {
      console.error('Error checking low minutes:', err);
      setError('Failed to check minutes status');
    } finally {
      if (isInitialLoad) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    // Initial load with loading state
    checkLowMinutes(true);

    // Background refresh every 2 minutes (without loading state to prevent blinking)
    const interval = setInterval(() => checkLowMinutes(false), 120000);

    return () => clearInterval(interval);
  }, []);

  return {
    lowMinutesStatus,
    loading,
    error,
    refresh: checkLowMinutes
  };
}
