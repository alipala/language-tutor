'use client';

import { useRouter } from 'next/navigation';
import { useState, useEffect, createContext, useContext, ReactNode } from 'react';
import logger from './logger';

// API base URL
// In Railway deployment, the API is served from the same domain
const isRailway = typeof window !== 'undefined' && (
  window.location.hostname.includes('railway.app') || 
  window.location.hostname === 'mytacoai.com'
);
const API_URL = isRailway 
  ? '' // Empty string means same domain, which is correct for Railway
  : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');

// Types
export interface User {
  _id: string;
  name: string;
  email: string;
  preferred_language?: string;
  preferred_level?: string;
  last_assessment_data?: any;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  googleLogin: (token: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  forgotPassword: (email: string) => Promise<void>;
  resetPassword: (token: string, newPassword: string) => Promise<void>;
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider component
export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check if user is logged in on mount
    const checkAuth = async () => {
      try {
        // Check if we're in Railway environment for additional logging
        const isRailwayEnv = typeof window !== 'undefined' && (
          window.location.hostname.includes('railway.app') || 
          window.location.hostname === 'mytacoai.com'
        );
        if (isRailwayEnv) {
          logger.debug('Running auth check in Railway environment');
          logger.debug('API_URL configured for Railway');
        }
        
        // Try to get token from localStorage
        let token;
        try {
          token = localStorage.getItem('token');
        } catch (storageErr) {
          logger.error('Error accessing localStorage:', storageErr);
          // Continue without token
        }
        
        if (token) {
          logger.debug('Checking authentication with token');
          
          // Determine the correct URL to use
          const authUrl = isRailway ? '/auth/me' : `${API_URL}/auth/me`;
          logger.debug('Using auth URL for authentication check');
          
          try {
            const response = await fetch(authUrl, {
              method: 'GET',
              headers: {
                'Authorization': `Bearer ${token}`,
                'Accept': 'application/json',
                'Content-Type': 'application/json'
              },
              credentials: 'omit',  // Don't send cookies for cross-origin requests
              mode: 'cors'  // Explicitly use CORS mode
            });

            logger.debug('Auth check response received');
            
            if (response.ok) {
              const userData = await response.json();
              logger.auth('User authentication successful', userData._id);
              
              // Store user data in localStorage
              try {
                localStorage.setItem('userData', JSON.stringify(userData));
              } catch (storageErr) {
                logger.error('Error storing user data in localStorage:', storageErr);
                // Continue without storing in localStorage
              }
              
              setUser(userData);
            } else {
              // Token is invalid or expired
              logger.debug('Token invalid or expired, clearing');
              try {
                localStorage.removeItem('token');
              } catch (storageErr) {
                logger.error('Error removing token from localStorage:', storageErr);
              }
              setUser(null);
            }
          } catch (fetchErr) {
            console.error('Fetch error during auth check:', fetchErr);
            // Try to recover with cached user data if available
            try {
              const cachedUserData = localStorage.getItem('userData');
              if (cachedUserData) {
                console.log('Recovering with cached user data');
                const userData = JSON.parse(cachedUserData);
                setUser(userData);
              } else {
                setUser(null);
              }
            } catch (cacheErr) {
              console.error('Error recovering with cached data:', cacheErr);
              setUser(null);
            }
          }
        } else {
          console.log('No token found in localStorage');
          setUser(null);
        }
      } catch (err) {
        console.error('Auth check error:', err);
        // Try to recover with cached user data if available
        try {
          const cachedUserData = localStorage.getItem('userData');
          if (cachedUserData) {
            console.log('Recovering with cached user data after error');
            const userData = JSON.parse(cachedUserData);
            setUser(userData);
          } else {
            setUser(null);
          }
        } catch (cacheErr) {
          console.error('Error recovering with cached data:', cacheErr);
          setUser(null);
        }
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  // Login function
  const login = async (email: string, password: string) => {
    setLoading(true);
    setError(null);

    try {
      logger.userAction('Login attempt', email);
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ email, password }),
        mode: 'cors',
        credentials: 'omit' // Don't send cookies for cross-origin requests
      });

      logger.debug('Login response received');

      if (!response.ok) {
        const errorData = await response.json();
        logger.apiError('/auth/login', errorData);
        throw new Error(errorData.detail || 'Login failed');
      }

      const data = await response.json();
      logger.auth('Login successful');
      
      // Save token to localStorage
      localStorage.setItem('token', data.access_token);
      logger.debug('Authentication token saved');
      
      // Set user data
      const userData = {
        _id: data.user_id,
        name: data.name,
        email: data.email
      };
      
      // Store user data in localStorage
      localStorage.setItem('userData', JSON.stringify(userData));
      setUser(userData);
      logger.auth('User session established', userData._id);

      // Save user preferences if available
      if (data.preferred_language) {
        sessionStorage.setItem('selectedLanguage', data.preferred_language);
      }
      
      if (data.preferred_level) {
        sessionStorage.setItem('selectedLevel', data.preferred_level);
      }
    } catch (err: any) {
      console.error('Login error:', err);
      setError(err.message || 'Login failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Google login function
  const googleLogin = async (token: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/auth/google-login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ token })
      });

      if (!response.ok) {
        const error = await response.json();
        if (response.status === 403 && error.detail?.includes('Email not verified')) {
          throw new Error('EMAIL_NOT_VERIFIED');
        }
        throw new Error(error.detail || 'Login failed');
      }

      const data = await response.json();
      
      // Save token to localStorage
      localStorage.setItem('token', data.access_token);
      
      // Set user data
      setUser({
        _id: data.user_id,
        name: data.name,
        email: data.email
      });

      // Save user preferences if available
      if (data.preferred_language) {
        sessionStorage.setItem('selectedLanguage', data.preferred_language);
      }
      
      if (data.preferred_level) {
        sessionStorage.setItem('selectedLevel', data.preferred_level);
      }
    } catch (err: any) {
      setError(err.message || 'Google login failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Signup function
  const signup = async (name: string, email: string, password: string) => {
    setLoading(true);
    setError(null);
    
    console.log('Signing up with:', { name, email });
    console.log('API URL:', API_URL);

    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        mode: 'cors',
        credentials: 'omit', // Don't send cookies for cross-origin requests
        body: JSON.stringify({ name, email, password })
      });

      console.log('Signup response status:', response.status);
      
      if (!response.ok) {
        let errorMessage = 'Signup failed';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
          console.error('Signup error details:', errorData);
        } catch (e) {
          console.error('Could not parse error response:', e);
        }
        throw new Error(errorMessage);
      }

      const userData = await response.json();
      console.log('Signup successful, user created:', userData);
      
      // Don't automatically login after signup - user needs to verify email first
      // The signup page will handle showing the verification message
      console.log('Signup completed successfully. User needs to verify email before login.');
      
    } catch (err: any) {
      console.error('Signup error:', err);
      setError(err.message || 'Signup failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Logout function
  const logout = () => {
    // Remove token and user data from localStorage
    localStorage.removeItem('token');
    localStorage.removeItem('userData');
    
    // Clear user data
    setUser(null);
    
    // Clear session storage
    sessionStorage.clear();
  };

  // Forgot password function
  const forgotPassword = async (email: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/auth/forgot-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Password reset request failed');
      }
    } catch (err: any) {
      setError(err.message || 'Password reset request failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Reset password function
  const resetPassword = async (token: string, new_password: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/auth/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ token, new_password })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Password reset failed');
      }
    } catch (err: any) {
      setError(err.message || 'Password reset failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const value = {
    user,
    loading,
    error,
    login,
    googleLogin,
    signup,
    logout,
    forgotPassword,
    resetPassword
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Custom hook to use the auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Hook for protected routes
export const useProtectedRoute = () => {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push('/auth/login');
    }
  }, [user, loading, router]);

  return { user, loading };
};
