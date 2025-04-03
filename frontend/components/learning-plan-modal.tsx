'use client';

import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import { getLearningGoals, createLearningPlan, LearningGoal, LearningPlanRequest } from '@/lib/learning-api';
import { useRouter } from 'next/navigation';
import { isAuthenticated } from '@/lib/auth-utils';

interface LearningPlanModalProps {
  isOpen: boolean;
  onClose: () => void;
  proficiencyLevel: string;
  language: string;
  onPlanCreated?: (planId: string) => void;
}

export default function LearningPlanModal({
  isOpen,
  onClose,
  proficiencyLevel,
  language,
  onPlanCreated
}: LearningPlanModalProps) {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [goals, setGoals] = useState<LearningGoal[]>([]);
  const [selectedGoals, setSelectedGoals] = useState<string[]>([]);
  const [customGoal, setCustomGoal] = useState('');
  const [duration, setDuration] = useState<number>(3);
  const [customDuration, setCustomDuration] = useState<number | null>(null);
  const [isCreatingPlan, setIsCreatingPlan] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [planId, setPlanId] = useState<string | null>(null);
  
  // Fetch learning goals when the modal opens
  useEffect(() => {
    if (isOpen) {
      fetchGoals();
    }
  }, [isOpen]);
  
  const fetchGoals = async () => {
    try {
      const goalsData = await getLearningGoals();
      setGoals(goalsData);
    } catch (error) {
      console.error('Error fetching learning goals:', error);
      setError('Failed to load learning goals. Please try again.');
    }
  };
  
  const handleNextStep = () => {
    if (step === 1 && selectedGoals.length === 0) {
      setError('Please select at least one learning goal');
      return;
    }
    
    if (step === 2 && !duration && !customDuration) {
      setError('Please select a duration for your learning plan');
      return;
    }
    
    setError(null);
    if (step < 3) {
      setStep(step + 1);
    } else {
      handleCreatePlan();
    }
  };
  
  const handlePrevStep = () => {
    if (step > 1) {
      setStep(step - 1);
    } else {
      onClose();
    }
  };
  
  const handleCreatePlan = async () => {
    setIsCreatingPlan(true);
    setError(null);
    
    try {
      // Prepare the learning plan request
      const planRequest: LearningPlanRequest = {
        language,
        proficiency_level: proficiencyLevel,
        goals: selectedGoals,
        duration_months: customDuration || duration,
        custom_goal: customGoal || undefined
      };
      
      // Check if user is already authenticated
      const isUserAuthenticated = isAuthenticated();
      console.log('User authenticated status:', isUserAuthenticated);
      
      try {
        // Create the learning plan
        const plan = await createLearningPlan(planRequest);
        console.log('Learning plan created with ID:', plan.id);
        
        // Store the plan ID in session storage for later use
        sessionStorage.setItem('pendingLearningPlanId', plan.id);
        setPlanId(plan.id);
        
        // Call the onPlanCreated callback if provided
        if (onPlanCreated) {
          onPlanCreated(plan.id);
        }
        
        // If user is already authenticated, we can immediately redirect to speech
        if (isUserAuthenticated) {
          console.log('User is authenticated, preparing direct navigation to speech page');
          // Set a short timeout to allow state updates to complete
          setTimeout(() => {
            // Clear any navigation flags
            sessionStorage.removeItem('navigationInProgress');
            sessionStorage.removeItem('redirectWithPlanId');
            
            // Navigate to speech page with the plan
            window.location.href = `/speech?plan=${plan.id}`;
          }, 100);
          return;
        }
        
        // Move to the authentication step
        setStep(4);
      } catch (planError: any) {
        console.error('Error creating learning plan:', planError);
        
        // Check if this is an authentication error
        if (planError.message?.includes('Not authenticated')) {
          // If user is not authenticated, show the authentication step
          setError('Please sign in to create a learning plan');
          setStep(4); // Go to authentication step
        } else {
          // For other errors, show a generic error message
          setError(`Failed to create learning plan: ${planError.message || 'Unknown error'}`); 
        }
      }
    } catch (error: any) {
      console.error('Unexpected error in handleCreatePlan:', error);
      setError('An unexpected error occurred. Please try again.');
    } finally {
      setIsCreatingPlan(false);
    }
  };
  
  const handleGoalToggle = (goalId: string, checked: boolean) => {
    if (checked) {
      setSelectedGoals([...selectedGoals, goalId]);
    } else {
      setSelectedGoals(selectedGoals.filter(id => id !== goalId));
    }
  };
  
  const handleSignIn = () => {
    // Store the plan ID in session storage before redirecting
    if (planId) {
      sessionStorage.setItem('pendingLearningPlanId', planId);
      console.log('Stored pendingLearningPlanId in session storage:', planId);
      
      // Store additional flag to indicate we should redirect to speech with this plan after login
      sessionStorage.setItem('redirectWithPlanId', planId);
    } else {
      console.warn('No plan ID available when redirecting to sign in');
    }
    
    // Store the intent to redirect to login page
    sessionStorage.setItem('redirectTarget', '/speech');
    
    // Clear any existing navigation flags that might interfere
    sessionStorage.removeItem('navigationInProgress');
    
    // Redirect to login page
    console.log('Redirecting to login page with pending plan:', planId);
    window.location.href = '/auth/login';
    onClose();
  };
  
  const handleSignUp = () => {
    if (!planId) {
      console.error('No plan ID available for sign up redirection');
      return;
    }
    
    console.log('Stored pendingLearningPlanId in session storage:', planId);
    sessionStorage.setItem('pendingLearningPlanId', planId);
    
    // Store additional flag to indicate we should redirect to speech with this plan after signup
    sessionStorage.setItem('redirectWithPlanId', planId);
    
    // Store the intent to redirect to signup page
    sessionStorage.setItem('redirectTarget', '/speech');
    
    // Clear any existing navigation flags that might interfere
    sessionStorage.removeItem('navigationInProgress');
    
    // Redirect to signup page
    console.log('Redirecting to signup page with pending plan:', planId);
    window.location.href = '/auth/signup';
    onClose();
  };
  
  const handleContinueWithoutSignIn = () => {
    if (!planId) {
      console.error('No plan ID available for continue without sign in');
      // Just redirect to speech page without a plan
      window.location.href = '/speech';
      return;
    }
    
    // Clear any pending plan ID since we're not going to assign it
    sessionStorage.removeItem('pendingLearningPlanId');
    
    // Clear any existing navigation flags that might interfere
    sessionStorage.removeItem('navigationInProgress');
    sessionStorage.removeItem('redirectWithPlanId');
    
    // Set the language and level in session storage for the speech page
    if (language) sessionStorage.setItem('selectedLanguage', language);
    if (proficiencyLevel) sessionStorage.setItem('selectedLevel', proficiencyLevel);
    
    // Redirect to speech page with the plan ID as a query parameter
    console.log('Continuing without sign in, redirecting to speech with plan:', planId);
    window.location.href = `/speech?plan=${planId}`;
    onClose();
  };
  
  // Group goals by category
  const goalsByCategory = goals.reduce((acc, goal) => {
    if (!acc[goal.category]) {
      acc[goal.category] = [];
    }
    acc[goal.category].push(goal);
    return acc;
  }, {} as Record<string, LearningGoal[]>);
  
  return (
    <Dialog open={isOpen} onOpenChange={(open: boolean) => !open && onClose()}>
      <DialogContent className="sm:max-w-[600px] p-0 rounded-xl shadow-xl bg-gradient-to-b from-purple-900 to-indigo-950 text-white border border-purple-400/20 overflow-hidden">
        {/* Step indicator */}
        {step < 4 && (
          <div className="w-full bg-black/20 px-6 pt-5 pb-3">
            <div className="flex justify-between items-center relative">
              {/* Progress bar background */}
              <div className="absolute h-1 bg-gray-700/50 top-4 left-4 right-4 z-0 rounded-full"></div>
              
              {/* Animated progress bar */}
              <div 
                className={`absolute h-1 bg-gradient-to-r from-purple-400 via-indigo-400 to-blue-400 top-4 left-4 z-10 rounded-full transition-all duration-500 ease-in-out`}
                style={{ width: `${Math.min((step - 1) * 45, 90)}%` }}
              ></div>
              
              {/* Step circles */}
              {[1, 2, 3].map((stepNumber) => (
                <div key={stepNumber} className="flex flex-col items-center z-20">
                  <div 
                    className={`w-9 h-9 rounded-full flex items-center justify-center mb-2 transition-all duration-300 transform
                    ${step >= stepNumber 
                      ? 'bg-gradient-to-r from-purple-400 to-indigo-500 text-white font-bold scale-110 shadow-lg shadow-purple-500/30' 
                      : 'bg-gray-800 text-gray-400 border border-gray-700'}`}
                  >
                    {stepNumber}
                  </div>
                  <div className="text-xs text-gray-400 font-medium">
                    {stepNumber === 1 ? 'Goals' : stepNumber === 2 ? 'Duration' : 'Review'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        <div className="px-6 pt-5 pb-6">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold text-center text-white mb-2">
              {step === 1 && 'Select Your Learning Goals'}
              {step === 2 && 'Choose Learning Duration'}
              {step === 3 && 'Review and Create Your Plan'}
              {step === 4 && 'Learning Plan Created!'}
            </DialogTitle>
            <DialogDescription className="text-blue-100 text-center text-base mb-6">
              {step === 1 && 'Choose the goals you want to achieve with your language learning.'}
              {step === 2 && 'How long do you plan to study this language?'}
              {step === 3 && 'Review your selections before creating your plan.'}
              {step === 4 && 'Your custom learning plan is ready to use!'}
            </DialogDescription>
          </DialogHeader>
        
        {/* Step 1: Goal Selection */}
        {step === 1 && (
          <div className="py-4 space-y-6">
            <ScrollArea className="h-[300px] pr-4">
              {/* Categorized Goals */}
              {Object.entries(goalsByCategory).map(([category, categoryGoals]) => (
                <div key={category} className="mb-6 bg-white/10 backdrop-blur-sm p-5 rounded-lg shadow-md border border-purple-300/20">
                  <h3 className="text-lg font-semibold mb-3 capitalize text-purple-200">{category}</h3>
                  <div className="space-y-3">
                    {categoryGoals.map((goal) => (
                      <div key={goal.id} className="flex items-center space-x-3 hover:bg-purple-500/10 p-2 rounded-md transition-colors">
                        <Checkbox
                          id={goal.id}
                          checked={selectedGoals.includes(goal.id)}
                          className="border-purple-300 data-[state=checked]:bg-purple-400 data-[state=checked]:text-purple-900"
                          onCheckedChange={(checked: boolean) => {
                            if (checked) {
                              setSelectedGoals([...selectedGoals, goal.id]);
                            } else {
                              setSelectedGoals(
                                selectedGoals.filter((id) => id !== goal.id)
                              );
                            }
                          }}
                        />
                        <Label htmlFor={goal.id} className="text-sm font-medium cursor-pointer text-white">{goal.text}</Label>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              {/* Custom Goal Input */}
              <div className="mt-6 bg-white/10 backdrop-blur-sm p-5 rounded-lg shadow-md border border-purple-300/20">
                <h3 className="text-lg font-semibold mb-3 text-purple-200">Custom Goal (Optional)</h3>
                <Input
                  placeholder="Enter your specific learning goal..."
                  value={customGoal}
                  onChange={(e) => setCustomGoal(e.target.value)}
                  className="w-full bg-white/20 border-purple-300/30 text-white placeholder:text-purple-200/60 focus:ring-purple-400 focus:border-purple-400"
                />
              </div>
            </ScrollArea>
          </div>
        )}
        
        {/* Step 2: Duration Selection */}
        {step === 2 && (
          <div className="py-4 space-y-6">
            <div className="bg-white/10 backdrop-blur-sm p-6 rounded-lg shadow-md border border-purple-300/20">
              <RadioGroup value={duration.toString()} onValueChange={(value: string) => {
                if (value === 'custom') {
                  setDuration(0);
                } else {
                  setDuration(parseInt(value));
                  setCustomDuration(null);
                }
              }} className="space-y-4 mt-2">
                {[1, 2, 3, 6, 12].map((months) => (
                  <div key={months} className="flex items-center space-x-3 hover:bg-blue-500/10 p-3 rounded-md transition-colors">
                    <RadioGroupItem 
                      value={months.toString()} 
                      id={`duration-${months}`} 
                      className="border-purple-300 text-purple-400"
                    />
                    <Label 
                      htmlFor={`duration-${months}`} 
                      className="font-medium cursor-pointer text-white"
                    >
                      {months} month{months !== 1 ? 's' : ''}
                    </Label>
                  </div>
                ))}
                <div className="flex items-center space-x-3 hover:bg-purple-500/10 p-3 rounded-md transition-colors">
                  <RadioGroupItem 
                    value="custom" 
                    id="duration-custom" 
                    className="border-blue-300 text-blue-400"
                  />
                  <Label htmlFor="duration-custom" className="font-medium cursor-pointer text-white">Custom duration</Label>
                </div>
              </RadioGroup>
              
              {duration === 0 && (
                <div className="mt-6 bg-purple-500/10 p-4 rounded-lg border border-purple-300/30">
                  <Label htmlFor="custom-duration" className="block mb-2 font-medium text-purple-200">Enter number of months:</Label>
                  <Input
                    id="custom-duration"
                    type="number"
                    min="1"
                    max="36"
                    value={customDuration || ''}
                    onChange={(e) => setCustomDuration(parseInt(e.target.value) || null)}
                    className="w-full bg-white/20 border-purple-300/30 text-white placeholder:text-purple-200/60 focus:ring-purple-400 focus:border-purple-400"
                  />
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* Step 3: Review and Create */}
        {step === 3 && (
          <div className="py-4">
            <div className="space-y-4 mb-6 bg-white/10 backdrop-blur-sm p-6 rounded-lg shadow-md border border-purple-300/20">
              <div className="bg-purple-500/10 p-4 rounded-md border border-purple-300/20">
                <h3 className="font-semibold text-purple-200">Language</h3>
                <p className="text-white mt-1 capitalize">{language}</p>
              </div>
              
              <div className="bg-purple-500/10 p-4 rounded-md border border-purple-300/20">
                <h3 className="font-semibold text-purple-200">Proficiency Level</h3>
                <p className="text-white mt-1 capitalize">{proficiencyLevel}</p>
              </div>
              
              <div className="bg-purple-500/10 p-4 rounded-md border border-purple-300/20">
                <h3 className="font-semibold text-purple-200">Selected Goals</h3>
                <ul className="text-white list-disc list-inside mt-2 space-y-2">
                  {selectedGoals.map((goalId) => {
                    const goal = goals.find(g => g.id === goalId);
                    return goal ? <li key={goalId}>{goal.text}</li> : null;
                  })}
                  {customGoal && <li className="font-medium">Custom: {customGoal}</li>}
                </ul>
              </div>
              
              <div className="bg-purple-500/10 p-4 rounded-md border border-purple-300/20">
                <h3 className="font-semibold text-purple-200">Duration</h3>
                <p className="text-white mt-1">
                  {customDuration || duration} month{(customDuration || duration) !== 1 ? 's' : ''}
                </p>
              </div>
            </div>
            
            {isCreatingPlan && (
              <div className="mt-6 flex flex-col items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-t-2 border-purple-400 mb-3"></div>
                <p className="text-purple-300 text-sm font-medium">Creating your personalized learning plan...</p>
              </div>
            )}
          </div>
        )}
        
        {/* Step 4: Plan Created */}
        {step === 4 && (
          <div className="py-6">
            <div className="text-center mb-8">
              <div className="mx-auto w-24 h-24 bg-gradient-to-br from-purple-400/30 to-indigo-600/30 rounded-full flex items-center justify-center mb-5 shadow-lg border border-purple-400/50 animate-[pulse_3s_ease-in-out_infinite]">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-purple-300">Your Learning Plan is Ready!</h3>
              <p className="text-base text-blue-100 mt-3 max-w-md mx-auto">
                Sign in or create an account to save your custom learning plan and start your language journey.
              </p>
            </div>
            
            <div className="space-y-4">
              <Button 
                className="w-full bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 text-white font-medium py-4 rounded-lg shadow-md transition-all hover:shadow-xl transform hover:-translate-y-1"
                onClick={handleSignIn}
              >
                <span className="flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                  </svg>
                  Sign In
                </span>
              </Button>
              
              <Button 
                className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-medium py-4 rounded-lg shadow-md transition-all hover:shadow-xl transform hover:-translate-y-1"
                onClick={handleSignUp}
              >
                <span className="flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                  </svg>
                  Create Account
                </span>
              </Button>
              
              <Button 
                className="w-full bg-white/10 hover:bg-white/20 text-white font-medium py-4 rounded-lg transition-all border border-white/20 backdrop-blur-sm hover:shadow-lg"
                onClick={handleContinueWithoutSignIn}
              >
                Continue Without Signing In
              </Button>
            </div>
          </div>
        )}
        
        {error && (
          <div className="bg-red-500/20 border border-red-500/30 text-white px-4 py-3 rounded-md my-4 flex items-start">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 mt-0.5 flex-shrink-0 text-red-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{error}</span>
          </div>
        )}
        
        {step < 4 && (
          <DialogFooter className="flex justify-between mt-6 pt-4 border-t border-purple-400/30">
            <Button 
              variant="outline" 
              onClick={handlePrevStep}
              disabled={isCreatingPlan}
              className="border-purple-300/30 bg-purple-600/20 hover:bg-purple-600/30 text-white transition-all hover:shadow-md px-4 py-2"
            >
              <span className="flex items-center">
                {step > 1 && (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                )}
                {step === 1 ? 'Cancel' : 'Back'}
              </span>
            </Button>
            
            <Button 
              onClick={handleNextStep}
              disabled={isCreatingPlan}
              className="bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 text-white shadow-md hover:shadow-lg transition-all transform hover:-translate-y-1 px-5 py-2"
            >
              <span className="flex items-center">
                {step === 3 ? 'Create Plan' : 'Next'}
                {step < 3 && (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                )}
              </span>
            </Button>
          </DialogFooter>
        )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
