/**
 * Centralized API Service with Caching
 * 
 * This service provides a single source of truth for all API calls across the application.
 * All components should use these functions instead of making direct fetch calls.
 * 
 * Benefits:
 * - Request deduplication (multiple simultaneous calls = 1 API request)
 * - Smart caching with configurable TTL
 * - Automatic cache invalidation
 * - Consistent error handling
 */

import { apiCache } from './api-cache';
import { getApiUrl } from './api-utils';

// Cache durations (in milliseconds)
// 🚀 PERFORMANCE OPTIMIZED: Increased cache durations to reduce API calls
const CACHE_DURATIONS = {
    SUBSCRIPTION_STATUS: 30000,      // 30 seconds (matches server-side cache)
    UNREAD_COUNT: 30000,             // 30 seconds
    PROGRESS_STATS: 60000,           // 60 seconds
    LEARNING_PLANS: 120000,          // 120 seconds
    CONVERSATION_HISTORY: 60000,     // 60 seconds
    ACHIEVEMENTS: 120000,            // 120 seconds
    USER_INFO: 300000,               // 5 minutes
    LOW_MINUTES_CHECK: 30000         // 30 seconds (matches server-side cache)
};

/**
 * Get authentication token from localStorage
 */
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('token');
}

/**
 * Get user ID from localStorage
 */
function getUserId(): string | null {
  if (typeof window === 'undefined') return null;
  const user = localStorage.getItem('userData'); // Fixed: was 'user', should be 'userData'
  if (!user) return null;
  try {
    const userData = JSON.parse(user);
    return userData._id || userData.id || null;
  } catch {
    return null;
  }
}

/**
 * Fetch subscription status with caching and retry logic
 */
export async function fetchSubscriptionStatus(retryCount = 0, maxRetries = 8) {
  // Wait longer initially for auth context to load
  if (retryCount === 0) {
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  const token = getAuthToken();
  const userId = getUserId();
  
  if (!token || !userId) {
    // Retry with exponential backoff if token not available yet
    if (retryCount < maxRetries) {
      console.log(`[API_SERVICE] Token not available yet, retry ${retryCount + 1}/${maxRetries}`);
      await new Promise(resolve => setTimeout(resolve, 400 * (retryCount + 1)));
      return fetchSubscriptionStatus(retryCount + 1, maxRetries);
    }
    throw new Error('Not authenticated');
  }

  return apiCache.fetchWithCache(
    `subscription-status-${userId}`,
    async () => {
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/api/stripe/subscription-status`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch subscription status');
      }

      return response.json();
    },
    CACHE_DURATIONS.SUBSCRIPTION_STATUS
  );
}

/**
 * Fetch unread notification count with caching
 */
export async function fetchUnreadCount() {
  const token = getAuthToken();
  const userId = getUserId();

  if (!token || !userId) {
    return { unread_count: 0 };
  }

  return apiCache.fetchWithCache(
    `unread-count-${userId}`,
    async () => {
      // Use relative URL to leverage Next.js rewrites
      const response = await fetch(`/api/unread-count`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch unread count');
      }

      return response.json();
    },
    CACHE_DURATIONS.UNREAD_COUNT
  );
}

/**
 * Fetch progress stats with caching
 */
export async function fetchProgressStats() {
  const token = getAuthToken();
  const userId = getUserId();
  
  if (!token || !userId) {
    throw new Error('Not authenticated');
  }

  return apiCache.fetchWithCache(
    `progress-stats-${userId}`,
    async () => {
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/api/progress/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch progress stats');
      }

      return response.json();
    },
    CACHE_DURATIONS.PROGRESS_STATS
  );
}

/**
 * Fetch conversation history with caching
 */
export async function fetchConversationHistory(limit: number = 10) {
  const token = getAuthToken();
  const userId = getUserId();
  
  if (!token || !userId) {
    throw new Error('Not authenticated');
  }

  return apiCache.fetchWithCache(
    `conversation-history-${userId}-${limit}`,
    async () => {
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/api/progress/conversations?limit=${limit}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch conversation history');
      }

      return response.json();
    },
    CACHE_DURATIONS.CONVERSATION_HISTORY
  );
}

/**
 * Fetch achievements with caching
 */
export async function fetchAchievements() {
  const token = getAuthToken();
  const userId = getUserId();
  
  if (!token || !userId) {
    throw new Error('Not authenticated');
  }

  return apiCache.fetchWithCache(
    `achievements-${userId}`,
    async () => {
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/api/progress/achievements`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch achievements');
      }

      return response.json();
    },
    CACHE_DURATIONS.ACHIEVEMENTS
  );
}

/**
 * Fetch low minutes check with caching
 */
export async function fetchLowMinutesCheck() {
  const token = getAuthToken();
  const userId = getUserId();
  
  if (!token || !userId) {
    return { has_low_minutes: false };
  }

  return apiCache.fetchWithCache(
    `low-minutes-check-${userId}`,
    async () => {
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/api/subscription/low-minutes-check`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        return { has_low_minutes: false };
      }

      return response.json();
    },
    CACHE_DURATIONS.LOW_MINUTES_CHECK
  );
}

/**
 * 🚀 BATCH ENDPOINT: Fetch all dashboard data in a single request
 * 
 * This replaces 6+ individual API calls with one batched call:
 * - Progress stats
 * - Recent conversations
 * - Achievements
 * - Flashcard sets
 * - Due flashcards
 * - Learning plans
 * 
 * All queries run in parallel on the backend for optimal performance.
 */
export async function fetchDashboardData() {
  const token = getAuthToken();
  const userId = getUserId();
  
  if (!token || !userId) {
    throw new Error('Not authenticated');
  }

  return apiCache.fetchWithCache(
    `dashboard-data-${userId}`,
    async () => {
      const apiUrl = getApiUrl();
      console.log('[API_SERVICE] 🚀 Fetching batched dashboard data...');
      
      const response = await fetch(`${apiUrl}/api/progress/dashboard-data`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch dashboard data');
      }

      const data = await response.json();
      console.log('[API_SERVICE] ✅ Batched dashboard data received');
      return data;
    },
    60000 // Cache for 60 seconds
  );
}

/**
 * Invalidate specific cache entries
 */
export function invalidateCache(keys: string[]) {
  const userId = getUserId();
  if (!userId) return;

  keys.forEach(key => {
    apiCache.invalidate(`${key}-${userId}`);
  });
}

/**
 * Invalidate all user-related cache
 */
export function invalidateAllUserCache() {
  const userId = getUserId();
  if (!userId) return;

  // Clear all cache entries for this user
  apiCache.clear();
}

/**
 * Prefetch critical data for faster page loads
 */
export async function prefetchCriticalData() {
  try {
    // Fetch all critical data in parallel
    await Promise.all([
      fetchSubscriptionStatus().catch(() => null),
      fetchUnreadCount().catch(() => null),
      fetchProgressStats().catch(() => null),
    ]);
    
    console.log('[API_SERVICE] ✅ Critical data prefetched successfully');
  } catch (error) {
    console.error('[API_SERVICE] ❌ Error prefetching data:', error);
  }
}
