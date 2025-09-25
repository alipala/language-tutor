/**
 * Comprehensive connectivity monitoring and error handling system
 * Provides robust backend connectivity management with fallback mechanisms
 */

import { checkBackendHealth, verifyBackendConnectivity, enhancedConnectivityCheck, HealthCheckResponse } from './healthCheck';

export interface ConnectivityStatus {
  isConnected: boolean;
  lastChecked: number;
  health?: HealthCheckResponse;
  error?: string;
  retryCount: number;
  fallbackActive: boolean;
}

export interface ConnectivityOptions {
  autoRetry: boolean;
  retryInterval: number;
  maxRetries: number;
  showUserNotifications: boolean;
  enableFallbacks: boolean;
}

class ConnectivityMonitor {
  private status: ConnectivityStatus = {
    isConnected: false,
    lastChecked: 0,
    retryCount: 0,
    fallbackActive: false
  };

  private options: ConnectivityOptions = {
    autoRetry: true,
    retryInterval: 30000, // 30 seconds
    maxRetries: 5,
    showUserNotifications: true,
    enableFallbacks: true
  };

  private listeners: Array<(status: ConnectivityStatus) => void> = [];
  private retryTimer: NodeJS.Timeout | null = null;
  private isChecking = false;

  constructor(options?: Partial<ConnectivityOptions>) {
    this.options = { ...this.options, ...options };
    this.startMonitoring();
  }

  /**
   * Start continuous connectivity monitoring
   */
  private startMonitoring(): void {
    console.log('[CONNECTIVITY_MONITOR] Starting connectivity monitoring...');
    
    // Initial check
    this.checkConnectivity();
    
    // Set up periodic checks
    if (this.options.autoRetry) {
      this.scheduleNextCheck();
    }
  }

  /**
   * Perform a connectivity check
   */
  public async checkConnectivity(): Promise<ConnectivityStatus> {
    if (this.isChecking) {
      console.log('[CONNECTIVITY_MONITOR] Check already in progress, skipping...');
      return this.status;
    }

    this.isChecking = true;
    console.log('[CONNECTIVITY_MONITOR] Performing connectivity check...');

    try {
      const result = await enhancedConnectivityCheck(this.options.showUserNotifications);
      
      this.status = {
        isConnected: result.connected,
        lastChecked: Date.now(),
        health: result.health,
        error: result.error,
        retryCount: result.connected ? 0 : this.status.retryCount + 1,
        fallbackActive: result.fallbackAvailable || false
      };

      if (result.connected) {
        console.log('[CONNECTIVITY_MONITOR] ✅ Connectivity restored');
        this.clearRetryTimer();
      } else {
        console.error('[CONNECTIVITY_MONITOR] ❌ Connectivity check failed:', result.error);
        this.scheduleRetry();
      }

    } catch (error) {
      console.error('[CONNECTIVITY_MONITOR] ❌ Connectivity check error:', error);
      
      this.status = {
        isConnected: false,
        lastChecked: Date.now(),
        error: error instanceof Error ? error.message : 'Unknown error',
        retryCount: this.status.retryCount + 1,
        fallbackActive: false
      };

      this.scheduleRetry();
    } finally {
      this.isChecking = false;
      this.notifyListeners();
    }

    return this.status;
  }

  /**
   * Schedule the next connectivity check
   */
  private scheduleNextCheck(): void {
    if (this.retryTimer) {
      clearTimeout(this.retryTimer);
    }

    this.retryTimer = setTimeout(() => {
      this.checkConnectivity();
    }, this.options.retryInterval);
  }

  /**
   * Schedule a retry after a failed check
   */
  private scheduleRetry(): void {
    if (!this.options.autoRetry || this.status.retryCount >= this.options.maxRetries) {
      console.log('[CONNECTIVITY_MONITOR] Max retries reached or auto-retry disabled');
      return;
    }

    // Exponential backoff for retries
    const delay = Math.min(this.options.retryInterval * Math.pow(2, this.status.retryCount - 1), 300000); // Max 5 minutes
    
    console.log(`[CONNECTIVITY_MONITOR] Scheduling retry ${this.status.retryCount}/${this.options.maxRetries} in ${delay}ms`);
    
    if (this.retryTimer) {
      clearTimeout(this.retryTimer);
    }

    this.retryTimer = setTimeout(() => {
      this.checkConnectivity();
    }, delay);
  }

  /**
   * Clear the retry timer
   */
  private clearRetryTimer(): void {
    if (this.retryTimer) {
      clearTimeout(this.retryTimer);
      this.retryTimer = null;
    }
  }

  /**
   * Notify all listeners of status changes
   */
  private notifyListeners(): void {
    this.listeners.forEach(listener => {
      try {
        listener(this.status);
      } catch (error) {
        console.error('[CONNECTIVITY_MONITOR] Error in listener:', error);
      }
    });
  }

  /**
   * Add a status change listener
   */
  public addListener(listener: (status: ConnectivityStatus) => void): () => void {
    this.listeners.push(listener);
    
    // Immediately notify with current status
    listener(this.status);
    
    // Return unsubscribe function
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  /**
   * Get current connectivity status
   */
  public getStatus(): ConnectivityStatus {
    return { ...this.status };
  }

  /**
   * Force a connectivity check
   */
  public async forceCheck(): Promise<ConnectivityStatus> {
    console.log('[CONNECTIVITY_MONITOR] Force checking connectivity...');
    return await this.checkConnectivity();
  }

  /**
   * Reset the retry count and error state
   */
  public reset(): void {
    console.log('[CONNECTIVITY_MONITOR] Resetting connectivity monitor...');
    this.status.retryCount = 0;
    this.status.error = undefined;
    this.clearRetryTimer();
    this.scheduleNextCheck();
  }

  /**
   * Stop monitoring
   */
  public stop(): void {
    console.log('[CONNECTIVITY_MONITOR] Stopping connectivity monitoring...');
    this.clearRetryTimer();
    this.listeners = [];
  }

  /**
   * Update monitoring options
   */
  public updateOptions(newOptions: Partial<ConnectivityOptions>): void {
    this.options = { ...this.options, ...newOptions };
    console.log('[CONNECTIVITY_MONITOR] Updated options:', this.options);
    
    // Restart monitoring with new options
    this.clearRetryTimer();
    if (this.options.autoRetry) {
      this.scheduleNextCheck();
    }
  }
}

// Global connectivity monitor instance
let globalMonitor: ConnectivityMonitor | null = null;

/**
 * Get or create the global connectivity monitor
 */
export function getConnectivityMonitor(options?: Partial<ConnectivityOptions>): ConnectivityMonitor {
  if (!globalMonitor) {
    globalMonitor = new ConnectivityMonitor(options);
  } else if (options) {
    globalMonitor.updateOptions(options);
  }
  
  return globalMonitor;
}

/**
 * React hook for connectivity monitoring
 */
export function useConnectivityMonitor(options?: Partial<ConnectivityOptions>) {
  const [status, setStatus] = React.useState<ConnectivityStatus>({
    isConnected: false,
    lastChecked: 0,
    retryCount: 0,
    fallbackActive: false
  });

  React.useEffect(() => {
    const monitor = getConnectivityMonitor(options);
    
    const unsubscribe = monitor.addListener((newStatus) => {
      setStatus(newStatus);
    });

    return unsubscribe;
  }, []);

  const forceCheck = React.useCallback(async () => {
    const monitor = getConnectivityMonitor();
    return await monitor.forceCheck();
  }, []);

  const reset = React.useCallback(() => {
    const monitor = getConnectivityMonitor();
    monitor.reset();
  }, []);

  return {
    status,
    forceCheck,
    reset,
    isConnected: status.isConnected,
    error: status.error,
    retryCount: status.retryCount,
    lastChecked: status.lastChecked
  };
}

/**
 * Utility function for safe API calls with connectivity checking
 */
export async function safeApiCall<T>(
  apiCall: () => Promise<T>,
  fallback?: T,
  options?: {
    checkConnectivity?: boolean;
    retries?: number;
    timeout?: number;
  }
): Promise<T> {
  const {
    checkConnectivity = true,
    retries = 2,
    timeout = 10000
  } = options || {};

  // Check connectivity first if requested
  if (checkConnectivity) {
    const monitor = getConnectivityMonitor();
    const status = monitor.getStatus();
    
    if (!status.isConnected && status.lastChecked > Date.now() - 60000) {
      // If we know we're disconnected and checked recently, don't try
      console.warn('[SAFE_API_CALL] Skipping API call - backend is disconnected');
      if (fallback !== undefined) {
        return fallback;
      }
      throw new Error('Backend is disconnected');
    }
  }

  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      console.log(`[SAFE_API_CALL] Attempt ${attempt + 1}/${retries + 1}`);
      
      // Create timeout promise
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error('API call timeout')), timeout);
      });
      
      // Race between API call and timeout
      const result = await Promise.race([apiCall(), timeoutPromise]);
      
      console.log('[SAFE_API_CALL] ✅ API call successful');
      return result;
      
    } catch (error) {
      lastError = error instanceof Error ? error : new Error('Unknown error');
      console.error(`[SAFE_API_CALL] Attempt ${attempt + 1} failed:`, lastError.message);
      
      if (attempt < retries) {
        // Wait before retrying
        const delay = 1000 * Math.pow(2, attempt);
        console.log(`[SAFE_API_CALL] Waiting ${delay}ms before retry...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  // All attempts failed
  console.error('[SAFE_API_CALL] ❌ All attempts failed');
  
  // Update connectivity status
  if (checkConnectivity) {
    const monitor = getConnectivityMonitor();
    monitor.checkConnectivity(); // Trigger a connectivity check
  }
  
  if (fallback !== undefined) {
    console.log('[SAFE_API_CALL] Using fallback value');
    return fallback;
  }
  
  throw lastError || new Error('API call failed');
}

// Import React for the hook
import React from 'react';

export default ConnectivityMonitor;
