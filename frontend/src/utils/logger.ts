/**
 * NEW-CRITICAL-D FIX: Production-safe logging utility
 *
 * In production, logs are suppressed to prevent:
 * - Sensitive data exposure (user info, API responses)
 * - Stack traces revealing code structure
 * - Config values in console
 *
 * In development, logs work normally for debugging.
 */

const isDev = import.meta.env.DEV;

export const logger = {
  /**
   * Log error messages
   * In production: silent
   * In development: outputs to console.error
   */
  error: (message: string, ...args: any[]) => {
    if (isDev) {
      console.error(message, ...args);
    }
    // In production, could send to error tracking service (e.g., Sentry)
  },

  /**
   * Log warning messages
   * In production: silent
   * In development: outputs to console.warn
   */
  warn: (message: string, ...args: any[]) => {
    if (isDev) {
      console.warn(message, ...args);
    }
  },

  /**
   * Log informational messages
   * In production: silent
   * In development: outputs to console.log
   */
  log: (message: string, ...args: any[]) => {
    if (isDev) {
      console.log(message, ...args);
    }
  },

  /**
   * Log debug messages
   * In production: silent
   * In development: outputs to console.debug
   */
  debug: (message: string, ...args: any[]) => {
    if (isDev) {
      console.debug(message, ...args);
    }
  },
};
