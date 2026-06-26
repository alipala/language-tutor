'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { institutionService } from '../../../services/institutionService';
import Link from 'next/link';

export const InstitutionLogin: React.FC = () => {
  const router = useRouter();
  const [formData, setFormData] = useState({
    admin_email: '',
    password: ''
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // Check if user is already authenticated on mount
  useEffect(() => {
    const token = localStorage.getItem('institution_token');
    const institutionId = localStorage.getItem('institution_id');

    if (token && institutionId) {
      // Already authenticated, redirect to dashboard
      router.push('/institution/dashboard');
    } else {
      setIsCheckingAuth(false);
    }
  }, [router]);

  // Pre-fill email from sessionStorage if available
  useEffect(() => {
    const b2bEmail = sessionStorage.getItem('b2bEmail');
    if (b2bEmail) {
      setFormData(prev => ({ ...prev, admin_email: b2bEmail }));
      sessionStorage.removeItem('b2bEmail'); // Clear it after use
    }
  }, []);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.admin_email.trim()) {
      newErrors.admin_email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.admin_email)) {
      newErrors.admin_email = 'Invalid email format';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
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
      const result = await institutionService.login({
        admin_email: formData.admin_email,
        password: formData.password
      });

      // Clear any old session data first
      sessionStorage.clear();
      
      // Set new authentication data
      localStorage.setItem('institution_token', result.access_token);
      localStorage.setItem('institution_id', result.institution_id);
      
      // Use window.location.href for hard navigation to prevent cache issues
      window.location.href = '/institution/dashboard';
    } catch (error: any) {
      setApiError(
        error.response?.data?.detail || 'Login failed. Please check your credentials.'
      );
      setIsSubmitting(false);
    }
  };

  const handleChange = (field: keyof typeof formData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  // Show loading state while checking authentication
  if (isCheckingAuth) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center p-4 pt-24">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-brand"></div>
          <p className="mt-4 text-gray-600">Checking authentication...</p>
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
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-brand to-[#3a9e92] rounded-full mb-4">
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">School Login</h1>
            <p className="text-gray-600 text-sm">Access your institution dashboard</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Admin Email */}
            <div>
              <label htmlFor="admin_email" className="block text-sm font-medium text-gray-700 mb-1">
                Admin Email
              </label>
              <input
                id="admin_email"
                type="email"
                value={formData.admin_email}
                onChange={(e) => handleChange('admin_email', e.target.value)}
                placeholder="admin@institution.edu"
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-brand focus:border-transparent ${
                  errors.admin_email ? 'border-red-500' : 'border-gray-300'
                }`}
                autoComplete="email"
              />
              {errors.admin_email && (
                <p className="text-red-500 text-xs mt-1">{errors.admin_email}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => handleChange('password', e.target.value)}
                placeholder="Enter your password"
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-brand focus:border-transparent ${
                  errors.password ? 'border-red-500' : 'border-gray-300'
                }`}
                autoComplete="current-password"
              />
              {errors.password && (
                <p className="text-red-500 text-xs mt-1">{errors.password}</p>
              )}
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
              className="w-full py-3 bg-brand text-white font-medium rounded-lg hover:bg-[#3a9e92] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Logging in...' : 'Login'}
            </button>

            {/* Links */}
            <div className="space-y-3 text-center text-sm">
              <p className="text-gray-600">
                Don't have an account?{' '}
                <Link href="/institution/signup" className="text-brand hover:text-[#3a9e92] font-medium">
                  Sign up here
                </Link>
              </p>
              <p>
                <Link href="/institution/forgot-password" className="text-brand hover:text-[#3a9e92] font-medium underline">
                  Forgot password?
                </Link>
              </p>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
