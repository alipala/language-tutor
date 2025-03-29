'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth';

export default function NavBar() {
  const { user, logout } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (isMenuOpen && !target.closest('.user-menu-container')) {
        setIsMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isMenuOpen]);

  const handleLogout = () => {
    logout();
    // Use direct window.location.href for reliable navigation in Railway
    const fullUrl = `${window.location.origin}/`;
    window.location.href = fullUrl;
  };

  const navigateTo = (path: string) => {
    // Use direct window.location.href for reliable navigation in Railway
    const fullUrl = `${window.location.origin}${path}`;
    window.location.href = fullUrl;
  };

  return (
    <nav className="w-full bg-transparent backdrop-blur-sm border-b border-white/20">
      <div className="container mx-auto px-4 py-3 flex justify-between items-center">
        {/* Logo */}
        <div 
          className="flex items-center cursor-pointer"
          onClick={() => navigateTo('/')}
        >
          <h1 className="text-xl font-bold text-white">
            Language Tutor
          </h1>
        </div>

        {/* Navigation Links */}
        <div className="hidden md:flex items-center space-x-6">
          <button 
            onClick={() => navigateTo('/language-selection')}
            className="text-white/80 hover:text-white"
          >
            Practice
          </button>
          
          {/* User Menu (when logged in) */}
          {user ? (
            <div className="relative user-menu-container">
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="flex items-center space-x-2 text-white/80 hover:text-white"
              >
                <span>{user.name}</span>
                <svg xmlns="http://www.w3.org/2000/svg" className={`h-4 w-4 transition-transform ${isMenuOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              {/* Dropdown Menu */}
              {isMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 glass-card rounded-md shadow-lg py-1 z-10 border border-white/20">
                  <button
                    onClick={() => navigateTo('/profile')}
                    className="block w-full text-left px-4 py-2 text-sm text-white/80 hover:bg-white/10"
                  >
                    Your Profile
                  </button>
                  <button
                    onClick={handleLogout}
                    className="block w-full text-left px-4 py-2 text-sm text-red-300 hover:bg-white/10"
                  >
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigateTo('/auth/login')}
                className="text-white/80 hover:text-white"
              >
                Sign In
              </button>
              <button
                onClick={() => navigateTo('/auth/signup')}
                className="px-4 py-2 rounded-lg glass-card border border-white/20 text-white hover:bg-white/10"
              >
                Sign Up
              </button>
            </div>
          )}
        </div>

        {/* Mobile Menu Button */}
        <div className="md:hidden">
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="text-white/80 hover:text-white focus:outline-none"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {isMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="md:hidden glass-card border border-white/20 shadow-lg mt-2 mx-4 rounded-lg overflow-hidden py-2 px-4">
          <button
            onClick={() => {
              navigateTo('/language-selection');
              setIsMenuOpen(false);
            }}
            className="block w-full text-left py-2 text-white/80 hover:text-white"
          >
            Practice
          </button>
          
          {user ? (
            <>
              <button
                onClick={() => {
                  navigateTo('/profile');
                  setIsMenuOpen(false);
                }}
                className="block w-full text-left py-2 text-white/80 hover:text-white"
              >
                Your Profile
              </button>
              <button
                onClick={() => {
                  handleLogout();
                  setIsMenuOpen(false);
                }}
                className="block w-full text-left py-2 text-red-300 hover:text-red-200"
              >
                Sign Out
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => {
                  navigateTo('/auth/login');
                  setIsMenuOpen(false);
                }}
                className="block w-full text-left py-2 text-white/80 hover:text-white"
              >
                Sign In
              </button>
              <button
                onClick={() => {
                  navigateTo('/auth/signup');
                  setIsMenuOpen(false);
                }}
                className="block w-full text-left py-2 text-white/80 hover:text-white"
              >
                Sign Up
              </button>
            </>
          )}
        </div>
      )}
    </nav>
  );
}
