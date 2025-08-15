from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId

# Custom ObjectId field for Pydantic models
class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not v or not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, _schema_generator, _field):
        return {"type": "string"}

# Story Learning Metrics Collection
class StoryLearningMetrics(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    world_id: str
    contribution_id: Optional[str] = None  # Link to specific contribution
    
    # Vocabulary tracking
    vocabulary_acquired: List[Dict[str, Any]] = []  # [{"word": "castle", "context": "medieval story", "learned_at": datetime}]
    vocabulary_reinforced: List[str] = []  # Words that appeared again and were used correctly
    
    # Grammar tracking
    grammar_patterns_used: List[Dict[str, Any]] = []  # [{"pattern": "past_perfect", "examples": ["had been"], "accuracy": 0.8}]
    grammar_improvements: List[Dict[str, Any]] = []  # [{"area": "verb_tenses", "before_score": 0.6, "after_score": 0.8}]
    
    # Pronunciation tracking
    pronunciation_improvements: List[Dict[str, Any]] = []  # [{"phoneme": "/θ/", "word": "think", "improvement": 0.2}]
    pronunciation_challenges: List[str] = []  # Sounds that need more practice
    
    # Cultural understanding
    cultural_references_understood: List[Dict[str, Any]] = []  # [{"reference": "medieval customs", "context": "story setting"}]
    cultural_learning_moments: List[Dict[str, Any]] = []  # [{"moment": "learned about British tea culture", "story_context": "..."}]
    
    # Story-specific metrics
    story_engagement_score: float = 0.0  # 0-1 based on participation quality
    narrative_contribution_quality: float = 0.0  # 0-1 based on story coherence and creativity
    collaborative_skills_score: float = 0.0  # 0-1 based on how well they build on others' contributions
    
    # Learning effectiveness
    retention_score: float = 0.0  # How well they remember and use previous story elements
    application_score: float = 0.0  # How well they apply learned concepts in new contexts
    
    # Session metadata
    session_duration_minutes: float = 0.0
    contribution_count: int = 0
    language: str
    proficiency_level: str
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Learning Gate Check Result
class LearningGateResult(BaseModel):
    can_contribute: bool
    gate_checks: Dict[str, bool]  # {"assessment_completed": True, "level_match": True, ...}
    blocking_reasons: List[str] = []  # Reasons why contribution is blocked
    recommendations: List[str] = []  # What user should do to unlock contribution
    user_level: Optional[str] = None
    world_level: Optional[str] = None
    days_since_practice: Optional[int] = None
    sessions_remaining: Optional[int] = None

# Progress Update Request
class StoryProgressUpdate(BaseModel):
    user_id: str
    world_id: str
    contribution_id: Optional[str] = None
    session_duration_minutes: float
    
    # Learning metrics to update
    vocabulary_learned: List[Dict[str, Any]] = []
    grammar_improvements: List[Dict[str, Any]] = []
    pronunciation_improvements: List[Dict[str, Any]] = []
    cultural_insights: List[Dict[str, Any]] = []
    
    # Engagement scores
    engagement_score: float = 0.0
    contribution_quality: float = 0.0
    collaboration_score: float = 0.0
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

# Achievement Extension Models
class StoryAchievement(BaseModel):
    achievement_id: str
    name: str
    description: str
    icon: str
    category: str = "story"  # "story", "collaboration", "learning"
    requirements: Dict[str, Any]  # Flexible requirements structure
    reward_points: int = 0
    is_hidden: bool = False  # Hidden until unlocked
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class UserStoryAchievement(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    achievement_id: str
    world_id: Optional[str] = None  # If achievement is world-specific
    
    earned_at: datetime = Field(default_factory=datetime.utcnow)
    progress_data: Dict[str, Any] = {}  # Data that led to earning this achievement
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Level Assessment Integration
class LevelAssessmentResult(BaseModel):
    current_level: str
    confidence_score: float  # 0-1 how confident we are in this level
    strengths: List[str] = []
    areas_for_improvement: List[str] = []
    recommended_next_level: Optional[str] = None
    assessment_date: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

# Story-based Learning Analytics
class StoryLearningAnalytics(BaseModel):
    user_id: str
    language: str
    
    # Aggregated metrics across all stories
    total_story_sessions: int = 0
    total_story_minutes: float = 0.0
    total_contributions: int = 0
    total_worlds_participated: int = 0
    
    # Learning progress
    vocabulary_growth_rate: float = 0.0  # Words learned per session
    grammar_improvement_rate: float = 0.0  # Grammar score improvement per session
    pronunciation_improvement_rate: float = 0.0  # Pronunciation score improvement per session
    
    # Engagement metrics
    average_engagement_score: float = 0.0
    average_contribution_quality: float = 0.0
    average_collaboration_score: float = 0.0
    
    # Story preferences and strengths
    preferred_genres: List[str] = []
    strongest_story_types: List[str] = []  # Where user performs best
    cultural_knowledge_areas: List[str] = []
    
    # Level progression
    level_progression_history: List[Dict[str, Any]] = []  # [{"level": "B1", "achieved_at": datetime, "story_contributions": 5}]
    current_effective_level: str = "A1"  # Based on story performance
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

# Integration with existing progress system
class StoryProgressIntegration(BaseModel):
    """Model for integrating story progress with main progress tracking"""
    user_id: str
    
    # Story-specific vocabulary to add to main vocabulary list
    story_vocabulary_learned: List[Dict[str, Any]] = []
    
    # Story-based improvements to add to main progress
    story_grammar_improvements: List[Dict[str, Any]] = []
    story_pronunciation_improvements: List[Dict[str, Any]] = []
    
    # Minutes and sessions to add to main tracking
    story_minutes_to_add: float = 0.0
    story_sessions_to_add: int = 0
    
    # Achievement IDs to unlock in main system
    achievements_to_unlock: List[str] = []
    
    # Level advancement recommendation
    level_advancement_recommendation: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
