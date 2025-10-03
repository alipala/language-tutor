import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ConsentScreen } from '../../components/institutional/ConsentScreen';
import './LearnerSignup.css';

interface SignupFormData {
  name: string;
  email: string;
  password: string;
  institution_code: string;
}

export const LearnerSignup: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<SignupFormData>({
    name: '',
    email: '',
    password: '',
    institution_code: ''
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [showConsent, setShowConsent] = useState(false);
  const [signupResult, setSignupResult] = useState<any>(null);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    if (!formData.institution_code.trim()) {
      newErrors.institution_code = 'Institution code is required';
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
      const response = await fetch('/api/v1/learners/self-signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Signup failed');
      }

      const result = await response.json();

      if (result.requires_consent) {
        setSignupResult(result);
        setShowConsent(true);
      } else {
        // Direct login if no consent needed (shouldn't happen)
        navigate('/dashboard');
      }
    } catch (error: any) {
      setApiError(error.message || 'Signup failed. Please try again.');
      setIsSubmitting(false);
    }
  };

  const handleConsentAccept = () => {
    // Store auth token if provided
    navigate('/dashboard');
  };

  const handleConsentDecline = () => {
    // User declined - offer individual account option
    setShowConsent(false);
    setApiError(
      'You declined consent. You can still use MyTaco AI as an individual learner.'
    );
  };

  const handleChange = (field: keyof SignupFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user types
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  if (showConsent && signupResult) {
    return (
      <ConsentScreen
        institutionName={signupResult.institution_name || 'Institution'}
        tutorName={signupResult.tutor_name || 'Your Tutor'}
        learnerId={signupResult.user_id}
        institutionId={signupResult.institution_id}
        tutorId={signupResult.tutor_id}
        onAccept={handleConsentAccept}
        onDecline={handleConsentDecline}
      />
    );
  }

  return (
    <div className="learner-signup-page">
      <div className="signup-container">
        <div className="signup-header">
          <h1>Join Your Institution</h1>
          <p>Sign up with your institution code to get started</p>
        </div>

        <form onSubmit={handleSubmit} className="signup-form">
          <div className="form-group">
            <label htmlFor="institution_code">Institution Code *</label>
            <input
              id="institution_code"
              type="text"
              value={formData.institution_code}
              onChange={(e) => handleChange('institution_code', e.target.value.toUpperCase())}
              placeholder="e.g., LINCOLN2025"
              className={errors.institution_code ? 'error' : ''}
            />
            {errors.institution_code && (
              <span className="error-text">{errors.institution_code}</span>
            )}
            <small className="help-text">
              Ask your institution for this code
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="name">Your Name *</label>
            <input
              id="name"
              type="text"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              placeholder="John Doe"
              className={errors.name ? 'error' : ''}
            />
            {errors.name && <span className="error-text">{errors.name}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="email">Email Address *</label>
            <input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => handleChange('email', e.target.value)}
              placeholder="you@example.com"
              className={errors.email ? 'error' : ''}
            />
            {errors.email && <span className="error-text">{errors.email}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="password">Password *</label>
            <input
              id="password"
              type="password"
              value={formData.password}
              onChange={(e) => handleChange('password', e.target.value)}
              placeholder="At least 8 characters"
              className={errors.password ? 'error' : ''}
            />
            {errors.password && (
              <span className="error-text">{errors.password}</span>
            )}
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
            {isSubmitting ? 'Creating Account...' : 'Create Account'}
          </button>

          <p className="switch-link">
            Want to learn independently?{' '}
            <a href="/signup">Sign up as individual learner</a>
          </p>
        </form>
      </div>
    </div>
  );
};
