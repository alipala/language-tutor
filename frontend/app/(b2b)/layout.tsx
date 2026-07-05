'use client';

import { usePathname } from 'next/navigation';
import { B2BBrandBar } from '@/src/components/b2b/B2BBrandBar';

/**
 * B2B route-group layout.
 *
 * Wraps every institution / tutor / admin page in a light, standalone shell
 * that is fully isolated from the consumer landing chrome. The landing NavBar
 * and Footer (rendered by the root layout) are suppressed on these routes via
 * a pathname guard in the root layout, so nothing here inherits the marketing
 * navigation or the dark background.
 *
 * Chrome selection:
 *  - Auth screens (login / signup / signup-success / forgot-password) get a
 *    minimal, NON-clickable brand bar (B2BBrandBar).
 *  - Signed-in dashboards render their own B2BAppBar (with logout) from inside
 *    the page, because logout + account name are portal-specific.
 */
export default function B2BLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() || '';

  // Auth surfaces where we want only the minimal brand bar.
  const isAuthScreen =
    pathname.endsWith('/login') ||
    pathname.endsWith('/signup') ||
    pathname.endsWith('/signup-success') ||
    pathname.endsWith('/forgot-password');

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {isAuthScreen ? <B2BBrandBar /> : null}
      {children}
    </div>
  );
}
