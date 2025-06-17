'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { 
  BookOpen, 
  Target, 
  Mic, 
  ArrowRight,
  Sparkles,
  Globe
} from 'lucide-react';

interface EmptyStateProps {
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ 
  className = "" 
}) => {
  const router = useRouter();

  const handleCreatePlan = () => {
    // Navigate to language selection to start creating a plan
    router.push('/language-selection');
  };

  const handleTakeAssessment = () => {
    // Navigate to assessment
    router.push('/assessment/speaking');
  };

  const handleExploreLanguages = () => {
    // Navigate to language selection
    router.push('/language-selection');
  };

  return (
    <section className={`py-16 bg-gradient-to-br from-gray-50 to-white ${className}`}>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Animated illustration */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="relative mx-auto w-32 h-32 mb-6">
            {/* Background circle */}
            <motion.div
              className="absolute inset-0 bg-gradient-to-br from-teal-100 to-blue-100 rounded-full"
              animate={{ scale: [1, 1.05, 1] }}
              transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            />
            
            {/* Icons */}
            <div className="absolute inset-0 flex items-center justify-center">
              <motion.div
                animate={{ rotate: [0, 5, -5, 0] }}
                transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
              >
                <BookOpen className="h-12 w-12 text-teal-600" />
              </motion.div>
            </div>
            
            {/* Floating elements */}
            <motion.div
              className="absolute -top-2 -right-2"
              animate={{ y: [-5, 5, -5] }}
              transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            >
              <Sparkles className="h-6 w-6 text-yellow-500" />
            </motion.div>
            
            <motion.div
              className="absolute -bottom-2 -left-2"
              animate={{ y: [5, -5, 5] }}
              transition={{ duration: 2, repeat: Infinity, ease: "easeInOut", delay: 1 }}
            >
              <Globe className="h-6 w-6 text-blue-500" />
            </motion.div>
          </div>
        </motion.div>

        {/* Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <h2 className="text-3xl font-bold text-gray-800 mb-4">
            Start Your Language Learning Journey
          </h2>
          <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
            Create your first personalized learning plan and begin practicing with our AI tutor. 
            Get assessed, set goals, and track your progress as you become fluent.
          </p>
        </motion.div>

        {/* Action cards */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          {/* Take Assessment */}
          <motion.div
            className="bg-white rounded-xl p-6 shadow-md border border-gray-100 hover:shadow-lg transition-all duration-300"
            whileHover={{ y: -4 }}
          >
            <div className="w-12 h-12 bg-gradient-to-br from-purple-100 to-pink-100 rounded-xl flex items-center justify-center mx-auto mb-4">
              <Mic className="h-6 w-6 text-purple-600" />
            </div>
            <h3 className="font-semibold text-gray-800 mb-2">Take Assessment</h3>
            <p className="text-sm text-gray-600 mb-4">
              Discover your current level with our AI-powered speaking assessment
            </p>
            <Button
              onClick={handleTakeAssessment}
              variant="outline"
              className="w-full border-purple-200 text-purple-600 hover:bg-purple-50"
            >
              Start Assessment
            </Button>
          </motion.div>

          {/* Create Plan */}
          <motion.div
            className="bg-white rounded-xl p-6 shadow-md border border-gray-100 hover:shadow-lg transition-all duration-300 ring-2 ring-teal-100"
            whileHover={{ y: -4 }}
          >
            <div className="w-12 h-12 bg-gradient-to-br from-teal-100 to-blue-100 rounded-xl flex items-center justify-center mx-auto mb-4">
              <Target className="h-6 w-6 text-teal-600" />
            </div>
            <h3 className="font-semibold text-gray-800 mb-2">Create Learning Plan</h3>
            <p className="text-sm text-gray-600 mb-4">
              Build a personalized plan based on your goals and schedule
            </p>
            <Button
              onClick={handleCreatePlan}
              className="w-full bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white"
            >
              Create Plan
            </Button>
          </motion.div>

          {/* Explore Languages */}
          <motion.div
            className="bg-white rounded-xl p-6 shadow-md border border-gray-100 hover:shadow-lg transition-all duration-300"
            whileHover={{ y: -4 }}
          >
            <div className="w-12 h-12 bg-gradient-to-br from-green-100 to-emerald-100 rounded-xl flex items-center justify-center mx-auto mb-4">
              <Globe className="h-6 w-6 text-green-600" />
            </div>
            <h3 className="font-semibold text-gray-800 mb-2">Explore Languages</h3>
            <p className="text-sm text-gray-600 mb-4">
              Browse available languages and start practicing immediately
            </p>
            <Button
              onClick={handleExploreLanguages}
              variant="outline"
              className="w-full border-green-200 text-green-600 hover:bg-green-50"
            >
              Explore
            </Button>
          </motion.div>
        </motion.div>

        {/* Quick start button */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
        >
          <Button
            onClick={handleCreatePlan}
            size="lg"
            className="bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white px-8 py-4 rounded-xl font-medium shadow-lg hover:shadow-xl transition-all duration-300"
          >
            Get Started Now
            <ArrowRight className="h-5 w-5 ml-2" />
          </Button>
        </motion.div>

        {/* Features preview */}
        <motion.div
          className="mt-12 pt-8 border-t border-gray-200"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.8 }}
        >
          <p className="text-sm text-gray-500 mb-4">What you'll get:</p>
          <div className="flex flex-wrap justify-center gap-6 text-sm text-gray-600">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-teal-500 rounded-full"></div>
              <span>Personalized learning plans</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span>AI-powered conversations</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              <span>Progress tracking</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Real-time feedback</span>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default EmptyState;
