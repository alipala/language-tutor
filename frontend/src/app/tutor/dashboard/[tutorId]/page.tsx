'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';

import { API_BASE_URL } from '../../../../lib/api-config';

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
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [perPage, setPerPage] = useState(10);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);

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
  
  // Reload data when pagination changes
  useEffect(() => {
    const token = localStorage.getItem('tutorToken');
    if (token && tutorName) {
      loadDashboardData(token);
    }
  }, [currentPage, perPage]);

  const loadDashboardData = async (token: string, filters = {}) => {
    try {
      setLoading(true);
      setError('');

      const queryParams = new URLSearchParams();
      if (languageFilter) queryParams.append('language', languageFilter);
      if (levelFilter) queryParams.append('level', levelFilter);
      if (statusFilter) queryParams.append('status', statusFilter);
      if (searchQuery) queryParams.append('search', searchQuery);
      
      // Add pagination parameters
      queryParams.append('page', currentPage.toString());
      queryParams.append('per_page', perPage.toString());

      const url = `${API_BASE_URL}/api/v1/tutor/dashboard/${tutorId}/learners?${queryParams.toString()}`;
      
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
      
      // Update pagination state from response
      if (data.pagination) {
        console.log('[PAGINATION] Received from backend:', data.pagination);
        setTotalPages(data.pagination.total_pages);
        setTotalItems(data.pagination.total_items);
        setCurrentPage(data.pagination.current_page);
        console.log('[PAGINATION] State updated - totalPages:', data.pagination.total_pages, 'totalItems:', data.pagination.total_items);
      } else {
        console.log('[PAGINATION] No pagination data in response');
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

  const applyFilters = () => {
    const token = localStorage.getItem('tutorToken');
    if (token) {
      loadDashboardData(token);
    }
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

  // Pagination Component
  const Pagination = ({ 
    currentPage, 
    totalPages,
    totalItems,
    onPageChange 
  }: { 
    currentPage: number; 
    totalPages: number;
    totalItems: number;
    onPageChange: (page: number) => void;
  }) => {
    const itemsPerPage = perPage;
    
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
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className={`px-3 py-2 rounded-lg font-medium transition-all ${
              currentPage === 1
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-white text-gray-700 hover:bg-blue-600 hover:text-white border'
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
                  onClick={() => onPageChange(page as number)}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${
                    currentPage === page
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'bg-white text-gray-700 hover:bg-gray-100 border'
                  }`}
                >
                  {page}
                </button>
              )
            ))}
          </div>
          
          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className={`px-3 py-2 rounded-lg font-medium transition-all ${
              currentPage === totalPages
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-white text-gray-700 hover:bg-blue-600 hover:text-white border'
            }`}
          >
            Next
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Tutor Dashboard</h1>
              <p className="text-sm text-gray-600 mt-1">Welcome back, {tutorName}</p>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

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
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Language</label>
              <select
                value={languageFilter}
                onChange={(e) => setLanguageFilter(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
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
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
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
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Status</option>
                <option value="on_track">On Track</option>
                <option value="at_risk">At Risk</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
          </div>
          <div className="flex gap-3 mt-4">
            <button
              onClick={applyFilters}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Apply Filters
            </button>
            <button
              onClick={clearFilters}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Clear All
            </button>
          </div>
        </div>

        {/* Learners List */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h2 className="text-xl font-semibold text-gray-900">Assigned Learners</h2>
            <p className="text-sm text-gray-600 mt-1">{learners.length} learner(s) found</p>
          </div>

          {loading ? (
            <div className="p-12 text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">Loading learners...</p>
            </div>
          ) : error ? (
            <div className="p-12 text-center">
              <p className="text-red-600">{error}</p>
            </div>
          ) : learners.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-gray-600">No learners found matching your filters.</p>
            </div>
          ) : (
            <div className="divide-y">
              {learners.map((learner) => {
                const plan = learner.learning_plans[0];
                if (!plan) return null;

                return (
                  <div key={learner.id} className="p-6 hover:bg-gray-50 transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900">{learner.name}</h3>
                          <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusBadgeColor(plan.progress_status)}`}>
                            {getStatusLabel(plan.progress_status)}
                          </span>
                          {!learner.consent_given && (
                            <span className="px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 border border-red-200">
                              No Consent
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mb-3">{learner.email}</p>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                          <div>
                            <div className="text-xs text-gray-500">Language</div>
                            <div className="text-sm font-medium text-gray-900">{plan.language}</div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500">Level</div>
                            <div className="text-sm font-medium text-gray-900">{plan.proficiency_level}</div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500">Progress</div>
                            <div className="text-sm font-medium text-gray-900">
                              {plan.completed_sessions}/{plan.total_sessions} sessions
                            </div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500">Completion</div>
                            <div className="text-sm font-medium text-gray-900">{plan.progress_percentage.toFixed(1)}%</div>
                          </div>
                        </div>

                        {/* Progress Bar */}
                        <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
                          <div
                            className={`h-2 rounded-full transition-all ${
                              plan.progress_status === 'on_track' ? 'bg-green-500' :
                              plan.progress_status === 'at_risk' ? 'bg-yellow-500' :
                              'bg-gray-400'
                            }`}
                            style={{ width: `${plan.progress_percentage}%` }}
                          ></div>
                        </div>

                        <div className="text-sm text-gray-600">
                          <strong>Next Focus:</strong> {plan.next_focus_area}
                        </div>
                      </div>

                      <button
                        onClick={() => handleViewDetails(learner)}
                        disabled={!learner.consent_given}
                        className="ml-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed text-sm"
                      >
                        View Details
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
          
          {/* Pagination */}
          {!loading && !error && totalPages > 1 && (
            <Pagination 
              currentPage={currentPage}
              totalPages={totalPages}
              totalItems={totalItems}
              onPageChange={setCurrentPage}
            />
          )}
        </div>
      </div>

      {/* Learner Detail Modal */}
      {showDetailModal && selectedLearner && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b flex justify-between items-center sticky top-0 bg-white">
              <h2 className="text-2xl font-bold text-gray-900">{selectedLearner.name}</h2>
              <button
                onClick={() => {
                  setShowDetailModal(false);
                  setLearnerDetails(null);
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6">
              {loadingDetails ? (
                <div className="text-center py-12">
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                  <p className="mt-4 text-gray-600">Loading detailed progress...</p>
                </div>
              ) : learnerDetails ? (
                <div className="space-y-6">
                  {/* Profile Section */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Profile</h3>
                    <div className="grid grid-cols-2 gap-4 bg-gray-50 p-4 rounded-lg">
                      <div>
                        <div className="text-sm text-gray-500">Email</div>
                        <div className="font-medium">{learnerDetails.profile.email}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-500">Total Sessions</div>
                        <div className="font-medium">{learnerDetails.profile.total_sessions}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-500">Total Minutes</div>
                        <div className="font-medium">{learnerDetails.profile.total_minutes}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-500">Languages</div>
                        <div className="font-medium">{learnerDetails.profile.languages_studied.join(', ')}</div>
                      </div>
                    </div>
                  </div>

                  {/* AI Insights */}
                  {learnerDetails.ai_insights && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">AI Insights</h3>
                      <div className="bg-blue-50 p-4 rounded-lg">
                        <p className="text-gray-800">{learnerDetails.ai_insights.overall_summary}</p>
                        
                        {learnerDetails.ai_insights.recommendations && learnerDetails.ai_insights.recommendations.length > 0 && (
                          <div className="mt-4">
                            <h4 className="font-semibold text-gray-900 mb-2">Recommendations:</h4>
                            <ul className="space-y-1">
                              {learnerDetails.ai_insights.recommendations.map((rec: string, idx: number) => (
                                <li key={idx} className="text-sm text-gray-700">• {rec}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Learning Plans */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Learning Plans</h3>
                    {learnerDetails.all_learning_plans.map((plan: any) => (
                      <div key={plan.id} className="border rounded-lg p-4 mb-3">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <h4 className="font-semibold text-gray-900">{plan.language} - {plan.proficiency_level}</h4>
                            <div className="text-sm text-gray-600 mt-1">
                              {plan.completed_sessions}/{plan.total_sessions} sessions ({plan.progress_percentage.toFixed(1)}%)
                            </div>
                          </div>
                          <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                            {plan.practice_minutes_used}/{plan.total_practice_minutes} min
                          </span>
                        </div>
                        
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${plan.progress_percentage}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-600">
                  Failed to load learner details
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
