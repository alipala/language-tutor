/**
 * API Cache Manager
 * Provides caching and request deduplication for API calls
 * 
 * PERFORMANCE OPTIMIZED: Uses localStorage for persistence across page navigations
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

const CACHE_STORAGE_KEY = 'api_cache_v1';
const MAX_CACHE_SIZE = 50; // Limit cache size to prevent localStorage overflow

class ApiCacheManager {
  private cache: Map<string, CacheEntry<any>> = new Map();
  private pendingRequests: Map<string, PendingRequest> = new Map();
  private defaultTTL = 60000; // 60 seconds default (increased for better performance)
  private initialized = false;

  constructor() {
    // Load cache from localStorage on initialization
    if (typeof window !== 'undefined') {
      this.loadCacheFromStorage();
    }
  }

  /**
   * Load cache from localStorage
   */
  private loadCacheFromStorage(): void {
    try {
      const stored = localStorage.getItem(CACHE_STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        const now = Date.now();
        
        // Only load non-expired entries
        Object.entries(parsed).forEach(([key, entry]: [string, any]) => {
          if (entry.expiresAt > now) {
            this.cache.set(key, entry);
          }
        });
        
        console.log(`[API_CACHE] Loaded ${this.cache.size} cached entries from storage`);
      }
      this.initialized = true;
    } catch (error) {
      console.error('[API_CACHE] Error loading cache from storage:', error);
      this.initialized = true;
    }
  }

  /**
   * Save cache to localStorage
   */
  private saveCacheToStorage(): void {
    if (typeof window === 'undefined') return;
    
    try {
      const cacheObj: Record<string, CacheEntry<any>> = {};
      const now = Date.now();
      
      // Only save non-expired entries
      this.cache.forEach((entry, key) => {
        if (entry.expiresAt > now) {
          cacheObj[key] = entry;
        }
      });
      
      // Limit cache size
      const entries = Object.entries(cacheObj);
      if (entries.length > MAX_CACHE_SIZE) {
        // Keep only the most recent entries
        entries.sort((a, b) => b[1].timestamp - a[1].timestamp);
        const limited = Object.fromEntries(entries.slice(0, MAX_CACHE_SIZE));
        localStorage.setItem(CACHE_STORAGE_KEY, JSON.stringify(limited));
      } else {
        localStorage.setItem(CACHE_STORAGE_KEY, JSON.stringify(cacheObj));
      }
    } catch (error) {
      console.error('[API_CACHE] Error saving cache to storage:', error);
    }
  }

  /**
   * Get cached data or fetch if not available/expired
   * OPTIMIZED: Persists cache to localStorage for cross-page performance
   */
  async fetchWithCache<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttl: number = this.defaultTTL
  ): Promise<T> {
    // Ensure cache is loaded
    if (!this.initialized && typeof window !== 'undefined') {
      this.loadCacheFromStorage();
    }

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

      // 🚀 PERFORMANCE FIX: Persist to localStorage
      this.saveCacheToStorage();

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
    this.saveCacheToStorage();
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
    this.saveCacheToStorage();
    console.log(`[API_CACHE] Invalidated ${keysToDelete.length} entries matching pattern`);
  }

  /**
   * Clear all cache
   */
  clear(): void {
    this.cache.clear();
    this.pendingRequests.clear();
    if (typeof window !== 'undefined') {
      localStorage.removeItem(CACHE_STORAGE_KEY);
    }
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
