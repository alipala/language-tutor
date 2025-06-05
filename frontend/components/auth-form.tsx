'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import GoogleAuthButton from './google-auth-button';

interface AuthFormProps {
  type: 'login' | 'signup';
  onSubmit: (data: any) => Promise<void>;
  onGoogleAuth?: () => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export const AuthForm: React.FC<AuthFormProps> = ({
  type,
  onSubmit,
  onGoogleAuth,
  isLoading,
  error
}) => {
  const router = useRouter();
  
  // Form state
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  
  // Form validation with user-friendly messages
  const validateForm = () => {
    const errors: Record<string, string> = {};
    
    if (!email.trim()) {
      errors.email = 'Please enter your email address';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      errors.email = 'Please enter a valid email address (e.g., john@example.com)';
    }
    
    if (!password) {
      errors.password = 'Please enter your password';
    } else if (password.length < 6) {
      errors.password = 'Password must be at least 6 characters long';
    }
    
    if (type === 'signup') {
      if (!name.trim()) {
        errors.name = 'Please enter your full name';
      } else if (name.trim().length < 2) {
        errors.name = 'Please enter your full name (at least 2 characters)';
      }
      
      if (!confirmPassword) {
        errors.confirmPassword = 'Please confirm your password';
      } else if (password !== confirmPassword) {
        errors.confirmPassword = 'Passwords do not match. Please try again';
      }
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Real-time validation for better UX
  const validateField = (fieldName: string, value: string) => {
    const errors = { ...validationErrors };
    
    switch (fieldName) {
      case 'name':
        if (value.trim().length === 0) {
          errors.name = 'Please enter your full name';
        } else if (value.trim().length < 2) {
          errors.name = 'Please enter your full name (at least 2 characters)';
        } else {
          delete errors.name;
        }
        break;
      case 'email':
        if (value.trim().length === 0) {
          errors.email = 'Please enter your email address';
        } else if (!/\S+@\S+\.\S+/.test(value)) {
          errors.email = 'Please enter a valid email address';
        } else {
          delete errors.email;
        }
        break;
      case 'password':
        if (value.length === 0) {
          errors.password = 'Please enter your password';
        } else if (value.length < 6) {
          errors.password = 'Password must be at least 6 characters long';
        } else {
          delete errors.password;
        }
        // Also validate confirm password if it exists
        if (type === 'signup' && confirmPassword && value !== confirmPassword) {
          errors.confirmPassword = 'Passwords do not match. Please try again';
        } else if (type === 'signup' && confirmPassword && value === confirmPassword) {
          delete errors.confirmPassword;
        }
        break;
      case 'confirmPassword':
        if (value.length === 0) {
          errors.confirmPassword = 'Please confirm your password';
        } else if (password !== value) {
          errors.confirmPassword = 'Passwords do not match. Please try again';
        } else {
          delete errors.confirmPassword;
        }
        break;
    }
    
    setValidationErrors(errors);
  };
  
  // Form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Clear any existing validation errors
    setValidationErrors({});
    
    if (!validateForm()) {
      return;
    }
    
    const data = type === 'login' 
      ? { email, password } 
      : { name, email, password };
      
    await onSubmit(data);
  };
  
  // Handle form type switching with proper URL navigation
  const switchToSignup = () => {
    router.push('/auth/signup');
  };
  
  const switchToLogin = () => {
    router.push('/auth/login');
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-white/95 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 overflow-hidden">
        {/* Tab Navigation */}
        <div className="flex bg-gray-50 border-b border-gray-200">
          <button
            type="button"
            onClick={switchToLogin}
            className={`flex-1 py-3 px-4 text-center font-medium transition-all duration-200 ${
              type === 'login'
                ? 'bg-white text-[#4ECFBF] border-b-2 border-[#4ECFBF] shadow-sm'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={switchToSignup}
            className={`flex-1 py-3 px-4 text-center font-medium transition-all duration-200 ${
              type === 'signup'
                ? 'bg-white text-[#4ECFBF] border-b-2 border-[#4ECFBF] shadow-sm'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
            }`}
          >
            Sign Up
          </button>
        </div>

        {/* Form Content */}
        <div className="p-4 sm:p-6">
          {/* Header */}
          <div className="text-center mb-4">
            <h2 className="text-lg sm:text-xl font-bold text-gray-800 mb-1">
              {type === 'login' ? 'Welcome Back' : 'Create Your Account'}
            </h2>
            <p className="text-gray-600 text-xs sm:text-sm">
              {type === 'login' 
                ? 'Sign in to continue your language learning journey' 
                : 'Join us and start learning languages today'
              }
            </p>
          </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center">
              <svg className="w-4 h-4 text-red-500 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <p className="text-red-700 text-xs sm:text-sm font-medium">{error}</p>
            </div>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name field for signup */}
          {type === 'signup' && (
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                Full Name
              </label>
              <input
                id="name"
                type="text"
                placeholder="Enter your full name"
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  validateField('name', e.target.value);
                }}
                onBlur={(e) => validateField('name', e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-[#4ECFBF] transition-colors duration-200 text-gray-900 placeholder-gray-500 bg-white"
                required
              />
              {validationErrors.name && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.name}</p>
              )}
            </div>
          )}

          {/* Email field */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                validateField('email', e.target.value);
              }}
              onBlur={(e) => validateField('email', e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-[#4ECFBF] transition-colors duration-200 text-gray-900 placeholder-gray-500 bg-white"
              required
            />
            {validationErrors.email && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.email}</p>
            )}
          </div>

          {/* Password field */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              id="password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                validateField('password', e.target.value);
              }}
              onBlur={(e) => validateField('password', e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-[#4ECFBF] transition-colors duration-200 text-gray-900 placeholder-gray-500 bg-white"
              required
            />
            {validationErrors.password && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.password}</p>
            )}
          </div>

          {/* Confirm Password field for signup */}
          {type === 'signup' && (
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                placeholder="Confirm your password"
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value);
                  validateField('confirmPassword', e.target.value);
                }}
                onBlur={(e) => validateField('confirmPassword', e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-[#4ECFBF] transition-colors duration-200 text-gray-900 placeholder-gray-500 bg-white"
                required
              />
              {validationErrors.confirmPassword && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.confirmPassword}</p>
              )}
            </div>
          )}

          {/* Forgot Password Link for login */}
          {type === 'login' && (
            <div className="text-right">
              <a 
                href="/auth/forgot-password" 
                className="text-sm text-[#4ECFBF] hover:text-[#3db3a7] font-medium transition-colors duration-200"
              >
                Forgot password?
              </a>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-[#4ECFBF] hover:bg-[#3db3a7] disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-semibold py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {type === 'login' ? 'Signing in...' : 'Creating account...'}
              </>
            ) : (
              type === 'login' ? 'Sign In' : 'Create Account'
            )}
          </button>
        </form>

        {/* Divider */}
        <div className="my-4">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-xs sm:text-sm">
              <span className="px-2 bg-white text-gray-500">
                Or continue with
              </span>
            </div>
          </div>
        </div>

        {/* Google Auth Button */}
        <div>
          <GoogleAuthButton 
            onSuccess={onGoogleAuth} 
            onError={(err) => console.error('Google auth error:', err)}
            disabled={isLoading}
          />
        </div>
        </div>
      </div>
    </div>
  );
};
