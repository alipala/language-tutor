'use client';

import React, { useState, useEffect } from 'react';
import { CheckCircle, CreditCard, User, Zap, Crown, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface PaymentProcessingModalProps {
  isOpen: boolean;
  onComplete: () => void;
  planName?: string;
  userEmail?: string;
}

interface ProcessingStep {
  id: string;
  label: string;
  icon: React.ReactNode;
  duration: number; // in milliseconds
}

export const PaymentProcessingModal: React.FC<PaymentProcessingModalProps> = ({
  isOpen,
  onComplete,
  planName = "Premium Plan",
  userEmail
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [isComplete, setIsComplete] = useState(false);

  const steps: ProcessingStep[] = [
    {
      id: 'payment',
      label: 'Confirming payment...',
      icon: <CreditCard className="w-6 h-6" />,
      duration: 2000
    },
    {
      id: 'subscription',
      label: 'Activating subscription...',
      icon: <Zap className="w-6 h-6" />,
      duration: 1500
    },
    {
      id: 'profile',
      label: 'Updating your profile...',
      icon: <User className="w-6 h-6" />,
      duration: 1200
    },
    {
      id: 'complete',
      label: 'Welcome to premium!',
      icon: <Crown className="w-6 h-6" />,
      duration: 1000
    }
  ];

  useEffect(() => {
    if (!isOpen) {
      setCurrentStep(0);
      setCompletedSteps(new Set());
      setIsComplete(false);
      return;
    }

    let timeoutId: NodeJS.Timeout;
    
    const processStep = (stepIndex: number) => {
      if (stepIndex >= steps.length) {
        // All steps completed
        setIsComplete(true);
        setTimeout(() => {
          onComplete();
        }, 2000);
        return;
      }

      const step = steps[stepIndex];
      
      // Mark current step as active
      setCurrentStep(stepIndex);
      
      // Complete the step after its duration
      timeoutId = setTimeout(() => {
        setCompletedSteps(prev => new Set([...Array.from(prev), stepIndex]));
        
        // Move to next step after a brief pause
        setTimeout(() => {
          processStep(stepIndex + 1);
        }, 300);
      }, step.duration);
    };

    // Start processing
    processStep(0);

    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [isOpen, onComplete]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-3xl shadow-2xl max-w-md w-full p-8 relative overflow-hidden"
      >
        {/* Background gradient animation */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 opacity-50"></div>
        
        {/* Animated background circles */}
        <div className="absolute -top-10 -right-10 w-32 h-32 bg-blue-200 rounded-full opacity-20 animate-pulse"></div>
        <div className="absolute -bottom-10 -left-10 w-24 h-24 bg-purple-200 rounded-full opacity-20 animate-pulse delay-1000"></div>
        
        <div className="relative z-10">
          {/* Header */}
          <div className="text-center mb-8">
            <AnimatePresence mode="wait">
              {!isComplete ? (
                <motion.div
                  key="processing"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                >
                  <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
                    <div className="w-8 h-8 border-3 border-white border-t-transparent rounded-full animate-spin"></div>
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">Processing Your Subscription</h2>
                  <p className="text-gray-600">Setting up your {planName} access...</p>
                </motion.div>
              ) : (
                <motion.div
                  key="complete"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ type: "spring", duration: 0.6 }}
                >
                  <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
                    <CheckCircle className="w-8 h-8 text-white" />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome to Premium!</h2>
                  <p className="text-gray-600">Your {planName} is now active</p>
                  {userEmail && (
                    <p className="text-sm text-gray-500 mt-2">Confirmation sent to {userEmail}</p>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Progress Steps */}
          <div className="space-y-4">
            {steps.map((step, index) => {
              const isCompleted = completedSteps.has(index);
              const isCurrent = currentStep === index && !isComplete;
              const isPending = index > currentStep && !isComplete;

              return (
                <motion.div
                  key={step.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={`flex items-center space-x-4 p-4 rounded-xl transition-all duration-500 ${
                    isCompleted
                      ? 'bg-green-50 border border-green-200'
                      : isCurrent
                      ? 'bg-blue-50 border border-blue-200 shadow-sm'
                      : 'bg-gray-50 border border-gray-200'
                  }`}
                >
                  <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center transition-all duration-500 ${
                    isCompleted
                      ? 'bg-green-500 text-white'
                      : isCurrent
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-300 text-gray-500'
                  }`}>
                    {isCompleted ? (
                      <CheckCircle className="w-5 h-5" />
                    ) : isCurrent ? (
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      >
                        {step.icon}
                      </motion.div>
                    ) : (
                      step.icon
                    )}
                  </div>
                  
                  <div className="flex-1">
                    <p className={`font-medium transition-colors duration-500 ${
                      isCompleted
                        ? 'text-green-800'
                        : isCurrent
                        ? 'text-blue-800'
                        : 'text-gray-500'
                    }`}>
                      {step.label}
                    </p>
                  </div>
                  
                  {isCompleted && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: "spring", duration: 0.4 }}
                    >
                      <Sparkles className="w-5 h-5 text-green-500" />
                    </motion.div>
                  )}
                </motion.div>
              );
            })}
          </div>

          {/* Success Message */}
          <AnimatePresence>
            {isComplete && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-6 p-4 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl text-center"
              >
                <p className="text-green-800 font-medium">
                  🎉 All set! Redirecting to your dashboard...
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
};

export default PaymentProcessingModal;
