'use client';

import React, { useState, useEffect } from 'react';
import { X, AlertCircle, CheckCircle, Info } from 'lucide-react';

export type NotificationType = 'success' | 'error' | 'info' | 'warning';

interface NotificationProps {
  type: NotificationType;
  message: string;
  isOpen: boolean;
  onClose: () => void;
  autoClose?: boolean;
  duration?: number;
}

export default function Notification({
  type,
  message,
  isOpen,
  onClose,
  autoClose = true,
  duration = 5000
}: NotificationProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIsVisible(true);
      
      if (autoClose) {
        const timer = setTimeout(() => {
          setIsVisible(false);
          setTimeout(onClose, 300); // Allow animation to complete before calling onClose
        }, duration);
        
        return () => clearTimeout(timer);
      }
    } else {
      setIsVisible(false);
    }
  }, [isOpen, autoClose, duration, onClose]);

  const getIcon = () => {
    switch (type) {
      case 'success':
        return <CheckCircle className={`h-5 w-5 ${getIconColor()}`} />;
      case 'error':
        return <AlertCircle className={`h-5 w-5 ${getIconColor()}`} />;
      case 'warning':
        return <AlertCircle className={`h-5 w-5 ${getIconColor()}`} />;
      case 'info':
      default:
        return <Info className={`h-5 w-5 ${getIconColor()}`} />;
    }
  };

  const getBackgroundColor = () => {
    switch (type) {
      case 'success':
        return 'bg-gradient-to-r from-emerald-50 to-teal-50 border-emerald-200 shadow-emerald-100/50';
      case 'error':
        return 'bg-gradient-to-r from-rose-50 to-pink-50 border-rose-200 shadow-rose-100/50';
      case 'warning':
        return 'bg-gradient-to-r from-amber-50 to-yellow-50 border-amber-200 shadow-amber-100/50';
      case 'info':
      default:
        return 'bg-gradient-to-r from-teal-50 to-cyan-50 border-teal-200 shadow-teal-100/50';
    }
  };

  const getTextColor = () => {
    switch (type) {
      case 'success':
        return 'text-emerald-800';
      case 'error':
        return 'text-rose-800';
      case 'warning':
        return 'text-amber-800';
      case 'info':
      default:
        return 'text-teal-800';
    }
  };

  const getIconColor = () => {
    switch (type) {
      case 'success':
        return 'text-emerald-600';
      case 'error':
        return 'text-rose-600';
      case 'warning':
        return 'text-amber-600';
      case 'info':
      default:
        return 'text-teal-600';
    }
  };

  const getProgressColor = () => {
    switch (type) {
      case 'success':
        return 'bg-emerald-400';
      case 'error':
        return 'bg-rose-400';
      case 'warning':
        return 'bg-amber-400';
      case 'info':
      default:
        return 'bg-teal-400';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed top-4 right-4 z-50 max-w-md w-full sm:w-96">
      <div 
        className={`${getBackgroundColor()} border backdrop-blur-sm rounded-lg shadow-lg transform transition-all duration-300 ${
          isVisible ? 'translate-y-0 opacity-100' : 'translate-y-[-20px] opacity-0'
        }`}
      >
        <div className="p-4 flex items-start">
          <div className="flex-shrink-0">
            {getIcon()}
          </div>
          <div className="ml-3 flex-1">
            <p className={`text-sm font-medium ${getTextColor()}`}>{message}</p>
          </div>
          <div className="ml-4 flex-shrink-0 flex">
            <button
              className={`bg-transparent rounded-md inline-flex ${getTextColor()} hover:opacity-70 focus:outline-none transition-opacity`}
              onClick={() => {
                setIsVisible(false);
                setTimeout(onClose, 300);
              }}
            >
              <span className="sr-only">Close</span>
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
        {autoClose && (
          <div className="h-1 bg-white/20 rounded-b-lg overflow-hidden">
            <div 
              className={`h-full ${getProgressColor()}`}
              style={{ 
                width: '100%', 
                animation: `shrink ${duration}ms linear forwards` 
              }}
            />
          </div>
        )}
      </div>
      <style jsx>{`
        @keyframes shrink {
          from { width: 100%; }
          to { width: 0%; }
        }
      `}</style>
    </div>
  );
}

// Context for global notification management
import { createContext, useContext } from 'react';

interface NotificationContextType {
  showNotification: (type: NotificationType, message: string, duration?: number) => void;
  hideNotification: () => void;
}

export const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [notification, setNotification] = useState<{
    type: NotificationType;
    message: string;
    isOpen: boolean;
    duration: number;
  }>({
    type: 'info',
    message: '',
    isOpen: false,
    duration: 5000
  });

  const showNotification = (type: NotificationType, message: string, duration = 5000) => {
    setNotification({
      type,
      message,
      isOpen: true,
      duration
    });
  };

  const hideNotification = () => {
    setNotification(prev => ({
      ...prev,
      isOpen: false
    }));
  };

  return (
    <NotificationContext.Provider value={{ showNotification, hideNotification }}>
      {children}
      <Notification
        type={notification.type}
        message={notification.message}
        isOpen={notification.isOpen}
        onClose={hideNotification}
        duration={notification.duration}
      />
    </NotificationContext.Provider>
  );
}

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
}
