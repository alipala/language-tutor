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
      sessions_completed?: number;
      total_sessions?: number;
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
  // Progress tracking fields (optional for backward compatibility)
  total_sessions?: number;
  completed_sessions?: number;
  progress_percentage?: number;
  session_summaries?: string[];
}

// Get learning goals
export const getLearningGoals = async (): Promise<LearningGoal[]> => {
  const apiUrl = getApiUrl();
  const response = await fetch(`${apiUrl}/api/learning/goals`, {
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

// Flashcard API functions
export interface Flashcard {
  id: string;
  session_id: string;
  user_id: string;
  language: string;
  level: string;
  topic?: string;
  front: string;
  back: string;
  category: string;
  difficulty: string;
  tags: string[];
  created_at: string;
  last_reviewed?: string;
  review_count: number;
  correct_count: number;
  incorrect_count: number;
  mastery_level: number;
  next_review_date?: string;
  is_active: boolean;
}

export interface FlashcardSet {
  id: string;
  session_id: string;
  user_id: string;
  language: string;
  level: string;
  topic?: string;
  title: string;
  description: string;
  flashcards: Flashcard[];
  total_cards: number;
  created_at: string;
  is_completed: boolean;
  completed_at?: string;
}

export interface FlashcardGenerationRequest {
  session_id: string;
  language: string;
  level: string;
  topic?: string;
  conversation_content?: string;
  session_summary?: string;
  count?: number;
}

export interface FlashcardReviewRequest {
  flashcard_id: string;
  correct: boolean;
}

export interface FlashcardProgress {
  total_cards: number;
  reviewed_today: number;
  due_today: number;
  mastered_cards: number;
  average_mastery: number;
}

// Generate flashcards from a speaking session
export const generateFlashcards = async (request: FlashcardGenerationRequest): Promise<FlashcardSet> => {
  const apiUrl = getApiUrl();

  // This endpoint requires authentication
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('Authentication required to generate flashcards');
  }

  const response = await fetch(`${apiUrl}/api/flashcards/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to generate flashcards');
  }

  return await response.json();
};

// Get all flashcard sets for the current user
export const getUserFlashcardSets = async (): Promise<FlashcardSet[]> => {
  const apiUrl = getApiUrl();

  // This endpoint requires authentication
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('Authentication required to access flashcard sets');
  }

  const response = await fetch(`${apiUrl}/api/flashcards/sets`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to fetch flashcard sets');
  }

  return await response.json();
};

// Get a specific flashcard set with all its flashcards
export const getFlashcardSet = async (setId: string): Promise<FlashcardSet> => {
  const apiUrl = getApiUrl();

  // This endpoint requires authentication
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('Authentication required to access flashcard set');
  }

  const response = await fetch(`${apiUrl}/api/flashcards/set/${setId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to fetch flashcard set');
  }

  return await response.json();
};

// Get flashcards that are due for review
export const getDueFlashcards = async (limit: number = 10): Promise<Flashcard[]> => {
  const apiUrl = getApiUrl();

  // This endpoint requires authentication
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('Authentication required to access due flashcards');
  }

  const response = await fetch(`${apiUrl}/api/flashcards/due?limit=${limit}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to fetch due flashcards');
  }

  return await response.json();
};

// Review a flashcard (mark as correct or incorrect)
export const reviewFlashcard = async (request: FlashcardReviewRequest): Promise<any> => {
  const apiUrl = getApiUrl();

  // This endpoint requires authentication
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('Authentication required to review flashcards');
  }

  const response = await fetch(`${apiUrl}/api/flashcards/review`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to review flashcard');
  }

  return await response.json();
};

// Get overall flashcard progress statistics
export const getFlashcardProgress = async (): Promise<FlashcardProgress> => {
  const apiUrl = getApiUrl();

  // This endpoint requires authentication
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('Authentication required to access flashcard progress');
  }

  const response = await fetch(`${apiUrl}/api/flashcards/progress`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to fetch flashcard progress');
  }

  return await response.json();
};

// Delete a flashcard set
export const deleteFlashcardSet = async (setId: string): Promise<any> => {
  const apiUrl = getApiUrl();

  // This endpoint requires authentication
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('Authentication required to delete flashcard set');
  }

  const response = await fetch(`${apiUrl}/api/flashcards/set/${setId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to delete flashcard set');
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
    
    const response = await fetch(`${apiUrl}/api/learning/plan`, options);

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
  const response = await fetch(`${apiUrl}/api/learning/plan/${planId}`, {
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
  
  const response = await fetch(`${apiUrl}/api/learning/plan/${planId}/assign`, {
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
  
  const response = await fetch(`${apiUrl}/api/learning/plans`, {
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
