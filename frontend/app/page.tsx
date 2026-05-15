'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/auth';
import NavBar from '@/components/nav-bar';
import FAQSection from '@/components/faq-section';
import LearningPlanDashboard from '@/components/dashboard/LearningPlanDashboard';
import ProjectKnowledgeChatbot from '@/components/project-knowledge-chatbot';
import SubscriptionPlans from '@/components/subscription-plans';
import SoundWaveLoader from '@/components/sound-wave-loader';
import { motion } from 'framer-motion';

// Section divider — glowing hairline between dark sections
function SectionDivider({ accent = '#4ECFBF' }: { accent?: string }) {
  return (
    <div className="relative h-px w-full overflow-visible">
      <div className="absolute inset-0" style={{ background: 'rgba(255,255,255,0.04)' }} />
      <div
        className="absolute left-1/2 -translate-x-1/2 h-px w-64"
        style={{
          background: `radial-gradient(ellipse at center, ${accent}60 0%, transparent 70%)`,
          filter: 'blur(1px)',
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
            className="w-[3px] rounded-full bg-gradient-to-t from-[#4ECFBF] to-[#7EEEE3] flex-shrink-0"
            style={{ height: baseH }}
            animate={{ height: [baseH, baseH * 1.8, baseH * 0.6, baseH] }}
            transition={{ duration: 1.4 + (i % 5) * 0.2, repeat: Infinity, delay: i * 0.05, ease: 'easeInOut' }}
          />
        );
      })}
    </div>
  );
}

// Fix 4 — Proper hexagonal SVG Radar Chart (replaces DNAStrandMini in the DNA bento card)
function RadarChart() {
  const strands = [
    { label: 'Rhythm', value: 82, color: '#4ECFBF', angle: -90 },
    { label: 'Confidence', value: 74, color: '#7C3AED', angle: -30 },
    { label: 'Vocabulary', value: 91, color: '#F59E0B', angle: 30 },
    { label: 'Accuracy', value: 68, color: '#EF4444', angle: 90 },
    { label: 'Learning', value: 85, color: '#10B981', angle: 150 },
    { label: 'Emotional', value: 77, color: '#EC4899', angle: 210 },
  ];
  const cx = 110, cy = 110, r = 75;
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const point = (angle: number, pct: number) => ({
    x: cx + r * pct * Math.cos(toRad(angle)),
    y: cy + r * pct * Math.sin(toRad(angle)),
  });
  const polygon = strands.map(s => point(s.angle, s.value / 100));
  const polygonStr = polygon.map(p => `${p.x},${p.y}`).join(' ');
  const rings = [0.25, 0.5, 0.75, 1.0];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
    >
      <svg width="220" height="220" viewBox="0 0 220 220">
        <defs>
          <radialGradient id="radarFill" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#4ECFBF" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#7C3AED" stopOpacity="0.15" />
          </radialGradient>
        </defs>
        {/* Grid rings */}
        {rings.map((ring, ri) => {
          const pts = strands.map(s => point(s.angle, ring));
          return (
            <polygon
              key={ri}
              points={pts.map(p => `${p.x},${p.y}`).join(' ')}
              fill="none"
              stroke="rgba(255,255,255,0.08)"
              strokeWidth="1"
            />
          );
        })}
        {/* Axis lines */}
        {strands.map((s, i) => {
          const outer = point(s.angle, 1.0);
          return (
            <line
              key={i}
              x1={cx}
              y1={cy}
              x2={outer.x}
              y2={outer.y}
              stroke="rgba(255,255,255,0.06)"
              strokeWidth="1"
            />
          );
        })}
        {/* Filled area */}
        <polygon
          points={polygonStr}
          fill="url(#radarFill)"
          stroke="#4ECFBF"
          strokeWidth="1.5"
          strokeOpacity="0.6"
        />
        {/* Data points */}
        {strands.map((s, i) => {
          const p = point(s.angle, s.value / 100);
          return <circle key={i} cx={p.x} cy={p.y} r="4" fill={s.color} />;
        })}
        {/* Labels */}
        {strands.map((s, i) => {
          const labelR = r + 22;
          const lx = cx + labelR * Math.cos(toRad(s.angle));
          const ly = cy + labelR * Math.sin(toRad(s.angle));
          const anchor = lx < cx - 5 ? 'end' : lx > cx + 5 ? 'start' : 'middle';
          return (
            <g key={i}>
              <text x={lx} y={ly - 4} textAnchor={anchor} fontSize="9" fill={s.color} fontWeight="600">
                {s.label}
              </text>
              <text x={lx} y={ly + 8} textAnchor={anchor} fontSize="9" fill="rgba(255,255,255,0.4)">
                {s.value}
              </text>
            </g>
          );
        })}
      </svg>
    </motion.div>
  );
}

// DNAStrandMini kept for "How it Works" step 02 aside
function DNAStrandMini() {
  const strands = [
    { label: 'Rhythm', pct: 82, color: '#4ECFBF' },
    { label: 'Confidence', pct: 74, color: '#7C3AED' },
    { label: 'Vocabulary', pct: 91, color: '#F59E0B' },
    { label: 'Accuracy', pct: 68, color: '#EF4444' },
    { label: 'Learning', pct: 85, color: '#10B981' },
    { label: 'Emotional', pct: 77, color: '#EC4899' },
  ];
  return (
    <div className="space-y-2">
      {strands.map((s, i) => (
        <motion.div
          key={s.label}
          className="flex items-center gap-2"
          initial={{ opacity: 0, x: -10 }}
          whileInView={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.08, duration: 0.4 }}
          viewport={{ once: true }}
        >
          <span className="text-[10px] text-white/60 w-16 shrink-0">{s.label}</span>
          <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ backgroundColor: s.color }}
              initial={{ width: 0 }}
              whileInView={{ width: `${s.pct}%` }}
              transition={{ delay: 0.3 + i * 0.08, duration: 0.8, ease: 'easeOut' }}
              viewport={{ once: true }}
            />
          </div>
          <span className="text-[10px] text-white/50 w-6 text-right">{s.pct}</span>
        </motion.div>
      ))}
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
      <span className="text-[#4ECFBF] font-bold text-sm">{value}</span>
      <span className="text-white/50 text-xs">{label}</span>
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
  const { user, loading: authLoading } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [isInstitutionUser, setIsInstitutionUser] = useState(false);
  const [isTutorUser, setIsTutorUser] = useState(false);

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
    <div className="min-h-screen overflow-x-hidden w-full bg-[#0A0A0F]">
      <NavBar />

      {isLoading ? (
        <div className="min-h-screen flex items-center justify-center bg-[#0A0A0F]">
          <SoundWaveLoader size="lg" color="#4ECFBF" text="Loading..." subtext="Preparing your experience" />
        </div>
      ) : (
        <main className="start-screen">

          {/* ─── HERO ─────────────────────────────────────────── */}
          <section
            id="features"
            className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden px-4 pt-24 pb-16"
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
              className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#4ECFBF]/30 bg-[#4ECFBF]/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-[#4ECFBF]"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#4ECFBF] opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-[#4ECFBF]" />
              </span>
              Voice · AI · Language Learning
            </motion.div>

            {/* Headline — two calm lines, shimmer gradient on the second */}
            <div className="text-center max-w-4xl mx-auto">
              <motion.div
                className="text-5xl sm:text-6xl md:text-7xl font-extrabold leading-[1.1] tracking-tight text-center mb-6"
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 0.1 }}
              >
                <span className="block text-white mb-2">Speak any language</span>
                <span className="block headline-shimmer">from your Voice DNA</span>
              </motion.div>

              <motion.p
                className="text-lg sm:text-xl text-white/55 max-w-2xl mx-auto mb-10 leading-relaxed"
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
                    className="group flex items-center gap-3 rounded-2xl bg-white px-6 py-3.5 text-[#0A0A0F] font-semibold text-sm shadow-lg hover:shadow-[0_0_32px_rgba(78,207,191,0.35)] hover:scale-[1.03] active:scale-[0.98] transition-all duration-200"
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
                    className="group flex items-center gap-3 rounded-2xl border border-white/20 bg-white/[0.06] backdrop-blur-md px-6 py-3.5 text-white font-semibold text-sm hover:bg-white/10 hover:border-[#4ECFBF]/40 hover:scale-[1.03] active:scale-[0.98] transition-all duration-200"
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
                className="flex flex-wrap items-center justify-center gap-3 mb-16"
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
              {/* Glassy UI card */}
              <div className="relative rounded-3xl border border-white/10 bg-white/[0.04] backdrop-blur-xl overflow-hidden shadow-[0_40px_80px_rgba(0,0,0,0.6)]">
                {/* Mac-style traffic lights */}
                <div className="flex items-center gap-1.5 px-4 pt-4 pb-3 border-b border-white/[0.06]">
                  <div className="w-3 h-3 rounded-full bg-[#FF5F57]" />
                  <div className="w-3 h-3 rounded-full bg-[#FFBD2E]" />
                  <div className="w-3 h-3 rounded-full bg-[#28CA41]" />
                  <span className="ml-auto text-xs text-white/30 font-medium">MyTaco AI · Live Session</span>
                </div>

                <div className="px-6 py-5">
                  {/* Waveform — fixed height via VoiceWaveform component */}
                  <div className="flex items-center gap-3 mb-5">
                    <div className="w-8 h-8 rounded-full bg-[#4ECFBF]/20 border border-[#4ECFBF]/30 flex items-center justify-center shrink-0">
                      <div className="w-2 h-2 rounded-full bg-[#4ECFBF] animate-pulse" />
                    </div>
                    <VoiceWaveform bars={50} className="flex-1" />
                    <span className="text-xs text-white/30 font-mono shrink-0">0:43</span>
                  </div>

                  {/* Chat messages */}
                  <div className="space-y-3 mb-5">
                    <div className="flex items-start gap-3">
                      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#4ECFBF] to-[#3a9e92] flex items-center justify-center shrink-0">
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
                      <div className="rounded-2xl rounded-tr-sm bg-[#4ECFBF]/15 border border-[#4ECFBF]/20 px-4 py-2.5 text-sm text-white/80 max-w-[75%]">
                        The word order was very confusing for me at first.
                      </div>
                    </div>
                  </div>

                  {/* AI feedback scores */}
                  <div className="rounded-xl bg-white/[0.04] border border-white/[0.06] px-4 py-3">
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
                className="absolute -top-4 -right-4 sm:-right-8 rounded-2xl bg-[#0A0A0F] border border-[#7C3AED]/40 px-4 py-3 shadow-lg backdrop-blur-xl"
                animate={{ y: [0, -6, 0] }}
                transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
              >
                <div className="text-[10px] uppercase tracking-wider text-[#7C3AED] font-semibold mb-1">
                  Speaking DNA
                </div>
                <div className="text-sm font-bold text-white">Identified ✓</div>
              </motion.div>

              {/* Floating streak badge */}
              <motion.div
                className="absolute -bottom-4 -left-4 sm:-left-8 rounded-2xl bg-[#0A0A0F] border border-[#F59E0B]/40 px-4 py-3 shadow-lg"
                animate={{ y: [0, 6, 0] }}
                transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut', delay: 1 }}
              >
                <div className="text-xs font-bold text-[#F59E0B]">🔥 12-day streak</div>
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

          {/* ─── BENTO FEATURES ───────────────────────────────── */}
          <section
            id="bento-features"
            className="relative py-24 px-4"
            style={{ background: '#0D0D18' }}
          >
            <div className="max-w-6xl mx-auto">
              <Reveal className="text-center mb-16">
                <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[#4ECFBF] mb-4">
                  What makes MyTaco different
                </p>
                <h2 className="text-4xl sm:text-5xl font-extrabold text-white leading-tight tracking-tight">
                  A learning experience{' '}
                  <br className="hidden sm:block" />
                  <span
                    style={{
                      background: 'linear-gradient(90deg, #4ECFBF, #7C3AED)',
                      backgroundClip: 'text',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                    }}
                  >
                    built from your voice
                  </span>
                </h2>
              </Reveal>

              {/* Fix 3 — Bento grid: DNA in ONE card only; other cards have distinct visuals */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 auto-rows-auto">

                {/* Fix 3+4 — Big card: Speaking DNA with RadarChart (not waveform/bar) */}
                <Reveal delay={0} className="sm:col-span-2 lg:col-span-2">
                  <div className="relative rounded-3xl border border-white/[0.08] bg-white/[0.03] p-6 h-full min-h-[280px] overflow-hidden group hover:border-[#4ECFBF]/30 hover:bg-white/[0.05] transition-all duration-300">
                    <div
                      className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                      style={{
                        background:
                          'radial-gradient(ellipse at 20% 50%, rgba(78,207,191,0.08) 0%, transparent 60%)',
                      }}
                    />
                    <div className="relative z-10 flex flex-col sm:flex-row gap-6 items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-4">
                          <div className="w-10 h-10 rounded-2xl bg-[#4ECFBF]/15 flex items-center justify-center text-xl">
                            🧬
                          </div>
                          <div>
                            <div className="text-white font-bold text-lg leading-tight">Speaking DNA</div>
                            <div className="text-white/40 text-xs">Your unique voice fingerprint</div>
                          </div>
                          <div className="ml-auto">
                            <span className="text-[10px] font-semibold uppercase tracking-wider bg-[#4ECFBF]/10 text-[#4ECFBF] border border-[#4ECFBF]/20 rounded-full px-3 py-1">
                              Standout Feature
                            </span>
                          </div>
                        </div>
                        <p className="text-white/50 text-sm mb-5 leading-relaxed max-w-lg">
                          Every voice is unique. MyTaco analyses 6 dimensions of your speech — rhythm, confidence,
                          vocabulary, accuracy, learning speed, and emotional expression — to create a profile that&apos;s
                          entirely yours.
                        </p>
                        {/* Strand legend with colored dots */}
                        <div className="flex flex-wrap gap-x-4 gap-y-1.5 mt-2">
                          {[
                            { label: 'Rhythm', color: '#4ECFBF', value: 82 },
                            { label: 'Confidence', color: '#7C3AED', value: 74 },
                            { label: 'Vocabulary', color: '#F59E0B', value: 91 },
                            { label: 'Accuracy', color: '#EF4444', value: 68 },
                            { label: 'Learning', color: '#10B981', value: 85 },
                            { label: 'Emotional', color: '#EC4899', value: 77 },
                          ].map(s => (
                            <div key={s.label} className="flex items-center gap-1.5">
                              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: s.color }} />
                              <span className="text-[11px] text-white/50">{s.label}</span>
                              <span className="text-[11px] font-semibold" style={{ color: s.color }}>{s.value}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                      {/* Fix 4 — RadarChart replacing DNAStrandMini here */}
                      <div className="shrink-0 self-center">
                        <RadarChart />
                      </div>
                    </div>
                  </div>
                </Reveal>

                {/* Daily Missions — distinct visual: mission tier checklist */}
                <Reveal delay={0.08}>
                  <div className="relative rounded-3xl border border-white/[0.08] bg-white/[0.03] p-6 h-full min-h-[280px] overflow-hidden group hover:border-[#F59E0B]/30 transition-all duration-300">
                    <div className="text-3xl mb-4">🎯</div>
                    <div className="text-white font-bold text-lg mb-2">Daily Missions</div>
                    <p className="text-white/45 text-sm leading-relaxed mb-5">
                      Bronze, Silver, and Gold missions every day. Complete your plan session, a challenge,
                      and review flashcards — all in under 10 minutes.
                    </p>
                    <div className="space-y-2">
                      {[
                        { tier: 'Bronze', label: "Complete today's plan session", color: '#CD7F32', done: true },
                        { tier: 'Silver', label: 'Play Native Check challenge', color: '#C0C0C0', done: true },
                        { tier: 'Gold', label: 'Review 3 flashcard sets', color: '#FFD700', done: false },
                      ].map((m) => (
                        <div key={m.tier} className="flex items-center gap-2 rounded-xl border border-white/[0.06] bg-white/[0.03] px-3 py-2">
                          <div
                            className="w-2.5 h-2.5 rounded-full shrink-0"
                            style={{ backgroundColor: m.color }}
                          />
                          <span className={`text-xs flex-1 ${m.done ? 'text-white/40 line-through' : 'text-white/80'}`}>
                            {m.label}
                          </span>
                          {m.done ? (
                            <span className="text-[10px] text-[#4ECFBF] font-bold">✓</span>
                          ) : (
                            <span className="text-[10px] text-white/25">...</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </Reveal>

                {/* 7 Challenges — distinct visual: challenge pill grid */}
                <Reveal delay={0.12}>
                  <div className="relative rounded-3xl border border-white/[0.08] bg-white/[0.03] p-6 h-full min-h-[220px] overflow-hidden group hover:border-[#7C3AED]/30 transition-all duration-300">
                    <div className="text-3xl mb-4">⚡</div>
                    <div className="text-white font-bold text-lg mb-2">7 Challenge Types</div>
                    <p className="text-white/45 text-sm leading-relaxed mb-4">
                      15,000+ curated exercises across Error Spotting, Micro Quiz, Brain Tickler, Story Builder and more.
                    </p>
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
                  </div>
                </Reveal>

                {/* Heart system — distinct visual: animated heart row */}
                <Reveal delay={0.16}>
                  <div className="relative rounded-3xl border border-white/[0.08] bg-white/[0.03] p-6 h-full min-h-[220px] overflow-hidden group hover:border-[#EF4444]/30 transition-all duration-300">
                    <div className="text-3xl mb-4">❤️</div>
                    <div className="text-white font-bold text-lg mb-2">Heart System</div>
                    <p className="text-white/45 text-sm leading-relaxed mb-4">
                      Stay sharp with limited hearts per challenge. Build a streak shield and protect your progress.
                    </p>
                    <div className="flex gap-2 items-center mb-3">
                      {[true, true, true, true, false].map((full, i) => (
                        <motion.span
                          key={i}
                          className="text-2xl"
                          animate={full ? { scale: [1, 1.15, 1] } : {}}
                          transition={{ duration: 0.6, delay: i * 0.1, repeat: Infinity, repeatDelay: 3 }}
                        >
                          {full ? '❤️' : '🖤'}
                        </motion.span>
                      ))}
                      <span className="ml-2 text-[10px] text-[#4ECFBF] font-semibold">4 / 5 left</span>
                    </div>
                    <div className="text-[10px] text-white/30 flex items-center gap-1.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-[#F59E0B]" />
                      Streak shield active · refills at midnight
                    </div>
                  </div>
                </Reveal>

                {/* News Sessions — distinct visual: live feed cards */}
                <Reveal delay={0.2}>
                  <div className="relative rounded-3xl border border-white/[0.08] bg-white/[0.03] p-6 h-full min-h-[220px] overflow-hidden group hover:border-[#10B981]/30 transition-all duration-300">
                    <div className="text-3xl mb-4">📰</div>
                    <div className="text-white font-bold text-lg mb-2">News Sessions</div>
                    <p className="text-white/45 text-sm leading-relaxed mb-3">
                      Practice with today&apos;s real news — curated in your target language at your CEFR level.
                      Then start an AI conversation about the article.
                    </p>
                    <div className="space-y-1.5">
                      {['🇩🇪 Aktuelle Nachrichten · B2', '🇪🇸 Noticias de hoy · A2', '🇫🇷 Infos du jour · C1'].map(item => (
                        <div key={item} className="text-[11px] text-white/40 bg-white/[0.04] border border-white/[0.06] rounded-lg px-3 py-1.5 flex items-center gap-2">
                          <div className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-pulse shrink-0" />
                          {item}
                        </div>
                      ))}
                    </div>
                  </div>
                </Reveal>

                {/* Real-Time AI Conversation — wide; distinct visual: chat bubbles, no waveform */}
                <Reveal delay={0.24} className="sm:col-span-2 lg:col-span-2">
                  <div className="relative rounded-3xl border border-white/[0.08] bg-white/[0.03] p-6 h-full min-h-[220px] overflow-hidden group hover:border-[#4ECFBF]/25 transition-all duration-300">
                    <div className="flex flex-col sm:flex-row gap-6 items-start">
                      <div className="flex-1 shrink-0">
                        <div className="text-3xl mb-4">🎙️</div>
                        <div className="text-white font-bold text-lg mb-2">Real-Time Conversation</div>
                        <p className="text-white/45 text-sm leading-relaxed max-w-sm">
                          WebRTC-powered voice sessions with your AI tutor. No typing, no delays — just speak.
                          Get corrections, hints, and vocabulary tips as you go.
                        </p>
                      </div>
                      {/* Distinct visual: mini live transcript */}
                      <div className="w-full sm:w-64 shrink-0 sm:ml-auto space-y-2">
                        {[
                          { from: 'AI', text: 'How was your weekend?', teal: true },
                          { from: 'You', text: 'Ich war... uh, im Park?', teal: false },
                          { from: 'AI', text: '✓ Ich war im Park. Great use of Akkusativ!', teal: true },
                        ].map((msg, i) => (
                          <motion.div
                            key={i}
                            className={`rounded-2xl px-3 py-2 text-xs ${msg.teal
                              ? 'bg-[#4ECFBF]/10 border border-[#4ECFBF]/20 text-white/70'
                              : 'bg-white/[0.06] border border-white/[0.08] text-white/60 ml-4'
                            }`}
                            initial={{ opacity: 0, x: msg.teal ? -8 : 8 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.15 * i, duration: 0.4 }}
                            viewport={{ once: true }}
                          >
                            <span className="font-semibold text-[10px] block mb-0.5" style={{ color: msg.teal ? '#4ECFBF' : 'rgba(255,255,255,0.3)' }}>{msg.from}</span>
                            {msg.text}
                          </motion.div>
                        ))}
                        <div className="text-center text-[10px] text-white/20 mt-1">Live audio · real-time analysis</div>
                      </div>
                    </div>
                  </div>
                </Reveal>

                {/* Story Worlds — distinct visual: genre cards */}
                <Reveal delay={0.28}>
                  <div className="relative rounded-3xl border border-white/[0.08] bg-white/[0.03] p-6 h-full min-h-[220px] overflow-hidden group hover:border-[#EC4899]/30 transition-all duration-300">
                    <div className="text-3xl mb-4">📖</div>
                    <div className="text-white font-bold text-lg mb-2">Story Worlds</div>
                    <p className="text-white/45 text-sm leading-relaxed mb-3">
                      Collaborate with other learners to build stories in your target language. 26 worlds — mystery,
                      romance, sci-fi and more.
                    </p>
                    <div className="grid grid-cols-3 gap-1.5">
                      {[
                        { emoji: '🔮', genre: 'Mystery' },
                        { emoji: '🚀', genre: 'Sci-Fi' },
                        { emoji: '🏰', genre: 'Fantasy' },
                        { emoji: '🌊', genre: 'Adventure' },
                        { emoji: '💘', genre: 'Romance' },
                        { emoji: '🌿', genre: 'Nature' },
                      ].map((w) => (
                        <div key={w.genre} className="flex flex-col items-center gap-1 rounded-xl bg-white/[0.04] border border-white/[0.06] py-2">
                          <span className="text-lg">{w.emoji}</span>
                          <span className="text-[9px] text-white/35">{w.genre}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </Reveal>
              </div>
            </div>
          </section>

          <SectionDivider accent="#7C3AED" />

          {/* ─── HOW IT WORKS ─────────────────────────────────── */}
          <section
            id="how-it-works"
            className="relative py-24 px-4"
            style={{ background: '#0B0B14' }}
          >
            <div className="max-w-5xl mx-auto">
              <Reveal className="text-center mb-20">
                <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[#4ECFBF] mb-4">
                  Simple by design
                </p>
                <h2 className="text-4xl sm:text-5xl font-extrabold text-white leading-tight tracking-tight">
                  From first word to fluency
                </h2>
              </Reveal>

              <div className="relative">
                {/* Vertical connector line (desktop) */}
                <div className="hidden lg:block absolute left-1/2 top-0 bottom-0 w-px bg-gradient-to-b from-transparent via-white/10 to-transparent" />

                <div className="space-y-16 lg:space-y-24">
                  {[
                    {
                      step: '01',
                      icon: '🎙️',
                      title: 'Speak for 60 seconds',
                      body: 'Say anything — introduce yourself, talk about your week. Our AI listens to your natural speech, not a scripted phrase.',
                      aside: (
                        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4">
                          <div className="text-[10px] uppercase tracking-wider text-white/30 mb-2">Recording</div>
                          <VoiceWaveform bars={20} />
                          <div className="mt-2 text-center font-mono text-sm text-[#4ECFBF]">0:43 / 1:00</div>
                        </div>
                      ),
                    },
                    {
                      step: '02',
                      icon: '🧬',
                      title: 'Your Voice DNA is created',
                      body: 'We map 6 unique dimensions of your speech into a profile that\'s as personal as a fingerprint. No two learners are alike.',
                      aside: <DNAStrandMini />,
                      reverse: true,
                    },
                    {
                      step: '03',
                      icon: '🗺️',
                      title: 'A plan built just for you',
                      body: 'Your AI tutor generates a week-by-week learning plan, missions, and challenge types that target your weakest strands first.',
                      aside: (
                        <div className="space-y-2">
                          {['Week 1 · Rhythm & Intonation', 'Week 2 · Vocabulary Depth', 'Week 3 · Grammar Confidence'].map(
                            (w) => (
                              <div
                                key={w}
                                className="flex items-center gap-3 rounded-xl border border-white/[0.07] bg-white/[0.03] px-4 py-2.5"
                              >
                                <div className="w-1.5 h-1.5 rounded-full bg-[#4ECFBF]" />
                                <span className="text-sm text-white/60">{w}</span>
                              </div>
                            )
                          )}
                        </div>
                      ),
                    },
                    {
                      step: '04',
                      icon: '🚀',
                      title: 'Practise daily, evolve faster',
                      body: 'Daily missions, real news articles, 7 challenge types, and live voice sessions keep every day fresh. Your DNA profile updates with every session.',
                      aside: (
                        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4 text-center">
                          <div className="text-3xl font-extrabold text-[#4ECFBF]">+14%</div>
                          <div className="text-[11px] text-white/40 mb-3">Fluency improvement · 30 days</div>
                          <div className="flex items-center justify-center gap-1">
                            {Array.from({ length: 7 }).map((_, i) => (
                              <div
                                key={i}
                                className="w-5 rounded-sm"
                                style={{
                                  height: `${20 + (i * 7 % 30)}px`,
                                  background: i < 5 ? '#4ECFBF' : 'rgba(255,255,255,0.1)',
                                }}
                              />
                            ))}
                          </div>
                          <div className="text-[10px] text-white/25 mt-2">Last 7 days</div>
                        </div>
                      ),
                      reverse: true,
                    },
                  ].map((item) => (
                    <Reveal key={item.step}>
                      <div
                        className={`flex flex-col ${
                          item.reverse ? 'lg:flex-row-reverse' : 'lg:flex-row'
                        } gap-8 lg:gap-16 items-center`}
                      >
                        {/* Text side */}
                        <div className="flex-1 flex flex-col items-start">
                          <div className="flex items-center gap-4 mb-5">
                            <div className="text-4xl">{item.icon}</div>
                            <div
                              className="text-5xl font-black leading-none"
                              style={{
                                background: 'linear-gradient(135deg, rgba(78,207,191,0.15), rgba(78,207,191,0.05))',
                                backgroundClip: 'text',
                                WebkitBackgroundClip: 'text',
                                WebkitTextFillColor: 'transparent',
                              }}
                            >
                              {item.step}
                            </div>
                          </div>
                          <h3 className="text-2xl sm:text-3xl font-bold text-white mb-4 leading-snug">
                            {item.title}
                          </h3>
                          <p className="text-white/50 text-base leading-relaxed">{item.body}</p>
                        </div>
                        {/* Visual side */}
                        <div className="w-full lg:w-80 shrink-0">{item.aside}</div>
                      </div>
                    </Reveal>
                  ))}
                </div>
              </div>
            </div>

            {/* CTA into pricing */}
            <Reveal delay={0.2} className="text-center mt-24">
              <button
                onClick={() => scrollTo('pricing')}
                className="inline-flex items-center gap-2 rounded-2xl bg-[#4ECFBF] px-8 py-4 text-[#0A0A0F] font-bold text-base hover:bg-[#3dc4b5] hover:scale-[1.03] active:scale-[0.98] transition-all duration-200 shadow-[0_0_40px_rgba(78,207,191,0.3)]"
              >
                See plans & pricing
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
              </button>
            </Reveal>
          </section>

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
                <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[#4ECFBF] mb-4">
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
                    className="flex items-center gap-3 rounded-2xl bg-white px-6 py-3.5 text-[#0A0A0F] font-semibold text-sm hover:shadow-[0_0_32px_rgba(78,207,191,0.3)] hover:scale-[1.03] active:scale-[0.98] transition-all duration-200"
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
                    className="flex items-center gap-3 rounded-2xl border border-white/15 bg-white/[0.04] px-6 py-3.5 text-white font-semibold text-sm hover:border-[#4ECFBF]/40 hover:bg-white/[0.08] hover:scale-[1.03] active:scale-[0.98] transition-all duration-200"
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

          {/* ─── FOOTER STRIP ─────────────────────────────────── */}
          <footer className="border-t border-white/[0.06] bg-[#0A0A0F] py-8 px-4 mt-0">
            <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
              <span className="text-white/25 text-xs">© {new Date().getFullYear()} MyTaco AI. All rights reserved.</span>
              <div className="flex gap-6">
                {[
                  { label: 'Privacy', href: '/privacy' },
                  { label: 'Terms', href: '/terms' },
                  { label: 'GDPR', href: '/gdpr' },
                  { label: 'Help', href: '/help' },
                ].map((l) => (
                  <a key={l.label} href={l.href} className="text-white/25 hover:text-white/60 text-xs transition-colors duration-150">
                    {l.label}
                  </a>
                ))}
              </div>
            </div>
          </footer>
        </main>
      )}

      <ProjectKnowledgeChatbot />
    </div>
  );
}
