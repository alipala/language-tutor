'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { AssessmentCard } from '@/components/assessment-card';
import { getUserLearningPlans, LearningPlan } from '@/lib/learning-api';
import { getApiUrl } from '@/lib/api-utils';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import ProtectedRoute from '@/components/protected-route';
import NavBar from '@/components/nav-bar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  User, Calendar, Trophy, Target, Star, Flame, 
  Download, Trash2, Settings, Edit3, Crown,
  TrendingUp, Award, BookOpen, Clock, Zap,
  ChevronRight, ChevronDown, Share2, Lock,
  Gem, Heart, Volume2, Mic, CheckCircle
} from 'lucide-react';

// API base URL
const API_URL = getApiUrl();

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
  const [activeTab, setActiveTab] = useState('overview');
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [expandedPlans, setExpandedPlans] = useState<Record<string, boolean>>({});
  
  // Collect all assessments from learning plans and user data
  const assessments = [];
  
  // Add user's last assessment if available
  if (user?.last_assessment_data) {
    assessments.push({
      ...user.last_assessment_data,
      date: new Date().toISOString(),
      source: 'User Profile',
      expanded: true
    });
  }
  
  // Add assessments from learning plans
  learningPlans.forEach((plan, index) => {
    if (plan.assessment_data) {
      assessments.push({
        ...plan.assessment_data,
        date: plan.created_at || new Date().toISOString(),
        planId: plan.id,
        language: plan.language,
        level: plan.proficiency_level,
        source: `${plan.language} - ${plan.proficiency_level}`,
        expanded: assessments.length === 0
      });
    }
  });
  
  // Sort assessments by date (newest first)
  assessments.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  
  // Get the latest assessment for quick access
  const latestAssessment = assessments.length > 0 ? assessments[0] : null;
  
  // State to track which assessments are expanded
  const [expandedAssessments, setExpandedAssessments] = useState<Record<number, boolean>>(
    assessments.reduce((acc, assessment, index) => {
      acc[index] = assessment.expanded || false;
      return acc;
    }, {})
  );
  
  // Toggle assessment expansion
  const toggleAssessment = (index: number) => {
    setExpandedAssessments(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  // Toggle plan expansion
  const togglePlanExpansion = (planId: string) => {
    setExpandedPlans(prev => ({
      ...prev,
      [planId]: !prev[planId]
    }));
  };
    
  // Helper function to get color class based on score
  const getColorClass = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-blue-500';
    if (score >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getSkillColor = (score: number) => {
    if (score >= 85) return 'bg-green-400';
    if (score >= 70) return 'bg-blue-400';
    if (score >= 55) return 'bg-yellow-400';
    return 'bg-red-400';
  };

  const getProgressBarColor = (progress: number) => {
    if (progress >= 80) return '#FFD63A';
    if (progress >= 60) return '#FFA955';
    return '#F75A5A';
  };

  // Mock user stats for display
  const userStats = {
    totalXP: 15750,
    currentLevel: 42,
    globalRank: 1247,
    currentStreak: 6,
    longestStreak: 45
  };

  // Mock achievements
  const achievements = [
    { name: 'Week Warrior', icon: '🔥', description: '7-day streak', earned: true, date: 'May 20, 2024' },
    { name: 'Monthly Master', icon: '👑', description: '30-day streak', earned: true, date: 'Apr 15, 2024' },
    { name: 'Perfect Practice', icon: '⭐', description: '100% lesson accuracy', earned: true, date: 'May 18, 2024' },
    { name: 'Speed Demon', icon: '⚡', description: 'Complete 10 lessons in one day', earned: true, date: 'May 10, 2024' },
    { name: 'Night Owl', icon: '🦉', description: 'Practice after 10 PM', earned: true, date: 'May 05, 2024' },
    { name: 'Century Club', icon: '💯', description: '100-day streak', earned: false }
  ];

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
    setShowLogoutConfirm(true);
  };

  const handleLogoutConfirm = async () => {
    await logout();
    window.location.href = '/';
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        <NavBar />
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Profile Hero Section */}
          <div className="bg-white rounded-2xl shadow-xl overflow-hidden mb-8">
            <div className="bg-teal-400 p-6 text-white relative overflow-hidden" style={{ backgroundColor: '#4ECFBF' }}>
              {/* Decorative background elements */}
              <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
              <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/10 rounded-full -ml-12 -mb-12"></div>
              
              <div className="relative z-10">
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-4">
                  <div className="flex items-center space-x-4 mb-4 md:mb-0">
                    <div className="h-16 w-16 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center text-xl font-bold">
                      {user?.name ? user.name.split(' ').map(n => n[0]).join('') : 'U'}
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold mb-1">{user?.name || 'User'}</h2>
                      <p className="text-white/80 text-sm mb-1">{user?.email}</p>
                      <p className="text-white/60 text-xs">Learning since {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long' })}</p>
                    </div>
                  </div>
                  
                  <div className="flex flex-col items-end space-y-1">
                    <div className="flex items-center space-x-2 bg-white/20 backdrop-blur-sm rounded-full px-3 py-1">
                      <Trophy className="h-4 w-4" />
                      <span className="font-semibold text-sm">Level {userStats.currentLevel}</span>
                    </div>
                    <div className="text-white/80 text-xs">
                      Global Rank: #{userStats.globalRank.toLocaleString()}
                    </div>
                  </div>
                </div>
                
                {/* Stats Row */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="bg-yellow-400 rounded-lg p-3 text-center" style={{ backgroundColor: '#FFD63A' }}>
                    <Zap className="h-5 w-5 mx-auto mb-1 text-white" />
                    <div className="text-lg font-bold text-white">{userStats.totalXP.toLocaleString()}</div>
                    <div className="text-white text-xs">Total XP</div>
                  </div>
                  <div className="bg-red-400 rounded-lg p-3 text-center" style={{ backgroundColor: '#F75A5A' }}>
                    <Flame className="h-5 w-5 mx-auto mb-1 text-white" />
                    <div className="text-lg font-bold text-white">{userStats.currentStreak}</div>
                    <div className="text-white text-xs">Day Streak</div>
                  </div>
                  <div className="bg-orange-400 rounded-lg p-3 text-center" style={{ backgroundColor: '#FFA955' }}>
                    <BookOpen className="h-5 w-5 mx-auto mb-1 text-white" />
                    <div className="text-lg font-bold text-white">{learningPlans.length}</div>
                    <div className="text-white text-xs">Languages</div>
                  </div>
                  <div className="bg-teal-400 border-2 border-white/30 rounded-lg p-3 text-center" style={{ backgroundColor: '#4ECFBF' }}>
                    <Award className="h-5 w-5 mx-auto mb-1 text-white" />
                    <div className="text-lg font-bold text-white">{achievements.filter(a => a.earned).length}</div>
                    <div className="text-white text-xs">Achievements</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="bg-white rounded-2xl shadow-lg overflow-hidden mb-8">
            <div className="border-b border-gray-200">
              <nav className="flex">
                {[
                  { id: 'overview', label: 'Overview', icon: TrendingUp },
                  { id: 'progress', label: 'Learning Progress', icon: Target },
                  { id: 'achievements', label: 'Achievements', icon: Trophy },
                  { id: 'settings', label: 'Settings', icon: Settings }
                ].map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === tab.id
                        ? 'border-teal-500 text-teal-600 bg-teal-50'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                    style={{
                      borderBottomColor: activeTab === tab.id ? '#4ECFBF' : 'transparent',
                      color: activeTab === tab.id ? '#4ECFBF' : undefined,
                      backgroundColor: activeTab === tab.id ? '#F0FDFA' : undefined
                    }}
                  >
                    <tab.icon className="h-4 w-4 mr-2" />
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>
          </div>

          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-8">
              {/* Learning Streak */}
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-gray-800 flex items-center">
                    <Flame className="h-6 w-6 mr-2" style={{ color: '#F75A5A' }} />
                    Learning Streak
                  </h3>
                  <div className="text-right">
                    <div className="text-2xl font-bold" style={{ color: '#F75A5A' }}>{userStats.currentStreak} days</div>
                    <div className="text-sm text-gray-500">Best: {userStats.longestStreak} days</div>
                  </div>
                </div>
                
                <div className="bg-red-50 border rounded-xl p-4" style={{ backgroundColor: '#FFF5F5', borderColor: 'rgba(247, 90, 90, 0.2)' }}>
                  <p className="text-sm font-medium" style={{ color: '#F75A5A' }}>
                    🔥 Keep it up! You're just 4 days away from breaking your personal record!
                  </p>
                </div>
              </div>

              {/* Recent Achievements */}
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-gray-800 flex items-center">
                    <Trophy className="h-6 w-6 mr-2" style={{ color: '#FFD63A' }} />
                    Recent Achievements
                  </h3>
                  <button 
                    onClick={() => setActiveTab('achievements')}
                    className="text-sm font-medium flex items-center hover:opacity-80 transition-opacity"
                    style={{ color: '#4ECFBF' }}
                  >
                    View all <ChevronRight className="h-4 w-4 ml-1" />
                  </button>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {achievements.filter(a => a.earned).slice(0, 4).map((achievement, index) => (
                    <div key={index} className="border rounded-xl p-4 flex items-center space-x-3" style={{ backgroundColor: '#FFFBF0', borderColor: 'rgba(255, 214, 58, 0.2)' }}>
                      <div className="text-2xl">{achievement.icon}</div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-800">{achievement.name}</h4>
                        <p className="text-sm text-gray-600">{achievement.description}</p>
                        <p className="text-xs text-gray-500 mt-1">{achievement.date}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Assessment Results */}
              {assessments.length > 0 && (
                <div className="bg-white rounded-2xl shadow-lg p-6">
                  <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
                    <Award className="h-6 w-6 mr-2" style={{ color: '#4ECFBF' }} />
                    Your Assessment Results
                    <span className="ml-2 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 text-xs px-2 py-0.5 rounded-full">
                      {assessments.length}
                    </span>
                  </h3>
                  
                  <div className="space-y-4">
                    {assessments.map((assessment, index) => (
                      <AssessmentCard
                        key={index}
                        assessment={assessment}
                        isExpanded={expandedAssessments[index]}
                        onToggle={() => toggleAssessment(index)}
                        index={index}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Learning Progress Tab */}
          {activeTab === 'progress' && (
            <div className="space-y-8">
              {plansLoading ? (
                <div className="bg-white rounded-2xl shadow-lg p-8 flex justify-center items-center">
                  <div className="animate-spin h-8 w-8 border-4 border-indigo-500 border-t-transparent rounded-full"></div>
                </div>
              ) : plansError ? (
                <div className="bg-white rounded-2xl shadow-lg p-6 bg-red-50 border border-red-200 text-red-600 text-sm flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {plansError}
                </div>
              ) : learningPlans.length === 0 ? (
                <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
                  <div className="w-16 h-16 mx-auto mb-4 bg-indigo-100 rounded-full flex items-center justify-center">
                    <BookOpen className="h-8 w-8 text-indigo-500" />
                  </div>
                  <h4 className="text-lg font-medium text-gray-800 mb-2">No Learning Plans Yet</h4>
                  <p className="text-gray-600 mb-4">Start your language learning journey by creating your first plan.</p>
                  <Button 
                    onClick={() => router.push('/language-selection')}
                    className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white py-2 px-6 rounded-lg shadow-md hover:shadow-lg transition-all"
                  >
                    Create Your First Plan
                  </Button>
                </div>
              ) : (
                learningPlans.map((plan) => (
                  <div key={plan.id} className="bg-white rounded-2xl shadow-lg overflow-hidden">
                    {/* Plan Header */}
                    <div className="p-6 text-white" style={{ backgroundColor: '#4ECFBF' }}>
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className="text-2xl font-bold capitalize flex items-center">
                            <span className="mr-3">{plan.language === 'Spanish' ? '🇪🇸' : plan.language === 'French' ? '🇫🇷' : '🌍'}</span>
                            {plan.language} - {plan.proficiency_level}
                          </h3>
                          <p className="text-white/80 mt-1">
                            Created {new Date(plan.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })} • {plan.duration_months} month journey
                          </p>
                        </div>
                        <div className="text-right">
                          <div className="text-3xl font-bold">75%</div>
                          <div className="text-white/80 text-sm">Complete</div>
                        </div>
                      </div>
                      
                      <div className="w-full bg-white/20 rounded-full h-3 overflow-hidden">
                        <div 
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: '75%',
                            backgroundColor: getProgressBarColor(75)
                          }}
                        ></div>
                      </div>
                    </div>

                    {/* Plan Content */}
                    <div className="p-6">
                      {/* Learning Goals */}
                      <div className="mb-6">
                        <h4 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                          <Target className="h-5 w-5 mr-2" style={{ color: '#4ECFBF' }} />
                          Learning Goals
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {plan.goals.map((goal, index) => (
                            <span key={index} className="px-3 py-1 rounded-full text-sm font-medium border" style={{ backgroundColor: '#E6FFFE', color: '#4ECFBF', borderColor: 'rgba(78, 207, 191, 0.2)' }}>
                              {goal}
                            </span>
                          ))}
                          {plan.custom_goal && (
                            <span className="px-3 py-1 rounded-full text-sm font-medium border" style={{ backgroundColor: '#FFF4E6', color: '#FFA955', borderColor: 'rgba(255, 169, 85, 0.2)' }}>
                              {plan.custom_goal}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Assessment Results */}
                      {plan.assessment_data && (
                        <div className="border rounded-xl p-6 mb-6" style={{ backgroundColor: '#F0F9FF', borderColor: 'rgba(78, 207, 191, 0.2)' }}>
                          <div className="flex items-center justify-between mb-4">
                            <h4 className="text-lg font-semibold text-gray-800 flex items-center">
                              <Award className="h-5 w-5 mr-2" style={{ color: '#4ECFBF' }} />
                              Latest Assessment Results
                            </h4>
                            <button
                              onClick={() => togglePlanExpansion(plan.id)}
                              className="flex items-center text-sm font-medium hover:opacity-80 transition-opacity"
                              style={{ color: '#4ECFBF' }}
                            >
                              {expandedPlans[plan.id] ? 'Show less' : 'Show details'}
                              <ChevronDown className={`h-4 w-4 ml-1 transform transition-transform ${
                                expandedPlans[plan.id] ? 'rotate-180' : ''
                              }`} />
                            </button>
                          </div>

                          {/* Quick Assessment Overview */}
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                            <div className="bg-white rounded-lg p-3 text-center">
                              <div className="text-2xl font-bold" style={{ color: '#4ECFBF' }}>{plan.assessment_data.overall_score}</div>
                              <div className="text-sm text-gray-600">Overall Score</div>
                            </div>
                            <div className="bg-white rounded-lg p-3 text-center">
                              <div className="text-2xl font-bold" style={{ color: '#FFD63A' }}>{plan.assessment_data.confidence}%</div>
                              <div className="text-sm text-gray-600">Confidence</div>
                            </div>
                            <div className="bg-white rounded-lg p-3 text-center">
                              <div className="text-2xl font-bold" style={{ color: '#FFA955' }}>B2</div>
                              <div className="text-sm text-gray-600">CEFR Level</div>
                            </div>
                            <div className="bg-white rounded-lg p-3 text-center">
                              <div className="text-sm text-gray-500">{new Date(plan.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</div>
                              <div className="text-sm text-gray-600">Assessed</div>
                            </div>
                          </div>

                          {/* Detailed Assessment View */}
                          {expandedPlans[plan.id] && (
                            <div className="space-y-6 mt-6 pt-6 border-t" style={{ borderColor: 'rgba(78, 207, 191, 0.2)' }}>
                              {/* Skill Breakdown */}
                              <div>
                                <h5 className="font-semibold text-gray-800 mb-3">Skill Breakdown</h5>
                                <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                                  {['pronunciation', 'grammar', 'vocabulary', 'fluency', 'coherence'].map((skill) => {
                                    const skillData = plan.assessment_data ? 
                                      (plan.assessment_data as any)[skill] : { score: 0, feedback: '' };
                                    
                                    return (
                                      <div key={skill} className="bg-white rounded-lg p-4 text-center">
                                        <div className="capitalize text-sm text-gray-600 mb-2">{skill}</div>
                                        <div className="text-xl font-bold text-gray-800 mb-2">{skillData.score}</div>
                                        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                                          <div 
                                            className={`h-full ${getSkillColor(skillData.score)} rounded-full`}
                                            style={{width: `${skillData.score}%`}}
                                          ></div>
                                        </div>
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>

                              {/* Strengths and Improvements */}
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                  <h5 className="font-semibold text-green-700 mb-3 flex items-center">
                                    <CheckCircle className="h-4 w-4 mr-2" />
                                    Strengths
                                  </h5>
                                  <div className="space-y-2">
                                    {plan.assessment_data?.strengths?.map((strength: string, index: number) => (
                                      <div key={index} className="bg-green-50 text-green-800 p-3 rounded-lg text-sm">
                                        {strength}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                                <div>
                                  <h5 className="font-semibold text-orange-700 mb-3 flex items-center">
                                    <Target className="h-4 w-4 mr-2" />
                                    Areas for Improvement
                                  </h5>
                                  <div className="space-y-2">
                                    {plan.assessment_data?.areas_for_improvement?.map((improvement: string, index: number) => (
                                      <div key={index} className="bg-orange-50 text-orange-800 p-3 rounded-lg text-sm">
                                        {improvement}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div className="flex flex-col sm:flex-row gap-3 mt-6">
                        <button 
                          onClick={() => router.push(`/speech?plan=${plan.id}`)}
                          className="flex-1 text-white py-3 px-6 rounded-xl font-medium hover:opacity-90 transition-opacity flex items-center justify-center" 
                          style={{ backgroundColor: '#4ECFBF' }}
                        >
                          <BookOpen className="h-5 w-5 mr-2" />
                          Continue Learning
                        </button>
                        <button className="flex-1 border-2 py-3 px-6 rounded-xl font-medium hover:bg-opacity-10 transition-all flex items-center justify-center" style={{ borderColor: '#4ECFBF', color: '#4ECFBF', backgroundColor: 'rgba(230, 255, 254, 0.5)' }}>
                          <Share2 className="h-5 w-5 mr-2" />
                          Share Progress
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Achievements Tab */}
          {activeTab === 'achievements' && (
            <div className="space-y-8">
              {/* Achievement Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="rounded-2xl p-6 text-white" style={{ backgroundColor: '#FFD63A' }}>
                  <Trophy className="h-12 w-12 mb-4 opacity-80" />
                  <div className="text-3xl font-bold">{achievements.filter(a => a.earned).length}</div>
                  <div className="text-yellow-100">Achievements Earned</div>
                </div>
                <div className="rounded-2xl p-6 text-white" style={{ backgroundColor: '#F75A5A' }}>
                  <Star className="h-12 w-12 mb-4 opacity-80" />
                  <div className="text-3xl font-bold">{userStats.longestStreak}</div>
                  <div className="text-red-100">Longest Streak</div>
                </div>
                <div className="rounded-2xl p-6 text-white" style={{ backgroundColor: '#4ECFBF' }}>
                  <Crown className="h-12 w-12 mb-4 opacity-80" />
                  <div className="text-3xl font-bold">{userStats.currentLevel}</div>
                  <div className="text-teal-100">Current Level</div>
                </div>
              </div>

              {/* Achievements Grid */}
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-800 mb-6">All Achievements</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {achievements.map((achievement, index) => (
                    <div key={index} className={`relative rounded-xl p-6 border-2 transition-all ${
                      achievement.earned 
                        ? 'shadow-md' 
                        : 'bg-gray-50 border-gray-200 opacity-60'
                    }`} style={achievement.earned ? { backgroundColor: '#FFFBF0', borderColor: '#FFD63A' } : {}}>
                      <div className="text-center">
                        <div className="text-4xl mb-3">{achievement.icon}</div>
                        <h4 className="font-bold text-gray-800 mb-2">{achievement.name}</h4>
                        <p className="text-sm text-gray-600 mb-3">{achievement.description}</p>
                        {achievement.earned ? (
                          <div className="text-xs text-green-600 font-medium">
                            Earned {achievement.date}
                          </div>
                        ) : (
                          <div className="text-xs text-gray-400">
                            Not earned yet
                          </div>
                        )}
                      </div>
                      {achievement.earned && (
                        <div className="absolute top-2 right-2">
                          <CheckCircle className="h-5 w-5 text-green-500" />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Settings Tab */}
          {activeTab === 'settings' && (
            <div className="space-y-8">
              {/* Account Settings */}
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
                  <User className="h-6 w-6 mr-2 text-purple-500" />
                  Account Settings
                </h3>
                
                {error && (
                  <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {error}
                  </div>
                )}
                
                <form onSubmit={handleSaveProfile} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
                      <Input 
                        type="text" 
                        className="w-full p-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
                      <Input 
                        type="email" 
                        className="w-full p-3 border border-gray-300 rounded-xl bg-gray-50 cursor-not-allowed"
                        value={email}
                        disabled
                      />
                      <p className="text-xs text-gray-500 mt-1">Email cannot be changed</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Preferred Language</label>
                      <Input
                        type="text"
                        className="w-full p-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        value={preferredLanguage}
                        onChange={(e) => setPreferredLanguage(e.target.value)}
                        placeholder="e.g. Spanish, French, German"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Proficiency Level</label>
                      <Input
                        type="text"
                        className="w-full p-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        value={preferredLevel}
                        onChange={(e) => setPreferredLevel(e.target.value)}
                        placeholder="e.g. Beginner, Intermediate, Advanced"
                      />
                    </div>
                  </div>
                  
                  <Button 
                    type="submit"
                    className="bg-gradient-to-r from-purple-500 to-indigo-600 text-white py-3 px-6 rounded-xl font-medium hover:shadow-lg transition-all"
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
                    ) : 'Save Changes'}
                  </Button>
                </form>
              </div>

              {/* Account Actions */}
              <div className="bg-white rounded-2xl shadow-lg p-6 border-2 border-red-100">
                <h3 className="text-xl font-bold text-red-600 mb-6 flex items-center">
                  <Trash2 className="h-6 w-6 mr-2" />
                  Account Actions
                </h3>
                
                <div className="space-y-4">
                  <div className="bg-red-50 rounded-xl p-4">
                    <h4 className="font-medium text-red-800 mb-2">Sign Out</h4>
                    <p className="text-sm text-red-600 mb-4">
                      Sign out of your account. You can sign back in anytime.
                    </p>
                    <button 
                      onClick={handleLogout}
                      className="bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-lg font-medium transition-all text-sm"
                    >
                      Sign Out
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Logout Confirmation Modal */}
      {showLogoutConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <div className="text-center">
              <Trash2 className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-gray-800 mb-2">Sign Out</h3>
              <p className="text-gray-600 mb-6">
                Are you sure you want to sign out?
              </p>
              
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowLogoutConfirm(false)}
                  className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 py-3 px-4 rounded-xl font-medium transition-all"
                >
                  Cancel
                </button>
                <button
                  onClick={handleLogoutConfirm}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white py-3 px-4 rounded-xl font-medium transition-all"
                >
                  Sign Out
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </ProtectedRoute>
  );
}
