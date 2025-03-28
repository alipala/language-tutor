'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

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
      className="w-full max-w-md bg-white dark:bg-slate-800/90 backdrop-blur-sm rounded-xl shadow-xl overflow-hidden border border-slate-200 dark:border-slate-700"
      initial="hidden"
      animate="visible"
      variants={formVariants}
    >
      <div className="p-8">
        <motion.h2 
          className="text-2xl font-bold text-center mb-6 text-slate-900 dark:text-white bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-purple-600"
          variants={itemVariants}
        >
          {type === 'login' ? 'Welcome Back' : 'Create Account'}
        </motion.h2>
        
        {error && (
          <motion.div 
            className="mb-6 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 rounded-lg text-sm"
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
              <label htmlFor="name" className="text-sm font-medium text-slate-700 dark:text-slate-200">
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
            <label htmlFor="email" className="text-sm font-medium text-slate-700 dark:text-slate-200">
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
            <label htmlFor="password" className="text-sm font-medium text-slate-700 dark:text-slate-200">
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
                className="text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300 transition-colors"
              >
                Forgot password?
              </a>
            </motion.div>
          )}
          
          <motion.div variants={itemVariants}>
            <motion.button
              type="submit"
              className="w-full py-2.5 px-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-medium rounded-lg transition-all duration-300 transform"
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
            <motion.button
              onClick={onGoogleAuth}
              className="w-full flex items-center justify-center px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-slate-700 hover:bg-gray-50 dark:hover:bg-slate-600 transition-all duration-300"
              variants={buttonVariants}
              whileHover="hover"
              whileTap="tap"
              disabled={isLoading}
            >
              <svg className="h-5 w-5 mr-2" viewBox="0 0 24 24" width="24" height="24">
                <g transform="matrix(1, 0, 0, 1, 27.009001, -39.238998)">
                  <path fill="#4285F4" d="M -3.264 51.509 C -3.264 50.719 -3.334 49.969 -3.454 49.239 L -14.754 49.239 L -14.754 53.749 L -8.284 53.749 C -8.574 55.229 -9.424 56.479 -10.684 57.329 L -10.684 60.329 L -6.824 60.329 C -4.564 58.239 -3.264 55.159 -3.264 51.509 Z" />
                  <path fill="#34A853" d="M -14.754 63.239 C -11.514 63.239 -8.804 62.159 -6.824 60.329 L -10.684 57.329 C -11.764 58.049 -13.134 58.489 -14.754 58.489 C -17.884 58.489 -20.534 56.379 -21.484 53.529 L -25.464 53.529 L -25.464 56.619 C -23.494 60.539 -19.444 63.239 -14.754 63.239 Z" />
                  <path fill="#FBBC05" d="M -21.484 53.529 C -21.734 52.809 -21.864 52.039 -21.864 51.239 C -21.864 50.439 -21.724 49.669 -21.484 48.949 L -21.484 45.859 L -25.464 45.859 C -26.284 47.479 -26.754 49.299 -26.754 51.239 C -26.754 53.179 -26.284 54.999 -25.464 56.619 L -21.484 53.529 Z" />
                  <path fill="#EA4335" d="M -14.754 43.989 C -12.984 43.989 -11.404 44.599 -10.154 45.789 L -6.734 42.369 C -8.804 40.429 -11.514 39.239 -14.754 39.239 C -19.444 39.239 -23.494 41.939 -25.464 45.859 L -21.484 48.949 C -20.534 46.099 -17.884 43.989 -14.754 43.989 Z" />
                </g>
              </svg>
              <span>Continue with Google</span>
            </motion.button>
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
