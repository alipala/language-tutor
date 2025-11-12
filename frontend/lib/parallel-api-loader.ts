/**
 * Parallel API Loader
 * 
 * PERFORMANCE OPTIMIZED: Loads multiple API endpoints in parallel
 * This dramatically reduces page load time by avoiding sequential API calls
 */

import { apiCache } from './api-cache';

interface ParallelLoadConfig {
  [key: string]: {
    fetcher: () => Promise<any>;
    ttl?: number;
  };
}

type ParallelLoadResult<T extends ParallelLoadConfig> = {
  [K in keyof T]: Awaited<ReturnType<T[K]['fetcher']>>;
};

/**
 * Load multiple API endpoints in parallel with caching
 * 
 * @example
 * const data = await loadInParallel({
 *   subscription: {
 *     fetcher: () => fetchSubscriptionStatus(token),
 *     ttl: 60000
 *   },
 *   progress: {
 *     fetcher: () => fetchProgressStats(token),
 *     ttl: 30000
 *   }
 * });
 * // data.subscription and data.progress are now available
 */
export async function loadInParallel<T extends ParallelLoadConfig>(
  config: T
): Promise<ParallelLoadResult<T>> {
  const keys = Object.keys(config);
  
  console.log(`[PARALLEL_LOADER] Loading ${keys.length} endpoints in parallel:`, keys);
  
  const startTime = Date.now();
  
  // Create promises for all endpoints
  const promises = keys.map(async (key) => {
    const { fetcher, ttl } = config[key];
    const cacheKey = `parallel-${key}`;
    
    try {
      const data = await apiCache.fetchWithCache(cacheKey, fetcher, ttl);
      return { key, data, error: null };
    } catch (error) {
      console.error(`[PARALLEL_LOADER] Error loading ${key}:`, error);
      return { key, data: null, error };
    }
  });
  
  // Wait for all promises to settle
  const results = await Promise.all(promises);
  
  const endTime = Date.now();
  console.log(`[PARALLEL_LOADER] Loaded ${keys.length} endpoints in ${endTime - startTime}ms`);
  
  // Build result object
  const result: any = {};
  results.forEach(({ key, data, error }) => {
    if (error) {
      // You can choose to throw or return null for failed requests
      result[key] = null;
    } else {
      result[key] = data;
    }
  });
  
  return result as ParallelLoadResult<T>;
}

/**
 * Load multiple API endpoints in parallel with individual error handling
 * Returns both successful and failed results
 */
export async function loadInParallelWithErrors<T extends ParallelLoadConfig>(
  config: T
): Promise<{
  data: Partial<ParallelLoadResult<T>>;
  errors: Partial<Record<keyof T, Error>>;
}> {
  const keys = Object.keys(config);
  
  console.log(`[PARALLEL_LOADER] Loading ${keys.length} endpoints in parallel with error tracking:`, keys);
  
  const startTime = Date.now();
  
  // Create promises for all endpoints
  const promises = keys.map(async (key) => {
    const { fetcher, ttl } = config[key];
    const cacheKey = `parallel-${key}`;
    
    try {
      const data = await apiCache.fetchWithCache(cacheKey, fetcher, ttl);
      return { key, data, error: null };
    } catch (error) {
      console.error(`[PARALLEL_LOADER] Error loading ${key}:`, error);
      return { key, data: null, error: error as Error };
    }
  });
  
  // Wait for all promises to settle
  const results = await Promise.all(promises);
  
  const endTime = Date.now();
  console.log(`[PARALLEL_LOADER] Loaded ${keys.length} endpoints in ${endTime - startTime}ms`);
  
  // Build result objects
  const data: any = {};
  const errors: any = {};
  
  results.forEach(({ key, data: resultData, error }) => {
    if (error) {
      errors[key] = error;
    } else {
      data[key] = resultData;
    }
  });
  
  return { data, errors };
}

/**
 * Preload API data in the background
 * Useful for prefetching data before navigation
 */
export function preloadInBackground<T extends ParallelLoadConfig>(
  config: T
): void {
  console.log('[PARALLEL_LOADER] Preloading data in background');
  
  // Fire and forget - don't await
  loadInParallel(config).catch((error) => {
    console.error('[PARALLEL_LOADER] Background preload error:', error);
  });
}
