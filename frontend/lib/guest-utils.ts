// Constants for guest user limitations
export const ASSESSMENT_DURATION_GUEST = 15; // 15 seconds for guest assessment
export const ASSESSMENT_DURATION_REGISTERED = 60; // 60 seconds for registered user assessment
export const CONVERSATION_DURATION_GUEST = 60; // 1 minute for guest conversation
export const CONVERSATION_DURATION_REGISTERED = 300; // 5 minutes for registered user conversation

/**
 * Gets the assessment duration based on user authentication status
 * @param {boolean} isAuthenticated - Whether the user is authenticated
 * @returns {number} The assessment duration in seconds
 */
export const getAssessmentDuration = (isAuthenticated: boolean): number => {
  return isAuthenticated ? ASSESSMENT_DURATION_REGISTERED : ASSESSMENT_DURATION_GUEST;
};

/**
 * Gets the conversation duration based on user authentication status
 * @param {boolean} isAuthenticated - Whether the user is authenticated
 * @returns {number} The conversation duration in seconds
 */
export const getConversationDuration = (isAuthenticated: boolean): number => {
  return isAuthenticated ? CONVERSATION_DURATION_REGISTERED : CONVERSATION_DURATION_GUEST;
};

/**
 * Gets the maximum number of assessment details to show based on user authentication status
 * @param {boolean} isAuthenticated - Whether the user is authenticated
 * @returns {number} The maximum number of details to show
 */
export const getMaxAssessmentDetails = (isAuthenticated: boolean): number => {
  return isAuthenticated ? 5 : 3; // Show fewer details for guest users
};

/**
 * Formats a time duration from seconds to MM:SS format
 * @param {number} seconds - The time in seconds
 * @returns {string} Formatted time string in MM:SS format
 */
export const formatTime = (seconds: number): string => {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;  
};

/**
 * Gets a description of the limitations for guest users
 * @returns {string} A description of the guest user limitations
 */
export const getGuestLimitationsDescription = (): string => {
  return `Limited to ${ASSESSMENT_DURATION_GUEST}s assessment and ${CONVERSATION_DURATION_GUEST}s conversation.`;
};

/**
 * Checks if a speech plan is still valid based on its creation time and user authentication status
 * @param {boolean} isAuthenticated - Whether the user is authenticated
 * @param {string | null} planCreationTime - ISO string of when the plan was created
 * @returns {boolean} Whether the plan is still valid
 */
export const isPlanValid = (isAuthenticated: boolean, planCreationTime: string | null): boolean => {
  if (!planCreationTime) return false;
  
  try {
    const creationTime = new Date(planCreationTime).getTime();
    const currentTime = new Date().getTime();
    const elapsedSeconds = Math.floor((currentTime - creationTime) / 1000);
    
    // Get the appropriate duration based on authentication status
    const maxDuration = getConversationDuration(isAuthenticated);
    
    // Plan is valid if elapsed time is less than the maximum duration
    return elapsedSeconds < maxDuration;
  } catch (error) {
    console.error('Error checking plan validity:', error);
    return false; // If there's an error, consider the plan invalid
  }
};
