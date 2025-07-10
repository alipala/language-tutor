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
  
  // Dragging state
  const [isDragging, setIsDragging] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [isInitialized, setIsInitialized] = useState(false);
  
  const timerRef = useRef<HTMLDivElement>(null);

  // Initialize position on first render
  useEffect(() => {
    if (!isInitialized && typeof window !== 'undefined') {
      // Default position: top right with some margin
      const defaultX = window.innerWidth - 200; // 200px from right edge
      const defaultY = 120; // 120px from top
      
      setPosition({ x: defaultX, y: defaultY });
      setIsInitialized(true);
    }
  }, [isInitialized]);

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
    handleDragStart(e.clientX, e.clientY);
  }, [handleDragStart]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    handleDragMove(e.clientX, e.clientY);
  }, [handleDragMove]);

  const handleMouseUp = useCallback(() => {
    handleDragEnd();
  }, [handleDragEnd]);

  // Touch event handlers
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    const touch = e.touches[0];
    handleDragStart(touch.clientX, touch.clientY);
  }, [handleDragStart]);

  const handleTouchMove = useCallback((e: TouchEvent) => {
    const touch = e.touches[0];
    handleDragMove(touch.clientX, touch.clientY);
  }, [handleDragMove]);

  const handleTouchEnd = useCallback(() => {
    handleDragEnd();
  }, [handleDragEnd]);

  // Add global event listeners for drag with smooth transitions
  useEffect(() => {
    if (isDragging) {
      // Prevent page scrolling during drag
      document.body.style.overflow = 'hidden';
      document.body.style.userSelect = 'none';
      
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.addEventListener('touchmove', handleTouchMove);
      document.addEventListener('touchend', handleTouchEnd);
    }

    return () => {
      // Restore page scrolling
      document.body.style.overflow = '';
      document.body.style.userSelect = '';
      
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
      className={`fixed z-50 select-none ${className}`}
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        cursor: isDragging ? 'grabbing' : 'grab',
        transform: isDragging ? 'scale(1.05)' : 'scale(1)',
        transition: isDragging ? 'none' : 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      }}
      onMouseDown={handleMouseDown}
      onTouchStart={handleTouchStart}
    >
      {/* Clean Analog Timer - Single View */}
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
    </div>
  );
}
