'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useAuth } from '../lib/auth';
import { LoadingSpinner } from './ui/loading-spinner';
import AuthRequiredModal from './auth-required-modal';

interface PricingFeature {
  text: string;
  included: boolean;
}

interface PricingCard {
  name: string;
  price: string;
  priceNote: string;
  originalPrice?: string;
  savings?: string;
  monthlyEquivalent?: string;
  description: string;
  features: PricingFeature[];
  ctaButton: string;
  popular: boolean;
  note?: string;
}

const monthlyPlans: PricingCard[] = [
  {
    name: "Try & Learn",
    price: "Free",
    priceNote: "",
    description: "Perfect for exploring AI language learning",
    features: [
      { text: "3 practice sessions (5 minutes each) monthly", included: true },
      { text: "1 speaking assessment monthly", included: true },
      { text: "Basic progress tracking", included: true },
      { text: "Core conversation topics only", included: true },
      { text: "Mobile app access", included: true },
      { text: "Community support", included: true }
    ],
    ctaButton: "Start Free",
    popular: false
  },
  {
    name: "Fluency Builder",
    price: "$19.99",
    priceNote: "/month",
    description: "Ideal for serious language learners",
    features: [
      { text: "30 practice sessions (5 minutes each) monthly", included: true },
      { text: "2 speaking assessments monthly", included: true },
      { text: "Advanced progress tracking", included: true },
      { text: "Learning plan progression", included: true },
      { text: "Achievement badges", included: true },
      { text: "All conversation topics + custom topics", included: true },
      { text: "Conversation history & analytics", included: true },
      { text: "Priority email support", included: true }
    ],
    ctaButton: "Get Started",
    popular: true
  },
  {
    name: "Team Mastery",
    price: "$39.99",
    priceNote: "/month per user",
    description: "For teams and organizations",
    features: [
      { text: "Unlimited practice sessions", included: true },
      { text: "Unlimited assessments", included: true },
      { text: "Premium learning plans", included: true },
      { text: "Advanced analytics", included: true },
      { text: "Priority support", included: true },
      { text: "Team collaboration features", included: true },
      { text: "API access & LMS integrations", included: true },
      { text: "SSO & admin controls", included: true }
    ],
    ctaButton: "Get Started",
    popular: false,
    note: "Minimum 5 users"
  }
];

const annualPlans: PricingCard[] = [
  {
    name: "Try & Learn",
    price: "Free",
    priceNote: "",
    description: "Perfect for exploring AI language learning",
    features: [
      { text: "3 practice sessions (5 minutes each) monthly", included: true },
      { text: "1 speaking assessment monthly", included: true },
      { text: "Basic progress tracking", included: true },
      { text: "Core conversation topics only", included: true },
      { text: "Mobile app access", included: true },
      { text: "Community support", included: true }
    ],
    ctaButton: "Start Free",
    popular: false
  },
  {
    name: "Fluency Builder",
    price: "$199.99",
    priceNote: "/year",
    originalPrice: "$239.88",
    savings: "Save $39.89 (17% off)",
    monthlyEquivalent: "Only $16.67/month",
    description: "Ideal for serious language learners",
    features: [
      { text: "360 practice sessions (5 minutes each) annually", included: true },
      { text: "24 speaking assessments annually", included: true },
      { text: "Advanced progress tracking", included: true },
      { text: "Learning plan progression", included: true },
      { text: "Achievement badges", included: true },
      { text: "All conversation topics + custom topics", included: true },
      { text: "Conversation history & analytics", included: true },
      { text: "Priority email support", included: true }
    ],
    ctaButton: "Get Started",
    popular: true
  },
  {
    name: "Team Mastery",
    price: "$399.99",
    priceNote: "/year per user",
    originalPrice: "$479.88",
    savings: "Save $79.89 (17% off)",
    monthlyEquivalent: "Only $33.33/month per user",
    description: "For teams and organizations",
    features: [
      { text: "Unlimited practice sessions", included: true },
      { text: "Unlimited assessments", included: true },
      { text: "Premium learning plans", included: true },
      { text: "Advanced analytics", included: true },
      { text: "Priority support", included: true },
      { text: "Team collaboration features", included: true },
      { text: "API access & LMS integrations", included: true },
      { text: "SSO & admin controls", included: true }
    ],
    ctaButton: "Get Started",
    popular: false,
    note: "Minimum 5 users"
  }
];

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

export default function SubscriptionPlans() {
  const [isAnnual, setIsAnnual] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<PricingCard | null>(null);
  const currentPlans = isAnnual ? annualPlans : monthlyPlans;
  const router = useRouter();
  const { user } = useAuth();

  const createCheckoutSession = async (priceId: string) => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/stripe/create-checkout-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          price_id: priceId,
          success_url: `${window.location.origin}/profile?checkout=success`,
          cancel_url: `${window.location.origin}/profile?checkout=canceled`,
        }),
      });

      const { url } = await response.json();
      
      // Redirect to Stripe Checkout
      window.location.href = url;
    } catch (error) {
      console.error('Error creating checkout session:', error);
      setIsLoading(false);
    }
  };

  const handleCTAClick = async (plan: PricingCard) => {
    if (plan.ctaButton === "Start Free") {
      // Navigate to sign up flow
      router.push('/auth/signup');
    } else if (plan.ctaButton === "Get Started") {
      // Check if user is authenticated
      if (!user) {
        // Show auth modal for guest users
        setSelectedPlan(plan);
        setShowAuthModal(true);
        return;
      }

      // User is authenticated - proceed with checkout
      let planId = '';
      if (plan.name === "Fluency Builder") {
        planId = 'fluency_builder';
      } else if (plan.name === "Team Mastery") {
        planId = 'team_mastery';
      }

      if (planId) {
        // Get the appropriate price ID
        const period = isAnnual ? 'annual' : 'monthly';
        const priceId = STRIPE_PRICES[period][planId as keyof typeof STRIPE_PRICES.monthly];
        
        if (priceId) {
          await createCheckoutSession(priceId);
        }
      }
    } else if (plan.ctaButton === "Contact Sales") {
      // Open contact form or email
      window.location.href = 'mailto:sales@mytacoai.com?subject=Team Mastery Plan Inquiry';
    }
  };

  return (
    <section id="pricing" className="py-20 bg-gradient-to-br from-gray-50 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            Choose Your Plan
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-12">
            Start your language learning journey with our AI-powered tutor. 
            Choose the plan that fits your learning goals and budget.
          </p>

          {/* Billing Toggle */}
          <div className="flex items-center justify-center mb-12">
            <span className={`text-lg font-medium transition-colors duration-300 ${!isAnnual ? 'text-gray-900' : 'text-gray-500'}`}>
              Monthly
            </span>
            <button
              onClick={() => setIsAnnual(!isAnnual)}
              className="mx-4 relative inline-flex h-8 w-14 items-center rounded-full bg-gray-200 transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-[#4ECFBF] focus:ring-offset-2"
              style={{ backgroundColor: isAnnual ? '#4ECFBF' : '#e5e7eb' }}
            >
              <span
                className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform duration-300 ${
                  isAnnual ? 'translate-x-7' : 'translate-x-1'
                }`}
              />
            </button>
            <span className={`text-lg font-medium transition-colors duration-300 ${isAnnual ? 'text-gray-900' : 'text-gray-500'}`}>
              Annual
            </span>
            {isAnnual && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                className="ml-3 px-3 py-1 bg-green-100 text-green-800 text-sm font-medium rounded-full"
              >
                Save up to 17%
              </motion.div>
            )}
          </div>
        </div>

        {/* Pricing Cards */}
        <AnimatePresence mode="wait">
          <motion.div
            key={isAnnual ? 'annual' : 'monthly'}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
            className="grid grid-cols-1 md:grid-cols-3 gap-8 lg:gap-12"
          >
            {currentPlans.map((plan, index) => (
              <motion.div
                key={`${plan.name}-${isAnnual ? 'annual' : 'monthly'}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                className={`relative bg-white rounded-2xl shadow-xl border-2 transition-all duration-300 hover:shadow-2xl hover:-translate-y-1 flex flex-col h-full ${
                  plan.popular 
                    ? 'border-[#4ECFBF] ring-4 ring-[#4ECFBF]/20 scale-105' 
                    : 'border-gray-200 hover:border-[#4ECFBF]/50'
                }`}
              >
                {/* Popular Badge */}
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <div className="bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white px-6 py-2 rounded-full text-sm font-bold shadow-lg">
                      MOST POPULAR
                    </div>
                  </div>
                )}

                <div className="p-8 flex flex-col h-full">
                  {/* Plan Header */}
                  <div className="text-center mb-8">
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                    
                    {/* Pricing */}
                    <div className="mb-4">
                      {plan.originalPrice && (
                        <div className="text-sm text-gray-500 line-through mb-1">
                          {plan.originalPrice}
                        </div>
                      )}
                      <div className="flex items-end justify-center">
                        <span className="text-5xl font-bold text-gray-900">{plan.price}</span>
                        {plan.priceNote && (
                          <span className="text-gray-600 ml-2 mb-2">{plan.priceNote}</span>
                        )}
                      </div>
                      {plan.savings && (
                        <div className="text-green-600 font-semibold text-sm mt-2">
                          {plan.savings}
                        </div>
                      )}
                      {plan.monthlyEquivalent && (
                        <div className="text-gray-600 text-sm mt-1">
                          {plan.monthlyEquivalent}
                        </div>
                      )}
                    </div>

                    <p className="text-gray-600">{plan.description}</p>
                  </div>

                  {/* Features */}
                  <ul className="space-y-4 mb-8 flex-grow">
                    {plan.features.map((feature, featureIndex) => (
                      <li key={featureIndex} className="flex items-start">
                        <svg
                          className={`w-5 h-5 mt-0.5 mr-3 flex-shrink-0 ${
                            feature.included ? 'text-[#4ECFBF]' : 'text-gray-300'
                          }`}
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                        <span className={feature.included ? 'text-gray-700' : 'text-gray-400'}>
                          {feature.text}
                        </span>
                      </li>
                    ))}
                  </ul>

                  {/* Note - Move above button for Team Mastery */}
                  {plan.note && (
                    <p className="text-xs text-gray-500 mb-4 text-center">
                      {plan.note}
                    </p>
                  )}

                  {/* CTA Button - This will be pushed to the bottom */}
                  <div className="mt-auto">
                    <button
                      onClick={() => handleCTAClick(plan)}
                      disabled={isLoading}
                      className={`w-full py-4 px-6 rounded-xl font-semibold text-lg transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-offset-2 ${
                        plan.popular
                          ? 'bg-[#4ECFBF] text-white hover:bg-[#3a9e92] focus:ring-[#4ECFBF] shadow-lg'
                          : plan.name === "Try & Learn"
                          ? 'bg-gray-100 text-gray-800 hover:bg-gray-200 focus:ring-gray-300'
                          : 'bg-white text-[#4ECFBF] border-2 border-[#4ECFBF] hover:bg-[#4ECFBF] hover:text-white focus:ring-[#4ECFBF]'
                      } ${isLoading ? 'opacity-70 cursor-not-allowed' : ''}`}
                    >
                      {isLoading ? (
                        <div className="flex items-center justify-center">
                          <LoadingSpinner size="sm" className="mr-2" />
                          <span>Processing...</span>
                        </div>
                      ) : (
                        plan.ctaButton
                      )}
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </AnimatePresence>

        {/* Bottom CTA */}
        <div className="text-center mt-16">
          <div className="bg-gradient-to-r from-[#4ECFBF]/10 to-[#3a9e92]/10 rounded-2xl p-8 border border-[#4ECFBF]/20">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              Need a custom solution?
            </h3>
            <p className="text-gray-600 mb-6 max-w-2xl mx-auto">
              Contact us for enterprise pricing and customized language training programs 
              for larger organizations with specific requirements.
            </p>
            <button
              onClick={() => window.location.href = 'mailto:enterprise@mytacoai.com?subject=Enterprise Plan Inquiry'}
              className="inline-flex items-center px-8 py-3 bg-[#4ECFBF] text-white font-semibold rounded-xl hover:bg-[#3a9e92] transition-colors duration-300 shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Contact Enterprise Sales
            </button>
          </div>
        </div>
      </div>

      {/* Auth Required Modal */}
      {selectedPlan && (
        <AuthRequiredModal
          isOpen={showAuthModal}
          onClose={() => {
            setShowAuthModal(false);
            setSelectedPlan(null);
          }}
          planName={selectedPlan.name}
          planPrice={selectedPlan.price}
          planPeriod={isAnnual ? 'year' : 'month'}
        />
      )}
    </section>
  );
}
