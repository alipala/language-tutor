'use client';

import { usePathname } from 'next/navigation';

/**
 * RootBackground — the app-wide background wrapper.
 *
 * The consumer app uses a dark canvas (#0A0A0F). The standalone B2B portals
 * (institution / tutor / admin) use their own light shell, so on those routes
 * we drop the dark background and let the B2B layout paint bg-slate-50 instead.
 */
const B2B_PREFIXES = ['/institution', '/tutor', '/admin'];

export default function RootBackground({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() || '';
  const isB2B = B2B_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`));

  return (
    <div
      className="app-background min-h-screen w-full"
      style={isB2B ? undefined : { backgroundColor: '#0A0A0F' }}
    >
      {children}
    </div>
  );
}
