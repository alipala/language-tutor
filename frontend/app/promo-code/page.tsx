'use client';

import { useRouter } from 'next/navigation';
import NavBar from '@/components/nav-bar';
import { motion } from 'framer-motion';
import { useAuth } from '@/lib/auth';

export default function PromoCodePage() {
  const router = useRouter();
  const { user } = useAuth();

  const handleGetStarted = () => {
    if (user) {
      // User is already logged in, go to pricing
      router.push('/#pricing');
    } else {
      // User needs to log in first
      router.push('/auth/signin?redirect=/#pricing');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-teal-50">
      <NavBar />

      <main className="pt-24 pb-16 px-4">
        <div className="max-w-3xl mx-auto">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center mb-12"
          >
            <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-[#4ECFBF] to-teal-600 rounded-2xl mb-6 shadow-lg">
              <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
              </svg>
            </div>

            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Apply Your Promo Code
            </h1>
            <p className="text-xl text-gray-600">
              Follow these simple steps to activate your discount
            </p>
          </motion.div>

          {/* Steps */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="bg-white rounded-3xl shadow-xl p-8 md:p-12 mb-8"
          >
            <div className="space-y-8">
              {/* Step 1 */}
              <div className="flex gap-6">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center w-12 h-12 bg-[#4ECFBF] text-white rounded-full text-xl font-bold shadow-lg">
                    1
                  </div>
                </div>
                <div className="flex-1 pt-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    Sign In or Create Account
                  </h3>
                  <p className="text-gray-600 leading-relaxed">
                    If you're already a user, sign in with your existing account (email or Google).
                    New here? Create an account using the same email you'll use for your subscription.
                  </p>
                </div>
              </div>

              <div className="border-l-2 border-gray-200 ml-6 h-6"></div>

              {/* Step 2 */}
              <div className="flex gap-6">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center w-12 h-12 bg-[#4ECFBF] text-white rounded-full text-xl font-bold shadow-lg">
                    2
                  </div>
                </div>
                <div className="flex-1 pt-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    Go to Pricing
                  </h3>
                  <p className="text-gray-600 leading-relaxed">
                    Click the "Upgrade" button or navigate to the pricing section to view available plans.
                  </p>
                </div>
              </div>

              <div className="border-l-2 border-gray-200 ml-6 h-6"></div>

              {/* Step 3 */}
              <div className="flex gap-6">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center w-12 h-12 bg-[#4ECFBF] text-white rounded-full text-xl font-bold shadow-lg">
                    3
                  </div>
                </div>
                <div className="flex-1 pt-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    Select Your Plan
                  </h3>
                  <p className="text-gray-600 leading-relaxed">
                    Choose between monthly or annual billing, and pick the plan that fits your learning goals
                    (Fluency Builder or Language Mastery).
                  </p>
                </div>
              </div>

              <div className="border-l-2 border-gray-200 ml-6 h-6"></div>

              {/* Step 4 */}
              <div className="flex gap-6">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center w-12 h-12 bg-[#4ECFBF] text-white rounded-full text-xl font-bold shadow-lg">
                    4
                  </div>
                </div>
                <div className="flex-1 pt-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    Enter Promo Code at Checkout
                  </h3>
                  <p className="text-gray-600 leading-relaxed">
                    On the Stripe checkout page, you'll see a "Add promotion code" field.
                    Click it and enter your promo code to apply your discount instantly.
                  </p>
                  <div className="mt-4 p-4 bg-amber-50 border-l-4 border-amber-400 rounded-r-lg">
                    <p className="text-sm text-amber-800 font-medium">
                      💡 Tip: Your promo code discount will be shown before you complete payment
                    </p>
                  </div>
                </div>
              </div>

              <div className="border-l-2 border-gray-200 ml-6 h-6"></div>

              {/* Step 5 */}
              <div className="flex gap-6">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center w-12 h-12 bg-[#4ECFBF] text-white rounded-full text-xl font-bold shadow-lg">
                    5
                  </div>
                </div>
                <div className="flex-1 pt-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    Return to the App
                  </h3>
                  <p className="text-gray-600 leading-relaxed">
                    After completing payment, return to the mobile app and your subscription will sync automatically.
                    You'll have instant access to all premium features!
                  </p>
                  <div className="mt-4 p-4 bg-green-50 border-l-4 border-green-400 rounded-r-lg">
                    <p className="text-sm text-green-800 font-medium">
                      ✨ Your subscription works across all devices - iOS, Android, and Web!
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* CTA Button */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="text-center"
          >
            <button
              onClick={handleGetStarted}
              className="inline-flex items-center gap-3 bg-gradient-to-r from-[#4ECFBF] to-teal-600 text-white px-8 py-4 rounded-xl font-bold text-lg hover:shadow-xl hover:scale-105 transition-all duration-200"
            >
              {user ? 'Go to Pricing' : 'Sign In to Get Started'}
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </button>
          </motion.div>

          {/* Help Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.6 }}
            className="mt-12 text-center"
          >
            <p className="text-gray-600">
              Need help?{' '}
              <a
                href="mailto:support@mytacoai.com"
                className="text-[#4ECFBF] font-semibold hover:underline"
              >
                Contact our support team
              </a>
            </p>
          </motion.div>
        </div>
      </main>
    </div>
  );
}
