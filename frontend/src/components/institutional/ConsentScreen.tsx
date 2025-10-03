/**
 * Consent screen for learners joining an institution
 */
import React, { useState } from 'react';
import './ConsentScreen.css';

interface ConsentScreenProps {
  institutionName: string;
  tutorName: string;
  learnerId: string;
  institutionId: string;
  tutorId: string;
  onAccept: () => void;
  onDecline: () => void;
}

export const ConsentScreen: React.FC<ConsentScreenProps> = ({
  institutionName,
  tutorName,
  learnerId,
  institutionId,
  tutorId,
  onAccept,
  onDecline
}) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const dataToShare = [
    'Assessment results (language level, skill scores)',
    'Learning plans and weekly progress',
    'Practice session summaries',
    'Progress metrics (time spent, sessions completed)'
  ];

  const dataNotShared = [
    'Payment information',
    'Personal messages or notes you create',
    'Account password',
    'Email address (unless you share it)'
  ];

  const handleAccept = async () => {
    setIsProcessing(true);
    setError(null);
    try {
      // Call consent service
      const { consentService } = await import('../../services/consentService');
      await consentService.grantConsent({
        learner_id: learnerId,
        institution_id: institutionId,
        tutor_id: tutorId
      });

      onAccept();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to grant consent');
      setIsProcessing(false);
    }
  };

  const handleDecline = () => {
    onDecline();
  };

  return (
    <div className="consent-screen-overlay">
      <div className="consent-screen-container">
        <div className="consent-header">
          <h2>Data Sharing Consent</h2>
          <p className="institution-info">
            <strong>{institutionName}</strong> would like to monitor your learning progress
          </p>
        </div>

        <div className="consent-body">
          <div className="consent-section">
            <h3>👨‍🏫 Your Assigned Tutor</h3>
            <p className="tutor-name">{tutorName}</p>
          </div>

          <div className="consent-section">
            <h3>📊 What Will Be Shared</h3>
            <ul className="data-list data-shared">
              {dataToShare.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="consent-section">
            <h3>🔒 What Will NOT Be Shared</h3>
            <ul className="data-list data-not-shared">
              {dataNotShared.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="consent-section rights-section">
            <h3>✅ Your Rights</h3>
            <p>
              You can <strong>revoke this consent at any time</strong> from your Settings page.
              Revoking consent will stop all data sharing with the institution, but your
              learning progress will be preserved.
            </p>
          </div>

          {error && (
            <div className="consent-error">
              {error}
            </div>
          )}

          <div className="consent-note">
            <p>
              💡 <strong>Note:</strong> Declining won't affect your ability to use MyTaco AI
              as an individual learner. You'll continue to have full access to all learning features.
            </p>
          </div>
        </div>

        <div className="consent-actions">
          <button
            className="btn-decline"
            onClick={handleDecline}
            disabled={isProcessing}
          >
            Decline
          </button>
          <button
            className="btn-accept"
            onClick={handleAccept}
            disabled={isProcessing}
          >
            {isProcessing ? 'Processing...' : 'I Accept'}
          </button>
        </div>
      </div>
    </div>
  );
};
