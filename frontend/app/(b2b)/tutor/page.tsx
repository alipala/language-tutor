'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

/**
 * Bare /tutor index — auth-aware redirect.
 * Signed-in tutors go to their dashboard (id from localStorage); everyone else
 * to login. Prevents a 404 on the base path.
 */
export default function TutorIndexPage() {
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
