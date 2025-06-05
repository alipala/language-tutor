'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

interface AuthSuccessTransitionProps {
  isVisible: boolean;
  type: 'login' | 'signup';
  onComplete: () => void;
}

export const AuthSuccessTransition: React.FC<AuthSuccessTransitionProps> = ({
  isVisible,
  type,
  onComplete
}) => {
  const [stage, setStage] = useState<'success' | 'loading' | 'redirecting'>('success');
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!isVisible) return;

    const timer1 = setTimeout(() => {
      setStage('loading');
      // Simulate progress
      let currentProgress = 0;
      const progressInterval = setInterval(() => {
        currentProgress += Math.random() * 15 + 5; // Random increment between 5-20
        if (currentProgress >= 100) {
          currentProgress = 100;
          clearInterval(progressInterval);
          setStage('redirecting');
          setTimeout(() => {
            onComplete();
          }, 800);
        }
        setProgress(currentProgress);
      }, 150);
    }, 1500); // Show success checkmark for 1.5s

    return () => {
      clearTimeout(timer1);
    };
  }, [isVisible, onComplete]);

  if (!isVisible) return null;

  const getStageText = () => {
    switch (stage) {
      case 'success':
        return type === 'login' ? 'Welcome back!' : 'Account created successfully!';
      case 'loading':
        return 'Setting up your learning environment...';
      case 'redirecting':
        return 'Taking you to your dashboard...';
      default:
        return '';
    }
  };

  const getSubText = () => {
    switch (stage) {
      case 'success':
        return type === 'login' ? 'Great to see you again' : 'Welcome to your language learning journey';
      case 'loading':
        return 'Preparing your personalized experience';
      case 'redirecting':
        return 'Almost ready!';
      default:
        return '';
    }
  };

  return (
    <motion.div
      className="fixed inset-0 bg-gradient-to-br from-[#4ECFBF] to-[#3db3a7] flex items-center justify-center z-50"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="text-center text-white px-6">
        {/* Success Checkmark */}
        {stage === 'success' && (
          <motion.div
            className="mb-6"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ 
              type: "spring",
              stiffness: 200,
              damping: 15,
              delay: 0.2 
            }}
          >
            <div className="w-20 h-20 mx-auto bg-white rounded-full flex items-center justify-center">
              <motion.svg
                className="w-10 h-10 text-[#4ECFBF]"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 0.8, delay: 0.5 }}
              >
                <motion.path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={3}
                  d="M5 13l4 4L19 7"
                />
              </motion.svg>
            </div>
          </motion.div>
        )}

        {/* Loading Spinner */}
        {(stage === 'loading' || stage === 'redirecting') && (
          <motion.div
            className="mb-6"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
          >
            <div className="w-16 h-16 mx-auto">
              <motion.div
                className="w-16 h-16 border-4 border-white/30 border-t-white rounded-full"
                animate={{ rotate: 360 }}
                transition={{
                  duration: 1,
                  repeat: Infinity,
                  ease: "linear"
                }}
              />
            </div>
          </motion.div>
        )}

        {/* Main Text */}
        <motion.h2
          className="text-2xl sm:text-3xl font-bold mb-2"
          key={stage} // This will trigger re-animation when stage changes
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {getStageText()}
        </motion.h2>

        {/* Sub Text */}
        <motion.p
          className="text-white/90 text-sm sm:text-base mb-6"
          key={`${stage}-sub`}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          {getSubText()}
        </motion.p>

        {/* Progress Bar */}
        {(stage === 'loading' || stage === 'redirecting') && (
          <motion.div
            className="w-64 max-w-full mx-auto"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: 0.2 }}
          >
            <div className="bg-white/20 rounded-full h-2 overflow-hidden">
              <motion.div
                className="bg-white h-full rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.3, ease: "easeOut" }}
              />
            </div>
            <motion.p
              className="text-white/80 text-xs mt-2"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
            >
              {Math.round(progress)}% complete
            </motion.p>
          </motion.div>
        )}

        {/* Decorative Elements */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {[...Array(6)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-2 h-2 bg-white/20 rounded-full"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
              }}
              animate={{
                y: [0, -20, 0],
                opacity: [0.2, 0.8, 0.2],
              }}
              transition={{
                duration: 2 + Math.random() * 2,
                repeat: Infinity,
                delay: Math.random() * 2,
              }}
            />
          ))}
        </div>
      </div>
    </motion.div>
  );
};
