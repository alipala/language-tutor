'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth';
import { useNavigation } from '@/lib/navigation';
import { useSubscriptionStatus } from '@/hooks/useSubscriptionStatus';
import { Logo } from './logo';
import { Crown, Star, Zap } from 'lucide-react';
import LeaveConfirmationModal from '@/components/leave-confirmation-modal';

export default function NavBar({ activeSection = '' }: { activeSection?: string }) {
  // Determine if we're on the landing page
  const [isLandingPage, setIsLandingPage] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const [isNavHidden, setIsNavHidden] = useState(false);
  const [lastScrollY, setLastScrollY] = useState(0);
  const [isMobile, setIsMobile] = useState(false);
  const { user, logout, loading: authLoading } = useAuth();
  const navigation = useNavigation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [showLeaveConfirm, setShowLeaveConfirm] = useState(false);
  
  // Institution user detection
  const [isInstitutionUser, setIsInstitutionUser] = useState(false);
  const [institutionName, setInstitutionName] = useState('');
  
  // Use shared subscription status hook
  const { subscriptionStatus, loading: subscriptionLoading } = useSubscriptionStatus();

  // Notification state
  const [unreadCount, setUnreadCount] = useState(0);

  // Fetch unread notification count
  const fetchUnreadCount = async () => {
    if (!user) return;

    try {
      const response = await fetch('/api/unread-count', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUnreadCount(data.unread_count);
      }
    } catch (error) {
      console.error('Error fetching unread count:', error);
    }
  };

  // Handle notifications navigation
  const handleNotificationsNavigation = () => {
    // Navigate to profile page with notifications tab
    window.location.href = '/profile?tab=notifications';
    setIsMenuOpen(false);
  };

  // Check if we're on the landing page and detect mobile
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const checkInstitutionUser = () => {
        const institutionToken = localStorage.getItem('institution_token');
        const institutionNameStored = localStorage.getItem('institution_name');
        setIsInstitutionUser(!!institutionToken);
        setInstitutionName(institutionNameStored || 'Institution');
      };
      
      setIsLandingPage(window.location.pathname === '/');
      
      // Check initially
      checkInstitutionUser();
      
      // Re-check on path change (for navigation)
      const intervalId = setInterval(checkInstitutionUser, 500);
      
      // Detect mobile device
      const checkMobile = () => {
        const isMobileDevice = window.innerWidth < 768 || 
          /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        setIsMobile(isMobileDevice);
      };
      
      checkMobile();
      window.addEventListener('resize', checkMobile);
      
      // Enhanced scroll handler for both landing page and mobile hide-on-scroll
      const handleScroll = () => {
        const currentScrollY = window.scrollY;
        
        // Landing page scroll effect
        setIsScrolled(currentScrollY > 50);
        
        // Mobile hide-on-scroll functionality (only on speech pages)
        if (isMobile && window.location.pathname.includes('/speech')) {
          const scrollDifference = currentScrollY - lastScrollY;
          
          // Hide navbar when scrolling down (more than 5px) and past 100px
          if (scrollDifference > 5 && currentScrollY > 100) {
            setIsNavHidden(true);
          }
          // Show navbar when scrolling up (more than 5px) or near top
          else if (scrollDifference < -5 || currentScrollY < 50) {
            setIsNavHidden(false);
          }
          
          setLastScrollY(currentScrollY);
        }
      };
      
      // Add scroll listener
      window.addEventListener('scroll', handleScroll, { passive: true });
      
      return () => {
        window.removeEventListener('scroll', handleScroll);
        window.removeEventListener('resize', checkMobile);
        clearInterval(intervalId);
      };
    }
  }, [lastScrollY, isMobile]);

  // Fetch unread count when user is available
  useEffect(() => {
    if (user) {
      fetchUnreadCount();
      
      // Poll for new notifications every 30 seconds
      const interval = setInterval(fetchUnreadCount, 30000);
      return () => clearInterval(interval);
    }
  }, [user]);
  

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
    // Comprehensive session cleanup
    if (isInstitutionUser) {
      // Institution user logout
      localStorage.removeItem('institution_token');
      localStorage.removeItem('institution_id');
      localStorage.removeItem('institution_name');
      localStorage.removeItem('institution_code');
      
      // Clear all session storage
      sessionStorage.clear();
      
      // Close dialogs
      setShowLogoutConfirm(false);
      setIsMenuOpen(false);
      
      // Redirect to institution login
      window.location.href = '/institution/login';
    } else {
      // Regular user logout
      logout(); // This already handles localStorage token removal
      
      // Clear all session storage
      sessionStorage.clear();
      
      // Close dialogs
      setShowLogoutConfirm(false);
      setIsMenuOpen(false);
      
      // Navigate to home page
      window.location.href = '/';
    }
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
  let navbarClass = `w-full backdrop-blur-sm transition-all duration-500 fixed left-0 right-0 z-50 ${isScrolled ? 'bg-[#4ECFBF]/95 shadow-lg' : 'bg-[#4ECFBF]/90'} ${activeSection ? 'navbar-section1' : ''}`;
  navbarClass += isScrolled ? ' py-1' : ' py-2';
  
  // Add hide/show animation for mobile on speech pages
  if (isMobile && window.location.pathname.includes('/speech')) {
    navbarClass += isNavHidden ? ' -top-20 opacity-0' : ' top-0 opacity-100';
  } else {
    navbarClass += ' top-0';
  }
  
  return (
    <nav className={`main-navbar ${navbarClass}`}>
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
          {/* Landing page navigation items - only show when not logged in */}
          {isLandingPage && !user && (
            <div className="flex items-center space-x-6 mr-4">
              <button 
                onClick={() => scrollToSection('features')}
                className="text-white/90 hover:text-[#FFD63A] transition-all duration-300 font-medium px-3 py-2 rounded-md hover:border hover:border-[#FFD63A]/70 hover:bg-[#FFD63A]/10 hover:shadow-lg"
              >
                Features
              </button>
              <button 
                onClick={() => scrollToSection('how-it-works')}
                className="text-white/90 hover:text-[#F75A5A] transition-all duration-300 font-medium px-3 py-2 rounded-md hover:border hover:border-[#F75A5A]/70 hover:bg-[#F75A5A]/10 hover:shadow-lg"
              >
                How It Works
              </button>
              <button 
                onClick={() => scrollToSection('pricing')}
                className="text-white/90 hover:text-[#FFA955] transition-all duration-300 font-medium px-3 py-2 rounded-md hover:border hover:border-[#FFA955]/70 hover:bg-[#FFA955]/10 hover:shadow-lg"
              >
                Pricing
              </button>
              <button 
                onClick={() => scrollToSection('faq')}
                className="text-white/90 hover:text-white transition-all duration-300 font-medium px-3 py-2 rounded-md hover:border hover:border-white/50 hover:bg-white/10 hover:shadow-lg"
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
          ) : isInstitutionUser ? (
            <div className="flex items-center space-x-2">
              <div className="relative user-menu-container">
                <button
                  onClick={() => setIsMenuOpen(!isMenuOpen)}
                  className="text-white/80 hover:text-white transition-all duration-300 relative"
                >
                  <div className="flex items-center space-x-2 px-3 py-2 rounded-md hover:border hover:border-white/50 hover:bg-white/10 transition-all duration-300">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                    <span className="font-medium text-lg">{institutionName}</span>
                    <svg xmlns="http://www.w3.org/2000/svg" className={`h-4 w-4 transition-transform ${isMenuOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </button>
                
                {/* Institution Dropdown Menu */}
                {isMenuOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-white/90 backdrop-blur-md rounded-md shadow-lg py-1 z-10 border border-white/30">
                    <button
                      onClick={() => {
                        window.location.href = '/institution/dashboard';
                        setIsMenuOpen(false);
                      }}
                      className="block w-full text-left px-4 py-3 text-sm text-[#3a9e92] font-medium hover:bg-[#3a9e92]/10"
                    >
                      Dashboard
                    </button>
                    <button
                      onClick={() => {
                        // TODO: Implement settings page
                        setIsMenuOpen(false);
                      }}
                      className="block w-full text-left px-4 py-3 text-sm text-[#3a9e92] font-medium hover:bg-[#3a9e92]/10"
                    >
                      Settings
                    </button>
                    <button
                      onClick={() => {
                        // TODO: Implement billing page
                        setIsMenuOpen(false);
                      }}
                      className="block w-full text-left px-4 py-3 text-sm text-[#3a9e92] font-medium hover:bg-[#3a9e92]/10"
                    >
                      Billing
                    </button>
                    <button
                      onClick={() => {
                        setShowLogoutConfirm(true);
                        setIsMenuOpen(false);
                      }}
                      className="block w-full text-left px-4 py-3 text-sm text-[#e74c3c] font-medium hover:bg-[#e74c3c]/10"
                    >
                      Logout
                    </button>
                  </div>
                )}
              </div>
            </div>
          ) : user ? (
            <div className="flex items-center space-x-2">
              <div className="relative user-menu-container">
                <button
                  onClick={() => setIsMenuOpen(!isMenuOpen)}
                  className="text-white/80 hover:text-white transition-all duration-300 relative"
                >
                  {!subscriptionLoading && planInfo.name !== 'Try & Learn' ? (
                    <div 
                      className="flex items-center justify-between px-3 py-2 rounded-md font-medium border border-white/50 hover:bg-white/10 transition-all duration-300 relative"
                      style={{ backgroundColor: planInfo.color }}
                    >
                      <div className="flex items-center space-x-2">
                        <span className="text-lg font-bold text-white drop-shadow-sm">{planInfo.icon}</span>
                        <span className="text-base">{user.name}</span>
                      </div>
                      <svg xmlns="http://www.w3.org/2000/svg" className={`h-4 w-4 ml-2 transition-transform ${isMenuOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                      {/* Notification dot */}
                      {unreadCount > 0 && (
                        <div className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-medium shadow-lg">
                          {unreadCount > 9 ? '9+' : unreadCount}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2 px-3 py-2 rounded-md hover:border hover:border-white/50 hover:bg-white/10 transition-all duration-300 relative">
                      <span className="font-medium text-lg">{user.name}</span>
                      <svg xmlns="http://www.w3.org/2000/svg" className={`h-4 w-4 transition-transform ${isMenuOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                      {/* Notification dot */}
                      {unreadCount > 0 && (
                        <div className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-medium shadow-lg">
                          {unreadCount > 9 ? '9+' : unreadCount}
                        </div>
                      )}
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
                    Your Dashboard
                  </button>
                  <button
                    onClick={handleNotificationsNavigation}
                    className="block w-full text-left px-4 py-3 text-sm text-[#3a9e92] font-medium hover:bg-[#3a9e92]/10 flex items-center justify-between"
                  >
                    <span>Notifications</span>
                    {unreadCount > 0 && (
                      <span className="bg-red-500 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center font-medium">
                        {unreadCount > 9 ? '9+' : unreadCount}
                      </span>
                    )}
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
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              setIsMenuOpen(!isMenuOpen);
            }}
            className="text-white/80 hover:text-white focus:outline-none p-3 -mr-2 touch-target relative z-50 bg-transparent border-none cursor-pointer"
            aria-label={isMenuOpen ? "Close menu" : "Open menu"}
            aria-expanded={isMenuOpen}
            style={{ minWidth: '48px', minHeight: '48px' }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
          {/* Landing page menu items on mobile - only show when not logged in */}
          {isLandingPage && !user && (
            <>
              <button
                onClick={() => scrollToSection('features')}
                className="block w-full text-left py-4 px-4 mx-2 my-1 rounded-md text-white/80 hover:text-[#FFD63A] hover:bg-[#FFD63A]/10 hover:border hover:border-[#FFD63A]/70 transition-all duration-300 touch-target"
              >
                Features
              </button>
              <button
                onClick={() => scrollToSection('how-it-works')}
                className="block w-full text-left py-4 px-4 mx-2 my-1 rounded-md text-white/80 hover:text-[#F75A5A] hover:bg-[#F75A5A]/10 hover:border hover:border-[#F75A5A]/70 transition-all duration-300 touch-target"
              >
                How It Works
              </button>
              <button
                onClick={() => scrollToSection('pricing')}
                className="block w-full text-left py-4 px-4 mx-2 my-1 rounded-md text-white/80 hover:text-[#FFA955] hover:bg-[#FFA955]/10 hover:border hover:border-[#FFA955]/70 transition-all duration-300 touch-target"
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
                Your Dashboard
              </button>
              <button
                onClick={handleNotificationsNavigation}
                className="block w-full text-left py-4 px-4 mx-2 my-1 rounded-md text-white/80 hover:text-white hover:bg-white/10 hover:border hover:border-white/50 transition-all duration-300 touch-target flex items-center justify-between"
              >
                <span>Notifications</span>
                {unreadCount > 0 && (
                  <span className="bg-red-500 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center font-medium">
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                )}
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
              {/* Institution Menu Items for Mobile */}
              <div className="px-4 py-2 mx-2 border-b border-white/10">
                <p className="text-xs text-white/60 font-medium uppercase tracking-wide">For Schools</p>
              </div>
              <Link
                href="/institution/signup"
                onClick={() => setIsMenuOpen(false)}
                className="block w-full text-left py-4 px-4 mx-2 my-1 rounded-md text-white/80 hover:text-white hover:bg-white/10 hover:border hover:border-white/50 transition-all duration-300 touch-target flex items-center space-x-2"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span>Create School Account</span>
              </Link>
              <Link
                href="/institution/login"
                onClick={() => setIsMenuOpen(false)}
                className="block w-full text-left py-4 px-4 mx-2 my-1 rounded-md text-white/80 hover:text-white hover:bg-white/10 hover:border hover:border-white/50 transition-all duration-300 touch-target flex items-center space-x-2"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                </svg>
                <span>School Login</span>
              </Link>
              
              <div className="border-t border-white/10 mx-2 my-2"></div>
              
              {/* Individual Learner Login */}
              <div className="px-4 py-2 mx-2 border-b border-white/10">
                <p className="text-xs text-white/60 font-medium uppercase tracking-wide">Individual Learners</p>
              </div>
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
