'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/auth';
import { getApiUrl } from '@/lib/api-utils';

interface SaveProgressButtonProps {
  messages: any[];
  language: string;
  level: string;
  topic?: string;
  conversationStartTime?: number;
  className?: string;
}

export default function SaveProgressButton({
  messages,
  language,
  level,
  topic,
  conversationStartTime,
  className = ""
}: SaveProgressButtonProps) {
  const { user } = useAuth();
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [cooldownTime, setCooldownTime] = useState(0);
  const [lastSaveTime, setLastSaveTime] = useState<number | null>(null);
  
  // Calculate current conversation duration
  const currentDuration = conversationStartTime 
    ? (Date.now() - conversationStartTime) / (1000 * 60) // in minutes
    : 0;
  
  // Minimum duration required to enable save button (4 minutes)
  const MIN_DURATION_FOR_SAVE = 4;
  const isMinimumDurationMet = currentDuration >= MIN_DURATION_FOR_SAVE;

  // Cooldown timer effect
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    
    if (cooldownTime > 0) {
      interval = setInterval(() => {
        setCooldownTime((prev) => {
          if (prev <= 1) {
            setSaveState('idle');
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [cooldownTime]);

  // Don't show button for non-authenticated users or if no messages
  if (!user || !messages || messages.length === 0) {
    return null;
  }

  const handleSaveProgress = async () => {
    // Check if this is a learning plan conversation
    const urlParams = new URLSearchParams(window.location.search);
    const planParam = urlParams.get('plan');
    
    // If this is a learning plan conversation, don't save to conversation history
    if (planParam) {
      console.log('[SAVE_PROGRESS] ⚠️ Skipping conversation save - this is a learning plan session:', planParam);
      console.log('[SAVE_PROGRESS] Learning plan conversations should not appear in conversation history');
      setSaveState('saved');
      setLastSaveTime(Date.now());
      setCooldownTime(60);
      
      // Show "saved" state briefly to provide user feedback
      setTimeout(() => {
        if (cooldownTime === 0) {
          setSaveState('idle');
        }
      }, 3000);
      return;
    }

    // Prevent spam clicking with 1-minute cooldown for meaningful summaries
    const now = Date.now();
    if (lastSaveTime && (now - lastSaveTime) < 60000) {
      const remainingCooldown = Math.ceil((60000 - (now - lastSaveTime)) / 1000);
      setCooldownTime(remainingCooldown);
      return;
    }

    setSaveState('saving');
    
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

      console.log('[SAVE_PROGRESS] Saving PRACTICE MODE conversation:', {
        language,
        level,
        topic,
        messageCount: messagesToSave.length,
        duration: durationMinutes,
        isPracticeMode: true
      });

      const token = localStorage.getItem('token');
      const response = await fetch(`${getApiUrl()}/api/progress/save-conversation`, {
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
          duration_minutes: durationMinutes,
          learning_plan_id: null, // Explicitly mark as practice mode
          conversation_type: 'practice'
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save conversation');
      }

      const result = await response.json();
      console.log('[SAVE_PROGRESS] ✅ Practice mode conversation saved successfully:', result);

      setSaveState('saved');
      setLastSaveTime(now);
      setCooldownTime(60); // 1-minute cooldown

      // Show success state for 3 seconds, then return to idle
      setTimeout(() => {
        if (cooldownTime === 0) {
          setSaveState('idle');
        }
      }, 3000);

    } catch (error) {
      console.error('[SAVE_PROGRESS] ❌ Error saving conversation:', error);
      setSaveState('error');
      
      // Show error state for 3 seconds, then return to idle
      setTimeout(() => {
        setSaveState('idle');
      }, 3000);
    }
  };

  const getButtonContent = () => {
    switch (saveState) {
      case 'saving':
        return (
          <>
            <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
            Saving...
          </>
        );
      case 'saved':
        return (
          <>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Saved ✓
          </>
        );
      case 'error':
        return (
          <>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Retry Save
          </>
        );
      default:
        if (cooldownTime > 0) {
          return (
            <>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Wait {cooldownTime}s
            </>
          );
        }
        return (
          <>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            💾 Save Progress
          </>
        );
    }
  };

  const getButtonColor = () => {
    switch (saveState) {
      case 'saving':
        return 'bg-blue-500 hover:bg-blue-600';
      case 'saved':
        return 'bg-green-500 hover:bg-green-600';
      case 'error':
        return 'bg-red-500 hover:bg-red-600';
      default:
        return cooldownTime > 0 
          ? 'bg-gray-400 cursor-not-allowed' 
          : 'bg-teal-500 hover:bg-teal-600';
    }
  };

  return (
    <div className="flex flex-col items-end">
      {/* Duration indicator when minimum not met */}
      {!isMinimumDurationMet && conversationStartTime && (
        <div className="text-xs text-gray-500 mb-1 text-right">
          {Math.floor(currentDuration)}:{((currentDuration % 1) * 60).toFixed(0).padStart(2, '0')} / 4:00 min
        </div>
      )}
      
      <Button
        onClick={handleSaveProgress}
        disabled={saveState === 'saving' || cooldownTime > 0 || !isMinimumDurationMet}
        className={`${getButtonColor()} text-white font-medium transition-all duration-300 flex items-center ${className}`}
        style={{ backgroundColor: saveState === 'idle' && cooldownTime === 0 && isMinimumDurationMet ? '#4ECFBF' : undefined }}
        title={!isMinimumDurationMet ? 'Minimum 4 minutes required to save progress' : undefined}
      >
        {getButtonContent()}
      </Button>
    </div>
  );
}
