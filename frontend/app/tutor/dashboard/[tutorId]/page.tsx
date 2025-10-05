'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Comprehensive Learner Modal Component
interface ComprehensiveLearnerModalProps {
  learner: Learner;
  learnerDetails: any;
  loadingDetails: boolean;
  onClose: () => void;
}

const ComprehensiveLearnerModal: React.FC<ComprehensiveLearnerModalProps> = ({
  learner,
  learnerDetails,
  loadingDetails,
  onClose
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'plans' | 'sessions' | 'insights'>('overview');
  const [expandedPlan, setExpandedPlan] = useState<string | null>(null);
  const [expandedSession, setExpandedSession] = useState<string | null>(null);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl max-w-6xl w-full my-8">
        {/* Header with Gradient */}
        <div className="p-6 bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] rounded-t-2xl">
          <div className="flex justify-between items-start">
            <div className="text-white">
              <h2 className="text-3xl font-bold mb-2">{learner.name}</h2>
              {learnerDetails?.profile && (
                <div className="flex items-center gap-6 text-white/90 text-sm">
                  <span>📧 {learnerDetails.profile.email}</span>
                  <span>📚 {learnerDetails.profile.total_sessions} sessions</span>
                  <span>⏱️ {learnerDetails.profile.total_minutes} minutes</span>
                  <span>🌍 {learnerDetails.profile.languages_studied?.join(', ') || 'No languages'}</span>
                </div>
              )}
            </div>
            <button
              onClick={onClose}
              className="text-white hover:bg-white/20 rounded-lg p-2 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b bg-white">
          <nav className="flex px-6">
            <button
              onClick={() => setActiveTab('overview')}
              className={`py-4 px-6 font-medium border-b-2 transition-colors ${
                activeTab === 'overview'
                  ? 'border-[#4ECFBF] text-[#4ECFBF]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              📊 Overview
            </button>
            <button
              onClick={() => setActiveTab('plans')}
              className={`py-4 px-6 font-medium border-b-2 transition-colors ${
                activeTab === 'plans'
                  ? 'border-[#4ECFBF] text-[#4ECFBF]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              📚 Learning Plans ({learnerDetails?.all_learning_plans?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('sessions')}
              className={`py-4 px-6 font-medium border-b-2 transition-colors ${
                activeTab === 'sessions'
                  ? 'border-[#4ECFBF] text-[#4ECFBF]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              💬 Practice Sessions ({learnerDetails?.practice_sessions?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('insights')}
              className={`py-4 px-6 font-medium border-b-2 transition-colors ${
                activeTab === 'insights'
                  ? 'border-[#4ECFBF] text-[#4ECFBF]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              🤖 AI Insights
            </button>
          </nav>
        </div>

        {/* Content */}
        <div className="p-6 max-h-[60vh] overflow-y-auto bg-gray-50">
          {loadingDetails ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-[#4ECFBF]"></div>
                <p className="mt-4 text-gray-600">Loading detailed progress...</p>
              </div>
            </div>
          ) : !learnerDetails ? (
            <div className="text-center py-12">
              <p className="text-gray-600">Failed to load learner details</p>
            </div>
          ) : (
            <>
              {/* Overview Tab */}
              {activeTab === 'overview' && learnerDetails.profile && (
                <div className="space-y-6">
                  {/* Quick Stats Cards */}
                  <div className="grid grid-cols-4 gap-4">
                    <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
                      <div className="text-sm text-gray-600">Total Sessions</div>
                      <div className="text-2xl font-bold text-[#4ECFBF]">{learnerDetails.profile.total_sessions}</div>
                    </div>
                    <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
                      <div className="text-sm text-gray-600">Total Minutes</div>
                      <div className="text-2xl font-bold text-[#4ECFBF]">{learnerDetails.profile.total_minutes}</div>
                    </div>
                    <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
                      <div className="text-sm text-gray-600">Learning Plans</div>
                      <div className="text-2xl font-bold text-[#4ECFBF]">{learnerDetails.all_learning_plans?.length || 0}</div>
                    </div>
                    <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
                      <div className="text-sm text-gray-600">Practice Sessions</div>
                      <div className="text-2xl font-bold text-[#4ECFBF]">{learnerDetails.practice_sessions?.length || 0}</div>
                    </div>
                  </div>

                  {/* Languages Overview */}
                  {learnerDetails.all_learning_plans && learnerDetails.all_learning_plans.length > 0 && (
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                      <h3 className="text-lg font-bold text-gray-900 mb-4">🌍 Languages Progress</h3>
                      <div className="space-y-4">
                        {learnerDetails.all_learning_plans.map((plan: any) => (
                          <div key={plan.id} className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <span className="text-lg font-bold text-gray-900">
                                  {plan.language?.charAt(0).toUpperCase() + plan.language?.slice(1)}
                                </span>
                                <span className="px-2 py-1 bg-white rounded-full text-sm font-medium text-[#4ECFBF]">
                                  {plan.proficiency_level}
                                </span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-3">
                                <div
                                  className="bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] h-3 rounded-full transition-all"
                                  style={{ width: `${plan.progress_percentage || 0}%` }}
                                ></div>
                              </div>
                            </div>
                            <div className="ml-6 text-right">
                              <div className="text-2xl font-bold text-[#4ECFBF]">{plan.progress_percentage?.toFixed(0) || 0}%</div>
                              <div className="text-sm text-gray-600">{plan.completed_sessions}/{plan.total_sessions} sessions</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Learning Plans Tab */}
              {activeTab === 'plans' && (
                <div className="space-y-4">
                  {learnerDetails.all_learning_plans && learnerDetails.all_learning_plans.length > 0 ? (
                    learnerDetails.all_learning_plans.map((plan: any) => (
                      <div key={plan.id} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                        {/* Plan Header */}
                        <div className="p-6 bg-gradient-to-r from-green-50 to-emerald-50">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-3">
                                <h4 className="text-xl font-bold text-gray-900">
                                  {plan.language?.charAt(0).toUpperCase() + plan.language?.slice(1)} {plan.proficiency_level}
                                </h4>
                                {plan.assessment_data?.overall_score && (
                                  <span className="px-3 py-1 bg-white rounded-full text-sm font-medium text-[#4ECFBF]">
                                    Score: {plan.assessment_data.overall_score}/100
                                  </span>
                                )}
                              </div>
                              <div className="grid grid-cols-3 gap-4 mb-3">
                                <div>
                                  <div className="text-sm text-gray-600">Progress</div>
                                  <div className="text-lg font-bold text-gray-900">{plan.progress_percentage?.toFixed(1) || 0}%</div>
                                </div>
                                <div>
                                  <div className="text-sm text-gray-600">Sessions</div>
                                  <div className="text-lg font-bold text-gray-900">{plan.completed_sessions || 0}/{plan.total_sessions || 16}</div>
                                </div>
                                <div>
                                  <div className="text-sm text-gray-600">Practice Time</div>
                                  <div className="text-lg font-bold text-gray-900">{plan.practice_minutes_used || 0}/{plan.total_practice_minutes || 80} min</div>
                                </div>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-3">
                                <div
                                  className="bg-gradient-to-r from-green-500 to-emerald-500 h-3 rounded-full"
                                  style={{ width: `${plan.progress_percentage || 0}%` }}
                                ></div>
                              </div>
                            </div>
                            <button
                              onClick={() => setExpandedPlan(expandedPlan === plan.id ? null : plan.id)}
                              className="ml-4 px-4 py-2 bg-white text-[#4ECFBF] rounded-lg hover:bg-[#4ECFBF] hover:text-white transition-colors font-medium border border-[#4ECFBF]"
                            >
                              {expandedPlan === plan.id ? 'Hide' : 'Show'} Details
                            </button>
                          </div>
                        </div>

                        {/* Expanded Details */}
                        {expandedPlan === plan.id && (
                          <div className="p-6 bg-white border-t space-y-6">
                            {/* Assessment Scores */}
                            {plan.assessment_data?.skill_scores && (
                              <div>
                                <h5 className="font-bold text-gray-900 mb-3">📊 Skill Assessment</h5>
                                <div className="grid grid-cols-4 gap-4">
                                  {Object.entries(plan.assessment_data.skill_scores).map(([skill, score]: [string, any]) => (
                                    <div key={skill} className="bg-gray-50 p-4 rounded-lg text-center">
                                      <div className="text-sm text-gray-600 capitalize mb-1">{skill}</div>
                                      <div className="text-2xl font-bold text-[#4ECFBF]">{score}/100</div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Strengths & Improvements */}
                            <div className="grid grid-cols-2 gap-6">
                              {plan.assessment_data?.strengths && plan.assessment_data.strengths.length > 0 && (
                                <div>
                                  <h5 className="font-bold text-green-900 mb-3">✅ Strengths</h5>
                                  <ul className="space-y-2">
                                    {plan.assessment_data.strengths.map((strength: string, idx: number) => (
                                      <li key={idx} className="text-sm text-gray-700 bg-green-50 p-3 rounded-lg">
                                        • {strength}
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              {plan.assessment_data?.areas_for_improvement && plan.assessment_data.areas_for_improvement.length > 0 && (
                                <div>
                                  <h5 className="font-bold text-orange-900 mb-3">🎯 Areas for Improvement</h5>
                                  <ul className="space-y-2">
                                    {plan.assessment_data.areas_for_improvement.map((area: string, idx: number) => (
                                      <li key={idx} className="text-sm text-gray-700 bg-orange-50 p-3 rounded-lg">
                                        • {area}
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>

                            {/* Learning Objectives */}
                            {plan.plan_content?.learning_objectives && plan.plan_content.learning_objectives.length > 0 && (
                              <div>
                                <h5 className="font-bold text-gray-900 mb-3">🎓 Learning Objectives</h5>
                                <ul className="space-y-2">
                                  {plan.plan_content.learning_objectives.map((obj: string, idx: number) => (
                                    <li key={idx} className="text-sm text-gray-700 bg-blue-50 p-3 rounded-lg">
                                      {idx + 1}. {obj}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {/* Session Summaries */}
                            {plan.session_summaries && plan.session_summaries.length > 0 && (
                              <div>
                                <h5 className="font-bold text-gray-900 mb-3">📝 Session Summaries</h5>
                                <div className="space-y-2">
                                  {plan.session_summaries.map((summary: string, idx: number) => (
                                    <div key={idx} className="bg-purple-50 p-4 rounded-lg">
                                      <div className="font-medium text-purple-900 mb-1">Session {idx + 1}</div>
                                      <div className="text-sm text-gray-700">{summary}</div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="bg-white p-12 rounded-xl text-center">
                      <div className="text-4xl mb-4">📚</div>
                      <p className="text-gray-600">No learning plans found for this learner.</p>
                    </div>
                  )}
                </div>
              )}

              {/* Practice Sessions Tab */}
              {activeTab === 'sessions' && (
                <div className="space-y-4">
                  {learnerDetails.practice_sessions && learnerDetails.practice_sessions.length > 0 ? (
                    learnerDetails.practice_sessions.map((session: any, idx: number) => (
                      <div key={session.id} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                        {/* Session Header */}
                        <div className="p-6 bg-gradient-to-r from-purple-50 to-pink-50">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <span className="text-lg font-bold text-gray-900">
                                  Session #{idx + 1}
                                </span>
                                <span className="px-3 py-1 bg-white rounded-full text-sm font-medium text-purple-700">
                                  {session.language} {session.level}
                                </span>
                              </div>
                              <div className="grid grid-cols-4 gap-4 text-sm">
                                <div>
                                  <div className="text-gray-600">Date</div>
                                  <div className="font-medium text-gray-900">
                                    {session.created_at ? new Date(session.created_at).toLocaleDateString() : 'N/A'}
                                  </div>
                                </div>
                                <div>
                                  <div className="text-gray-600">Duration</div>
                                  <div className="font-medium text-gray-900">{session.duration_minutes || 0} min</div>
                                </div>
                                <div>
                                  <div className="text-gray-600">Messages</div>
                                  <div className="font-medium text-gray-900">{session.message_count || 0}</div>
                                </div>
                                <div>
                                  <div className="text-gray-600">Overall Score</div>
                                  <div className="font-medium text-gray-900">N/A</div>
                                </div>
                              </div>
                            </div>
                            <button
                              onClick={() => setExpandedSession(expandedSession === session.id ? null : session.id)}
                              className="ml-4 px-4 py-2 bg-white text-purple-700 rounded-lg hover:bg-purple-700 hover:text-white transition-colors font-medium border border-purple-700"
                            >
                              {expandedSession === session.id ? 'Hide' : 'Show'} Details
                            </button>
                          </div>
                        </div>

                        {/* Expanded Session Details */}
                        {expandedSession === session.id && (
                          <div className="p-6 bg-white border-t space-y-4">
                            <div className="bg-gray-50 p-4 rounded-lg">
                              <div className="text-sm text-gray-600">Full conversation details would be displayed here with message previews and analysis.</div>
                            </div>
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="bg-white p-12 rounded-xl text-center">
                      <div className="text-4xl mb-4">💬</div>
                      <p className="text-gray-600">No practice sessions found for this learner.</p>
                    </div>
                  )}
                </div>
              )}

              {/* AI Insights Tab */}
              {activeTab === 'insights' && learnerDetails.ai_insights && (
                <div className="space-y-6">
                  {/* Overall Summary */}
                  <div className="bg-gradient-to-r from-indigo-50 to-purple-50 p-6 rounded-xl border border-indigo-200">
                    <h3 className="text-lg font-bold text-gray-900 mb-3">🤖 AI Analysis Summary</h3>
                    <p className="text-gray-700 leading-relaxed">{learnerDetails.ai_insights.overall_summary}</p>
                  </div>

                  {/* Learning Metrics */}
                  <div className="grid grid-cols-2 gap-6">
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                      <h4 className="font-bold text-gray-900 mb-4">📚 Learning Style</h4>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Preferred Time</span>
                          <span className="font-medium text-gray-900 capitalize">
                            {learnerDetails.ai_insights.learning_style?.preferred_time}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Sessions/Week</span>
                          <span className="font-medium text-gray-900">
                            {learnerDetails.ai_insights.learning_style?.sessions_per_week}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                      <h4 className="font-bold text-gray-900 mb-4">📈 Progress Rate</h4>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Rate</span>
                          <span className="font-medium text-gray-900 capitalize">
                            {learnerDetails.ai_insights.progress_rate?.rate}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Description</span>
                          <span className="font-medium text-gray-900 capitalize">
                            {learnerDetails.ai_insights.progress_rate?.description}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Recommendations */}
                  {learnerDetails.ai_insights.recommendations && learnerDetails.ai_insights.recommendations.length > 0 && (
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                      <h4 className="font-bold text-gray-900 mb-4">💡 Tutor Recommendations</h4>
                      <ul className="space-y-3">
                        {learnerDetails.ai_insights.recommendations.map((rec: string, idx: number) => (
                          <li key={idx} className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg">
                            <span className="text-yellow-600 font-bold">{idx + 1}.</span>
                            <span className="text-gray-700">{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

interface LearningPlan {
  id: string;
  language: string;
  proficiency_level: string;
  progress_percentage: number;
  progress_status: 'on_track' | 'at_risk' | 'inactive';
  last_activity_date: string | null;
  days_since_activity: number;
  completed_sessions: number;
  total_sessions: number;
  assessment_score: number;
  last_session_summary: string | null;
  next_focus_area: string;
}

interface Learner {
  id: string;
  user_id: string;
  name: string;
  email: string;
  enrolled_at: string;
  consent_given: boolean;
  learning_plans: LearningPlan[];
}

interface Analytics {
  total_assigned_learners: number;
  active_learners: number;
  at_risk_learners: number;
  inactive_learners: number;
  average_progress: number;
  total_sessions_completed: number;
  total_minutes_practiced: number;
  languages_taught: string[];
  level_distribution: Record<string, number>;
}

export default function TutorDashboardPage() {
  const router = useRouter();
  const params = useParams();
  const tutorId = params.tutorId as string;

  const [tutorName, setTutorName] = useState('');
  const [learners, setLearners] = useState<Learner[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filters
  const [languageFilter, setLanguageFilter] = useState('');
  const [levelFilter, setLevelFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLearner, setSelectedLearner] = useState<Learner | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [learnerDetails, setLearnerDetails] = useState<any>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const itemsPerPage = 10;

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem('tutorToken');
    const storedTutorId = localStorage.getItem('tutorId');
    const storedTutorName = localStorage.getItem('tutorName');

    if (!token || storedTutorId !== tutorId) {
      router.push('/tutor/login');
      return;
    }

    setTutorName(storedTutorName || 'Tutor');
    
    // Load dashboard data
    loadDashboardData(token);
    loadAnalytics(token);
  }, [tutorId, router]);

  // Auto-apply filters whenever they change (instant filtering)
  useEffect(() => {
    const token = localStorage.getItem('tutorToken');
    if (token) {
      loadDashboardData(token);
    }
  }, [languageFilter, levelFilter, statusFilter, searchQuery, tutorName]);

  const loadDashboardData = async (token: string, page: number = 1) => {
    try {
      setLoading(true);
      setError('');

      const queryParams = new URLSearchParams();
      if (languageFilter) queryParams.append('language', languageFilter);
      if (levelFilter) queryParams.append('level', levelFilter);
      if (statusFilter) queryParams.append('status', statusFilter);
      if (searchQuery) queryParams.append('search', searchQuery);
      queryParams.append('page', page.toString());
      queryParams.append('per_page', itemsPerPage.toString());

      const url = `${API_BASE_URL}/api/v1/tutor/dashboard/${tutorId}/learners${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          router.push('/tutor/login');
          return;
        }
        throw new Error('Failed to load learners');
      }

      const data = await response.json();
      setLearners(data.learners || []);
      
      // Update pagination state if backend provides it
      if (data.pagination) {
        setTotalPages(data.pagination.total_pages || 1);
        setTotalItems(data.pagination.total_items || 0);
        setCurrentPage(data.pagination.current_page || 1);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const loadAnalytics = async (token: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/tutor/dashboard/${tutorId}/analytics`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (err) {
      console.error('Failed to load analytics:', err);
    }
  };

  const handleViewDetails = async (learner: Learner) => {
    if (!learner.consent_given) {
      alert('This learner has not provided consent to view detailed progress.');
      return;
    }

    setSelectedLearner(learner);
    setShowDetailModal(true);
    setLoadingDetails(true);

    try {
      const token = localStorage.getItem('tutorToken');
      const response = await fetch(
        `${API_BASE_URL}/api/v1/tutor/dashboard/${tutorId}/learner/${learner.user_id}/details`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setLearnerDetails(data);
      } else {
        throw new Error('Failed to load learner details');
      }
    } catch (err: any) {
      alert(err.message || 'Failed to load learner details');
      setShowDetailModal(false);
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('tutorToken');
    localStorage.removeItem('tutorId');
    localStorage.removeItem('tutorName');
    localStorage.removeItem('tutorEmail');
    localStorage.removeItem('institutionId');
    router.push('/tutor/login');
  };

  const clearFilters = () => {
    setLanguageFilter('');
    setLevelFilter('');
    setStatusFilter('');
    setSearchQuery('');
    const token = localStorage.getItem('tutorToken');
    if (token) {
      setTimeout(() => loadDashboardData(token), 100);
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'on_track':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'at_risk':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'inactive':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'on_track':
        return 'On Track';
      case 'at_risk':
        return 'At Risk';
      case 'inactive':
        return 'Inactive';
      default:
        return status;
    }
  };

  const handlePageChange = (newPage: number) => {
    const token = localStorage.getItem('tutorToken');
    if (token) {
      setCurrentPage(newPage);
      loadDashboardData(token, newPage);
    }
  };

  // Pagination Component
  const Pagination = () => {
    if (totalPages <= 1) return null;

    const getPageNumbers = () => {
      const pages = [];
      const showEllipsis = totalPages > 7;
      
      if (!showEllipsis) {
        for (let i = 1; i <= totalPages; i++) {
          pages.push(i);
        }
      } else {
        if (currentPage <= 3) {
          pages.push(1, 2, 3, 4, '...', totalPages);
        } else if (currentPage >= totalPages - 2) {
          pages.push(1, '...', totalPages - 3, totalPages - 2, totalPages - 1, totalPages);
        } else {
          pages.push(1, '...', currentPage - 1, currentPage, currentPage + 1, '...', totalPages);
        }
      }
      
      return pages;
    };

    return (
      <div className="flex items-center justify-between px-6 py-4 border-t bg-gray-50">
        <div className="text-sm text-gray-700">
          Showing <span className="font-medium">{(currentPage - 1) * itemsPerPage + 1}</span> to{' '}
          <span className="font-medium">{Math.min(currentPage * itemsPerPage, totalItems)}</span> of{' '}
          <span className="font-medium">{totalItems}</span> results
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className={`px-3 py-2 rounded-lg font-medium transition-all ${
              currentPage === 1
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-white text-gray-700 hover:bg-[#4ECFBF] hover:text-white border'
            }`}
          >
            Previous
          </button>
          
          <div className="flex space-x-1">
            {getPageNumbers().map((page, index) => (
              page === '...' ? (
                <span key={`ellipsis-${index}`} className="px-3 py-2 text-gray-500">...</span>
              ) : (
                <button
                  key={page}
                  onClick={() => handlePageChange(page as number)}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${
                    currentPage === page
                      ? 'bg-[#4ECFBF] text-white shadow-md'
                      : 'bg-white text-gray-700 hover:bg-gray-100 border'
                  }`}
                >
                  {page}
                </button>
              )
            ))}
          </div>
          
          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className={`px-3 py-2 rounded-lg font-medium transition-all ${
              currentPage === totalPages
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-white text-gray-700 hover:bg-[#4ECFBF] hover:text-white border'
            }`}
          >
            Next
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 pt-20">
      {/* Removed duplicate header - using global navigation instead */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Analytics Cards */}
        {analytics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm font-medium text-gray-600">Total Learners</div>
              <div className="text-3xl font-bold text-gray-900 mt-2">{analytics.total_assigned_learners}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm font-medium text-gray-600">On Track</div>
              <div className="text-3xl font-bold text-green-600 mt-2">{analytics.active_learners}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm font-medium text-gray-600">At Risk</div>
              <div className="text-3xl font-bold text-yellow-600 mt-2">{analytics.at_risk_learners}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm font-medium text-gray-600">Avg Progress</div>
              <div className="text-3xl font-bold text-blue-600 mt-2">{analytics.average_progress.toFixed(1)}%</div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Filters</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Name or email..."
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Language</label>
              <select
                value={languageFilter}
                onChange={(e) => setLanguageFilter(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
              >
                <option value="">All Languages</option>
                <option value="English">English</option>
                <option value="Dutch">Dutch</option>
                <option value="Spanish">Spanish</option>
                <option value="French">French</option>
                <option value="German">German</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Level</label>
              <select
                value={levelFilter}
                onChange={(e) => setLevelFilter(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
              >
                <option value="">All Levels</option>
                <option value="A1">A1</option>
                <option value="A2">A2</option>
                <option value="B1">B1</option>
                <option value="B2">B2</option>
                <option value="C1">C1</option>
                <option value="C2">C2</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
              >
                <option value="">All Status</option>
                <option value="on_track">On Track</option>
                <option value="at_risk">At Risk</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
          </div>
          {(searchQuery || languageFilter || levelFilter || statusFilter) && (
            <div className="flex gap-3 mt-4">
              <button
                onClick={clearFilters}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
              >
                ✕ Clear All Filters
              </button>
            </div>
          )}
        </div>

        {/* ENRICHED LEARNERS TABLE */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="p-6 border-b bg-gradient-to-r from-[#4ECFBF]/5 to-[#3a9e92]/5">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-xl font-bold text-gray-900">📚 Assigned Learners</h2>
                <p className="text-sm text-gray-600 mt-1">
                  {learners.length} learner{learners.length !== 1 ? 's' : ''} • 
                  Track progress, assess performance, and monitor engagement
                </p>
              </div>
            </div>
          </div>

          {loading ? (
            <div className="p-12 text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-[#4ECFBF]"></div>
              <p className="mt-4 text-gray-600">Loading learners...</p>
            </div>
          ) : error ? (
            <div className="p-12 text-center">
              <p className="text-red-600">{error}</p>
            </div>
          ) : learners.length === 0 ? (
            <div className="p-12 text-center">
              <div className="text-4xl mb-4">🎓</div>
              <p className="text-gray-600">No learners found matching your filters.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b-2 border-gray-200">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                      Learner Info
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                      Language & Level
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                      Progress & Sessions
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                      Performance
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                      Activity Status
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {learners.map((learner, index) => {
                    const plan = learner.learning_plans[0];
                    if (!plan) return null;

                    // Calculate status indicators
                    const isOnTrack = plan.progress_status === 'on_track';
                    const isAtRisk = plan.progress_status === 'at_risk';
                    const isInactive = plan.progress_status === 'inactive';
                    const hasConsent = learner.consent_given;

                    return (
                      <tr 
                        key={learner.id}
                        className={`hover:bg-gradient-to-r hover:from-[#4ECFBF]/5 hover:to-transparent transition-all ${
                          index % 2 === 0 ? 'bg-white' : 'bg-gray-50/30'
                        }`}
                      >
                        {/* Learner Info Column */}
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-4">
                            {/* Avatar with Status Ring */}
                            <div className="relative">
                              <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-md ${
                                isOnTrack ? 'bg-gradient-to-br from-green-400 to-green-600' :
                                isAtRisk ? 'bg-gradient-to-br from-yellow-400 to-orange-500' :
                                'bg-gradient-to-br from-gray-400 to-gray-600'
                              }`}>
                                {learner.name.charAt(0).toUpperCase()}
                              </div>
                              {/* Status Dot */}
                              <div className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-white ${
                                isOnTrack ? 'bg-green-500' :
                                isAtRisk ? 'bg-yellow-500' :
                                'bg-gray-400'
                              }`} title={getStatusLabel(plan.progress_status)}></div>
                            </div>
                            
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <p className="font-bold text-gray-900 truncate">{learner.name}</p>
                                {!hasConsent && (
                                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700 border border-red-200" title="No consent given">
                                    🔒
                                  </span>
                                )}
                              </div>
                              <p className="text-sm text-gray-600 truncate">{learner.email}</p>
                              <p className="text-xs text-gray-500 mt-1">
                                Enrolled: {new Date(learner.enrolled_at).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                        </td>

                        {/* Language & Level Column */}
                        <td className="px-6 py-4">
                          <div className="space-y-2">
                            <div className="flex items-center gap-2">
                              <span className="text-2xl">
                                {plan.language.toLowerCase() === 'english' ? '🇬🇧' :
                                 plan.language.toLowerCase() === 'dutch' ? '🇳🇱' :
                                 plan.language.toLowerCase() === 'spanish' ? '🇪🇸' :
                                 plan.language.toLowerCase() === 'french' ? '🇫🇷' :
                                 plan.language.toLowerCase() === 'german' ? '🇩🇪' : '🌍'}
                              </span>
                              <div>
                                <div className="font-medium text-gray-900 capitalize">{plan.language}</div>
                                <div className="text-xs text-gray-500">Target Language</div>
                              </div>
                            </div>
                            <div className="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white shadow-sm">
                              Level {plan.proficiency_level}
                            </div>
                          </div>
                        </td>

                        {/* Progress & Sessions Column */}
                        <td className="px-6 py-4">
                          <div className="space-y-3">
                            {/* Progress Bar */}
                            <div>
                              <div className="flex justify-between items-center mb-1">
                                <span className="text-xs font-medium text-gray-700">Plan Progress</span>
                                <span className="text-xs font-bold text-[#4ECFBF]">{plan.progress_percentage.toFixed(0)}%</span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden shadow-inner">
                                <div
                                  className={`h-3 rounded-full transition-all duration-500 ${
                                    isOnTrack ? 'bg-gradient-to-r from-green-400 to-green-600' :
                                    isAtRisk ? 'bg-gradient-to-r from-yellow-400 to-orange-500' :
                                    'bg-gradient-to-r from-gray-400 to-gray-500'
                                  }`}
                                  style={{ width: `${plan.progress_percentage}%` }}
                                ></div>
                              </div>
                            </div>

                            {/* Session Stats */}
                            <div className="flex items-center justify-between p-2 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg">
                              <div className="text-center flex-1">
                                <div className="text-xs text-gray-600">Completed</div>
                                <div className="text-lg font-bold text-blue-700">{plan.completed_sessions}</div>
                              </div>
                              <div className="text-gray-400">/</div>
                              <div className="text-center flex-1">
                                <div className="text-xs text-gray-600">Total</div>
                                <div className="text-lg font-bold text-gray-700">{plan.total_sessions}</div>
                              </div>
                            </div>
                          </div>
                        </td>

                        {/* Performance Column */}
                        <td className="px-6 py-4">
                          <div className="space-y-2">
                            {/* Assessment Score */}
                            {plan.assessment_score > 0 ? (
                              <div className="flex flex-col items-center justify-center p-3 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg">
                                <div className="text-xs text-gray-600 mb-1">Assessment Score</div>
                                <div className={`text-3xl font-bold ${
                                  plan.assessment_score >= 80 ? 'text-green-600' :
                                  plan.assessment_score >= 60 ? 'text-yellow-600' :
                                  'text-red-600'
                                }`}>
                                  {plan.assessment_score}/100
                                </div>
                              </div>
                            ) : (
                              <div className="text-sm text-gray-500 italic p-3 bg-gray-50 rounded-lg text-center">
                                No assessment yet
                              </div>
                            )}

                            {/* Next Focus Area */}
                            <div className="text-xs p-2 bg-yellow-50 border border-yellow-200 rounded-lg">
                              <div className="font-semibold text-yellow-900 mb-1">🎯 Next Focus:</div>
                              <div className="text-gray-700 line-clamp-2">{plan.next_focus_area}</div>
                            </div>
                          </div>
                        </td>

                        {/* Activity Status Column */}
                        <td className="px-6 py-4">
                          <div className="space-y-2">
                            {/* Status Badge */}
                            <div className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-bold shadow-sm ${
                              isOnTrack ? 'bg-green-100 text-green-800 border-2 border-green-300' :
                              isAtRisk ? 'bg-yellow-100 text-yellow-800 border-2 border-yellow-300' :
                              'bg-gray-100 text-gray-800 border-2 border-gray-300'
                            }`}>
                              {isOnTrack && '✅ On Track'}
                              {isAtRisk && '⚠️ At Risk'}
                              {isInactive && 'Inactive'}
                            </div>

                            {/* Last Activity */}
                            <div className="text-xs space-y-1">
                              <div className="flex items-center gap-1 text-gray-600">
                                <span>📅</span>
                                <span>Last Active:</span>
                              </div>
                              <div className="font-medium text-gray-900">
                                {plan.last_activity_date 
                                  ? new Date(plan.last_activity_date).toLocaleDateString()
                                  : 'No activity'
                                }
                              </div>
                              {plan.days_since_activity !== undefined && plan.days_since_activity < 999 && (
                                <div className={`text-xs ${
                                  plan.days_since_activity <= 3 ? 'text-green-600' :
                                  plan.days_since_activity <= 7 ? 'text-yellow-600' :
                                  'text-red-600'
                                }`}>
                                  {plan.days_since_activity === 0 ? 'Today!' :
                                   plan.days_since_activity === 1 ? 'Yesterday' :
                                   `${plan.days_since_activity} days ago`}
                                </div>
                              )}
                            </div>
                          </div>
                        </td>

                        {/* Actions Column */}
                        <td className="px-6 py-4">
                          <button
                            onClick={() => handleViewDetails(learner)}
                            disabled={!hasConsent}
                            className={`w-full px-4 py-2.5 rounded-lg font-medium transition-all shadow-sm whitespace-nowrap ${
                              hasConsent
                                ? 'bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white hover:shadow-md hover:scale-105 transform'
                                : 'bg-gray-200 text-gray-500 cursor-not-allowed'
                            }`}
                            title={hasConsent ? 'View detailed progress' : 'Learner has not given consent'}
                          >
                            {hasConsent ? 'View Details' : 'No Access'}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
          
          {/* Pagination */}
          {!loading && !error && learners.length > 0 && <Pagination />}
        </div>
      </div>

      {/* COMPREHENSIVE LEARNER PROGRESS MODAL */}
      {showDetailModal && selectedLearner && (
        <ComprehensiveLearnerModal
          learner={selectedLearner}
          learnerDetails={learnerDetails}
          loadingDetails={loadingDetails}
          onClose={() => {
            setShowDetailModal(false);
            setLearnerDetails(null);
          }}
        />
      )}
    </div>
  );
}
