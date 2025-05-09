'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth';
import { useNavigation } from '@/lib/navigation';

export default function NavBar({ activeSection = '' }: { activeSection?: string }) {
  const { user, logout } = useAuth();
  const navigation = useNavigation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

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
    // Close the confirmation dialog
    setShowLogoutConfirm(false);
    // Close the menu
    setIsMenuOpen(false);
    // Navigate to home page after logout
    window.location.href = '/';
  };

  const navigateTo = (path: string) => {
    // Use navigation service for consistent navigation
    switch(path) {
      case '/':
        navigation.navigateToHome();
        break;
      case '/language-selection':
        navigation.navigateToLanguageSelection();
        break;
      case '/profile':
        navigation.navigateToProfile();
        break;
      case '/auth/login':
        navigation.navigateToLogin();
        break;
      case '/auth/signup':
        navigation.navigateToSignup();
        break;
      default:
        // For any other paths, use the navigate method
        navigation.navigate(path);
    }
  };

  // Keep the navbar fixed with the first section color (turquoise)
  let navbarClass = "w-full backdrop-blur-sm border-b border-white/20 transition-all duration-500 fixed top-0 left-0 right-0 z-50 navbar-section1";
  
  return (
    <nav className={navbarClass}>
      <div className="container mx-auto px-4 py-3 flex justify-between items-center">
        {/* Logo */}
        <div 
          className="flex items-center cursor-pointer"
          onClick={() => {
            // Clear navigation state before navigating to home
            // This prevents automatic redirection to level-selection
            navigation.clearNavigationState();
            // Clear specific keys that might cause redirects
            sessionStorage.removeItem('selectedLanguage');
            sessionStorage.removeItem('selectedLevel');
            // Navigate to home page
            navigation.navigateToHome();
          }}
        >
          <h1 className="text-xl font-bold text-white">
            Your Smart Language Coach
          </h1>
        </div>

        {/* Navigation Links */}
        <div className="hidden md:flex items-center space-x-6">
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
                <div className="absolute right-0 mt-2 w-48 bg-white/90 backdrop-blur-md rounded-md shadow-lg py-1 z-10 border border-white/30">
                  <button
                    onClick={() => {
                      navigateTo('/profile');
                      setIsMenuOpen(false);
                    }}
                    className="block w-full text-left px-4 py-3 text-sm text-[#3a9e92] font-medium hover:bg-[#3a9e92]/10"
                  >
                    Your Profile
                  </button>
                  <button
                    onClick={() => setShowLogoutConfirm(true)}
                    className="block w-full text-left px-4 py-3 text-sm text-[#e74c3c] font-medium hover:bg-[#e74c3c]/10"
                  >
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center">
              <button
                onClick={() => navigateTo('/auth/login')}
                className="login-button px-4 py-2 rounded-lg transition-all duration-300"
              >
                Login
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
                onClick={() => setShowLogoutConfirm(true)}
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
                Login
              </button>
            </>
          )}
        </div>
      )}
      
      {/* Logout Confirmation Dialog */}
      {showLogoutConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-800 rounded-lg max-w-md w-full p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">Sign Out</h3>
            <p className="text-slate-700 dark:text-slate-300 mb-4">Are you sure you want to sign out?</p>
            
            <div className="flex space-x-2 justify-end">
              <button
                onClick={() => setShowLogoutConfirm(false)}
                className="px-4 py-2 rounded bg-slate-200 hover:bg-slate-300 text-slate-800 dark:bg-slate-700 dark:hover:bg-slate-600 dark:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleLogout}
                className="px-4 py-2 rounded bg-[#e74c3c] hover:bg-[#c0392b] text-white transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}
