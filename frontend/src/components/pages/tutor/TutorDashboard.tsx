import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './TutorDashboard.css';

interface Learner {
  user_id: string;
  name: string;
  email: string;
  consent_given: boolean;
  enrolled_at: string;
  last_session?: string;
  total_sessions?: number;
  practice_minutes?: number;
}

export const TutorDashboard: React.FC<{ tutorId: string }> = ({ tutorId }) => {
  const [learners, setLearners] = useState<Learner[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterConsent, setFilterConsent] = useState<'all' | 'consented' | 'pending'>('all');

  useEffect(() => {
    loadLearners();
  }, [tutorId]);

  const loadLearners = async () => {
    try {
      const response = await fetch(`/learners/tutor/${tutorId}`);
      if (!response.ok) {
        throw new Error('Failed to load learners');
      }
      const data = await response.json();
      setLearners(data);
    } catch (error) {
      console.error('Failed to load learners:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredLearners = learners.filter(learner => {
    if (filterConsent === 'consented') return learner.consent_given;
    if (filterConsent === 'pending') return !learner.consent_given;
    return true;
  });

  if (loading) {
    return (
      <div className="tutor-dashboard">
        <div className="loading">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="tutor-dashboard">
      <div className="dashboard-header">
        <h1>My Learners</h1>

        <div className="stats-row">
          <div className="stat-card">
            <h3>Total Learners</h3>
            <p className="stat-value">{learners.length}</p>
          </div>
          <div className="stat-card">
            <h3>Active Today</h3>
            <p className="stat-value">
              {learners.filter(l =>
                l.last_session &&
                new Date(l.last_session).toDateString() === new Date().toDateString()
              ).length}
            </p>
          </div>
          <div className="stat-card">
            <h3>Pending Consent</h3>
            <p className="stat-value">
              {learners.filter(l => !l.consent_given).length}
            </p>
          </div>
        </div>
      </div>

      <div className="filters">
        <button
          className={filterConsent === 'all' ? 'active' : ''}
          onClick={() => setFilterConsent('all')}
        >
          All Learners
        </button>
        <button
          className={filterConsent === 'consented' ? 'active' : ''}
          onClick={() => setFilterConsent('consented')}
        >
          Consented Only
        </button>
        <button
          className={filterConsent === 'pending' ? 'active' : ''}
          onClick={() => setFilterConsent('pending')}
        >
          Pending Consent
        </button>
      </div>

      <div className="learners-grid">
        {filteredLearners.map(learner => (
          <div key={learner.user_id} className="learner-card">
            <div className="learner-info">
              <h3>{learner.name}</h3>
              <p className="learner-email">{learner.email}</p>

              <div className="consent-badge">
                {learner.consent_given ? (
                  <span className="badge success">Consent Granted</span>
                ) : (
                  <span className="badge warning">Pending Consent</span>
                )}
              </div>
            </div>

            {learner.consent_given && (
              <div className="learner-stats">
                <div className="stat">
                  <span className="label">Sessions</span>
                  <span className="value">{learner.total_sessions || 0}</span>
                </div>
                <div className="stat">
                  <span className="label">Minutes</span>
                  <span className="value">{learner.practice_minutes || 0}</span>
                </div>
                <div className="stat">
                  <span className="label">Last Active</span>
                  <span className="value">
                    {learner.last_session
                      ? new Date(learner.last_session).toLocaleDateString()
                      : 'Never'
                    }
                  </span>
                </div>
              </div>
            )}

            <div className="card-actions">
              {learner.consent_given ? (
                <Link to={`/tutor/learner/${learner.user_id}`} className="view-details-btn">
                  View Details
                </Link>
              ) : (
                <span className="disabled-link">
                  Waiting for consent
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {filteredLearners.length === 0 && (
        <div className="empty-state">
          <p>No learners found matching your filter</p>
        </div>
      )}
    </div>
  );
};
