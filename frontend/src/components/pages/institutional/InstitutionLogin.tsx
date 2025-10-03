'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { institutionService } from '../../../services/institutionService';
import './InstitutionLogin.css';

export const InstitutionLogin: React.FC = () => {
  const router = useRouter();
  const [formData, setFormData] = useState({
    admin_email: '',
    password: ''
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

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

      // Store authentication token
      localStorage.setItem('institution_token', result.access_token);
      localStorage.setItem('institution_id', result.institution_id);

      // Navigate to institution dashboard
      router.push('/institution/dashboard');
    } catch (error: any) {
      setApiError(
        error.response?.data?.detail || 'Login failed. Please check your credentials.'
      );
      setIsSubmitting(false);
    }
  };

  const handleChange = (field: keyof typeof formData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user types
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <div className="institution-login-page">
      <div className="login-container">
        <div className="login-header">
          <h1>Institution Login</h1>
          <p>Access your institution dashboard</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="admin_email">Admin Email</label>
            <input
              id="admin_email"
              type="email"
              value={formData.admin_email}
              onChange={(e) => handleChange('admin_email', e.target.value)}
              placeholder="admin@institution.edu"
              className={errors.admin_email ? 'error' : ''}
              autoComplete="email"
            />
            {errors.admin_email && (
              <span className="error-text">{errors.admin_email}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={formData.password}
              onChange={(e) => handleChange('password', e.target.value)}
              placeholder="Enter your password"
              className={errors.password ? 'error' : ''}
              autoComplete="current-password"
            />
            {errors.password && (
              <span className="error-text">{errors.password}</span>
            )}
          </div>

          {apiError && <div className="api-error">{apiError}</div>}

          <button
            type="submit"
            className="submit-button"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Logging in...' : 'Login'}
          </button>

          <div className="form-footer">
            <p className="signup-link">
              Don't have an account?{' '}
              <a href="/institution/signup">Sign up here</a>
            </p>
            <p className="forgot-password-link">
              <a href="/institution/forgot-password">Forgot password?</a>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};
