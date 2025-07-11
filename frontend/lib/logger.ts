/**
 * Production-safe logging utility
 * Prevents console logs from appearing in production builds
 * while maintaining development debugging capabilities
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LoggerConfig {
  isDevelopment: boolean;
  isProduction: boolean;
  allowedLevels: LogLevel[];
}

class Logger {
  private config: LoggerConfig;

  constructor() {
    const nodeEnv = process.env.NODE_ENV || 'development';
    const isProduction = nodeEnv === 'production';
    const isDevelopment = nodeEnv === 'development';

    this.config = {
      isDevelopment,
      isProduction,
      // In production, only allow error logs (for critical issues)
      // In development, allow all log levels
      allowedLevels: isProduction ? ['error'] : ['debug', 'info', 'warn', 'error']
    };
  }

  private shouldLog(level: LogLevel): boolean {
    return this.config.allowedLevels.includes(level);
  }

  private formatMessage(level: LogLevel, message: any, ...args: any[]): void {
    if (!this.shouldLog(level)) {
      return;
    }

    // In development, use original console methods with styling
    if (this.config.isDevelopment) {
      const timestamp = new Date().toISOString();
      const prefix = `[${timestamp}] [${level.toUpperCase()}]`;
      
      switch (level) {
        case 'debug':
          console.debug(`%c${prefix}`, 'color: #6B7280', message, ...args);
          break;
        case 'info':
          console.info(`%c${prefix}`, 'color: #3B82F6', message, ...args);
          break;
        case 'warn':
          console.warn(`%c${prefix}`, 'color: #F59E0B', message, ...args);
          break;
        case 'error':
          console.error(`%c${prefix}`, 'color: #EF4444', message, ...args);
          break;
      }
    } else if (this.config.isProduction && level === 'error') {
      // In production, only log errors (for monitoring/debugging critical issues)
      // Remove sensitive information and keep it minimal
      console.error('[ERROR]', message, ...args);
    }
  }

  /**
   * Debug level logging - only shows in development
   */
  debug(message: any, ...args: any[]): void {
    this.formatMessage('debug', message, ...args);
  }

  /**
   * Info level logging - only shows in development
   */
  info(message: any, ...args: any[]): void {
    this.formatMessage('info', message, ...args);
  }

  /**
   * Warning level logging - only shows in development
   */
  warn(message: any, ...args: any[]): void {
    this.formatMessage('warn', message, ...args);
  }

  /**
   * Error level logging - shows in both development and production
   * Use sparingly in production for critical errors only
   */
  error(message: any, ...args: any[]): void {
    this.formatMessage('error', message, ...args);
  }

  /**
   * Log API responses (development only)
   */
  apiResponse(endpoint: string, response: any): void {
    if (this.config.isDevelopment) {
      this.debug(`API Response [${endpoint}]:`, response);
    }
  }

  /**
   * Log API errors (production safe - removes sensitive data)
   */
  apiError(endpoint: string, error: any): void {
    if (this.config.isDevelopment) {
      this.error(`API Error [${endpoint}]:`, error);
    } else {
      // In production, log minimal error info without sensitive data
      this.error(`API Error [${endpoint}]:`, {
        status: error?.status || 'unknown',
        message: error?.message || 'Request failed'
      });
    }
  }

  /**
   * Log user actions (development only)
   */
  userAction(action: string, data?: any): void {
    if (this.config.isDevelopment) {
      this.info(`User Action [${action}]:`, data);
    }
  }

  /**
   * Log component lifecycle (development only)
   */
  component(componentName: string, event: string, data?: any): void {
    if (this.config.isDevelopment) {
      this.debug(`Component [${componentName}] ${event}:`, data);
    }
  }

  /**
   * Log authentication events (production safe)
   */
  auth(event: string, data?: any): void {
    if (this.config.isDevelopment) {
      this.info(`Auth [${event}]:`, data);
    } else {
      // In production, only log auth events without sensitive data
      this.info(`Auth [${event}]`);
    }
  }
}

// Create singleton instance
const logger = new Logger();

// Export the logger instance
export default logger;

// Export individual methods for convenience
export const { debug, info, warn, error, apiResponse, apiError, userAction, component, auth } = logger;

// Legacy console replacement (for gradual migration)
export const console_safe = {
  log: logger.debug,
  info: logger.info,
  warn: logger.warn,
  error: logger.error,
  debug: logger.debug
};
