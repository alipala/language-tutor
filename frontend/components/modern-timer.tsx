'use client';

import React, { useState, useEffect } from 'react';
import { formatTime } from '@/lib/guest-utils';

interface ModernTimerProps {
  initialTime: number; // in seconds
  isActive: boolean;
  onTimeUp: () => void;
  onTimeWarning?: (remainingTime: number) => void;
  warningThreshold?: number; // seconds before end to trigger warning
  className?: string;
}

export default function ModernTimer({
  initialTime,
  isActive,
  onTimeUp,
  onTimeWarning,
  warningThreshold = 30,
  className = ''
}: ModernTimerProps) {
  const [timeRemaining, setTimeRemaining] = useState(initialTime);
  const [hasWarned, setHasWarned] = useState(false);

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

  // Calculate progress percentage
  const progressPercentage = (timeRemaining / initialTime) * 100;

  // Determine color based on remaining time
  const getTimerColor = () => {
    if (timeRemaining <= 10) return 'text-red-500';
    if (timeRemaining <= 30) return 'text-orange-500';
    if (timeRemaining <= 60) return 'text-yellow-500';
    return 'text-green-500';
  };

  const getProgressColor = () => {
    if (timeRemaining <= 10) return 'stroke-red-500';
    if (timeRemaining <= 30) return 'stroke-orange-500';
    if (timeRemaining <= 60) return 'stroke-yellow-500';
    return 'stroke-green-500';
  };

  const getBackgroundColor = () => {
    if (timeRemaining <= 10) return 'bg-red-50 border-red-200';
    if (timeRemaining <= 30) return 'bg-orange-50 border-orange-200';
    if (timeRemaining <= 60) return 'bg-yellow-50 border-yellow-200';
    return 'bg-green-50 border-green-200';
  };

  // Calculate stroke dash array for circular progress
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (progressPercentage / 100) * circumference;

  return (
    <div className={`flex items-center justify-center ${className}`}>
      <div className={`relative p-4 rounded-2xl border-2 transition-all duration-300 ${getBackgroundColor()}`}>
        {/* Circular Progress Ring */}
        <div className="relative w-24 h-24 flex items-center justify-center">
          <svg
            className="w-24 h-24 transform -rotate-90"
            viewBox="0 0 100 100"
          >
            {/* Background circle */}
            <circle
              cx="50"
              cy="50"
              r={radius}
              stroke="currentColor"
              strokeWidth="8"
              fill="transparent"
              className="text-gray-200"
            />
            {/* Progress circle */}
            <circle
              cx="50"
              cy="50"
              r={radius}
              stroke="currentColor"
              strokeWidth="8"
              fill="transparent"
              strokeDasharray={strokeDasharray}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              className={`transition-all duration-1000 ease-out ${getProgressColor()}`}
            />
          </svg>
          
          {/* Timer display in center */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className={`text-2xl font-bold transition-colors duration-300 ${getTimerColor()}`}>
              {formatTime(timeRemaining)}
            </div>
            <div className="text-xs text-gray-500 font-medium mt-1">
              {isActive ? 'remaining' : 'ready'}
            </div>
          </div>
        </div>

        {/* Status indicator */}
        <div className="flex items-center justify-center mt-3">
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
      </div>
    </div>
  );
}
