'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import './InstitutionSignupSuccess.css';

export const InstitutionSignupSuccess: React.FC = () => {
  const router = useRouter();
  const [institutionCode, setInstitutionCode] = useState<string>('');
  const [institutionId, setInstitutionId] = useState<string>('');

  useEffect(() => {
    // Get institution data from localStorage
    const code = localStorage.getItem('institution_code');
    const id = localStorage.getItem('institution_id');

    if (!code || !id) {
      // If no data, redirect back to signup
      router.push('/institution/signup');
      return;
    }

    setInstitutionCode(code);
    setInstitutionId(id);
  }, [router]);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(institutionCode);
    // You could add a toast notification here
  };

  return (
    <div className="institution-success-page">
      <div className="success-container">
        <div className="success-icon">
          <svg
            className="checkmark"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 52 52"
          >
            <circle className="checkmark-circle" cx="26" cy="26" r="25" fill="none" />
            <path
              className="checkmark-check"
              fill="none"
              d="M14.1 27.2l7.1 7.2 16.7-16.8"
            />
          </svg>
        </div>

        <h1>Institution Account Created!</h1>
        <p className="success-message">
          Your institution has been successfully registered with MyTaco AI.
        </p>

        <div className="institution-code-section">
          <h2>Your Institution Code</h2>
          <div className="code-box">
            <code className="institution-code">{institutionCode}</code>
            <button className="copy-button" onClick={copyToClipboard} title="Copy to clipboard">
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
            </button>
          </div>
          <p className="code-info">
            Share this code with tutors and learners to join your institution
          </p>
        </div>

        <div className="next-steps">
          <h2>Next Steps</h2>
          <div className="steps-grid">
            <div className="step-card">
              <div className="step-number">1</div>
              <h3>Invite Tutors</h3>
              <p>Add your language tutors to the platform</p>
            </div>
            <div className="step-card">
              <div className="step-number">2</div>
              <h3>Enroll Learners</h3>
              <p>Students can self-enroll using your institution code</p>
            </div>
            <div className="step-card">
              <div className="step-number">3</div>
              <h3>Start Learning</h3>
              <p>Monitor progress and manage your language programs</p>
            </div>
          </div>
        </div>

        <div className="action-buttons">
          <button className="primary-button" onClick={() => router.push('/institution/login')}>
            Go to Dashboard
          </button>
          <button className="secondary-button" onClick={() => window.print()}>
            Print Details
          </button>
        </div>

        <div className="support-section">
          <p>
            Need help getting started?{' '}
            <a href="/help" className="help-link">
              Visit our Help Center
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};
