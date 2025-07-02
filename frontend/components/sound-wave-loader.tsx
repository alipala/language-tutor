'use client';

import React from 'react';

interface SoundWaveLoaderProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  color?: string;
  text?: string;
  subtext?: string;
}

export default function SoundWaveLoader({ 
  className = '', 
  size = 'md',
  color = '#4ECFBF',
  text = 'Loading...',
  subtext = 'Preparing your language learning experience'
}: SoundWaveLoaderProps) {
  // Size configurations
  const sizeConfig = {
    sm: {
      container: 'w-16 h-12',
      bar: 'w-1',
      spacing: 'gap-1'
    },
    md: {
      container: 'w-24 h-16',
      bar: 'w-1.5',
      spacing: 'gap-1.5'
    },
    lg: {
      container: 'w-32 h-20',
      bar: 'w-2',
      spacing: 'gap-2'
    }
  };

  const config = sizeConfig[size];

  // Generate 9 bars for realistic sound wave
  const bars = Array.from({ length: 9 }, (_, i) => i);

  return (
    <div className={`flex flex-col items-center ${className}`}>
      {/* Sound Wave Animation */}
      <div className={`flex items-end justify-center ${config.container} ${config.spacing} mb-4`}>
        {bars.map((bar, index) => (
          <div
            key={bar}
            className={`${config.bar} bg-current rounded-full`}
            style={{
              color: color,
              height: '20%',
              animation: `soundWave 1.5s ease-in-out infinite`,
              animationDelay: `${index * 0.1}s`,
            }}
          />
        ))}
      </div>

      {/* Text */}
      <div className="text-center">
        <p className="text-gray-800 text-xl font-medium mb-1">{text}</p>
        {subtext && (
          <p className="text-gray-600 text-sm">{subtext}</p>
        )}
      </div>

      <style jsx>{`
        @keyframes soundWave {
          0%, 100% {
            height: 20%;
            opacity: 0.4;
          }
          10% {
            height: 30%;
            opacity: 0.6;
          }
          20% {
            height: 60%;
            opacity: 0.8;
          }
          30% {
            height: 80%;
            opacity: 1;
          }
          40% {
            height: 100%;
            opacity: 1;
          }
          50% {
            height: 85%;
            opacity: 0.9;
          }
          60% {
            height: 70%;
            opacity: 0.8;
          }
          70% {
            height: 45%;
            opacity: 0.7;
          }
          80% {
            height: 25%;
            opacity: 0.5;
          }
          90% {
            height: 35%;
            opacity: 0.6;
          }
        }
      `}</style>
    </div>
  );
}
