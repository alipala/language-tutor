'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { B2BAuthCard, B2BField, b2bInputClass, b2bPrimaryButtonClass } from '@/src/components/b2b/B2BAuthCard';

export const InstitutionForgotPassword: React.FC = () => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const validateEmail = (): boolean => {
    if (!email.trim()) {
      setError('Email is required');
      return false;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Invalid email format');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (!validateEmail()) return;

    setIsSubmitting(true);

    try {
      // TODO: Implement actual password reset API call
      // const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
      // await fetch(`${apiUrl}/institution/forgot-password`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ admin_email: email })
      // });
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      setIsSuccess(true);
    } catch (error: any) {
      setError('Failed to send reset email. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSuccess) {
    return (
      <B2BAuthCard
        icon={
          <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        }
        title="Check Your Email"
        subtitle={`We've sent password reset instructions to ${email}`}
      >
        <div className="space-y-6 text-center">
          <p className="text-sm text-slate-500">
            Didn't receive the email? Check your spam folder or try again.
          </p>
          <Link
            href="/institution/login"
            className="inline-block rounded-lg bg-[#4ECFBF] px-6 py-3 font-medium text-white transition-colors hover:bg-[#3A9E92]"
          >
            Back to Login
          </Link>
        </div>
      </B2BAuthCard>
    );
  }

  return (
    <B2BAuthCard
      icon={
        <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
        </svg>
      }
      title="Reset Password"
      subtitle="Enter your email and we'll send you instructions to reset your password"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <B2BField id="email" label="Admin Email" error={error}>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              setError('');
            }}
            placeholder="admin@institution.edu"
            className={`${b2bInputClass} ${error ? 'border-red-500' : ''}`}
            autoComplete="email"
          />
        </B2BField>

        <button type="submit" disabled={isSubmitting} className={b2bPrimaryButtonClass}>
          {isSubmitting ? 'Sending...' : 'Send Reset Instructions'}
        </button>

        <div className="text-center text-sm">
          <Link href="/institution/login" className="font-medium text-[#3A9E92] hover:text-[#4ECFBF]">
            ← Back to Login
          </Link>
        </div>
      </form>
    </B2BAuthCard>
  );
};
