'use client';

import React from 'react';

interface ProgressRingProps {
  percentage: number;
  size?: number;
  strokeWidth?: number;
  animated?: boolean;
  className?: string;
}

export const ProgressRing: React.FC<ProgressRingProps> = ({ 
  percentage, 
  size = 120, 
  strokeWidth = 8,
  animated = true,
  className = ""
}) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const strokeDasharray = `${circumference} ${circumference}`;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  // Color based on progress
  const getProgressColor = (progress: number) => {
    if (progress >= 80) return { from: '#10B981', to: '#34D399' }; // Green
    if (progress >= 60) return { from: '#4ECFBF', to: '#44D9E8' }; // Teal
    if (progress >= 40) return { from: '#F59E0B', to: '#FBBF24' }; // Orange
    return { from: '#EF4444', to: '#F87171' }; // Red
  };

  const colors = getProgressColor(percentage);

  return (
    <div className={`flex items-center space-x-4 ${className}`}>
      {/* Progress Ring */}
      <div className="relative">
        <svg 
          width={size} 
          height={size} 
          className="transform -rotate-90"
          viewBox={`0 0 ${size} ${size}`}
        >
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="currentColor"
            strokeWidth={strokeWidth}
            fill="transparent"
            className="text-gray-200"
          />
          
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="url(#progressGradient)"
            strokeWidth={strokeWidth}
            fill="transparent"
            strokeDasharray={strokeDasharray}
            strokeDashoffset={animated ? strokeDashoffset : circumference}
            strokeLinecap="round"
            className={animated ? "transition-all duration-1000 ease-out" : ""}
            style={{
              strokeDashoffset: animated ? strokeDashoffset : circumference
            }}
          />
          
          {/* Gradient definition */}
          <defs>
            <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor={colors.from} />
              <stop offset="100%" stopColor={colors.to} />
            </linearGradient>
          </defs>
        </svg>
      </div>
      
      {/* Percentage text - positioned to the right of the circle */}
      <div className="text-center">
        <div className={`font-bold text-gray-800 ${size >= 120 ? 'text-2xl' : 'text-xl'}`}>
          {Math.round(percentage)}%
        </div>
        <div className={`text-gray-500 ${size >= 120 ? 'text-sm' : 'text-xs'} leading-tight`}>
          Complete
        </div>
      </div>
    </div>
  );
};

export default ProgressRing;
