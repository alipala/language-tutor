/**
 * Example usage of the ConsentScreen component
 */
import React, { useState } from 'react';
import { ConsentScreen } from './ConsentScreen';

function EnrollmentFlow() {
  const [showConsent, setShowConsent] = useState(true);

  const handleAccept = () => {
    console.log('Consent granted');
    // Navigate to learning dashboard
    setShowConsent(false);
  };

  const handleDecline = () => {
    console.log('Consent declined');
    // Navigate to individual learner path
    setShowConsent(false);
  };

  return showConsent ? (
    <ConsentScreen
      institutionName="Lincoln Academy"
      tutorName="Sarah Johnson"
      learnerId="user123"
      institutionId="inst456"
      tutorId="tutor789"
      onAccept={handleAccept}
      onDecline={handleDecline}
    />
  ) : (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h2>Enrollment Complete</h2>
      <p>You can now start learning!</p>
    </div>
  );
}

export default EnrollmentFlow;
