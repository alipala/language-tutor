'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth';
import { useNavigation } from '@/lib/navigation';
import { useSubscriptionStatus } from '@/hooks/useSubscriptionStatus';
import { Logo } from './logo';
import { Crown, Star, Zap } from 'lucide-react';
import LeaveConfirmationModal from '@/components/leave-confirmation-modal';
import NotificationBell from '@/components/notification-bell';

export default function NavBar({ activeSection = '' }: { activeSection?: string }) {
  // Determine if we're on the landing page
  const [isLandingPage, setIsLandingPage] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const { user, logout, loading: authLoading } = useAuth();
  const navigation = useNavigation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [showLeaveConfirm, setShowLeaveConfirm] = useState(false);
  
  // Use shared subscription status hook
  const { subscriptionStatus, loading: subscriptionLoading } = useSubscriptionStatus();

  // Check if we're on the landing page
  useEffect(() => {
    if (typeof window !== 'undefined') {
      setIsLandingPage(window.location.pathname === '/');
      
      // Add scroll listener for the landing page
      const handleScroll = () => {
        setIsScrolled(window.scrollY > 50);
      };
      
      if (window.location.pathname === '/') {
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
      }
    }
  }, []);
  

  // Helper function to get plan display info
  const getPlanDisplayInfo = () => {
    if (!subscriptionStatus) return { name: 'Try & Learn', icon: '⚡', color: '#9CA3AF' };
    
    switch (subscriptionStatus.plan) {
      case 'fluency_builder':
        return { 
          name: 'Fluency Builder', 
          icon: '⭐',
          color: '#FFD63A'
        };
      case 'team_mastery':
        return { 
          name: 'Team Mastery', 
          icon: '👑',
          color: '#FFA955'
        };
      default:
        return { name: 'Try & Learn', icon: '⚡', color: '#9CA3AF' };
    }
  };

  const planInfo = getPlanDisplayInfo();

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (isMenuOpen && !target.closest('.user-menu-container') && !target.closest('.mobile-menu-container')) {
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

  // Handle profile navigation with confirmation if on speech page
  const handleProfileNavigation = () => {
    // Check if we're on a speech page or in a conversation
    const currentPath = window.location.pathname;
    const isOnSpeechPage = currentPath.includes('/speech') || currentPath.includes('/assessment');
    const isInConversation = sessionStorage.getItem('isInConversation') === 'true';
    
    if (isOnSpeechPage || isInConversation) {
      // Show confirmation modal
      setShowLeaveConfirm(true);
    } else {
      // Navigate directly
      navigation.navigateToProfile();
    }
    
    // Close the menu
    setIsMenuOpen(false);
  };

  // Handle leave confirmation
  const handleLeaveConfirm = () => {
    // Set flag to allow navigation
    sessionStorage.setItem('allowNavigation', 'true');
    sessionStorage.setItem('intentionalNavigation', 'true');
    
    // Clear conversation flag
    sessionStorage.removeItem('isInConversation');
    
    // Navigate to profile
    navigation.navigateToProfile();
    
    setShowLeaveConfirm(false);
  };

  // Handle stay on current page
  const handleStayOnPage = () => {
    setShowLeaveConfirm(false);
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
        handleProfileNavigation();
        return; // Don't call navigation.navigateToProfile() directly
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

  // Scroll to section on landing page
  const scrollToSection = useCallback((sectionId: string) => {
    if (typeof window !== 'undefined') {
      const section = document.getElementById(sectionId);
      if (section) {
        section.scrollIntoView({ behavior: 'smooth' });
        setIsMenuOpen(false);
      }
    }
  }, []);

  // Keep the navbar fixed with appropriate styling - compact height with large logo
  let navbarClass = `w-full backdrop-blur-sm transition-all duration-500 fixed top-0 left-0 right-0 z-50 ${isScrolled ? 'bg-[#4ECFBF]/95 shadow-lg' : 'bg-[#4ECFBF]/90'} ${activeSection ? 'navbar-section1' : ''}`;
  navbarClass += isScrolled ? ' py-1' : ' py-2';
  
  return (
    <nav className={navbarClass}>
      <div className="container mx-auto px-4 flex justify-between items-center">
        {/* Logo */}
        <Logo 
          variant="full"
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
        />

        {/* Navigation Links */}
        <div className="hidden md:flex items-center space-x-6">
          {/* Landing page navigation items */}
          {isLandingPage && (
            <div className="flex items-center space-x-6 mr-4">
              <button 
                onClick={() => scrollToSection('features')}
                className="text-white/90 hover:text-white transition-all duration-300 font-medium px-3 py-2 rounded-md hover:border hover:border-white/50 hover:bg-white/10"
              >
                Features
              </button>
              <button 
                onClick={() => scrollToSection('how-it-works')}
                className="text-white/90 hover:text-white transition-all duration-300 font-medium px-3 py-2 rounded-md hover:border hover:border-white/50 hover:bg-white/10"
              >
                How It Works
              </button>
              <button 
                onClick={() => scrollToSection('pricing')}
                className="text-white/90 hover:text-white transition-all duration-300 font-medium px-3 py-2 rounded-md hover:border hover:border-white/50 hover:bg-white/10"
              >
                Pricing
              </button>
              <button 
                onClick={() => scrollToSection('faq')}
                className="text-white/90 hover:text-white transition-all duration-300 font-medium px-3 py-2 rounded-md hover:border hover:border-white/50 hover:bg-white/10"
              >
                FAQ
              </button>
            </div>
          )}
          
          
          {/* User Menu (when logged in) or Loading State */}
          {authLoading ? (
            <div className="flex items-center">
              {/* Loading skeleton that matches the user menu size */}
              <div className="flex items-center space-x-2 px-3 py-2 rounded-md border border-white/30 bg-white/10">
                <div className="w-6 h-6 bg-white/20 rounded-full animate-pulse"></div>
                <div className="w-16 h-4 bg-white/20 rounded animate-pulse"></div>
                <div className="w-4 h-4 bg-white/20 rounded animate-pulse"></div>
              </div>
            </div>
          ) : user ? (
            <div className="flex items-center space-x-2">
              {/* Notification Bell */}
              <NotificationBell />
              
              <div className="relative user-menu-container">
                <button
                  onClick={() => setIsMenuOpen(!isMenuOpen)}
                  className="text-white/80 hover:text-white transition-all duration-300"
                >
                  {!subscriptionLoading && planInfo.name !== 'Try & Learn' ? (
                    <div 
                      className="flex items-center justify-between px-3 py-2 rounded-md font-medium border border-white/50 hover:bg-white/10 transition-all duration-300"
                      style={{ backgroundColor: planInfo.color }}
                    >
                      <div className="flex items-center space-x-2">
                        <span className="text-lg font-bold text-white drop-shadow-sm">{planInfo.icon}</span>
                        <span className="text-base">{user.name}</span>
                      </div>
                      <svg xmlns="http://www.w3.org/2000/svg" className={`h-4 w-4 ml-2 transition-transform ${isMenuOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2 px-3 py-2 rounded-md hover:border hover:border-white/50 hover:bg-white/10 transition-all duration-300">
                      <span className="font-medium text-lg">{user.name}</span>
                      <svg xmlns="http://www.w3.org/2000/svg" className={`h-4 w-4 transition-transform ${isMenuOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  )}
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

        {/* Mobile Menu Button - Enhanced for better touch targets */}
        <div className="block md:hidden">
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="text-white/80 hover:text-white focus:outline-none p-2 -mr-2 touch-target"
            aria-label={isMenuOpen ? "Close menu" : "Open menu"}
            aria-expanded={isMenuOpen}
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

      {/* Mobile Menu - Enhanced for better mobile UX */}
      {isMenuOpen && (
        <div className="block md:hidden bg-white/10 backdrop-blur-md border border-white/20 shadow-lg mt-2 mx-4 rounded-lg overflow-hidden mobile-menu-container">
          {/* Landing page menu items on mobile */}
          {isLandingPage && (
            <>
              <button
                onClick={() => scrollToSection('features')}
                className="block w-full text-left py-4 px-4 mx-2 my-1 rounded-md text-white/80 hover:text-white hover:bg-white/10 hover:border hover:border-white/50 transition-all duration-300 touch-target"
              >
                Features
              </button>
              <button
                onClick={() => scrollToSection('how-it-works')}
                className="block w-full text-left py-4 px-4 mx-2 my-1 rounded-md text-white/80 hover:text-white hover:bg-white/10 hover:border hover:border-white/50 transition-all duration-300 touch-target"
              >
                How It Works
              </button>
              <button
                onClick={() => scrollToSection('pricing')}
                className="block w-full text-left py-4 px-4 mx-2 my-1 rounded-md text-white/80 hover:text-white hover:bg-white/10 hover:border hover:border-white/50 transition-all duration-300 touch-target"
              >
                Pricing
              </button>
              <button
                onClick={() => scrollToSection('faq')}
                className="block w-full text-left py-4 px-4 mx-2 my-1 rounded-md text-white/80 hover:text-white hover:bg-white/10 hover:border hover:border-white/50 transition-all duration-300 touch-target"
              >
                FAQ
              </button>
              <div className="border-t border-white/10 mx-2 my-2"></div>
            </>
          )}
          
          {authLoading ? (
            <>
              {/* Loading skeleton for mobile menu */}
              <div className="py-4 px-4 mx-2 my-1 rounded-md">
                <div className="w-24 h-4 bg-white/20 rounded animate-pulse"></div>
              </div>
            </>
          ) : user ? (
            <>
              <button
                onClick={() => {
                  navigateTo('/profile');
                  setIsMenuOpen(false);
                }}
                className="block w-full text-left py-4 px-4 mx-2 my-1 rounded-md text-white/80 hover:text-white hover:bg-white/10 hover:border hover:border-white/50 transition-all duration-300 touch-target"
              >
                Your Profile
              </button>
              <button
                onClick={() => setShowLogoutConfirm(true)}
                className="block w-full text-left py-4 px-4 mx-2 my-1 rounded-md text-red-300 hover:text-red-200 hover:bg-red-500/10 hover:border hover:border-red-400/50 transition-all duration-300 touch-target"
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
                className="block w-full text-left py-4 px-4 mx-2 my-1 rounded-md text-white/80 hover:text-white hover:bg-white/10 hover:border hover:border-white/50 transition-all duration-300 touch-target"
              >
                Login
              </button>
            </>
          )}
        </div>
      )}
      
      {/* Leave Confirmation Modal */}
      <LeaveConfirmationModal
        isOpen={showLeaveConfirm}
        onStay={handleStayOnPage}
        onLeave={handleLeaveConfirm}
        userType={user ? 'authenticated' : 'guest'}
      />

      {/* Logout Confirmation Dialog */}
      {showLogoutConfirm && (
        <>
          {/* Backdrop for clicking outside to close */}
          <div 
            className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm" 
            onClick={() => setShowLogoutConfirm(false)}
          />
          {/* Position dialog at the specific location marked in the screenshot - Mobile optimized */}
          <div 
            className="fixed top-[200px] left-1/2 -translate-x-1/2 z-50 animate-slideDown w-[90%] max-w-sm mx-auto"
            onClick={(e) => e.stopPropagation()} // Prevent clicks inside from closing
          >
              <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-2xl border border-gray-200 dark:border-slate-700">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-3">Sign Out</h3>
                <p className="text-slate-700 dark:text-slate-300 mb-6">Are you sure you want to sign out?</p>
                
                <div className="flex flex-col sm:flex-row gap-3 sm:gap-2 sm:justify-end">
                  <button
                    onClick={() => setShowLogoutConfirm(false)}
                    className="px-4 py-3 sm:py-2 rounded bg-slate-200 hover:bg-slate-300 text-slate-800 dark:bg-slate-700 dark:hover:bg-slate-600 dark:text-white transition-colors text-sm font-medium touch-target"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleLogout}
                    className="px-4 py-3 sm:py-2 rounded bg-[#e74c3c] hover:bg-[#c0392b] text-white transition-colors text-sm font-medium touch-target"
                  >
                    Sign Out
                  </button>
                </div>
              </div>
            </div>
        </>
      )}
    </nav>
  );
}
