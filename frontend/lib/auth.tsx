'use client';

import { useRouter } from 'next/navigation';
import { useState, useEffect, createContext, useContext, ReactNode } from 'react';

// API base URL
// In Railway deployment, the API is served from the same domain
const isRailway = typeof window !== 'undefined' && window.location.hostname.includes('railway.app');
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
        const isRailway = typeof window !== 'undefined' && window.location.hostname.includes('railway.app');
        if (isRailway) {
          console.log('Running auth check in Railway environment');
          console.log('API_URL:', API_URL);
        }
        
        // Try to get token from localStorage
        let token;
        try {
          token = localStorage.getItem('token');
        } catch (storageErr) {
          console.error('Error accessing localStorage:', storageErr);
          // Continue without token
        }
        
        if (token) {
          console.log('Checking authentication with token');
          
          // Determine the correct URL to use
          const authUrl = isRailway ? '/auth/me' : `${API_URL}/auth/me`;
          console.log('Using auth URL:', authUrl);
          
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

            console.log('Auth check response status:', response.status);
            
            if (response.ok) {
              const userData = await response.json();
              console.log('User data retrieved:', userData);
              
              // Store user data in localStorage
              try {
                localStorage.setItem('userData', JSON.stringify(userData));
              } catch (storageErr) {
                console.error('Error storing user data in localStorage:', storageErr);
                // Continue without storing in localStorage
              }
              
              setUser(userData);
            } else {
              // Token is invalid or expired
              console.log('Token invalid or expired, clearing');
              try {
                localStorage.removeItem('token');
              } catch (storageErr) {
                console.error('Error removing token from localStorage:', storageErr);
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
      console.log('Attempting login for:', email);
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

      console.log('Login response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Login error:', errorData);
        throw new Error(errorData.detail || 'Login failed');
      }

      const data = await response.json();
      console.log('Login successful, token received');
      
      // Save token to localStorage
      localStorage.setItem('token', data.access_token);
      console.log('Token saved to localStorage');
      
      // Set user data
      const userData = {
        _id: data.user_id,
        name: data.name,
        email: data.email
      };
      
      // Store user data in localStorage
      localStorage.setItem('userData', JSON.stringify(userData));
      setUser(userData);
      console.log('User data set in context and stored in localStorage');

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
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Google login failed');
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
      
      // After signup, automatically log in
      console.log('Proceeding to login after successful signup');
      await login(email, password);
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
