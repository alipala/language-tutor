import React from 'react';

interface GradientBackgroundProps {
  children: React.ReactNode;
  className?: string;
}

export default function GradientBackground({ children, className = '' }: GradientBackgroundProps) {
  return (
    <div 
      className={`min-h-screen w-full ${className}`}
      style={{
        backgroundImage: 'linear-gradient(32deg, #0bd1ff 0%, #ffa3ff 50%, #ffd34e 100%)',
        backgroundSize: 'cover',
        backgroundAttachment: 'fixed'
      }}
    >
      {children}
    </div>
  );
}
