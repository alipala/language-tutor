'use client';

import React, { useState, useEffect } from 'react';
import { X, Check, ChevronRight, Sparkles, Target, Calendar, Zap, ArrowRight, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { createLearningPlan, getEnrichedGoals, getSubGoals } from '@/lib/learning-api';
import { SpeakingAssessmentResult } from '@/lib/speaking-assessment-api';
import { isAuthenticated } from '@/lib/auth-utils';

interface EnhancedLearningPlanModalProps {
  isOpen: boolean;
  onClose: () => void;
  proficiencyLevel: string;
  language: string;
  onPlanCreated: (planId: string) => void;
  assessmentData?: SpeakingAssessmentResult;
}

interface MainGoal {
  id: string;
  text: string;
  category: string;
  icon: string;
  description: string;
}

interface SubGoal {
  id: string;
  text: string;
  description: string;
}

export default function EnhancedLearningPlanModal({
  isOpen,
  onClose,
  proficiencyLevel,
  language,
  onPlanCreated,
  assessmentData
}: EnhancedLearningPlanModalProps) {
  // State management
  const [step, setStep] = useState<'goals' | 'subgoals' | 'duration' | 'creating'>('goals');
  const [mainGoals, setMainGoals] = useState<MainGoal[]>([]);
  const [selectedMainGoal, setSelectedMainGoal] = useState<string | null>(null);
  const [subGoals, setSubGoals] = useState<SubGoal[]>([]);
  const [selectedSubGoals, setSelectedSubGoals] = useState<string[]>([]);
  const [duration, setDuration] = useState<number>(3);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load enriched goals when modal opens
  useEffect(() => {
    if (isOpen) {
      loadEnrichedGoals();
    }
  }, [isOpen]);

  const loadEnrichedGoals = async () => {
    try {
      setIsLoading(true);
      const goals = await getEnrichedGoals();
      setMainGoals(goals);
      setIsLoading(false);
    } catch (err) {
      console.error('Error loading enriched goals:', err);
      setError('Failed to load learning goals');
      setIsLoading(false);
    }
  };

  const handleMainGoalSelect = async (goalId: string) => {
    setSelectedMainGoal(goalId);
    setIsLoading(true);
    
    try {
      const subGoalsData = await getSubGoals(goalId);
      setSubGoals(subGoalsData);
      setStep('subgoals');
      setIsLoading(false);
    } catch (err) {
      console.error('Error loading sub-goals:', err);
      setError('Failed to load sub-goals');
      setIsLoading(false);
    }
  };

  const handleSubGoalToggle = (subGoalId: string) => {
    setSelectedSubGoals(prev => {
      if (prev.includes(subGoalId)) {
        return prev.filter(id => id !== subGoalId);
      } else {
        // Limit to 3 sub-goals
        if (prev.length >= 3) {
          return prev;
        }
        return [...prev, subGoalId];
      }
    });
  };

  const handleCreatePlan = async () => {
    if (!selectedMainGoal) return;

    setStep('creating');
    setIsLoading(true);

    try {
      const planData = {
        language,
        proficiency_level: proficiencyLevel,
        goals: [selectedMainGoal],
        sub_goals: selectedSubGoals,
        duration_months: duration,
        assessment_data: assessmentData
      };

      console.log('[ENHANCED_MODAL] Creating plan with data:', planData);

      const plan = await createLearningPlan(planData);
      
      console.log('[ENHANCED_MODAL] Plan created successfully:', plan.id);
      
      onPlanCreated(plan.id);
      handleClose();
    } catch (err: any) {
      console.error('[ENHANCED_MODAL] Error creating plan:', err);
      setError(err.message || 'Failed to create learning plan');
      setIsLoading(false);
      setStep('duration');
    }
  };

  const handleClose = () => {
    setStep('goals');
    setSelectedMainGoal(null);
    setSelectedSubGoals([]);
    setDuration(3);
    setError(null);
    onClose();
  };

  const handleBack = () => {
    if (step === 'subgoals') {
      setStep('goals');
      setSelectedMainGoal(null);
      setSubGoals([]);
    } else if (step === 'duration') {
      setStep('subgoals');
      setSelectedSubGoals([]);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-white rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="relative bg-gradient-to-r from-[#4ECFBF] to-[#3AA8B1] p-6 text-white">
          <button
            onClick={handleClose}
            className="absolute top-4 right-4 p-2 rounded-full hover:bg-white/20 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
          
          <div className="flex items-center space-x-3 mb-2">
            <div className="p-2 bg-white/20 rounded-lg">
              <Sparkles className="h-6 w-6" />
            </div>
            <h2 className="text-2xl font-bold">Create Your Learning Plan</h2>
          </div>
          
          <p className="text-white/90 text-sm">
            Personalized for {language} • Level: {proficiencyLevel}
          </p>

          {/* Progress Steps */}
          <div className="flex items-center justify-center space-x-2 mt-6">
            <div className={`flex items-center ${step === 'goals' ? 'text-white' : 'text-white/60'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                step === 'goals' ? 'bg-white text-[#4ECFBF]' : 'bg-white/20'
              }`}>
                1
              </div>
              <span className="ml-2 text-sm font-medium hidden sm:inline">Goal</span>
            </div>
            
            <ChevronRight className="h-4 w-4 text-white/60" />
            
            <div className={`flex items-center ${step === 'subgoals' ? 'text-white' : 'text-white/60'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                step === 'subgoals' ? 'bg-white text-[#4ECFBF]' : 'bg-white/20'
              }`}>
                2
              </div>
              <span className="ml-2 text-sm font-medium hidden sm:inline">Focus</span>
            </div>
            
            <ChevronRight className="h-4 w-4 text-white/60" />
            
            <div className={`flex items-center ${step === 'duration' || step === 'creating' ? 'text-white' : 'text-white/60'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                step === 'duration' || step === 'creating' ? 'bg-white text-[#4ECFBF]' : 'bg-white/20'
              }`}>
                3
              </div>
              <span className="ml-2 text-sm font-medium hidden sm:inline">Duration</span>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Step 1: Main Goal Selection */}
          {step === 'goals' && (
            <div className="space-y-4">
              <div className="text-center mb-6">
                <h3 className="text-xl font-bold text-[#333333] mb-2">
                  What's your main learning goal?
                </h3>
                <p className="text-[#555555] text-sm">
                  Choose the primary reason you're learning {language}
                </p>
              </div>

              {isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 text-[#4ECFBF] animate-spin" />
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {mainGoals.map((goal) => (
                    <button
                      key={goal.id}
                      onClick={() => handleMainGoalSelect(goal.id)}
                      className="group relative p-6 bg-gradient-to-br from-white to-[#F8FDFC] rounded-xl border-2 border-[#4ECFBF]/20 hover:border-[#4ECFBF] shadow-md hover:shadow-xl transition-all duration-300 text-left"
                    >
                      <div className="flex items-start space-x-4">
                        <div className="text-4xl">{goal.icon}</div>
                        <div className="flex-1">
                          <h4 className="text-lg font-bold text-[#333333] mb-2 group-hover:text-[#4ECFBF] transition-colors">
                            {goal.text}
                          </h4>
                          <p className="text-sm text-[#555555] mb-3">
                            {goal.description}
                          </p>
                          <div className="flex items-center text-xs text-[#4ECFBF] font-medium">
                            <span>Select goal</span>
                            <ChevronRight className="h-3 w-3 ml-1 group-hover:translate-x-1 transition-transform" />
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Step 2: Sub-Goals Selection */}
          {step === 'subgoals' && (
            <div className="space-y-4">
              <button
                onClick={handleBack}
                className="flex items-center text-[#4ECFBF] hover:text-[#3AA8B1] transition-colors mb-4"
              >
                <ChevronRight className="h-4 w-4 rotate-180 mr-1" />
                <span className="text-sm">Back to goals</span>
              </button>

              <div className="text-center mb-6">
                <h3 className="text-xl font-bold text-[#333333] mb-2">
                  What specific areas do you want to focus on?
                </h3>
                <p className="text-[#555555] text-sm">
                  Select up to 3 focus areas (optional - you can skip this step)
                </p>
              </div>

              {isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 text-[#4ECFBF] animate-spin" />
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-1 gap-3">
                    {subGoals.map((subGoal) => {
                      const isSelected = selectedSubGoals.includes(subGoal.id);
                      const isDisabled = !isSelected && selectedSubGoals.length >= 3;

                      return (
                        <button
                          key={subGoal.id}
                          onClick={() => !isDisabled && handleSubGoalToggle(subGoal.id)}
                          disabled={isDisabled}
                          className={`p-4 rounded-xl border-2 transition-all duration-200 text-left ${
                            isSelected
                              ? 'bg-[#4ECFBF]/10 border-[#4ECFBF] shadow-md'
                              : isDisabled
                              ? 'bg-gray-50 border-gray-200 opacity-50 cursor-not-allowed'
                              : 'bg-white border-gray-200 hover:border-[#4ECFBF]/50 hover:shadow-md'
                          }`}
                        >
                          <div className="flex items-start space-x-3">
                            <div className={`mt-0.5 w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                              isSelected
                                ? 'bg-[#4ECFBF] border-[#4ECFBF]'
                                : 'border-gray-300'
                            }`}>
                              {isSelected && <Check className="h-3 w-3 text-white" />}
                            </div>
                            <div className="flex-1">
                              <h4 className="font-semibold text-[#333333] mb-1">
                                {subGoal.text}
                              </h4>
                              <p className="text-sm text-[#555555]">
                                {subGoal.description}
                              </p>
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>

                  <div className="flex items-center justify-between mt-6 pt-6 border-t border-gray-200">
                    <div className="text-sm text-[#555555]">
                      {selectedSubGoals.length} of 3 selected
                    </div>
                    <Button
                      onClick={() => setStep('duration')}
                      className="bg-[#4ECFBF] hover:bg-[#3AA8B1] text-white px-6 py-2 rounded-lg flex items-center space-x-2"
                    >
                      <span>Continue</span>
                      <ArrowRight className="h-4 w-4" />
                    </Button>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Step 3: Duration Selection */}
          {step === 'duration' && (
            <div className="space-y-6">
              <button
                onClick={handleBack}
                className="flex items-center text-[#4ECFBF] hover:text-[#3AA8B1] transition-colors mb-4"
              >
                <ChevronRight className="h-4 w-4 rotate-180 mr-1" />
                <span className="text-sm">Back to focus areas</span>
              </button>

              <div className="text-center mb-8">
                <h3 className="text-xl font-bold text-[#333333] mb-2">
                  How long do you want to study?
                </h3>
                <p className="text-[#555555] text-sm">
                  Choose a duration that fits your schedule and goals
                </p>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[1, 2, 3, 6].map((months) => (
                  <button
                    key={months}
                    onClick={() => setDuration(months)}
                    className={`p-6 rounded-xl border-2 transition-all duration-200 ${
                      duration === months
                        ? 'bg-[#4ECFBF]/10 border-[#4ECFBF] shadow-lg scale-105'
                        : 'bg-white border-gray-200 hover:border-[#4ECFBF]/50 hover:shadow-md'
                    }`}
                  >
                    <div className="text-center">
                      <Calendar className={`h-8 w-8 mx-auto mb-2 ${
                        duration === months ? 'text-[#4ECFBF]' : 'text-gray-400'
                      }`} />
                      <div className="text-2xl font-bold text-[#333333] mb-1">
                        {months}
                      </div>
                      <div className="text-sm text-[#555555]">
                        {months === 1 ? 'Month' : 'Months'}
                      </div>
                      <div className="text-xs text-[#777777] mt-2">
                        {months * 8} sessions
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              {/* Summary Card */}
              <div className="bg-gradient-to-br from-[#F0FDFB] to-white p-6 rounded-xl border border-[#4ECFBF]/30 shadow-md">
                <h4 className="font-semibold text-[#333333] mb-4 flex items-center">
                  <Target className="h-5 w-5 mr-2 text-[#4ECFBF]" />
                  Your Learning Plan Summary
                </h4>
                
                <div className="space-y-3 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-[#555555]">Language:</span>
                    <span className="font-medium text-[#333333]">{language}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[#555555]">Level:</span>
                    <span className="font-medium text-[#333333]">{proficiencyLevel}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[#555555]">Main Goal:</span>
                    <span className="font-medium text-[#333333]">
                      {mainGoals.find(g => g.id === selectedMainGoal)?.text}
                    </span>
                  </div>
                  {selectedSubGoals.length > 0 && (
                    <div className="flex items-start justify-between">
                      <span className="text-[#555555]">Focus Areas:</span>
                      <div className="text-right">
                        {selectedSubGoals.map(id => {
                          const subGoal = subGoals.find(sg => sg.id === id);
                          return (
                            <div key={id} className="font-medium text-[#333333] text-xs">
                              • {subGoal?.text}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                  <div className="flex items-center justify-between">
                    <span className="text-[#555555]">Duration:</span>
                    <span className="font-medium text-[#333333]">{duration} months</span>
                  </div>
                  <div className="flex items-center justify-between pt-3 border-t border-[#4ECFBF]/20">
                    <span className="text-[#555555]">Total Sessions:</span>
                    <span className="font-bold text-[#4ECFBF] text-lg">{duration * 8}</span>
                  </div>
                </div>
              </div>

              <Button
                onClick={handleCreatePlan}
                disabled={isLoading}
                className="w-full bg-gradient-to-r from-[#4ECFBF] to-[#3AA8B1] hover:from-[#5CCFC0] hover:to-[#4BB8C1] text-white py-4 rounded-xl font-semibold text-lg shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center space-x-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    <span>Creating your plan...</span>
                  </>
                ) : (
                  <>
                    <Zap className="h-5 w-5" />
                    <span>Create My Learning Plan</span>
                  </>
                )}
              </Button>
            </div>
          )}

          {/* Step 4: Creating */}
          {step === 'creating' && (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="relative mb-6">
                <div className="absolute inset-0 bg-[#4ECFBF]/20 rounded-full blur-xl animate-pulse"></div>
                <div className="relative w-24 h-24 bg-gradient-to-br from-[#4ECFBF] to-[#3AA8B1] rounded-full flex items-center justify-center shadow-xl">
                  <Loader2 className="h-12 w-12 text-white animate-spin" />
                </div>
              </div>
              
              <h3 className="text-2xl font-bold text-[#333333] mb-2">
                Creating Your Personalized Plan
              </h3>
              <p className="text-[#555555] text-center max-w-md">
                Our AI is analyzing your assessment results and crafting a customized learning journey just for you...
              </p>
              
              <div className="mt-8 flex items-center space-x-2">
                <div className="w-2 h-2 bg-[#4ECFBF] rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-[#4ECFBF] rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-[#4ECFBF] rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
