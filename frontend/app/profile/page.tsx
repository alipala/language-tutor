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

  const handleLogout = () => {
    logout();
    // Use direct window.location.href for reliable navigation in Railway
    const fullUrl = `${window.location.origin}/`;
    window.location.href = fullUrl;
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen flex flex-col app-background">
        <NavBar />

        {/* Main content */}
        <main className="flex-grow container mx-auto p-4 md:p-6">
          <div className="max-w-2xl mx-auto bg-white dark:bg-slate-800 rounded-lg shadow-lg overflow-hidden">
            <div className="p-6 md:p-8">
              <h2 className="text-2xl font-bold mb-6 text-slate-900 dark:text-white">Your Profile</h2>
              
              {error && (
                <div className="mb-6 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">
                  {error}
                </div>
              )}
              
              {isSaved && (
                <div className="mb-6 p-3 bg-green-50 border border-green-200 text-green-700 rounded-md text-sm">
                  Profile updated successfully!
                </div>
              )}
              
              <form onSubmit={handleSaveProfile} className="space-y-6">
                <div className="space-y-2">
                  <label htmlFor="name" className="text-sm font-medium text-slate-700 dark:text-slate-200">
                    Full Name
                  </label>
                  <Input
                    id="name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Your full name"
                    required
                    className="w-full"
                  />
                </div>
                
                <div className="space-y-2">
                  <label htmlFor="email" className="text-sm font-medium text-slate-700 dark:text-slate-200">
                    Email Address
                  </label>
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    disabled
                    className="w-full bg-gray-100 dark:bg-slate-700"
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Email cannot be changed
                  </p>
                </div>
                
                <div className="space-y-2">
                  <label htmlFor="preferred-language" className="text-sm font-medium text-slate-700 dark:text-slate-200">
                    Preferred Language
                  </label>
                  <select
                    id="preferred-language"
                    value={preferredLanguage}
                    onChange={(e) => setPreferredLanguage(e.target.value)}
                    className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:text-white"
                  >
                    <option value="">Select a language</option>
                    <option value="spanish">Spanish</option>
                    <option value="french">French</option>
                    <option value="german">German</option>
                    <option value="italian">Italian</option>
                    <option value="portuguese">Portuguese</option>
                    <option value="russian">Russian</option>
                    <option value="japanese">Japanese</option>
                    <option value="chinese">Chinese</option>
                  </select>
                </div>
                
                <div className="space-y-2">
                  <label htmlFor="preferred-level" className="text-sm font-medium text-slate-700 dark:text-slate-200">
                    Preferred Level
                  </label>
                  <select
                    id="preferred-level"
                    value={preferredLevel}
                    onChange={(e) => setPreferredLevel(e.target.value)}
                    className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:text-white"
                  >
                    <option value="">Select a level</option>
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                  </select>
                </div>
                
                <div className="pt-4">
                  <Button 
                    type="submit" 
                    className="w-full bg-indigo-600 hover:bg-indigo-700 text-white"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                        <span>Saving...</span>
                      </>
                    ) : 'Save Profile'}
                  </Button>
                </div>
              </form>
              
              {/* Learning Plans Section */}
              <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-medium mb-4 text-slate-900 dark:text-white">Your Learning Plans</h3>
                
                {plansLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin h-6 w-6 border-2 border-indigo-500 border-t-transparent rounded-full mr-2"></div>
                    <span className="text-slate-600 dark:text-slate-300">Loading your learning plans...</span>
                  </div>
                ) : plansError ? (
                  <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md text-red-700 dark:text-red-400 text-sm">
                    {plansError}
                  </div>
                ) : learningPlans.length === 0 ? (
                  <div className="p-4 bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-md text-slate-600 dark:text-slate-400 text-sm">
                    You don't have any learning plans yet. Create one from the language selection page.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {learningPlans.map((plan) => (
                      <div key={plan.id} className="p-4 bg-white dark:bg-slate-800 border border-gray-200 dark:border-gray-700 rounded-md shadow-sm">
                        <div className="flex justify-between items-start mb-2">
                          <h4 className="text-md font-medium text-slate-900 dark:text-white capitalize">{plan.language} - {plan.proficiency_level}</h4>
                          <span className="text-xs bg-indigo-100 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-300 px-2 py-1 rounded">
                            {new Date(plan.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        
                        <div className="mt-2 space-y-2">
                          <div>
                            <h5 className="text-sm font-medium text-slate-700 dark:text-slate-300">Learning Goals:</h5>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {plan.goals.map((goal, index) => (
                                <span key={index} className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300 px-2 py-1 rounded capitalize">
                                  {goal}
                                </span>
                              ))}
                              {plan.custom_goal && (
                                <span className="text-xs bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 px-2 py-1 rounded">
                                  {plan.custom_goal}
                                </span>
                              )}
                            </div>
                          </div>
                          
                          <div>
                            <h5 className="text-sm font-medium text-slate-700 dark:text-slate-300">Duration:</h5>
                            <p className="text-sm text-slate-600 dark:text-slate-400">{plan.duration_months} months</p>
                          </div>
                          
                          <div className="pt-2">
                            <Button 
                              onClick={() => router.push(`/speech?plan=${plan.id}`)}
                              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white text-sm py-1"
                            >
                              Continue Learning
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              {/* Account Actions Section */}
              <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-medium mb-4 text-slate-900 dark:text-white">Account Actions</h3>
                
                <div className="space-y-4">
                  <button
                    onClick={handleLogout}
                    className="w-full py-2 px-4 border border-red-300 text-red-600 rounded-md hover:bg-red-50 dark:border-red-700 dark:text-red-400 dark:hover:bg-red-900/20"
                  >
                    Sign Out
                  </button>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
