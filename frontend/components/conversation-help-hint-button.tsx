'use client';

import React, { useState, useEffect } from 'react';
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
}

const ConversationHelpHintButton: React.FC<ConversationHelpHintButtonProps> = ({
  isHelpReady,
  isHelpEnabled,
  isLoading = false,
  helpLanguage,
  onToggleHelp,
  onChangeLanguage,
  onShowHelp,
  className = ''
}) => {
  const [showSettings, setShowSettings] = useState(false);
  const [animationState, setAnimationState] = useState<'idle' | 'ready' | 'pulse'>('idle');

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
    if (!isHelpEnabled) return 'bg-gray-400 hover:bg-gray-500';
    if (isLoading) return 'bg-gradient-to-r from-blue-500 to-indigo-600 animate-loading-glow';
    if (isHelpReady) return 'bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600';
    return 'bg-blue-500 hover:bg-blue-600';
  };

  return (
    <div className={`relative ${className}`}>
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
        {/* Settings Button */}
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="w-8 h-8 bg-gray-100 hover:bg-gray-200 rounded-full flex items-center justify-center transition-colors duration-200"
          title="AI Help Settings"
        >
          <Settings className="w-4 h-4 text-gray-600" />
        </button>

        {/* Main Hint Button */}
        <button
          onClick={isHelpEnabled && isHelpReady ? onShowHelp : undefined}
          disabled={!isHelpEnabled || !isHelpReady}
          className={`
            relative w-12 h-12 rounded-full flex items-center justify-center
            transition-all duration-300 shadow-lg
            ${getButtonColor()}
            ${getAnimationClasses()}
            ${!isHelpEnabled || !isHelpReady ? 'cursor-not-allowed opacity-60' : 'cursor-pointer hover:scale-105'}
          `}
          title={
            !isHelpEnabled 
              ? "AI Help is disabled" 
              : !isHelpReady 
                ? "Waiting for AI response..." 
                : "Click for conversation help"
          }
        >
          {/* Microphone ready effect overlay */}
          {animationState === 'ready' && (
            <div className="absolute inset-0 rounded-full bg-blue-300 opacity-30 animate-ping"></div>
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
              {isHelpReady && isHelpEnabled ? (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="w-6 h-6 text-white drop-shadow-sm"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  viewBox="0 0 24 24"
                >
                  <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                  <line x1="12" y1="19" x2="12" y2="23" />
                  <line x1="8" y1="23" x2="16" y2="23" />
                </svg>
              ) : (
                <Lightbulb className="w-6 h-6 text-white drop-shadow-sm" />
              )}

              {/* Ready indicator */}
              {isHelpReady && isHelpEnabled && (
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white flex items-center justify-center">
                  <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                </div>
              )}
            </>
          )}
        </button>
      </div>

      {/* Tooltip */}
      {isHelpReady && isHelpEnabled && (
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-1 bg-gray-900 text-white text-xs rounded-md whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
          Conversation help ready!
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
        </div>
      )}
    </div>
  );
};

export default ConversationHelpHintButton;
