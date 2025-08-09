'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Lightbulb, Zap, Languages, Settings } from 'lucide-react';

interface ConversationHelpHintButtonProps {
  isHelpReady: boolean;
  isHelpEnabled: boolean;
  isLoading?: boolean;
  helpLanguage: string;
  onToggleHelp: (enabled: boolean) => void;
  onChangeLanguage: (language: string) => void;
  onShowHelp: () => void;
  className?: string;
  sessionEnded?: boolean;
}

const ConversationHelpHintButton: React.FC<ConversationHelpHintButtonProps> = ({
  isHelpReady,
  isHelpEnabled,
  isLoading = false,
  helpLanguage,
  onToggleHelp,
  onChangeLanguage,
  onShowHelp,
  className = '',
  sessionEnded = false
}) => {
  const [showSettings, setShowSettings] = useState(false);
  const [animationState, setAnimationState] = useState<'idle' | 'ready' | 'pulse'>('idle');
  
  // Dragging state for mobile
  const [isDragging, setIsDragging] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const buttonRef = useRef<HTMLDivElement>(null);
  const dragTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Handle help ready animation
  useEffect(() => {
    if (isHelpReady && isHelpEnabled) {
      setAnimationState('ready');
      
      // Start pulsing animation
      const pulseTimer = setTimeout(() => {
        setAnimationState('pulse');
      }, 500);

      return () => clearTimeout(pulseTimer);
    } else {
      setAnimationState('idle');
    }
  }, [isHelpReady, isHelpEnabled]);

  // Available help languages
  const helpLanguages = [
    { code: "english", name: "English", native: "English" },
    { code: "spanish", name: "Spanish", native: "Español" },
    { code: "french", name: "French", native: "Français" },
    { code: "german", name: "German", native: "Deutsch" },
    { code: "italian", name: "Italian", native: "Italiano" },
    { code: "portuguese", name: "Portuguese", native: "Português" },
    { code: "dutch", name: "Dutch", native: "Nederlands" },
    { code: "russian", name: "Russian", native: "Русский" },
    { code: "chinese", name: "Chinese", native: "中文" },
    { code: "japanese", name: "Japanese", native: "日本語" },
    { code: "korean", name: "Korean", native: "한국어" },
    { code: "arabic", name: "Arabic", native: "العربية" },
    { code: "hindi", name: "Hindi", native: "हिन्दी" },
    { code: "turkish", name: "Turkish", native: "Türkçe" }
  ];

  const getAnimationClasses = () => {
    switch (animationState) {
      case 'ready':
        return 'animate-flash-lightning';
      case 'pulse':
        return 'animate-pulse-glow';
      default:
        return '';
    }
  };

  const getButtonColor = () => {
    if (sessionEnded) return 'bg-gray-400';
    if (!isHelpEnabled) return 'bg-gray-400 hover:bg-gray-500';
    if (isLoading) return 'bg-gradient-to-r from-blue-500 to-indigo-600 animate-loading-glow';
    if (isHelpReady) return 'bg-gradient-to-r from-yellow-400 to-orange-500 hover:from-yellow-500 hover:to-orange-600';
    return 'bg-blue-500 hover:bg-blue-600';
  };

  // Touch event handlers for mobile dragging
  const handleTouchStart = (e: React.TouchEvent) => {
    const touch = e.touches[0];
    setDragStart({ x: touch.clientX - position.x, y: touch.clientY - position.y });
    setIsDragging(false); // Reset dragging state
    
    // Set a timeout to detect if this is a drag vs tap
    dragTimeoutRef.current = setTimeout(() => {
      setIsDragging(true);
    }, 150); // 150ms threshold for drag detection
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (dragTimeoutRef.current) {
      clearTimeout(dragTimeoutRef.current);
      dragTimeoutRef.current = null;
    }
    
    const touch = e.touches[0];
    const newX = touch.clientX - dragStart.x;
    const newY = touch.clientY - dragStart.y;
    
    // Get viewport dimensions
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const buttonSize = 65; // Approximate button width including settings (48px hint + 8px gap + 36px settings = ~65px)
    
    // Constrain to viewport bounds
    const constrainedX = Math.max(0, Math.min(viewportWidth - buttonSize, newX));
    const constrainedY = Math.max(0, Math.min(viewportHeight - buttonSize, newY));
    
    setPosition({ x: constrainedX, y: constrainedY });
    setIsDragging(true);
    
    // Prevent scrolling while dragging
    e.preventDefault();
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (dragTimeoutRef.current) {
      clearTimeout(dragTimeoutRef.current);
      dragTimeoutRef.current = null;
    }
    
    // If this was a tap (not a drag), trigger the button action
    if (!isDragging && isHelpEnabled && isHelpReady && !sessionEnded) {
      onShowHelp();
    }
    
    // Reset dragging state after a short delay
    setTimeout(() => {
      setIsDragging(false);
    }, 100);
  };

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (dragTimeoutRef.current) {
        clearTimeout(dragTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div 
      ref={buttonRef}
      className={`relative ${className} ${isDragging ? 'z-50' : ''}`}
      style={{
        transform: `translate(${position.x}px, ${position.y}px)`,
        transition: isDragging ? 'none' : 'transform 0.2s ease-out',
        touchAction: 'none' // Prevent default touch behaviors
      }}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* Settings Panel */}
      {showSettings && (
        <div className="absolute bottom-full right-0 mb-2 bg-white rounded-lg shadow-xl border border-gray-200 p-4 min-w-[280px] z-50">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-900 flex items-center gap-2">
              <Settings className="w-4 h-4" />
              AI Help Settings
            </h3>
            <button
              onClick={() => setShowSettings(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          </div>
          
          {/* Help Toggle */}
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm font-medium text-gray-700">Enable AI Help</span>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={isHelpEnabled}
                onChange={(e) => onToggleHelp(e.target.checked)}
                className="sr-only peer"
              />
              <div className={`relative w-11 h-6 rounded-full peer transition-colors duration-200 ease-in-out ${
                isHelpEnabled 
                  ? 'bg-blue-600' 
                  : 'bg-gray-300'
              }`}>
                <div className={`absolute top-0.5 left-0.5 bg-white rounded-full h-5 w-5 transition-transform duration-200 ease-in-out shadow-md ${
                  isHelpEnabled ? 'translate-x-5' : 'translate-x-0'
                }`}></div>
              </div>
            </label>
          </div>

          {/* Language Selection */}
          {isHelpEnabled && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Help Language
              </label>
              <select
                value={helpLanguage}
                onChange={(e) => onChangeLanguage(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm text-black"
              >
                {helpLanguages.map((lang) => (
                  <option key={lang.code} value={lang.code} className="bg-white text-black">
                    {lang.native} ({lang.name})
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      )}

      {/* Main Button */}
      <div className="flex items-center gap-2">
        {/* Main Hint Button */}
        <button
          onClick={isHelpEnabled && isHelpReady && !sessionEnded ? onShowHelp : undefined}
          disabled={!isHelpEnabled || !isHelpReady || sessionEnded}
          className={`
            relative w-12 h-12 rounded-full flex items-center justify-center
            transition-all duration-300 shadow-lg
            ${getButtonColor()}
            ${getAnimationClasses()}
            ${!isHelpEnabled || !isHelpReady || sessionEnded ? 'cursor-not-allowed opacity-60' : 'cursor-pointer hover:scale-105'}
          `}
          title={
            sessionEnded
              ? "Session ended - help not available"
              : !isHelpEnabled 
                ? "AI Help is disabled" 
                : !isHelpReady 
                  ? "Waiting for AI response..." 
                  : "Click for conversation help"
          }
        >
          {/* Lightning ready effect overlay */}
          {animationState === 'ready' && (
            <div className="absolute inset-0 rounded-full bg-yellow-300 opacity-30 animate-ping"></div>
          )}
          
          {/* Enhanced Loading Animation */}
          {isLoading && isHelpEnabled ? (
            <div className="relative">
              {/* Outer rotating ring */}
              <div className="w-7 h-7 border-2 border-white/20 border-t-white border-r-white rounded-full animate-spin"></div>
              {/* Inner rotating ring - opposite direction */}
              <div className="absolute inset-0.5 w-6 h-6 border-2 border-white/30 border-b-white border-l-white rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}></div>
              {/* Center pulsing core */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-3 h-3 bg-white rounded-full animate-loading-pulse-center"></div>
              </div>
              {/* Subtle shimmer overlay */}
              <div className="absolute inset-0 rounded-full bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"></div>
            </div>
          ) : (
            /* Icon */
            <>
              <Lightbulb className="w-6 h-6 text-white drop-shadow-sm" />

              {/* Ready indicator */}
              {isHelpReady && isHelpEnabled && !sessionEnded && (
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white flex items-center justify-center">
                  <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                </div>
              )}
            </>
          )}
        </button>

        {/* Settings Button */}
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="w-9 h-9 bg-gray-100 hover:bg-gray-200 rounded-full flex items-center justify-center transition-colors duration-200"
          title="AI Help Settings"
        >
          <Settings className="w-4 h-4 text-gray-600" />
        </button>
      </div>

      {/* Tooltip */}
      {isHelpReady && isHelpEnabled && !sessionEnded && (
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-1 bg-gray-900 text-white text-xs rounded-md whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
          Conversation help ready!
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
        </div>
      )}
    </div>
  );
};

export default ConversationHelpHintButton;
