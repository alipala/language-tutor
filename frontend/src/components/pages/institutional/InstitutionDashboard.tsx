'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

interface DashboardStats {
  total_learners: number;
  active_learners: number;
  total_minutes: number;
  avg_progress: number;
}

interface Tutor {
  id: string;
  name: string;
  email: string;
  learner_count: number;
  avg_progress: number;
  last_active: string;
}

interface Learner {
  id: string;
  name: string;
  email: string;
  language: string;
  level: string;
  progress: number;
  last_active: string;
}

export const InstitutionDashboard: React.FC = () => {
  const router = useRouter();
  const [institutionName, setInstitutionName] = useState('');
  const [institutionCode, setInstitutionCode] = useState('');
  const [stats, setStats] = useState<DashboardStats>({
    total_learners: 0,
    active_learners: 0,
    total_minutes: 0,
    avg_progress: 0
  });
  const [tutors, setTutors] = useState<Tutor[]>([]);
  const [topLearners, setTopLearners] = useState<Learner[]>([]);
  const [atRiskLearners, setAtRiskLearners] = useState<Learner[]>([]);
  const [period, setPeriod] = useState('30');
  const [activeTab, setActiveTab] = useState<'overview' | 'tutors' | 'learners'>('overview');

  useEffect(() => {
    // Load institution data
    const code = localStorage.getItem('institution_code') || '';
    const name = localStorage.getItem('institution_name') || 'Your Institution';
    setInstitutionCode(code);
    setInstitutionName(name);

    // TODO: Fetch real data from API
    // For now, using mock data
    loadDashboardData();
  }, [period]);

  const loadDashboardData = () => {
    // Mock data - replace with API calls
    setStats({
      total_learners: 150,
      active_learners: 98,
      total_minutes: 2450,
      avg_progress: 72
    });

    setTutors([
      {
        id: '1',
        name: 'Sarah Johnson',
        email: 'sarah@example.com',
        learner_count: 15,
        avg_progress: 78,
        last_active: '2 hours ago'
      },
      {
        id: '2',
        name: 'Michael Chen',
        email: 'michael@example.com',
        learner_count: 18,
        avg_progress: 65,
        last_active: '5 hours ago'
      },
      {
        id: '3',
        name: 'Emma Williams',
        email: 'emma@example.com',
        learner_count: 12,
        avg_progress: 82,
        last_active: '1 day ago'
      }
    ]);

    setTopLearners([
      {
        id: '1',
        name: 'Maria Garcia',
        email: 'maria@example.com',
        language: 'Spanish',
        level: 'B2',
        progress: 95,
        last_active: '1 hour ago'
      },
      {
        id: '2',
        name: 'Ahmed Hassan',
        email: 'ahmed@example.com',
        language: 'English',
        level: 'C1',
        progress: 92,
        last_active: '3 hours ago'
      },
      {
        id: '3',
        name: 'Li Wei',
        email: 'li@example.com',
        language: 'French',
        level: 'A2',
        progress: 88,
        last_active: '5 hours ago'
      }
    ]);

    setAtRiskLearners([
      {
        id: '4',
        name: 'John Doe',
        email: 'john@example.com',
        language: 'German',
        level: 'A1',
        progress: 15,
        last_active: '7 days ago'
      },
      {
        id: '5',
        name: 'Jane Smith',
        email: 'jane@example.com',
        language: 'Spanish',
        level: 'A1',
        progress: 5,
        last_active: '2 days ago'
      }
    ]);
  };

  const copyInstitutionCode = () => {
    navigator.clipboard.writeText(institutionCode);
    // Show toast notification
  };

  return (
    <div className="min-h-screen bg-gray-50 pt-16">

      {/* Institution Code Banner */}
      {institutionCode && (
        <div className="bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white py-3">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
                <span className="text-sm font-medium">Institution Code:</span>
                <span className="text-lg font-bold tracking-wider">{institutionCode}</span>
              </div>
              <button
                onClick={copyInstitutionCode}
                className="flex items-center space-x-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                <span className="text-sm font-medium">Copy</span>
              </button>
            </div>
            <p className="text-sm text-white/90 mt-1">Share this code with tutors and learners to join your institution</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('overview')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'overview'
                  ? 'border-[#4ECFBF] text-[#4ECFBF]'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📊 Overview
            </button>
            <button
              onClick={() => setActiveTab('tutors')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'tutors'
                  ? 'border-[#4ECFBF] text-[#4ECFBF]'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              👥 Tutors ({tutors.length})
            </button>
            <button
              onClick={() => setActiveTab('learners')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'learners'
                  ? 'border-[#4ECFBF] text-[#4ECFBF]'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🎓 Learners ({stats.total_learners})
            </button>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && (
          <>
            {/* Period Selector */}
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Overview</h2>
              <select
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent"
              >
                <option value="7">Last 7 Days</option>
                <option value="30">Last 30 Days</option>
                <option value="90">Last 90 Days</option>
                <option value="365">Last Year</option>
              </select>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Learners</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{stats.total_learners}</p>
                  </div>
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Active Users</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{stats.active_learners}</p>
                  </div>
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Minutes</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{stats.total_minutes.toLocaleString()}</p>
                  </div>
                  <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Avg Progress</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{stats.avg_progress}%</p>
                  </div>
                  <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>

            {/* Tutors Section */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 mb-8">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-bold text-gray-900">👥 Tutors ({tutors.length})</h3>
                <button className="px-4 py-2 bg-[#4ECFBF] text-white rounded-lg hover:bg-[#3a9e92] transition-colors text-sm font-medium">
                  + Add Tutor
                </button>
              </div>
              
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Name</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Learners</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Avg Progress</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Last Active</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tutors.map((tutor) => (
                      <tr key={tutor.id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-4 px-4">
                          <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-[#4ECFBF] to-[#3a9e92] rounded-full flex items-center justify-center text-white font-medium">
                              {tutor.name.charAt(0)}
                            </div>
                            <div>
                              <p className="font-medium text-gray-900">{tutor.name}</p>
                              <p className="text-sm text-gray-500">{tutor.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-4 text-gray-900">{tutor.learner_count}</td>
                        <td className="py-4 px-4">
                          <div className="flex items-center space-x-2">
                            <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-[100px]">
                              <div 
                                className="bg-[#4ECFBF] h-2 rounded-full" 
                                style={{ width: `${tutor.avg_progress}%` }}
                              ></div>
                            </div>
                            <span className="text-sm font-medium text-gray-900">{tutor.avg_progress}%</span>
                          </div>
                        </td>
                        <td className="py-4 px-4 text-gray-600">{tutor.last_active}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              <div className="mt-4 text-center">
                <button className="text-[#4ECFBF] hover:text-[#3a9e92] font-medium text-sm">
                  View All Tutors →
                </button>
              </div>
            </div>

            {/* Top Performers & At-Risk */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Top Performers */}
              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-bold text-gray-900">🎯 Top Performing Learners</h3>
                  <button className="text-[#4ECFBF] hover:text-[#3a9e92] font-medium text-sm">
                    View All →
                  </button>
                </div>
                
                <div className="space-y-4">
                  {topLearners.map((learner, index) => (
                    <div key={learner.id} className="flex items-center space-x-4">
                      <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                        {index + 1}
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">{learner.name}</p>
                        <p className="text-sm text-gray-500">{learner.language} {learner.level} - {learner.progress}% complete</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* At-Risk Learners */}
              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-bold text-gray-900">⚠️ At-Risk Learners ({atRiskLearners.length})</h3>
                  <button className="text-[#4ECFBF] hover:text-[#3a9e92] font-medium text-sm">
                    View All →
                  </button>
                </div>
                
                <div className="space-y-4">
                  {atRiskLearners.map((learner) => (
                    <div key={learner.id} className="flex items-center justify-between p-4 bg-red-50 rounded-lg border border-red-200">
                      <div>
                        <p className="font-medium text-gray-900">{learner.name}</p>
                        <p className="text-sm text-red-600">Last active: {learner.last_active}</p>
                        <p className="text-sm text-gray-600">{learner.progress}% complete</p>
                      </div>
                      <button className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium">
                        Contact
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}

        {activeTab === 'tutors' && (
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Tutor Management</h2>
              <button className="px-6 py-3 bg-[#4ECFBF] text-white rounded-lg hover:bg-[#3a9e92] transition-colors font-medium">
                + Add Tutor
              </button>
            </div>
            <p className="text-gray-600">Comprehensive tutor management features coming soon...</p>
          </div>
        )}

        {activeTab === 'learners' && (
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Learner Management</h2>
              <div className="flex space-x-3">
                <button className="px-6 py-3 bg-white border-2 border-[#4ECFBF] text-[#4ECFBF] rounded-lg hover:bg-[#4ECFBF] hover:text-white transition-colors font-medium">
                  📤 Import CSV
                </button>
                <button className="px-6 py-3 bg-[#4ECFBF] text-white rounded-lg hover:bg-[#3a9e92] transition-colors font-medium">
                  + Add Learner
                </button>
              </div>
            </div>
            <p className="text-gray-600">Bulk enrollment and learner management features coming soon...</p>
          </div>
        )}
      </main>
    </div>
  );
};
