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
        backgroundColor: 'var(--turquoise)',
        backgroundSize: 'cover',
        backgroundAttachment: 'fixed'
      }}
    >
      {children}
    </div>
  );
}
