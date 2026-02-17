'use client';

import Link from 'next/link';
import NavBar from '@/components/nav-bar';

export default function PromoCodePage() {
  const steps = [
    {
      number: 1,
      title: 'Sign In',
      description: 'Login or create account',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      )
    },
    {
      number: 2,
      title: 'Choose Plan',
      description: 'Select monthly or annual',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    },
    {
      number: 3,
      title: 'Enter Code',
      description: 'Apply your promo code',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
        </svg>
      )
    },
    {
      number: 4,
      title: 'Pay',
      description: 'Complete checkout',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
        </svg>
      )
    },
    {
      number: 5,
      title: 'Done!',
      description: 'Return to app',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-blue-50">
      <NavBar />

      <main className="pt-20 pb-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {/* Compact Hero */}
          <div className="text-center mb-8 lg:mb-12">
            <div className="inline-flex items-center gap-2 bg-teal-100 text-teal-700 px-4 py-2 rounded-full text-sm font-semibold mb-4">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z" />
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clipRule="evenodd" />
              </svg>
              Exclusive Discount
            </div>
            <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-3">
              Apply Your Promo Code
            </h1>
            <p className="text-lg text-gray-600">
              5 simple steps to activate your discount
            </p>
          </div>

          {/* Horizontal Timeline (Desktop) / Vertical (Mobile) */}
          <div className="mb-8 lg:mb-10">
            {/* Desktop: Horizontal */}
            <div className="hidden lg:block">
              <div className="relative">
                {/* Progress Line */}
                <div className="absolute top-12 left-0 right-0 h-1 bg-gradient-to-r from-teal-200 via-teal-300 to-teal-400 rounded-full mx-20"></div>

                {/* Steps */}
                <div className="relative grid grid-cols-5 gap-4">
                  {steps.map((step, index) => (
                    <div key={step.number} className="flex flex-col items-center group">
                      {/* Circle */}
                      <div className="relative z-10 w-24 h-24 bg-gradient-to-br from-teal-400 to-teal-600 rounded-2xl shadow-lg flex items-center justify-center transform group-hover:scale-110 transition-all duration-300 group-hover:shadow-2xl">
                        <div className="text-center text-white">
                          <div className="mb-1">{step.icon}</div>
                          <div className="text-xs font-bold">{step.number}</div>
                        </div>
                      </div>

                      {/* Content */}
                      <div className="mt-4 text-center">
                        <h3 className="font-bold text-gray-900 text-lg mb-1">{step.title}</h3>
                        <p className="text-sm text-gray-600">{step.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Mobile: Vertical */}
            <div className="lg:hidden bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
              <div className="space-y-4">
                {steps.map((step, index) => (
                  <div key={step.number}>
                    <div className="flex gap-4 items-start">
                      <div className="flex-shrink-0 w-14 h-14 bg-gradient-to-br from-teal-400 to-teal-600 rounded-xl shadow-lg flex items-center justify-center text-white">
                        <div className="text-center">
                          <div className="mb-0.5">{step.icon}</div>
                          <div className="text-xs font-bold">{step.number}</div>
                        </div>
                      </div>
                      <div className="flex-1 pt-2">
                        <h3 className="font-bold text-gray-900 text-lg mb-1">{step.title}</h3>
                        <p className="text-sm text-gray-600">{step.description}</p>
                      </div>
                    </div>
                    {index < steps.length - 1 && (
                      <div className="ml-7 h-6 w-0.5 bg-gradient-to-b from-teal-300 to-teal-200 my-2"></div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Info Banner */}
          <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-xl px-6 py-4 mb-8 max-w-3xl mx-auto">
            <div className="flex items-start gap-3">
              <svg className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <p className="text-sm text-amber-900">
                <span className="font-semibold">Important:</span> Promo codes can only be applied on the website, not in mobile app stores.
              </p>
            </div>
          </div>

          {/* CTA Section */}
          <div className="text-center space-y-4 mb-8">
            <Link
              href="https://mytacoai.com/auth/login"
              className="inline-flex items-center justify-center gap-2 bg-gradient-to-r from-teal-500 to-teal-600 text-white px-10 py-4 rounded-xl font-bold text-lg hover:from-teal-600 hover:to-teal-700 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              Get Started Now
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
            <p className="text-sm text-gray-500">
              Need help? <a href="mailto:support@mytacoai.com" className="text-teal-600 hover:text-teal-700 font-medium hover:underline">Contact Support</a>
            </p>
          </div>

          {/* Trust Indicators */}
          <div className="max-w-2xl mx-auto pt-6 border-t border-gray-200">
            <div className="grid grid-cols-3 gap-6 text-center">
              <div className="group">
                <div className="text-3xl font-bold bg-gradient-to-r from-teal-500 to-teal-600 bg-clip-text text-transparent mb-1 group-hover:scale-110 transition-transform">7 days</div>
                <div className="text-sm text-gray-600">Free Trial</div>
              </div>
              <div className="group">
                <div className="text-3xl font-bold bg-gradient-to-r from-teal-500 to-teal-600 bg-clip-text text-transparent mb-1 group-hover:scale-110 transition-transform">Secure</div>
                <div className="text-sm text-gray-600">Payment</div>
              </div>
              <div className="group">
                <div className="text-3xl font-bold bg-gradient-to-r from-teal-500 to-teal-600 bg-clip-text text-transparent mb-1 group-hover:scale-110 transition-transform">Cancel</div>
                <div className="text-sm text-gray-600">Anytime</div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
