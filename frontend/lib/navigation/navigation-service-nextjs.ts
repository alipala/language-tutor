/**
 * Next.js Navigation Service
 * 
 * PERFORMANCE OPTIMIZED: Uses Next.js router for client-side navigation
 * This prevents full page reloads and dramatically improves performance
 */

import { AppRouterInstance } from 'next/dist/shared/lib/app-router-context.shared-runtime';

// Constants
const NAVIGATION_STATE_KEY = 'navigationState';
const REDIRECT_AFTER_AUTH_KEY = 'redirectAfterAuth';
const PENDING_LEARNING_PLAN_ID_KEY = 'pendingLearningPlanId';
const SELECTED_LANGUAGE_KEY = 'selectedLanguage';
const SELECTED_LEVEL_KEY = 'selectedLevel';

/**
 * NavigationService provides centralized navigation functionality
 * OPTIMIZED: Uses Next.js router instead of window.location for faster navigation
 */
class NextJsNavigationService {
  private router: AppRouterInstance | null = null;

  /**
   * Initialize the service with Next.js router
   * This should be called once in the app layout
   */
  initialize(router: AppRouterInstance): void {
    this.router = router;
    console.log('[NavigationService] Initialized with Next.js router');
  }

  /**
   * Navigate to a specific route using Next.js router (client-side navigation)
   * 
   * @param route The route to navigate to (e.g., '/language-selection')
   * @param options Navigation options
   */
  navigate(route: string, options: {
    replace?: boolean;
    state?: Record<string, any>;
    preserveQueryParams?: boolean;
    useHistory?: boolean;
    isBackNavigation?: boolean;
  } = {}): void {
    try {
      console.log(`[NavigationService] Navigating to: ${route}`);
      
      // Check if we're already on the target page
      if (typeof window !== 'undefined') {
        const currentPath = window.location.pathname;
        const targetPath = route.startsWith('/') ? route : `/${route}`;
        
        if (currentPath === targetPath && !options.isBackNavigation && !options.state?.force) {
          console.log(`[NavigationService] Already on ${targetPath}, skipping navigation`);
          return;
        }
      }
      
      // Store any navigation state
      if (options.state) {
        this.setNavigationState(options.state);
      }
      
      // Set intentional navigation flag
      if (!options.isBackNavigation && typeof window !== 'undefined') {
        sessionStorage.setItem('intentionalNavigation', 'true');
      }
      
      // Construct the relative URL path
      let relativePath = route;
      if (!route.startsWith('/') && !route.startsWith('http')) {
        relativePath = `/${route}`;
      }
      
      // Preserve query params if requested
      if (options.preserveQueryParams && typeof window !== 'undefined' && window.location.search) {
        const currentSearch = window.location.search;
        if (relativePath.includes('?')) {
          relativePath += `&${currentSearch.substring(1)}`;
        } else {
          relativePath += currentSearch;
        }
      }
      
      console.log(`[NavigationService] Full URL: ${typeof window !== 'undefined' ? window.location.origin : ''}${relativePath}`);
      
      // 🚀 PERFORMANCE FIX: Use Next.js router for client-side navigation
      if (this.router) {
        if (options.replace) {
          this.router.replace(relativePath);
        } else {
          this.router.push(relativePath);
        }
      } else {
        // Fallback to window.location if router not initialized
        console.warn('[NavigationService] Router not initialized, falling back to window.location');
        if (typeof window !== 'undefined') {
          if (options.replace) {
            window.location.replace(relativePath);
          } else {
            window.location.href = relativePath;
          }
        }
      }
    } catch (error) {
      console.error('[NavigationService] Navigation error:', error);
      throw error;
    }
  }

  /**
   * Navigate to the home page
   */
  navigateToHome(): void {
    this.clearNavigationState();
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem(SELECTED_LANGUAGE_KEY);
      sessionStorage.removeItem(SELECTED_LEVEL_KEY);
      sessionStorage.removeItem('selectedTopic');
      sessionStorage.removeItem('intentionalNavigation');
      sessionStorage.removeItem('popStateToTopicSelection');
      sessionStorage.removeItem('fromLevelSelection');
      sessionStorage.removeItem('backButtonNavigation');
      sessionStorage.removeItem('levelSelectionRedirectAttempt');
      sessionStorage.removeItem('speechPageRefreshCount');
    }
    this.navigate('/', { replace: true });
  }

  /**
   * Navigate to the language selection page
   */
  navigateToLanguageSelection(): void {
    this.navigate('/language-selection', { replace: true });
  }

  /**
   * Navigate to the level selection page
   */
  navigateToLevelSelection(): void {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('intentionalNavigation', 'true');
      sessionStorage.removeItem('backButtonNavigation');
      sessionStorage.removeItem('popStateToTopicSelection');
    }
    this.navigate('/level-selection', { replace: false });
  }

  /**
   * Navigate to the topic selection page
   */
  navigateToTopicSelection(): void {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('intentionalNavigation', 'true');
      sessionStorage.setItem('intentionalTopicChange', 'true');
      sessionStorage.removeItem('backButtonNavigation');
    }
    this.navigate('/topic-selection', { replace: false, useHistory: true });
  }

  /**
   * Navigate to the speaking assessment page
   */
  navigateToSpeakingAssessment(): void {
    this.navigate('/assessment/speaking', { replace: true });
  }

  /**
   * Navigate to the speech page
   */
  navigateToSpeech(planId?: string): void {
    const route = planId ? `/speech?plan=${planId}` : '/speech';
    this.navigate(route, { replace: true });
  }

  /**
   * Navigate to the login page
   */
  navigateToLogin(redirectAfterAuth?: string): void {
    if (redirectAfterAuth) {
      this.setRedirectAfterAuth(redirectAfterAuth);
    }
    this.navigate('/auth/login', { replace: true });
  }

  /**
   * Navigate to the signup page
   */
  navigateToSignup(redirectAfterAuth?: string): void {
    if (redirectAfterAuth) {
      this.setRedirectAfterAuth(redirectAfterAuth);
    }
    this.navigate('/auth/signup', { replace: true });
  }

  /**
   * Navigate to the profile page
   */
  navigateToProfile(): void {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('allowNavigation', 'true');
      sessionStorage.setItem('intentionalNavigation', 'true');
    }
    this.navigate('/profile', { replace: true });
  }

  // Storage methods remain the same
  getNavigationState<T>(): T | null {
    if (typeof window === 'undefined') return null;
    try {
      const stateJson = sessionStorage.getItem(NAVIGATION_STATE_KEY);
      return stateJson ? JSON.parse(stateJson) : null;
    } catch (error) {
      console.error('[NavigationService] Error getting navigation state:', error);
      return null;
    }
  }

  setNavigationState(state: Record<string, any>): void {
    if (typeof window === 'undefined') return;
    try {
      sessionStorage.setItem(NAVIGATION_STATE_KEY, JSON.stringify(state));
    } catch (error) {
      console.error('[NavigationService] Error setting navigation state:', error);
    }
  }

  clearNavigationState(): void {
    if (typeof window === 'undefined') return;
    try {
      sessionStorage.removeItem(NAVIGATION_STATE_KEY);
    } catch (error) {
      console.error('[NavigationService] Error clearing navigation state:', error);
    }
  }

  setRedirectAfterAuth(route: string): void {
    if (typeof window === 'undefined') return;
    try {
      sessionStorage.setItem(REDIRECT_AFTER_AUTH_KEY, route);
    } catch (error) {
      console.error('[NavigationService] Error setting redirect after auth:', error);
    }
  }

  getRedirectAfterAuth(): string | null {
    if (typeof window === 'undefined') return null;
    try {
      return sessionStorage.getItem(REDIRECT_AFTER_AUTH_KEY);
    } catch (error) {
      console.error('[NavigationService] Error getting redirect after auth:', error);
      return null;
    }
  }

  clearRedirectAfterAuth(): void {
    if (typeof window === 'undefined') return;
    try {
      sessionStorage.removeItem(REDIRECT_AFTER_AUTH_KEY);
    } catch (error) {
      console.error('[NavigationService] Error clearing redirect after auth:', error);
    }
  }

  setPendingLearningPlanId(planId: string): void {
    if (typeof window === 'undefined') return;
    try {
      sessionStorage.setItem(PENDING_LEARNING_PLAN_ID_KEY, planId);
    } catch (error) {
      console.error('[NavigationService] Error setting pending learning plan ID:', error);
    }
  }

  getPendingLearningPlanId(): string | null {
    if (typeof window === 'undefined') return null;
    try {
      return sessionStorage.getItem(PENDING_LEARNING_PLAN_ID_KEY);
    } catch (error) {
      console.error('[NavigationService] Error getting pending learning plan ID:', error);
      return null;
    }
  }

  clearPendingLearningPlanId(): void {
    if (typeof window === 'undefined') return;
    try {
      sessionStorage.removeItem(PENDING_LEARNING_PLAN_ID_KEY);
    } catch (error) {
      console.error('[NavigationService] Error clearing pending learning plan ID:', error);
    }
  }

  setSelectedLanguage(language: string): void {
    if (typeof window === 'undefined') return;
    try {
      sessionStorage.setItem(SELECTED_LANGUAGE_KEY, language);
    } catch (error) {
      console.error('[NavigationService] Error setting selected language:', error);
    }
  }

  getSelectedLanguage(): string | null {
    if (typeof window === 'undefined') return null;
    try {
      return sessionStorage.getItem(SELECTED_LANGUAGE_KEY);
    } catch (error) {
      console.error('[NavigationService] Error getting selected language:', error);
      return null;
    }
  }

  setSelectedLevel(level: string): void {
    if (typeof window === 'undefined') return;
    try {
      sessionStorage.setItem(SELECTED_LEVEL_KEY, level);
    } catch (error) {
      console.error('[NavigationService] Error setting selected level:', error);
    }
  }

  getSelectedLevel(): string | null {
    if (typeof window === 'undefined') return null;
    try {
      return sessionStorage.getItem(SELECTED_LEVEL_KEY);
    } catch (error) {
      console.error('[NavigationService] Error getting selected level:', error);
      return null;
    }
  }

  handlePostAuthNavigation(): void {
    try {
      const redirectRoute = this.getRedirectAfterAuth();
      this.clearRedirectAfterAuth();
      
      if (redirectRoute) {
        console.log(`[NavigationService] Post-auth navigation to: ${redirectRoute}`);
        this.navigate(redirectRoute, { replace: true });
      } else {
        this.navigateToProfile();
      }
    } catch (error) {
      console.error('[NavigationService] Error in post-auth navigation:', error);
      this.navigateToProfile();
    }
  }
}

// Export singleton instance
export const navigationService = new NextJsNavigationService();
