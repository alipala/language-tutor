/**
 * API Cache Manager
 * Provides caching and request deduplication for API calls
 */

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

interface PendingRequest {
  promise: Promise<any>;
  timestamp: number;
}

class ApiCacheManager {
  private cache: Map<string, CacheEntry<any>> = new Map();
  private pendingRequests: Map<string, PendingRequest> = new Map();
  private defaultTTL = 30000; // 30 seconds default

  /**
   * Get cached data or fetch if not available/expired
   */
  async fetchWithCache<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttl: number = this.defaultTTL
  ): Promise<T> {
    // Check if we have valid cached data
    const cached = this.cache.get(key);
    if (cached && Date.now() < cached.expiresAt) {
      console.log(`[API_CACHE] Cache hit for: ${key}`);
      return cached.data as T;
    }

    // Check if there's already a pending request for this key
    const pending = this.pendingRequests.get(key);
    if (pending) {
      console.log(`[API_CACHE] Deduplicating request for: ${key}`);
      return pending.promise;
    }

    // Make the request
    console.log(`[API_CACHE] Cache miss, fetching: ${key}`);
    const promise = fetcher();
    
    // Store as pending
    this.pendingRequests.set(key, {
      promise,
      timestamp: Date.now()
    });

    try {
      const data = await promise;
      
      // Cache the result
      this.cache.set(key, {
        data,
        timestamp: Date.now(),
        expiresAt: Date.now() + ttl
      });

      return data;
    } finally {
      // Remove from pending
      this.pendingRequests.delete(key);
    }
  }

  /**
   * Invalidate cache for a specific key
   */
  invalidate(key: string): void {
    this.cache.delete(key);
    console.log(`[API_CACHE] Invalidated cache for: ${key}`);
  }

  /**
   * Invalidate all cache entries matching a pattern
   */
  invalidatePattern(pattern: RegExp): void {
    const keysToDelete: string[] = [];
    this.cache.forEach((_, key) => {
      if (pattern.test(key)) {
        keysToDelete.push(key);
      }
    });
    keysToDelete.forEach(key => this.cache.delete(key));
    console.log(`[API_CACHE] Invalidated ${keysToDelete.length} entries matching pattern`);
  }

  /**
   * Clear all cache
   */
  clear(): void {
    this.cache.clear();
    this.pendingRequests.clear();
    console.log('[API_CACHE] Cleared all cache');
  }

  /**
   * Get cache stats
   */
  getStats() {
    return {
      cacheSize: this.cache.size,
      pendingRequests: this.pendingRequests.size,
      entries: Array.from(this.cache.keys())
    };
  }
}

// Export singleton instance
export const apiCache = new ApiCacheManager();

/**
 * Helper function to create a cached fetch wrapper
 */
export function createCachedFetch<T>(
  endpoint: string,
  ttl?: number
) {
  return async (token: string): Promise<T> => {
    const cacheKey = `${endpoint}:${token.substring(0, 20)}`;
    
    return apiCache.fetchWithCache(
      cacheKey,
      async () => {
        const response = await fetch(endpoint, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          throw new Error(`API call failed: ${response.status}`);
        }

        return response.json();
      },
      ttl
    );
  };
}
