'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';

// Register ChartJS components
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement);

interface LanguageDistribution {
  language: string;
  count: number;
  percentage: number;
}

interface LevelDistribution {
  level: string;
  count: number;
  percentage: number;
}

interface Tutor {
  id: string;
  name: string;
  email: string;
  bio?: string;
  specializations: string[];
  learner_count: number;
  learners: Learner[];
  permissions: string[];
}

interface Learner {
  id: string;
  user_id: string;
  name: string;
  email: string;
  language: string | null;
  level: string | null;
  tutor: { id: string; name: string; email: string } | null;
  enrollment_method: string;
  consent_given: boolean;
  enrolled_at: string;
  progress?: {
    percentage: number;
    completed_sessions: number;
    total_sessions: number;
    category: string;
    color: string;
    emoji: string;
  };
}

export const InstitutionDashboardComplete: React.FC = () => {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [institutionId, setInstitutionId] = useState('');
  const [institutionName, setInstitutionName] = useState('');
  
  // Analytics data
  const [languageDistribution, setLanguageDistribution] = useState<LanguageDistribution[]>([]);
  const [levelDistribution, setLevelDistribution] = useState<LevelDistribution[]>([]);
  
  // Tutors and Learners
  const [tutors, setTutors] = useState<Tutor[]>([]);
  const [learners, setLearners] = useState<Learner[]>([]);
  const [filteredLearners, setFilteredLearners] = useState<Learner[]>([]);
  
  // UI State
  const [activeTab, setActiveTab] = useState<'overview' | 'tutors' | 'learners'>('overview');
  const [showAddTutorModal, setShowAddTutorModal] = useState(false);
  const [showAddLearnerModal, setShowAddLearnerModal] = useState(false);
  const [showImportCSVModal, setShowImportCSVModal] = useState(false);
  const [selectedTutor, setSelectedTutor] = useState<Tutor | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterLanguage, setFilterLanguage] = useState('all');
  const [filterLevel, setFilterLevel] = useState('all');
  const [filterTutor, setFilterTutor] = useState('all');
  const [filterProgress, setFilterProgress] = useState('all');
  const [isExporting, setIsExporting] = useState(false);
  
  // Pagination states
  const [tutorsPage, setTutorsPage] = useState(1);
  const [learnersPage, setLearnersPage] = useState(1);
  const itemsPerPage = 10;

  // Modal states for notifications and confirmations
  const [notification, setNotification] = useState<{
    show: boolean;
    type: 'success' | 'error' | 'info';
    title: string;
    message: string;
  }>({
    show: false,
    type: 'info',
    title: '',
    message: ''
  });

  const [confirmation, setConfirmation] = useState<{
    show: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
    confirmText?: string;
    cancelText?: string;
  }>({
    show: false,
    title: '',
    message: '',
    onConfirm: () => {},
    confirmText: 'Confirm',
    cancelText: 'Cancel'
  });

  // Form states
  const [tutorForm, setTutorForm] = useState({
    name: '',
    email: '',
    bio: '',
    languages: [] as string[],
    specializations: '',
    permissions: ['view_learners', 'assign_tasks']
  });

  // Available languages with flags
  const availableLanguages = [
    { code: 'english', name: 'English', flag: '🇬🇧' },
    { code: 'dutch', name: 'Dutch', flag: '🇳🇱' },
    { code: 'spanish', name: 'Spanish', flag: '🇪🇸' },
    { code: 'french', name: 'French', flag: '🇫🇷' },
    { code: 'german', name: 'German', flag: '🇩🇪' },
    { code: 'portuguese', name: 'Portuguese', flag: '🇵🇹' }
  ];

  // Authentication check
  useEffect(() => {
    const token = localStorage.getItem('institution_token');
    const instId = localStorage.getItem('institution_id');
    const instName = localStorage.getItem('institution_name');
    
    if (!token || !instId) {
      router.push('/institution/login');
      return;
    }
    
    setIsAuthenticated(true);
    setInstitutionId(instId);
    setInstitutionName(instName || 'Your Institution');
    setIsLoading(false);
  }, [router]);

  // Load all data when authenticated
  useEffect(() => {
    if (isAuthenticated && institutionId) {
      loadAllData();
    }
  }, [isAuthenticated, institutionId]);

  // Filter learners based on search and filters
  useEffect(() => {
    let filtered = learners;
    
    if (searchQuery) {
      filtered = filtered.filter(l => 
        l.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        l.email.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    if (filterLanguage !== 'all') {
      filtered = filtered.filter(l => l.language === filterLanguage);
    }
    
    if (filterLevel !== 'all') {
      filtered = filtered.filter(l => l.level === filterLevel);
    }
    
    if (filterTutor !== 'all') {
      filtered = filtered.filter(l => l.tutor?.id === filterTutor);
    }
    
    if (filterProgress !== 'all') {
      filtered = filtered.filter(l => {
        if (!l.progress) return filterProgress === 'none';
        return l.progress.category === filterProgress;
      });
    }
    
    setFilteredLearners(filtered);
    setLearnersPage(1); // Reset to first page when filters change
  }, [learners, searchQuery, filterLanguage, filterLevel, filterTutor, filterProgress]);

  const loadAllData = async () => {
    try {
      const token = localStorage.getItem('institution_token');
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Load analytics
      const [langRes, levelRes, tutorsRes, learnersRes] = await Promise.all([
        fetch(`${backendUrl}/api/v1/institution/dashboard/${institutionId}/analytics/language-distribution`, { headers }),
        fetch(`${backendUrl}/api/v1/institution/dashboard/${institutionId}/analytics/level-distribution`, { headers }),
        fetch(`${backendUrl}/api/v1/institution/dashboard/${institutionId}/tutors`, { headers }),
        fetch(`${backendUrl}/api/v1/institution/dashboard/${institutionId}/learners`, { headers })
      ]);

      if (langRes.ok) {
        const data = await langRes.json();
        setLanguageDistribution(data.distribution || []);
      }

      if (levelRes.ok) {
        const data = await levelRes.json();
        setLevelDistribution(data.distribution || []);
      }

      if (tutorsRes.ok) {
        const data = await tutorsRes.json();
        setTutors(data.tutors || []);
      }

      if (learnersRes.ok) {
        const data = await learnersRes.json();
        setLearners(data.learners || []);
        setFilteredLearners(data.learners || []);
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    }
  };

  const handleAddTutor = async () => {
    try {
      const token = localStorage.getItem('institution_token');
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/v1/institution/dashboard/${institutionId}/tutors`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: tutorForm.name,
          email: tutorForm.email,
          bio: tutorForm.bio,
          specializations: tutorForm.specializations.split(',').map(s => s.trim()),
          permissions: tutorForm.permissions
        })
      });

      if (response.ok) {
        setNotification({
          show: true,
          type: 'success',
          title: 'Success!',
          message: 'Tutor added successfully!'
        });
        setShowAddTutorModal(false);
        setTutorForm({ name: '', email: '', bio: '', languages: [], specializations: '', permissions: ['view_learners', 'assign_tasks'] });
        loadAllData();
      } else {
        const error = await response.json();
        setNotification({
          show: true,
          type: 'error',
          title: 'Error',
          message: error.detail || 'Failed to add tutor'
        });
      }
    } catch (error) {
      console.error('Error adding tutor:', error);
      setNotification({
        show: true,
        type: 'error',
        title: 'Error',
        message: `Failed to add tutor: ${error}`
      });
    }
  };

  const handleRemoveTutor = async (tutorId: string) => {
    setConfirmation({
      show: true,
      title: 'Remove Tutor?',
      message: 'Are you sure you want to remove this tutor? This action cannot be undone.',
      confirmText: 'Remove',
      cancelText: 'Cancel',
      onConfirm: async () => {
        try {
          const token = localStorage.getItem('institution_token');
          const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
          const response = await fetch(`${backendUrl}/api/v1/institution/dashboard/${institutionId}/tutors/${tutorId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
          });

          if (response.ok) {
            setNotification({
              show: true,
              type: 'success',
              title: 'Success!',
              message: 'Tutor removed successfully!'
            });
            loadAllData();
          } else {
            setNotification({
              show: true,
              type: 'error',
              title: 'Error',
              message: 'Failed to remove tutor'
            });
          }
        } catch (error) {
          console.error('Error removing tutor:', error);
          setNotification({
            show: true,
            type: 'error',
            title: 'Error',
            message: 'Failed to remove tutor'
          });
        }
      }
    });
  };

  const handleAssignLearnerToTutor = async (learnerId: string, tutorId: string) => {
    try {
      const token = localStorage.getItem('institution_token');
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/v1/institution/dashboard/${institutionId}/learners/assign-tutor`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ learner_id: learnerId, tutor_id: tutorId })
      });

      if (response.ok) {
        setNotification({
          show: true,
          type: 'success',
          title: 'Success!',
          message: 'Learner assigned successfully!'
        });
        loadAllData();
      } else {
        setNotification({
          show: true,
          type: 'error',
          title: 'Error',
          message: 'Failed to assign learner'
        });
      }
    } catch (error) {
      console.error('Error assigning learner:', error);
      setNotification({
        show: true,
        type: 'error',
        title: 'Error',
        message: 'Failed to assign learner'
      });
    }
  };

  const handleDeactivateLearner = async (learnerId: string) => {
    setConfirmation({
      show: true,
      title: 'Deactivate Learner?',
      message: 'Are you sure you want to deactivate this learner? They will lose access to the platform.',
      confirmText: 'Deactivate',
      cancelText: 'Cancel',
      onConfirm: async () => {
        try {
          const token = localStorage.getItem('institution_token');
          const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
          const response = await fetch(`${backendUrl}/api/v1/institution/dashboard/${institutionId}/learners/deactivate/${learnerId}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
          });

          if (response.ok) {
            setNotification({
              show: true,
              type: 'success',
              title: 'Success!',
              message: 'Learner deactivated successfully!'
            });
            loadAllData();
          } else {
            setNotification({
              show: true,
              type: 'error',
              title: 'Error',
              message: 'Failed to deactivate learner'
            });
          }
        } catch (error) {
          console.error('Error deactivating learner:', error);
          setNotification({
            show: true,
            type: 'error',
            title: 'Error',
            message: 'Failed to deactivate learner'
          });
        }
      }
    });
  };

  const handleExportLearners = async () => {
    setIsExporting(true);
    try {
      const token = localStorage.getItem('institution_token');
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/v1/institution/dashboard/${institutionId}/learners/export`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        
        // Convert to CSV
        const csv = [
          ['Name', 'Email', 'Language', 'Level', 'Tutor Email', 'Enrolled At', 'Consent Given'].join(','),
          ...data.data.map((row: any) => [
            row.name,
            row.email,
            row.language,
            row.level,
            row.tutor_email,
            row.enrolled_at,
            row.consent_given
          ].join(','))
        ].join('\n');

        // Small delay for better UX
        await new Promise(resolve => setTimeout(resolve, 500));

        // Download
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `learners_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        
        setNotification({
          show: true,
          type: 'success',
          title: 'Export Successful!',
          message: `Exported ${data.data.length} learners to CSV file.`
        });
      } else {
        setNotification({
          show: true,
          type: 'error',
          title: 'Export Failed',
          message: 'Failed to export learners. Please try again.'
        });
      }
    } catch (error) {
      console.error('Error exporting learners:', error);
      setNotification({
        show: true,
        type: 'error',
        title: 'Export Error',
        message: 'An error occurred while exporting learners.'
      });
    } finally {
      setIsExporting(false);
    }
  };

  const handleImportCSV = async (file: File) => {
    try {
      const token = localStorage.getItem('institution_token');
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${backendUrl}/api/v1/institution/dashboard/${institutionId}/learners/bulk-import`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        setNotification({
          show: true,
          type: 'success',
          title: 'Import Completed!',
          message: `Successfully imported ${result.success_count} learners. ${result.failed_count} failed.`
        });
        setShowImportCSVModal(false);
        loadAllData();
      } else {
        setNotification({
          show: true,
          type: 'error',
          title: 'Import Failed',
          message: 'Failed to import CSV file. Please check the file format.'
        });
      }
    } catch (error) {
      console.error('Error importing CSV:', error);
      setNotification({
        show: true,
        type: 'error',
        title: 'Import Error',
        message: 'An error occurred while importing the CSV file.'
      });
    }
  };

  // Chart data
  const languageChartData = {
    labels: languageDistribution.map(d => d.language),
    datasets: [{
      data: languageDistribution.map(d => d.count),
      backgroundColor: [
        '#4ECFBF',
        '#FF6384',
        '#36A2EB',
        '#FFCE56',
        '#4BC0C0',
        '#9966FF'
      ]
    }]
  };

  const levelChartData = {
    labels: levelDistribution.map(d => d.level),
    datasets: [{
      label: 'Number of Learners',
      data: levelDistribution.map(d => d.count),
      backgroundColor: '#4ECFBF'
    }]
  };

  // Pagination logic
  const paginatedTutors = tutors.slice(
    (tutorsPage - 1) * itemsPerPage,
    tutorsPage * itemsPerPage
  );
  const totalTutorPages = Math.ceil(tutors.length / itemsPerPage);

  const paginatedLearners = filteredLearners.slice(
    (learnersPage - 1) * itemsPerPage,
    learnersPage * itemsPerPage
  );
  const totalLearnerPages = Math.ceil(filteredLearners.length / itemsPerPage);

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
                  onClick={() => onPageChange(page as number)}
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
            onClick={() => onPageChange(currentPage + 1)}
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

  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 pt-20">
      {/* Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('overview')}
              className={`py-4 border-b-2 ${activeTab === 'overview' ? 'border-[#4ECFBF] text-[#4ECFBF]' : 'border-transparent text-gray-500'}`}
            >
              📊 Overview
            </button>
            <button
              onClick={() => setActiveTab('tutors')}
              className={`py-4 border-b-2 ${activeTab === 'tutors' ? 'border-[#4ECFBF] text-[#4ECFBF]' : 'border-transparent text-gray-500'}`}
            >
              👥 Tutors ({tutors.length})
            </button>
            <button
              onClick={() => setActiveTab('learners')}
              className={`py-4 border-b-2 ${activeTab === 'learners' ? 'border-[#4ECFBF] text-[#4ECFBF]' : 'border-transparent text-gray-500'}`}
            >
              🎓 Learners ({learners.length})
            </button>
          </nav>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* Analytics Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Language Distribution */}
              <div className="bg-white p-6 rounded-xl shadow">
                <h3 className="text-lg font-bold mb-4">Language Distribution</h3>
                {languageDistribution.length > 0 ? (
                  <div className="h-64">
                    <Pie data={languageChartData} options={{ maintainAspectRatio: false }} />
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">No data available</p>
                )}
              </div>

              {/* Level Distribution */}
              <div className="bg-white p-6 rounded-xl shadow">
                <h3 className="text-lg font-bold mb-4">Proficiency Level Distribution</h3>
                {levelDistribution.length > 0 ? (
                  <div className="h-64">
                    <Bar data={levelChartData} options={{ maintainAspectRatio: false }} />
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">No data available</p>
                )}
              </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white p-6 rounded-xl shadow">
                <p className="text-gray-600">Total Learners</p>
                <p className="text-3xl font-bold text-[#4ECFBF]">{learners.length}</p>
              </div>
              <div className="bg-white p-6 rounded-xl shadow">
                <p className="text-gray-600">Total Tutors</p>
                <p className="text-3xl font-bold text-[#4ECFBF]">{tutors.length}</p>
              </div>
              <div className="bg-white p-6 rounded-xl shadow">
                <p className="text-gray-600">Languages</p>
                <p className="text-3xl font-bold text-[#4ECFBF]">{languageDistribution.length}</p>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'tutors' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Tutor Management</h2>
              <button
                onClick={() => setShowAddTutorModal(true)}
                className="px-6 py-3 bg-[#4ECFBF] text-white rounded-lg hover:bg-[#3a9e92]"
              >
                + Add Tutor
              </button>
            </div>

            <div className="bg-white rounded-xl shadow overflow-hidden">
              {paginatedTutors.map(tutor => (
                <div key={tutor.id} className="p-6 border-b last:border-b-0">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-gray-900">{tutor.name}</h3>
                      <p className="text-gray-600">{tutor.email}</p>
                      <p className="text-sm text-gray-500 mt-2">{tutor.bio}</p>
                      <p className="text-sm mt-2 text-gray-700">
                        <span className="font-medium">Specializations:</span> {tutor.specializations.join(', ')}
                      </p>
                      <p className="text-sm text-gray-700">
                        <span className="font-medium">Assigned Learners:</span> {tutor.learner_count}
                      </p>
                      
                      {/* Show learners */}
                      {tutor.learners && tutor.learners.length > 0 && (
                        <div className="mt-4">
                          <button
                            onClick={() => setSelectedTutor(selectedTutor?.id === tutor.id ? null : tutor)}
                            className="text-[#4ECFBF] text-sm"
                          >
                            {selectedTutor?.id === tutor.id ? 'Hide' : 'Show'} Learners →
                          </button>
                          
                          {selectedTutor?.id === tutor.id && (
                            <div className="mt-2 pl-4 border-l-2 border-[#4ECFBF]">
                              {tutor.learners.slice(0, 5).map(learner => (
                                <div key={learner.user_id} className="text-sm py-1 text-gray-700">
                                  • {learner.name} ({learner.email})
                                </div>
                              ))}
                              {tutor.learners.length > 5 && (
                                <p className="text-sm text-gray-500">...and {tutor.learners.length - 5} more</p>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                    
                    <button
                      onClick={() => handleRemoveTutor(tutor.id)}
                      className="px-4 py-2 text-red-600 hover:bg-red-50 rounded"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))}
              
              {/* Pagination for Tutors */}
              {totalTutorPages > 1 && (
                <Pagination 
                  currentPage={tutorsPage}
                  totalPages={totalTutorPages}
                  totalItems={tutors.length}
                  onPageChange={setTutorsPage}
                />
              )}
            </div>
          </div>
        )}

        {activeTab === 'learners' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">Learner Management</h2>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowImportCSVModal(true)}
                  className="px-6 py-3 border-2 border-[#4ECFBF] text-[#4ECFBF] rounded-lg hover:bg-[#4ECFBF] hover:text-white transition-colors"
                >
                  📤 Import CSV
                </button>
                <button
                  onClick={handleExportLearners}
                  disabled={isExporting}
                  className={`px-6 py-3 border-2 border-[#4ECFBF] rounded-lg transition-all ${
                    isExporting
                      ? 'bg-[#4ECFBF] text-white cursor-wait'
                      : 'text-[#4ECFBF] hover:bg-[#4ECFBF] hover:text-white'
                  }`}
                >
                  {isExporting ? (
                    <span className="flex items-center space-x-2">
                      <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <span>Exporting...</span>
                    </span>
                  ) : (
                    <span>📥 Export CSV</span>
                  )}
                </button>
              </div>
            </div>

            {/* Filters */}
            <div className="bg-white p-4 rounded-xl shadow flex gap-4 flex-wrap">
              <input
                type="text"
                placeholder="Search learners..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 min-w-[200px] px-4 py-2 border rounded-lg text-gray-900 placeholder-gray-500"
              />
              <select
                value={filterLanguage}
                onChange={(e) => setFilterLanguage(e.target.value)}
                className="px-4 py-2 border rounded-lg text-gray-900"
              >
                <option value="all">All Languages</option>
                {Array.from(new Set(learners.map(l => l.language).filter(Boolean))).map(lang => (
                  <option key={lang} value={lang!}>{lang}</option>
                ))}
              </select>
              <select
                value={filterLevel}
                onChange={(e) => setFilterLevel(e.target.value)}
                className="px-4 py-2 border rounded-lg text-gray-900"
              >
                <option value="all">All Levels</option>
                {['A1', 'A2', 'B1', 'B2', 'C1', 'C2'].map(level => (
                  <option key={level} value={level}>{level}</option>
                ))}
              </select>
              <select
                value={filterProgress}
                onChange={(e) => setFilterProgress(e.target.value)}
                className="px-4 py-2 border rounded-lg text-gray-900"
              >
                <option value="all">All Progress</option>
                <option value="Just Started">🟢 Just Started</option>
                <option value="Early Progress">🔵 Early Progress</option>
                <option value="Intermediate">🟡 Intermediate</option>
                <option value="Advanced">🟠 Advanced</option>
                <option value="Nearly Complete">🔴 Nearly Complete</option>
                <option value="none">No Progress Data</option>
              </select>
              <select
                value={filterTutor}
                onChange={(e) => setFilterTutor(e.target.value)}
                className="px-4 py-2 border rounded-lg text-gray-900"
              >
                <option value="all">All Tutors</option>
                {tutors.map(tutor => (
                  <option key={tutor.id} value={tutor.id}>{tutor.name}</option>
                ))}
              </select>
            </div>

            {/* Learners Table */}
            <div className="bg-white rounded-xl shadow overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Language</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Level</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Progress</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tutor</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {paginatedLearners.map(learner => (
                    <tr key={learner.id}>
                      <td className="px-6 py-4">
                        <div>
                          <p className="font-medium text-gray-900">{learner.name}</p>
                          <p className="text-sm text-gray-500">{learner.email}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-gray-700">{learner.language || 'Not set'}</td>
                      <td className="px-6 py-4 text-gray-700">{learner.level || 'Not set'}</td>
                      <td className="px-6 py-4">
                        {learner.progress ? (
                          <div className="space-y-2">
                            {/* Progress Bar */}
                            <div className="flex items-center space-x-3">
                              <div className="flex-1">
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                  <div 
                                    className={`h-2 rounded-full ${
                                      learner.progress.color === 'green' ? 'bg-green-500' :
                                      learner.progress.color === 'blue' ? 'bg-blue-500' :
                                      learner.progress.color === 'yellow' ? 'bg-yellow-500' :
                                      learner.progress.color === 'orange' ? 'bg-orange-500' :
                                      'bg-red-500'
                                    }`}
                                    style={{ width: `${learner.progress.percentage}%` }}
                                  ></div>
                                </div>
                              </div>
                              <span className="text-sm font-medium text-gray-700 min-w-[45px]">
                                {learner.progress.percentage}%
                              </span>
                            </div>
                            {/* Session Count and Badge */}
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-gray-600">
                                {learner.progress.completed_sessions}/{learner.progress.total_sessions} sessions
                              </span>
                              <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-700 flex items-center space-x-1">
                                <span>{learner.progress.emoji}</span>
                                <span>{learner.progress.category}</span>
                              </span>
                            </div>
                          </div>
                        ) : (
                          <span className="text-sm text-gray-500">No progress data</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <select
                          value={learner.tutor?.id || ''}
                          onChange={(e) => handleAssignLearnerToTutor(learner.id, e.target.value)}
                          className="px-3 py-1 border rounded text-sm text-gray-900 bg-white"
                        >
                          <option value="">Unassigned</option>
                          {tutors.map(tutor => (
                            <option key={tutor.id} value={tutor.id}>{tutor.name}</option>
                          ))}
                        </select>
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => handleDeactivateLearner(learner.id)}
                          className="px-4 py-2 bg-red-50 text-red-600 rounded-lg text-sm font-medium hover:bg-red-100 hover:text-red-700 transition-all border border-red-200"
                        >
                          Deactivate
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {/* Pagination for Learners */}
              {totalLearnerPages > 1 && (
                <Pagination 
                  currentPage={learnersPage}
                  totalPages={totalLearnerPages}
                  totalItems={filteredLearners.length}
                  onPageChange={setLearnersPage}
                />
              )}
            </div>
          </div>
        )}
      </main>

      {/* Add Tutor Modal */}
      {showAddTutorModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl max-w-md w-full">
            <h3 className="text-xl font-bold mb-4 text-gray-900">Add New Tutor</h3>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Name"
                value={tutorForm.name}
                onChange={(e) => setTutorForm({...tutorForm, name: e.target.value})}
                className="w-full px-4 py-2 border rounded-lg text-gray-900 placeholder-gray-500"
              />
              <input
                type="email"
                placeholder="Email"
                value={tutorForm.email}
                onChange={(e) => setTutorForm({...tutorForm, email: e.target.value})}
                className="w-full px-4 py-2 border rounded-lg text-gray-900 placeholder-gray-500"
              />
              <textarea
                placeholder="Bio"
                value={tutorForm.bio}
                onChange={(e) => setTutorForm({...tutorForm, bio: e.target.value})}
                className="w-full px-4 py-2 border rounded-lg text-gray-900 placeholder-gray-500"
                rows={3}
              />
              
              {/* Language Selection with Flags */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Languages</label>
                <div className="grid grid-cols-2 gap-3">
                  {availableLanguages.map((lang) => (
                    <button
                      key={lang.code}
                      type="button"
                      onClick={() => {
                        const isSelected = tutorForm.languages.includes(lang.code);
                        setTutorForm({
                          ...tutorForm,
                          languages: isSelected
                            ? tutorForm.languages.filter(l => l !== lang.code)
                            : [...tutorForm.languages, lang.code]
                        });
                      }}
                      className={`flex items-center space-x-2 px-4 py-3 border-2 rounded-lg transition-all ${
                        tutorForm.languages.includes(lang.code)
                          ? 'border-[#4ECFBF] bg-[#4ECFBF]/10 text-[#4ECFBF]'
                          : 'border-gray-200 hover:border-[#4ECFBF]/50'
                      }`}
                    >
                      <span className="text-2xl">{lang.flag}</span>
                      <span className="font-medium text-gray-900">{lang.name}</span>
                      {tutorForm.languages.includes(lang.code) && (
                        <svg className="w-5 h-5 ml-auto" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              <input
                type="text"
                placeholder="Specializations (comma-separated)"
                value={tutorForm.specializations}
                onChange={(e) => setTutorForm({...tutorForm, specializations: e.target.value})}
                className="w-full px-4 py-2 border rounded-lg text-gray-900 placeholder-gray-500"
              />
              <div className="flex gap-3">
                <button
                  onClick={handleAddTutor}
                  className="flex-1 px-4 py-2 bg-[#4ECFBF] text-white rounded-lg hover:bg-[#3a9e92]"
                >
                  Add Tutor
                </button>
                <button
                  onClick={() => setShowAddTutorModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-900 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Import CSV Modal */}
      {showImportCSVModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl max-w-md w-full">
            <h3 className="text-xl font-bold mb-4 text-gray-900">Import Learners from CSV</h3>
            <p className="text-sm text-gray-600 mb-4">
              CSV format: name, email, language, level, tutor_email
            </p>
            <input
              type="file"
              accept=".csv"
              onChange={(e) => {
                if (e.target.files?.[0]) {
                  handleImportCSV(e.target.files[0]);
                }
              }}
              className="w-full px-4 py-2 border rounded-lg mb-4 text-gray-900"
            />
            <button
              onClick={() => setShowImportCSVModal(false)}
              className="w-full px-4 py-2 border-2 border-gray-300 text-gray-900 rounded-lg hover:bg-gray-50 font-medium transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Modern Notification Modal */}
      {notification.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 animate-fadeIn">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 transform transition-all animate-slideUp">
            <div className={`p-6 rounded-t-2xl ${
              notification.type === 'success' ? 'bg-gradient-to-r from-green-50 to-emerald-50' :
              notification.type === 'error' ? 'bg-gradient-to-r from-red-50 to-rose-50' :
              'bg-gradient-to-r from-blue-50 to-cyan-50'
            }`}>
              <div className="flex items-center space-x-4">
                <div className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center ${
                  notification.type === 'success' ? 'bg-green-100' :
                  notification.type === 'error' ? 'bg-red-100' :
                  'bg-blue-100'
                }`}>
                  {notification.type === 'success' && (
                    <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                  {notification.type === 'error' && (
                    <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  )}
                  {notification.type === 'info' && (
                    <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  )}
                </div>
                <div className="flex-1">
                  <h3 className={`text-lg font-bold ${
                    notification.type === 'success' ? 'text-green-900' :
                    notification.type === 'error' ? 'text-red-900' :
                    'text-blue-900'
                  }`}>
                    {notification.title}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">{notification.message}</p>
                </div>
              </div>
            </div>
            <div className="p-4 bg-white rounded-b-2xl">
              <button
                onClick={() => setNotification({...notification, show: false})}
                className="w-full px-6 py-3 bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white rounded-lg font-medium hover:shadow-lg transform hover:scale-105 transition-all"
              >
                Got it
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modern Confirmation Modal */}
      {confirmation.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 animate-fadeIn">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 transform transition-all animate-slideUp">
            <div className="p-6 bg-gradient-to-r from-orange-50 to-amber-50 rounded-t-2xl">
              <div className="flex items-center space-x-4">
                <div className="flex-shrink-0 w-12 h-12 rounded-full bg-orange-100 flex items-center justify-center">
                  <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-orange-900">{confirmation.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{confirmation.message}</p>
                </div>
              </div>
            </div>
            <div className="p-4 bg-white rounded-b-2xl flex gap-3">
              <button
                onClick={() => setConfirmation({...confirmation, show: false})}
                className="flex-1 px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-all"
              >
                {confirmation.cancelText || 'Cancel'}
              </button>
              <button
                onClick={() => {
                  confirmation.onConfirm();
                  setConfirmation({...confirmation, show: false});
                }}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg font-medium hover:shadow-lg transform hover:scale-105 transition-all"
              >
                {confirmation.confirmText || 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fadeIn {
          animation: fadeIn 0.2s ease-out;
        }
        .animate-slideUp {
          animation: slideUp 0.3s ease-out;
        }
      `}</style>
    </div>
  );
};
