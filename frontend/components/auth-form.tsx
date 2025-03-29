'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import GoogleAuthButton from './google-auth-button';

// Define animation variants
const formVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      staggerChildren: 0.1,
      delayChildren: 0.2
    }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { 
      type: 'spring', 
      stiffness: 100,
      damping: 10
    }
  }
};

const buttonVariants = {
  idle: { scale: 1 },
  hover: { 
    scale: 1.05,
    boxShadow: '0px 0px 8px rgba(129, 140, 248, 0.6)',
    transition: {
      type: 'spring',
      stiffness: 400,
      damping: 10
    }
  },
  tap: { scale: 0.95 }
};

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
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [focusedField, setFocusedField] = useState<string | null>(null);

  const validateForm = () => {
    const errors: Record<string, string> = {};
    
    if (!email) {
      errors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      errors.email = 'Email is invalid';
    }
    
    if (!password) {
      errors.password = 'Password is required';
    } else if (password.length < 6) {
      errors.password = 'Password must be at least 6 characters';
    }
    
    if (type === 'signup') {
      if (!name) {
        errors.name = 'Name is required';
      }
      
      if (password !== confirmPassword) {
        errors.confirmPassword = 'Passwords do not match';
      }
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    const data = type === 'login' 
      ? { email, password } 
      : { name, email, password };
      
    await onSubmit(data);
  };

  return (
    <motion.div
      className="w-full max-w-md glass-card rounded-xl shadow-xl overflow-hidden border border-white/20"
      initial="hidden"
      animate="visible"
      variants={formVariants}
    >
      <div className="p-8">
        <motion.h2 
          className="text-2xl font-bold text-center mb-6 text-white"
          variants={itemVariants}
        >
          {type === 'login' ? 'Welcome Back' : 'Create Account'}
        </motion.h2>
        
        {error && (
          <motion.div 
            className="mb-6 p-3 glass-card border border-white/20 text-white/80 rounded-lg text-sm"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            {error}
          </motion.div>
        )}
        
        <motion.form onSubmit={handleSubmit} className="space-y-5" variants={formVariants}>
          {type === 'signup' && (
            <motion.div className="space-y-2" variants={itemVariants}>
              <label htmlFor="name" className="text-sm font-medium text-white">
                Full Name
              </label>
              <div className="relative">
                <Input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  onFocus={() => setFocusedField('name')}
                  onBlur={() => setFocusedField(null)}
                  placeholder="Enter your full name"
                  className={`w-full transition-all duration-300 border-slate-300 dark:border-slate-600 ${
                    focusedField === 'name' ? 'border-indigo-500 ring-2 ring-indigo-500/20' : ''
                  } ${validationErrors.name ? 'border-red-500 dark:border-red-500' : ''}`}
                />
                {validationErrors.name && (
                  <p className="mt-1 text-xs text-red-500">{validationErrors.name}</p>
                )}
                <motion.div 
                  className="absolute bottom-0 left-0 h-0.5 bg-gradient-to-r from-indigo-500 to-purple-600"
                  initial={{ width: 0 }}
                  animate={{ width: focusedField === 'name' ? '100%' : 0 }}
                  transition={{ duration: 0.3 }}
                />
              </div>
            </motion.div>
          )}
          
          <motion.div className="space-y-2" variants={itemVariants}>
            <label htmlFor="email" className="text-sm font-medium text-white">
              Email
            </label>
            <div className="relative">
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onFocus={() => setFocusedField('email')}
                onBlur={() => setFocusedField(null)}
                placeholder="Enter your email"
                className={`w-full transition-all duration-300 border-slate-300 dark:border-slate-600 ${
                  focusedField === 'email' ? 'border-indigo-500 ring-2 ring-indigo-500/20' : ''
                } ${validationErrors.email ? 'border-red-500 dark:border-red-500' : ''}`}
              />
              {validationErrors.email && (
                <p className="mt-1 text-xs text-red-500">{validationErrors.email}</p>
              )}
              <motion.div 
                className="absolute bottom-0 left-0 h-0.5 bg-gradient-to-r from-indigo-500 to-purple-600"
                initial={{ width: 0 }}
                animate={{ width: focusedField === 'email' ? '100%' : 0 }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </motion.div>
          
          <motion.div className="space-y-2" variants={itemVariants}>
            <label htmlFor="password" className="text-sm font-medium text-white">
              Password
            </label>
            <div className="relative">
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onFocus={() => setFocusedField('password')}
                onBlur={() => setFocusedField(null)}
                placeholder={type === 'login' ? "Enter your password" : "Create a password"}
                className={`w-full transition-all duration-300 border-slate-300 dark:border-slate-600 ${
                  focusedField === 'password' ? 'border-indigo-500 ring-2 ring-indigo-500/20' : ''
                } ${validationErrors.password ? 'border-red-500 dark:border-red-500' : ''}`}
              />
              {validationErrors.password && (
                <p className="mt-1 text-xs text-red-500">{validationErrors.password}</p>
              )}
              <motion.div 
                className="absolute bottom-0 left-0 h-0.5 bg-gradient-to-r from-indigo-500 to-purple-600"
                initial={{ width: 0 }}
                animate={{ width: focusedField === 'password' ? '100%' : 0 }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </motion.div>
          
          {type === 'signup' && (
            <motion.div className="space-y-2" variants={itemVariants}>
              <label htmlFor="confirm-password" className="text-sm font-medium text-slate-700 dark:text-slate-200">
                Confirm Password
              </label>
              <div className="relative">
                <Input
                  id="confirm-password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  onFocus={() => setFocusedField('confirmPassword')}
                  onBlur={() => setFocusedField(null)}
                  placeholder="Confirm your password"
                  className={`w-full transition-all duration-300 border-slate-300 dark:border-slate-600 ${
                    focusedField === 'confirmPassword' ? 'border-indigo-500 ring-2 ring-indigo-500/20' : ''
                  } ${validationErrors.confirmPassword ? 'border-red-500 dark:border-red-500' : ''}`}
                />
                {validationErrors.confirmPassword && (
                  <p className="mt-1 text-xs text-red-500">{validationErrors.confirmPassword}</p>
                )}
                <motion.div 
                  className="absolute bottom-0 left-0 h-0.5 bg-gradient-to-r from-indigo-500 to-purple-600"
                  initial={{ width: 0 }}
                  animate={{ width: focusedField === 'confirmPassword' ? '100%' : 0 }}
                  transition={{ duration: 0.3 }}
                />
              </div>
            </motion.div>
          )}
          
          {type === 'login' && (
            <motion.div 
              className="text-right text-sm"
              variants={itemVariants}
            >
              <a 
                href="/auth/forgot-password" 
                className="text-white/80 hover:text-white transition-colors"
              >
                Forgot password?
              </a>
            </motion.div>
          )}
          
          <motion.div variants={itemVariants}>
            <motion.button
              type="submit"
              className="w-full py-2.5 px-4 primary-button rounded-lg transition-all duration-300 transform"
              variants={buttonVariants}
              whileHover="hover"
              whileTap="tap"
              disabled={isLoading}
            >
              {isLoading ? (
                <div className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>{type === 'login' ? 'Signing in...' : 'Creating account...'}</span>
                </div>
              ) : (
                <span>{type === 'login' ? 'Sign In' : 'Sign Up'}</span>
              )}
            </motion.button>
          </motion.div>
        </motion.form>
        
        <motion.div 
          className="mt-6"
          variants={itemVariants}
        >
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300 dark:border-gray-600"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white dark:bg-slate-800 text-gray-500 dark:text-gray-400">
                Or continue with
              </span>
            </div>
          </div>
          
          <div className="mt-6">
            <GoogleAuthButton 
              onSuccess={() => console.log('Google auth success')} 
              onError={(err) => console.error('Google auth error:', err)}
              disabled={isLoading}
            />
          </div>
        </motion.div>
        
        <motion.p 
          className="mt-8 text-center text-sm text-gray-600 dark:text-gray-400"
          variants={itemVariants}
        >
          {type === 'login' ? "Don't have an account? " : "Already have an account? "}
          <a
            href={type === 'login' ? '/auth/signup' : '/auth/login'}
            className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300 transition-colors"
          >
            {type === 'login' ? 'Sign up' : 'Sign in'}
          </a>
        </motion.p>
      </div>
    </motion.div>
  );
};
