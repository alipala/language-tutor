import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import './LearnerProfile.css';

interface LearnerProfile {
  user_id: string;
  name: string;
  email: string;
  current_level: string;
  learning_plan: any;
  recent_sessions: any[];
  progress_metrics: {
    total_sessions: number;
    practice_minutes: number;
    assessment_scores: any[];
  };
}

export const LearnerProfile: React.FC = () => {
  const { learnerId } = useParams<{ learnerId: string }>();
  const [profile, setProfile] = useState<LearnerProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (learnerId) {
      loadProfile();
    }
  }, [learnerId]);

  const loadProfile = async () => {
    try {
      const response = await fetch(`/api/v1/tutor/learner/${learnerId}`);
      if (!response.ok) {
        throw new Error('Failed to load profile');
      }
      const data = await response.json();
      setProfile(data);
    } catch (error) {
      console.error('Failed to load profile:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="learner-profile">
        <div className="loading">Loading learner profile...</div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="learner-profile">
        <div className="error">Learner not found</div>
      </div>
    );
  }

  return (
    <div className="learner-profile">
      <div className="profile-header">
        <h1>{profile.name}</h1>
        <p className="email">{profile.email}</p>
        <span className="level-badge">{profile.current_level}</span>
      </div>

      <div className="profile-sections">
        <section className="progress-section">
          <h2>Progress Overview</h2>
          <div className="metrics-grid">
            <div className="metric">
              <h3>Total Sessions</h3>
              <p className="metric-value">
                {profile.progress_metrics.total_sessions}
              </p>
            </div>
            <div className="metric">
              <h3>Practice Time</h3>
              <p className="metric-value">
                {profile.progress_metrics.practice_minutes} min
              </p>
            </div>
          </div>
        </section>

        <section className="sessions-section">
          <h2>Recent Sessions</h2>
          <div className="sessions-list">
            {profile.recent_sessions.map((session, i) => (
              <div key={i} className="session-card">
                <div className="session-date">
                  {new Date(session.created_at).toLocaleDateString()}
                </div>
                <div className="session-details">
                  <p><strong>Topic:</strong> {session.topic}</p>
                  <p><strong>Duration:</strong> {session.duration_minutes} min</p>
                  <p><strong>Summary:</strong> {session.summary}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="learning-plan-section">
          <h2>Current Learning Plan</h2>
          {profile.learning_plan ? (
            <div className="learning-plan">
              <p><strong>Language:</strong> {profile.learning_plan.language}</p>
              <p><strong>Level:</strong> {profile.learning_plan.proficiency_level}</p>
              <p><strong>Duration:</strong> {profile.learning_plan.duration_months} months</p>
            </div>
          ) : (
            <p>No active learning plan</p>
          )}
        </section>
      </div>
    </div>
  );
};
