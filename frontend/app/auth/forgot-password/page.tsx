'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/auth';

export default function ForgotPasswordPage() {
  const router = useRouter();
  const { forgotPassword, error: authError, loading: authLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Sync auth state with local state
  useEffect(() => {
    if (authError) {
      setError(authError);
    }
    setIsLoading(authLoading);
  }, [authError, authLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      console.log('Password reset requested for:', email);
      await forgotPassword(email);
      
      // Show success message
      setIsLoading(false);
      setIsSubmitted(true);
    } catch (err: any) {
      console.error('Password reset error:', err);
      setError(err.message || 'Failed to send reset link. Please try again.');
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col app-background">
      {/* Header with logo */}
      <header className="w-full p-4 md:p-6">
        <div className="container mx-auto">
          <Link href="/">
            <h1 className="text-2xl md:text-3xl font-bold text-white">
              Your Smart Language Coach
            </h1>
          </Link>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-grow flex items-center justify-center p-4">
        <div className="max-w-md mx-auto bg-white p-8 rounded-md shadow-xl overflow-hidden border-2 border-[#4ECFBF]">
          <h2 className="text-2xl font-bold text-center mb-6 text-gray-800">
            {isSubmitted ? 'Check Your Email' : 'Forgot Password'}
          </h2>
          
          {error && (
            <div className="mb-4 p-3 glass-card border border-red-400/30 text-red-100 rounded-md text-sm bg-red-500/10">
              {error}
            </div>
          )}
          
          {isSubmitted ? (
            <div className="text-center">
              <div className="mb-4 mx-auto w-16 h-16 flex items-center justify-center rounded-full bg-green-500/20 border border-green-400/30">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p className="text-white/80 mb-6">
                We've sent a password reset link to <strong className="text-white">{email}</strong>. Please check your email and follow the instructions to reset your password.
              </p>
              <div className="flex flex-col space-y-3">
                <div className="field btn h-[50px] w-full mt-5 rounded-md relative overflow-hidden">
                  <div 
                    className="btn-layer h-full w-[300%] absolute left-[-100%] bg-gradient-to-r from-purple-600 via-pink-500 to-purple-600 rounded-md"
                    style={{transition: 'all 0.4s ease'}}
                  ></div>
                  <Link href="/auth/login" className="block">
                    <button
                      type="button"
                      className="h-full w-full z-[1] relative bg-transparent border-none text-white px-0 rounded-md text-lg font-medium cursor-pointer"
                    >
                      Return to Sign In
                    </button>
                  </Link>
                </div>
                <button 
                  onClick={() => setIsSubmitted(false)}
                  className="text-sm text-pink-400 hover:text-pink-300 transition-colors font-medium"
                >
                  Try another email
                </button>
              </div>
            </div>
          ) : (
            <>
              <p className="mb-6 text-gray-600">
                Enter your email address and we'll send you a link to reset your password.
              </p>
              
              <form onSubmit={handleSubmit}>
                <div className="field h-[50px] w-full mt-5">
                  <input 
                    type="email" 
                    placeholder="Email Address" 
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="h-full w-full outline-none pl-4 rounded-md border border-[#4ECFBF] bg-white text-gray-800 placeholder-gray-500 text-base transition-all duration-300 focus:border-[#3db3a7]"
                    style={{transition: 'all 0.3s ease'}}
                  />
                </div>
                
                <div className="field btn h-[50px] w-full mt-5 rounded-md relative overflow-hidden">
                  <div 
                    className="btn-layer h-full w-[300%] absolute left-[-100%] bg-gradient-to-r from-purple-600 via-pink-500 to-purple-600 rounded-md"
                    style={{transition: 'all 0.4s ease'}}
                  ></div>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="h-full w-full z-[1] relative bg-white border-2 border-[#4ECFBF] text-[#4ECFBF] px-0 rounded-md text-lg font-medium cursor-pointer hover:bg-gray-50 transition-colors duration-300"
                  >
                    {isLoading ? (
                      <div className="flex items-center justify-center">
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-[#4ECFBF]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span>Sending...</span>
                      </div>
                    ) : (
                      'Send Reset Link'
                    )}
                  </button>
                </div>
              </form>
              
              <div className="signup-link text-center mt-7">
                <span className="text-gray-600 text-sm">Remember your password?</span>
                <Link
                  href="/auth/login"
                  className="ml-1 text-[#4ECFBF] hover:text-[#3db3a7] transition-colors font-medium underline"
                >
                  Sign in
                </Link>
              </div>
            </>
          )}
        </div>
      </main>
      
      {/* Footer */}
      <footer className="w-full p-4 text-center text-xs text-white/60">
        <p>
          Need help?{' '}
          <a href="#" className="text-pink-400 hover:text-pink-300 transition-colors font-medium">
            Contact support
          </a>
        </p>
      </footer>
    </div>
  );
}
