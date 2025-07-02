'use client';

import React from 'react';
import { AlertTriangle, ArrowLeft, LogOut } from 'lucide-react';

interface LeaveConfirmationModalProps {
  isOpen: boolean;
  onStay: () => void;
  onLeave: () => void;
  isGuestUser?: boolean;
  userType?: 'guest' | 'authenticated';
}

export default function LeaveConfirmationModal({
  isOpen,
  onStay,
  onLeave,
  isGuestUser = true,
  userType = 'guest'
}: LeaveConfirmationModalProps) {
  if (!isOpen) return null;

  const getModalContent = () => {
    if (userType === 'guest') {
      return {
        title: "Don't leave your practice session!",
        message: "You're making great progress! Leaving now will end your current conversation and you'll lose your session progress.",
        stayButtonText: "Continue Practice",
        leaveButtonText: "End Session",
        icon: <AlertTriangle className="h-8 w-8 text-[#FFD63A]" />,
        iconBgColor: "bg-[#FFD63A]/20"
      };
    } else {
      return {
        title: "End current conversation?",
        message: "You're currently in a conversation. Leaving this page will end your current session.",
        stayButtonText: "Continue Conversation",
        leaveButtonText: "End Conversation",
        icon: <LogOut className="h-8 w-8 text-[#FFA955]" />,
        iconBgColor: "bg-[#FFA955]/20"
      };
    }
  };

  const content = getModalContent();

  return (
    <div className="fixed inset-0 z-[60] bg-black/60 backdrop-blur-sm transition-all duration-300">
      <div 
        className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden border border-white/20 animate-in fade-in zoom-in duration-300"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header with Icon */}
        <div className="px-6 pt-6 pb-4">
          <div className="flex items-center justify-center mb-4">
            <div className={`w-16 h-16 rounded-full ${content.iconBgColor} flex items-center justify-center`}>
              {content.icon}
            </div>
          </div>
          
          <h3 className="text-2xl font-bold text-gray-800 text-center mb-3">
            {content.title}
          </h3>
          
          <p className="text-gray-600 text-center leading-relaxed">
            {content.message}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="px-6 pb-6">
          <div className="flex flex-col gap-3">
            {/* Primary Action - Stay */}
            <button
              onClick={onStay}
              className="group relative overflow-hidden bg-[#4ECFBF] hover:bg-[#4ECFBF]/90 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-300 transform hover:translate-y-[-2px] hover:shadow-lg hover:shadow-[#4ECFBF]/30 flex items-center justify-center gap-3"
            >
              <ArrowLeft className="h-5 w-5 transition-transform duration-300 group-hover:translate-x-[-2px]" />
              <span>{content.stayButtonText}</span>
              
              {/* Subtle shine effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 transform translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
            </button>
            
            {/* Secondary Action - Leave */}
            <button
              onClick={onLeave}
              className="group relative overflow-hidden bg-white/80 hover:bg-white border-2 border-gray-200 hover:border-gray-300 text-gray-700 hover:text-gray-800 font-medium py-3 px-6 rounded-xl transition-all duration-300 transform hover:translate-y-[-1px] hover:shadow-md flex items-center justify-center gap-3"
            >
              <LogOut className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-[2px]" />
              <span>{content.leaveButtonText}</span>
            </button>
          </div>
        </div>

        {/* Bottom accent line */}
        <div className="h-1 bg-gradient-to-r from-[#4ECFBF] via-[#FFD63A] to-[#FFA955]"></div>
      </div>
    </div>
  );
}
