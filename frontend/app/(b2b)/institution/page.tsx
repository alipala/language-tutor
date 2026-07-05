'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

/**
 * Bare /institution index — auth-aware redirect.
 * Signed-in institution admins go to their dashboard; everyone else to login.
 * (Prevents a 404 when someone hits the base path directly.)
 */
export default function InstitutionIndexPage() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('institution_token');
    const id = localStorage.getItem('institution_id');
    router.replace(token && id ? '/institution/dashboard' : '/institution/login');
  }, [router]);

  return (
    <div className="flex min-h-[calc(100vh-64px)] items-center justify-center bg-slate-50">
      <div className="h-10 w-10 animate-spin rounded-full border-b-2 border-[#4ECFBF]" />
    </div>
  );
}
