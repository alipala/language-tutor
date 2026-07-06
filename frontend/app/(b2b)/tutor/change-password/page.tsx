'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { B2BAuthCard, B2BField, b2bInputClass, b2bPrimaryButtonClass } from '@/src/components/b2b/B2BAuthCard';

const API_BASE_URL = '/api';

/**
 * Tutor first-login / forced password change.
 *
 * A newly-created tutor logs in with the temporary password the admin gave them
 * and is redirected here. They confirm the current (temp) password and set a new
 * one. On success the backend clears the reset flags and we send them to their
 * dashboard. Requires a valid tutor token (set at login).
 */
export default function TutorChangePasswordPage() {
  const router = useRouter();
  const [tutorId, setTutorId] = useState<string | null>(null);

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState<{ current?: string; next?: string; confirm?: string }>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Must be an authenticated tutor to be here.
  useEffect(() => {
    const token = localStorage.getItem('tutorToken');
    const id = localStorage.getItem('tutorId');
    if (!token || !id) {
      router.replace('/tutor/login');
      return;
    }
    setTutorId(id);
  }, [router]);

  const validate = (): boolean => {
    const next: typeof errors = {};
    if (!currentPassword) next.current = 'Enter your temporary password';
    if (!newPassword) next.next = 'Enter a new password';
    else if (newPassword.length < 8) next.next = 'At least 8 characters';
    else if (!/[a-z]/.test(newPassword) || !/[A-Z]/.test(newPassword) || !/\d/.test(newPassword))
      next.next = 'Use upper- and lower-case letters and a number';
    if (confirmPassword !== newPassword) next.confirm = 'Passwords do not match';
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError(null);
    if (!validate()) return;

    setLoading(true);
    try {
      const token = localStorage.getItem('tutorToken');
      const res = await fetch(`${API_BASE_URL}/tutor/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });

      if (res.status === 401) {
        // Token invalid/expired — back to login.
        localStorage.removeItem('tutorToken');
        router.replace('/tutor/login');
        return;
      }
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Could not change password');
      }

      // Success → go to the tutor's dashboard.
      const id = tutorId || localStorage.getItem('tutorId');
      router.replace(id ? `/tutor/dashboard/${id}` : '/tutor/login');
    } catch (err: any) {
      setApiError(err.message || 'Could not change password. Please try again.');
      setLoading(false);
    }
  };

  return (
    <B2BAuthCard
      icon={
        <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      }
      title="Set Your Password"
      subtitle="Welcome! For security, please replace the temporary password you were given."
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <B2BField id="current_password" label="Temporary Password *" error={errors.current}>
          <input
            id="current_password"
            type="password"
            value={currentPassword}
            onChange={(e) => {
              setCurrentPassword(e.target.value);
              if (errors.current) setErrors((p) => ({ ...p, current: undefined }));
            }}
            placeholder="The password your admin gave you"
            className={`${b2bInputClass} ${errors.current ? 'border-red-500' : ''}`}
            autoComplete="current-password"
          />
        </B2BField>

        <B2BField id="new_password" label="New Password *" error={errors.next}>
          <input
            id="new_password"
            type="password"
            value={newPassword}
            onChange={(e) => {
              setNewPassword(e.target.value);
              if (errors.next) setErrors((p) => ({ ...p, next: undefined }));
            }}
            placeholder="At least 8 chars, with a number & upper-case"
            className={`${b2bInputClass} ${errors.next ? 'border-red-500' : ''}`}
            autoComplete="new-password"
          />
        </B2BField>

        <B2BField id="confirm_password" label="Confirm New Password *" error={errors.confirm}>
          <input
            id="confirm_password"
            type="password"
            value={confirmPassword}
            onChange={(e) => {
              setConfirmPassword(e.target.value);
              if (errors.confirm) setErrors((p) => ({ ...p, confirm: undefined }));
            }}
            placeholder="Re-enter your new password"
            className={`${b2bInputClass} ${errors.confirm ? 'border-red-500' : ''}`}
            autoComplete="new-password"
          />
        </B2BField>

        {apiError && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3">
            <p className="text-sm text-red-600">{apiError}</p>
          </div>
        )}

        <button type="submit" disabled={loading} className={b2bPrimaryButtonClass}>
          {loading ? 'Saving...' : 'Set Password & Continue'}
        </button>
      </form>
    </B2BAuthCard>
  );
}
