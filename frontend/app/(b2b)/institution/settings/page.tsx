'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { SettingsTab } from '@/src/components/pages/institutional/InstitutionDashboardComplete';

export default function InstitutionSettingsPage() {
  const router = useRouter();
  const [institutionId, setInstitutionId] = useState('');
  const [token, setToken]                 = useState('');
  const [ready, setReady]                 = useState(false);
  const [notification, setNotification]   = useState<{
    show: boolean; type: 'success' | 'error' | 'info'; title: string; message: string;
  }>({ show: false, type: 'info', title: '', message: '' });

  useEffect(() => {
    const t  = localStorage.getItem('institution_token');
    const id = localStorage.getItem('institution_id');
    if (!t || !id) { router.push('/institution/login'); return; }
    setToken(t);
    setInstitutionId(id);
    setReady(true);
  }, [router]);

  if (!ready) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="w-10 h-10 border-4 border-brand/30 border-t-[#4ECFBF] rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 pt-8 sm:pt-24 pb-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Page header */}
        <div className="mb-6 sm:mb-8">
          <button
            onClick={() => router.push('/institution/dashboard')}
            className="text-sm text-brand hover:text-[#3a9e92] font-medium mb-4 inline-flex items-center gap-1"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-500 mt-1 text-sm">Manage your institution profile and admin account.</p>
        </div>

        <SettingsTab
          institutionId={institutionId}
          token={token}
          onNotify={(type, title, message) =>
            setNotification({ show: true, type, title, message })
          }
        />
      </div>

      {/* Notification modal */}
      {notification.show && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4">
            <div className={`p-6 rounded-t-2xl ${
              notification.type === 'success' ? 'bg-gradient-to-r from-green-50 to-emerald-50' :
              notification.type === 'error'   ? 'bg-gradient-to-r from-red-50 to-rose-50' :
                                                'bg-gradient-to-r from-blue-50 to-cyan-50'
            }`}>
              <div className="flex items-center gap-3 sm:gap-4">
                <div className={`w-10 h-10 sm:w-12 sm:h-12 shrink-0 rounded-full flex items-center justify-center ${
                  notification.type === 'success' ? 'bg-green-100' :
                  notification.type === 'error'   ? 'bg-red-100' : 'bg-blue-100'
                }`}>
                  {notification.type === 'success' && (
                    <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                  {notification.type === 'error' && (
                    <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  )}
                </div>
                <div className="min-w-0">
                  <h3 className={`font-bold text-base sm:text-lg ${
                    notification.type === 'success' ? 'text-green-900' :
                    notification.type === 'error'   ? 'text-red-900' : 'text-blue-900'
                  }`}>{notification.title}</h3>
                  <p className="text-sm text-gray-600 mt-1 break-words">{notification.message}</p>
                </div>
              </div>
            </div>
            <div className="p-4">
              <button
                onClick={() => setNotification(n => ({ ...n, show: false }))}
                className="w-full py-3 bg-gradient-to-r from-brand to-[#3a9e92] text-white rounded-xl font-medium hover:shadow-lg transition-all"
              >
                Got it
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
