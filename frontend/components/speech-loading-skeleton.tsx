'use client';

import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

interface SpeechLoadingSkeletonProps {
  stage: 'initializing' | 'fetching-token' | 'connecting' | 'ready';
  language?: string;
  level?: string;
  topic?: string;
}

export default function SpeechLoadingSkeleton({ 
  stage, 
  language = 'Language',
  level = 'Level',
  topic = 'Topic'
}: SpeechLoadingSkeletonProps) {
  const [progress, setProgress] = useState(0);

  // Simulate progress based on stage
  useEffect(() => {
    const targetProgress = {
      'initializing': 25,
      'fetching-token': 60,
      'connecting': 85,
      'ready': 100
    }[stage];

    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= targetProgress) return targetProgress;
        return prev + 1;
      });
    }, 20);

    return () => clearInterval(interval);
  }, [stage]);

  const getStageMessage = () => {
    switch (stage) {
      case 'initializing':
        return 'Preparing your session...';
      case 'fetching-token':
        return 'Connecting to AI tutor...';
      case 'connecting':
        return 'Almost ready...';
      case 'ready':
        return 'Ready to speak!';
    }
  };

  const getStageIcon = () => {
    switch (stage) {
      case 'initializing':
        return (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="w-16 h-16 border-4 border-[#4ECFBF] border-t-transparent rounded-full"
          />
        );
      case 'fetching-token':
        return (
          <motion.svg
            className="w-16 h-16 text-[#4ECFBF]"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            animate={{ scale: [1, 1.1, 1] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </motion.svg>
        );
      case 'connecting':
        return (
          <motion.svg
            className="w-16 h-16 text-[#4ECFBF]"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1, repeat: Infinity }}
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
          </motion.svg>
        );
      case 'ready':
        return (
          <motion.svg
            className="w-16 h-16 text-green-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 200, damping: 10 }}
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </motion.svg>
        );
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header Skeleton */}
      <div className="text-center mb-6 px-4">
        <motion.h1 
          className="text-4xl font-bold tracking-tight text-white"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {language} Conversation
        </motion.h1>
        <motion.p 
          className="text-white/80 mt-2"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          Level: {level} - {getStageMessage()}
        </motion.p>
      </div>

      {/* User Selection Summary Skeleton */}
      <motion.div 
        className="bg-white border-2 border-[#4ECFBF] rounded-xl p-4 mb-4 w-full max-w-7xl mx-auto shadow-lg"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <div className="flex flex-wrap items-center justify-center gap-4 text-gray-800">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-[#4ECFBF] rounded-full flex items-center justify-center shadow-lg">
              <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M7 2a1 1 0 011 1v1h3a1 1 0 110 2H9.578a18.87 18.87 0 01-1.724 4.78c.29.354.596.696.914 1.026a1 1 0 11-1.44 1.389c-.188-.196-.373-.396-.554-.6a19.098 19.098 0 01-3.107 3.567 1 1 0 01-1.334-1.49 17.087 17.087 0 003.13-3.733a18.992 18.992 0 01-1.487-2.494 1 1 0 111.79-.89c.234.47.489.928.764 1.372.417-.934.752-1.913.997-2.927H3a1 1 0 110-2h3V3a1 1 0 011-1zm6 6a1 1 0 01.894.553l2.991 5.982a.869.869 0 01.02.037l.99 1.98A1 1 0 0117 18H10a1 1 0 01-.894-1.447l.99-1.98.019-.038 2.991-5.982A1 1 0 0114 8h-1z" clipRule="evenodd" />
              </svg>
            </div>
            <span className="font-semibold text-lg">{language}</span>
          </div>
          
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-[#FFD63A] rounded-full flex items-center justify-center shadow-lg">
              <svg className="w-5 h-5 text-gray-800" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <span className="font-semibold text-lg">Level {level}</span>
          </div>
          
          {topic && (
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-[#4ECFBF] rounded-full flex items-center justify-center shadow-lg">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                </svg>
              </div>
              <span className="font-semibold text-lg">{topic}</span>
            </div>
          )}
        </div>
      </motion.div>

      {/* Main Loading Area */}
      <div className="flex-1 flex flex-col items-center justify-center px-4">
        <motion.div
          className="text-center max-w-md"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
        >
          {/* Animated Icon */}
          <div className="flex justify-center mb-6">
            {getStageIcon()}
          </div>

          {/* Stage Message */}
          <motion.h2
            className="text-2xl font-bold text-white mb-2"
            key={stage}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            {getStageMessage()}
          </motion.h2>

          {/* Progress Bar */}
          <div className="w-full bg-white/20 rounded-full h-2 mb-4 overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-[#4ECFBF] to-[#FFD63A] rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>

          {/* Progress Percentage */}
          <p className="text-white/60 text-sm mb-6">{progress}% complete</p>

          {/* Stage-specific Tips */}
          <motion.div
            className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20"
            key={`tip-${stage}`}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: 0.2 }}
          >
            {stage === 'initializing' && (
              <p className="text-white/80 text-sm">
                💡 <strong>Tip:</strong> Find a quiet space for the best experience
              </p>
            )}
            {stage === 'fetching-token' && (
              <p className="text-white/80 text-sm">
                🎧 <strong>Tip:</strong> Use headphones to prevent audio feedback
              </p>
            )}
            {stage === 'connecting' && (
              <p className="text-white/80 text-sm">
                🎤 <strong>Tip:</strong> Speak clearly and at a normal pace
              </p>
            )}
            {stage === 'ready' && (
              <p className="text-white/80 text-sm">
                ✨ <strong>Ready!</strong> Click the microphone to start speaking
              </p>
            )}
          </motion.div>

          {/* Animated Dots for Loading States */}
          {stage !== 'ready' && (
            <motion.div
              className="flex justify-center gap-2 mt-6"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8 }}
            >
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  className="w-2 h-2 bg-[#4ECFBF] rounded-full"
                  animate={{
                    scale: [1, 1.5, 1],
                    opacity: [0.5, 1, 0.5],
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    delay: i * 0.2,
                  }}
                />
              ))}
            </motion.div>
          )}
        </motion.div>
      </div>

      {/* Skeleton for Conversation Areas */}
      <motion.div
        className="grid grid-cols-1 lg:grid-cols-2 gap-6 px-4 pb-8 max-w-7xl mx-auto w-full"
        initial={{ opacity: 0 }}
        animate={{ opacity: stage === 'connecting' || stage === 'ready' ? 0.3 : 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Analysis Section Skeleton */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6 h-[650px]">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-6 h-6 bg-white/20 rounded animate-pulse" />
            <div className="h-4 bg-white/20 rounded w-48 animate-pulse" />
          </div>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 bg-white/10 rounded animate-pulse" />
            ))}
          </div>
        </div>

        {/* Conversation Section Skeleton */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6 h-[650px]">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-6 h-6 bg-white/20 rounded animate-pulse" />
            <div className="h-4 bg-white/20 rounded w-48 animate-pulse" />
          </div>
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div 
                key={i} 
                className={`h-16 bg-white/10 rounded animate-pulse ${i % 2 === 0 ? 'ml-auto w-3/4' : 'w-3/4'}`} 
              />
            ))}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
