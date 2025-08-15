import { getApiUrl } from './api-utils';

// World Building Types
export interface StoryWorld {
  id: string;
  title: string;
  description: string;
  creator_id: string;
  creator_name?: string;
  language: 'en' | 'nl' | 'es' | 'de' | 'fr' | 'pt';
  target_level: 'A1' | 'A2' | 'B1' | 'B2' | 'C1' | 'C2';
  genre: 'mystery' | 'adventure' | 'romance' | 'sci-fi' | 'historical' | 'business' | 'cultural';
  privacy_setting: 'public' | 'private' | 'friends_only';
  learning_objectives: {
    primary_focus: 'grammar' | 'vocabulary' | 'pronunciation' | 'cultural';
    target_structures: string[];
    vocabulary_themes: string[];
  };
  world_state: {
    current_plot_point: string;
    active_characters: Array<{
      name: string;
      role: string;
      description: string;
    }>;
    locations: Array<{
      name: string;
      description: string;
    }>;
    important_items: Array<{
      name: string;
      significance: string;
    }>;
  };
  collaboration_settings: {
    max_contributors: number;
    session_duration_minutes: number;
    requires_approval: boolean;
    contribution_order: 'sequential' | 'random' | 'scheduled';
  };
  statistics: {
    total_sessions: number;
    total_contributors: number;
    average_session_rating: number;
    completion_rate: number;
    learning_effectiveness_score: number;
  };
  contributors: string[];
  status: 'draft' | 'active' | 'paused' | 'completed' | 'archived';
  tags: string[];
  featured: boolean;
  created_at: string;
  updated_at: string;
  last_contribution_at?: string;
}

export interface WorldFilters {
  language?: string[];
  target_level?: string[];
  genre?: string[];
  search?: string;
  featured?: boolean;
  status?: string[];
  session_duration_min?: number;
  session_duration_max?: number;
  sort_by?: 'created_at' | 'updated_at' | 'popularity' | 'rating';
  sort_order?: 'asc' | 'desc';
  creator_id?: string;
}

export interface WorldDiscoveryResponse {
  worlds: StoryWorld[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface WorldSearchResponse {
  worlds: StoryWorld[];
  total: number;
  query: string;
  suggestions?: string[];
}

// API Client Class
export class WorldBuildingAPI {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${getApiUrl()}/api/v2/worlds`;
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  // Check if world building feature is enabled
  async checkFeatureEnabled(): Promise<boolean> {
    try {
      // Try to access the world building health endpoint directly
      const response = await fetch(`${this.baseUrl}/health`);
      if (response.ok) {
        const result = await response.json();
        return result.feature_enabled === true;
      }
      return false;
    } catch (error) {
      console.error('Error checking world building feature:', error);
      return false;
    }
  }

  // Discover worlds with filtering and pagination
  async discoverWorlds(
    filters: WorldFilters = {},
    page: number = 1,
    limit: number = 12
  ): Promise<WorldDiscoveryResponse> {
    // If there's a search query, use the search endpoint
    if (filters.search && filters.search.trim()) {
      const searchResponse = await this.searchWorlds(filters.search, filters, limit);
      return {
        worlds: searchResponse.worlds,
        total: searchResponse.total,
        page: page,
        limit: limit,
        has_next: searchResponse.worlds.length === limit,
        has_prev: page > 1
      };
    }

    const params = new URLSearchParams();
    
    // Add pagination
    params.append('offset', ((page - 1) * limit).toString());
    params.append('limit', limit.toString());
    
    // Add filters
    if (filters.language?.length) {
      filters.language.forEach(lang => params.append('language', lang));
    }
    if (filters.target_level?.length) {
      filters.target_level.forEach(level => params.append('target_level', level));
    }
    if (filters.genre?.length) {
      filters.genre.forEach(genre => params.append('genre', genre));
    }
    if (filters.featured !== undefined) {
      params.append('featured', filters.featured.toString());
    }
    if (filters.status?.length) {
      filters.status.forEach(status => params.append('status', status));
    }
    if (filters.creator_id) {
      params.append('creator_id', filters.creator_id);
    }

    const response = await this.makeRequest<{worlds: StoryWorld[], total_count: number, has_more: boolean}>(`/discover?${params.toString()}`);
    
    return {
      worlds: response.worlds || [],
      total: response.total_count || 0,
      page: page,
      limit: limit,
      has_next: response.has_more || false,
      has_prev: page > 1
    };
  }

  // Search worlds
  async searchWorlds(
    query: string,
    filters: WorldFilters = {},
    limit: number = 20
  ): Promise<WorldSearchResponse> {
    const params = new URLSearchParams();
    params.append('q', query);
    params.append('limit', limit.toString());
    
    // Add filters
    if (filters.language?.length) {
      filters.language.forEach(lang => params.append('language', lang));
    }
    if (filters.target_level?.length) {
      filters.target_level.forEach(level => params.append('target_level', level));
    }
    if (filters.genre?.length) {
      filters.genre.forEach(genre => params.append('genre', genre));
    }

    const response = await this.makeRequest<{worlds: StoryWorld[], total_count: number, has_more: boolean}>(`/search?${params.toString()}`);
    
    return {
      worlds: response.worlds || [],
      total: response.total_count || 0,
      query: query
    };
  }

  // Get world details
  async getWorldDetails(worldId: string): Promise<StoryWorld> {
    return this.makeRequest<StoryWorld>(`/${worldId}`);
  }

  // Join a world as a contributor
  async joinWorld(worldId: string, userId: string): Promise<StoryWorld> {
    return this.makeRequest<StoryWorld>(`/${worldId}/join`, {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    });
  }

  // Get featured worlds
  async getFeaturedWorlds(limit: number = 6): Promise<StoryWorld[]> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    
    const response = await this.makeRequest<{worlds: StoryWorld[], total_count: number, has_more: boolean}>(`/featured?${params.toString()}`);
    return response.worlds || [];
  }

  // Get trending worlds
  async getTrendingWorlds(limit: number = 6): Promise<StoryWorld[]> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    
    const response = await this.makeRequest<{worlds: StoryWorld[], total_count: number, has_more: boolean}>(`/trending?${params.toString()}`);
    return response.worlds || [];
  }

  // Create a new story world
  async createStoryWorld(worldData: {
    title: string;
    description: string;
    language: string;
    target_level: string;
    genre: string;
    privacy_setting: string;
    current_plot_point: string;
    characters: Array<{
      name: string;
      role: string;
      description: string;
    }>;
    locations: Array<{
      name: string;
      description: string;
    }>;
    important_items: Array<{
      name: string;
      significance: string;
    }>;
    primary_focus: string;
    target_structures: string[];
    vocabulary_themes: string[];
    max_contributors: number;
    session_duration_minutes: number;
    requires_approval: boolean;
    tags: string[];
  }): Promise<{success: boolean; world_id: string; message: string}> {
    // Send flat structure that matches the backend StoryWorldCreate model
    const payload = {
      title: worldData.title,
      description: worldData.description,
      language: worldData.language,
      target_level: worldData.target_level,
      genre: worldData.genre,
      privacy_setting: worldData.privacy_setting,
      // Flattened story content fields
      current_plot_point: worldData.current_plot_point,
      characters: worldData.characters,
      locations: worldData.locations,
      important_items: worldData.important_items,
      // Flattened learning fields
      primary_focus: worldData.primary_focus,
      target_structures: worldData.target_structures,
      vocabulary_themes: worldData.vocabulary_themes,
      // Flattened collaboration fields
      max_contributors: worldData.max_contributors,
      session_duration_minutes: worldData.session_duration_minutes,
      requires_approval: worldData.requires_approval,
      // Optional fields
      tags: worldData.tags,
      status: 'active'
    };

    const response = await this.makeRequest<StoryWorld>('/create', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    return {
      success: true,
      world_id: response.id,
      message: 'Story world created successfully!'
    };
  }

  // ============================================================================
  // VOICE INTEGRATION METHODS
  // ============================================================================

  /**
   * Get configuration for a story voice session
   */
  async getStoryVoiceSessionConfig(
    worldId: string,
    sessionType: 'practice' | 'contribution' | 'review' = 'contribution'
  ): Promise<StoryVoiceSessionConfig> {
    const params = new URLSearchParams();
    params.append('session_type', sessionType);
    
    return this.makeRequest<StoryVoiceSessionConfig>(`/${worldId}/voice/session-config?${params.toString()}`);
  }

  /**
   * Validate if user can start a story voice session
   */
  async validateStoryVoiceSession(
    worldId: string,
    sessionType: 'practice' | 'contribution' | 'review' = 'contribution'
  ): Promise<StoryVoiceSessionValidation> {
    const formData = new FormData();
    formData.append('session_type', sessionType);

    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    
    const response = await fetch(`${this.baseUrl}/${worldId}/voice/validate-session`, {
      method: 'POST',
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Complete a story voice session and process the result
   */
  async completeStoryVoiceSession(
    worldId: string,
    sessionType: 'practice' | 'contribution' | 'review',
    transcript: string,
    durationSeconds: number,
    audioBase64?: string
  ): Promise<StoryVoiceSessionCompletion> {
    const formData = new FormData();
    formData.append('session_type', sessionType);
    formData.append('transcript', transcript);
    formData.append('duration_seconds', durationSeconds.toString());
    
    if (audioBase64) {
      formData.append('audio_base64', audioBase64);
    }

    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    
    const response = await fetch(`${this.baseUrl}/${worldId}/voice/complete-session`, {
      method: 'POST',
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get story context for voice session (for debugging/testing)
   */
  async getStoryContextForVoice(
    worldId: string,
    sessionType: 'practice' | 'contribution' | 'review' = 'contribution'
  ): Promise<StoryContext> {
    const params = new URLSearchParams();
    params.append('session_type', sessionType);
    
    return this.makeRequest<StoryContext>(`/${worldId}/voice/story-context?${params.toString()}`);
  }

  /**
   * Helper method to check if a world supports voice integration
   */
  async canUseVoiceIntegration(worldId: string): Promise<boolean> {
    try {
      const validation = await this.validateStoryVoiceSession(worldId, 'practice');
      return validation.can_access;
    } catch (error) {
      console.error('Error checking voice integration support:', error);
      return false;
    }
  }

  /**
   * Get session type limits and configuration
   */
  getSessionTypeLimits(sessionType: 'practice' | 'contribution' | 'review') {
    const limits = {
      practice: {
        min_duration: 30,    // 30 seconds
        max_duration: 120,   // 2 minutes
        saves_to_story: false,
        description: 'Explore story ideas and practice language skills'
      },
      contribution: {
        min_duration: 30,    // 30 seconds
        max_duration: 300,   // 5 minutes
        saves_to_story: true,
        description: 'Add your contribution to the collaborative story'
      },
      review: {
        min_duration: 0,     // No minimum for review
        max_duration: 600,   // 10 minutes for review
        saves_to_story: false,
        description: 'Review and analyze the collaborative story'
      }
    };
    
    return limits[sessionType];
  }
}

// Export singleton instance
export const worldBuildingAPI = new WorldBuildingAPI();

// Helper functions
export const LANGUAGE_OPTIONS = [
  { value: 'en', label: 'English', flag: '🇺🇸' },
  { value: 'nl', label: 'Dutch', flag: '🇳🇱' },
  { value: 'es', label: 'Spanish', flag: '🇪🇸' },
  { value: 'de', label: 'German', flag: '🇩🇪' },
  { value: 'fr', label: 'French', flag: '🇫🇷' },
  { value: 'pt', label: 'Portuguese', flag: '🇵🇹' },
];

export const LEVEL_OPTIONS = [
  { value: 'A1', label: 'A1 - Beginner', color: '#4ECFBF' },
  { value: 'A2', label: 'A2 - Elementary', color: '#FFD63A' },
  { value: 'B1', label: 'B1 - Intermediate', color: '#FFA955' },
  { value: 'B2', label: 'B2 - Upper Intermediate', color: '#F75A5A' },
  { value: 'C1', label: 'C1 - Advanced', color: '#9B59B6' },
  { value: 'C2', label: 'C2 - Proficient', color: '#2C3E50' },
];

export const GENRE_OPTIONS = [
  { value: 'mystery', label: 'Mystery', icon: '🔍' },
  { value: 'adventure', label: 'Adventure', icon: '🗺️' },
  { value: 'romance', label: 'Romance', icon: '💕' },
  { value: 'sci-fi', label: 'Sci-Fi', icon: '🚀' },
  { value: 'historical', label: 'Historical', icon: '🏛️' },
  { value: 'business', label: 'Business', icon: '💼' },
  { value: 'cultural', label: 'Cultural', icon: '🌍' },
];

export const SORT_OPTIONS = [
  { value: 'created_at', label: 'Newest First' },
  { value: 'updated_at', label: 'Recently Updated' },
  { value: 'popularity', label: 'Most Popular' },
  { value: 'rating', label: 'Highest Rated' },
];

// Voice Integration Types
export interface StoryVoiceSessionConfig {
  success: boolean;
  story_context: {
    world_id: string;
    world_title: string;
    genre: string;
    language: string;
    target_level: string;
    session_type: string;
    current_plot_point: string;
    active_characters: Array<{
      name: string;
      role: string;
      description: string;
    }>;
    locations: Array<{
      name: string;
      description: string;
    }>;
    important_items: Array<{
      name: string;
      significance: string;
    }>;
    primary_focus: string;
    target_structures: string[];
    vocabulary_themes: string[];
    previous_contribution?: {
      transcript: string;
      contributor_name: string;
      session_number: number;
    };
    session_limits: {
      min_duration: number;
      max_duration: number;
      saves_to_story: boolean;
    };
    collaboration_settings: any;
    total_contributions: number;
  };
  session_limits: {
    min_duration: number;
    max_duration: number;
    saves_to_story: boolean;
  };
  enhanced_prompt: string;
  session_type: string;
  world_id: string;
  user_id: string;
}

export interface StoryVoiceSessionValidation {
  can_access: boolean;
  message: string;
  session_type: string;
  world_id: string;
  user_id: string;
}

export interface StoryVoiceSessionCompletion {
  success: boolean;
  message: string;
  session_type: string;
  duration_seconds: number;
  speaking_minutes: number;
  contribution_id?: string;
}

export interface StoryContext {
  world_id: string;
  world_title: string;
  genre: string;
  language: string;
  target_level: string;
  session_type: string;
  current_plot_point: string;
  active_characters: Array<{
    name: string;
    role: string;
    description: string;
  }>;
  locations: Array<{
    name: string;
    description: string;
  }>;
  important_items: Array<{
    name: string;
    significance: string;
  }>;
  primary_focus: string;
  target_structures: string[];
  vocabulary_themes: string[];
  previous_contribution?: {
    transcript: string;
    contributor_name: string;
    session_number: number;
  };
  session_limits: {
    min_duration: number;
    max_duration: number;
    saves_to_story: boolean;
  };
  collaboration_settings: any;
  total_contributions: number;
}
