'use client';

import Link from 'next/link';
import NavBar from '@/components/nav-bar';

export default function PromoCodePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-blue-50">
      <NavBar />

      <main className="pt-16 pb-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          {/* Hero Section */}
          <div className="text-center mb-10 sm:mb-12">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 bg-teal-100 text-teal-700 px-4 py-2 rounded-full text-sm font-medium mb-4 sm:mb-6">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z" />
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clipRule="evenodd" />
              </svg>
              <span>Exclusive Discount</span>
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-3 sm:mb-4 leading-tight">
              Apply Your<br className="sm:hidden" /> Promo Code
            </h1>
            <p className="text-base sm:text-lg text-gray-600 max-w-2xl mx-auto">
              Get started in 5 simple steps
            </p>
          </div>

          {/* Steps Card */}
          <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden mb-8">
            {/* Steps Container */}
            <div className="p-6 sm:p-8 lg:p-10">
              <div className="space-y-6">
                {/* Step 1 */}
                <div className="flex gap-4 sm:gap-5 group">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-teal-400 to-teal-600 text-white rounded-xl flex items-center justify-center font-bold text-lg shadow-lg group-hover:scale-110 transition-transform">
                      1
                    </div>
                  </div>
                  <div className="flex-1 pt-1">
                    <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-2">Sign In</h3>
                    <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                      Log in with your account or create a new one
                    </p>
                  </div>
                </div>

                {/* Connector */}
                <div className="ml-5 sm:ml-6 h-6 w-0.5 bg-gradient-to-b from-teal-200 to-teal-100"></div>

                {/* Step 2 */}
                <div className="flex gap-4 sm:gap-5 group">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-teal-400 to-teal-600 text-white rounded-xl flex items-center justify-center font-bold text-lg shadow-lg group-hover:scale-110 transition-transform">
                      2
                    </div>
                  </div>
                  <div className="flex-1 pt-1">
                    <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-2">Choose Your Plan</h3>
                    <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                      Navigate to pricing and select monthly or annual billing
                    </p>
                  </div>
                </div>

                {/* Connector */}
                <div className="ml-5 sm:ml-6 h-6 w-0.5 bg-gradient-to-b from-teal-200 to-teal-100"></div>

                {/* Step 3 */}
                <div className="flex gap-4 sm:gap-5 group">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-teal-400 to-teal-600 text-white rounded-xl flex items-center justify-center font-bold text-lg shadow-lg group-hover:scale-110 transition-transform">
                      3
                    </div>
                  </div>
                  <div className="flex-1 pt-1">
                    <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-2">Enter Promo Code</h3>
                    <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                      Click "Add promotion code" and enter your discount code
                    </p>
                  </div>
                </div>

                {/* Connector */}
                <div className="ml-5 sm:ml-6 h-6 w-0.5 bg-gradient-to-b from-teal-200 to-teal-100"></div>

                {/* Step 4 */}
                <div className="flex gap-4 sm:gap-5 group">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-teal-400 to-teal-600 text-white rounded-xl flex items-center justify-center font-bold text-lg shadow-lg group-hover:scale-110 transition-transform">
                      4
                    </div>
                  </div>
                  <div className="flex-1 pt-1">
                    <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-2">Complete Payment</h3>
                    <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                      Your discount will be applied instantly at checkout
                    </p>
                  </div>
                </div>

                {/* Connector */}
                <div className="ml-5 sm:ml-6 h-6 w-0.5 bg-gradient-to-b from-teal-200 to-teal-100"></div>

                {/* Step 5 */}
                <div className="flex gap-4 sm:gap-5 group">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-teal-400 to-teal-600 text-white rounded-xl flex items-center justify-center font-bold text-lg shadow-lg group-hover:scale-110 transition-transform">
                      5
                    </div>
                  </div>
                  <div className="flex-1 pt-1">
                    <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-2">Return to App</h3>
                    <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                      Your subscription syncs automatically across all devices
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Info Banner */}
            <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-t border-amber-100 px-6 sm:px-8 lg:px-10 py-5">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-0.5">
                  <svg className="w-5 h-5 sm:w-6 sm:h-6 text-amber-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="flex-1">
                  <p className="text-sm sm:text-base text-amber-900 leading-relaxed">
                    <span className="font-semibold">Important:</span> Promo codes can only be applied on the website, not in mobile app stores.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* CTA Section */}
          <div className="text-center space-y-4">
            <Link
              href="https://mytacoai.com/auth/login"
              className="inline-flex items-center justify-center gap-2 bg-gradient-to-r from-teal-500 to-teal-600 text-white px-8 py-4 rounded-xl font-bold text-base sm:text-lg hover:from-teal-600 hover:to-teal-700 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 w-full sm:w-auto"
            >
              Get Started Now
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>

            <p className="text-sm sm:text-base text-gray-500">
              Need help? <a href="mailto:support@mytacoai.com" className="text-teal-600 hover:text-teal-700 font-medium hover:underline">Contact Support</a>
            </p>
          </div>

          {/* Trust Indicators */}
          <div className="mt-12 pt-8 border-t border-gray-200">
            <div className="grid grid-cols-3 gap-4 sm:gap-8 text-center">
              <div>
                <div className="text-2xl sm:text-3xl font-bold text-teal-600 mb-1">7 days</div>
                <div className="text-xs sm:text-sm text-gray-600">Free Trial</div>
              </div>
              <div>
                <div className="text-2xl sm:text-3xl font-bold text-teal-600 mb-1">Secure</div>
                <div className="text-xs sm:text-sm text-gray-600">Payment</div>
              </div>
              <div>
                <div className="text-2xl sm:text-3xl font-bold text-teal-600 mb-1">Cancel</div>
                <div className="text-xs sm:text-sm text-gray-600">Anytime</div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
