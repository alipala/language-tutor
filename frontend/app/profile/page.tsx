'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/auth';
import ProtectedRoute from '@/components/protected-route';
import NavBar from '@/components/nav-bar';
import { getUserLearningPlans, LearningPlan } from '@/lib/learning-api';
import { getApiUrl } from '@/lib/api-utils';
import { Progress } from '@/components/ui/progress';
import { SpeakingAssessmentResult } from '@/lib/speaking-assessment-api';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';

// API base URL
// In Railway deployment, the API is served from the same domain
// Using getApiUrl() to ensure consistent API URL configuration across the application
const API_URL = getApiUrl(); // This will use port 8000 as defined in api-utils.ts

export default function ProfilePage() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [preferredLanguage, setPreferredLanguage] = useState('');
  const [preferredLevel, setPreferredLevel] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [learningPlans, setLearningPlans] = useState<LearningPlan[]>([]);
  const [plansLoading, setPlansLoading] = useState(true);
  const [plansError, setPlansError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('profile');
  
  // Get the assessment data either from the user's last_assessment_data or from the most recent learning plan
  const latestAssessment = user?.last_assessment_data || 
    (learningPlans.length > 0 && learningPlans[0].assessment_data 
      ? learningPlans[0].assessment_data 
      : null);
    
  // Helper function to get color class based on score
  const getColorClass = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-blue-500';
    if (score >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  // Load user data when component mounts
  useEffect(() => {
    if (user) {
      setName(user.name);
      setEmail(user.email);
      setPreferredLanguage(user.preferred_language || '');
      setPreferredLevel(user.preferred_level || '');
      
      // Fetch user's learning plans
      fetchUserLearningPlans();
    }
  }, [user]);
  
  // Fetch user's learning plans
  const fetchUserLearningPlans = async () => {
    if (!user) return;
    
    setPlansLoading(true);
    setPlansError(null);
    
    try {
      const plans = await getUserLearningPlans();
      setLearningPlans(plans);
    } catch (err: any) {
      console.error('Error fetching learning plans:', err);
      setPlansError(err.message || 'Failed to load learning plans');
    } finally {
      setPlansLoading(false);
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setIsSaved(false);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`${API_URL}/auth/update-profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name,
          preferred_language: preferredLanguage,
          preferred_level: preferredLevel
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update profile');
      }

      // Update session storage with new preferences
      if (preferredLanguage) {
        sessionStorage.setItem('selectedLanguage', preferredLanguage);
      }
      
      if (preferredLevel) {
        sessionStorage.setItem('selectedLevel', preferredLevel);
      }

      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 3000);
    } catch (err: any) {
      console.error('Profile update error:', err);
      setError(err.message || 'Failed to update profile. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-slate-900">
        <NavBar />
        
        {/* Main content */}
        <main className="flex-grow container mx-auto p-4 md:p-6">
          <div className="max-w-4xl mx-auto px-4 py-8 md:px-6">
            {/* Assessment Dashboard */}
            {latestAssessment && (
              <div className="mb-8 bg-white dark:bg-slate-800/90 border border-gray-200 dark:border-gray-700 rounded-xl shadow-md overflow-hidden">
                <div className="bg-gradient-to-r from-purple-500 to-indigo-600 dark:from-purple-600 dark:to-indigo-700 p-4 text-white relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
                  <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/10 rounded-full -ml-12 -mb-12"></div>
                  
                  <div className="relative z-10 flex justify-between items-center">
                    <div>
                      <h2 className="text-xl font-bold">Your Assessment Results</h2>
                      <p className="text-white/80 text-sm mt-1">Detailed analysis of your speaking skills</p>
                    </div>
                    <div className="flex items-center bg-white/20 rounded-full px-3 py-1.5">
                      <span className="text-sm font-medium mr-1">Recommended Level:</span>
                      <span className="text-sm font-bold bg-white/30 px-2 py-0.5 rounded-full">
                        {latestAssessment.recommended_level || "B1"}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="p-5">
                  {/* Overall Score and Confidence */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div className="bg-indigo-50/50 dark:bg-indigo-900/10 p-4 rounded-xl">
                      <div className="flex justify-between items-center mb-2">
                        <h3 className="text-base font-semibold text-slate-700 dark:text-slate-300 flex items-center">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1.5 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                          </svg>
                          Overall Score
                        </h3>
                        <span className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
                          {latestAssessment.overall_score}/100
                        </span>
                      </div>
                      <div className="h-3 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden mb-2">
                        <div 
                          className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                          style={{ width: `${latestAssessment.overall_score}%` }}
                        ></div>
                      </div>
                      <div className="text-sm text-slate-600 dark:text-slate-400 italic">
                        {latestAssessment.overall_score >= 80 ? "Excellent" : 
                         latestAssessment.overall_score >= 70 ? "Very Good" :
                         latestAssessment.overall_score >= 60 ? "Good" :
                         latestAssessment.overall_score >= 50 ? "Fair" : "Needs Improvement"}
                      </div>
                    </div>
                    
                    <div className="bg-green-50/50 dark:bg-green-900/10 p-4 rounded-xl">
                      <div className="flex justify-between items-center mb-2">
                        <h3 className="text-base font-semibold text-slate-700 dark:text-slate-300 flex items-center">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1.5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Confidence
                        </h3>
                        <span className="text-3xl font-bold text-green-600 dark:text-green-400">
                          {latestAssessment.confidence}%
                        </span>
                      </div>
                      <div className="h-3 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden mb-2">
                        <div 
                          className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full"
                          style={{ width: `${latestAssessment.confidence}%` }}
                        ></div>
                      </div>
                      <div className="text-sm text-slate-600 dark:text-slate-400 italic">
                        {latestAssessment.confidence >= 80 ? "Very Confident" : 
                         latestAssessment.confidence >= 60 ? "Confident" :
                         latestAssessment.confidence >= 40 ? "Moderately Confident" : "Needs Confidence Building"}
                      </div>
                    </div>
                  </div>
                  
                  {/* Skill Breakdown */}
                  <div className="mb-6">
                    <h3 className="text-base font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1.5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                      </svg>
                      Skill Breakdown
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                      {['pronunciation', 'grammar', 'vocabulary', 'fluency', 'coherence'].map((skill) => {
                        // Type assertion to access dynamic properties safely
                        const skillData = latestAssessment ? 
                          (latestAssessment as any)[skill] : { score: 0, feedback: '' };
                        
                        return (
                          <div key={skill} className="bg-white dark:bg-slate-800/90 border border-gray-200 dark:border-gray-700 rounded-lg p-3 shadow-sm">
                            <div className="flex justify-between items-center mb-1">
                              <div className="text-sm font-medium capitalize text-slate-700 dark:text-slate-300">{skill}</div>
                              <div className="text-lg font-bold text-blue-600 dark:text-blue-400">
                                {skillData.score}
                              </div>
                            </div>
                            <div className="h-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden mb-2">
                              <div 
                                className={`h-full ${getColorClass(skillData.score)} rounded-full`}
                                style={{ width: `${skillData.score}%` }}
                              ></div>
                            </div>
                            <div className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2 h-8" title={skillData.feedback}>
                              {skillData.feedback}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                  
                  {/* Strengths and Areas for Improvement */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div className="bg-green-50/50 dark:bg-green-900/10 p-4 rounded-xl">
                      <h3 className="text-base font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1.5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        Strengths
                      </h3>
                      <ul className="space-y-2">
                        {latestAssessment.strengths?.map((strength: string, index: number) => (
                          <li key={index} className="flex items-start">
                            <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-xs mr-2 mt-0.5 flex-shrink-0">
                              {index + 1}
                            </span>
                            <span className="text-sm text-slate-700 dark:text-slate-300">{strength}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    
                    <div className="bg-amber-50/50 dark:bg-amber-900/10 p-4 rounded-xl">
                      <h3 className="text-base font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1.5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        Areas to Improve
                      </h3>
                      <ul className="space-y-2">
                        {latestAssessment.areas_for_improvement?.map((area: string, index: number) => (
                          <li key={index} className="flex items-start">
                            <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 text-xs mr-2 mt-0.5 flex-shrink-0">
                              {index + 1}
                            </span>
                            <span className="text-sm text-slate-700 dark:text-slate-300">{area}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                  
                  {/* Next Steps */}
                  <div className="bg-blue-50/50 dark:bg-blue-900/10 p-4 rounded-xl">
                    <h3 className="text-base font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1.5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                      </svg>
                      Recommended Next Steps
                    </h3>
                    <ul className="space-y-2">
                      {latestAssessment.next_steps?.map((step: string, index: number) => (
                        <li key={index} className="flex items-start">
                          <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs mr-2 mt-0.5 flex-shrink-0">
                            {index + 1}
                          </span>
                          <span className="text-sm text-slate-700 dark:text-slate-300">{step}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  {/* Recognized Text */}
                  {latestAssessment.recognized_text && (
                    <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                      <h3 className="text-base font-semibold text-slate-700 dark:text-slate-300 mb-2 flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1.5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                        </svg>
                        Your Speech Sample
                      </h3>
                      <div className="bg-slate-50 dark:bg-slate-800/50 p-3 rounded-lg border border-slate-200 dark:border-slate-700 text-sm text-slate-600 dark:text-slate-400 italic">
                        "{latestAssessment.recognized_text}"
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
            
            {/* Learning Progress Summary */}
            {learningPlans.length > 0 && (
              <div className="mb-8 bg-white dark:bg-slate-800/90 border border-gray-200 dark:border-gray-700 rounded-xl shadow-md overflow-hidden">
                <div className="bg-gradient-to-r from-blue-500 to-indigo-600 dark:from-blue-600 dark:to-indigo-700 p-4 text-white relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
                  <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/10 rounded-full -ml-12 -mb-12"></div>
                  
                  <div className="relative z-10">
                    <h2 className="text-xl font-bold">Your Language Learning Journey</h2>
                    <p className="text-white/80 text-sm mt-1">Track your progress and achievements</p>
                  </div>
                </div>
                
                <div className="p-5">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                      <div className="flex items-center mb-2">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        <h3 className="font-semibold text-slate-700 dark:text-slate-300">Active Plans</h3>
                      </div>
                      <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{learningPlans.length}</div>
                    </div>
                    
                    <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
                      <div className="flex items-center mb-2">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-purple-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                        </svg>
                        <h3 className="font-semibold text-slate-700 dark:text-slate-300">Languages</h3>
                      </div>
                      <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                        {new Set(learningPlans.map(plan => plan.language)).size}
                      </div>
                    </div>
                    
                    <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                      <div className="flex items-center mb-2">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <h3 className="font-semibold text-slate-700 dark:text-slate-300">Assessments</h3>
                      </div>
                      <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                        {learningPlans.filter(plan => plan.assessment_data).length}
                      </div>
                    </div>
                  </div>
                  
                  {latestAssessment && (
                    <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                      <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">Latest Assessment Overview</h3>
                      <div className="grid grid-cols-5 gap-2">
                        {['pronunciation', 'grammar', 'vocabulary', 'fluency', 'coherence'].map((skill) => {
                          // Type assertion to access dynamic properties safely
                          const skillData = latestAssessment ? 
                            (latestAssessment as any)[skill] : { score: 0, feedback: '' };
                          
                          return (
                            <div key={skill} className="text-center">
                              <div className="text-xs capitalize mb-1 text-slate-600 dark:text-slate-400">{skill}</div>
                              <div className="h-1.5 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                <div 
                                  className={`h-full ${getColorClass(skillData.score)} rounded-full`}
                                  style={{ width: `${skillData.score}%` }}
                                ></div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
            
            {/* User Profile Section */}
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md overflow-hidden mb-8">
              <div className="bg-gradient-to-r from-indigo-500 to-purple-600 dark:from-indigo-600 dark:to-purple-700 p-4 text-white relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
                <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/10 rounded-full -ml-12 -mb-12"></div>
                
                <div className="relative z-10">
                  <h2 className="text-xl font-bold">Your Profile</h2>
                  <p className="text-white/80 text-sm mt-1">Update your personal information and preferences</p>
                </div>
              </div>
              
              <div className="p-6">
                {error && (
                  <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400 text-sm flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {error}
                  </div>
                )}
                
                <form onSubmit={handleSaveProfile} className="space-y-5">
                  <div>
                    <label htmlFor="name" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Name
                    </label>
                    <Input
                      id="name"
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full"
                      placeholder="Your name"
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Email
                    </label>
                    <Input
                      id="email"
                      type="email"
                      value={email}
                      disabled
                      className="w-full bg-gray-50 dark:bg-slate-700/50 cursor-not-allowed"
                    />
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                      Email cannot be changed
                    </p>
                  </div>
                  
                  <div>
                    <label htmlFor="preferredLanguage" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Preferred Language
                    </label>
                    <Input
                      id="preferredLanguage"
                      type="text"
                      value={preferredLanguage}
                      onChange={(e) => setPreferredLanguage(e.target.value)}
                      className="w-full"
                      placeholder="e.g. Spanish, French, German"
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="preferredLevel" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Proficiency Level
                    </label>
                    <Input
                      id="preferredLevel"
                      type="text"
                      value={preferredLevel}
                      onChange={(e) => setPreferredLevel(e.target.value)}
                      className="w-full"
                      placeholder="e.g. Beginner, Intermediate, Advanced"
                    />
                  </div>
                  
                  <div className="pt-2">
                    <Button 
                      type="submit" 
                      className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white py-2 rounded-lg shadow-md hover:shadow-lg transition-all flex items-center justify-center"
                      disabled={isLoading}
                    >
                      {isLoading ? (
                        <>
                          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Saving...
                        </>
                      ) : isSaved ? (
                        <>
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          Saved!
                        </>
                      ) : 'Save Profile'}
                    </Button>
                  </div>
                </form>
              </div>
            </div>
            
            {/* Learning Plans Section */}
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md overflow-hidden mb-8">
              <div className="bg-gradient-to-r from-indigo-500 to-purple-600 dark:from-indigo-600 dark:to-purple-700 p-4 text-white relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
                <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/10 rounded-full -ml-12 -mb-12"></div>
                
                <div className="flex justify-between items-center relative z-10">
                  <div>
                    <h2 className="text-xl font-bold">Your Learning Plans</h2>
                    <p className="text-white/80 text-sm mt-1">Track your language learning progress</p>
                  </div>
                  
                  <Button 
                    onClick={() => router.push('/language-selection')}
                    className="bg-white/20 hover:bg-white/30 text-white text-sm py-1 px-3 rounded-full transition-all"
                  >
                    Create New Plan
                  </Button>
                </div>
              </div>
              
              <div className="p-6">
                {plansLoading ? (
                  <div className="p-8 flex justify-center items-center">
                    <div className="animate-spin h-8 w-8 border-4 border-indigo-500 border-t-transparent rounded-full"></div>
                  </div>
                ) : plansError ? (
                  <div className="p-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-red-600 dark:text-red-400 text-sm flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {plansError}
                  </div>
                ) : learningPlans.length === 0 ? (
                  <div className="p-8 bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-xl text-center">
                    <div className="w-16 h-16 mx-auto mb-4 bg-indigo-100 dark:bg-indigo-900/30 rounded-full flex items-center justify-center">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-indigo-500 dark:text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                      </svg>
                    </div>
                    <h4 className="text-lg font-medium text-slate-700 dark:text-slate-300 mb-2">No Learning Plans Yet</h4>
                    <p className="text-slate-600 dark:text-slate-400 mb-4">Start your language learning journey by creating your first plan.</p>
                    <Button 
                      onClick={() => router.push('/language-selection')}
                      className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white py-2 px-6 rounded-lg shadow-md hover:shadow-lg transition-all"
                    >
                      Create Your First Plan
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {learningPlans.map((plan) => (
                      <div key={plan.id} className="bg-white dark:bg-slate-800/90 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden">
                        {/* Plan Header with Gradient */}
                        <div className="bg-gradient-to-r from-indigo-500/80 to-purple-600/80 dark:from-indigo-600/80 dark:to-purple-700/80 p-4 text-white relative overflow-hidden">
                          <div className="flex justify-between items-start relative z-10">
                            <div>
                              <h4 className="text-lg font-bold capitalize flex items-center">
                                {plan.language} - {plan.proficiency_level}
                                {plan.assessment_data && (
                                  <span className="ml-2 bg-white/20 text-xs px-2 py-0.5 rounded-full">
                                    Assessed
                                  </span>
                                )}
                              </h4>
                              <p className="text-white/80 text-sm mt-1">
                                Created {new Date(plan.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}
                              </p>
                            </div>
                            <div className="flex items-center bg-white/20 rounded-lg px-3 py-1.5">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                              <span className="text-sm">{plan.duration_months} months</span>
                            </div>
                          </div>
                        </div>
                        
                        <div className="p-5">
                          {/* Learning Goals */}
                          <div className="mb-4">
                            <h5 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2 flex items-center">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                              </svg>
                              Learning Goals
                            </h5>
                            <div className="flex flex-wrap gap-2">
                              {plan.goals.map((goal, index) => (
                                <span key={index} className="text-xs bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 px-3 py-1.5 rounded-full capitalize">
                                  {goal}
                                </span>
                              ))}
                              {plan.custom_goal && (
                                <span className="text-xs bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 px-3 py-1.5 rounded-full">
                                  {plan.custom_goal}
                                </span>
                              )}
                            </div>
                          </div>
                          
                          {/* Speaking Assessment Data */}
                          {plan.assessment_data && (
                            <div className="mb-4 p-4 bg-indigo-50/50 dark:bg-indigo-900/10 rounded-xl">
                              <h5 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                </svg>
                                Speaking Assessment Results
                              </h5>
                              
                              {/* Overall Score and Confidence */}
                              <div className="grid grid-cols-2 gap-4 mb-4">
                                <div className="bg-white dark:bg-slate-800 p-3 rounded-lg shadow-sm">
                                  <div className="flex justify-between items-center text-xs mb-2">
                                    <span className="text-slate-600 dark:text-slate-400 font-medium">Overall Score</span>
                                    <span className="font-bold text-indigo-600 dark:text-indigo-400">
                                      {plan.assessment_data.overall_score}/100
                                    </span>
                                  </div>
                                  <div className="h-2.5 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                    <div 
                                      className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                                      style={{ width: `${plan.assessment_data.overall_score}%` }}
                                    ></div>
                                  </div>
                                </div>
                                
                                <div className="bg-white dark:bg-slate-800 p-3 rounded-lg shadow-sm">
                                  <div className="flex justify-between items-center text-xs mb-2">
                                    <span className="text-slate-600 dark:text-slate-400 font-medium">Confidence</span>
                                    <span className="font-bold text-green-600 dark:text-green-400">
                                      {plan.assessment_data.confidence}%
                                    </span>
                                  </div>
                                  <div className="h-2.5 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                    <div 
                                      className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full"
                                      style={{ width: `${plan.assessment_data.confidence}%` }}
                                    ></div>
                                  </div>
                                </div>
                              </div>
                              
                              {/* Skill Breakdown */}
                              <div className="grid grid-cols-5 gap-2 mb-3">
                                {['pronunciation', 'grammar', 'vocabulary', 'fluency', 'coherence'].map((skill) => {
                                  // Type assertion to access dynamic properties safely
                                  const skillData = plan.assessment_data ? 
                                    (plan.assessment_data as any)[skill] : { score: 0, feedback: '' };
                                  
                                  // Define color based on score
                                  const getColorClass = (score: number) => {
                                    if (score >= 80) return 'bg-green-500';
                                    if (score >= 60) return 'bg-blue-500';
                                    if (score >= 40) return 'bg-yellow-500';
                                    return 'bg-red-500';
                                  };
                                  
                                  return (
                                    <div key={skill} className="text-center p-2 bg-white dark:bg-slate-800 rounded-lg shadow-sm flex flex-col items-center">
                                      <div className="text-xs capitalize mb-1 text-slate-600 dark:text-slate-400">{skill}</div>
                                      <div className="font-bold text-sm">
                                        {skillData.score.toFixed(0)}
                                      </div>
                                      <div className="h-1.5 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden mt-1">
                                        <div 
                                          className={`h-full ${getColorClass(skillData.score)} rounded-full`}
                                          style={{ width: `${skillData.score}%` }}
                                        ></div>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                              
                              {/* Strengths and Areas for Improvement */}
                              <div className="grid grid-cols-2 gap-3 mt-3">
                                <div>
                                  <h6 className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1.5">Strengths</h6>
                                  {plan.assessment_data?.strengths?.slice(0, 2).map((strength: string, index: number) => (
                                    <div key={index} className="text-xs bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 px-2.5 py-1.5 rounded-md mb-1.5 flex items-start">
                                      <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5 mr-1.5 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                      </svg>
                                      <span>{strength}</span>
                                    </div>
                                  ))}
                                </div>
                                
                                <div>
                                  <h6 className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1.5">Areas to Improve</h6>
                                  {plan.assessment_data?.areas_for_improvement?.slice(0, 2).map((area: string, index: number) => (
                                    <div key={index} className="text-xs bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-300 px-2.5 py-1.5 rounded-md mb-1.5 flex items-start">
                                      <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5 mr-1.5 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                      </svg>
                                      <span>{area}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>
                          )}
                          
                          {/* Continue Learning Button */}
                          <Button 
                            onClick={() => router.push(`/speech?plan=${plan.id}`)}
                            className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-medium py-3 rounded-lg shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Continue Learning
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            
            {/* Account Actions Section */}
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md overflow-hidden mb-8">
              <div className="bg-gradient-to-r from-red-500 to-orange-600 dark:from-red-600 dark:to-orange-700 p-4 text-white relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
                <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/10 rounded-full -ml-12 -mb-12"></div>
                
                <div className="relative z-10">
                  <h2 className="text-xl font-bold">Account Actions</h2>
                  <p className="text-white/80 text-sm mt-1">Manage your account settings</p>
                </div>
              </div>
              
              <div className="p-6">
                <button
                  onClick={handleLogout}
                  className="w-full py-3 px-4 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 dark:border-red-700 dark:text-red-400 dark:hover:bg-red-900/20 font-medium transition-all flex items-center justify-center gap-2"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  Sign Out
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
