'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/auth';
import SaveProgressButton from './save-progress-button';

interface LeaveConversationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLeave: () => void;
  messages: any[];
  language: string;
  level: string;
  topic?: string;
  conversationStartTime?: number;
  practiceTime?: string;
}

export default function LeaveConversationModal({
  isOpen,
  onClose,
  onLeave,
  messages,
  language,
  level,
  topic,
  conversationStartTime,
  practiceTime
}: LeaveConversationModalProps) {
  const { user } = useAuth();
  const [isSaving, setIsSaving] = useState(false);

  // Handle browser navigation protection
  useEffect(() => {
    if (!isOpen) return;

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = '';
      return '';
    };

    const handlePopState = (e: PopStateEvent) => {
      e.preventDefault();
      // Push the current state back to prevent navigation
      window.history.pushState(null, '', window.location.href);
    };

    // Add event listeners
    window.addEventListener('beforeunload', handleBeforeUnload);
    window.addEventListener('popstate', handlePopState);

    // Push a state to handle back button
    window.history.pushState(null, '', window.location.href);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('popstate', handlePopState);
    };
  }, [isOpen]);

  const handleSaveAndLeave = async () => {
    if (!user || !messages || messages.length === 0) {
      onLeave();
      return;
    }

    setIsSaving(true);
    
    try {
      // Calculate conversation duration
      const durationMinutes = conversationStartTime 
        ? (Date.now() - conversationStartTime) / (1000 * 60)
        : 0;

      // Prepare messages for saving
      const messagesToSave = messages.map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp || new Date().toISOString()
      }));

      console.log('[LEAVE_MODAL] Saving conversation before leaving:', {
        language,
        level,
        topic,
        messageCount: messagesToSave.length,
        duration: durationMinutes
      });

      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/progress/save-conversation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          language,
          level,
          topic,
          messages: messagesToSave,
          duration_minutes: durationMinutes
        })
      });

      if (response.ok) {
        console.log('[LEAVE_MODAL] ✅ Conversation saved successfully before leaving');
      } else {
        console.error('[LEAVE_MODAL] ❌ Failed to save conversation before leaving');
      }
    } catch (error) {
      console.error('[LEAVE_MODAL] ❌ Error saving conversation before leaving:', error);
    } finally {
      setIsSaving(false);
      onLeave();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl animate-fade-in">
        <div className="text-center">
          {/* Icon */}
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-yellow-100 mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>

          {/* Title */}
          <h3 className="text-xl font-bold text-gray-800 mb-2">
            Leave Conversation?
          </h3>

          {/* Content */}
          <div className="mb-6">
            <p className="text-gray-600 mb-4">
              You're about to leave your conversation. 
              {practiceTime && (
                <span className="block mt-2 font-medium text-gray-800">
                  Practice time: {practiceTime}
                </span>
              )}
            </p>

            {user && messages && messages.length > 0 ? (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <p className="text-blue-800 text-sm">
                  💡 <strong>Save your progress</strong> to track your learning journey and maintain your streak!
                </p>
              </div>
            ) : (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
                <p className="text-gray-600 text-sm">
                  ℹ️ Sign in to save your conversation progress and track your learning journey.
                </p>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col space-y-3">
            {/* Save & Leave Button (for authenticated users with messages) */}
            {user && messages && messages.length > 0 && (
              <Button
                onClick={handleSaveAndLeave}
                disabled={isSaving}
                className="w-full bg-teal-500 hover:bg-teal-600 text-white py-3 px-4 rounded-xl font-medium transition-all flex items-center justify-center"
                style={{ backgroundColor: '#4ECFBF' }}
              >
                {isSaving ? (
                  <>
                    <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                    Saving & Leaving...
                  </>
                ) : (
                  <>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    Save & Leave
                  </>
                )}
              </Button>
            )}

            {/* Leave Without Saving Button */}
            <Button
              onClick={onLeave}
              disabled={isSaving}
              className="w-full bg-red-500 hover:bg-red-600 text-white py-3 px-4 rounded-xl font-medium transition-all"
            >
              {user && messages && messages.length > 0 ? 'Leave Without Saving' : 'Leave Conversation'}
            </Button>

            {/* Stay & Continue Button */}
            <Button
              onClick={onClose}
              disabled={isSaving}
              className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 py-3 px-4 rounded-xl font-medium transition-all"
            >
              Stay & Continue
            </Button>
          </div>

          {/* Additional Info for Guest Users */}
          {!user && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <p className="text-xs text-gray-500">
                <a href="/auth/login" className="text-blue-600 hover:text-blue-800 font-medium">
                  Sign in
                </a> to save your conversations and track your progress
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
