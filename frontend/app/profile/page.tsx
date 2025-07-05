'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { AssessmentCard } from '@/components/assessment-card';
import AssessmentLearningPlanCard from '@/components/assessment-learning-plan-card';
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
  Gem, Heart, Volume2, Mic, CheckCircle, Brain,
  Bell
} from 'lucide-react';
import EnhancedAnalysisModal from '@/components/enhanced-analysis-modal';
import ExportModal from '@/components/export-modal';
import SubscriptionManagement from './subscription-management';
import MembershipBadge, { UsageIndicator } from '@/components/membership-badge';
import PaymentProcessingModal from '@/components/payment-processing-modal';
import SoundWaveLoader from '@/components/sound-wave-loader';
import NotificationsTab from '@/components/notifications-tab';

// API base URL
const API_URL = getApiUrl();

export default function ProfilePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, logout } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [preferredLanguage, setPreferredLanguage] = useState('');
  const [preferredLevel, setPreferredLevel] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [isPasswordLoading, setIsPasswordLoading] = useState(false);
  const [learningPlans, setLearningPlans] = useState<LearningPlan[]>([]);
  const [plansLoading, setPlansLoading] = useState(true);
  const [plansError, setPlansError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');

  // Check for tab parameter in URL
  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab && ['overview', 'progress', 'achievements', 'notifications', 'export', 'settings'].includes(tab)) {
      setActiveTab(tab);
    }
  }, [searchParams]);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [expandedPlans, setExpandedPlans] = useState<Record<string, boolean>>({});
  
  // Create assessment-learning plan pairs
  const assessmentLearningPairs: Array<{
    assessment: any;
    learningPlan: LearningPlan | null;
  }> = [];
  
  // Add user's last assessment if available (standalone assessment)
  if (user?.last_assessment_data) {
    // Check if this assessment is already linked to a learning plan
    const linkedPlan = learningPlans.find(plan => 
      plan.assessment_data && 
      plan.assessment_data.overall_score === user.last_assessment_data.overall_score &&
      plan.assessment_data.confidence === user.last_assessment_data.confidence
    );
    
    if (!linkedPlan) {
      assessmentLearningPairs.push({
        assessment: {
          ...user.last_assessment_data,
          date: new Date().toISOString(),
          source: 'User Profile',
          expanded: true
        },
        learningPlan: null
      });
    }
  }
  
  // Add assessments from learning plans (linked pairs)
  learningPlans.forEach((plan, index) => {
    if (plan.assessment_data) {
      assessmentLearningPairs.push({
        assessment: {
          ...plan.assessment_data,
          date: plan.created_at || new Date().toISOString(),
          planId: plan.id,
          language: plan.language,
          level: plan.proficiency_level,
          source: `${plan.language} - ${plan.proficiency_level}`,
          expanded: false // Always start collapsed
        },
        learningPlan: plan
      });
    }
  });
  
  // Sort pairs by assessment date (newest first)
  assessmentLearningPairs.sort((a, b) => new Date(b.assessment.date).getTime() - new Date(a.assessment.date).getTime());
  
  // State to track which assessment-plan pairs are expanded
  const [expandedAssessmentPlans, setExpandedAssessmentPlans] = useState<Record<number, boolean>>({});
  
  // Initialize expanded state when pairs change
  useEffect(() => {
    const initialExpanded: Record<number, boolean> = {};
    assessmentLearningPairs.forEach((pair, index) => {
      initialExpanded[index] = pair.assessment.expanded || false;
    });
    setExpandedAssessmentPlans(initialExpanded);
  }, [assessmentLearningPairs.length]);
  
  // Toggle assessment-plan pair expansion
  const toggleAssessmentPlan = (index: number) => {
    setExpandedAssessmentPlans(prev => ({
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

  // Progress stats state
  const [progressStats, setProgressStats] = useState<any>(null);
  const [conversationHistory, setConversationHistory] = useState<any[]>([]);
  const [achievements, setAchievements] = useState<any[]>([]);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);

  // Enhanced analysis modal state
  const [showEnhancedAnalysis, setShowEnhancedAnalysis] = useState(false);
  const [selectedAnalysis, setSelectedAnalysis] = useState<any>(null);
  const [selectedSessionInfo, setSelectedSessionInfo] = useState<any>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);

  // Export modal state
  const [showExportModal, setShowExportModal] = useState(false);
  
  // Payment processing modal state
  const [showPaymentProcessing, setShowPaymentProcessing] = useState(false);
  
  // Check if user came from successful checkout
  const checkoutSuccess = searchParams.get('checkout') === 'success';
  
  // Export loading states
  const [exportLoading, setExportLoading] = useState<Record<string, boolean>>({});
  
  // Calculate export stats for export modal
  const exportStats = {
    learningPlans: learningPlans.length,
    conversations: conversationHistory.length,
    assessments: assessmentLearningPairs.length
  };

  // Direct export functions
  const handleDirectExport = async (type: 'learning-plans' | 'conversations' | 'data', format: 'pdf' | 'csv' | 'zip' | 'json') => {
    if (!user) return;
    
    const exportKey = `${type}-${format}`;
    setExportLoading(prev => ({ ...prev, [exportKey]: true }));
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`${API_URL}/api/export/${type}?format=${format}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Export failed');
      }

      // Get filename from response headers or create default
      const contentDisposition = response.headers.get('content-disposition');
      let filename = `${type}_${user.name.replace(' ', '_')}.${format}`;
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
    } catch (error) {
      console.error('Export error:', error);
      // You could add a toast notification here
    } finally {
      setExportLoading(prev => ({ ...prev, [exportKey]: false }));
    }
  };

  // Subscription status state
  const [subscriptionStatus, setSubscriptionStatus] = useState<any>(null);
  const [subscriptionLoading, setSubscriptionLoading] = useState(true);

  // Mock user stats for display (will be replaced with real data)
  const userStats = {
    totalXP: progressStats?.total_sessions ? progressStats.total_sessions * 250 : 1500,
    currentLevel: Math.floor((progressStats?.total_minutes || 10) / 10) + 1,
    globalRank: 1247,
    currentStreak: progressStats?.current_streak || 0,
    longestStreak: progressStats?.longest_streak || 0
  };

  // Fetch subscription status
  const fetchSubscriptionStatus = async () => {
    if (!user) return;
    
    setSubscriptionLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.log('[PROFILE] No token found for subscription status fetch');
        setSubscriptionLoading(false);
        return;
      }

      console.log('[PROFILE] Fetching subscription status...');
      const response = await fetch('/api/stripe/subscription-status', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      console.log('[PROFILE] Subscription status response:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('[PROFILE] Subscription status data:', data);
        setSubscriptionStatus(data);
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        console.error('[PROFILE] Subscription status error:', errorData);
      }
    } catch (error) {
      console.error('[PROFILE] Error fetching subscription status:', error);
    } finally {
      setSubscriptionLoading(false);
    }
  };

  // Helper function to get plan display info
  const getPlanDisplayInfo = () => {
    if (!subscriptionStatus) return { name: 'Free', color: '#9CA3AF', icon: '⚡' };
    
    switch (subscriptionStatus.plan) {
      case 'fluency_builder':
        return { 
          name: 'Fluency Builder', 
          color: '#4ECFBF', 
          icon: '⭐',
          period: subscriptionStatus.period === 'annual' ? 'Annual' : 'Monthly'
        };
      case 'team_mastery':
        return { 
          name: 'Team Mastery', 
          color: '#FFD63A', 
          icon: '👑',
          period: subscriptionStatus.period === 'annual' ? 'Annual' : 'Monthly'
        };
      default:
        return { name: 'Try & Learn', color: '#9CA3AF', icon: '⚡' };
    }
  };

  const planInfo = getPlanDisplayInfo();

  // Load user data when component mounts
  useEffect(() => {
    if (user) {
      setName(user.name);
      setEmail(user.email);
      setPreferredLanguage(user.preferred_language || '');
      setPreferredLevel(user.preferred_level || '');
      
      // Fetch user's learning plans and progress data
      fetchUserLearningPlans();
      fetchProgressData();
      fetchSubscriptionStatus();
    }
  }, [user]);

  // Handle checkout success flow
  useEffect(() => {
    if (checkoutSuccess && user) {
      console.log('[PROFILE] Checkout success detected, showing payment processing modal');
      setShowPaymentProcessing(true);
    }
  }, [checkoutSuccess, user]);

  // Fetch progress data from API
  const fetchProgressData = async () => {
    if (!user) return;
    
    setStatsLoading(true);
    setStatsError(null);
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      // Fetch progress stats
      const statsResponse = await fetch(`${API_URL}/api/progress/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (statsResponse.ok) {
        const stats = await statsResponse.json();
        setProgressStats(stats);
        console.log('[PROFILE] Progress stats loaded:', stats);
      } else {
        console.error('[PROFILE] Failed to fetch progress stats');
      }

      // Fetch conversation history
      const historyResponse = await fetch(`${API_URL}/api/progress/conversations?limit=10`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (historyResponse.ok) {
        const historyData = await historyResponse.json();
        setConversationHistory(historyData.sessions || []);
        console.log('[PROFILE] Conversation history loaded:', historyData.sessions?.length || 0, 'sessions');
      } else {
        console.error('[PROFILE] Failed to fetch conversation history');
      }

      // Fetch achievements
      const achievementsResponse = await fetch(`${API_URL}/api/progress/achievements`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (achievementsResponse.ok) {
        const achievementsData = await achievementsResponse.json();
        setAchievements(achievementsData.achievements || []);
        console.log('[PROFILE] Achievements loaded:', achievementsData.achievements?.length || 0, 'achievements');
      } else {
        console.error('[PROFILE] Failed to fetch achievements');
        // Set empty achievements array as fallback
        setAchievements([]);
      }

    } catch (err: any) {
      console.error('[PROFILE] Error fetching progress data:', err);
      setStatsError(err.message || 'Failed to load progress data');
      // Set fallback empty data
      setAchievements([]);
    } finally {
      setStatsLoading(false);
    }
  };
  
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
    setIsPasswordLoading(true);
    setError(null);
    setPasswordError(null);
    setIsSaved(false);
    setPasswordSuccess(false);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      // Update profile information
      const profileResponse = await fetch(`${API_URL}/auth/update-profile`, {
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

      if (!profileResponse.ok) {
        const errorData = await profileResponse.json();
        throw new Error(errorData.detail || 'Failed to update profile');
      }

      // Update session storage with new preferences
      if (preferredLanguage) {
        sessionStorage.setItem('selectedLanguage', preferredLanguage);
      }
      
      if (preferredLevel) {
        sessionStorage.setItem('selectedLevel', preferredLevel);
      }

      // Handle password update if fields are provided
      if (currentPassword && newPassword && confirmPassword) {
        // Validation
        if (newPassword !== confirmPassword) {
          setPasswordError('New passwords do not match');
          setIsLoading(false);
          setIsPasswordLoading(false);
          return;
        }

        if (newPassword.length < 6) {
          setPasswordError('New password must be at least 6 characters long');
          setIsLoading(false);
          setIsPasswordLoading(false);
          return;
        }

        const passwordResponse = await fetch(`${API_URL}/auth/update-password`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword
          })
        });

        if (!passwordResponse.ok) {
          const errorData = await passwordResponse.json();
          throw new Error(errorData.detail || 'Failed to update password');
        }

        // Clear password fields
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setPasswordSuccess(true);
      }

      setIsSaved(true);
      setTimeout(() => {
        setIsSaved(false);
        setPasswordSuccess(false);
      }, 3000);
    } catch (err: any) {
      console.error('Update error:', err);
      if (err.message.includes('password')) {
        setPasswordError(err.message || 'Failed to update password. Please try again.');
      } else {
        setError(err.message || 'Failed to update profile. Please try again.');
      }
    } finally {
      setIsLoading(false);
      setIsPasswordLoading(false);
    }
  };

  const handlePasswordUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsPasswordLoading(true);
    setPasswordError(null);
    setPasswordSuccess(false);

    // Validation
    if (!currentPassword || !newPassword || !confirmPassword) {
      setPasswordError('All password fields are required');
      setIsPasswordLoading(false);
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match');
      setIsPasswordLoading(false);
      return;
    }

    if (newPassword.length < 6) {
      setPasswordError('New password must be at least 6 characters long');
      setIsPasswordLoading(false);
      return;
    }

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`${API_URL}/auth/update-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update password');
      }

      // Clear password fields
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      
      setPasswordSuccess(true);
      setTimeout(() => setPasswordSuccess(false), 3000);
    } catch (err: any) {
      console.error('Password update error:', err);
      setPasswordError(err.message || 'Failed to update password. Please try again.');
    } finally {
      setIsPasswordLoading(false);
    }
  };

  const handleLogout = () => {
    setShowLogoutConfirm(true);
  };

  const handleLogoutConfirm = async () => {
    await logout();
    window.location.href = '/';
  };

  const handleDeleteAccount = () => {
    setShowDeleteConfirm(true);
  };

  const handleDeleteAccountConfirm = async () => {
    setIsDeleting(true);
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`${API_URL}/auth/deactivate-account`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete account');
      }

      // Account deactivated successfully, logout and redirect
      await logout();
      window.location.href = '/';
    } catch (err: any) {
      console.error('Account deletion error:', err);
      setError(err.message || 'Failed to delete account. Please try again.');
      setShowDeleteConfirm(false);
    } finally {
      setIsDeleting(false);
    }
  };

  // Function to fetch and show enhanced analysis
  const handleShowEnhancedAnalysis = async (sessionId: string, sessionInfo: any) => {
    if (!user) return;
    
    setAnalysisLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`${API_URL}/api/progress/conversation/${sessionId}/analysis`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const analysisData = await response.json();
        // Include conversation messages in the analysis data
        const enhancedAnalysisWithMessages = {
          ...analysisData.enhanced_analysis,
          conversation_messages: analysisData.conversation_messages || []
        };
        setSelectedAnalysis(enhancedAnalysisWithMessages);
        setSelectedSessionInfo(analysisData.session_info);
        setShowEnhancedAnalysis(true);
      } else {
        console.error('Failed to fetch enhanced analysis');
      }
    } catch (error) {
      console.error('Error fetching enhanced analysis:', error);
    } finally {
      setAnalysisLoading(false);
    }
  };

  // Handle payment processing completion
  const handlePaymentProcessingComplete = () => {
    console.log('[PROFILE] Payment processing complete, refreshing subscription status');
    setShowPaymentProcessing(false);
    
    // Refresh subscription status to get updated data
    fetchSubscriptionStatus();
    
    // Remove checkout parameter from URL
    const url = new URL(window.location.href);
    url.searchParams.delete('checkout');
    window.history.replaceState({}, '', url.toString());
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        <NavBar />
        
        <div className="container mx-auto px-4 pt-24 pb-8">
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
                  
                  <div className="flex flex-col items-end space-y-2">
                    <div className="flex items-center space-x-2 bg-white/20 backdrop-blur-sm rounded-full px-3 py-1">
                      <Trophy className="h-4 w-4" />
                      <span className="font-semibold text-sm">Level {userStats.currentLevel}</span>
                    </div>
                    <div className="text-white/80 text-xs">
                      Global Rank: #{userStats.globalRank.toLocaleString()}
                    </div>
                  </div>
                </div>
                
                {/* Subscription & Stats Row */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Subscription Status Card */}
                  <div className="bg-white/30 backdrop-blur-sm rounded-xl p-6 shadow-lg border border-white/40">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <div className="text-3xl">{planInfo.icon}</div>
                        <div>
                          <div className="text-white font-bold text-xl tracking-tight">{planInfo.name}</div>
                          {planInfo.period && (
                            <div className="text-white/90 text-base font-medium">{planInfo.period}</div>
                          )}
                        </div>
                      </div>
                      {subscriptionStatus?.status === 'active' && (
                        <div className="flex items-center text-white text-base font-medium">
                          <div className="w-3 h-3 bg-green-400 rounded-full mr-2 animate-pulse"></div>
                          Active
                        </div>
                      )}
                    </div>
                    
                    {!subscriptionLoading && subscriptionStatus?.limits && (
                      <div className="space-y-3">
                        <div className="flex justify-between text-white text-base">
                          <span className="font-medium">Practice Sessions</span>
                          <span className="font-bold text-lg">
                            {subscriptionStatus.limits.is_unlimited ? '∞' : 
                             `${subscriptionStatus.limits.sessions_remaining}/${subscriptionStatus.limits.sessions_limit}`}
                          </span>
                        </div>
                        <div className="flex justify-between text-white text-base">
                          <span className="font-medium">Assessments</span>
                          <span className="font-bold text-lg">
                            {subscriptionStatus.limits.is_unlimited ? '∞' : 
                             `${subscriptionStatus.limits.assessments_remaining}/${subscriptionStatus.limits.assessments_limit}`}
                          </span>
                        </div>
                      </div>
                    )}
                    
                    {subscriptionLoading && (
                      <div className="flex items-center justify-center py-3">
                        <div className="animate-spin h-5 w-5 border-2 border-white/30 border-t-white rounded-full"></div>
                      </div>
                    )}
                  </div>
                  
                  {/* Learning Stats Grid */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-yellow-400 rounded-lg p-3 text-center" style={{ backgroundColor: '#FFD63A' }}>
                      <Flame className="h-5 w-5 mx-auto mb-1 text-white" />
                      <div className="text-lg font-bold text-white">{userStats.currentStreak}</div>
                      <div className="text-white text-xs">Day Streak</div>
                    </div>
                    <div className="bg-red-400 rounded-lg p-3 text-center" style={{ backgroundColor: '#F75A5A' }}>
                      <BookOpen className="h-5 w-5 mx-auto mb-1 text-white" />
                      <div className="text-lg font-bold text-white">{learningPlans.length}</div>
                      <div className="text-white text-xs">Languages</div>
                    </div>
                    <div className="bg-orange-400 rounded-lg p-3 text-center" style={{ backgroundColor: '#FFA955' }}>
                      <Award className="h-5 w-5 mx-auto mb-1 text-white" />
                      <div className="text-lg font-bold text-white">{achievements.filter(a => a.earned).length}</div>
                      <div className="text-white text-xs">Achievements</div>
                    </div>
                    <div className="bg-blue-500 rounded-lg p-3 text-center">
                      <Zap className="h-5 w-5 mx-auto mb-1 text-white" />
                      <div className="text-lg font-bold text-white">{userStats.totalXP.toLocaleString()}</div>
                      <div className="text-white text-xs">Total XP</div>
                    </div>
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
                  { id: 'notifications', label: 'Notifications', icon: Bell },
                  { id: 'export', label: 'Export Data', icon: Download },
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


              {/* Conversation History */}
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-gray-800 flex items-center">
                    <Mic className="h-6 w-6 mr-2" style={{ color: '#4ECFBF' }} />
                    Conversation History
                    <span className="ml-2 bg-teal-100 text-teal-700 text-xs px-2 py-0.5 rounded-full">
                      {progressStats?.total_sessions || 0} sessions
                    </span>
                  </h3>
                  <div className="text-sm text-gray-500">
                    {progressStats?.total_minutes ? `${Math.round(progressStats.total_minutes)} minutes practiced` : ''}
                  </div>
                </div>
                
                {statsLoading ? (
                  <div className="flex justify-center items-center py-8">
                    <SoundWaveLoader 
                      size="md"
                      color="#4ECFBF"
                      text="Loading conversations..."
                      subtext="Fetching your practice history"
                    />
                  </div>
                ) : conversationHistory.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="w-16 h-16 mx-auto mb-4 bg-teal-100 rounded-full flex items-center justify-center">
                      <Mic className="h-8 w-8 text-teal-500" />
                    </div>
                    <h4 className="text-lg font-medium text-gray-800 mb-2">No Conversations Yet</h4>
                    <p className="text-gray-600 mb-4">Start practicing to see your conversation history here.</p>
                    <Button 
                      onClick={() => router.push('/speech')}
                      className="text-white py-2 px-6 rounded-lg shadow-md hover:shadow-lg transition-all"
                      style={{ backgroundColor: '#4ECFBF' }}
                    >
                      Start Practicing
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {conversationHistory.slice(0, 5).map((session, index) => (
                      <div key={session.id || index} className="border rounded-xl p-4" style={{ backgroundColor: '#F0FDFA', borderColor: 'rgba(78, 207, 191, 0.2)' }}>
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold" style={{ backgroundColor: '#4ECFBF' }}>
                              {session.language?.charAt(0)?.toUpperCase() || 'L'}
                            </div>
                            <div>
                              <h4 className="font-semibold text-gray-800 capitalize">
                                {session.language} - {session.level}
                              </h4>
                              <p className="text-sm text-gray-600">
                                {session.topic && `Topic: ${session.topic} • `}
                                {Math.round(session.duration_minutes || 0)} min • {session.message_count || 0} messages
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-xs text-gray-500">
                              {session.created_at ? new Date(session.created_at).toLocaleDateString('en-US', { 
                                month: 'short', 
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                              }) : 'Recent'}
                            </div>
                            {session.is_streak_eligible && (
                              <div className="flex items-center text-xs text-green-600 mt-1">
                                <Flame className="h-3 w-3 mr-1" />
                                Streak eligible
                              </div>
                            )}
                          </div>
                        </div>
                        
                        {session.summary && (
                          <div className="bg-white rounded-lg p-3 text-sm text-gray-700 mb-3">
                            <strong>Summary:</strong> {session.summary}
                          </div>
                        )}
                        
                        {/* Enhanced Analysis Button */}
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            {session.enhanced_analysis && (
                              <Badge variant="secondary" className="bg-purple-100 text-purple-700 text-xs">
                                <Brain className="h-3 w-3 mr-1" />
                                Enhanced Analysis Available
                              </Badge>
                            )}
                          </div>
                          
                          {session.enhanced_analysis && (
                            <Button
                              onClick={() => handleShowEnhancedAnalysis(session.id, {
                                language: session.language,
                                level: session.level,
                                topic: session.topic,
                                duration_minutes: session.duration_minutes,
                                message_count: session.message_count,
                                created_at: session.created_at
                              })}
                              variant="outline"
                              size="sm"
                              className="text-purple-600 border-purple-200 hover:bg-purple-50"
                              disabled={analysisLoading}
                            >
                              {analysisLoading ? (
                                <>
                                  <div className="animate-spin h-3 w-3 mr-1 border border-purple-600 border-t-transparent rounded-full"></div>
                                  Loading...
                                </>
                              ) : (
                                <>
                                  <Brain className="h-3 w-3 mr-1" />
                                  View Analysis
                                </>
                              )}
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                    
                    {conversationHistory.length > 5 && (
                      <div className="text-center pt-4">
                        <button 
                          className="text-sm font-medium hover:opacity-80 transition-opacity"
                          style={{ color: '#4ECFBF' }}
                        >
                          View all {conversationHistory.length} conversations
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>

            </div>
          )}

          {/* Learning Progress Tab */}
          {activeTab === 'progress' && (
            <div className="space-y-8">
              {/* Assessment & Learning Plan Results */}
              {assessmentLearningPairs.length > 0 && (
                <div className="bg-white rounded-2xl shadow-lg p-6">
                  <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
                    <Award className="h-6 w-6 mr-2" style={{ color: '#4ECFBF' }} />
                    Your Learning Journey
                    <span className="ml-2 bg-indigo-100 text-indigo-700 text-xs px-2 py-0.5 rounded-full">
                      {assessmentLearningPairs.length}
                    </span>
                  </h3>
                  
                  <div className="space-y-6">
                    {assessmentLearningPairs.map((pair, index) => (
                      <AssessmentLearningPlanCard
                        key={index}
                        assessment={pair.assessment}
                        learningPlan={pair.learningPlan}
                        isExpanded={expandedAssessmentPlans[index] || false}
                        onToggle={() => toggleAssessmentPlan(index)}
                        index={index}
                      />
                    ))}
                  </div>
                </div>
              )}

              {plansLoading ? (
                <div className="bg-white rounded-2xl shadow-lg p-8 flex justify-center items-center">
                  <SoundWaveLoader 
                    size="lg"
                    color="#6366F1"
                    text="Loading learning plans..."
                    subtext="Fetching your personalized journey"
                  />
                </div>
              ) : plansError ? (
                <div className="bg-white rounded-2xl shadow-lg p-6 bg-red-50 border border-red-200 text-red-600 text-sm flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {plansError}
                </div>
              ) : assessmentLearningPairs.length === 0 && learningPlans.length === 0 ? (
                <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
                  <div className="w-16 h-16 mx-auto mb-4 bg-indigo-100 rounded-full flex items-center justify-center">
                    <BookOpen className="h-8 w-8 text-indigo-500" />
                  </div>
                  <h4 className="text-lg font-medium text-gray-800 mb-2">No Learning Journey Yet</h4>
                  <p className="text-gray-600 mb-4">Start your language learning journey by taking an assessment and creating your first plan.</p>
                  <Button 
                    onClick={() => router.push('/language-selection')}
                    className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white py-2 px-6 rounded-lg shadow-md hover:shadow-lg transition-all"
                  >
                    Start Your Journey
                  </Button>
                </div>
              ) : null}
            </div>
          )}

          {/* Notifications Tab */}
          {activeTab === 'notifications' && (
            <NotificationsTab />
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

          {/* Export Data Tab */}
          {activeTab === 'export' && (
            <div className="space-y-8">
              {/* Export Overview */}
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
                  <Download className="h-6 w-6 mr-2" style={{ color: '#4ECFBF' }} />
                  Export Your Learning Data
                </h3>
                
                <div className="bg-teal-50 border border-teal-200 rounded-xl p-4 mb-6">
                  <p className="text-sm text-teal-700">
                    <strong>📊 Data Available for Export:</strong> Download your complete learning journey including assessments, 
                    learning plans, conversation history, and detailed AI analysis. All data is available in multiple formats 
                    for your convenience.
                  </p>
                </div>

                {/* Data Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                  <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-3">
                      <BookOpen className="h-8 w-8 text-blue-500" />
                      <span className="text-2xl font-bold text-blue-600">{learningPlans.length}</span>
                    </div>
                    <h4 className="font-semibold text-blue-800">Learning Plans</h4>
                    <p className="text-sm text-blue-600">Assessment results & personalized plans</p>
                  </div>
                  
                  <div className="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-3">
                      <Mic className="h-8 w-8 text-green-500" />
                      <span className="text-2xl font-bold text-green-600">{conversationHistory.length}</span>
                    </div>
                    <h4 className="font-semibold text-green-800">Conversations</h4>
                    <p className="text-sm text-green-600">Practice sessions & AI analysis</p>
                  </div>
                  
                  <div className="bg-gradient-to-br from-purple-50 to-violet-50 border border-purple-200 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-3">
                      <Award className="h-8 w-8 text-purple-500" />
                      <span className="text-2xl font-bold text-purple-600">{assessmentLearningPairs.length}</span>
                    </div>
                    <h4 className="font-semibold text-purple-800">Assessments</h4>
                    <p className="text-sm text-purple-600">Skill evaluations & progress tracking</p>
                  </div>
                </div>

                {/* Export Options */}
                <div className="space-y-6">
                  {/* Learning Plans Export */}
                  <div className={`border rounded-xl p-6 ${learningPlans.length === 0 ? 'border-gray-300 bg-gray-50 opacity-60' : 'border-gray-200'}`}>
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${learningPlans.length === 0 ? 'bg-gray-200' : 'bg-blue-100'}`}>
                          <BookOpen className={`h-6 w-6 ${learningPlans.length === 0 ? 'text-gray-400' : 'text-blue-600'}`} />
                        </div>
                        <div>
                          <h4 className={`text-lg font-semibold ${learningPlans.length === 0 ? 'text-gray-500' : 'text-gray-800'}`}>Assessment & Learning Plans</h4>
                          <p className={`text-sm ${learningPlans.length === 0 ? 'text-gray-400' : 'text-gray-600'}`}>Complete assessment results, skill breakdowns, and personalized learning plans</p>
                        </div>
                      </div>
                      <Badge variant="secondary" className={learningPlans.length === 0 ? 'bg-gray-200 text-gray-500' : 'bg-blue-100 text-blue-700'}>
                        {learningPlans.length} plans
                      </Badge>
                    </div>
                    
                    <div className={`rounded-lg p-4 mb-4 ${learningPlans.length === 0 ? 'bg-gray-100' : 'bg-gray-50'}`}>
                      <h5 className={`font-medium mb-2 ${learningPlans.length === 0 ? 'text-gray-500' : 'text-gray-800'}`}>📋 Includes:</h5>
                      <ul className={`text-sm space-y-1 ${learningPlans.length === 0 ? 'text-gray-400' : 'text-gray-600'}`}>
                        <li>• Assessment scores and skill breakdowns (pronunciation, grammar, vocabulary, fluency)</li>
                        <li>• Personalized learning plans with goals and recommendations</li>
                        <li>• Progress tracking and level assessments</li>
                        <li>• Learning statistics and performance analytics</li>
                      </ul>
                    </div>
                    
                    {learningPlans.length === 0 ? (
                      <div className="text-center py-4">
                        <p className="text-sm text-gray-500 mb-3">No learning plans available to export</p>
                        <Button
                          onClick={() => router.push('/language-selection')}
                          variant="outline"
                          size="sm"
                          className="border-gray-300 text-gray-500 hover:bg-gray-100"
                        >
                          Create Your First Plan
                        </Button>
                      </div>
                    ) : (
                      <div className="flex flex-wrap gap-3">
                        <Button
                          onClick={() => handleDirectExport('learning-plans', 'pdf')}
                          disabled={exportLoading['learning-plans-pdf']}
                          className="bg-blue-600 hover:bg-blue-700 text-white"
                          size="sm"
                        >
                          {exportLoading['learning-plans-pdf'] ? (
                            <div className="animate-spin h-4 w-4 mr-2 border border-white border-t-transparent rounded-full"></div>
                          ) : (
                            <Download className="h-4 w-4 mr-2" />
                          )}
                          Export as PDF
                        </Button>
                      </div>
                    )}
                  </div>

                  {/* Conversation History Export */}
                  <div className={`border rounded-xl p-6 ${conversationHistory.length === 0 ? 'border-gray-300 bg-gray-50 opacity-60' : 'border-gray-200'}`}>
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${conversationHistory.length === 0 ? 'bg-gray-200' : 'bg-green-100'}`}>
                          <Mic className={`h-6 w-6 ${conversationHistory.length === 0 ? 'text-gray-400' : 'text-green-600'}`} />
                        </div>
                        <div>
                          <h4 className={`text-lg font-semibold ${conversationHistory.length === 0 ? 'text-gray-500' : 'text-gray-800'}`}>Conversation History & Analysis</h4>
                          <p className={`text-sm ${conversationHistory.length === 0 ? 'text-gray-400' : 'text-gray-600'}`}>Practice sessions, AI analysis, and detailed conversation insights</p>
                        </div>
                      </div>
                      <Badge variant="secondary" className={conversationHistory.length === 0 ? 'bg-gray-200 text-gray-500' : 'bg-green-100 text-green-700'}>
                        {conversationHistory.length} sessions
                      </Badge>
                    </div>
                    
                    <div className={`rounded-lg p-4 mb-4 ${conversationHistory.length === 0 ? 'bg-gray-100' : 'bg-gray-50'}`}>
                      <h5 className={`font-medium mb-2 ${conversationHistory.length === 0 ? 'text-gray-500' : 'text-gray-800'}`}>💬 Includes:</h5>
                      <ul className={`text-sm space-y-1 ${conversationHistory.length === 0 ? 'text-gray-400' : 'text-gray-600'}`}>
                        <li>• Complete conversation transcripts and session summaries</li>
                        <li>• Enhanced AI analysis with quality metrics and insights</li>
                        <li>• Breakthrough moments and areas for improvement</li>
                        <li>• Vocabulary highlights and personalized recommendations</li>
                      </ul>
                    </div>
                    
                    {conversationHistory.length === 0 ? (
                      <div className="text-center py-4">
                        <p className="text-sm text-gray-500 mb-3">No conversation history available to export</p>
                        <Button
                          onClick={() => router.push('/speech')}
                          variant="outline"
                          size="sm"
                          className="border-gray-300 text-gray-500 hover:bg-gray-100"
                        >
                          Start Practicing
                        </Button>
                      </div>
                    ) : (
                      <div className="flex flex-wrap gap-3">
                        <Button
                          onClick={() => handleDirectExport('conversations', 'pdf')}
                          disabled={exportLoading['conversations-pdf']}
                          className="bg-green-600 hover:bg-green-700 text-white"
                          size="sm"
                        >
                          {exportLoading['conversations-pdf'] ? (
                            <div className="animate-spin h-4 w-4 mr-2 border border-white border-t-transparent rounded-full"></div>
                          ) : (
                            <Download className="h-4 w-4 mr-2" />
                          )}
                          Export as PDF
                        </Button>
                        <Button
                          onClick={() => handleDirectExport('conversations', 'csv')}
                          disabled={exportLoading['conversations-csv']}
                          variant="outline"
                          className="border-green-200 text-green-600 hover:bg-green-50"
                          size="sm"
                        >
                          {exportLoading['conversations-csv'] ? (
                            <div className="animate-spin h-4 w-4 mr-2 border border-green-600 border-t-transparent rounded-full"></div>
                          ) : (
                            <Download className="h-4 w-4 mr-2" />
                          )}
                          Export as CSV
                        </Button>
                      </div>
                    )}
                  </div>

                  {/* Complete Data Export */}
                  <div className="border-2 border-teal-200 rounded-xl p-6 bg-gradient-to-br from-teal-50 to-cyan-50">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-12 h-12 bg-teal-100 rounded-xl flex items-center justify-center">
                          <Share2 className="h-6 w-6 text-teal-600" />
                        </div>
                        <div>
                          <h4 className="text-lg font-semibold text-gray-800">Complete Learning Data</h4>
                          <p className="text-sm text-gray-600">Everything in one comprehensive package - perfect for backup or analysis</p>
                        </div>
                      </div>
                      <Badge className="bg-teal-600 text-white">
                        Recommended
                      </Badge>
                    </div>
                    
                    <div className="bg-white rounded-lg p-4 mb-4 border border-teal-200">
                      <h5 className="font-medium text-gray-800 mb-2">📦 Complete Package Includes:</h5>
                      <ul className="text-sm text-gray-600 space-y-1">
                        <li>• All assessment results and learning plans (PDF + CSV)</li>
                        <li>• Complete conversation history and AI analysis (PDF + CSV)</li>
                        <li>• Professional course documents ready for sharing</li>
                        <li>• Organized in a convenient ZIP archive</li>
                      </ul>
                    </div>
                    
                    {(learningPlans.length === 0 && conversationHistory.length === 0) ? (
                      <div className="text-center py-4">
                        <p className="text-sm text-gray-500 mb-3">No data available to export</p>
                        <Button
                          onClick={() => router.push('/language-selection')}
                          variant="outline"
                          size="sm"
                          className="border-gray-300 text-gray-500 hover:bg-gray-100"
                        >
                          Start Your Learning Journey
                        </Button>
                      </div>
                    ) : (
                      <div className="flex flex-wrap gap-3">
                        <Button
                          onClick={() => handleDirectExport('data', 'zip')}
                          disabled={exportLoading['data-zip']}
                          className="text-white"
                          style={{ backgroundColor: '#4ECFBF' }}
                          size="sm"
                        >
                          {exportLoading['data-zip'] ? (
                            <div className="animate-spin h-4 w-4 mr-2 border border-white border-t-transparent rounded-full"></div>
                          ) : (
                            <Download className="h-4 w-4 mr-2" />
                          )}
                          Export Complete Package (ZIP)
                        </Button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Privacy Notice */}
                <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 mt-6">
                  <div className="flex items-start space-x-3">
                    <Lock className="h-5 w-5 text-gray-500 mt-0.5 flex-shrink-0" />
                    <div>
                      <h5 className="font-medium text-gray-800 mb-1">🔒 Privacy & Security</h5>
                      <p className="text-sm text-gray-600">
                        Your exported data contains only your personal learning information. No other user data is included. 
                        All exports are generated securely and are not stored on our servers after download.
                      </p>
                    </div>
                  </div>
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
                  <User className="h-6 w-6 mr-2" style={{ color: '#4ECFBF' }} />
                  Account Settings
                </h3>

                <div>
                  {error && (
                    <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-400 rounded-r-lg">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                          </svg>
                        </div>
                        <div className="ml-3">
                          <p className="text-sm text-red-700 font-medium">{error}</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {isSaved && (
                    <div className="mb-6 p-4 bg-green-50 border-l-4 border-green-400 rounded-r-lg">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <CheckCircle className="h-5 w-5 text-green-400" />
                        </div>
                        <div className="ml-3">
                          <p className="text-sm text-green-700 font-medium">Settings saved successfully!</p>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  <form onSubmit={handleSaveProfile} className="space-y-8">
                    {/* Personal Information Section */}
                    <div>
                      <div className="flex items-center space-x-2 mb-4">
                        <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                          <User className="h-4 w-4 text-blue-600" />
                        </div>
                        <h4 className="text-lg font-semibold text-gray-800">Personal Information</h4>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Full Name Field */}
                        <div className="group">
                          <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
                            <Edit3 className="h-4 w-4 mr-1 text-gray-400" />
                            Full Name
                          </label>
                          <div className="relative">
                            <Input 
                              type="text" 
                              className="w-full p-4 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white hover:border-gray-300 group-hover:shadow-sm"
                              value={name}
                              onChange={(e) => setName(e.target.value)}
                              placeholder="Enter your full name"
                            />
                            <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                              <div className="w-2 h-2 bg-green-400 rounded-full opacity-0 group-focus-within:opacity-100 transition-opacity"></div>
                            </div>
                          </div>
                        </div>

                        {/* Email Field */}
                        <div className="group">
                          <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
                            <Lock className="h-4 w-4 mr-1 text-gray-400" />
                            Email Address
                          </label>
                          <div className="relative">
                            <Input 
                              type="email" 
                              className="w-full p-4 border-2 border-gray-200 rounded-xl bg-gray-50 cursor-not-allowed text-gray-500"
                              value={email}
                              disabled
                            />
                            <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                              <Lock className="h-4 w-4 text-gray-400" />
                            </div>
                          </div>
                          <p className="text-xs text-gray-500 mt-2 flex items-center">
                            <svg className="h-3 w-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 00-1-1H9z" clipRule="evenodd" />
                            </svg>
                            Email cannot be changed
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Password Update Section */}
                    <div>
                      <div className="flex items-center space-x-2 mb-4">
                        <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
                          <Lock className="h-4 w-4 text-red-600" />
                        </div>
                        <h4 className="text-lg font-semibold text-gray-800">Password & Security</h4>
                      </div>

                      {passwordError && (
                        <div className="mb-4 p-3 bg-red-50 border-l-4 border-red-400 rounded-r-lg">
                          <p className="text-sm text-red-700">{passwordError}</p>
                        </div>
                      )}

                      {passwordSuccess && (
                        <div className="mb-4 p-3 bg-green-50 border-l-4 border-green-400 rounded-r-lg">
                          <p className="text-sm text-green-700">Password updated successfully!</p>
                        </div>
                      )}

                      <div className="space-y-4">
                        {/* All Password Fields in One Row */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div className="group">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              Current Password
                            </label>
                            <Input
                              type="password"
                              className="w-full p-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all duration-200"
                              value={currentPassword}
                              onChange={(e) => setCurrentPassword(e.target.value)}
                              placeholder="Current password"
                            />
                          </div>

                          <div className="group">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              New Password
                            </label>
                            <Input
                              type="password"
                              className="w-full p-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all duration-200"
                              value={newPassword}
                              onChange={(e) => setNewPassword(e.target.value)}
                              placeholder="New password"
                            />
                          </div>

                          <div className="group">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              Confirm New Password
                            </label>
                            <Input
                              type="password"
                              className="w-full p-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all duration-200"
                              value={confirmPassword}
                              onChange={(e) => setConfirmPassword(e.target.value)}
                              placeholder="Confirm password"
                            />
                          </div>
                        </div>

                        <div className="text-xs text-gray-500">
                          Password must be at least 6 characters long. Leave blank to keep current password.
                        </div>
                      </div>
                    </div>

                    {/* Single Action Button */}
                    <div className="flex items-center justify-between pt-6 border-t border-gray-200">
                      <div className="text-sm text-gray-500">
                        Save your profile changes and update password if provided
                      </div>
                      
                      <button
                        type="submit"
                        disabled={isLoading || isPasswordLoading}
                        className="relative px-8 py-3 bg-white border-2 rounded-xl font-medium text-white overflow-hidden transition-all duration-300 hover:shadow-lg focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                        style={{ 
                          borderColor: '#4ECFBF',
                          backgroundColor: (isLoading || isPasswordLoading) ? '#9CA3AF' : '#4ECFBF'
                        }}
                      >
                        <div className="relative z-10 flex items-center">
                          {(isLoading || isPasswordLoading) ? (
                            <>
                              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                              Saving Changes...
                            </>
                          ) : (isSaved || passwordSuccess) ? (
                            <>
                              <CheckCircle className="h-5 w-5 mr-2" />
                              Changes Saved!
                            </>
                          ) : (
                            <>
                              <Settings className="h-5 w-5 mr-2" />
                              Save Changes
                            </>
                          )}
                        </div>
                        
                        {/* Animated background effect */}
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
                      </button>
                    </div>
                  </form>
                </div>
              </div>

              {/* Subscription Management */}
              <SubscriptionManagement />
              
              {/* Dangerous Area */}
              <div className="bg-white rounded-2xl shadow-lg p-6 border-2 border-red-100">
                <h3 className="text-xl font-bold text-red-600 mb-6 flex items-center">
                  <Trash2 className="h-6 w-6 mr-2" />
                  Dangerous Area
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

                  <div className="bg-red-100 rounded-xl p-4 border border-red-200">
                    <h4 className="font-medium text-red-800 mb-2">Delete Account</h4>
                    <p className="text-sm text-red-600 mb-4">
                      Permanently delete your account and all associated data. This action cannot be undone.
                    </p>
                    <button 
                      onClick={handleDeleteAccount}
                      className="bg-red-700 hover:bg-red-800 text-white py-2 px-4 rounded-lg font-medium transition-all text-sm"
                    >
                      Delete Account
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Enhanced Analysis Modal */}
      {showEnhancedAnalysis && selectedAnalysis && selectedSessionInfo && (
        <EnhancedAnalysisModal
          isOpen={showEnhancedAnalysis}
          onClose={() => setShowEnhancedAnalysis(false)}
          analysis={selectedAnalysis}
          sessionInfo={selectedSessionInfo}
        />
      )}

      {/* Export Modal */}
      {showExportModal && (
        <ExportModal
          isOpen={showExportModal}
          onClose={() => setShowExportModal(false)}
          userName={user?.name || 'User'}
        />
      )}

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

      {/* Delete Account Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <div className="text-center">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Trash2 className="h-8 w-8 text-red-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-800 mb-2">Delete Account</h3>
              <p className="text-gray-600 mb-6">
                Are you sure you want to permanently delete your account? This action cannot be undone and will remove all your learning data, progress, and subscription information.
              </p>
              
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-6">
                <p className="text-sm text-red-700 font-medium">
                  ⚠️ This will permanently deactivate your account and you will lose access to all your data.
                </p>
              </div>
              
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  disabled={isDeleting}
                  className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 py-3 px-4 rounded-xl font-medium transition-all disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteAccountConfirm}
                  disabled={isDeleting}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white py-3 px-4 rounded-xl font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isDeleting ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Deleting...
                    </>
                  ) : (
                    'Delete Account'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Payment Processing Modal */}
      <PaymentProcessingModal
        isOpen={showPaymentProcessing}
        onComplete={handlePaymentProcessingComplete}
        planName={planInfo.name}
        userEmail={user?.email}
      />
    </ProtectedRoute>
  );
}
