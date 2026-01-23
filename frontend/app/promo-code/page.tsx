'use client';

import Link from 'next/link';
import NavBar from '@/components/nav-bar';

export default function PromoCodePage() {
  return (
    <div className="min-h-screen bg-white">
      <NavBar />

      <main className="pt-20 pb-12 px-4">
        <div className="max-w-2xl mx-auto">
          {/* Compact Header */}
          <div className="text-center mb-8">
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
              How to Apply Your Promo Code
            </h1>
            <p className="text-gray-600">5 simple steps to activate your discount</p>
          </div>

          {/* Compact Steps */}
          <div className="bg-gray-50 rounded-xl p-6 mb-6">
            <div className="space-y-4">
              {/* Step 1 */}
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 bg-[#4ECFBF] text-white rounded-full flex items-center justify-center text-sm font-bold">
                  1
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 mb-1">Sign In</h3>
                  <p className="text-sm text-gray-600">Log in with your account or create a new one</p>
                </div>
              </div>

              {/* Step 2 */}
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 bg-[#4ECFBF] text-white rounded-full flex items-center justify-center text-sm font-bold">
                  2
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 mb-1">Choose Your Plan</h3>
                  <p className="text-sm text-gray-600">Navigate to pricing and select monthly or annual billing</p>
                </div>
              </div>

              {/* Step 3 */}
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 bg-[#4ECFBF] text-white rounded-full flex items-center justify-center text-sm font-bold">
                  3
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 mb-1">Enter Promo Code</h3>
                  <p className="text-sm text-gray-600">On the checkout page, click "Add promotion code" and enter your code</p>
                </div>
              </div>

              {/* Step 4 */}
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 bg-[#4ECFBF] text-white rounded-full flex items-center justify-center text-sm font-bold">
                  4
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 mb-1">Complete Payment</h3>
                  <p className="text-sm text-gray-600">Your discount will be applied instantly before checkout</p>
                </div>
              </div>

              {/* Step 5 */}
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 bg-[#4ECFBF] text-white rounded-full flex items-center justify-center text-sm font-bold">
                  5
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 mb-1">Return to App</h3>
                  <p className="text-sm text-gray-600">Your subscription syncs automatically across all devices</p>
                </div>
              </div>
            </div>

            {/* Info Box */}
            <div className="mt-6 p-4 bg-teal-50 border border-teal-200 rounded-lg">
              <p className="text-sm text-teal-900">
                <span className="font-semibold">💡 Note:</span> Promo codes can only be applied on the website, not in the mobile app stores.
              </p>
            </div>
          </div>

          {/* CTA Button */}
          <div className="text-center">
            <Link
              href="https://mytacoai.com/auth/login"
              className="inline-flex items-center gap-2 bg-[#4ECFBF] text-white px-6 py-3 rounded-lg font-semibold hover:bg-[#3DBFAF] transition-colors"
            >
              Sign In to Get Started
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
          </div>

          {/* Footer */}
          <div className="mt-8 text-center text-sm text-gray-500">
            Need help? <a href="mailto:support@mytacoai.com" className="text-[#4ECFBF] hover:underline">Contact Support</a>
          </div>
        </div>
      </main>
    </div>
  );
}
