'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import GoogleAuthButton from './google-auth-button';

interface AuthFormProps {
  type: 'login' | 'signup';
  onSubmit: (data: any) => Promise<void>;
  onGoogleAuth?: () => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export const AuthForm: React.FC<AuthFormProps> = ({
  type: initialType,
  onSubmit,
  onGoogleAuth,
  isLoading,
  error
}) => {
  // Form state
  const [activeTab, setActiveTab] = useState<'login' | 'signup'>(initialType);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  
  // Refs for DOM manipulation (just like in the original HTML/CSS example)
  const titleLoginRef = useRef<HTMLDivElement>(null);
  const loginFormRef = useRef<HTMLFormElement>(null);
  const sliderTabRef = useRef<HTMLDivElement>(null);
  
  // Update active tab when type prop changes
  useEffect(() => {
    setActiveTab(initialType);
    updateFormPosition(initialType);
  }, [initialType]);
  
  // Function to update form position based on active tab (mimics the original JS)
  const updateFormPosition = (tab: 'login' | 'signup') => {
    if (loginFormRef.current && titleLoginRef.current && sliderTabRef.current) {
      if (tab === 'signup') {
        loginFormRef.current.style.marginLeft = '-50%';
        titleLoginRef.current.style.marginLeft = '-50%';
        sliderTabRef.current.style.left = '50%';
      } else {
        loginFormRef.current.style.marginLeft = '0%';
        titleLoginRef.current.style.marginLeft = '0%';
        sliderTabRef.current.style.left = '0%';
      }
    }
  };
  
  // Switch between login and signup tabs
  const switchTab = (tab: 'login' | 'signup') => {
    setActiveTab(tab);
    updateFormPosition(tab);
  };
  
  // Form validation
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
    
    if (activeTab === 'signup') {
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
  
  // Form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    const data = activeTab === 'login' 
      ? { email, password } 
      : { name, email, password };
      
    await onSubmit(data);
  };
  
  // Handle signup link click
  const handleSignupLinkClick = (e: React.MouseEvent) => {
    e.preventDefault();
    switchTab('signup');
  };

  return (
    <div className="wrapper max-w-md mx-auto bg-white/10 backdrop-blur-md p-8 rounded-md shadow-xl overflow-hidden border border-white/20">
      {/* Title text - exactly like the original example */}
      <div className="title-text flex w-[200%]">
        <div ref={titleLoginRef} className="title w-1/2 text-2xl font-bold text-center transition-all duration-600" style={{transition: 'all 0.6s cubic-bezier(0.68,-0.55,0.265,1.55)'}}>
          Login Form
        </div>
        <div className="title w-1/2 text-2xl font-bold text-center">
          Signup Form
        </div>
      </div>
      
      {/* Form container - following the original HTML structure */}
      <div className="form-container w-full overflow-hidden">
        {/* Slide controls */}
        <div className="slide-controls relative flex h-[50px] w-full overflow-hidden my-7 justify-between border border-white/30 rounded-md">
          <input 
            type="radio" 
            name="slide" 
            id="login" 
            checked={activeTab === 'login'} 
            onChange={() => switchTab('login')}
            className="hidden"
          />
          <input 
            type="radio" 
            name="slide" 
            id="signup" 
            checked={activeTab === 'signup'} 
            onChange={() => switchTab('signup')}
            className="hidden"
          />
          <label 
            htmlFor="login" 
            className={`slide login h-full w-full text-lg font-medium text-center leading-[48px] cursor-pointer z-[1] transition-all duration-600 ${activeTab === 'login' ? 'text-white' : 'text-white/70'}`}
            onClick={() => switchTab('login')}
            style={{transition: 'all 0.6s ease'}}
          >
            Login
          </label>
          <label 
            htmlFor="signup" 
            className={`slide signup h-full w-full text-lg font-medium text-center leading-[48px] cursor-pointer z-[1] transition-all duration-600 ${activeTab === 'signup' ? 'text-white' : 'text-white/70'}`}
            onClick={() => switchTab('signup')}
            style={{transition: 'all 0.6s ease'}}
          >
            Signup
          </label>
          <div 
            ref={sliderTabRef} 
            className="slider-tab absolute h-full w-1/2 left-0 z-0 rounded-md bg-gradient-to-r from-purple-600 to-pink-500"
            style={{transition: 'all 0.6s cubic-bezier(0.68,-0.55,0.265,1.55)'}}
          ></div>
        </div>
        
        {/* Form inner - exactly like the original example */}
        <div className="form-inner flex w-[200%]">
          {/* Login form */}
          <form 
            ref={loginFormRef} 
            onSubmit={handleSubmit} 
            className="login w-1/2"
            style={{transition: 'all 0.6s cubic-bezier(0.68,-0.55,0.265,1.55)'}}
          >
            {error && (
              <motion.div 
                className="mb-4 p-3 glass-card border border-red-400/30 text-red-100 rounded-md text-sm bg-red-500/10"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                {error}
              </motion.div>
            )}
            
            <div className="field h-[50px] w-full mt-5">
              <input 
                type="email" 
                placeholder="Email Address" 
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-full w-full outline-none pl-4 rounded-md border border-white/30 border-b-[2px] bg-white/10 backdrop-blur text-white placeholder-white/60 text-base transition-all duration-300 focus:border-pink-400"
                style={{transition: 'all 0.3s ease'}}
              />
              {validationErrors.email && (
                <p className="mt-1 text-xs text-red-400">{validationErrors.email}</p>
              )}
            </div>
            
            <div className="field h-[50px] w-full mt-5">
              <input 
                type="password" 
                placeholder="Password" 
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-full w-full outline-none pl-4 rounded-md border border-white/30 border-b-[2px] bg-white/10 backdrop-blur text-white placeholder-white/60 text-base transition-all duration-300 focus:border-pink-400"
                style={{transition: 'all 0.3s ease'}}
              />
              {validationErrors.password && (
                <p className="mt-1 text-xs text-red-400">{validationErrors.password}</p>
              )}
            </div>
            
            <div className="pass-link mt-1 text-right">
              <a href="/auth/forgot-password" className="text-pink-400 hover:text-pink-300 text-sm transition-colors font-medium">
                Forgot password?
              </a>
            </div>
            
            <div className="field btn h-[50px] w-full mt-5 rounded-md relative overflow-hidden">
              <div 
                className="btn-layer h-full w-[300%] absolute left-[-100%] bg-gradient-to-r from-purple-600 via-pink-500 to-purple-600 rounded-md"
                style={{transition: 'all 0.4s ease'}}
              ></div>
              <button
                type="submit"
                disabled={isLoading}
                className="h-full w-full z-[1] relative bg-transparent border-none text-white px-0 rounded-md text-lg font-medium cursor-pointer"
              >
                {isLoading ? (
                  <div className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Signing in...</span>
                  </div>
                ) : (
                  'Login'
                )}
              </button>
            </div>
            
            <div className="signup-link text-center mt-7">
              <span className="text-white/80 text-sm">Not a member?</span>
              <a
                href="#"
                onClick={handleSignupLinkClick}
                className="ml-1 text-pink-400 hover:text-pink-300 transition-colors font-medium"
              >
                Signup now
              </a>
            </div>
            
            <div className="mt-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-white/20"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-transparent text-white/60">
                    Or continue with
                  </span>
                </div>
              </div>
              
              <div className="mt-4">
                <GoogleAuthButton 
                  onSuccess={onGoogleAuth} 
                  onError={(err) => console.error('Google auth error:', err)}
                  disabled={isLoading}
                />
              </div>
            </div>
          </form>
          
          {/* Signup form */}
          <form 
            onSubmit={handleSubmit} 
            className="signup w-1/2"
            style={{transition: 'all 0.6s cubic-bezier(0.68,-0.55,0.265,1.55)'}}
          >
            {error && (
              <motion.div 
                className="mb-4 p-3 glass-card border border-red-400/30 text-red-100 rounded-md text-sm bg-red-500/10"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                {error}
              </motion.div>
            )}
            
            <div className="field h-[50px] w-full mt-5">
              <input 
                type="text" 
                placeholder="Full Name" 
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="h-full w-full outline-none pl-4 rounded-md border border-white/30 border-b-[2px] bg-white/10 backdrop-blur text-white placeholder-white/60 text-base transition-all duration-300 focus:border-pink-400"
                style={{transition: 'all 0.3s ease'}}
              />
              {validationErrors.name && (
                <p className="mt-1 text-xs text-red-400">{validationErrors.name}</p>
              )}
            </div>
            
            <div className="field h-[50px] w-full mt-5">
              <input 
                type="email" 
                placeholder="Email Address" 
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-full w-full outline-none pl-4 rounded-md border border-white/30 border-b-[2px] bg-white/10 backdrop-blur text-white placeholder-white/60 text-base transition-all duration-300 focus:border-pink-400"
                style={{transition: 'all 0.3s ease'}}
              />
              {validationErrors.email && (
                <p className="mt-1 text-xs text-red-400">{validationErrors.email}</p>
              )}
            </div>
            
            <div className="field h-[50px] w-full mt-5">
              <input 
                type="password" 
                placeholder="Password" 
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-full w-full outline-none pl-4 rounded-md border border-white/30 border-b-[2px] bg-white/10 backdrop-blur text-white placeholder-white/60 text-base transition-all duration-300 focus:border-pink-400"
                style={{transition: 'all 0.3s ease'}}
              />
              {validationErrors.password && (
                <p className="mt-1 text-xs text-red-400">{validationErrors.password}</p>
              )}
            </div>
            
            <div className="field h-[50px] w-full mt-5">
              <input 
                type="password" 
                placeholder="Confirm password" 
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="h-full w-full outline-none pl-4 rounded-md border border-white/30 border-b-[2px] bg-white/10 backdrop-blur text-white placeholder-white/60 text-base transition-all duration-300 focus:border-pink-400"
                style={{transition: 'all 0.3s ease'}}
              />
              {validationErrors.confirmPassword && (
                <p className="mt-1 text-xs text-red-400">{validationErrors.confirmPassword}</p>
              )}
            </div>
            
            <div className="field btn h-[50px] w-full mt-5 rounded-md relative overflow-hidden">
              <div 
                className="btn-layer h-full w-[300%] absolute left-[-100%] bg-gradient-to-r from-purple-600 via-pink-500 to-purple-600 rounded-md"
                style={{transition: 'all 0.4s ease'}}
              ></div>
              <button
                type="submit"
                disabled={isLoading}
                className="h-full w-full z-[1] relative bg-transparent border-none text-white px-0 rounded-md text-lg font-medium cursor-pointer"
              >
                {isLoading ? (
                  <div className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Creating account...</span>
                  </div>
                ) : (
                  'Signup'
                )}
              </button>
            </div>
            
            <div className="mt-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-white/20"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-transparent text-white/60">
                    Or continue with
                  </span>
                </div>
              </div>
              
              <div className="mt-4">
                <GoogleAuthButton 
                  onSuccess={onGoogleAuth} 
                  onError={(err) => console.error('Google auth error:', err)}
                  disabled={isLoading}
                />
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
