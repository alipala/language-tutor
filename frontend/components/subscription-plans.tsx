'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useAuth } from '../lib/auth';
import { LoadingSpinner } from './ui/loading-spinner';
import { usePlanModal } from './modals/plan-modal-context';

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
    name: 'Try & Learn',
    price: 'Free',
    priceNote: '',
    description: 'Explore AI language learning at no cost',
    features: [
      { text: '15 min monthly speaking time', included: true },
      { text: 'Unlimited session tracking', included: true },
      { text: '1 speaking assessment / month', included: true },
      { text: 'Basic progress dashboard', included: true },
      { text: 'Core conversation topics', included: true },
      { text: 'Mobile app access', included: true },
      { text: 'Advanced analytics', included: false },
    ],
    ctaButton: 'Start Free',
    popular: false,
  },
  {
    name: 'Fluency Builder',
    price: '€9.99',
    priceNote: '/month',
    description: 'For consistent learners ready to level up',
    features: [
      { text: '3-day free trial included', included: true },
      { text: 'Speaking minutes monthly', included: true },
      { text: 'Personalised learning plan', included: true },
      { text: 'Voice DNA analysis', included: true },
      { text: '10 hearts for challenges', included: true },
      { text: 'Advanced progress tracking', included: true },
      { text: 'All conversation topics', included: true },
    ],
    ctaButton: 'Start Free Trial',
    popular: true,
  },
  {
    name: 'Language Mastery',
    price: '€17.99',
    priceNote: '/month',
    description: 'The ultimate immersive experience',
    features: [
      { text: '3-day free trial included', included: true },
      { text: 'UNLIMITED speaking time', included: true },
      { text: 'Personalised learning plan', included: true },
      { text: 'DNA acoustic analysis', included: true },
      { text: 'UNLIMITED hearts & games', included: true },
      { text: 'Instant heart refills', included: true },
      { text: 'Advanced analytics & DNA reports', included: true },
    ],
    ctaButton: 'Start Free Trial',
    popular: false,
  },
];

const annualPlans: PricingCard[] = [
  {
    name: 'Try & Learn',
    price: 'Free',
    priceNote: '',
    description: 'Explore AI language learning at no cost',
    features: [
      { text: '15 min monthly speaking time', included: true },
      { text: 'Unlimited session tracking', included: true },
      { text: '1 speaking assessment / month', included: true },
      { text: 'Basic progress dashboard', included: true },
      { text: 'Core conversation topics', included: true },
      { text: 'Mobile app access', included: true },
      { text: 'Advanced analytics', included: false },
    ],
    ctaButton: 'Start Free',
    popular: false,
  },
  {
    name: 'Fluency Builder',
    price: '€59.99',
    priceNote: '/year',
    savings: 'Save €59.89 · ~€5/month',
    description: 'For consistent learners ready to level up',
    features: [
      { text: '3-day free trial included', included: true },
      { text: 'Speaking minutes annually', included: true },
      { text: 'Personalised learning plan', included: true },
      { text: 'Voice DNA analysis', included: true },
      { text: '10 hearts for challenges', included: true },
      { text: 'Advanced progress tracking', included: true },
      { text: 'All conversation topics', included: true },
    ],
    ctaButton: 'Get Started',
    popular: true,
  },
  {
    name: 'Language Mastery',
    price: '€107.88',
    priceNote: '/year',
    savings: 'Save €107.99 · ~€9/month',
    description: 'The ultimate immersive experience',
    features: [
      { text: '3-day free trial included', included: true },
      { text: 'UNLIMITED speaking time', included: true },
      { text: 'Personalised learning plan', included: true },
      { text: 'DNA acoustic analysis', included: true },
      { text: 'UNLIMITED hearts & games', included: true },
      { text: 'Instant heart refills', included: true },
      { text: 'Advanced analytics & DNA reports', included: true },
    ],
    ctaButton: 'Get Started',
    popular: false,
  },
];

const STRIPE_PRICES = {
  monthly: {
    fluency_builder: process.env.NEXT_PUBLIC_STRIPE_PRICE_FLUENCY_BUILDER_MONTHLY || 'price_1RdxNjJcquSiYwWN2XQMwwYW',
    team_mastery: process.env.NEXT_PUBLIC_STRIPE_PRICE_TEAM_MASTERY_MONTHLY || 'price_1RdxlGJcquSiYwWNWvyEgmgL',
  },
  annual: {
    fluency_builder: process.env.NEXT_PUBLIC_STRIPE_PRICE_FLUENCY_BUILDER_YEARLY || 'price_1SoQw4JcquSiYwWNzi2zSgXt',
    team_mastery: process.env.NEXT_PUBLIC_STRIPE_PRICE_TEAM_MASTERY_YEARLY || 'price_1SoQy8JcquSiYwWNalBlWPEQ',
  },
};

// Card accent colors per plan
const PLAN_ACCENT: Record<string, { border: string; glow: string; badge: string; cta: string; ctaText: string }> = {
  'Try & Learn': {
    border: 'border-white/[0.08]',
    glow: '',
    badge: '',
    cta: 'bg-white/[0.08] hover:bg-white/[0.14] text-white/80',
    ctaText: '',
  },
  'Fluency Builder': {
    border: 'border-[#4ECFBF]/40',
    glow: '0 0 40px rgba(78,207,191,0.15)',
    badge: 'bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92]',
    cta: 'bg-[#4ECFBF] hover:bg-[#3dc4b5] text-[#0A0A0F]',
    ctaText: '',
  },
  'Language Mastery': {
    border: 'border-[#7C3AED]/30',
    glow: '0 0 40px rgba(124,58,237,0.12)',
    badge: '',
    cta: 'border border-[#7C3AED]/50 text-[#a78bfa] hover:bg-[#7C3AED]/15',
    ctaText: '',
  },
};

export default function SubscriptionPlans() {
  const [isAnnual, setIsAnnual] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const currentPlans = isAnnual ? annualPlans : monthlyPlans;
  const router = useRouter();
  const { user } = useAuth();
  const { openPlanModal } = usePlanModal();

  const createCheckoutSession = async (priceId: string) => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/stripe/create-checkout-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          price_id: priceId,
          success_url: `${window.location.origin}/profile?checkout=success`,
          cancel_url: `${window.location.origin}/profile?checkout=canceled`,
        }),
      });
      const { url } = await response.json();
      window.location.href = url;
    } catch {
      setIsLoading(false);
    }
  };

  const handleCTAClick = async (plan: PricingCard) => {
    if (plan.ctaButton === 'Start Free') {
      router.push('/auth/signup');
      return;
    }

    let planId = '';
    if (plan.name === 'Fluency Builder') planId = 'fluency_builder';
    else if (plan.name === 'Language Mastery') planId = 'team_mastery';
    if (!planId) return;

    const period = isAnnual ? 'annual' : 'monthly';

    if (!user) {
      sessionStorage.setItem('selectedPlan', JSON.stringify({ name: plan.name, planId, period }));
      router.push('/auth/login?from=pricing');
    } else {
      router.push(`/checkout?plan=${planId}&period=${period}`);
    }
  };

  return (
    <section
      id="pricing"
      style={{ background: 'linear-gradient(to bottom, #0D0D18, #0A0A0F)' }}
      className="py-24 px-4"
    >
      <div className="max-w-6xl mx-auto">

        {/* Header */}
        <motion.div
          className="text-center mb-14"
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-60px' }}
          transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
        >
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[#4ECFBF] mb-4">
            Simple &amp; transparent
          </p>
          <h2 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight mb-4">
            Choose Your Plan
          </h2>
          <p className="text-white/40 text-base max-w-lg mx-auto">
            Start free. Upgrade when you&apos;re ready. Cancel anytime.
          </p>
        </motion.div>

        {/* Billing toggle */}
        <motion.div
          className="flex items-center justify-center gap-4 mb-12"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.15 }}
        >
          <span className={`text-sm font-medium transition-colors ${!isAnnual ? 'text-white' : 'text-white/35'}`}>
            Monthly
          </span>
          <button
            onClick={() => setIsAnnual(!isAnnual)}
            aria-label="Toggle billing period"
            className="relative inline-flex h-7 w-12 items-center rounded-full transition-colors duration-300 focus:outline-none"
            style={{ backgroundColor: isAnnual ? '#4ECFBF' : 'rgba(255,255,255,0.12)' }}
          >
            <span
              className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform duration-300 ${
                isAnnual ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
          <span className={`text-sm font-medium transition-colors ${isAnnual ? 'text-white' : 'text-white/35'}`}>
            Annual
          </span>
          <AnimatePresence>
            {isAnnual && (
              <motion.span
                initial={{ opacity: 0, scale: 0.8, x: -6 }}
                animate={{ opacity: 1, scale: 1, x: 0 }}
                exit={{ opacity: 0, scale: 0.8, x: -6 }}
                transition={{ duration: 0.2 }}
                className="text-[11px] font-bold bg-[#10B981]/15 border border-[#10B981]/30 text-[#10B981] rounded-full px-3 py-1"
              >
                Save 50%
              </motion.span>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Cards */}
        <AnimatePresence mode="wait">
          <motion.div
            key={isAnnual ? 'annual' : 'monthly'}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -16 }}
            transition={{ duration: 0.3 }}
            className="grid grid-cols-1 md:grid-cols-3 gap-5"
          >
            {currentPlans.map((plan, index) => {
              const accent = PLAN_ACCENT[plan.name];
              return (
                <motion.div
                  key={`${plan.name}-${isAnnual ? 'annual' : 'monthly'}`}
                  initial={{ opacity: 0, y: 24 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: index * 0.08 }}
                  className={`relative flex flex-col rounded-3xl border ${accent.border} bg-white/[0.03] backdrop-blur-sm overflow-hidden transition-all duration-300 hover:-translate-y-1 ${
                    plan.popular ? 'md:scale-[1.04]' : ''
                  }`}
                  style={accent.glow ? { boxShadow: accent.glow } : {}}
                >
                  {/* Popular badge */}
                  {plan.popular && (
                    <div className="absolute top-0 inset-x-0 flex justify-center">
                      <div className={`${accent.badge} text-white text-[10px] font-bold uppercase tracking-widest px-5 py-1.5 rounded-b-xl`}>
                        Most Popular
                      </div>
                    </div>
                  )}

                  {/* Subtle top glow for popular */}
                  {plan.popular && (
                    <div
                      className="pointer-events-none absolute inset-0 rounded-3xl"
                      style={{
                        background: 'radial-gradient(ellipse 80% 40% at 50% 0%, rgba(78,207,191,0.1) 0%, transparent 70%)',
                      }}
                    />
                  )}

                  <div className={`flex flex-col flex-1 p-7 ${plan.popular ? 'pt-12' : 'pt-8'}`}>
                    {/* Plan name & description */}
                    <div className="mb-6">
                      <h3 className="text-lg font-bold text-white mb-1">{plan.name}</h3>
                      <p className="text-white/40 text-sm leading-snug">{plan.description}</p>
                    </div>

                    {/* Price */}
                    <div className="mb-6">
                      <div className="flex items-end gap-1.5">
                        <span className="text-4xl font-extrabold text-white tracking-tight">{plan.price}</span>
                        {plan.priceNote && (
                          <span className="text-white/35 text-sm mb-1.5">{plan.priceNote}</span>
                        )}
                      </div>
                      {plan.savings && (
                        <div className="mt-1.5 text-[11px] font-semibold text-[#10B981]">{plan.savings}</div>
                      )}
                      {/* Payment methods for paid plans */}
                      {plan.price !== 'Free' && (
                        <div className="mt-2 flex items-center gap-2 text-[11px] text-white/25">
                          <span>💳 Card</span>
                          <span>·</span>
                          <span>🇳🇱 iDEAL</span>
                        </div>
                      )}
                    </div>

                    {/* Divider */}
                    <div className="h-px bg-white/[0.07] mb-6" />

                    {/* Features */}
                    <ul className="flex-1 space-y-3 mb-8">
                      {plan.features.map((feature, fi) => (
                        <li key={fi} className="flex items-start gap-3">
                          {feature.included ? (
                            <svg className="w-4 h-4 mt-0.5 shrink-0 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                            </svg>
                          ) : (
                            <div className="w-4 h-4 mt-0.5 shrink-0 flex items-center justify-center">
                              <div className="w-1.5 h-1.5 rounded-full bg-white/20" />
                            </div>
                          )}
                          <span className={`text-sm leading-snug ${feature.included ? 'text-white/75' : 'text-white/25'}`}>
                            {feature.text}
                          </span>
                        </li>
                      ))}
                    </ul>

                    {/* CTA */}
                    <button
                      onClick={() => handleCTAClick(plan)}
                      disabled={isLoading}
                      className={`w-full py-3.5 rounded-2xl text-sm font-bold transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] focus:outline-none ${accent.cta} ${
                        isLoading ? 'opacity-60 cursor-not-allowed' : ''
                      }`}
                    >
                      {isLoading ? (
                        <span className="flex items-center justify-center gap-2">
                          <LoadingSpinner size="sm" />
                          Processing...
                        </span>
                      ) : (
                        plan.ctaButton
                      )}
                    </button>
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        </AnimatePresence>

        {/* Money-back + enterprise strip */}
        <motion.div
          className="mt-12 flex flex-col sm:flex-row items-center justify-between gap-6 rounded-2xl border border-white/[0.07] bg-white/[0.02] px-8 py-6"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-[#10B981]/10 border border-[#10B981]/20 flex items-center justify-center text-lg">
              🛡️
            </div>
            <div>
              <div className="text-sm font-semibold text-white">Cancel anytime</div>
              <div className="text-xs text-white/35">No long-term commitment required</div>
            </div>
          </div>
          <div className="hidden sm:block w-px h-8 bg-white/[0.08]" />
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-[#F59E0B]/10 border border-[#F59E0B]/20 flex items-center justify-center text-lg">
              ⚡
            </div>
            <div>
              <div className="text-sm font-semibold text-white">Free trial on paid plans</div>
              <div className="text-xs text-white/35">3 days free, no credit card required</div>
            </div>
          </div>
          <div className="hidden sm:block w-px h-8 bg-white/[0.08]" />
          <button
            onClick={() => { window.location.href = 'mailto:hello@mytacoai.com?subject=Enterprise Plan Inquiry'; }}
            className="text-sm font-semibold text-[#4ECFBF] hover:text-white transition-colors duration-200 underline underline-offset-4 decoration-[#4ECFBF]/40"
          >
            Need enterprise? Contact us →
          </button>
        </motion.div>

      </div>
    </section>
  );
}
