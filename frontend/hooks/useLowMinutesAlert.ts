'use client';

import { useState, useEffect } from 'react';
import { getApiUrl } from '@/lib/api-utils';

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

      const token = localStorage.getItem('token');
      if (!token) {
        if (isInitialLoad) {
          setLoading(false);
        }
        return;
      }

      const response = await fetch(`${getApiUrl()}/api/subscription/low-minutes-check`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.data) {
          setLowMinutesStatus(data.data);
        }
      } else {
        console.error('Failed to check low minutes status');
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
