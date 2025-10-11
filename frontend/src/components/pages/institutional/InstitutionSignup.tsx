'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { institutionService, InstitutionSignupData } from '../../../services/institutionService';
import Link from 'next/link';

export const InstitutionSignup: React.FC = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [formData, setFormData] = useState<InstitutionSignupData>({
    name: '',
    institution_type: 'school',
    admin_email: '',
    admin_password: '',
    admin_name: '',
    activation_code: ''
  });
  
  // Get activation code from URL parameter
  useEffect(() => {
    const code = searchParams.get('code');
    if (code) {
      setFormData(prev => ({ ...prev, activation_code: code }));
    }
  }, [searchParams]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) newErrors.name = 'Institution name is required';
    if (!formData.admin_email.trim()) {
      newErrors.admin_email = 'Admin email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.admin_email)) {
      newErrors.admin_email = 'Invalid email format';
    }
    if (!formData.admin_name.trim()) newErrors.admin_name = 'Admin name is required';
    if (!formData.admin_password) {
      newErrors.admin_password = 'Password is required';
    } else if (formData.admin_password.length < 8) {
      newErrors.admin_password = 'Password must be at least 8 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsSubmitting(true);
    setApiError(null);

    try {
      const result = await institutionService.signup(formData);
      localStorage.setItem('institution_code', result.institution_code);
      localStorage.setItem('institution_id', result.institution_id);
      localStorage.setItem('institution_name', formData.name);
      
      // Show success animation
      setShowSuccess(true);
      
      // Redirect to dashboard after animation
      setTimeout(() => {
        router.push('/institution/dashboard');
      }, 2000);
    } catch (error: any) {
      setApiError(error.response?.data?.detail || 'Signup failed. Please try again.');
      setIsSubmitting(false);
    }
  };

  const handleChange = (field: keyof InstitutionSignupData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  // Success animation screen
  if (showSuccess) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-24 h-24 bg-green-100 rounded-full mb-6 animate-bounce">
            <svg className="w-12 h-12 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">Account Created!</h2>
          <p className="text-gray-600 mb-4">Redirecting to your dashboard...</p>
          <div className="flex justify-center space-x-1">
            <div className="w-2 h-2 bg-[#4ECFBF] rounded-full animate-pulse"></div>
            <div className="w-2 h-2 bg-[#4ECFBF] rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
            <div className="w-2 h-2 bg-[#4ECFBF] rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center p-4 pt-24">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-xl p-8 text-gray-900">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-[#4ECFBF] to-[#3a9e92] rounded-full mb-4">
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Create School Account</h1>
            <p className="text-gray-600 text-sm">Join schools worldwide using MyTaco AI</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Institution Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                Institution Name *
              </label>
              <input
                id="name"
                type="text"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                placeholder="e.g., Lincoln Academy"
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent ${
                  errors.name ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name}</p>}
            </div>

            {/* Institution Type */}
            <div>
              <label htmlFor="institution_type" className="block text-sm font-medium text-gray-700 mb-1">
                Institution Type *
              </label>
              <select
                id="institution_type"
                value={formData.institution_type}
                onChange={(e) => handleChange('institution_type', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent text-gray-900 bg-white"
              >
                <option value="school">School</option>
                <option value="university">University</option>
                <option value="language_center">Language Center</option>
                <option value="corporate">Corporate</option>
              </select>
            </div>

            {/* Admin Name */}
            <div>
              <label htmlFor="admin_name" className="block text-sm font-medium text-gray-700 mb-1">
                Your Name *
              </label>
              <input
                id="admin_name"
                type="text"
                value={formData.admin_name}
                onChange={(e) => handleChange('admin_name', e.target.value)}
                placeholder="John Doe"
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent ${
                  errors.admin_name ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {errors.admin_name && <p className="text-red-500 text-xs mt-1">{errors.admin_name}</p>}
            </div>

            {/* Admin Email */}
            <div>
              <label htmlFor="admin_email" className="block text-sm font-medium text-gray-700 mb-1">
                Admin Email *
              </label>
              <input
                id="admin_email"
                type="email"
                value={formData.admin_email}
                onChange={(e) => handleChange('admin_email', e.target.value)}
                placeholder="admin@institution.edu"
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent ${
                  errors.admin_email ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {errors.admin_email && <p className="text-red-500 text-xs mt-1">{errors.admin_email}</p>}
            </div>

            {/* Password */}
            <div>
              <label htmlFor="admin_password" className="block text-sm font-medium text-gray-700 mb-1">
                Password *
              </label>
              <input
                id="admin_password"
                type="password"
                value={formData.admin_password}
                onChange={(e) => handleChange('admin_password', e.target.value)}
                placeholder="At least 8 characters"
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent ${
                  errors.admin_password ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {errors.admin_password && <p className="text-red-500 text-xs mt-1">{errors.admin_password}</p>}
            </div>

            {/* API Error */}
            {apiError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-red-600 text-sm">{apiError}</p>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3 bg-[#4ECFBF] text-white font-medium rounded-lg hover:bg-[#3a9e92] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Creating Account...' : 'Create Institution Account'}
            </button>

            {/* Login Link */}
            <p className="text-center text-sm text-gray-600">
              Already have an account?{' '}
              <Link href="/institution/login" className="text-[#4ECFBF] hover:text-[#3a9e92] font-medium">
                Log in here
              </Link>
            </p>
          </form>
        </div>
      </div>
    </div>
  );
};
