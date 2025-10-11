import React, { useState, useEffect } from 'react';
import { AddLearnerModal } from '../../../components/admin/AddLearnerModal';
import { BulkImportModal } from '../../../components/admin/BulkImportModal';
import './LearnerManagement.css';

interface Learner {
  user_id: string;
  name: string;
  email: string;
  tutor_name: string;
  consent_given: boolean;
  enrolled_at: string;
}

export const LearnerManagement: React.FC<{ institutionId: string }> = ({
  institutionId
}) => {
  const [learners, setLearners] = useState<Learner[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showBulkModal, setShowBulkModal] = useState(false);

  useEffect(() => {
    loadLearners();
  }, [institutionId]);

  const loadLearners = async () => {
    try {
      const response = await fetch(`/learners/institution/${institutionId}`);
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

  const handleAddLearner = async (learnerData: any) => {
    // API call to add learner
    await loadLearners();
    setShowAddModal(false);
  };

  const handleBulkImport = async (csvData: any[]) => {
    // API call to bulk import
    await loadLearners();
    setShowBulkModal(false);
  };

  if (loading) {
    return (
      <div className="learner-management">
        <div className="loading">Loading learners...</div>
      </div>
    );
  }

  return (
    <div className="learner-management">
      <div className="header">
        <h1>Learner Management</h1>
        <div className="actions">
          <button
            className="btn btn-primary"
            onClick={() => setShowAddModal(true)}
          >
            Add Learner
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => setShowBulkModal(true)}
          >
            Bulk Import CSV
          </button>
        </div>
      </div>

      <div className="stats">
        <div className="stat-card">
          <h3>Total Learners</h3>
          <p className="stat-value">{learners.length}</p>
        </div>
        <div className="stat-card">
          <h3>Consented</h3>
          <p className="stat-value">
            {learners.filter(l => l.consent_given).length}
          </p>
        </div>
        <div className="stat-card">
          <h3>Pending Consent</h3>
          <p className="stat-value">
            {learners.filter(l => !l.consent_given).length}
          </p>
        </div>
      </div>

      <div className="learners-table">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Tutor</th>
              <th>Consent Status</th>
              <th>Enrolled Date</th>
            </tr>
          </thead>
          <tbody>
            {learners.map(learner => (
              <tr key={learner.user_id}>
                <td>{learner.name}</td>
                <td>{learner.email}</td>
                <td>{learner.tutor_name}</td>
                <td>
                  <span className={`status ${learner.consent_given ? 'active' : 'pending'}`}>
                    {learner.consent_given ? 'Granted' : 'Pending'}
                  </span>
                </td>
                <td>{new Date(learner.enrolled_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showAddModal && (
        <AddLearnerModal
          institutionId={institutionId}
          onClose={() => setShowAddModal(false)}
          onSuccess={handleAddLearner}
        />
      )}

      {showBulkModal && (
        <BulkImportModal
          institutionId={institutionId}
          onClose={() => setShowBulkModal(false)}
          onSuccess={handleBulkImport}
        />
      )}
    </div>
  );
};
