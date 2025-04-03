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
    }
    
    console.log('Stored pendingLearningPlanId in session storage:', planId);
    
    // Store additional flag to indicate we should redirect to speech with this plan after login
    sessionStorage.setItem('redirectWithPlanId', planId);
    
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
      <DialogContent className="sm:max-w-[600px] p-6 rounded-xl shadow-lg dark:bg-slate-900 dark:text-white bg-gradient-to-b from-blue-50 to-white border-blue-200">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-center text-blue-800 dark:text-blue-300 mb-2">
            {step === 1 && 'Select Your Learning Goals'}
            {step === 2 && 'Choose Learning Duration'}
            {step === 3 && 'Review and Create Your Plan'}
            {step === 4 && 'Learning Plan Created!'}
          </DialogTitle>
          <DialogDescription className="text-gray-600 dark:text-gray-300 text-center text-base mb-4">
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
                <div key={category} className="mb-6 bg-white dark:bg-slate-800 p-4 rounded-lg shadow-sm border border-blue-100 dark:border-slate-700">
                  <h3 className="text-lg font-medium mb-3 capitalize text-blue-700 dark:text-blue-300">{category}</h3>
                  <div className="space-y-3">
                    {categoryGoals.map((goal) => (
                      <div key={goal.id} className="flex items-center space-x-3 hover:bg-blue-50 dark:hover:bg-slate-700 p-2 rounded-md transition-colors">
                        <Checkbox
                          id={goal.id}
                          checked={selectedGoals.includes(goal.id)}
                          className="border-blue-400 data-[state=checked]:bg-blue-600 data-[state=checked]:text-white"
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
                        <Label htmlFor={goal.id} className="text-sm font-medium cursor-pointer">{goal.text}</Label>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              {/* Custom Goal Input */}
              <div className="mt-6 bg-white dark:bg-slate-800 p-4 rounded-lg shadow-sm border border-blue-100 dark:border-slate-700">
                <h3 className="text-lg font-medium mb-3 text-blue-700 dark:text-blue-300">Custom Goal (Optional)</h3>
                <Input
                  placeholder="Enter your specific learning goal..."
                  value={customGoal}
                  onChange={(e) => setCustomGoal(e.target.value)}
                  className="w-full border-blue-200 dark:border-slate-600 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </ScrollArea>
          </div>
        )}
        
        {/* Step 2: Duration Selection */}
        {step === 2 && (
          <div className="py-4 space-y-6 bg-white dark:bg-slate-800 p-6 rounded-lg shadow-sm border border-blue-100 dark:border-slate-700">
            <RadioGroup value={duration.toString()} onValueChange={(value: string) => {
              if (value === 'custom') {
                setDuration(0);
              } else {
                setDuration(parseInt(value));
                setCustomDuration(null);
              }
            }} className="space-y-4 mt-4">
              <div className="flex items-center space-x-2 mb-3">
                <RadioGroupItem value="1" id="duration-1" />
                <Label htmlFor="duration-1">1 month</Label>
              </div>
              <div className="flex items-center space-x-3 hover:bg-blue-50 dark:hover:bg-slate-700 p-2 rounded-md transition-colors">
                <RadioGroupItem 
                  value="2" 
                  id="duration-2" 
                  className="border-blue-400 text-blue-600"
                />
                <Label htmlFor="duration-2" className="font-medium cursor-pointer">2 months</Label>
              </div>
              <div className="flex items-center space-x-2 mb-3">
                <RadioGroupItem value="3" id="duration-3" />
                <Label htmlFor="duration-3">3 months</Label>
              </div>
              <div className="flex items-center space-x-3 hover:bg-blue-50 dark:hover:bg-slate-700 p-2 rounded-md transition-colors">
                <RadioGroupItem 
                  value="6" 
                  id="duration-6" 
                  className="border-blue-400 text-blue-600"
                />
                <Label htmlFor="duration-6" className="font-medium cursor-pointer">6 months</Label>
              </div>
              <div className="flex items-center space-x-2 mb-3">
                <RadioGroupItem value="12" id="duration-12" />
                <Label htmlFor="duration-12">12 months</Label>
              </div>
              <div className="flex items-center space-x-3 hover:bg-blue-50 dark:hover:bg-slate-700 p-2 rounded-md transition-colors">
                <RadioGroupItem 
                  value="custom" 
                  id="duration-custom" 
                  className="border-blue-400 text-blue-600"
                />
                <Label htmlFor="duration-custom" className="font-medium cursor-pointer">Custom duration</Label>
              </div>
            </RadioGroup>
            
            {duration === 0 && (
              <div className="mt-6 bg-blue-50 dark:bg-slate-700 p-4 rounded-lg">
                <Label htmlFor="custom-duration" className="block mb-2 font-medium">Enter number of months:</Label>
                <Input
                  id="custom-duration"
                  type="number"
                  min="1"
                  max="36"
                  value={customDuration || ''}
                  onChange={(e) => setCustomDuration(parseInt(e.target.value) || null)}
                  className="w-full border-blue-300 dark:border-slate-600 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            )}
          </div>
        )}
        
        {/* Step 3: Review and Create */}
        {step === 3 && (
          <div className="py-4">
            <div className="space-y-6 mb-6 bg-white dark:bg-slate-800 p-6 rounded-lg shadow-sm border border-blue-100 dark:border-slate-700">
              <div className="bg-blue-50 dark:bg-slate-700 p-3 rounded-md">
                <h3 className="font-medium text-blue-700 dark:text-blue-300">Language</h3>
                <p className="text-sm text-gray-700 dark:text-gray-300 mt-1 capitalize">{language}</p>
              </div>
              
              <div className="bg-blue-50 dark:bg-slate-700 p-3 rounded-md">
                <h3 className="font-medium text-blue-700 dark:text-blue-300">Proficiency Level</h3>
                <p className="text-sm text-gray-700 dark:text-gray-300 mt-1 capitalize">{proficiencyLevel}</p>
              </div>
              
              <div className="bg-blue-50 dark:bg-slate-700 p-3 rounded-md">
                <h3 className="font-medium text-blue-700 dark:text-blue-300">Selected Goals</h3>
                <ul className="text-sm text-gray-700 dark:text-gray-300 list-disc list-inside mt-2 space-y-1">
                  {selectedGoals.map((goalId) => {
                    const goal = goals.find(g => g.id === goalId);
                    return goal ? <li key={goalId}>{goal.text}</li> : null;
                  })}
                  {customGoal && <li className="font-medium">Custom: {customGoal}</li>}
                </ul>
              </div>
              
              <div className="bg-blue-50 dark:bg-slate-700 p-3 rounded-md">
                <h3 className="font-medium text-blue-700 dark:text-blue-300">Duration</h3>
                <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">
                  {customDuration || duration} month{(customDuration || duration) !== 1 ? 's' : ''}
                </p>
              </div>
            </div>
            
            {isCreatingPlan && (
              <div className="mt-6 flex flex-col items-center justify-center">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-t-2 border-blue-600 mb-3"></div>
                <p className="text-blue-600 dark:text-blue-400 text-sm font-medium">Creating your personalized learning plan...</p>
              </div>
            )}
          </div>
        )}
        
        {/* Step 4: Plan Created */}
        {step === 4 && (
          <div className="py-6">
            <div className="text-center mb-8">
              <div className="mx-auto w-20 h-20 bg-gradient-to-br from-green-100 to-green-200 dark:from-green-800 dark:to-green-900 rounded-full flex items-center justify-center mb-5 shadow-md">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-green-600 dark:text-green-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-green-700 dark:text-green-400">Your Learning Plan is Ready!</h3>
              <p className="text-base text-gray-600 dark:text-gray-300 mt-3 max-w-md mx-auto">
                Sign in or create an account to save your custom learning plan and start your language journey.
              </p>
            </div>
            
            <div className="space-y-4">
              <Button 
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-5 rounded-lg shadow-md transition-all hover:shadow-lg"
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
                className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-5 rounded-lg shadow-md transition-all hover:shadow-lg"
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
                className="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-white font-medium py-4 rounded-lg transition-all"
                onClick={handleContinueWithoutSignIn}
              >
                Continue Without Signing In
              </Button>
            </div>
          </div>
        )}
        
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md dark:bg-red-900/50 dark:border-red-800 dark:text-red-300 my-4 flex items-start">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{error}</span>
          </div>
        )}
        
        {step < 4 && (
          <DialogFooter className="flex justify-between mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
            <Button 
              variant="outline" 
              onClick={handlePrevStep}
              disabled={isCreatingPlan}
              className="border-gray-300 hover:bg-gray-100 dark:border-gray-600 dark:hover:bg-gray-800 transition-colors"
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
              className="bg-blue-600 hover:bg-blue-700 text-white shadow-md hover:shadow-lg transition-all"
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
      </DialogContent>
    </Dialog>
  );
}
