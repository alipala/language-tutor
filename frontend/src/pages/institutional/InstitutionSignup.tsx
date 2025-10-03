'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { institutionService, InstitutionSignupData } from '../../services/institutionService';
import './InstitutionSignup.css';

const PLANS = [
  {
    id: 'starter' as const,
    name: 'Starter',
    price: '$49',
    features: ['Up to 2 tutors', 'Up to 50 learners', 'Basic analytics']
  },
  {
    id: 'professional' as const,
    name: 'Professional',
    price: '$199',
    features: ['Up to 10 tutors', 'Up to 200 learners', 'Advanced analytics', 'Dedicated support']
  },
  {
    id: 'enterprise' as const,
    name: 'Enterprise',
    price: 'Custom',
    features: ['Unlimited tutors', '1000+ learners', 'White-label', 'API access']
  }
];

export const InstitutionSignup: React.FC = () => {
  const router = useRouter();
  const [formData, setFormData] = useState<InstitutionSignupData>({
    name: '',
    domain: '',
    admin_email: '',
    admin_password: '',
    admin_name: '',
    subscription_plan: 'starter'
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Institution name is required';
    }

    if (!formData.admin_email.trim()) {
      newErrors.admin_email = 'Admin email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.admin_email)) {
      newErrors.admin_email = 'Invalid email format';
    }

    if (!formData.admin_name.trim()) {
      newErrors.admin_name = 'Admin name is required';
    }

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

      // Store institution code for display
      localStorage.setItem('institution_code', result.institution_code);
      localStorage.setItem('institution_id', result.institution_id);

      // Navigate to success page
      router.push('/institution/signup-success');
    } catch (error: any) {
      setApiError(
        error.response?.data?.detail || 'Signup failed. Please try again.'
      );
      setIsSubmitting(false);
    }
  };

  const handleChange = (field: keyof InstitutionSignupData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user types
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <div className="institution-signup-page">
      <div className="signup-container">
        <div className="signup-header">
          <h1>Create Your Institution Account</h1>
          <p>Start managing your language learners with MyTaco AI</p>
        </div>

        {/* Subscription Plans */}
        <div className="plans-section">
          <h3>Choose Your Plan</h3>
          <div className="plans-grid">
            {PLANS.map(plan => (
              <div
                key={plan.id}
                className={`plan-card ${
                  formData.subscription_plan === plan.id ? 'selected' : ''
                }`}
                onClick={() => handleChange('subscription_plan', plan.id)}
              >
                <h4>{plan.name}</h4>
                <div className="plan-price">{plan.price}</div>
                <ul className="plan-features">
                  {plan.features.map((feature, i) => (
                    <li key={i}>{feature}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Signup Form */}
        <form onSubmit={handleSubmit} className="signup-form">
          <div className="form-section">
            <h3>Institution Details</h3>

            <div className="form-group">
              <label htmlFor="name">Institution Name *</label>
              <input
                id="name"
                type="text"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                placeholder="e.g., Lincoln Academy"
                className={errors.name ? 'error' : ''}
              />
              {errors.name && <span className="error-text">{errors.name}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="domain">Domain (optional)</label>
              <input
                id="domain"
                type="text"
                value={formData.domain}
                onChange={(e) => handleChange('domain', e.target.value)}
                placeholder="e.g., lincoln-academy.edu"
              />
            </div>
          </div>

          <div className="form-section">
            <h3>Admin Account</h3>

            <div className="form-group">
              <label htmlFor="admin_name">Your Name *</label>
              <input
                id="admin_name"
                type="text"
                value={formData.admin_name}
                onChange={(e) => handleChange('admin_name', e.target.value)}
                placeholder="John Doe"
                className={errors.admin_name ? 'error' : ''}
              />
              {errors.admin_name && (
                <span className="error-text">{errors.admin_name}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="admin_email">Admin Email *</label>
              <input
                id="admin_email"
                type="email"
                value={formData.admin_email}
                onChange={(e) => handleChange('admin_email', e.target.value)}
                placeholder="admin@institution.edu"
                className={errors.admin_email ? 'error' : ''}
              />
              {errors.admin_email && (
                <span className="error-text">{errors.admin_email}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="admin_password">Password *</label>
              <input
                id="admin_password"
                type="password"
                value={formData.admin_password}
                onChange={(e) => handleChange('admin_password', e.target.value)}
                placeholder="At least 8 characters"
                className={errors.admin_password ? 'error' : ''}
              />
              {errors.admin_password && (
                <span className="error-text">{errors.admin_password}</span>
              )}
            </div>
          </div>

          {apiError && (
            <div className="api-error">
              {apiError}
            </div>
          )}

          <button
            type="submit"
            className="submit-button"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Creating Account...' : 'Create Institution Account'}
          </button>

          <p className="login-link">
            Already have an account?{' '}
            <a href="/institution/login">Log in here</a>
          </p>
        </form>
      </div>
    </div>
  );
};
