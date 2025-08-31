'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Info, Sparkles } from 'lucide-react';

interface TooltipProps {
  content: string;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  className?: string;
  variant?: 'default' | 'info' | 'success' | 'premium';
  showIcon?: boolean;
  delay?: number;
}

export function Tooltip({ 
  content, 
  children, 
  position = 'top', 
  className = '', 
  variant = 'default',
  showIcon = false,
  delay = 300
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [timeoutId, setTimeoutId] = useState<NodeJS.Timeout | null>(null);

  const handleMouseEnter = () => {
    const id = setTimeout(() => setIsVisible(true), delay);
    setTimeoutId(id);
  };

  const handleMouseLeave = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
      setTimeoutId(null);
    }
    setIsVisible(false);
  };

  const positionClasses = {
    top: 'bottom-full left-1/2 transform -translate-x-1/2 mb-3',
    bottom: 'top-full left-1/2 transform -translate-x-1/2 mt-3',
    left: 'right-full top-1/2 transform -translate-y-1/2 mr-3',
    right: 'left-full top-1/2 transform -translate-y-1/2 ml-3'
  };

  const getVariantStyles = () => {
    switch (variant) {
      case 'info':
        return {
          bg: 'bg-gradient-to-br from-blue-600 to-blue-700',
          border: 'border-blue-400/30',
          shadow: 'shadow-blue-500/25',
          arrow: 'border-blue-600'
        };
      case 'success':
        return {
          bg: 'bg-gradient-to-br from-emerald-600 to-emerald-700',
          border: 'border-emerald-400/30',
          shadow: 'shadow-emerald-500/25',
          arrow: 'border-emerald-600'
        };
      case 'premium':
        return {
          bg: 'bg-gradient-to-br from-purple-600 via-purple-700 to-indigo-700',
          border: 'border-purple-400/30',
          shadow: 'shadow-purple-500/25',
          arrow: 'border-purple-600'
        };
      default:
        return {
          bg: 'bg-gradient-to-br from-slate-800 via-slate-900 to-slate-800',
          border: 'border-slate-600/30',
          shadow: 'shadow-slate-900/50',
          arrow: 'border-slate-800'
        };
    }
  };

  const variantStyles = getVariantStyles();

  const arrowClasses = {
    top: `top-full left-1/2 transform -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent border-t-8 ${variantStyles.arrow.replace('border-', 'border-t-')}`,
    bottom: `bottom-full left-1/2 transform -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent border-b-8 ${variantStyles.arrow.replace('border-', 'border-b-')}`,
    left: `left-full top-1/2 transform -translate-y-1/2 border-t-transparent border-b-transparent border-r-transparent border-l-8 ${variantStyles.arrow.replace('border-', 'border-l-')}`,
    right: `right-full top-1/2 transform -translate-y-1/2 border-t-transparent border-b-transparent border-l-transparent border-r-8 ${variantStyles.arrow.replace('border-', 'border-r-')}`
  };

  const getIcon = () => {
    if (!showIcon) return null;
    
    switch (variant) {
      case 'premium':
        return <Sparkles className="h-3.5 w-3.5 text-yellow-300 flex-shrink-0" />;
      default:
        return <Info className="h-3.5 w-3.5 text-blue-300 flex-shrink-0" />;
    }
  };

  return (
    <div 
      className={`relative inline-block ${className}`}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {children}
      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ 
              opacity: 0, 
              scale: 0.85,
              y: position === 'top' ? 10 : position === 'bottom' ? -10 : 0,
              x: position === 'left' ? 10 : position === 'right' ? -10 : 0
            }}
            animate={{ 
              opacity: 1, 
              scale: 1,
              y: 0,
              x: 0
            }}
            exit={{ 
              opacity: 0, 
              scale: 0.85,
              y: position === 'top' ? 5 : position === 'bottom' ? -5 : 0,
              x: position === 'left' ? 5 : position === 'right' ? -5 : 0
            }}
            transition={{ 
              type: "spring",
              stiffness: 400,
              damping: 25,
              mass: 0.5
            }}
            className={`
              absolute z-[100] 
              px-4 py-3 
              text-sm font-medium text-white 
              ${variantStyles.bg}
              border ${variantStyles.border}
              rounded-xl 
              shadow-xl ${variantStyles.shadow}
              backdrop-blur-sm
              max-w-xs sm:max-w-sm
              ${positionClasses[position]}
            `}
            style={{
              filter: 'drop-shadow(0 4px 12px rgba(0, 0, 0, 0.15))'
            }}
          >
            {/* Subtle gradient overlay for depth */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/10 to-transparent rounded-xl pointer-events-none" />
            
            {/* Content */}
            <div className="relative flex items-start gap-2">
              {getIcon()}
              <div className="flex-1">
                <p className="leading-relaxed text-white/95">
                  {content}
                </p>
              </div>
            </div>

            {/* Enhanced arrow with gradient */}
            <div className="absolute">
              <div className={`w-0 h-0 ${arrowClasses[position]}`} />
              {/* Arrow shadow for depth */}
              <div 
                className={`absolute w-0 h-0 ${arrowClasses[position]} opacity-20`}
                style={{
                  transform: position === 'top' ? 'translate(-50%, 1px)' :
                           position === 'bottom' ? 'translate(-50%, -1px)' :
                           position === 'left' ? 'translate(1px, -50%)' :
                           'translate(-1px, -50%)'
                }}
              />
            </div>

            {/* Subtle shine effect */}
            <motion.div
              initial={{ x: '-100%' }}
              animate={{ x: '100%' }}
              transition={{ 
                duration: 2,
                repeat: Infinity,
                repeatDelay: 3,
                ease: "easeInOut"
              }}
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent rounded-xl pointer-events-none"
              style={{ transform: 'skewX(-20deg)' }}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
