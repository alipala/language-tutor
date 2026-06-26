'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/auth';
import NavBar from '@/components/nav-bar';
import FAQSection from '@/components/faq-section';
import LearningPlanDashboard from '@/components/dashboard/LearningPlanDashboard';
import ProjectKnowledgeChatbot from '@/components/project-knowledge-chatbot';
import SubscriptionPlans from '@/components/subscription-plans';
import SoundWaveLoader from '@/components/sound-wave-loader';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import LearningJourneySection from '@/components/learning-journey-section';
import { Card, CardIcon, CardHeader, CardTitle, CardBody } from '@/components/ui/card';
import SpeakingDNASection from '@/components/landing/speaking-dna-section';
import StoryWorldsSection from '@/components/landing/story-worlds-section';
import ForSchoolsSection from '@/components/landing/for-schools-section';
import SecurityComplianceSection from '@/components/landing/security-compliance-section';

/**
 * SectionDivider — layered separator between dark sections.
 *
 * Three layers rendered in a 64px tall container:
 *  1. Top closing gradient — the outgoing section fades to transparent.
 *  2. Hairline — full-width line that fades at both edges via a horizontal gradient,
 *     with its full-width glow spread via box-shadow.
 *  3. Centered orb — a soft radial glow at the midpoint that acts as a
 *     focal "light source", making the transition feel physical not decorative.
 *  4. Bottom opening gradient — the incoming section opens from transparent.
 */
function SectionDivider({ accent = '#4ECFBF' }: { accent?: string }) {
  return (
    <div className="relative w-full pointer-events-none select-none" style={{ height: 64, overflow: 'visible' }}>
      {/* Layer 1: closing gradient — top half fades the outgoing section */}
      <div
        className="absolute inset-x-0 top-0"
        style={{
          height: 32,
          background: `linear-gradient(to bottom, transparent, rgba(255,255,255,0.015))`,
        }}
      />

      {/* Layer 2: hairline + wide glow */}
      <div
        className="absolute inset-x-0"
        style={{
          top: 31,
          height: 1,
          background: `linear-gradient(to right, transparent 0%, ${accent}55 20%, ${accent}99 50%, ${accent}55 80%, transparent 100%)`,
          boxShadow: `0 0 18px 4px ${accent}30, 0 0 48px 12px ${accent}14`,
        }}
      />

      {/* Layer 3: centered orb — tiny bright point at the middle of the line */}
      <div
        className="absolute left-1/2 -translate-x-1/2"
        style={{
          top: 28,
          width: 8,
          height: 8,
          borderRadius: '50%',
          background: accent,
          opacity: 0.9,
          boxShadow: `0 0 12px 4px ${accent}80, 0 0 32px 10px ${accent}40, 0 0 64px 20px ${accent}18`,
        }}
      />

      {/* Layer 4: opening gradient — bottom half opens the incoming section */}
      <div
        className="absolute inset-x-0 bottom-0"
        style={{
          height: 32,
          background: `linear-gradient(to top, transparent, rgba(255,255,255,0.015))`,
        }}
      />
    </div>
  );
}

// Fix 2 — VoiceWaveform with fixed height container (no layout shift)
function VoiceWaveform({ bars = 40, className = '' }: { bars?: number; className?: string }) {
  return (
    <div className={`flex items-end gap-[3px] h-12 flex-shrink-0 ${className}`}>
      {Array.from({ length: bars }).map((_, i) => {
        const heights = [8, 16, 24, 32, 20, 28, 12, 36, 18, 30];
        const baseH = heights[i % heights.length];
        return (
          <motion.div
            key={i}
            className="w-[3px] rounded-full bg-gradient-to-t from-brand to-[#7EEEE3] flex-shrink-0"
            style={{ height: baseH }}
            animate={{ height: [baseH, baseH * 1.8, baseH * 0.6, baseH] }}
            transition={{ duration: 1.4 + (i % 5) * 0.2, repeat: Infinity, delay: i * 0.05, ease: 'easeInOut' }}
          />
        );
      })}
    </div>
  );
}


// Floating stat chip
function StatChip({ value, label, delay = 0 }: { value: string; label: string; delay?: number }) {
  return (
    <motion.div
      className="inline-flex items-center gap-2 bg-white/[0.07] backdrop-blur-md border border-white/10 rounded-full px-4 py-2"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5 }}
    >
      <span className="text-brand font-bold text-xs sm:text-sm">{value}</span>
      <span className="text-white/50 text-[10px] sm:text-xs">{label}</span>
    </motion.div>
  );
}

// Scroll-reveal wrapper
function Reveal({
  children,
  delay = 0,
  className = '',
}: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 32 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: 0.65, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

export default function Home() {
  const WORDS = ['Confident', 'Fluent', 'Natural', 'Unstoppable'];
  const { user, loading: authLoading } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [wordIndex, setWordIndex] = useState(0);
  const [isInstitutionUser, setIsInstitutionUser] = useState(false);
  const [isTutorUser, setIsTutorUser] = useState(false);
  const prefersReducedMotion = useReducedMotion();

  useEffect(() => {
    // Don't rotate the hero word for users who asked for reduced motion.
    if (prefersReducedMotion) return;
    const id = setInterval(() => setWordIndex(i => (i + 1) % WORDS.length), 2800);
    return () => clearInterval(id);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefersReducedMotion]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setIsInstitutionUser(!!localStorage.getItem('institution_token'));
      setIsTutorUser(!!localStorage.getItem('tutorToken'));
    }
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined' || authLoading) return;
    setIsLoading(false);
  }, [authLoading, user]);

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  // Authenticated users see their dashboard
  if (!authLoading && user) {
    return (
      <div className="min-h-screen overflow-x-hidden w-full">
        <NavBar />
        <LearningPlanDashboard />
        <ProjectKnowledgeChatbot />
      </div>
    );
  }

  return (
    <div className="min-h-screen overflow-x-hidden w-full bg-bg">
      <NavBar />

      {isLoading ? (
        <div className="min-h-screen flex items-center justify-center bg-bg">
          <SoundWaveLoader size="lg" color="#4ECFBF" text="Loading..." subtext="Preparing your experience" />
        </div>
      ) : (
        <main className="start-screen">

          {/* ─── HERO ─────────────────────────────────────────── */}
          <section
            id="features"
            className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden px-4 pt-28 sm:pt-32 pb-12 sm:pb-16"
            style={{ background: '#0A0A0F' }}
          >
            {/* Mesh gradient blobs */}
            <div
              className="pointer-events-none absolute inset-0"
              style={{
                background:
                  'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(78,207,191,0.18) 0%, transparent 70%), radial-gradient(ellipse 60% 50% at 80% 80%, rgba(124,58,237,0.12) 0%, transparent 60%), radial-gradient(ellipse 50% 40% at 10% 90%, rgba(16,185,129,0.08) 0%, transparent 60%)',
              }}
            />

            {/* Eyebrow badge */}
            <motion.div
              className="mb-6 inline-flex items-center gap-2 rounded-full border border-brand/30 bg-brand/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-brand"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-brand" />
              </span>
              Voice · AI · Language Learning
            </motion.div>

            <div className="text-center max-w-4xl mx-auto">
              <motion.div
                className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight text-center mb-4 sm:mb-6"
                style={{ lineHeight: 1.08 }}
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 0.1 }}
              >
                {/* Line 1 — static */}
                <span className="block text-white">Become</span>

                {/* Line 2 — rotating word.
                    Solid brand color (no gradient-clip), simple fade + small
                    rise (no blur / no scale) so it renders reliably on every
                    browser & mobile GPU. Reduced-motion → shows a fixed word. */}
                <span
                  className="relative grid overflow-hidden text-brand"
                  style={{ minHeight: '1.15em' }}
                >
                  {prefersReducedMotion ? (
                    <span className="col-start-1 row-start-1 flex items-center justify-center font-extrabold">
                      Fluent
                    </span>
                  ) : (
                    <AnimatePresence mode="wait" initial={false}>
                      <motion.span
                        key={WORDS[wordIndex]}
                        className="col-start-1 row-start-1 flex items-center justify-center font-extrabold will-change-[opacity,transform]"
                        initial={{ opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -6 }}
                        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
                      >
                        {WORDS[wordIndex]}
                      </motion.span>
                    </AnimatePresence>
                  )}
                </span>

                {/* Line 3 — static */}
                <span className="block text-white">From Your Voice DNA</span>
              </motion.div>

              <motion.p
                className="text-base sm:text-lg md:text-xl text-white/55 max-w-2xl mx-auto mb-8 sm:mb-10 leading-relaxed px-2 sm:px-0"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4, duration: 0.7 }}
              >
                MyTaco AI listens to how you actually speak — rhythm, confidence, vocabulary, accuracy —
                and builds a personalised path that evolves with every conversation.
              </motion.p>

              {/* CTAs */}
              {!isInstitutionUser && !isTutorUser && (
                <motion.div
                  className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12"
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.55, duration: 0.6 }}
                >
                  <a
                    href="https://apps.apple.com/br/app/mytaco/id6757149290?l=en-GB"
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label="Download on the App Store"
                    className="group flex items-center gap-3 rounded-2xl bg-white px-6 py-3.5 text-bg font-semibold text-sm shadow-lg hover:shadow-[0_0_32px_rgba(78,207,191,0.35)] hover:scale-[1.03] active:scale-[0.98] transition-all duration-200"
                  >
                    <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z" />
                    </svg>
                    <span>Download on App Store</span>
                  </a>

                  <a
                    href="https://play.google.com/store/apps/details?id=com.bigdavinci.MyTacoAI"
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label="Get it on Google Play"
                    className="group flex items-center gap-3 rounded-2xl border border-white/20 bg-white/[0.06] backdrop-blur-md px-6 py-3.5 text-white font-semibold text-sm hover:bg-white/10 hover:border-brand/40 hover:scale-[1.03] active:scale-[0.98] transition-all duration-200"
                  >
                    <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M3.18 23.76c.34.19.73.23 1.1.12l12.02-12.02-2.49-2.49L3.18 23.76zM20.54 10.23l-2.93-1.65-2.81 2.81 2.81 2.81 2.96-1.67c.84-.47.84-1.83-.03-2.3zM1.91.17C1.65.45 1.5.86 1.5 1.38v21.24c0 .52.15.93.41 1.21l.07.06L13.17 12 1.98.11l-.07.06zM14.38 12l2.49-2.49L4.28.23c-.35-.2-.73-.24-1.1-.14L14.38 12z" />
                    </svg>
                    <span>Get it on Google Play</span>
                  </a>
                </motion.div>
              )}

              {/* Social proof chips */}
              <motion.div
                className="flex flex-wrap items-center justify-center gap-2 sm:gap-3 mb-10 sm:mb-16 px-4 sm:px-0"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.75, duration: 0.6 }}
              >
                <StatChip value="289+" label="conversations" delay={0.8} />
                <StatChip value="6" label="languages" delay={0.9} />
                <StatChip value="15K+" label="practice challenges" delay={1.0} />
                <StatChip value="24/7" label="AI available" delay={1.1} />
              </motion.div>
            </div>

            {/* Hero waveform visual */}
            <motion.div
              className="relative w-full max-w-3xl mx-auto"
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
            >
              {/* Hero UI card — solid elevated */}
              <div className="relative rounded-3xl border border-white/[0.12] overflow-hidden shadow-[0_40px_80px_rgba(0,0,0,0.7)]" style={{ backgroundColor: '#13131F' }}>
                {/* Mac-style traffic lights */}
                <div className="flex items-center gap-1.5 px-4 pt-4 pb-3 border-b border-white/[0.06]">
                  <div className="w-3 h-3 rounded-full bg-[#FF5F57]" />
                  <div className="w-3 h-3 rounded-full bg-[#FFBD2E]" />
                  <div className="w-3 h-3 rounded-full bg-[#28CA41]" />
                  <span className="ml-auto text-xs text-white/30 font-medium">MyTaco AI · Live Session</span>
                </div>

                <div className="px-4 sm:px-6 py-4 sm:py-5">
                  {/* Waveform — fixed height via VoiceWaveform component */}
                  <div className="flex items-center gap-3 mb-5">
                    <div className="w-8 h-8 rounded-full bg-brand/20 border border-brand/30 flex items-center justify-center shrink-0">
                      <div className="w-2 h-2 rounded-full bg-brand animate-pulse" />
                    </div>
                    <VoiceWaveform bars={28} className="flex-1" />
                    <span className="text-xs text-white/30 font-mono shrink-0">0:43</span>
                  </div>

                  {/* Chat messages */}
                  <div className="space-y-3 mb-5">
                    <div className="flex items-start gap-3">
                      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-brand to-[#3a9e92] flex items-center justify-center shrink-0">
                        <svg className="w-3.5 h-3.5 text-white" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
                        </svg>
                      </div>
                      <div className="rounded-2xl rounded-tl-sm bg-white/[0.07] border border-white/[0.08] px-4 py-2.5 text-sm text-white/80 max-w-[75%]">
                        What was the most challenging part of learning Dutch for you?
                      </div>
                    </div>
                    <div className="flex items-start gap-3 flex-row-reverse">
                      <div className="w-7 h-7 rounded-full bg-white/10 flex items-center justify-center shrink-0 text-[10px] text-white/60 font-semibold">
                        You
                      </div>
                      <div className="rounded-2xl rounded-tr-sm bg-brand/15 border border-brand/20 px-4 py-2.5 text-sm text-white/80 max-w-[75%]">
                        The word order was very confusing for me at first.
                      </div>
                    </div>
                  </div>

                  {/* AI feedback scores */}
                  <div className="rounded-xl border border-white/[0.10] px-4 py-3" style={{ backgroundColor: '#0E0E1A' }}>
                    <div className="text-[10px] font-semibold uppercase tracking-wider text-white/30 mb-2.5">
                      Voice DNA · Session Feedback
                    </div>
                    <div className="grid grid-cols-3 gap-3">
                      {[
                        { label: 'Pronunciation', score: 92, color: '#4ECFBF' },
                        { label: 'Grammar', score: 85, color: '#7C3AED' },
                        { label: 'Fluency', score: 78, color: '#F59E0B' },
                      ].map((m) => (
                        <div key={m.label} className="text-center">
                          <div className="text-xl font-bold" style={{ color: m.color }}>
                            {m.score}
                          </div>
                          <div className="text-[10px] text-white/40">{m.label}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Floating DNA badge */}
              <motion.div
                className="absolute -top-4 right-2 sm:-right-6 rounded-2xl bg-bg border border-cat-challenge/40 px-3 py-2 shadow-lg backdrop-blur-xl"
                animate={{ y: [0, -6, 0] }}
                transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
              >
                <div className="text-[10px] uppercase tracking-wider text-cat-challenge font-semibold mb-1">
                  Speaking DNA
                </div>
                <div className="text-sm font-bold text-white">Identified ✓</div>
              </motion.div>

              {/* Floating streak badge */}
              <motion.div
                className="absolute -bottom-4 left-2 sm:-left-6 rounded-2xl bg-bg border border-cat-missions/40 px-3 py-2 shadow-lg"
                animate={{ y: [0, 6, 0] }}
                transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut', delay: 1 }}
              >
                <div className="text-xs font-bold text-cat-missions">🔥 12-day streak</div>
                <div className="text-[10px] text-white/50">Keep going!</div>
              </motion.div>
            </motion.div>

            {/* Scroll indicator */}
            <motion.div
              className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 cursor-pointer"
              onClick={() => scrollTo('bento-features')}
              animate={{ y: [0, 6, 0] }}
              transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
            >
              <span className="text-xs text-white/30 tracking-widest uppercase">Scroll</span>
              <div className="w-[1px] h-8 bg-gradient-to-b from-white/30 to-transparent" />
            </motion.div>
          </section>

          <SectionDivider accent="#4ECFBF" />

          {/* ─── SPEAKING DNA (flagship feature) ──────────────── */}
          <SpeakingDNASection />

          <SectionDivider accent="#7C3AED" />

          {/* ─── BENTO FEATURES ───────────────────────────────── */}
          <section
            id="bento-features"
            className="relative py-24 px-4"
            style={{ background: '#0D0D18' }}
          >
            <div className="max-w-6xl mx-auto">
              <Reveal className="text-center mb-16">
                <p className="text-xs font-semibold uppercase tracking-[0.3em] text-brand mb-4">
                  Everything in one place
                </p>
                <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white leading-tight tracking-tight">
                  More ways to{' '}
                  <br className="hidden sm:block" />
                  <span
                    style={{
                      background: 'linear-gradient(90deg, #4ECFBF, #7C3AED)',
                      backgroundClip: 'text',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                    }}
                  >
                    practise every day
                  </span>
                </h2>
              </Reveal>

              {/* Bento grid — every card shares one elevation system (color = identity) */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 auto-rows-auto">

                {/* Daily Missions — mission tier checklist */}
                <Reveal delay={0.08}>
                  <Card elevation="rest" category="missions" interactive className="h-full min-h-[280px]">
                    <CardIcon category="missions" className="mb-4">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>
                    </CardIcon>
                    <CardTitle className="mb-2">Daily Missions</CardTitle>
                    <CardBody className="mb-5">
                      Bronze, Silver, and Gold missions every day. Complete your plan session, a challenge,
                      and review flashcards — all in under 10 minutes.
                    </CardBody>
                    <div className="space-y-2">
                      {[
                        { tier: 'Bronze', label: "Complete today's plan session", color: '#CD7F32', done: true },
                        { tier: 'Silver', label: 'Play Native Check challenge', color: '#C0C0C0', done: true },
                        { tier: 'Gold', label: 'Review 3 flashcard sets', color: '#FFD700', done: false },
                      ].map((m) => (
                        <div key={m.tier} className="flex items-center gap-2 rounded-xl border border-white/[0.08] bg-surface-sunken px-3 py-2">
                          <div
                            className="w-2.5 h-2.5 rounded-full shrink-0"
                            style={{ backgroundColor: m.color }}
                          />
                          <span className={`text-xs flex-1 ${m.done ? 'text-ink-faint line-through' : 'text-white/80'}`}>
                            {m.label}
                          </span>
                          {m.done ? (
                            <span className="text-[10px] text-brand font-bold">✓</span>
                          ) : (
                            <span className="text-[10px] text-ink-faint">...</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </Card>
                </Reveal>

                {/* 7 Challenges — challenge pill grid */}
                <Reveal delay={0.12}>
                  <Card elevation="rest" category="challenge" interactive className="h-full min-h-[220px]">
                    <CardIcon category="challenge" className="mb-4">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                    </CardIcon>
                    <CardTitle className="mb-2">7 Challenge Types</CardTitle>
                    <CardBody className="mb-4">
                      15,000+ curated exercises across Error Spotting, Micro Quiz, Brain Tickler, Story Builder and more.
                    </CardBody>
                    <div className="flex flex-wrap gap-1.5">
                      {[
                        { name: 'Error Spot', color: '#EF4444' },
                        { name: 'Micro Quiz', color: '#7C3AED' },
                        { name: 'Brain Tickler', color: '#F59E0B' },
                        { name: 'Native Check', color: '#4ECFBF' },
                        { name: 'Story Builder', color: '#EC4899' },
                        { name: 'Smart Card', color: '#10B981' },
                        { name: 'Swipe Fix', color: '#3B82F6' },
                      ].map((c) => (
                        <span
                          key={c.name}
                          className="text-[10px] border rounded-full px-2.5 py-1 font-medium"
                          style={{ borderColor: `${c.color}40`, color: c.color, backgroundColor: `${c.color}12` }}
                        >
                          {c.name}
                        </span>
                      ))}
                    </div>
                  </Card>
                </Reveal>

                {/* Heart system — animated heart row */}
                <Reveal delay={0.16}>
                  <Card elevation="rest" category="hearts" interactive className="h-full min-h-[220px]">
                    <CardIcon category="hearts" className="mb-4">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" /></svg>
                    </CardIcon>
                    <CardTitle className="mb-2">Heart System</CardTitle>
                    <CardBody className="mb-4">
                      Stay sharp with limited hearts per challenge. Build a streak shield and protect your progress.
                    </CardBody>
                    <div className="flex gap-2 items-center mb-3">
                      {[true, true, true, true, false].map((full, i) => (
                        <motion.span
                          key={i}
                          className="text-2xl"
                          aria-hidden="true"
                          animate={full ? { scale: [1, 1.15, 1] } : {}}
                          transition={{ duration: 0.6, delay: i * 0.1, repeat: Infinity, repeatDelay: 3 }}
                        >
                          {full ? '❤️' : '🖤'}
                        </motion.span>
                      ))}
                      <span className="ml-2 text-[10px] text-brand font-semibold">4 / 5 left</span>
                    </div>
                    <div className="text-[10px] text-ink-faint flex items-center gap-1.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-warning" />
                      Streak shield active · refills at midnight
                    </div>
                  </Card>
                </Reveal>

                {/* News Sessions — live feed cards */}
                <Reveal delay={0.2}>
                  <Card elevation="rest" category="news" interactive className="h-full min-h-[220px]">
                    <CardIcon category="news" className="mb-4">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" /></svg>
                    </CardIcon>
                    <CardTitle className="mb-2">News Sessions</CardTitle>
                    <CardBody className="mb-3">
                      Practice with today&apos;s real news — curated in your target language at your CEFR level.
                      Then start an AI conversation about the article.
                    </CardBody>
                    <div className="space-y-1.5">
                      {['🇩🇪 Aktuelle Nachrichten · B2', '🇪🇸 Noticias de hoy · A2', '🇫🇷 Infos du jour · C1'].map(item => (
                        <div key={item} className="text-[11px] text-ink-muted bg-surface-sunken border border-white/[0.08] rounded-lg px-3 py-1.5 flex items-center gap-2">
                          <div className="w-1.5 h-1.5 rounded-full bg-success animate-pulse shrink-0" />
                          {item}
                        </div>
                      ))}
                    </div>
                  </Card>
                </Reveal>

                {/* Real-Time AI Conversation — wide; chat transcript */}
                <Reveal delay={0.24} className="sm:col-span-2 lg:col-span-2">
                  <Card elevation="rest" category="conversation" interactive className="h-full min-h-[220px]">
                    <div className="flex flex-col sm:flex-row gap-6 items-start">
                      <div className="flex-1 shrink-0">
                        <CardIcon category="conversation" className="mb-4">
                          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" /></svg>
                        </CardIcon>
                        <CardTitle className="mb-2">Real-Time Conversation</CardTitle>
                        <CardBody className="max-w-sm">
                          Instant, natural voice sessions with your AI tutor — no typing, no lag, just speak.
                          Get corrections, hints, and vocabulary tips the moment you need them.
                        </CardBody>
                      </div>
                      {/* Mini live transcript */}
                      <div className="w-full sm:w-72 shrink-0 sm:ml-auto space-y-2">
                        {[
                          { from: 'AI', text: 'How was your weekend?', teal: true },
                          { from: 'You', text: 'Ich war... uh, im Park?', teal: false },
                          { from: 'AI', text: '✓ Ich war im Park. Great use of Akkusativ!', teal: true },
                        ].map((msg, i) => (
                          <motion.div
                            key={i}
                            className={`rounded-2xl px-3 py-2 text-xs ${msg.teal
                              ? 'bg-brand/10 border border-brand/20 text-white/75'
                              : 'bg-white/[0.06] border border-white/[0.08] text-ink-muted ml-4'
                            }`}
                            initial={{ opacity: 0, x: msg.teal ? -8 : 8 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.15 * i, duration: 0.4 }}
                            viewport={{ once: true }}
                          >
                            <span className="font-semibold text-[10px] block mb-0.5" style={{ color: msg.teal ? '#4ECFBF' : 'rgba(255,255,255,0.4)' }}>{msg.from}</span>
                            {msg.text}
                          </motion.div>
                        ))}
                        <div className="text-center text-[10px] text-ink-faint mt-1">Live audio · real-time analysis</div>
                      </div>
                    </div>
                  </Card>
                </Reveal>
              </div>
            </div>
          </section>

          <SectionDivider accent="#E84C88" />

          {/* ─── STORY WORLDS (flagship game showcase) ─────────── */}
          <StoryWorldsSection />

          <SectionDivider accent="#7C3AED" />

          {/* ─── YOUR LEARNING JOURNEY ────────────────────────── */}
          <LearningJourneySection scrollTo={scrollTo} />

          <SectionDivider accent="#4ECFBF" />

          {/* ─── FOR SCHOOLS & INSTITUTIONS (B2B) ─────────────── */}
          <ForSchoolsSection />

          <SectionDivider accent="#10B981" />

          {/* ─── SECURITY & COMPLIANCE ────────────────────────── */}
          <SecurityComplianceSection />

          <SectionDivider accent="#4ECFBF" />

          {/* Pricing — all styling lives inside SubscriptionPlans */}
          <SubscriptionPlans />

          <SectionDivider accent="#F59E0B" />

          {/* ─── FAQ ──────────────────────────────────────────── */}
          <section
            id="faq"
            className="relative py-24 px-4"
            style={{ background: '#0D0D18' }}
          >
            <div className="max-w-3xl mx-auto">
              <Reveal className="text-center mb-12">
                <p className="text-xs font-semibold uppercase tracking-[0.3em] text-brand mb-4">
                  Got questions?
                </p>
                <h2 className="text-4xl sm:text-5xl font-extrabold text-white">
                  FAQ
                </h2>
              </Reveal>
              <FAQSection />

              {/* Final download CTA */}
              <Reveal delay={0.2} className="text-center mt-16">
                <p className="text-white/40 text-sm mb-6">Ready to speak with confidence?</p>
                <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                  <a
                    href="https://apps.apple.com/br/app/mytaco/id6757149290?l=en-GB"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-3 rounded-2xl bg-white px-6 py-3.5 text-bg font-semibold text-sm hover:shadow-[0_0_32px_rgba(78,207,191,0.3)] hover:scale-[1.03] active:scale-[0.98] transition-all duration-200"
                  >
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z" />
                    </svg>
                    App Store
                  </a>
                  <a
                    href="https://play.google.com/store/apps/details?id=com.bigdavinci.MyTacoAI"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-3 rounded-2xl border border-white/15 bg-white/[0.04] px-6 py-3.5 text-white font-semibold text-sm hover:border-brand/40 hover:bg-white/[0.08] hover:scale-[1.03] active:scale-[0.98] transition-all duration-200"
                  >
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M3.18 23.76c.34.19.73.23 1.1.12l12.02-12.02-2.49-2.49L3.18 23.76zM20.54 10.23l-2.93-1.65-2.81 2.81 2.81 2.81 2.96-1.67c.84-.47.84-1.83-.03-2.3zM1.91.17C1.65.45 1.5.86 1.5 1.38v21.24c0 .52.15.93.41 1.21l.07.06L13.17 12 1.98.11l-.07.06zM14.38 12l2.49-2.49L4.28.23c-.35-.2-.73-.24-1.1-.14L14.38 12z" />
                    </svg>
                    Google Play
                  </a>
                </div>
              </Reveal>
            </div>
          </section>

          {/* Footer rendered globally via layout.tsx → ConditionalFooter → footer.tsx */}
        </main>
      )}

      <ProjectKnowledgeChatbot />
    </div>
  );
}
