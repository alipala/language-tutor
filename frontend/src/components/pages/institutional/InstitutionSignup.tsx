'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { institutionService, ActivationCodePreview } from '../../../services/institutionService';
import Link from 'next/link';
import { B2BAuthCard, B2BField, b2bInputClass, b2bPrimaryButtonClass } from '@/src/components/b2b/B2BAuthCard';

const TYPE_LABELS: Record<string, string> = {
  school: 'School',
  university: 'University',
  language_center: 'Language Center',
  corporate: 'Corporate',
};

function prettyType(t: string): string {
  const key = (t || '').trim().toLowerCase().replace(/\s+/g, '_');
  return TYPE_LABELS[key] || t;
}

/**
 * Institution activation page.
 *
 * This is NOT a self-serve signup: the school was invited by the master admin,
 * who already entered the institution name / email / type / plan when generating
 * the activation code. Here the invited admin only confirms those details
 * (shown read-only) and sets their name + password. The code arrives pre-filled
 * via the email link (?code=...).
 */
export const InstitutionSignup: React.FC = () => {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [code, setCode] = useState('');
  const [preview, setPreview] = useState<ActivationCodePreview | null>(null);
  const [previewState, setPreviewState] = useState<'loading' | 'ok' | 'error'>('loading');
  const [previewError, setPreviewError] = useState<string>('');

  const [adminName, setAdminName] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<{ adminName?: string; password?: string }>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);

  // Resolve the activation code from the URL and fetch its preview.
  useEffect(() => {
    const c = searchParams.get('code') || '';
    setCode(c);

    if (!c) {
      setPreviewState('error');
      setPreviewError('No activation code found. Please use the link from your invitation email.');
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const data = await institutionService.previewActivationCode(c);
        if (cancelled) return;
        setPreview(data);
        setPreviewState('ok');
      } catch (err: any) {
        if (cancelled) return;
        const status = err?.response?.status;
        const detail = err?.response?.data?.detail;
        setPreviewError(
          detail ||
            (status === 404
              ? 'This activation code is invalid.'
              : status === 409
              ? 'This activation code has already been used.'
              : status === 410
              ? 'This activation code has expired.'
              : 'Could not verify this activation code.')
        );
        setPreviewState('error');
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [searchParams]);

  const validate = (): boolean => {
    const next: typeof errors = {};
    if (!adminName.trim()) next.adminName = 'Your name is required';
    if (!password) next.password = 'Password is required';
    else if (password.length < 8) next.password = 'Password must be at least 8 characters';
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!preview || !validate()) return;

    setIsSubmitting(true);
    setApiError(null);

    try {
      // Institution name / email / type come from the code (master admin entered
      // them); the backend also re-derives limits & plan from the code itself.
      const result = await institutionService.signup({
        name: preview.institution_name,
        institution_type: (prettyType(preview.institution_type).toLowerCase().replace(/\s+/g, '_') as any),
        admin_email: preview.institution_email,
        admin_password: password,
        admin_name: adminName.trim(),
        activation_code: code,
      });

      localStorage.setItem('institution_code', result.institution_code);
      localStorage.setItem('institution_id', result.institution_id);
      localStorage.setItem('institution_name', preview.institution_name);

      setShowSuccess(true);
      setTimeout(() => {
        router.push('/institution/dashboard');
      }, 2000);
    } catch (error: any) {
      setApiError(error.response?.data?.detail || 'Activation failed. Please try again.');
      setIsSubmitting(false);
    }
  };

  // ── Success animation ────────────────────────────────────────────────
  if (showSuccess) {
    return (
      <div className="flex min-h-[calc(100vh-64px)] items-center justify-center bg-slate-50 p-4">
        <div className="text-center">
          <div className="mx-auto mb-6 inline-flex h-24 w-24 animate-bounce items-center justify-center rounded-full bg-green-100">
            <svg className="h-12 w-12 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="mb-2 text-3xl font-bold text-slate-900">Account Activated!</h2>
          <p className="mb-4 text-slate-500">Redirecting to your dashboard...</p>
          <div className="flex justify-center space-x-1">
            <div className="h-2 w-2 animate-pulse rounded-full bg-[#4ECFBF]"></div>
            <div className="h-2 w-2 animate-pulse rounded-full bg-[#4ECFBF]" style={{ animationDelay: '0.2s' }}></div>
            <div className="h-2 w-2 animate-pulse rounded-full bg-[#4ECFBF]" style={{ animationDelay: '0.4s' }}></div>
          </div>
        </div>
      </div>
    );
  }

  // ── Loading the code preview ─────────────────────────────────────────
  if (previewState === 'loading') {
    return (
      <div className="flex min-h-[calc(100vh-64px)] items-center justify-center bg-slate-50 p-4">
        <div className="text-center">
          <div className="inline-block h-12 w-12 animate-spin rounded-full border-b-2 border-[#4ECFBF]"></div>
          <p className="mt-4 text-slate-500">Verifying your invitation...</p>
        </div>
      </div>
    );
  }

  // ── Invalid / expired / used / missing code ──────────────────────────
  if (previewState === 'error' || !preview) {
    return (
      <B2BAuthCard
        icon={
          <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        }
        title="Invitation Problem"
        subtitle={previewError}
      >
        <div className="space-y-4 text-center text-sm text-slate-500">
          <p>
            If you believe this is a mistake, contact your MyTaco AI representative for a new
            invitation link.
          </p>
          <p>
            Already activated your account?{' '}
            <Link href="/institution/login" className="font-medium text-[#3A9E92] hover:text-[#4ECFBF]">
              Log in here
            </Link>
          </p>
        </div>
      </B2BAuthCard>
    );
  }

  // ── Valid code → activation form (name + password only) ──────────────
  return (
    <B2BAuthCard
      icon={
        <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      }
      title="Activate Your School Account"
      subtitle="You've been invited — confirm your school and set a password to get started."
    >
      {/* Read-only institution summary (from the activation code) */}
      <div className="mb-5 rounded-xl border border-slate-200 bg-slate-50 p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-slate-900">{preview.institution_name}</p>
            <p className="truncate text-xs text-slate-500">{preview.institution_email}</p>
          </div>
          <span className="shrink-0 rounded-full bg-[#4ECFBF]/10 px-2.5 py-1 text-xs font-semibold text-[#3A9E92]">
            {prettyType(preview.institution_type)}
          </span>
        </div>
        <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-slate-500">
          <span className="rounded-md bg-white px-2 py-1 ring-1 ring-slate-200">
            Plan: <span className="font-medium capitalize text-slate-700">{preview.subscription_plan}</span>
            {preview.is_trial ? ' (trial)' : ''}
          </span>
          <span className="rounded-md bg-white px-2 py-1 ring-1 ring-slate-200">
            Up to {preview.max_tutors} tutors
          </span>
          <span className="rounded-md bg-white px-2 py-1 ring-1 ring-slate-200">
            Up to {preview.max_learners} learners
          </span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <B2BField id="admin_name" label="Your Name *" error={errors.adminName}>
          <input
            id="admin_name"
            type="text"
            value={adminName}
            onChange={(e) => {
              setAdminName(e.target.value);
              if (errors.adminName) setErrors((p) => ({ ...p, adminName: undefined }));
            }}
            placeholder="e.g., John Doe"
            className={`${b2bInputClass} ${errors.adminName ? 'border-red-500' : ''}`}
            autoComplete="name"
          />
        </B2BField>

        <B2BField id="admin_password" label="Set Password *" error={errors.password}>
          <input
            id="admin_password"
            type="password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              if (errors.password) setErrors((p) => ({ ...p, password: undefined }));
            }}
            placeholder="At least 8 characters"
            className={`${b2bInputClass} ${errors.password ? 'border-red-500' : ''}`}
            autoComplete="new-password"
          />
        </B2BField>

        {apiError && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3">
            <p className="text-sm text-red-600">{apiError}</p>
          </div>
        )}

        <button type="submit" disabled={isSubmitting} className={b2bPrimaryButtonClass}>
          {isSubmitting ? 'Activating...' : 'Activate Account'}
        </button>

        <p className="text-center text-sm text-slate-500">
          Already activated?{' '}
          <Link href="/institution/login" className="font-medium text-[#3A9E92] hover:text-[#4ECFBF]">
            Log in here
          </Link>
        </p>
      </form>
    </B2BAuthCard>
  );
};
