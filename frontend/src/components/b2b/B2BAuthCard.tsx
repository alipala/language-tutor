'use client';

import React from 'react';

interface B2BAuthCardProps {
  /** Optional icon rendered in the teal circle above the title. */
  icon?: React.ReactNode;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}

/**
 * B2BAuthCard — shared shell for all B2B auth screens (institution + tutor
 * login/signup/forgot-password). Guarantees consistent card, spacing, icon
 * treatment and the teal brand accent across every portal form.
 */
export function B2BAuthCard({ icon, title, subtitle, children }: B2BAuthCardProps) {
  return (
    <div className="flex min-h-[calc(100vh-64px)] items-center justify-center bg-slate-50 px-4 py-10">
      <div className="w-full max-w-md">
        <div className="rounded-2xl border border-slate-200 bg-white p-8 text-slate-900 shadow-sm">
          <div className="mb-6 text-center">
            {icon ? (
              <div className="mx-auto mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-[#4ECFBF] to-[#3A9E92] text-white">
                {icon}
              </div>
            ) : null}
            <h1 className="mb-1.5 text-2xl font-bold text-slate-900">{title}</h1>
            {subtitle ? <p className="text-sm text-slate-500">{subtitle}</p> : null}
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}

/** Shared teal-accent input for B2B forms. */
export function B2BField({
  id,
  label,
  error,
  children,
}: {
  id: string;
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-slate-700">
        {label}
      </label>
      {children}
      {error ? <p className="mt-1 text-xs text-red-500">{error}</p> : null}
    </div>
  );
}

/** Tailwind class string for consistent B2B text inputs (teal focus ring). */
export const b2bInputClass =
  'w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-slate-900 placeholder:text-slate-400 transition focus:border-transparent focus:outline-none focus:ring-2 focus:ring-[#4ECFBF]';

/** Tailwind class string for the primary teal B2B submit button. */
export const b2bPrimaryButtonClass =
  'w-full rounded-lg bg-[#4ECFBF] px-4 py-3 font-semibold text-white transition-colors hover:bg-[#3A9E92] disabled:cursor-not-allowed disabled:opacity-50';
