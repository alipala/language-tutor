/**
 * Navigation Service
 * 
 * A centralized service for handling all navigation in the Your Smart Language Coach application.
 * This service ensures consistent navigation behavior across development and production environments.
 */

// Define navigation state type if not imported
interface NavigationState {
  [key: string]: any;
}

// Constants
const NAVIGATION_STATE_KEY = 'navigationState';
const REDIRECT_AFTER_AUTH_KEY = 'redirectAfterAuth';
const PENDING_LEARNING_PLAN_ID_KEY = 'pendingLearningPlanId';
const SELECTED_LANGUAGE_KEY = 'selectedLanguage';
const SELECTED_LEVEL_KEY = 'selectedLevel';

/**
 * NavigationService provides centralized navigation functionality for the application
 */
class NavigationService {
  /**
   * Determines if the application is running in Railway production environment
   */
  isRailwayEnvironment(): boolean {
    return typeof window !== 'undefined' && 
           (window.location.hostname.includes('railway.app') || 
            window.location.hostname === 'mytacoai.com');
  }

  /**
   * Navigate to a specific route using the most reliable method for the current environment
   * 
   * @param route The route to navigate to (e.g., '/language-selection')
   * @param options Navigation options
   */
  navigate(route: string, options: {
    replace?: boolean;  // Whether to replace the current history entry
    state?: Record<string, any>;  // State to store with the navigation
    preserveQueryParams?: boolean;  // Whether to preserve current query parameters
    useHistory?: boolean;  // Whether to use history.pushState for navigation (enables back button)
    isBackNavigation?: boolean; // Whether this is a back button navigation
  } = {}): void {
    try {
      console.log(`[NavigationService] Navigating to: ${route}`);
      
      // Check if we're in a potential redirect loop
      const currentPath = window.location.pathname;
      const targetPath = route.startsWith('/') ? route : `/${route}`;
      
      // If we're already on the target page, don't navigate again unless forced
      if (currentPath === targetPath && !options.isBackNavigation && !options.state?.force) {
        console.log(`[NavigationService] Already on ${targetPath}, skipping navigation`);
        return;
      }
      
      // Store any navigation state
      if (options.state) {
        this.setNavigationState(options.state);
      }
      
      // Set a flag for intentional navigation to help with back button handling
      if (!options.isBackNavigation) {
        sessionStorage.setItem('intentionalNavigation', 'true');
      }
      
      // Construct the relative URL path
      let relativePath = route;
      if (!route.startsWith('/') && !route.startsWith('http')) {
        relativePath = `/${route}`;
      }
      
      // Construct the full URL for window.location navigation
      let fullUrl = relativePath;
      if (!route.startsWith('http')) {
        fullUrl = `${window.location.origin}${relativePath}`;
      }
      
      // Preserve query params if requested
      if (options.preserveQueryParams && window.location.search) {
        const currentSearch = window.location.search;
        if (fullUrl.includes('?')) {
          fullUrl += `&${currentSearch.substring(1)}`;
          relativePath += `&${currentSearch.substring(1)}`;
        } else {
          fullUrl += currentSearch;
          relativePath += currentSearch;
        }
      }
      
      console.log(`[NavigationService] Full URL: ${fullUrl}`);
      
      // Use history API if requested (enables back button navigation)
      if (options.useHistory && !this.isRailwayEnvironment()) {
        console.log('[NavigationService] Using history API for navigation');
        if (options.replace) {
          window.history.replaceState(
            { ...(options.state || {}), navigationServiceManaged: true },
            '',
            relativePath
          );
        } else {
          window.history.pushState(
            { ...(options.state || {}), navigationServiceManaged: true },
            '',
            relativePath
          );
        }
        
        // Dispatch a custom event to notify components of the navigation
        window.dispatchEvent(new CustomEvent('navigationServiceNavigate', {
          detail: { path: relativePath, state: options.state }
        }));
        
        return;
      }
      
      // Fall back to the most reliable navigation method
      if (options.replace) {
        window.location.replace(fullUrl);
      } else {
        window.location.href = fullUrl;
      }
    } catch (error) {
      console.error('[NavigationService] Navigation error:', error);
      throw error;
    }
  }

  /**
   * Navigate to the home page
   * Clears selected language and level to prevent automatic redirects
   */
  navigateToHome(): void {
    // Clear navigation state and specific keys that might cause redirects
    this.clearNavigationState();
    sessionStorage.removeItem(SELECTED_LANGUAGE_KEY);
    sessionStorage.removeItem(SELECTED_LEVEL_KEY);
    sessionStorage.removeItem('selectedTopic');
    sessionStorage.removeItem('intentionalNavigation');
    sessionStorage.removeItem('popStateToTopicSelection');
    sessionStorage.removeItem('fromLevelSelection');
    sessionStorage.removeItem('backButtonNavigation');
    
    // Clear any refresh counters that might be tracking potential loops
    sessionStorage.removeItem('levelSelectionRedirectAttempt');
    sessionStorage.removeItem('speechPageRefreshCount');
    
    // Navigate to home
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
    // Set intentional navigation flag to prevent redirect loops
    sessionStorage.setItem('intentionalNavigation', 'true');
    // Clear any back button navigation flags
    sessionStorage.removeItem('backButtonNavigation');
    sessionStorage.removeItem('popStateToTopicSelection');
    
    // Navigate to level selection
    this.navigate('/level-selection', { replace: false });
  }

  /**
   * Navigate to the topic selection page
   */
  navigateToTopicSelection(): void {
    // Set intentional navigation flag to prevent redirect loops
    sessionStorage.setItem('intentionalNavigation', 'true');
    // Set a flag to indicate we're intentionally changing topics
    sessionStorage.setItem('intentionalTopicChange', 'true');
    // Clear any back button navigation flags
    sessionStorage.removeItem('backButtonNavigation');
    
    // Navigate to topic selection
    this.navigate('/topic-selection', { 
      replace: false, // Use push instead of replace to enable back button
      useHistory: true // Use history API for better back button support
    });
  }

  /**
   * Navigate to the speaking assessment page
   */
  navigateToSpeakingAssessment(): void {
    this.navigate('/assessment/speaking', { replace: true });
  }

  /**
   * Navigate to the speech page, optionally with a learning plan ID
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
    this.navigate('/profile', { replace: true });
  }

  /**
   * Get the current navigation state
   */
  getNavigationState<T extends NavigationState>(): T | null {
    try {
      const stateJson = sessionStorage.getItem(NAVIGATION_STATE_KEY);
      return stateJson ? JSON.parse(stateJson) : null;
    } catch (error) {
      console.error('[NavigationService] Error getting navigation state:', error);
      return null;
    }
  }

  /**
   * Set the navigation state
   */
  setNavigationState(state: Record<string, any>): void {
    try {
      sessionStorage.setItem(NAVIGATION_STATE_KEY, JSON.stringify(state));
    } catch (error) {
      console.error('[NavigationService] Error setting navigation state:', error);
    }
  }

  /**
   * Clear the navigation state
   */
  clearNavigationState(): void {
    try {
      sessionStorage.removeItem(NAVIGATION_STATE_KEY);
    } catch (error) {
      console.error('[NavigationService] Error clearing navigation state:', error);
    }
  }

  /**
   * Set the redirect after authentication
   */
  setRedirectAfterAuth(route: string): void {
    try {
      sessionStorage.setItem(REDIRECT_AFTER_AUTH_KEY, route);
    } catch (error) {
      console.error('[NavigationService] Error setting redirect after auth:', error);
    }
  }

  /**
   * Get the redirect after authentication
   */
  getRedirectAfterAuth(): string | null {
    try {
      return sessionStorage.getItem(REDIRECT_AFTER_AUTH_KEY);
    } catch (error) {
      console.error('[NavigationService] Error getting redirect after auth:', error);
      return null;
    }
  }

  /**
   * Clear the redirect after authentication
   */
  clearRedirectAfterAuth(): void {
    try {
      sessionStorage.removeItem(REDIRECT_AFTER_AUTH_KEY);
    } catch (error) {
      console.error('[NavigationService] Error clearing redirect after auth:', error);
    }
  }

  /**
   * Set the pending learning plan ID
   */
  setPendingLearningPlanId(planId: string): void {
    try {
      sessionStorage.setItem(PENDING_LEARNING_PLAN_ID_KEY, planId);
    } catch (error) {
      console.error('[NavigationService] Error setting pending learning plan ID:', error);
    }
  }

  /**
   * Get the pending learning plan ID
   */
  getPendingLearningPlanId(): string | null {
    try {
      return sessionStorage.getItem(PENDING_LEARNING_PLAN_ID_KEY);
    } catch (error) {
      console.error('[NavigationService] Error getting pending learning plan ID:', error);
      return null;
    }
  }

  /**
   * Clear the pending learning plan ID
   */
  clearPendingLearningPlanId(): void {
    try {
      sessionStorage.removeItem(PENDING_LEARNING_PLAN_ID_KEY);
    } catch (error) {
      console.error('[NavigationService] Error clearing pending learning plan ID:', error);
    }
  }

  /**
   * Set the selected language
   */
  setSelectedLanguage(language: string): void {
    try {
      sessionStorage.setItem(SELECTED_LANGUAGE_KEY, language);
    } catch (error) {
      console.error('[NavigationService] Error setting selected language:', error);
    }
  }

  /**
   * Get the selected language
   */
  getSelectedLanguage(): string | null {
    try {
      return sessionStorage.getItem(SELECTED_LANGUAGE_KEY);
    } catch (error) {
      console.error('[NavigationService] Error getting selected language:', error);
      return null;
    }
  }

  /**
   * Set the selected level
   */
  setSelectedLevel(level: string): void {
    try {
      sessionStorage.setItem(SELECTED_LEVEL_KEY, level);
    } catch (error) {
      console.error('[NavigationService] Error setting selected level:', error);
    }
  }

  /**
   * Get the selected level
   */
  getSelectedLevel(): string | null {
    try {
      return sessionStorage.getItem(SELECTED_LEVEL_KEY);
    } catch (error) {
      console.error('[NavigationService] Error getting selected level:', error);
      return null;
    }
  }

  /**
   * Handle post-authentication navigation
   * This should be called after successful authentication
   */
  handlePostAuthNavigation(): void {
    try {
      const redirectRoute = this.getRedirectAfterAuth();
      this.clearRedirectAfterAuth();
      
      if (redirectRoute) {
        console.log(`[NavigationService] Post-auth navigation to: ${redirectRoute}`);
        this.navigate(redirectRoute, { replace: true });
      } else {
        // Default redirect to profile if no specific redirect is set
        this.navigateToProfile();
      }
    } catch (error) {
      console.error('[NavigationService] Error in post-auth navigation:', error);
      // Fallback to profile page
      this.navigateToProfile();
    }
  }
}

// Export a singleton instance
export const navigationService = new NavigationService();
