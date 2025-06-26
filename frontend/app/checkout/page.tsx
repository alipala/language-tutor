'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import NavBar from '@/components/nav-bar';
import { motion } from 'framer-motion';

export default function CheckoutPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get plan details from URL params
  const planId = searchParams.get('plan');
  const period = searchParams.get('period') || 'monthly';

  // Stripe price IDs
  const STRIPE_PRICES = {
    monthly: {
      fluency_builder: "price_1Re01yJcquSiYwWNJRg7nyce",
      team_mastery: "price_1Re09WJcquSiYwWNddEyeuxq"
    },
    annual: {
      fluency_builder: "price_1Re06kJcquSiYwWN89Ra57wC",
      team_mastery: "price_1Re0LdJcquSiYwWNmF516G2p"
    }
  };

  // Plan details for display
  const planDetails = {
    fluency_builder: {
      name: 'Fluency Builder',
      monthly: { price: '$19.99', priceNote: '/month' },
      annual: { price: '$199.99', priceNote: '/year', savings: 'Save $39.89 (17% off)' }
    },
    team_mastery: {
      name: 'Team Mastery',
      monthly: { price: '$39.99', priceNote: '/month per user' },
      annual: { price: '$399.99', priceNote: '/year per user', savings: 'Save $79.89 (17% off)' }
    }
  };

  useEffect(() => {
    // If no plan specified, redirect to home
    if (!planId || !planDetails[planId as keyof typeof planDetails]) {
      router.push('/#pricing');
      return;
    }

    // Auto-start checkout process
    handleCheckout();
  }, [planId, period]);

  const createCheckoutSession = async (priceId: string, isGuest: boolean = false) => {
    try {
      const baseUrl = window.location.origin;
      
      // Get the return URL from session storage (where user started checkout)
      const returnUrl = sessionStorage.getItem('checkoutReturnUrl') || '/';
      
      const successUrl = isGuest 
        ? `${baseUrl}/auth/signup?checkout=success&session_id={CHECKOUT_SESSION_ID}`
        : `${baseUrl}${returnUrl}?checkout=success`;
      const cancelUrl = `${baseUrl}${returnUrl}`;

      let response;

      if (isGuest) {
        // For guest users, create checkout session without authentication
        response = await fetch('/api/stripe/create-guest-checkout-session', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            price_id: priceId,
            success_url: successUrl,
            cancel_url: cancelUrl,
          }),
        });
      } else {
        // For authenticated users, use existing endpoint
        const token = localStorage.getItem('token');
        response = await fetch('/api/stripe/create-checkout-session', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            price_id: priceId,
            success_url: successUrl,
            cancel_url: cancelUrl,
          }),
        });
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to create checkout session');
      }

      const { url } = await response.json();
      
      // Store checkout context for post-payment flow
      if (isGuest) {
        sessionStorage.setItem('pendingSubscription', JSON.stringify({
          planId,
          period,
          priceId
        }));
      }
      
      // Redirect to Stripe Checkout
      window.location.href = url;
    } catch (error) {
      console.error('Error creating checkout session:', error);
      throw error;
    }
  };

  const handleCheckout = async () => {
    if (!planId) return;

    setIsLoading(true);
    setError(null);

    try {
      // Get the appropriate price ID
      const priceId = STRIPE_PRICES[period as keyof typeof STRIPE_PRICES]?.[planId as keyof typeof STRIPE_PRICES.monthly];
      
      if (!priceId) {
        throw new Error('Invalid plan or period selected');
      }

      // Create checkout session based on user authentication status
      await createCheckoutSession(priceId, !user);
    } catch (err: any) {
      console.error('Checkout error:', err);
      setError(err.message || 'Failed to start checkout process');
      setIsLoading(false);
    }
  };

  const currentPlan = planDetails[planId as keyof typeof planDetails];
  const currentPricing = currentPlan?.[period as 'monthly' | 'annual'];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
      <NavBar />
      
      <main className="pt-20 pb-12">
        <div className="max-w-md mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-2xl shadow-xl p-8 text-center"
          >
            {isLoading ? (
              <>
                {/* Progress Indicator */}
                <div className="mb-8">
                  <div className="flex items-center justify-center space-x-4 mb-4">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-[#4ECFBF] text-white rounded-full flex items-center justify-center text-sm font-medium">
                        1
                      </div>
                      <span className="ml-2 text-sm font-medium text-gray-800">Payment</span>
                    </div>
                    <div className="w-8 h-0.5 bg-gray-300"></div>
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-gray-200 text-gray-500 rounded-full flex items-center justify-center text-sm font-medium">
                        2
                      </div>
                      <span className="ml-2 text-sm text-gray-500">Account Setup</span>
                    </div>
                    <div className="w-8 h-0.5 bg-gray-300"></div>
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-gray-200 text-gray-500 rounded-full flex items-center justify-center text-sm font-medium">
                        3
                      </div>
                      <span className="ml-2 text-sm text-gray-500">Start Learning</span>
                    </div>
                  </div>
                </div>

                <div className="w-16 h-16 mx-auto mb-6 bg-[#4ECFBF]/10 rounded-full flex items-center justify-center">
                  <LoadingSpinner size="lg" />
                </div>
                
                <h2 className="text-2xl font-bold text-gray-800 mb-4">
                  Secure Payment Processing
                </h2>
                
                <p className="text-gray-600 mb-6">
                  {user ? 
                    "We're redirecting you to our secure payment processor." :
                    "Complete your payment, then create your account to access your subscription."
                  }
                </p>

                {currentPlan && currentPricing && (
                  <div className="bg-gray-50 rounded-lg p-4 mb-6">
                    <h3 className="font-semibold text-gray-800 mb-2">{currentPlan.name}</h3>
                    <div className="text-2xl font-bold text-[#4ECFBF]">
                      {currentPricing.price}
                      <span className="text-sm text-gray-600 ml-1">{currentPricing.priceNote}</span>
                    </div>
                    {'savings' in currentPricing && currentPricing.savings && (
                      <div className="text-green-600 text-sm font-medium mt-1">
                        {currentPricing.savings}
                      </div>
                    )}
                  </div>
                )}

                {/* What happens next */}
                <div className="bg-blue-50 rounded-lg p-4 mb-6 text-left">
                  <h4 className="font-medium text-blue-900 mb-2">What happens next:</h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li className="flex items-center">
                      <svg className="w-4 h-4 text-blue-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      Secure payment with Stripe
                    </li>
                    {!user && (
                      <li className="flex items-center">
                        <svg className="w-4 h-4 text-blue-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                        Quick account creation
                      </li>
                    )}
                    <li className="flex items-center">
                      <svg className="w-4 h-4 text-blue-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      Instant access to your plan
                    </li>
                  </ul>
                </div>

                <div className="text-sm text-gray-500">
                  Redirecting to secure payment...
                </div>
              </>
            ) : error ? (
              <>
                <div className="w-16 h-16 mx-auto mb-6 bg-red-100 rounded-full flex items-center justify-center">
                  <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                
                <h2 className="text-2xl font-bold text-gray-800 mb-4">
                  Something went wrong
                </h2>
                
                <p className="text-gray-600 mb-6">
                  {error}
                </p>

                <div className="space-y-3">
                  <button
                    onClick={handleCheckout}
                    className="w-full bg-[#4ECFBF] text-white py-3 px-4 rounded-lg font-medium hover:bg-[#3a9e92] transition-colors"
                  >
                    Try Again
                  </button>
                  
                  <button
                    onClick={() => router.push('/#pricing')}
                    className="w-full text-gray-600 py-3 px-4 rounded-lg font-medium hover:bg-gray-50 transition-colors"
                  >
                    Back to Plans
                  </button>
                </div>
              </>
            ) : null}
          </motion.div>
        </div>
      </main>
    </div>
  );
}
