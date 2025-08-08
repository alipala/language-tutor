'use client';

import React, { useEffect, useState } from 'react';
import { Clock, MessageCircle, AlertCircle, Info } from 'lucide-react';

interface TimeoutNotificationProps {
  show: boolean;
  message: string;
  type: 'timeout' | 'error' | 'info';
}

const ConversationHelpTimeoutNotification: React.FC<TimeoutNotificationProps> = ({
  show,
  message,
  type
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [animationState, setAnimationState] = useState<'entering' | 'visible' | 'exiting' | 'hidden'>('hidden');

  useEffect(() => {
    if (show) {
      setIsVisible(true);
      setAnimationState('entering');
      
      // Transition to visible state
      setTimeout(() => {
        setAnimationState('visible');
      }, 50);
    } else {
      setAnimationState('exiting');
      
      // Hide after exit animation
      setTimeout(() => {
        setIsVisible(false);
        setAnimationState('hidden');
      }, 300);
    }
  }, [show]);

  if (!isVisible) return null;

  const getIcon = () => {
    switch (type) {
      case 'timeout':
        return <Clock className="w-5 h-5 text-blue-600" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-orange-600" />;
      default:
        return <Info className="w-5 h-5 text-blue-600" />;
    }
  };

  const getBackgroundColor = () => {
    switch (type) {
      case 'timeout':
        return 'bg-blue-50 border-blue-200';
      case 'error':
        return 'bg-orange-50 border-orange-200';
      default:
        return 'bg-blue-50 border-blue-200';
    }
  };

  const getTextColor = () => {
    switch (type) {
      case 'timeout':
        return 'text-blue-800';
      case 'error':
        return 'text-orange-800';
      default:
        return 'text-blue-800';
    }
  };

  const getAnimationClasses = () => {
    switch (animationState) {
      case 'entering':
        return 'animate-slide-down-enter';
      case 'visible':
        return 'animate-slide-down-visible';
      case 'exiting':
        return 'animate-slide-down-exit';
      default:
        return '';
    }
  };

  return (
    <div className={`
      fixed top-4 left-1/2 transform -translate-x-1/2 z-50
      ${getBackgroundColor()} border rounded-lg shadow-lg p-4 max-w-sm mx-4
      ${getAnimationClasses()}
    `}>
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">
          {getIcon()}
        </div>
        <div className="flex-1">
          <p className={`text-sm font-medium ${getTextColor()}`}>
            {message}
          </p>
        </div>
        <div className="flex-shrink-0">
          <MessageCircle className="w-4 h-4 text-gray-400" />
        </div>
      </div>
    </div>
  );
};

export default ConversationHelpTimeoutNotification;
