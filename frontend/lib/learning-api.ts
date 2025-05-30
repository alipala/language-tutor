import { getApiUrl } from './api-utils';
// No need to import authentication functions, we'll check directly

export interface LearningGoal {
  id: string;
  text: string;
  category: string;
}

export interface LearningPlanRequest {
  language: string;
  proficiency_level: string;
  goals: string[];
  duration_months: number;
  custom_goal?: string;
  assessment_data?: any; // Speaking assessment data
}

export interface LearningPlan {
  id: string;
  user_id?: string;
  language: string;
  proficiency_level: string;
  goals: string[];
  duration_months: number;
  custom_goal?: string;
  plan_content: {
    overview: string;
    weekly_schedule: {
      week: number;
      focus: string;
      activities: string[];
      resources?: string[];
    }[];
    resources?: {
      apps: string[];
      books: string[];
      websites: string[];
      other: string[];
    } | string[];
    milestones?: {
      milestone: string;
      timeline: string;
      assessment: string;
    }[];
    title?: string;
    assessment_summary?: {
      overall_score: number;
      recommended_level: string;
      strengths: string[];
      areas_for_improvement: string[];
      skill_scores: {
        pronunciation: number;
        grammar: number;
        vocabulary: number;
        fluency: number;
        coherence: number;
      };
    };
  };
  assessment_data?: {
    recognized_text: string;
    recommended_level: string;
    overall_score: number;
    confidence: number;
    pronunciation: {
      score: number;
      feedback: string;
      examples: string[];
    };
    grammar: {
      score: number;
      feedback: string;
      examples: string[];
    };
    vocabulary: {
      score: number;
      feedback: string;
      examples: string[];
    };
    fluency: {
      score: number;
      feedback: string;
      examples: string[];
    };
    coherence: {
      score: number;
      feedback: string;
      examples: string[];
    };
    strengths: string[];
    areas_for_improvement: string[];
    next_steps: string[];
  };
  created_at: string;
}

// Get learning goals
export const getLearningGoals = async (): Promise<LearningGoal[]> => {
  const apiUrl = getApiUrl();
  const response = await fetch(`${apiUrl}/learning/goals`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to fetch learning goals');
  }

  return await response.json();
};

// Create learning plan
export const createLearningPlan = async (planRequest: LearningPlanRequest): Promise<LearningPlan> => {
  const apiUrl = getApiUrl();
  
  // Try to get auth token if available, but don't require it
  let headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  
  // Get auth token from local storage if available
  const token = localStorage.getItem('token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  try {
    // Wrap the request data in a plan_request field as expected by the backend
    // Only include credentials if we have a token (authenticated user)
    const options: RequestInit = {
      method: 'POST',
      headers,
      body: JSON.stringify({ plan_request: planRequest }),
    };
    
    // Only include credentials for authenticated users
    if (token) {
      options.credentials = 'include';
    }
    
    const response = await fetch(`${apiUrl}/learning/plan`, options);

    if (!response.ok) {
      // Handle different error status codes
      if (response.status === 401) {
        throw new Error('Not authenticated');
      } else if (response.status === 422) {
        throw new Error('Invalid plan request format');
      } else {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to create learning plan: ${response.status}`);
      }
    }

    return await response.json();
  } catch (error) {
    console.error('Error in createLearningPlan:', error);
    throw error;
  }
};

// Get learning plan by ID
export const getLearningPlan = async (planId: string): Promise<LearningPlan> => {
  const apiUrl = getApiUrl();
  
  // Check if user is authenticated
  const token = localStorage.getItem('token');
  
  // For guest users, try to get the plan from session storage first
  if (!token) {
    // Try to get language and level from session storage
    const language = sessionStorage.getItem('selectedLanguage');
    const level = sessionStorage.getItem('selectedLevel');
    
    // If we have the basic info in session storage, create a minimal plan object
    if (language && level) {
      console.log('Creating minimal plan for guest user from session storage');
      return {
        id: planId,
        language,
        proficiency_level: level,
        goals: [],
        duration_months: 3,
        plan_content: {
          overview: '',
          weekly_schedule: [],
          resources: { apps: [], books: [], websites: [], other: [] },
          milestones: []
        },
        created_at: new Date().toISOString()
      };
    }
    
    // If we don't have the info in session storage, throw an error
    throw new Error('Authentication required to access learning plan');
  }
  
  // For authenticated users, fetch the plan from the API
  const response = await fetch(`${apiUrl}/learning/plan/${planId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to fetch learning plan');
  }

  return await response.json();
};

// Assign learning plan to user
export const assignPlanToUser = async (planId: string): Promise<LearningPlan> => {
  const apiUrl = getApiUrl();
  
  // This endpoint requires authentication
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('Authentication required to assign learning plan');
  }
  
  const response = await fetch(`${apiUrl}/learning/plan/${planId}/assign`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to assign learning plan to user');
  }

  return await response.json();
};

// Get all learning plans for the current user
export const getUserLearningPlans = async (): Promise<LearningPlan[]> => {
  const apiUrl = getApiUrl();
  
  // This endpoint requires authentication
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('Authentication required to access user learning plans');
  }
  
  const response = await fetch(`${apiUrl}/learning/plans`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to fetch user learning plans');
  }

  return await response.json();
};
