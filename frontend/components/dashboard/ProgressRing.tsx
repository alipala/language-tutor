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
  const isCompleted = percentage >= 100;

  // Color based on progress
  const getProgressColor = (progress: number) => {
    if (progress >= 100) return { from: '#10B981', to: '#059669', glow: '#10B981' }; // Vibrant Green for completion
    if (progress >= 80) return { from: '#10B981', to: '#34D399', glow: null }; // Green
    if (progress >= 60) return { from: '#4ECFBF', to: '#44D9E8', glow: null }; // Teal
    if (progress >= 40) return { from: '#F59E0B', to: '#FBBF24', glow: null }; // Orange
    return { from: '#EF4444', to: '#F87171', glow: null }; // Red
  };

  const colors = getProgressColor(percentage);

  return (
    <div className={`flex items-center space-x-4 ${className}`}>
      {/* Progress Ring */}
      <div className="relative">
        {/* Glow effect for 100% completion */}
        {isCompleted && (
          <div 
            className="absolute inset-0 rounded-full animate-pulse"
            style={{
              background: `radial-gradient(circle, ${colors.glow}40 0%, transparent 70%)`,
              filter: 'blur(8px)'
            }}
          />
        )}
        
        <svg 
          width={size} 
          height={size} 
          className="transform -rotate-90 relative z-10"
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
            className={isCompleted ? "text-green-100" : "text-gray-200"}
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
              strokeDashoffset: animated ? strokeDashoffset : circumference,
              filter: isCompleted ? 'drop-shadow(0 0 4px rgba(16, 185, 129, 0.5))' : 'none'
            }}
          />
          
          {/* Gradient definition */}
          <defs>
            <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor={colors.from} />
              <stop offset="100%" stopColor={colors.to} />
            </linearGradient>
          </defs>
          
          {/* Checkmark for 100% completion */}
          {isCompleted && (
            <g transform={`translate(${size / 2}, ${size / 2}) rotate(90)`}>
              <circle
                cx="0"
                cy="0"
                r={radius * 0.6}
                fill="#10B981"
                className="animate-pulse"
              />
              <path
                d={`M ${-radius * 0.3} ${0} L ${-radius * 0.1} ${radius * 0.25} L ${radius * 0.35} ${-radius * 0.3}`}
                stroke="white"
                strokeWidth={strokeWidth * 0.8}
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </g>
          )}
        </svg>
      </div>
      
      {/* Percentage text - positioned to the right of the circle */}
      <div className="text-center">
        <div className={`font-bold ${isCompleted ? 'text-green-600' : 'text-gray-800'} ${size >= 120 ? 'text-2xl' : 'text-xl'}`}>
          {Math.round(percentage)}%
        </div>
        <div className={`${isCompleted ? 'text-green-600 font-semibold' : 'text-gray-500'} ${size >= 120 ? 'text-sm' : 'text-xs'} leading-tight`}>
          {isCompleted ? '🎉 Completed!' : 'Complete'}
        </div>
      </div>
    </div>
  );
};

export default ProgressRing;
