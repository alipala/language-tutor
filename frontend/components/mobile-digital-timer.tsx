'use client';

import React, { useState, useEffect } from 'react';

interface MobileDigitalTimerProps {
  initialTime: number; // in seconds
  isActive: boolean;
  onTimeUp: () => void;
  className?: string;
}

export default function MobileDigitalTimer({ 
  initialTime, 
  isActive, 
  onTimeUp, 
  className = '' 
}: MobileDigitalTimerProps) {
  const [timeLeft, setTimeLeft] = useState(initialTime);
  const [isMobile, setIsMobile] = useState(false);

  // Detect mobile device
  useEffect(() => {
    const checkMobile = () => {
      const isMobileDevice = window.innerWidth < 768 || 
        /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
      setIsMobile(isMobileDevice);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Timer logic
  useEffect(() => {
    if (!isActive || timeLeft <= 0) return;

    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          onTimeUp();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isActive, timeLeft, onTimeUp]);

  // Reset timer when initialTime changes
  useEffect(() => {
    setTimeLeft(initialTime);
  }, [initialTime]);

  // Format time as MM:SS
  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  // Get status color based on time remaining
  const getStatusColor = (): string => {
    const percentage = (timeLeft / initialTime) * 100;
    if (percentage > 50) return '#10B981'; // Green
    if (percentage > 25) return '#F59E0B'; // Yellow
    return '#EF4444'; // Red
  };

  // Get status text
  const getStatusText = (): string => {
    if (!isActive) return 'Paused';
    if (timeLeft === 0) return 'Time Up';
    return 'Active';
  };

  // Only show digital timer on mobile devices
  if (!isMobile) return null;

  return (
    <div className={`mobile-digital-timer ${className}`}>
      <div className="flex items-center gap-2">
        {/* Timer Display */}
        <div 
          className="font-mono text-lg font-bold"
          style={{ color: getStatusColor() }}
        >
          {formatTime(timeLeft)}
        </div>
        
        {/* Status Indicator */}
        <div className="flex items-center gap-1">
          <div 
            className={`w-2 h-2 rounded-full ${isActive && timeLeft > 0 ? 'animate-pulse' : ''}`}
            style={{ backgroundColor: getStatusColor() }}
          />
          <span className="text-xs text-gray-600 font-medium">
            {getStatusText()}
          </span>
        </div>
      </div>
    </div>
  );
}
