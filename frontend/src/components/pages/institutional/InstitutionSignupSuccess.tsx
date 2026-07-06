'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export const InstitutionSignupSuccess: React.FC = () => {
  const router = useRouter();
  const [institutionCode, setInstitutionCode] = useState<string>('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const code = localStorage.getItem('institution_code');
    const id = localStorage.getItem('institution_id');
    if (!code || !id) {
      router.push('/institution/signup');
      return;
    }
    setInstitutionCode(code);
  }, [router]);

  const copyToClipboard = () => {
    navigator.clipboard?.writeText(institutionCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const steps = [
    { n: 1, title: 'Invite Tutors', body: 'Add your language tutors to the platform' },
    { n: 2, title: 'Enroll Learners', body: 'Students can self-enroll using your institution code' },
    { n: 3, title: 'Start Learning', body: 'Monitor progress and manage your language programs' },
  ];

  return (
    <div className="min-h-[calc(100vh-64px)] bg-slate-50 px-4 py-8 sm:py-12">
      <div className="mx-auto w-full max-w-2xl">
        {/* Success icon */}
        <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-green-100 sm:h-20 sm:w-20">
          <svg className="h-8 w-8 text-green-600 sm:h-10 sm:w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>

        <h1 className="text-center text-2xl font-bold text-slate-900 sm:text-3xl">
          Institution Account Created!
        </h1>
        <p className="mt-2 text-center text-sm text-slate-500 sm:text-base">
          Your institution has been successfully registered with MyTaco AI.
        </p>

        {/* Institution code */}
        <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
          <h2 className="text-sm font-semibold text-slate-700">Your Institution Code</h2>
          <div className="mt-3 flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 p-3 sm:p-4">
            <code className="min-w-0 flex-1 truncate font-mono text-lg font-bold tracking-wide text-slate-900 sm:text-xl">
              {institutionCode || '—'}
            </code>
            <button
              onClick={copyToClipboard}
              title="Copy to clipboard"
              className="shrink-0 rounded-lg bg-[#4ECFBF]/10 p-2 text-[#3A9E92] transition-colors hover:bg-[#4ECFBF]/20"
            >
              {copied ? (
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                </svg>
              )}
            </button>
          </div>
          <p className="mt-2 text-xs text-slate-500">
            Share this code with tutors and learners to join your institution
          </p>
        </div>

        {/* Next steps */}
        <div className="mt-6">
          <h2 className="text-sm font-semibold text-slate-700">Next Steps</h2>
          <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
            {steps.map((s) => (
              <div key={s.n} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <div className="mb-2 flex h-8 w-8 items-center justify-center rounded-full bg-[#4ECFBF] text-sm font-bold text-white">
                  {s.n}
                </div>
                <h3 className="text-sm font-semibold text-slate-900">{s.title}</h3>
                <p className="mt-1 text-xs text-slate-500">{s.body}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <button
            onClick={() => router.push('/institution/login')}
            className="w-full rounded-lg bg-[#4ECFBF] px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#3A9E92] sm:flex-1"
          >
            Go to Dashboard
          </button>
          <button
            onClick={() => window.print()}
            className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 sm:flex-1"
          >
            Print Details
          </button>
        </div>

        <p className="mt-6 text-center text-xs text-slate-500">
          Need help getting started?{' '}
          <a href="/help" className="font-medium text-[#3A9E92] hover:text-[#4ECFBF]">
            Visit our Help Center
          </a>
        </p>
      </div>
    </div>
  );
};
