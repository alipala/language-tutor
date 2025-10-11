import React, { useState, useEffect } from 'react';

interface AddLearnerModalProps {
  institutionId: string;
  onClose: () => void;
  onSuccess: (data: any) => void;
}

export const AddLearnerModal: React.FC<AddLearnerModalProps> = ({
  institutionId,
  onClose,
  onSuccess
}) => {
  const [formData, setFormData] = useState({
    email: '',
    name: '',
    tutor_id: ''
  });
  const [tutors, setTutors] = useState<any[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTutors();
  }, [institutionId]);

  const loadTutors = async () => {
    try {
      const response = await fetch(`/tutors/institution/${institutionId}`);
      if (!response.ok) {
        throw new Error('Failed to load tutors');
      }
      const data = await response.json();
      setTutors(data);
    } catch (err: any) {
      setError('Failed to load tutors');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch('/learners/enroll', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          institution_id: institutionId,
          enrolled_by: 'current_admin_id' // TODO: Get from auth context
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to add learner');
      }

      const data = await response.json();
      onSuccess(data);
    } catch (err: any) {
      setError(err.message);
      setIsSubmitting(false);
    }
  };

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Add New Learner</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name">Learner Name *</label>
            <input
              id="name"
              type="text"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              placeholder="Enter learner's full name"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email Address *</label>
            <input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => handleChange('email', e.target.value)}
              placeholder="learner@example.com"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="tutor">Assign to Tutor *</label>
            <select
              id="tutor"
              value={formData.tutor_id}
              onChange={(e) => handleChange('tutor_id', e.target.value)}
              required
            >
              <option value="">Select a tutor...</option>
              {tutors.map(tutor => (
                <option key={tutor.id} value={tutor.id}>
                  {tutor.name} ({tutor.email})
                </option>
              ))}
            </select>
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'Adding...' : 'Add Learner'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
