'use client';

import { ReactNode } from 'react';
import { AuthProvider } from '@/lib/auth';
import { NotificationProvider } from '@/components/ui/notification';

export default function AuthProviderWrapper({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <NotificationProvider>
        {children}
      </NotificationProvider>
    </AuthProvider>
  );
}
