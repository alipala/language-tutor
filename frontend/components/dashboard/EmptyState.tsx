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
  Globe,
  Clock,
  TrendingUp,
  MessageSquare,
  Award,
  Users,
  Star,
  Play,
  Zap,
  Brain,
  CheckCircle,
  Languages,
  Volume2,
  BarChart3,
  Lightbulb,
  Headphones,
  Rocket,
  MapPin,
  Compass
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
    // Navigate to language selection first (same as practice)
    router.push('/language-selection');
  };

  const handleExploreLanguages = () => {
    // Navigate to language selection
    router.push('/language-selection');
  };

  return (
    <section className={`pt-24 pb-12 bg-gradient-to-br from-gray-50 to-white min-h-screen ${className}`}>
      {/* Subtle Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-teal-50 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-50 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>
        <div className="absolute top-40 left-40 w-80 h-80 bg-purple-50 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-4000"></div>
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* AI Learning Plan Reminder */}
        <div className="max-w-4xl mx-auto mb-8">
          <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-2xl p-6">
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center flex-shrink-0">
                <Sparkles className="w-6 h-6 text-amber-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-amber-900 mb-2">
                  🎯 No Custom Learning Plan Yet
                </h3>
                <p className="text-amber-800">
                  You don't have a personalized AI-adaptive learning plan. Create one now to get a customized roadmap 
                  based on your current level, goals, and learning preferences for maximum progress!
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Main Action Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-12 max-w-5xl mx-auto">
          {/* AI Learning Plan Card */}
          <div className="group relative overflow-hidden rounded-2xl bg-white border border-gray-200 p-6 shadow-lg hover:shadow-2xl transition-all duration-300 hover:scale-[1.02] hover:-translate-y-1 flex flex-col h-full cursor-pointer">
            <div className="relative z-10 flex flex-col h-full">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                  <Award className="w-6 h-6 text-purple-600" />
                </div>
                <div className="text-right">
                  <div className="text-gray-500 text-xs">Perfect for</div>
                  <div className="text-gray-800 font-semibold text-sm">New learners</div>
                </div>
              </div>
              
              <h3 className="text-xl font-bold text-gray-800 mb-3">AI Learning Plan</h3>
              <p className="text-gray-600 text-sm leading-relaxed" style={{ minHeight: '3rem', marginBottom: '1rem' }}>
                Get a personalized AI-adaptive learning plan based on your speaking assessment. 
                Perfect for structured, goal-oriented language learning.
              </p>

              {/* Visual Learning Journey */}
              <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl p-4 mb-4 flex-grow">
                <div className="text-center mb-3">
                  <h4 className="text-sm font-bold text-purple-800 mb-1">Your Learning Journey</h4>
                  <p className="text-xs text-purple-600">Personalized AI-powered path</p>
                </div>
                
                {/* Visual Journey Steps */}
                <div className="flex items-center justify-between relative">
                  {/* Connection Line */}
                  <div className="absolute top-6 left-6 right-6 h-0.5 bg-gradient-to-r from-purple-200 via-purple-300 to-purple-200"></div>
                  
                  {/* Step 1: Language Selection */}
                  <div className="relative z-10 flex flex-col items-center">
                    <div className="w-12 h-12 bg-gradient-to-br from-purple-400 to-purple-500 rounded-full flex items-center justify-center shadow-lg mb-2">
                      <Languages className="w-6 h-6 text-white" />
                    </div>
                    <span className="text-xs font-medium text-purple-700">Choose</span>
                  </div>
                  
                  {/* Step 2: Speaking Assessment */}
                  <div className="relative z-10 flex flex-col items-center">
                    <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-indigo-500 rounded-full flex items-center justify-center shadow-lg mb-2">
                      <Mic className="w-6 h-6 text-white" />
                    </div>
                    <span className="text-xs font-medium text-purple-700">Speak</span>
                  </div>
                  
                  {/* Step 3: AI Analysis */}
                  <div className="relative z-10 flex flex-col items-center">
                    <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-blue-500 rounded-full flex items-center justify-center shadow-lg mb-2">
                      <Brain className="w-6 h-6 text-white" />
                    </div>
                    <span className="text-xs font-medium text-purple-700">Analyze</span>
                  </div>
                  
                  {/* Step 4: Learning Plan */}
                  <div className="relative z-10 flex flex-col items-center">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-teal-500 rounded-full flex items-center justify-center shadow-lg mb-2">
                      <Rocket className="w-6 h-6 text-white" />
                    </div>
                    <span className="text-xs font-medium text-purple-700">Learn</span>
                  </div>
                </div>
                
                {/* Key Benefits */}
                <div className="mt-4 grid grid-cols-2 gap-2">
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 bg-purple-200 rounded-full flex items-center justify-center">
                      <Clock className="w-2.5 h-2.5 text-purple-600" />
                    </div>
                    <span className="text-xs text-purple-700">5-10 min</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 bg-purple-200 rounded-full flex items-center justify-center">
                      <Target className="w-2.5 h-2.5 text-purple-600" />
                    </div>
                    <span className="text-xs text-purple-700">CEFR Level</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 bg-purple-200 rounded-full flex items-center justify-center">
                      <Lightbulb className="w-2.5 h-2.5 text-purple-600" />
                    </div>
                    <span className="text-xs text-purple-700">AI Insights</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 bg-purple-200 rounded-full flex items-center justify-center">
                      <MapPin className="w-2.5 h-2.5 text-purple-600" />
                    </div>
                    <span className="text-xs text-purple-700">Custom Plan</span>
                  </div>
                </div>
              </div>

              <Button
                onClick={handleTakeAssessment}
                className="w-full bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 text-white py-2 px-4 rounded-lg font-medium transition-all duration-300 text-sm shadow-md hover:shadow-lg mt-auto"
              >
                <Mic className="w-4 h-4 mr-2" />
                Start Assessment
              </Button>
            </div>

            {/* Subtle background decoration */}
            <div className="absolute top-0 right-0 w-24 h-24 bg-purple-50 rounded-full -translate-y-12 translate-x-12 opacity-50"></div>
            <div className="absolute bottom-0 left-0 w-16 h-16 bg-purple-50 rounded-full translate-y-8 -translate-x-8 opacity-30"></div>
          </div>

          {/* Quick Practice Card */}
          <div className="group relative overflow-hidden rounded-2xl bg-white border border-gray-200 p-6 shadow-lg hover:shadow-2xl transition-all duration-300 hover:scale-[1.02] hover:-translate-y-1 flex flex-col h-full cursor-pointer">
            <div className="relative z-10 flex flex-col h-full">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 bg-teal-100 rounded-xl flex items-center justify-center">
                  <MessageSquare className="w-6 h-6 text-teal-600" />
                </div>
                <div className="text-right">
                  <div className="text-gray-500 text-xs">Perfect for</div>
                  <div className="text-gray-800 font-semibold text-sm">All levels</div>
                </div>
              </div>
              
              <h3 className="text-xl font-bold text-gray-800 mb-3">Quick Practice</h3>
              <p className="text-gray-600 text-sm leading-relaxed" style={{ minHeight: '3rem', marginBottom: '1rem' }}>
                Jump straight into conversation practice with our AI tutor. 
                Perfect for immediate practice without formal assessment.
              </p>

              {/* Visual Practice Journey */}
              <div className="bg-gradient-to-r from-teal-50 to-blue-50 rounded-xl p-4 mb-4 flex-grow">
                <div className="text-center mb-3">
                  <h4 className="text-sm font-bold text-teal-800 mb-1">Quick Start Journey</h4>
                  <p className="text-xs text-teal-600">Instant conversation practice</p>
                </div>
                
                {/* Visual Journey Steps */}
                <div className="flex items-center justify-between relative">
                  {/* Connection Line */}
                  <div className="absolute top-6 left-6 right-6 h-0.5 bg-gradient-to-r from-teal-200 via-teal-300 to-teal-200"></div>
                  
                  {/* Step 1: Language Selection */}
                  <div className="relative z-10 flex flex-col items-center">
                    <div className="w-12 h-12 bg-gradient-to-br from-teal-400 to-teal-500 rounded-full flex items-center justify-center shadow-lg mb-2">
                      <Languages className="w-6 h-6 text-white" />
                    </div>
                    <span className="text-xs font-medium text-teal-700">Choose</span>
                  </div>
                  
                  {/* Step 2: Topic Selection */}
                  <div className="relative z-10 flex flex-col items-center">
                    <div className="w-12 h-12 bg-gradient-to-br from-teal-500 to-blue-500 rounded-full flex items-center justify-center shadow-lg mb-2">
                      <BookOpen className="w-6 h-6 text-white" />
                    </div>
                    <span className="text-xs font-medium text-teal-700">Topic</span>
                  </div>
                  
                  {/* Step 3: Level Selection */}
                  <div className="relative z-10 flex flex-col items-center">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-full flex items-center justify-center shadow-lg mb-2">
                      <Target className="w-6 h-6 text-white" />
                    </div>
                    <span className="text-xs font-medium text-teal-700">Level</span>
                  </div>
                  
                  {/* Step 4: Practice */}
                  <div className="relative z-10 flex flex-col items-center">
                    <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center shadow-lg mb-2">
                      <Headphones className="w-6 h-6 text-white" />
                    </div>
                    <span className="text-xs font-medium text-teal-700">Practice</span>
                  </div>
                </div>
                
                {/* Key Benefits */}
                <div className="mt-4 grid grid-cols-2 gap-2">
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 bg-teal-200 rounded-full flex items-center justify-center">
                      <Zap className="w-2.5 h-2.5 text-teal-600" />
                    </div>
                    <span className="text-xs text-teal-700">Instant Start</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 bg-teal-200 rounded-full flex items-center justify-center">
                      <Volume2 className="w-2.5 h-2.5 text-teal-600" />
                    </div>
                    <span className="text-xs text-teal-700">Voice Chat</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 bg-teal-200 rounded-full flex items-center justify-center">
                      <Star className="w-2.5 h-2.5 text-teal-600" />
                    </div>
                    <span className="text-xs text-teal-700">Live Feedback</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 bg-teal-200 rounded-full flex items-center justify-center">
                      <Globe className="w-2.5 h-2.5 text-teal-600" />
                    </div>
                    <span className="text-xs text-teal-700">20+ Topics</span>
                  </div>
                </div>
              </div>

              <Button
                onClick={handleExploreLanguages}
                className="w-full bg-gradient-to-r from-teal-500 to-blue-600 hover:from-teal-600 hover:to-blue-700 text-white py-2 px-4 rounded-lg font-medium transition-all duration-300 text-sm shadow-md hover:shadow-lg mt-auto"
              >
                <Play className="w-4 h-4 mr-2" />
                Start Practice
              </Button>
            </div>

            {/* Subtle background decoration */}
            <div className="absolute top-0 right-0 w-24 h-24 bg-teal-50 rounded-full -translate-y-12 translate-x-12 opacity-50"></div>
            <div className="absolute bottom-0 left-0 w-16 h-16 bg-teal-50 rounded-full translate-y-8 -translate-x-8 opacity-30"></div>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-purple-100 to-pink-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Brain className="w-8 h-8 text-purple-600" />
            </div>
            <h4 className="text-lg font-semibold text-gray-800 mb-2">AI-Powered Learning</h4>
            <p className="text-gray-600">
              Advanced AI technology adapts to your learning style and provides personalized feedback
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-teal-100 to-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <TrendingUp className="w-8 h-8 text-teal-600" />
            </div>
            <h4 className="text-lg font-semibold text-gray-800 mb-2">Track Your Progress</h4>
            <p className="text-gray-600">
              Monitor your improvement with detailed analytics, streaks, and achievement badges
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-green-100 to-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <h4 className="text-lg font-semibold text-gray-800 mb-2">Proven Results</h4>
            <p className="text-gray-600">
              Join thousands of learners who have improved their language skills with our platform
            </p>
          </div>
        </div>

      </div>
    </section>
  );
};

export default EmptyState;
