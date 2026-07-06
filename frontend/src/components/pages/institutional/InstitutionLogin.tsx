'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { institutionService } from '../../../services/institutionService';
import Link from 'next/link';
import { B2BAuthCard, B2BField, b2bInputClass, b2bPrimaryButtonClass } from '@/src/components/b2b/B2BAuthCard';

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
      localStorage.setItem('institution_name', result.institution_name || '');
      if (result.admin_name) localStorage.setItem('institution_admin_name', result.admin_name);
      if (result.admin_email) localStorage.setItem('institution_admin_email', result.admin_email);

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
      <div className="flex min-h-[calc(100vh-64px)] items-center justify-center bg-slate-50 p-4">
        <div className="text-center">
          <div className="inline-block h-12 w-12 animate-spin rounded-full border-b-2 border-[#4ECFBF]"></div>
          <p className="mt-4 text-slate-500">Checking authentication...</p>
        </div>
      </div>
    );
  }

  return (
    <B2BAuthCard
      icon={
        <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      }
      title="School Login"
      subtitle="Access your institution dashboard"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <B2BField id="admin_email" label="Admin Email" error={errors.admin_email}>
          <input
            id="admin_email"
            type="email"
            value={formData.admin_email}
            onChange={(e) => handleChange('admin_email', e.target.value)}
            placeholder="admin@institution.edu"
            className={`${b2bInputClass} ${errors.admin_email ? 'border-red-500' : ''}`}
            autoComplete="email"
          />
        </B2BField>

        <B2BField id="password" label="Password" error={errors.password}>
          <input
            id="password"
            type="password"
            value={formData.password}
            onChange={(e) => handleChange('password', e.target.value)}
            placeholder="Enter your password"
            className={`${b2bInputClass} ${errors.password ? 'border-red-500' : ''}`}
            autoComplete="current-password"
          />
        </B2BField>

        {apiError && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3">
            <p className="text-sm text-red-600">{apiError}</p>
          </div>
        )}

        <button type="submit" disabled={isSubmitting} className={b2bPrimaryButtonClass}>
          {isSubmitting ? 'Logging in...' : 'Login'}
        </button>

        <div className="space-y-3 text-center text-sm">
          <p>
            <Link href="/institution/forgot-password" className="font-medium text-[#3A9E92] underline hover:text-[#4ECFBF]">
              Forgot password?
            </Link>
          </p>
          <p className="text-xs text-slate-400">
            New schools are onboarded by invitation. Received an activation email? Use the link in it to
            activate your account.
          </p>
        </div>
      </form>
    </B2BAuthCard>
  );
};
