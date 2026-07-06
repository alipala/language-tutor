'use client';

import { usePathname } from 'next/navigation';

/**
 * LandingChromeGuard — hides the consumer landing chrome (NavBar / Footer)
 * on the standalone B2B portals.
 *
 * The root layout renders the marketing NavBar + Footer globally. On the B2B
 * route group (institution / tutor / admin) we want a fully isolated shell, so
 * this guard returns null for those path prefixes and renders its children
 * (the landing chrome) everywhere else.
 */
const B2B_PREFIXES = ['/institution', '/tutor', '/admin'];

export default function LandingChromeGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() || '';
  const isB2B = B2B_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`));

  if (isB2B) return null;
  return <>{children}</>;
}
