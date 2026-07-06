'use client';

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';

interface B2BLogoutButtonProps {
  /** Portal type — drives which tokens are cleared and where we redirect. */
  portal: 'institution' | 'tutor';
  /** Account display name shown in the dropdown header. */
  name?: string;
  /** Account email shown in the dropdown header (optional). */
  email?: string;
}

const INSTITUTION_KEYS = ['institution_token', 'institution_id', 'institution_name', 'institution_code'];
const TUTOR_KEYS = ['tutorToken', 'tutorId', 'tutorName', 'tutorEmail', 'institutionId'];

/**
 * B2BLogoutButton — avatar dropdown + Sign-Out confirmation modal for the
 * institution & tutor portals. Mirrors the master-admin panel's UX: an avatar
 * button opens a dropdown (name + email + Sign Out); Sign Out opens a centered
 * confirmation modal.
 *
 * On confirm it: (1) best-effort blocklists the JWT server-side, (2) wipes ALL
 * client auth state (localStorage keys, sessionStorage, cookies), and (3)
 * hard-replaces to login with a Back-button guard so the unauthenticated
 * dashboard can't be reached via history navigation.
 */
export function B2BLogoutButton({ portal, name, email }: B2BLogoutButtonProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [mounted, setMounted] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => setMounted(true), []);

  // Close dropdown on outside click.
  useEffect(() => {
    if (!dropdownOpen) return;
    const onClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, [dropdownOpen]);

  const doLogout = useCallback(async () => {
    setBusy(true);

    const loginPath = portal === 'institution' ? '/institution/login' : '/tutor/login';
    const tokenKey = portal === 'institution' ? 'institution_token' : 'tutorToken';
    const logoutUrl = portal === 'institution'
      ? '/api/institution/dashboard/logout'
      : '/api/tutor/logout';

    // 1) Best-effort server-side token blocklist.
    try {
      const token = localStorage.getItem(tokenKey);
      if (token) {
        await fetch(logoutUrl, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        }).catch(() => {});
      }
    } catch {
      /* non-blocking */
    }

    // 2) Wipe ALL client auth state.
    try {
      [...INSTITUTION_KEYS, ...TUTOR_KEYS].forEach((k) => localStorage.removeItem(k));
      sessionStorage.clear();
      document.cookie.split(';').forEach((c) => {
        const cname = c.split('=')[0].trim();
        if (cname) {
          document.cookie = `${cname}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
        }
      });
    } catch {
      /* ignore */
    }

    // 3) Redirect + neutralise the Back button.
    try {
      window.history.replaceState(null, '', loginPath);
      window.addEventListener('popstate', () => window.history.pushState(null, '', loginPath));
    } catch {
      /* ignore */
    }
    window.location.replace(loginPath);
  }, [portal]);

  const initial = (name || 'A').charAt(0).toUpperCase();

  return (
    <>
      {/* Avatar + dropdown */}
      <div className="relative" ref={dropdownRef}>
        <button
          type="button"
          onClick={() => setDropdownOpen((v) => !v)}
          className="flex h-9 w-9 items-center justify-center rounded-full bg-[#4ECFBF] text-sm font-bold text-white transition-colors hover:bg-[#3ab5a6] focus:outline-none focus:ring-2 focus:ring-[#4ECFBF]/40"
          aria-label="Account menu"
        >
          {initial}
        </button>

        {dropdownOpen && (
          <div className="absolute right-0 z-50 mt-2 w-56 overflow-hidden rounded-xl border border-gray-100 bg-white shadow-lg">
            <div className="border-b border-gray-100 px-4 py-3">
              <p className="truncate text-sm font-semibold text-gray-900">{name || 'Account'}</p>
              {email ? <p className="truncate text-xs text-gray-500">{email}</p> : null}
            </div>
            <div className="p-2">
              <button
                type="button"
                onClick={() => { setDropdownOpen(false); setConfirmOpen(true); }}
                className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-red-600 transition-colors hover:bg-red-50"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                Sign Out
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Confirmation modal — portaled to <body> so it's centered on the full
          viewport (not clipped/offset by the sticky header). */}
      {confirmOpen && mounted && createPortal(
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-4"
          onClick={() => !busy && setConfirmOpen(false)}
        >
          <div
            className="w-full max-w-sm overflow-hidden rounded-2xl bg-white shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
                <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </div>
              <h3 className="text-center text-lg font-bold text-gray-900">Sign Out?</h3>
              <p className="mt-1 text-center text-sm text-gray-500">You&apos;ll be redirected to the login page.</p>
            </div>
            <div className="flex gap-3 px-6 pb-6">
              <button
                type="button"
                onClick={() => setConfirmOpen(false)}
                disabled={busy}
                className="flex-1 rounded-xl border border-gray-200 px-4 py-2.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:opacity-60"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={doLogout}
                disabled={busy}
                className="flex-1 rounded-xl bg-red-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {busy ? 'Signing out…' : 'Sign Out'}
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
}
