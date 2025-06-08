'use client';

import React from 'react';
import { Brain } from 'lucide-react';

interface LoadingModalProps {
  isOpen: boolean;
  message?: string;
}

export default function LoadingModal({
  isOpen,
  message = "Your taalcoach knowledge is being extended. Hold on please!"
}: LoadingModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div 
        className="bg-gray-800/90 backdrop-blur-md rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden animate-in fade-in zoom-in duration-300 border border-white/10"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Content */}
        <div className="px-8 py-10">
          <div className="flex flex-col items-center text-center">
            {/* Animated Brain Icon */}
            <div className="relative mb-6">
              {/* Outer pulsing ring */}
              <div className="absolute inset-0 w-20 h-20 rounded-full bg-gradient-to-r from-[#4ECFBF]/20 to-[#FFD63A]/20 animate-ping-slow"></div>
              
              {/* Middle pulsing ring */}
              <div className="absolute inset-2 w-16 h-16 rounded-full bg-gradient-to-r from-[#4ECFBF]/30 to-[#FFD63A]/30 animate-ping-slower"></div>
              
              {/* Inner brain icon container */}
              <div className="relative w-20 h-20 rounded-full bg-gradient-to-r from-[#4ECFBF] to-[#FFD63A] flex items-center justify-center shadow-lg">
                <Brain className="h-10 w-10 text-white animate-pulse" />
              </div>
            </div>
            
            {/* Loading Message */}
            <h3 className="text-xl font-semibold text-white mb-4 leading-relaxed">
              {message}
            </h3>
            
            {/* Loading Progress Bar */}
            <div className="w-full bg-gray-700/50 rounded-full h-2 mb-4 overflow-hidden">
              <div className="h-full bg-gradient-to-r from-[#4ECFBF] via-[#FFD63A] to-[#FFA955] rounded-full animate-loading-progress"></div>
            </div>
            
            {/* Loading Dots */}
            <div className="flex space-x-2">
              <div className="w-2 h-2 bg-[#4ECFBF] rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-[#FFD63A] rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-[#FFA955] rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
