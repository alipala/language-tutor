/**
 * Connectivity Error Boundary Component
 * Handles backend connectivity errors and provides user-friendly fallbacks
 */

'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCw, Wifi, WifiOff } from 'lucide-react';
import { getRobustConnectivityMonitor, ConnectivityStatus } from '@/lib/connectivity-monitor-robust';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  showRetryButton?: boolean;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  connectivityStatus: ConnectivityStatus;
  isRetrying: boolean;
}

export class ConnectivityErrorBoundary extends Component<Props, State> {
  private connectivityMonitor = getRobustConnectivityMonitor();
  private unsubscribeConnectivity: (() => void) | null = null;

  constructor(props: Props) {
    super(props);
    
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      connectivityStatus: this.connectivityMonitor.getStatus(),
      isRetrying: false
    };
  }

  componentDidMount() {
    // Subscribe to connectivity changes
    this.unsubscribeConnectivity = this.connectivityMonitor.addListener((status) => {
      this.setState({ connectivityStatus: status });
      
      // If connectivity is restored and we had an error, try to recover
      if (status.isConnected && this.state.hasError) {
        console.log('[ERROR_BOUNDARY] Connectivity restored, attempting recovery...');
        this.handleRetry();
      }
    });
  }

  componentWillUnmount() {
    if (this.unsubscribeConnectivity) {
      this.unsubscribeConnectivity();
    }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[ERROR_BOUNDARY] Caught error:', error);
    console.error('[ERROR_BOUNDARY] Error info:', errorInfo);
    
    this.setState({
      error,
      errorInfo
    });

    // Check if this is a connectivity-related error
    const isConnectivityError = this.isConnectivityError(error);
    
    if (isConnectivityError) {
      console.log('[ERROR_BOUNDARY] Detected connectivity error, triggering connectivity check...');
      this.connectivityMonitor.forceCheck();
    }

    // Call the onError prop if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log error for monitoring
    this.logErrorForMonitoring(error, errorInfo, isConnectivityError);
  }

  private isConnectivityError(error: Error): boolean {
    const connectivityKeywords = [
      'fetch',
      'network',
      'connectivity',
      'backend',
      'Cannot read properties of undefined',
      'environment',
      'CORS',
      'timeout',
      'unreachable',
      'connection'
    ];

    const errorMessage = error.message.toLowerCase();
    const errorStack = error.stack?.toLowerCase() || '';
    
    return connectivityKeywords.some(keyword => 
      errorMessage.includes(keyword) || errorStack.includes(keyword)
    );
  }

  private async logErrorForMonitoring(error: Error, errorInfo: ErrorInfo, isConnectivityError: boolean) {
    try {
      // Create error report
      const errorReport = {
        timestamp: new Date().toISOString(),
        error: {
          message: error.message,
          stack: error.stack,
          name: error.name
        },
        errorInfo: {
          componentStack: errorInfo.componentStack
        },
        connectivity: {
          isConnectivityError,
          status: this.state.connectivityStatus
        },
        environment: {
          userAgent: typeof window !== 'undefined' ? window.navigator.userAgent : 'unknown',
          url: typeof window !== 'undefined' ? window.location.href : 'unknown',
          timestamp: Date.now()
        }
      };

      console.log('[ERROR_BOUNDARY] Error report:', errorReport);
      
      // In a real application, you might send this to an error tracking service
      // For now, we'll just log it
      
    } catch (loggingError) {
      console.error('[ERROR_BOUNDARY] Failed to log error:', loggingError);
    }
  }

  private handleRetry = async () => {
    console.log('[ERROR_BOUNDARY] Attempting to retry...');
    
    this.setState({ isRetrying: true });
    
    try {
      // Force a connectivity check
      await this.connectivityMonitor.forceCheck();
      
      // Wait a moment for the check to complete
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Reset the error state to try rendering again
      this.setState({
        hasError: false,
        error: null,
        errorInfo: null,
        isRetrying: false
      });
      
      console.log('[ERROR_BOUNDARY] ✅ Retry successful, component should re-render');
      
    } catch (error) {
      console.error('[ERROR_BOUNDARY] ❌ Retry failed:', error);
      this.setState({ isRetrying: false });
    }
  };

  private handleReset = () => {
    console.log('[ERROR_BOUNDARY] Resetting error boundary...');
    
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      isRetrying: false
    });
    
    // Reset the connectivity monitor
    this.connectivityMonitor.reset();
  };

  private renderConnectivityStatus() {
    const { connectivityStatus } = this.state;
    
    return (
      <div className="flex items-center gap-2 text-sm text-gray-600 mb-4">
        {connectivityStatus.isConnected ? (
          <>
            <Wifi className="w-4 h-4 text-green-500" />
            <span>Backend connected</span>
          </>
        ) : (
          <>
            <WifiOff className="w-4 h-4 text-red-500" />
            <span>Backend disconnected</span>
            {connectivityStatus.retryCount > 0 && (
              <span className="text-xs">
                (Retry {connectivityStatus.retryCount}/5)
              </span>
            )}
          </>
        )}
      </div>
    );
  }

  private renderErrorDetails() {
    const { error, errorInfo } = this.state;
    
    if (!error) return null;

    const isConnectivityError = this.isConnectivityError(error);
    
    return (
      <details className="mt-4 text-sm">
        <summary className="cursor-pointer text-gray-600 hover:text-gray-800">
          Technical Details
        </summary>
        <div className="mt-2 p-3 bg-gray-50 rounded border text-xs font-mono">
          <div className="mb-2">
            <strong>Error Type:</strong> {isConnectivityError ? 'Connectivity Error' : 'Application Error'}
          </div>
          <div className="mb-2">
            <strong>Message:</strong> {error.message}
          </div>
          {error.stack && (
            <div className="mb-2">
              <strong>Stack:</strong>
              <pre className="mt-1 whitespace-pre-wrap">{error.stack}</pre>
            </div>
          )}
          {errorInfo?.componentStack && (
            <div>
              <strong>Component Stack:</strong>
              <pre className="mt-1 whitespace-pre-wrap">{errorInfo.componentStack}</pre>
            </div>
          )}
        </div>
      </details>
    );
  }

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { error, connectivityStatus, isRetrying } = this.state;
      const isConnectivityError = error ? this.isConnectivityError(error) : false;

      return (
        <div className="min-h-screen bg-gradient-to-br from-brand to-[#44A08D] flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full">
            <div className="text-center">
              <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
              
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                {isConnectivityError ? 'Connection Error' : 'Something went wrong'}
              </h1>
              
              <p className="text-gray-600 mb-6">
                {isConnectivityError 
                  ? 'Unable to connect to the backend server. Please try again later.'
                  : 'An unexpected error occurred. Please try refreshing the page.'
                }
              </p>

              {this.renderConnectivityStatus()}

              <div className="space-y-3">
                {this.props.showRetryButton !== false && (
                  <Button
                    onClick={this.handleRetry}
                    disabled={isRetrying}
                    className="w-full bg-brand hover:bg-[#44A08D] text-white"
                  >
                    {isRetrying ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        Retrying...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Retry Connection
                      </>
                    )}
                  </Button>
                )}
                
                <Button
                  onClick={this.handleReset}
                  variant="outline"
                  className="w-full"
                >
                  Reset Application
                </Button>
                
                <Button
                  onClick={() => window.location.reload()}
                  variant="outline"
                  className="w-full"
                >
                  Refresh Page
                </Button>
              </div>

              {this.renderErrorDetails()}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Higher-order component for wrapping components with connectivity error handling
 */
export function withConnectivityErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  options?: {
    fallback?: ReactNode;
    showRetryButton?: boolean;
    onError?: (error: Error, errorInfo: ErrorInfo) => void;
  }
) {
  const ComponentWithErrorBoundary = (props: P) => {
    return (
      <ConnectivityErrorBoundary
        fallback={options?.fallback}
        showRetryButton={options?.showRetryButton}
        onError={options?.onError}
      >
        <WrappedComponent {...props} />
      </ConnectivityErrorBoundary>
    );
  };

  ComponentWithErrorBoundary.displayName = `withConnectivityErrorBoundary(${WrappedComponent.displayName || WrappedComponent.name})`;
  
  return ComponentWithErrorBoundary;
}

/**
 * Simple connectivity status indicator component
 */
export function ConnectivityIndicator({ className }: { className?: string }) {
  const { status } = useRobustConnectivityMonitor();
  
  if (status.isConnected) {
    return null; // Don't show anything when connected
  }
  
  return (
    <div className={`fixed top-4 right-4 bg-red-500 text-white px-3 py-2 rounded-lg shadow-lg z-50 ${className}`}>
      <div className="flex items-center gap-2">
        <WifiOff className="w-4 h-4" />
        <span className="text-sm">Connection lost</span>
        {status.retryCount > 0 && (
          <span className="text-xs opacity-75">
            (Retry {status.retryCount}/5)
          </span>
        )}
      </div>
    </div>
  );
}

// Import the hook from robust connectivity-monitor
import { useRobustConnectivityMonitor } from '@/lib/connectivity-monitor-robust';

export default ConnectivityErrorBoundary;
