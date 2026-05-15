'use client';

import { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';

/* ─────────────────────────────────────────────────────────────
 *  LAYOUT:  Each row is  [ dot-column | card ]
 *
 *  DOT_COL = 40px wide  (flex-shrink-0)
 *  The dot (28px circle) is centred in that column → left: 6px
 *  The spine is a 2px line centred in that column  → left: 19px
 *  Both are siblings inside the same relative parent → same reference frame.
 *  No coordinate mismatch possible.
 * ─────────────────────────────────────────────────────────────*/

/* ─── Spine — 2px line down the left column ──────────────── */
function JourneySpine({ containerRef }: { containerRef: React.RefObject<HTMLDivElement | null> }) {
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start 80%', 'end 40%'],
  });
  const scaleY = useTransform(scrollYProgress, [0, 1], [0, 1]);

  return (
    /* Centered in the 40px dot-column: left = (40/2) - 1 = 19px */
    <div
      className="absolute top-0 bottom-0 w-[2px] pointer-events-none z-0"
      style={{ left: 19 }}
      aria-hidden
    >
      {/* Faint static track always visible */}
      <div className="absolute inset-0 rounded-full" style={{ background: 'rgba(255,255,255,0.07)' }} />
      {/* Scroll-driven gradient fill */}
      <motion.div
        className="absolute inset-x-0 top-0 origin-top rounded-full"
        style={{
          scaleY,
          height: '100%',
          background: 'linear-gradient(to bottom, #4ECFBF 0%, #7C3AED 40%, #4ECFBF 75%, #10B981 100%)',
          boxShadow: '0 0 10px 3px rgba(78,207,191,0.45)',
        }}
      />
    </div>
  );
}

/* ─── Dot — centred in the 40px dot-column ───────────────── */
function SpineNode({ color = '#4ECFBF', delay = 0 }: { color?: string; delay?: number }) {
  /*  dot is 28px.  column is 40px.  left = (40 - 28) / 2 = 6px  */
  return (
    <motion.div
      className="flex items-center justify-center rounded-full flex-shrink-0 z-10 relative"
      style={{
        width: 28,
        height: 28,
        marginLeft: 6,   /* (40 - 28) / 2  → centred in 40px column */
        marginRight: 6,  /* column total = 6 + 28 + 6 = 40px */
        backgroundColor: `${color}18`,
        border: `2px solid ${color}`,
        boxShadow: `0 0 0 4px ${color}12`,
      }}
      initial={{ scale: 0, opacity: 0 }}
      whileInView={{ scale: 1, opacity: 1 }}
      viewport={{ once: true, amount: 0.5 }}
      transition={{ delay, type: 'spring', stiffness: 280, damping: 22 }}
    >
      <div
        style={{
          width: 10,
          height: 10,
          borderRadius: '50%',
          backgroundColor: color,
          boxShadow: `0 0 8px 3px ${color}60`,
        }}
      />
    </motion.div>
  );
}

/* ─── Row wrapper — dot + card side by side ──────────────── */
function JourneyRow({
  accent,
  dotDelay,
  cardDelay,
  children,
}: {
  accent: string;
  dotDelay: number;
  cardDelay: number;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-0">
      {/* Left column: fixed 40px, dot centred, spine runs behind */}
      <div className="flex-shrink-0 flex flex-col items-center" style={{ width: 40 }}>
        <SpineNode color={accent} delay={dotDelay} />
      </div>

      {/* Right column: card */}
      <motion.div
        className="flex-1 min-w-0 mb-6"
        initial={{ opacity: 0, x: -20 }}
        whileInView={{ opacity: 1, x: 0 }}
        viewport={{ once: true, amount: 0.2 }}
        transition={{ duration: 0.55, delay: cardDelay, ease: [0.22, 1, 0.36, 1] }}
      >
        {children}
      </motion.div>
    </div>
  );
}

/* ─── Card shell ─────────────────────────────────────────── */
function JourneyCard({
  step,
  icon,
  accent,
  title,
  subtitle,
  children,
}: {
  step: string;
  icon: string;
  accent: string;
  title: string;
  subtitle: string;
  children?: React.ReactNode;
}) {
  return (
    <motion.div
      className="rounded-2xl border bg-white/[0.03] backdrop-blur-sm p-5 sm:p-6"
      style={{ borderColor: `${accent}28` }}
      whileHover={{ borderColor: `${accent}55`, transition: { duration: 0.2 } }}
    >
      <div className="flex items-center gap-3 mb-3">
        <div
          className="w-9 h-9 rounded-xl flex items-center justify-center text-lg shrink-0"
          style={{ backgroundColor: `${accent}18` }}
        >
          {icon}
        </div>
        <span
          className="text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full"
          style={{ color: accent, backgroundColor: `${accent}15` }}
        >
          {step}
        </span>
      </div>
      <h3 className="text-base sm:text-lg font-bold text-white mb-1">{title}</h3>
      <p className="text-white/45 text-sm leading-relaxed mb-4">{subtitle}</p>
      {children}
    </motion.div>
  );
}

/* ─── Sub-components (unchanged) ─────────────────────────── */
function Pill({ label, color }: { label: string; color: string }) {
  return (
    <span
      className="inline-flex items-center text-[11px] font-semibold px-2.5 py-1 rounded-full border"
      style={{ color, borderColor: `${color}40`, backgroundColor: `${color}10` }}
    >
      {label}
    </span>
  );
}

function CEFRScore() {
  const scores = [
    { label: 'Pronunciation', pct: 82, color: '#4ECFBF' },
    { label: 'Grammar',       pct: 74, color: '#7C3AED' },
    { label: 'Vocabulary',    pct: 88, color: '#F59E0B' },
    { label: 'Fluency',       pct: 71, color: '#10B981' },
  ];
  return (
    <div className="rounded-xl border border-white/[0.07] bg-white/[0.03] p-4 space-y-2">
      <div className="flex items-center justify-between mb-3">
        <span className="text-[10px] uppercase tracking-wider text-white/30">CEFR Score</span>
        <span className="text-xs font-bold text-[#4ECFBF]">B1 → Assigned</span>
      </div>
      {scores.map(s => (
        <div key={s.label} className="flex items-center gap-2">
          <span className="text-[10px] text-white/40 w-20 shrink-0">{s.label}</span>
          <div className="flex-1 h-1 bg-white/[0.08] rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ backgroundColor: s.color }}
              initial={{ width: 0 }}
              whileInView={{ width: `${s.pct}%` }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.3, ease: 'easeOut' }}
            />
          </div>
          <span className="text-[10px] font-semibold w-6 text-right" style={{ color: s.color }}>{s.pct}</span>
        </div>
      ))}
    </div>
  );
}

function MissionList() {
  const missions = [
    { tier: 'Bronze', color: '#CD7F32', label: "Complete today's plan session", done: true  },
    { tier: 'Silver', color: '#94A3B8', label: 'Play Native Check challenge',    done: true  },
    { tier: 'Gold',   color: '#F59E0B', label: 'Review 3 flashcard sets',        done: false },
  ];
  return (
    <div className="space-y-2">
      {missions.map(m => (
        <div key={m.tier} className="flex items-center gap-3 rounded-xl border border-white/[0.06] bg-white/[0.03] px-3 py-2">
          <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: m.color }} />
          <span className={`text-xs flex-1 ${m.done ? 'line-through text-white/30' : 'text-white/70'}`}>
            {m.label}
          </span>
          {m.done
            ? <span className="text-[10px] font-bold text-[#4ECFBF]">✓</span>
            : <span className="text-[10px] text-white/20">···</span>
          }
        </div>
      ))}
    </div>
  );
}

function SessionFlow() {
  const steps = [
    { icon: '🧬', label: 'DNA Voice Check', color: '#4ECFBF' },
    { icon: '🎙️', label: 'Conversation',    color: '#7C3AED' },
    { icon: '📊', label: 'Analysis',        color: '#F59E0B' },
  ];
  return (
    <div className="flex items-center gap-2 flex-wrap">
      {steps.map((s, i) => (
        <div key={s.label} className="flex items-center gap-2">
          <div
            className="flex items-center gap-1.5 rounded-xl border px-3 py-1.5 text-xs font-semibold"
            style={{ color: s.color, borderColor: `${s.color}35`, backgroundColor: `${s.color}10` }}
          >
            <span>{s.icon}</span>
            <span>{s.label}</span>
          </div>
          {i < steps.length - 1 && (
            <svg className="w-3 h-3 text-white/20 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          )}
        </div>
      ))}
    </div>
  );
}

function AssessmentBranch() {
  return (
    <div className="grid grid-cols-2 gap-3 mt-4">
      <motion.div
        className="rounded-xl border border-[#10B981]/30 p-4"
        style={{ backgroundColor: 'rgba(16,185,129,0.07)' }}
        initial={{ opacity: 0, x: -20 }}
        whileInView={{ opacity: 1, x: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 0.3, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="text-[#10B981] font-bold text-sm mb-1">✓ Pass</div>
        <p className="text-white/40 text-xs leading-snug">Next level plan auto-generated.</p>
      </motion.div>
      <motion.div
        className="rounded-xl border border-[#F59E0B]/30 p-4"
        style={{ backgroundColor: 'rgba(245,158,11,0.06)' }}
        initial={{ opacity: 0, x: 20 }}
        whileInView={{ opacity: 1, x: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 0.4, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="text-[#F59E0B] font-bold text-sm mb-1">↺ Retry</div>
        <p className="text-white/40 text-xs leading-snug">Targeted retry plan created.</p>
      </motion.div>
    </div>
  );
}

/* ─── MAIN EXPORT ─────────────────────────────────────────── */
export default function LearningJourneySection({ scrollTo, locale: _locale }: { scrollTo: (id: string) => void; locale?: string }) {
  const containerRef = useRef<HTMLDivElement>(null);

  return (
    <section
      id="how-it-works"
      className="relative py-24 px-4 overflow-hidden"
      style={{ background: '#0B0B14' }}
    >
      {/* Ambient glow */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            'radial-gradient(ellipse 60% 40% at 50% 0%, rgba(78,207,191,0.05) 0%, transparent 60%), radial-gradient(ellipse 40% 30% at 80% 100%, rgba(124,58,237,0.06) 0%, transparent 60%)',
        }}
      />

      <div className="max-w-2xl mx-auto relative">

        {/* Header */}
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-60px' }}
          transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
        >
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[#4ECFBF] mb-4">
            Your path to fluency
          </p>
          <h2 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight mb-4">
            A guided journey,<br />not just lessons
          </h2>
          <p className="text-white/40 text-base max-w-md mx-auto">
            MyTaco builds you a living, adapting path from your very first spoken word
            to your next CEFR level.
          </p>
        </motion.div>

        {/* Timeline — spine + rows in same ref container */}
        <div ref={containerRef} className="relative">
          <JourneySpine containerRef={containerRef} />

          <div className="space-y-4">

            <JourneyRow accent="#4ECFBF" dotDelay={0.1} cardDelay={0}>
              <JourneyCard step="Start" icon="🎙️" accent="#4ECFBF"
                title="Speaking Assessment"
                subtitle="Speak for 60 seconds on any topic. No script. Our AI records and analyses your natural voice across 6 dimensions."
              >
                <div className="flex flex-wrap gap-2 mb-4">
                  <Pill label="60s recording" color="#4ECFBF" />
                  <Pill label="45s minimum"   color="#4ECFBF" />
                  <Pill label="Any topic"     color="#4ECFBF" />
                </div>
                <CEFRScore />
              </JourneyCard>
            </JourneyRow>

            <JourneyRow accent="#7C3AED" dotDelay={0.18} cardDelay={0.08}>
              <JourneyCard step="Auto-created" icon="🗺️" accent="#7C3AED"
                title="Your Learning Plan"
                subtitle="Based on your CEFR score, a personalised week-by-week plan is instantly created — targeting your exact weak spots."
              >
                <div className="space-y-1.5">
                  {[
                    { label: 'Week 1–2 · Rhythm & Intonation', color: '#4ECFBF' },
                    { label: 'Week 3–4 · Vocabulary Depth',    color: '#7C3AED' },
                    { label: 'Week 5–6 · Grammar Confidence',  color: '#F59E0B' },
                    { label: 'Week 7–8 · Fluency & Coherence', color: '#10B981' },
                  ].map(w => (
                    <div key={w.label} className="flex items-center gap-2 text-xs text-white/50">
                      <div className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: w.color }} />
                      {w.label}
                    </div>
                  ))}
                </div>
              </JourneyCard>
            </JourneyRow>

            <JourneyRow accent="#4ECFBF" dotDelay={0.26} cardDelay={0.16}>
              <JourneyCard step="Every day" icon="📅" accent="#4ECFBF"
                title="Daily Plan Session"
                subtitle="Each session follows a 3-step flow: DNA Voice Check → guided conversation tied to your plan → post-session analysis."
              >
                <SessionFlow />
              </JourneyCard>
            </JourneyRow>

            <JourneyRow accent="#F59E0B" dotDelay={0.34} cardDelay={0.24}>
              <JourneyCard step="Daily" icon="🎯" accent="#F59E0B"
                title="Missions Support Your Plan"
                subtitle="Bronze, Silver, and Gold missions generated every day — chosen to reinforce the current week's focus area."
              >
                <MissionList />
              </JourneyCard>
            </JourneyRow>

            <JourneyRow accent="#7C3AED" dotDelay={0.42} cardDelay={0.32}>
              <JourneyCard step="Mid-plan" icon="📊" accent="#7C3AED"
                title="Intermediate Assessment"
                subtitle="Halfway through, a progress check re-scores your 6 strands. Your plan adapts — harder or softer — based on results."
              >
                <div className="flex gap-2 flex-wrap">
                  <Pill label="Plan adapts"      color="#7C3AED" />
                  <Pill label="DNA re-scored"    color="#4ECFBF" />
                  <Pill label="Missions updated" color="#F59E0B" />
                </div>
              </JourneyCard>
            </JourneyRow>

            <JourneyRow accent="#10B981" dotDelay={0.50} cardDelay={0.40}>
              <JourneyCard step="Plan end" icon="🏆" accent="#10B981"
                title="Final Assessment"
                subtitle="At the end of your plan, a full speaking assessment determines whether you advance to the next CEFR level."
              >
                <AssessmentBranch />
              </JourneyCard>
            </JourneyRow>

          </div>
        </div>

        {/* CTA */}
        <motion.div
          className="text-center mt-14"
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2, duration: 0.6 }}
        >
          <button
            onClick={() => scrollTo('pricing')}
            className="inline-flex items-center gap-2 rounded-2xl bg-[#4ECFBF] px-8 py-4 text-[#0A0A0F] font-bold text-sm hover:bg-[#3dc4b5] hover:scale-[1.03] active:scale-[0.98] transition-all duration-200 shadow-[0_0_40px_rgba(78,207,191,0.25)]"
          >
            Start your journey
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </button>
        </motion.div>

      </div>
    </section>
  );
}
