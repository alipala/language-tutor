'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Clock, X, Zap } from 'lucide-react';
import { LowMinutesStatus } from '@/hooks/useLowMinutesAlert';
import { useRouter } from 'next/navigation';

interface LowMinutesAlertProps {
  status: LowMinutesStatus;
  onDismiss?: () => void;
  showDismiss?: boolean;
  className?: string;
}

export const LowMinutesAlert: React.FC<LowMinutesAlertProps> = ({
  status,
  onDismiss,
  showDismiss = false,
  className = ''
}) => {
  const router = useRouter();

  if (!status.has_low_minutes || status.is_unlimited) {
    return null;
  }

  const minutesRemaining = status.minutes_remaining || 0;
  const severity = status.severity || 'info';

  // Determine styling based on severity
  const getSeverityStyles = () => {
    switch (severity) {
      case 'critical':
        return {
          bg: 'bg-gradient-to-r from-red-50 to-orange-50',
          border: 'border-red-300',
          icon: 'text-red-600',
          text: 'text-red-900',
          button: 'bg-red-600 hover:bg-red-700'
        };
      case 'warning':
        return {
          bg: 'bg-gradient-to-r from-orange-50 to-yellow-50',
          border: 'border-orange-300',
          icon: 'text-orange-600',
          text: 'text-orange-900',
          button: 'bg-orange-600 hover:bg-orange-700'
        };
      default:
        return {
          bg: 'bg-gradient-to-r from-blue-50 to-cyan-50',
          border: 'border-blue-300',
          icon: 'text-blue-600',
          text: 'text-blue-900',
          button: 'bg-blue-600 hover:bg-blue-700'
        };
    }
  };

  const styles = getSeverityStyles();

  const handleUpgrade = () => {
    router.push('/profile#subscription');
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -20, scale: 0.95 }}
        transition={{ duration: 0.3 }}
        className={`relative ${styles.bg} border-2 ${styles.border} rounded-2xl p-4 shadow-lg ${className}`}
      >
        {/* Animated pulse effect for critical alerts */}
        {severity === 'critical' && (
          <motion.div
            className="absolute inset-0 rounded-2xl bg-red-400 opacity-20"
            animate={{
              scale: [1, 1.02, 1],
              opacity: [0.2, 0.3, 0.2]
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
        )}

        <div className="relative flex items-start gap-4">
          {/* Icon */}
          <div className={`flex-shrink-0 ${styles.icon}`}>
            {severity === 'critical' ? (
              <motion.div
                animate={{ rotate: [0, -10, 10, -10, 0] }}
                transition={{ duration: 0.5, repeat: Infinity, repeatDelay: 2 }}
              >
                <AlertTriangle className="h-6 w-6" />
              </motion.div>
            ) : (
              <Clock className="h-6 w-6" />
            )}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <h3 className={`font-bold text-lg ${styles.text} mb-1`}>
                  {minutesRemaining <= 0 ? (
                    '🚫 No Speaking Time Remaining'
                  ) : minutesRemaining === 1 ? (
                    '⏰ Only 1 Minute Left!'
                  ) : (
                    `⏰ Only ${minutesRemaining} Minutes Left!`
                  )}
                </h3>
                <p className={`text-sm ${styles.text} opacity-90`}>
                  {status.message || `You have ${minutesRemaining} minutes of speaking time remaining this ${status.period || 'period'}.`}
                </p>
              </div>

              {/* Dismiss button */}
              {showDismiss && onDismiss && (
                <button
                  onClick={onDismiss}
                  className={`flex-shrink-0 ${styles.icon} hover:opacity-70 transition-opacity`}
                  aria-label="Dismiss"
                >
                  <X className="h-5 w-5" />
                </button>
              )}
            </div>

            {/* Action button */}
            <motion.button
              onClick={handleUpgrade}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={`mt-3 ${styles.button} text-white font-semibold px-4 py-2 rounded-lg transition-colors flex items-center gap-2 text-sm`}
            >
              <Zap className="h-4 w-4" />
              Upgrade to Continue Learning
            </motion.button>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default LowMinutesAlert;
