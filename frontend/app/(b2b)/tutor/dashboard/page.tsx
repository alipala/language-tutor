'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

/**
 * Bare /tutor/dashboard (no tutorId) — resolve the id from localStorage and
 * redirect to the real dashboard, or to login if not signed in.
 * Prevents a 404 when someone drops the id from the URL.
 */
export default function TutorDashboardIndexPage() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('tutorToken');
    const id = localStorage.getItem('tutorId');
    router.replace(token && id ? `/tutor/dashboard/${id}` : '/tutor/login');
  }, [router]);

  return (
    <div className="flex min-h-[calc(100vh-64px)] items-center justify-center bg-slate-50">
      <div className="h-10 w-10 animate-spin rounded-full border-b-2 border-[#4ECFBF]" />
    </div>
  );
}
