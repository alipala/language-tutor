/**
 * ROBUST CONNECTIVITY MONITORING SYSTEM
 * Fixes "Connection lost" modal appearing during page transitions
 * 
 * Key Features:
 * - Navigation-aware monitoring
 * - Smart debouncing (3-second delay)
 * - Enhanced error classification
 * - Page visibility handling
 * - Consecutive failure tracking
 * - Lightweight health checks
 */

import { checkBackendHealth, verifyBackendConnectivity, enhancedConnectivityCheck, HealthCheckResponse } from './healthCheck';

export interface ConnectivityStatus {
  isConnected: boolean;
  lastChecked: number;
  health?: HealthCheckResponse;
  error?: string;
  retryCount: number;
  fallbackActive: boolean;
  consecutiveFailures: number;
  isNavigating: boolean;
}

export interface ConnectivityOptions {
  autoRetry: boolean;
  retryInterval: number;
  maxRetries: number;
  showUserNotifications: boolean;
  enableFallbacks: boolean;
  debounceDelay: number;
  consecutiveFailureThreshold: number;
  activityBasedChecking: boolean; // Only check after inactivity
  inactivityThreshold: number; // Milliseconds of inactivity before checking
}

class RobustConnectivityMonitor {
  private status: ConnectivityStatus = {
    isConnected: true, // Start optimistic
    lastChecked: 0,
    retryCount: 0,
    fallbackActive: false,
    consecutiveFailures: 0,
    isNavigating: false
  };

  private options: ConnectivityOptions = {
    autoRetry: true,
    retryInterval: 300000, // 5 minutes (only after inactivity)
    maxRetries: 5,
    showUserNotifications: true,
    enableFallbacks: true,
    debounceDelay: 3000, // 3 seconds debounce
    consecutiveFailureThreshold: 2, // Require 2 consecutive failures
    activityBasedChecking: true, // Only check after inactivity
    inactivityThreshold: 300000 // 5 minutes of inactivity
  };

  private listeners: Array<(status: ConnectivityStatus) => void> = [];
  private retryTimer: NodeJS.Timeout | null = null;
  private debounceTimer: NodeJS.Timeout | null = null;
  private navigationTimeout: NodeJS.Timeout | null = null;
  private isChecking = false;
  private suppressNotifications = false;
  private lastActivityTime: number = Date.now();
  private activityListenersAttached = false;

  constructor(options?: Partial<ConnectivityOptions>) {
    this.options = { ...this.options, ...options };
    this.initializeNavigationTracking();
    this.initializePageVisibilityTracking();
    this.initializeActivityTracking();
    this.startMonitoring();
  }

  /**
   * Initialize Next.js router navigation tracking
   */
  private initializeNavigationTracking(): void {
    if (typeof window === 'undefined') return;

    try {
      // Try to access Next.js router through window object
      const windowWithNext = window as any;
      if (windowWithNext.next && windowWithNext.next.router) {
        const router = windowWithNext.next.router;
        
        router.events.on('routeChangeStart', () => {
          console.log('[CONNECTIVITY] Navigation started - suppressing notifications');
          this.status.isNavigating = true;
          this.suppressNotifications = true;
          this.clearDebounceTimer();
        });

        router.events.on('routeChangeComplete', () => {
          console.log('[CONNECTIVITY] Navigation completed - grace period started');
          this.navigationTimeout = setTimeout(() => {
            this.status.isNavigating = false;
            this.suppressNotifications = false;
            console.log('[CONNECTIVITY] Navigation grace period ended');
          }, 2000); // 2-second grace period
        });

        router.events.on('routeChangeError', () => {
          console.log('[CONNECTIVITY] Navigation error - ending suppression');
          this.status.isNavigating = false;
          this.suppressNotifications = false;
        });
      } else {
        // Fallback: Listen for browser navigation events
        this.initializeBrowserNavigationTracking();
      }
    } catch (error) {
      console.warn('[CONNECTIVITY] Router events not available, using fallback navigation tracking');
      this.initializeBrowserNavigationTracking();
    }
  }

  /**
   * Fallback browser navigation tracking
   */
  private initializeBrowserNavigationTracking(): void {
    if (typeof window === 'undefined') return;

    // Listen for beforeunload (page leaving)
    window.addEventListener('beforeunload', () => {
      this.status.isNavigating = true;
      this.suppressNotifications = true;
    });

    // Listen for page load completion
    window.addEventListener('load', () => {
      setTimeout(() => {
        this.status.isNavigating = false;
        this.suppressNotifications = false;
      }, 1000);
    });

    // Listen for popstate (back/forward navigation)
    window.addEventListener('popstate', () => {
      this.status.isNavigating = true;
      this.suppressNotifications = true;
      
      setTimeout(() => {
        this.status.isNavigating = false;
        this.suppressNotifications = false;
      }, 2000);
    });
  }

  /**
   * Initialize page visibility tracking
   */
  private initializePageVisibilityTracking(): void {
    if (typeof document === 'undefined') return;

    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        console.log('[CONNECTIVITY] Page hidden - pausing monitoring');
        this.pauseMonitoring();
      } else {
        console.log('[CONNECTIVITY] Page visible - resuming monitoring');
        this.resumeMonitoring();
      }
    });
  }

  /**
   * Initialize user activity tracking
   */
  private initializeActivityTracking(): void {
    if (typeof window === 'undefined' || !this.options.activityBasedChecking) return;

    if (this.activityListenersAttached) return;
    
    const updateActivity = () => {
      this.lastActivityTime = Date.now();
    };
    
    // Track various user activities
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
    
    events.forEach(event => {
      window.addEventListener(event, updateActivity, { passive: true });
    });
    
    this.activityListenersAttached = true;
    console.log('[CONNECTIVITY] Activity tracking initialized');
  }

  /**
   * Check if user has been inactive
   */
  private isUserInactive(): boolean {
    if (!this.options.activityBasedChecking) return false;
    
    const timeSinceActivity = Date.now() - this.lastActivityTime;
    return timeSinceActivity >= this.options.inactivityThreshold;
  }

  /**
   * Start connectivity monitoring
   */
  private startMonitoring(): void {
    console.log('[CONNECTIVITY] Starting robust connectivity monitoring with activity-based checking...');
    
    // Initial check on app load after a short delay
    setTimeout(() => {
      console.log('[CONNECTIVITY] Initial connectivity check on app load');
      this.checkConnectivity();
    }, 1000);
    
    // Set up periodic checks based on activity
    if (this.options.autoRetry) {
      this.scheduleNextCheck();
    }
  }

  /**
   * Pause monitoring (when page is hidden)
   */
  private pauseMonitoring(): void {
    this.clearRetryTimer();
    this.clearDebounceTimer();
  }

  /**
   * Resume monitoring (when page becomes visible)
   */
  private resumeMonitoring(): void {
    if (this.options.autoRetry) {
      this.scheduleNextCheck();
    }
  }

  /**
   * Perform a smart connectivity check
   */
  public async checkConnectivity(): Promise<ConnectivityStatus> {
    if (this.isChecking) {
      console.log('[CONNECTIVITY] Check already in progress, skipping...');
      return this.status;
    }

    // Skip checks during navigation
    if (this.status.isNavigating) {
      console.log('[CONNECTIVITY] Skipping check during navigation');
      return this.status;
    }

    this.isChecking = true;
    console.log('[CONNECTIVITY] Performing smart connectivity check...');

    try {
      const result = await this.smartHealthCheck();
      
      if (result) {
        // Connection successful
        console.log('[CONNECTIVITY] ✅ Connectivity check passed');
        
        this.status = {
          ...this.status,
          isConnected: true,
          lastChecked: Date.now(),
          error: undefined,
          retryCount: 0,
          consecutiveFailures: 0
        };

        this.clearRetryTimer();
        this.scheduleNextCheck();
      } else {
        // Connection failed
        console.log('[CONNECTIVITY] ❌ Connectivity check failed');
        
        this.status = {
          ...this.status,
          isConnected: false,
          lastChecked: Date.now(),
          consecutiveFailures: this.status.consecutiveFailures + 1,
          retryCount: this.status.retryCount + 1
        };

        this.scheduleRetry();
      }

    } catch (error) {
      console.error('[CONNECTIVITY] ❌ Connectivity check error:', error);
      
      const isRealIssue = this.isRealConnectivityIssue(error as Error);
      
      this.status = {
        ...this.status,
        isConnected: false,
        lastChecked: Date.now(),
        error: error instanceof Error ? error.message : 'Unknown error',
        consecutiveFailures: isRealIssue ? this.status.consecutiveFailures + 1 : this.status.consecutiveFailures,
        retryCount: this.status.retryCount + 1
      };

      this.scheduleRetry();
    } finally {
      this.isChecking = false;
      this.debouncedStatusUpdate();
    }

    return this.status;
  }

  /**
   * Smart health check using lightweight ping endpoint
   */
  private async smartHealthCheck(): Promise<boolean> {
    // Skip checks during navigation
    if (this.status.isNavigating) return true;

    try {
      // Use lightweight ping endpoint
      const response = await fetch('/api/health/ping', {
        method: 'HEAD',
        cache: 'no-cache',
        signal: AbortSignal.timeout(8000) // 8-second timeout — backend may be busy
      });
      
      return response.ok;
    } catch (error) {
      console.log('[CONNECTIVITY] Ping failed, trying fallback health check');
      
      // Fallback to regular health check
      try {
        const result = await enhancedConnectivityCheck(false); // Don't show notifications
        return result.connected;
      } catch (fallbackError) {
        return false;
      }
    }
  }

  /**
   * Determine if error represents a real connectivity issue
   */
  private isRealConnectivityIssue(error: Error): boolean {
    const realConnectivityErrors = [
      'ERR_NETWORK',
      'ERR_INTERNET_DISCONNECTED', 
      'ERR_CONNECTION_REFUSED',
      'fetch failed',
      'NetworkError',
      'Failed to fetch'
    ];
    
    // Ignore errors during navigation
    if (this.status.isNavigating) return false;
    
    // Ignore single timeouts (could be server load)
    if (error.message.includes('timeout') && this.status.consecutiveFailures < 1) {
      return false;
    }
    
    return realConnectivityErrors.some(err => 
      error.message.includes(err) || error.name.includes(err)
    );
  }

  /**
   * Debounced status update to prevent rapid notifications
   */
  private debouncedStatusUpdate(): void {
    this.clearDebounceTimer();
    
    this.debounceTimer = setTimeout(() => {
      // Only notify if:
      // 1. Not currently navigating
      // 2. Multiple consecutive failures (for disconnection)
      // 3. Not suppressing notifications
      const shouldNotify = !this.status.isNavigating && 
                          !this.suppressNotifications &&
                          (this.status.isConnected || 
                           this.status.consecutiveFailures >= this.options.consecutiveFailureThreshold);
      
      if (shouldNotify) {
        console.log('[CONNECTIVITY] Notifying listeners of status change');
        this.notifyListeners();
      } else {
        console.log('[CONNECTIVITY] Suppressing notification - navigation or insufficient failures');
      }
    }, this.options.debounceDelay);
  }

  /**
   * Get retry delay with intelligent backoff
   */
  private getRetryDelay(): number {
    // Faster retries during navigation
    if (this.status.isNavigating) return 1000;
    
    // Exponential backoff for real issues
    return Math.min(5000 * Math.pow(1.5, this.status.retryCount), 30000);
  }

  /**
   * Schedule the next connectivity check
   */
  private scheduleNextCheck(): void {
    this.clearRetryTimer();

    this.retryTimer = setTimeout(() => {
      // Only check if user is inactive or activity-based checking is disabled
      if (!this.options.activityBasedChecking || this.isUserInactive()) {
        console.log('[CONNECTIVITY] User inactive - performing scheduled connectivity check');
        this.checkConnectivity();
      } else {
        console.log('[CONNECTIVITY] User active - skipping scheduled check, rescheduling');
        // Reschedule for next check
        this.scheduleNextCheck();
      }
    }, this.options.retryInterval);
  }

  /**
   * Schedule a retry after a failed check
   */
  private scheduleRetry(): void {
    if (!this.options.autoRetry || this.status.retryCount >= this.options.maxRetries) {
      console.log('[CONNECTIVITY] Max retries reached or auto-retry disabled');
      return;
    }

    const delay = this.getRetryDelay();
    
    console.log(`[CONNECTIVITY] Scheduling retry ${this.status.retryCount}/${this.options.maxRetries} in ${delay}ms`);
    
    this.clearRetryTimer();

    this.retryTimer = setTimeout(() => {
      this.checkConnectivity();
    }, delay);
  }

  /**
   * Clear timers
   */
  private clearRetryTimer(): void {
    if (this.retryTimer) {
      clearTimeout(this.retryTimer);
      this.retryTimer = null;
    }
  }

  private clearDebounceTimer(): void {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = null;
    }
  }

  private clearNavigationTimeout(): void {
    if (this.navigationTimeout) {
      clearTimeout(this.navigationTimeout);
      this.navigationTimeout = null;
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
        console.error('[CONNECTIVITY] Error in listener:', error);
      }
    });
  }

  /**
   * Add a status change listener
   */
  public addListener(listener: (status: ConnectivityStatus) => void): () => void {
    this.listeners.push(listener);
    
    // Immediately notify with current status (only if connected or sufficient failures)
    const shouldNotify = this.status.isConnected || 
                        this.status.consecutiveFailures >= this.options.consecutiveFailureThreshold;
    
    if (shouldNotify && !this.suppressNotifications) {
      listener(this.status);
    }
    
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
    console.log('[CONNECTIVITY] Force checking connectivity...');
    return await this.checkConnectivity();
  }

  /**
   * Reset the monitor state
   */
  public reset(): void {
    console.log('[CONNECTIVITY] Resetting robust connectivity monitor...');
    this.status.retryCount = 0;
    this.status.consecutiveFailures = 0;
    this.status.error = undefined;
    this.clearRetryTimer();
    this.clearDebounceTimer();
    this.clearNavigationTimeout();
    this.scheduleNextCheck();
  }

  /**
   * Stop monitoring
   */
  public stop(): void {
    console.log('[CONNECTIVITY] Stopping robust connectivity monitoring...');
    this.clearRetryTimer();
    this.clearDebounceTimer();
    this.clearNavigationTimeout();
    this.listeners = [];
  }

  /**
   * Update monitoring options
   */
  public updateOptions(newOptions: Partial<ConnectivityOptions>): void {
    this.options = { ...this.options, ...newOptions };
    console.log('[CONNECTIVITY] Updated options:', this.options);
    
    // Restart monitoring with new options
    this.clearRetryTimer();
    if (this.options.autoRetry) {
      this.scheduleNextCheck();
    }
  }
}

// Global robust connectivity monitor instance
let globalRobustMonitor: RobustConnectivityMonitor | null = null;

/**
 * Get or create the global robust connectivity monitor
 */
export function getRobustConnectivityMonitor(options?: Partial<ConnectivityOptions>): RobustConnectivityMonitor {
  if (!globalRobustMonitor) {
    globalRobustMonitor = new RobustConnectivityMonitor(options);
  } else if (options) {
    globalRobustMonitor.updateOptions(options);
  }
  
  return globalRobustMonitor;
}

/**
 * React hook for robust connectivity monitoring
 */
export function useRobustConnectivityMonitor(options?: Partial<ConnectivityOptions>) {
  const [status, setStatus] = React.useState<ConnectivityStatus>({
    isConnected: true, // Start optimistic
    lastChecked: 0,
    retryCount: 0,
    fallbackActive: false,
    consecutiveFailures: 0,
    isNavigating: false
  });

  React.useEffect(() => {
    const monitor = getRobustConnectivityMonitor(options);
    
    const unsubscribe = monitor.addListener((newStatus) => {
      setStatus(newStatus);
    });

    return unsubscribe;
  }, []);

  const forceCheck = React.useCallback(async () => {
    const monitor = getRobustConnectivityMonitor();
    return await monitor.forceCheck();
  }, []);

  const reset = React.useCallback(() => {
    const monitor = getRobustConnectivityMonitor();
    monitor.reset();
  }, []);

  return {
    status,
    forceCheck,
    reset,
    isConnected: status.isConnected,
    error: status.error,
    retryCount: status.retryCount,
    lastChecked: status.lastChecked,
    isNavigating: status.isNavigating,
    consecutiveFailures: status.consecutiveFailures
  };
}

// Import React for the hook
import React from 'react';

export default RobustConnectivityMonitor;
