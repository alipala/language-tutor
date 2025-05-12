/**
 * Navigation Types
 * 
 * Type definitions for the navigation system in the Your Smart Language Coach application.
 */

/**
 * Base navigation state interface
 */
export interface NavigationState {
  /**
   * The previous route the user was on
   */
  previousRoute?: string;
  
  /**
   * Any additional state data
   */
  [key: string]: any;
}

/**
 * Navigation state for learning flow
 */
export interface LearningFlowState extends NavigationState {
  /**
   * The selected language code
   */
  language: string;
  
  /**
   * The selected proficiency level
   */
  level?: string;
  
  /**
   * The selected topic
   */
  topic?: string;
  
  /**
   * The learning plan ID if one exists
   */
  learningPlanId?: string;
}

/**
 * Navigation state for authentication flow
 */
export interface AuthFlowState extends NavigationState {
  /**
   * The route to redirect to after successful authentication
   */
  redirectAfterAuth: string;
  
  /**
   * Whether the user is signing up (true) or logging in (false)
   */
  isSignup?: boolean;
}
