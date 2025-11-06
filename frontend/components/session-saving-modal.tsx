'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';

interface SessionSavingModalProps {
  isOpen: boolean;
  stage: 'saving' | 'analyzing' | 'finalizing' | 'success';
  conversationHighlights: string[];
  sentenceCount: number;
  duration: string;
  messageCount: number;
  onComplete: () => void;
}

export default function SessionSavingModal({
  isOpen,
  stage,
  conversationHighlights,
  sentenceCount,
  duration,
  messageCount,
  onComplete
}: SessionSavingModalProps) {
  const [currentHighlight, setCurrentHighlight] = useState(0);

  // Rotate conversation highlights
  useEffect(() => {
    if (conversationHighlights.length > 0 && stage !== 'success') {
      const interval = setInterval(() => {
        setCurrentHighlight(prev => 
          (prev + 1) % conversationHighlights.length
        );
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [conversationHighlights.length, stage]);

  const getStageConfig = () => {
    switch (stage) {
      case 'saving':
        return {
          icon: '💾',
          title: 'Saving Your Conversation...',
          subtitle: 'Preserving your progress',
          progress: 33,
          color: 'from-[#FFA955] to-[#F75A5A]', // Orange to Coral
          bgColor: 'from-orange-50 to-red-50',
          borderColor: 'border-orange-200'
        };
      case 'analyzing':
        return {
          icon: '🔍',
          title: 'Analyzing Your Speech...',
          subtitle: `Processing ${sentenceCount} sentences`,
          progress: 66,
          color: 'from-[#4ECFBF] to-[#FFD63A]', // Turquoise to Yellow
          bgColor: 'from-teal-50 to-yellow-50',
          borderColor: 'border-teal-200'
        };
      case 'finalizing':
        return {
          icon: '✨',
          title: 'Finalizing Your Session...',
          subtitle: 'Almost done',
          progress: 90,
          color: 'from-[#FFD63A] to-[#4ECFBF]', // Yellow to Turquoise
          bgColor: 'from-yellow-50 to-teal-50',
          borderColor: 'border-yellow-200'
        };
      case 'success':
        return {
          icon: '🎉',
          title: 'Session Saved Successfully!',
          subtitle: 'Your progress has been saved and analyzed',
          progress: 100,
          color: 'from-[#4ECFBF] to-[#4ECFBF]', // Turquoise (brand success color)
          bgColor: 'from-teal-50 to-teal-100',
          borderColor: 'border-teal-300'
        };
    }
  };

  const config = getStageConfig();

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden"
        >
          {/* Header with gradient */}
          <div className={`bg-gradient-to-r ${config.color} p-6 text-white`}>
            <motion.div
              key={stage}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="text-6xl text-center mb-4"
            >
              {config.icon}
            </motion.div>
            <h3 className="text-2xl font-bold text-center mb-2">
              {config.title}
            </h3>
            <p className="text-center text-white/90">
              {config.subtitle}
            </p>
          </div>

          {/* Progress Bar */}
          <div className="px-6 pt-6">
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
              <motion.div
                className={`h-full bg-gradient-to-r ${config.color}`}
                initial={{ width: 0 }}
                animate={{ width: `${config.progress}%` }}
                transition={{ duration: 0.5, ease: "easeOut" }}
              />
            </div>
          </div>

          {/* Content Area */}
          <div className="p-6">
            {stage !== 'success' ? (
              <>
                {/* Conversation Highlights */}
                {conversationHighlights.length > 0 && (
                  <div className="mb-6">
                    <AnimatePresence mode="wait">
                      <motion.div
                        key={currentHighlight}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className={`bg-gradient-to-br ${config.bgColor} rounded-lg p-4 border ${config.borderColor}`}
                      >
                        <p className="text-gray-700 dark:text-gray-300 italic">
                          "{conversationHighlights[currentHighlight]}"
                        </p>
                      </motion.div>
                    </AnimatePresence>
                  </div>
                )}

                {/* Analysis Steps */}
                {stage === 'analyzing' && (
                  <div className="space-y-3">
                    <AnalysisStep completed text="Grammar check" color="#4ECFBF" />
                    <AnalysisStep completed text="Vocabulary assessment" color="#4ECFBF" />
                    <AnalysisStep active text="Generating feedback..." color="#FFD63A" />
                  </div>
                )}
              </>
            ) : (
              <>
                {/* Success Stats */}
                <div className="grid grid-cols-3 gap-4 mb-6">
                  <StatCard icon="📊" label="Duration" value={duration} />
                  <StatCard icon="💬" label="Messages" value={messageCount.toString()} />
                  <StatCard icon="🎯" label="Analyzed" value={sentenceCount.toString()} />
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3">
                  <button
                    onClick={onComplete}
                    className="flex-1 bg-gradient-to-r from-[#4ECFBF] to-[#4ECFBF] text-white py-3 rounded-lg font-semibold hover:from-[#3DBFAF] hover:to-[#3DBFAF] transition-all shadow-lg hover:shadow-xl"
                  >
                    Continue
                  </button>
                </div>
              </>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

// Helper Components
function AnalysisStep({ completed, active, text, color }: { completed?: boolean; active?: boolean; text: string; color?: string }) {
  return (
    <div className="flex items-center gap-3">
      <div 
        className={`w-6 h-6 rounded-full flex items-center justify-center ${
          completed ? '' : active ? '' : 'bg-gray-300 dark:bg-gray-600'
        }`}
        style={completed || active ? { backgroundColor: color || '#4ECFBF' } : {}}
      >
        {completed ? (
          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        ) : active ? (
          <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
        ) : null}
      </div>
      <span className={`text-sm ${completed || active ? 'text-gray-900 dark:text-gray-100' : 'text-gray-500 dark:text-gray-400'}`}>
        {text}
      </span>
    </div>
  );
}

function StatCard({ icon, label, value }: { icon: string; label: string; value: string }) {
  return (
    <div className="text-center">
      <div className="text-2xl mb-1">{icon}</div>
      <div className="text-sm text-gray-500 dark:text-gray-400">{label}</div>
      <div className="text-lg font-bold text-gray-900 dark:text-gray-100">{value}</div>
    </div>
  );
}
