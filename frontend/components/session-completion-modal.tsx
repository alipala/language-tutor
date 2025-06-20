'use client';

import React, { useEffect, useState } from 'react';
import { CheckCircle, Home, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';

interface SessionCompletionModalProps {
  isOpen: boolean;
  onGoHome: () => void;
  onStartNew: () => void;
  sessionDuration: string;
  messageCount: number;
  language: string;
  level: string;
}

export default function SessionCompletionModal({
  isOpen,
  onGoHome,
  onStartNew,
  sessionDuration,
  messageCount,
  language,
  level
}: SessionCompletionModalProps) {
  const router = useRouter();
  const [countdown, setCountdown] = useState(10);
  const [autoRedirect, setAutoRedirect] = useState(true);

  // Auto-redirect countdown
  useEffect(() => {
    if (!isOpen || !autoRedirect) return;

    const interval = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          onGoHome();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isOpen, autoRedirect, onGoHome]);

  // Reset countdown when modal opens
  useEffect(() => {
    if (isOpen) {
      setCountdown(10);
      setAutoRedirect(true);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop overlay */}
      <div className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm" />
      
      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div 
          className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden animate-in fade-in zoom-in duration-500"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Success Header */}
          <div className="bg-gradient-to-r from-green-500 to-emerald-500 px-6 py-8 text-center">
            <div className="w-20 h-20 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="h-12 w-12 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Session Complete!</h2>
            <p className="text-green-100">Your conversation has been saved successfully</p>
          </div>
          
          {/* Content */}
          <div className="px-6 py-6">
            {/* Session Stats */}
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <h3 className="font-semibold text-gray-900 mb-3 text-center">Session Summary</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{sessionDuration}</div>
                  <div className="text-gray-600">Duration</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{messageCount}</div>
                  <div className="text-gray-600">Messages</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold text-purple-600 capitalize">{language}</div>
                  <div className="text-gray-600">Language</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold text-orange-600">{level.toUpperCase()}</div>
                  <div className="text-gray-600">Level</div>
                </div>
              </div>
            </div>

            {/* Progress Message */}
            <div className="text-center mb-6">
              <p className="text-gray-700 mb-2">
                🎉 Great job! Your progress has been saved to your learning plan.
              </p>
              <p className="text-sm text-gray-600">
                Check your dashboard to see your updated progress and start your next session.
              </p>
            </div>

            {/* Auto-redirect notice */}
            {autoRedirect && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 text-center">
                <p className="text-sm text-blue-800">
                  Redirecting to dashboard in <span className="font-bold text-blue-600">{countdown}</span> seconds
                </p>
                <button
                  onClick={() => setAutoRedirect(false)}
                  className="text-xs text-blue-600 hover:text-blue-800 underline mt-1"
                >
                  Cancel auto-redirect
                </button>
              </div>
            )}
            
            {/* Action Buttons */}
            <div className="space-y-3">
              <Button 
                className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 rounded-lg shadow-sm transition-all hover:shadow-md flex items-center justify-center gap-2"
                onClick={onGoHome}
              >
                <Home className="h-4 w-4" />
                View Progress & Dashboard
              </Button>
              
              <Button 
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-lg shadow-sm transition-all hover:shadow-md flex items-center justify-center gap-2"
                onClick={onStartNew}
              >
                <RotateCcw className="h-4 w-4" />
                Start New Session
              </Button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
