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
    <nav className="w-full bg-white dark:bg-slate-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <div className="container mx-auto px-4 py-3 flex justify-between items-center">
        {/* Logo */}
        <div 
          className="flex items-center cursor-pointer"
          onClick={() => navigateTo('/')}
        >
          <h1 className="text-xl font-bold gradient-text dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-r dark:from-indigo-200 dark:to-purple-300">
            Language Tutor
          </h1>
        </div>

        {/* Navigation Links */}
        <div className="hidden md:flex items-center space-x-6">
          <button 
            onClick={() => navigateTo('/language-selection')}
            className="text-gray-600 hover:text-indigo-600 dark:text-gray-300 dark:hover:text-indigo-400"
          >
            Practice
          </button>
          
          {/* User Menu (when logged in) */}
          {user ? (
            <div className="relative user-menu-container">
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="flex items-center space-x-2 text-gray-600 hover:text-indigo-600 dark:text-gray-300 dark:hover:text-indigo-400"
              >
                <span>{user.name}</span>
                <svg xmlns="http://www.w3.org/2000/svg" className={`h-4 w-4 transition-transform ${isMenuOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              {/* Dropdown Menu */}
              {isMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-slate-800 rounded-md shadow-lg py-1 z-10 border border-gray-200 dark:border-gray-700">
                  <button
                    onClick={() => navigateTo('/profile')}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-slate-700"
                  >
                    Your Profile
                  </button>
                  <button
                    onClick={handleLogout}
                    className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100 dark:text-red-400 dark:hover:bg-slate-700"
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
                className="text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300"
              >
                Sign In
              </button>
              <button
                onClick={() => navigateTo('/auth/signup')}
                className="px-4 py-2 rounded-md bg-indigo-600 text-white hover:bg-indigo-700"
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
            className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white focus:outline-none"
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
        <div className="md:hidden bg-white dark:bg-slate-800 py-2 px-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={() => {
              navigateTo('/language-selection');
              setIsMenuOpen(false);
            }}
            className="block w-full text-left py-2 text-gray-600 hover:text-indigo-600 dark:text-gray-300 dark:hover:text-indigo-400"
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
                className="block w-full text-left py-2 text-gray-600 hover:text-indigo-600 dark:text-gray-300 dark:hover:text-indigo-400"
              >
                Your Profile
              </button>
              <button
                onClick={() => {
                  handleLogout();
                  setIsMenuOpen(false);
                }}
                className="block w-full text-left py-2 text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
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
                className="block w-full text-left py-2 text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300"
              >
                Sign In
              </button>
              <button
                onClick={() => {
                  navigateTo('/auth/signup');
                  setIsMenuOpen(false);
                }}
                className="block w-full text-left py-2 text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300"
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
