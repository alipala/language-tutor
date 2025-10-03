'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { institutionService } from '../../../src/services/institutionService';

export default function InstitutionDashboard() {
  const router = useRouter();
  const [institution, setInstitution] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadInstitutionData = async () => {
      try {
        // Check if user is authenticated
        const token = localStorage.getItem('institution_token');
        const institutionId = localStorage.getItem('institution_id');

        if (!token || !institutionId) {
          router.push('/institution/login');
          return;
        }

        // Fetch institution data
        const data = await institutionService.getInstitution(institutionId);
        setInstitution(data);
        setLoading(false);
      } catch (err: any) {
        console.error('Error loading institution data:', err);
        setError('Failed to load institution data');
        setLoading(false);
        
        // If unauthorized, redirect to login
        if (err.response?.status === 401) {
          localStorage.removeItem('institution_token');
          localStorage.removeItem('institution_id');
          router.push('/institution/login');
        }
      }
    };

    loadInstitutionData();
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem('institution_token');
    localStorage.removeItem('institution_id');
    router.push('/institution/login');
  };

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}>
        <div>Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}>
        <div style={{ textAlign: 'center' }}>
          <h2 style={{ color: '#e53e3e' }}>Error</h2>
          <p>{error}</p>
          <button 
            onClick={() => router.push('/institution/login')}
            style={{
              marginTop: '1rem',
              padding: '0.5rem 1rem',
              backgroundColor: '#4ECFBF',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ 
      minHeight: '100vh',
      backgroundColor: '#f7fafc',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      {/* Header */}
      <header style={{
        backgroundColor: '#4ECFBF',
        color: 'white',
        padding: '1rem 2rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Institution Dashboard</h1>
        <button
          onClick={handleLogout}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: 'white',
            color: '#4ECFBF',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: '500'
          }}
        >
          Logout
        </button>
      </header>

      {/* Main Content */}
      <main style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
        {/* Institution Info Card */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '2rem',
          marginBottom: '2rem',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <h2 style={{ marginTop: 0, color: '#2d3748' }}>
            {institution?.name || 'Institution Name'}
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem', marginTop: '1.5rem' }}>
            <div>
              <p style={{ margin: '0.5rem 0', color: '#718096' }}>
                <strong>Type:</strong> {institution?.institution_type || 'N/A'}
              </p>
              <p style={{ margin: '0.5rem 0', color: '#718096' }}>
                <strong>Admin Email:</strong> {institution?.admin_email || 'N/A'}
              </p>
            </div>
            <div>
              <p style={{ margin: '0.5rem 0', color: '#718096' }}>
                <strong>Contact:</strong> {institution?.contact_phone || 'N/A'}
              </p>
              <p style={{ margin: '0.5rem 0', color: '#718096' }}>
                <strong>Website:</strong> {institution?.website || 'N/A'}
              </p>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '1.5rem',
          marginBottom: '2rem'
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '1.5rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            cursor: 'pointer',
            transition: 'transform 0.2s',
          }}
          onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
          onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
          >
            <h3 style={{ marginTop: 0, color: '#2d3748' }}>Manage Learners</h3>
            <p style={{ color: '#718096', fontSize: '0.875rem' }}>
              View and manage enrolled learners
            </p>
          </div>

          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '1.5rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            cursor: 'pointer',
            transition: 'transform 0.2s',
          }}
          onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
          onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
          >
            <h3 style={{ marginTop: 0, color: '#2d3748' }}>View Reports</h3>
            <p style={{ color: '#718096', fontSize: '0.875rem' }}>
              Access learning analytics and reports
            </p>
          </div>

          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '1.5rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            cursor: 'pointer',
            transition: 'transform 0.2s',
          }}
          onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
          onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
          >
            <h3 style={{ marginTop: 0, color: '#2d3748' }}>Settings</h3>
            <p style={{ color: '#718096', fontSize: '0.875rem' }}>
              Update institution settings
            </p>
          </div>
        </div>

        {/* Coming Soon Notice */}
        <div style={{
          backgroundColor: '#fff5e6',
          border: '1px solid #ffd699',
          borderRadius: '8px',
          padding: '1rem',
          textAlign: 'center'
        }}>
          <p style={{ margin: 0, color: '#996600' }}>
            📊 Full dashboard features coming soon! This is a basic version.
          </p>
        </div>
      </main>
    </div>
  );
}
