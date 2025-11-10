'use client';

import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, MessageCircle, Mic, Lock } from 'lucide-react';
import { useSubscriptionStatus } from '@/hooks/useSubscriptionStatus';

interface SessionModeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectMode: (mode: 'practice' | 'assessment') => void;
}

export const SessionModeModal: React.FC<SessionModeModalProps> = ({
  isOpen,
  onClose,
  onSelectMode
}) => {
  const { subscriptionStatus, loading, refreshSubscriptionStatus } = useSubscriptionStatus();

  // Refresh subscription status when modal opens (only once when isOpen changes to true)
  useEffect(() => {
    if (isOpen) {
      refreshSubscriptionStatus();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]); // Only depend on isOpen, not refreshSubscriptionStatus to prevent infinite loop

  // Check if assessments are available
  const assessmentsRemaining = subscriptionStatus?.limits?.assessments_remaining ?? 0;
  const assessmentsLimit = subscriptionStatus?.limits?.assessments_limit ?? 0;
  const isAssessmentDisabled = assessmentsRemaining === 0;

  console.log('[SessionModeModal] Assessment status:', {
    assessmentsRemaining,
    assessmentsLimit,
    isAssessmentDisabled,
    subscriptionStatus
  });

  const handleAssessmentClick = () => {
    if (isAssessmentDisabled) {
      // Show upgrade prompt instead of starting assessment
      console.log('[SessionModeModal] Assessment blocked - showing upgrade prompt');
      // You can implement an upgrade modal here or redirect to upgrade page
      alert('You have used all your assessments for this subscription period. Please upgrade your plan to get more assessments.');
      return;
    }
    
    console.log('[SessionModeModal] Assessment allowed - proceeding');
    onSelectMode('assessment');
  };
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full mx-4 overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="relative bg-gradient-to-r from-teal-500 to-blue-500 p-6 text-white">
              <button
                onClick={onClose}
                className="absolute top-4 right-4 p-2 hover:bg-white/20 rounded-full transition-colors duration-200"
              >
                <X className="h-5 w-5" />
              </button>
              
              <div className="text-center">
                <h2 className="text-2xl font-bold mb-2">Choose Your Learning Mode</h2>
                <p className="text-white/90">How would you like to start your language session?</p>
              </div>
            </div>

            {/* Content */}
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Practice Mode */}
                <motion.button
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => onSelectMode('practice')}
                  className="group relative overflow-hidden rounded-xl p-6 text-left border-2 border-gray-200 hover:border-teal-400 transition-all duration-300 bg-gradient-to-br from-gray-50 to-white hover:shadow-lg"
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-teal-500/5 via-transparent to-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  
                  <div className="relative z-10">
                    <div className="w-12 h-12 bg-gradient-to-br from-teal-500 to-blue-500 rounded-full flex items-center justify-center mb-4 shadow-lg">
                      <MessageCircle className="h-6 w-6 text-white" />
                    </div>
                    
                    <h3 className="text-xl font-bold text-gray-800 mb-3 group-hover:text-teal-600 transition-colors duration-300">
                      Practice Conversation
                    </h3>
                    
                    <p className="text-gray-600 text-sm mb-4 group-hover:text-gray-700 transition-colors duration-300">
                      Start a conversation practice session on topics of your choice. Perfect for improving your speaking skills.
                    </p>
                    
                    <div className="flex flex-wrap gap-2">
                      <span className="text-xs px-3 py-1 bg-teal-100 text-teal-700 rounded-full">
                        Topic Selection
                      </span>
                      <span className="text-xs px-3 py-1 bg-blue-100 text-blue-700 rounded-full">
                        Interactive Chat
                      </span>
                    </div>
                  </div>
                  
                  <div className="absolute bottom-0 left-0 h-1 bg-gradient-to-r from-teal-500 to-blue-500 w-0 group-hover:w-full transition-all duration-500"></div>
                </motion.button>

                {/* Speaking Assessment Mode */}
                <motion.button
                  whileHover={!isAssessmentDisabled ? { scale: 1.02, y: -2 } : {}}
                  whileTap={!isAssessmentDisabled ? { scale: 0.98 } : {}}
                  onClick={handleAssessmentClick}
                  disabled={isAssessmentDisabled}
                  className={`group relative overflow-hidden rounded-xl p-6 text-left border-2 transition-all duration-300 ${
                    isAssessmentDisabled
                      ? 'border-gray-300 bg-gray-100 cursor-not-allowed opacity-60'
                      : 'border-gray-200 hover:border-purple-400 bg-gradient-to-br from-gray-50 to-white hover:shadow-lg cursor-pointer'
                  }`}
                >
                  {/* Disabled overlay */}
                  {isAssessmentDisabled && (
                    <div className="absolute inset-0 bg-gray-200/50 flex items-center justify-center z-20">
                      <div className="bg-white/90 backdrop-blur-sm rounded-lg px-4 py-2 flex items-center gap-2 shadow-lg">
                        <Lock className="h-4 w-4 text-gray-600" />
                        <span className="text-sm font-medium text-gray-700">
                          {loading ? 'Checking...' : `${assessmentsRemaining}/${assessmentsLimit} Used`}
                        </span>
                      </div>
                    </div>
                  )}
                  
                  <div className={`absolute inset-0 bg-gradient-to-br from-purple-500/5 via-transparent to-pink-500/5 opacity-0 transition-opacity duration-300 ${
                    !isAssessmentDisabled ? 'group-hover:opacity-100' : ''
                  }`}></div>
                  
                  <div className="relative z-10">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-4 shadow-lg ${
                      isAssessmentDisabled
                        ? 'bg-gray-400'
                        : 'bg-gradient-to-br from-purple-500 to-pink-500'
                    }`}>
                      {isAssessmentDisabled ? (
                        <Lock className="h-6 w-6 text-white" />
                      ) : (
                        <Mic className="h-6 w-6 text-white" />
                      )}
                    </div>
                    
                    <h3 className={`text-xl font-bold mb-3 transition-colors duration-300 ${
                      isAssessmentDisabled
                        ? 'text-gray-500'
                        : 'text-gray-800 group-hover:text-purple-600'
                    }`}>
                      Speaking Assessment
                    </h3>
                    
                    <p className={`text-sm mb-4 transition-colors duration-300 ${
                      isAssessmentDisabled
                        ? 'text-gray-400'
                        : 'text-gray-600 group-hover:text-gray-700'
                    }`}>
                      {isAssessmentDisabled
                        ? 'You have used all your assessments for this subscription period. Upgrade to get more assessments.'
                        : 'Take a quick speaking assessment to evaluate your current language proficiency level and get personalized feedback.'
                      }
                    </p>
                    
                    <div className="flex flex-wrap gap-2">
                      {isAssessmentDisabled ? (
                        <span className="text-xs px-3 py-1 bg-red-100 text-red-700 rounded-full">
                          Upgrade Required
                        </span>
                      ) : (
                        <>
                          <span className="text-xs px-3 py-1 bg-purple-100 text-purple-700 rounded-full">
                            Level Assessment
                          </span>
                          <span className="text-xs px-3 py-1 bg-pink-100 text-pink-700 rounded-full">
                            Instant Feedback
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                  
                  <div className={`absolute bottom-0 left-0 h-1 w-0 transition-all duration-500 ${
                    !isAssessmentDisabled
                      ? 'bg-gradient-to-r from-purple-500 to-pink-500 group-hover:w-full'
                      : 'bg-gray-400'
                  }`}></div>
                </motion.button>
              </div>

              {/* Additional Info */}
              <div className="mt-6 p-4 bg-gray-50 rounded-xl">
                <p className="text-sm text-gray-600 text-center">
                  💡 <strong>Tip:</strong> If you're unsure about your level, start with the Speaking Assessment to get personalized recommendations.
                </p>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default SessionModeModal;
