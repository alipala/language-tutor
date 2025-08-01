'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { formatTime } from '@/lib/guest-utils';

interface DraggableTimerProps {
  initialTime: number; // in seconds
  isActive: boolean;
  onTimeUp: () => void;
  onTimeWarning?: (remainingTime: number) => void;
  warningThreshold?: number; // seconds before end to trigger warning
  className?: string;
}

export default function DraggableTimer({
  initialTime,
  isActive,
  onTimeUp,
  onTimeWarning,
  warningThreshold = 30,
  className = ''
}: DraggableTimerProps) {
  const [timeRemaining, setTimeRemaining] = useState(initialTime);
  const [hasWarned, setHasWarned] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  
  // Dragging state
  const [isDragging, setIsDragging] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [isInitialized, setIsInitialized] = useState(false);
  
  const timerRef = useRef<HTMLDivElement>(null);

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

  // Initialize position on first render
  useEffect(() => {
    if (!isInitialized && typeof window !== 'undefined') {
      // Mobile: position at top center, Desktop: top right
      const defaultX = isMobile 
        ? (window.innerWidth / 2) - (isMobile ? 80 : 100) // Center for mobile
        : window.innerWidth - 200; // 200px from right edge for desktop
      const defaultY = isMobile ? 80 : 120; // Higher for mobile to avoid navbar
      
      setPosition({ x: defaultX, y: defaultY });
      setIsInitialized(true);
    }
  }, [isInitialized, isMobile]);

  // Reset timer when initialTime changes
  useEffect(() => {
    setTimeRemaining(initialTime);
    setHasWarned(false);
  }, [initialTime]);

  // Timer countdown effect
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;

    if (isActive && timeRemaining > 0) {
      interval = setInterval(() => {
        setTimeRemaining((prevTime) => {
          const newTime = prevTime - 1;

          // Trigger warning if threshold reached and not already warned
          if (newTime === warningThreshold && !hasWarned && onTimeWarning) {
            setHasWarned(true);
            onTimeWarning(newTime);
          }

          // Trigger time up when reaching 0
          if (newTime <= 0) {
            onTimeUp();
            return 0;
          }

          return newTime;
        });
      }, 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isActive, timeRemaining, warningThreshold, hasWarned, onTimeWarning, onTimeUp]);

  // Handle drag start
  const handleDragStart = useCallback((clientX: number, clientY: number) => {
    if (!timerRef.current) return;
    
    setIsDragging(true);
    
    const rect = timerRef.current.getBoundingClientRect();
    setDragOffset({
      x: clientX - rect.left,
      y: clientY - rect.top
    });
  }, []);

  // Handle drag move with smooth transitions
  const handleDragMove = useCallback((clientX: number, clientY: number) => {
    if (!isDragging) return;

    const newX = clientX - dragOffset.x;
    const newY = clientY - dragOffset.y;

    // Constrain to viewport bounds
    const timerWidth = 160;
    const timerHeight = 160;
    const maxX = window.innerWidth - timerWidth;
    const maxY = window.innerHeight - timerHeight;
    
    const constrainedX = Math.max(0, Math.min(newX, maxX));
    const constrainedY = Math.max(0, Math.min(newY, maxY));

    setPosition({ x: constrainedX, y: constrainedY });
  }, [isDragging, dragOffset]);

  // Handle drag end
  const handleDragEnd = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Mouse event handlers
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    handleDragStart(e.clientX, e.clientY);
  }, [handleDragStart]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (isDragging) {
      e.preventDefault();
      e.stopPropagation();
      handleDragMove(e.clientX, e.clientY);
    }
  }, [handleDragMove, isDragging]);

  const handleMouseUp = useCallback((e: MouseEvent) => {
    if (isDragging) {
      e.preventDefault();
      e.stopPropagation();
      handleDragEnd();
    }
  }, [handleDragEnd, isDragging]);

  // More selective touch event handlers for real mobile devices
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    // Only prevent default on the timer itself, not globally
    e.preventDefault();
    
    const touch = e.touches[0];
    if (touch) {
      handleDragStart(touch.clientX, touch.clientY);
    }
  }, [handleDragStart]);

  const handleTouchMove = useCallback((e: TouchEvent) => {
    if (isDragging && e.touches.length > 0) {
      // Only prevent default when actively dragging
      e.preventDefault();
      
      const touch = e.touches[0];
      if (touch) {
        handleDragMove(touch.clientX, touch.clientY);
      }
    }
  }, [handleDragMove, isDragging]);

  const handleTouchEnd = useCallback((e: TouchEvent) => {
    if (isDragging) {
      // Only prevent default when we were actually dragging
      e.preventDefault();
      
      handleDragEnd();
    }
  }, [handleDragEnd, isDragging]);

  // More selective global event listeners - only when actively dragging
  useEffect(() => {
    if (isDragging) {
      // Only prevent scrolling during drag, but allow other interactions
      document.body.style.userSelect = 'none';
      document.body.style.webkitUserSelect = 'none';
      
      // Add event listeners for drag continuation
      document.addEventListener('mousemove', handleMouseMove, { passive: false });
      document.addEventListener('mouseup', handleMouseUp, { passive: false });
      document.addEventListener('touchmove', handleTouchMove, { passive: false });
      document.addEventListener('touchend', handleTouchEnd, { passive: false });
    }

    return () => {
      // Restore body styles
      document.body.style.userSelect = '';
      document.body.style.webkitUserSelect = '';
      
      // Remove event listeners
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
    };
  }, [isDragging, handleMouseMove, handleMouseUp, handleTouchMove, handleTouchEnd]);

  // Calculate progress percentage
  const progressPercentage = (timeRemaining / initialTime) * 100;

  // Determine color based on remaining time
  const getTimerColor = () => {
    if (timeRemaining <= 10) return 'text-red-500';
    if (timeRemaining <= 30) return 'text-orange-500';
    if (timeRemaining <= 60) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getProgressColor = () => {
    if (timeRemaining <= 10) return 'stroke-red-500';
    if (timeRemaining <= 30) return 'stroke-orange-500';
    if (timeRemaining <= 60) return 'stroke-yellow-600';
    return 'stroke-green-600';
  };

  const getBackgroundColor = () => {
    if (timeRemaining <= 10) return 'bg-red-50 border-red-200';
    if (timeRemaining <= 30) return 'bg-orange-50 border-orange-200';
    if (timeRemaining <= 60) return 'bg-[#FFF8E1] border-[#FFD63A]';
    return 'bg-green-50 border-green-200';
  };

  if (!isInitialized) {
    return null; // Don't render until position is initialized
  }

  return (
    <div
      ref={timerRef}
      className={`fixed z-[9999] select-none ${className}`}
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        cursor: isDragging ? 'grabbing' : 'grab',
        transform: isDragging ? 'scale(1.05)' : 'scale(1)',
        transition: isDragging ? 'none' : 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        // Enhanced touch prevention styles
        touchAction: 'none',
        userSelect: 'none',
        WebkitUserSelect: 'none',
        WebkitTouchCallout: 'none',
        WebkitUserDrag: 'none',
      } as React.CSSProperties & { WebkitUserDrag?: string; WebkitTouchCallout?: string }}
      onMouseDown={handleMouseDown}
      onTouchStart={handleTouchStart}
    >
      {isMobile ? (
        /* Mobile: Compact Digital Timer */
        <div className={`relative px-3 py-2 rounded-lg border-2 transition-all duration-300 shadow-lg backdrop-blur-sm ${getBackgroundColor()}`}>
          {/* Drag handle indicator */}
          <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-6 h-1 bg-gray-400 rounded-full opacity-60"></div>
          
          {/* Digital Timer Display */}
          <div className="flex items-center gap-2">
            {/* Status dot */}
            <div className={`w-2 h-2 rounded-full transition-all duration-300 ${
              isActive 
                ? timeRemaining <= 10 
                  ? 'bg-red-500 animate-pulse' 
                  : timeRemaining <= 30 
                    ? 'bg-orange-500 animate-pulse' 
                    : 'bg-green-500'
                : 'bg-gray-300'
            }`} />
            
            {/* Time display */}
            <div className={`text-sm font-bold transition-colors duration-300 ${getTimerColor()}`}>
              {formatTime(timeRemaining)}
            </div>
            
            {/* Progress bar */}
            <div className="flex-1 h-1 bg-gray-200 rounded-full overflow-hidden ml-2">
              <div 
                className={`h-full transition-all duration-1000 ease-out rounded-full ${
                  timeRemaining <= 10 ? 'bg-red-500' :
                  timeRemaining <= 30 ? 'bg-orange-500' :
                  timeRemaining <= 60 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
          </div>

          {/* Warning pulse effect for low time */}
          {isActive && timeRemaining <= 10 && (
            <div className="absolute inset-0 rounded-lg border-2 border-red-400 animate-ping opacity-75" />
          )}
        </div>
      ) : (
        /* Desktop: Analog Timer */
        <div className={`relative p-3 rounded-2xl border-2 transition-all duration-300 shadow-lg backdrop-blur-sm ${getBackgroundColor()}`}>
          {/* Drag handle indicator */}
          <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-8 h-1 bg-gray-400 rounded-full opacity-60"></div>
          
          {/* Circular Progress Ring */}
          <div className="relative w-20 h-20 flex items-center justify-center">
            <svg
              className="w-20 h-20 transform -rotate-90"
              viewBox="0 0 80 80"
            >
              {/* Background circle */}
              <circle
                cx="40"
                cy="40"
                r="35"
                stroke="currentColor"
                strokeWidth="6"
                fill="transparent"
                className="text-gray-200"
              />
              {/* Progress circle */}
              <circle
                cx="40"
                cy="40"
                r="35"
                stroke="currentColor"
                strokeWidth="6"
                fill="transparent"
                strokeDasharray={2 * Math.PI * 35}
                strokeDashoffset={2 * Math.PI * 35 - (progressPercentage / 100) * 2 * Math.PI * 35}
                strokeLinecap="round"
                className={`transition-all duration-1000 ease-out ${getProgressColor()}`}
              />
            </svg>
            
            {/* Timer display in center */}
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <div className={`text-lg font-bold transition-colors duration-300 ${getTimerColor()}`}>
                {formatTime(timeRemaining)}
              </div>
              <div className="text-xs text-gray-500 font-medium">
                {isActive ? 'left' : 'ready'}
              </div>
            </div>
          </div>

          {/* Status indicator */}
          <div className="flex items-center justify-center mt-2">
            <div className={`w-2 h-2 rounded-full transition-all duration-300 ${
              isActive 
                ? timeRemaining <= 10 
                  ? 'bg-red-500 animate-pulse' 
                  : timeRemaining <= 30 
                    ? 'bg-orange-500 animate-pulse' 
                    : 'bg-green-500'
                : 'bg-gray-300'
            }`} />
            <span className="text-xs text-gray-600 ml-2 font-medium">
              {isActive ? 'Active' : 'Paused'}
            </span>
          </div>

          {/* Warning pulse effect for low time */}
          {isActive && timeRemaining <= 10 && (
            <div className="absolute inset-0 rounded-2xl border-2 border-red-400 animate-ping opacity-75" />
          )}

          {/* Floating effect shadow */}
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-white/20 to-transparent pointer-events-none"></div>
        </div>
      )}
    </div>
  );
}
