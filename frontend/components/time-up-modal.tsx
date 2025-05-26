'use client';

import React from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { isAuthenticated } from '@/lib/auth-utils';

interface TimeUpModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSignIn: () => void;
  onSignUp: () => void;
  onNewAssessment: () => void;
}

export default function TimeUpModal({
  isOpen,
  onClose,
  onSignIn,
  onSignUp,
  onNewAssessment
}: TimeUpModalProps) {
  const router = useRouter();
  const userIsAuthenticated = isAuthenticated();
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div 
        className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 overflow-hidden animate-in fade-in zoom-in duration-300"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-[#4ECFBF]/10 border-b border-[#4ECFBF]/20">
          <h2 className="text-xl font-semibold text-gray-900">Time's Up!</h2>
          <button 
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        
        {/* Content */}
        <div className="px-6 py-5">
          <div className="flex flex-col items-center mb-6">
            <div className="w-16 h-16 bg-[#FFF2C7] rounded-full flex items-center justify-center mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-[#FFD63A]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            
            <h3 className="text-lg font-medium text-gray-900 mb-2">Your conversation time has ended</h3>
            
            {userIsAuthenticated ? (
              <p className="text-gray-600 text-center">
                As a registered user, your conversation is limited to 5 minutes. 
                You can start a new assessment to continue practicing.
              </p>
            ) : (
              <p className="text-gray-600 text-center">
                As a guest, your conversation is limited to 1 minute.
                Sign up for a free account to get 5-minute conversations!
              </p>
            )}
          </div>
          
          {/* Action Buttons */}
          <div className="space-y-3">
            {!userIsAuthenticated && (
              <>
                <Button 
                  className="w-full bg-[#4ECFBF] hover:bg-[#5CCFC0] text-white font-medium py-3 rounded-lg shadow-sm transition-all hover:shadow-md"
                  onClick={onSignUp}
                >
                  Sign Up for Free
                </Button>
                
                <Button 
                  className="w-full bg-[#FFD63A] hover:bg-[#ECC235] text-gray-800 font-medium py-3 rounded-lg shadow-sm transition-all hover:shadow-md"
                  onClick={onSignIn}
                >
                  Sign In
                </Button>
              </>
            )}
            
            <Button 
              className={`w-full ${userIsAuthenticated ? 'bg-[#4ECFBF] hover:bg-[#5CCFC0] text-white' : 'bg-white hover:bg-gray-100 text-gray-700 border border-gray-300'} font-medium py-3 rounded-lg shadow-sm transition-all hover:shadow-md`}
              onClick={onNewAssessment}
            >
              Start New Assessment
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
