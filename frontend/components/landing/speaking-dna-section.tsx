'use client';

import { useState } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { Card } from '@/components/ui/card';

/**
 * Speaking DNA — flagship showcase.
 *
 * Recreates the mobile app's DNA double-helix (two offset sine-wave backbones
 * with faint rungs + six colored "base-pair" beads — one per speaking
 * dimension) next to a column of metric cards. Hovering any card spotlights
 * that dimension's strand in the helix and dims the rest.
 * Helix math mirrors src/screens/SpeakingDNA/components/SpeakingDNAHelix.tsx.
 */

// The six dimensions, colors + icons matched to the mobile app.
// `why` = a defensible, research-grounded reason the dimension matters for L2
// speaking (sources cited in the "science" strip below — no overclaiming).
const DIMENSIONS = [
  {
    key: 'rhythm', label: 'Rhythm', score: 84, color: '#4ECFBF', icon: 'pulse',
    why: 'Stress, rhythm and intonation — the suprasegmentals — are how listeners actually extract meaning from speech, beyond getting individual sounds right.',
  },
  {
    key: 'confidence', label: 'Confidence', score: 72, color: '#A78BFA', icon: 'shield',
    why: 'Steadier delivery — fewer hesitations and self-corrections — reads as more proficient and is easier for a listener to follow.',
  },
  {
    key: 'pronunciation', label: 'Pronunciation', score: 77, color: '#FFA955', icon: 'mic',
    why: 'Computer-assisted pronunciation training shows a clear, medium-sized benefit over traditional practice — targeted feedback works.',
  },
  {
    key: 'vocabulary', label: 'Vocabulary', score: 60, color: '#34D399', icon: 'book',
    why: 'The range and precision of the words you reach for is a core component of every standardised speaking rubric.',
  },
  {
    key: 'accuracy', label: 'Accuracy', score: 91, color: '#FFD63A', icon: 'target',
    why: 'Grammatical and phonetic accuracy are consistently linked to how intelligible and how native-like your speech is judged to be.',
  },
  {
    key: 'fluency', label: 'Fluency', score: 68, color: '#5B9DFF', icon: 'chat',
    why: 'Speech rate and pausing are among the strongest predictors of perceived fluency — and where you pause (mid-sentence vs. at a boundary) is itself diagnostic.',
  },
] as const;

// ── helix geometry (matches the mobile SVG) ──────────────────────────────
const VB_W = 150;            // viewBox width (+25% wider helix)
const CX = VB_W / 2;         // center x
const AMP = 47.5;            // sine amplitude (+25%, keeps the swing proportional)
const CYCLES = 3;            // full twists across the height
const ROW_H = 92;            // px per dimension row (matches card rhythm)
const TOP = ROW_H / 2;       // first bead center
const VB_H = ROW_H * DIMENSIONS.length;

const phase = (y: number) => ((y - 0) / VB_H) * CYCLES * 2 * Math.PI;
const xA = (y: number) => CX + AMP * Math.sin(phase(y));
const xB = (y: number) => CX - AMP * Math.sin(phase(y));

// sampled backbone polylines
function backbone(fn: (y: number) => number) {
  const pts: string[] = [];
  for (let y = 0; y <= VB_H; y += 6) {
    pts.push(`${fn(y).toFixed(1)},${y}`);
  }
  return 'M' + pts.join(' L');
}

// faint connecting rungs along the strand
function rungs() {
  const out: { y: number; x1: number; x2: number; o: number }[] = [];
  for (let y = 8; y <= VB_H - 8; y += 11) {
    const a = xA(y), b = xB(y);
    const len = Math.abs(a - b);
    if (len > 4) out.push({ y, x1: Math.min(a, b), x2: Math.max(a, b), o: len < 26 ? 0.08 : 0.14 });
  }
  return out;
}

const ICONS: Record<string, React.ReactNode> = {
  pulse:  <path strokeLinecap="round" strokeLinejoin="round" d="M3 12h4l2 6 4-12 2 6h6" />,
  shield: <path strokeLinecap="round" strokeLinejoin="round" d="M12 3l7 3v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3zM9.5 12l2 2 3.5-4" />,
  mic:    <path strokeLinecap="round" strokeLinejoin="round" d="M12 3a3 3 0 00-3 3v6a3 3 0 006 0V6a3 3 0 00-3-3zM5 11a7 7 0 0014 0M12 18v3" />,
  book:   <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.5C10.8 5.7 9.2 5.3 7.5 5.3S4.2 5.7 3 6.5v13c1.2-.8 2.8-1.2 4.5-1.2s3.3.4 4.5 1.2m0-13c1.2-.8 2.8-1.2 4.5-1.2s3.3.4 4.5 1.2v13c-1.2-.8-2.8-1.2-4.5-1.2s-3.3.4-4.5 1.2m0-13v13" />,
  target: <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9 9 0 100-18 9 9 0 000 18zM12 16a4 4 0 100-8 4 4 0 000 8zM12 12h.01" />,
  chat:   <path strokeLinecap="round" strokeLinejoin="round" d="M4 5h16v11H8l-4 4V5zM8 10h.01M12 10h.01M16 10h.01" />,
};

function Reveal({ children, delay = 0, className = '' }: { children: React.ReactNode; delay?: number; className?: string }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

export default function SpeakingDNASection() {
  const reduce = useReducedMotion();
  const beadCenters = DIMENSIONS.map((_, i) => TOP + i * ROW_H);

  // Hovering any card (metric OR science) spotlights that dimension's strand in
  // the helix and dims the others.
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const isActive = (k: string) => activeKey === null || activeKey === k;
  const dimOpacity = (k: string) => (isActive(k) ? 1 : 0.3);

  // Right-hand detail card: shows the hovered dimension, or the top-scoring one
  // by default. Its size is FIXED so it never resizes as content changes.
  const defaultKey = DIMENSIONS.reduce((a, b) => (b.score > a.score ? b : a)).key;
  const shown = DIMENSIONS.find((d) => d.key === (activeKey ?? defaultKey))!;

  return (
    <section id="speaking-dna" className="relative py-24 px-4" style={{ background: '#0B1A1F' }}>
      {/* teal ambient glow */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{ background: 'radial-gradient(ellipse 60% 50% at 50% -5%, rgba(78,207,191,0.12) 0%, transparent 65%)' }}
      />
      <div className="relative max-w-6xl mx-auto">
        <Reveal className="text-center mb-4">
          <span className="inline-flex items-center gap-2 rounded-full border border-brand/30 bg-brand/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-brand">
            Standout feature · Speaking DNA
          </span>
        </Reveal>
        <Reveal delay={0.05} className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white leading-tight tracking-tight">
            A learning experience{' '}
            <br className="hidden sm:block" />
            <span
              style={{
                background: 'linear-gradient(90deg, #4ECFBF, #A78BFA)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              built from your voice
            </span>
          </h2>
          <p className="text-base sm:text-lg text-ink-muted max-w-2xl mx-auto mt-5 leading-relaxed">
            Every voice is unique. MyTaco listens to <em>how</em> you actually speak and maps six
            dimensions of your speech into a profile that&apos;s entirely yours — and that evolves
            with every conversation.
          </p>
        </Reveal>

        <Reveal delay={0.1}>
          <Card elevation="hero" category="dna" className="overflow-hidden">
            <div className="flex flex-col sm:flex-row gap-4 sm:gap-8">
              {/* ── Helix ── */}
              <div className="shrink-0 mx-auto sm:mx-0 self-stretch flex">
                <svg
                  width={VB_W}
                  height="100%"
                  viewBox={`0 0 ${VB_W} ${VB_H}`}
                  preserveAspectRatio="xMidYMid meet"
                  className="max-h-[560px]"
                  role="img"
                  aria-label="DNA double helix representing six speaking dimensions"
                >
                  {/* backbones */}
                  <path d={backbone(xA)} fill="none" stroke="#AEE3DC" strokeOpacity={0.24} strokeWidth={2.5} strokeLinecap="round" />
                  <path d={backbone(xB)} fill="none" stroke="#AEE3DC" strokeOpacity={0.24} strokeWidth={2.5} strokeLinecap="round" />
                  {/* faint rungs */}
                  {rungs().map((r, i) => (
                    <line key={i} x1={r.x1} y1={r.y} x2={r.x2} y2={r.y} stroke="#BFE9E3" strokeOpacity={r.o} strokeWidth={1.5} />
                  ))}
                  {/* colored base-pair beads, one per dimension */}
                  {DIMENSIONS.map((d, i) => {
                    const y = beadCenters[i];
                    const lx = xA(y), rx = xB(y);
                    const on = activeKey === d.key;
                    return (
                      <motion.g
                        key={d.key}
                        initial={reduce ? false : { opacity: 0, scale: 0.6 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.5, delay: 0.15 * i, ease: [0.22, 1, 0.36, 1] }}
                        style={{ transformOrigin: `${CX}px ${y}px`, cursor: 'pointer' }}
                        onMouseEnter={() => setActiveKey(d.key)}
                        onMouseLeave={() => setActiveKey(null)}
                      >
                        <motion.g
                          animate={reduce ? undefined : { opacity: dimOpacity(d.key), scale: on ? 1.18 : 1 }}
                          transition={{ duration: 0.3, ease: 'easeOut' }}
                          style={{ transformOrigin: `${CX}px ${y}px` }}
                        >
                          {on && !reduce && (
                            <>
                              <circle cx={lx} cy={y} r={14} fill={d.color} opacity={0.16} />
                              <circle cx={rx} cy={y} r={14} fill={d.color} opacity={0.16} />
                              <circle cx={lx} cy={y} r={9} fill="none" stroke={d.color} strokeWidth={1} opacity={0.7} />
                              <circle cx={rx} cy={y} r={9} fill="none" stroke={d.color} strokeWidth={1} opacity={0.7} />
                            </>
                          )}
                          <line x1={Math.min(lx, rx)} y1={y} x2={Math.max(lx, rx)} y2={y} stroke={d.color} strokeWidth={on ? 3.5 : 2.5} strokeOpacity={0.9} />
                          <circle cx={lx} cy={y} r={9} fill={d.color} opacity={0.18} />
                          <circle cx={lx} cy={y} r={5} fill={d.color} />
                          <circle cx={rx} cy={y} r={9} fill={d.color} opacity={0.18} />
                          <circle cx={rx} cy={y} r={5} fill={d.color} />
                        </motion.g>
                      </motion.g>
                    );
                  })}
                </svg>
              </div>

              {/* ── Metric cards ── */}
              <div className="flex-1 space-y-2.5">
                {DIMENSIONS.map((d, i) => {
                  const on = activeKey === d.key;
                  return (
                    <motion.div
                      key={d.key}
                      onMouseEnter={() => setActiveKey(d.key)}
                      onMouseLeave={() => setActiveKey(null)}
                      initial={reduce ? false : { opacity: 0, x: 16 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.45, delay: 0.1 + 0.08 * i }}
                      className="relative flex items-center gap-3 rounded-2xl border pl-4 pr-4 py-3 overflow-hidden transition-all duration-300 cursor-pointer"
                      style={{
                        minHeight: ROW_H - 14,
                        opacity: dimOpacity(d.key),
                        borderColor: on ? `${d.color}66` : 'rgba(255,255,255,0.07)',
                        background: on ? `${d.color}14` : 'rgba(255,255,255,0.04)',
                        boxShadow: on ? `0 0 24px ${d.color}33` : 'none',
                      }}
                    >
                      {/* accent edge */}
                      <span className="absolute left-0 top-0 bottom-0" style={{ width: on ? 4 : 3, background: d.color }} />
                      {/* icon */}
                      <span
                        className="shrink-0 w-9 h-9 rounded-xl flex items-center justify-center"
                        style={{ backgroundColor: `${d.color}1f`, color: d.color }}
                      >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.6}>
                          {ICONS[d.icon]}
                        </svg>
                      </span>
                      {/* body */}
                      <div className="flex-1 min-w-0">
                        <div className="w-1/2">
                          <div className="flex items-baseline justify-between gap-2 mb-1.5">
                            <span className="text-sm font-semibold text-white truncate">{d.label}</span>
                            <span className="text-lg font-extrabold tabular-nums" style={{ color: d.color }}>{d.score}</span>
                          </div>
                          <div className="h-2 w-full rounded-full bg-white/[0.09] overflow-hidden">
                            <motion.div
                              className="h-full rounded-full"
                              style={{ background: d.color }}
                              initial={reduce ? false : { width: 0 }}
                              whileInView={{ width: `${d.score}%` }}
                              viewport={{ once: true }}
                              transition={{ duration: 0.9, delay: 0.25 + 0.08 * i, ease: [0.22, 1, 0.36, 1] }}
                            />
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>

              {/* ── Fixed-size detail card (right) — follows hover, never resizes ── */}
              <div className="hidden lg:flex shrink-0 items-center" style={{ width: 300 }}>
                <AnimatePresence mode="wait">
                  <motion.div
                    key={shown.key}
                    initial={reduce ? false : { opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={reduce ? undefined : { opacity: 0, y: -8 }}
                    transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
                    className="w-full rounded-2xl border p-5 flex flex-col overflow-hidden"
                    style={{
                      height: 260,                       // FIXED height — never changes
                      borderColor: `${shown.color}3a`,
                      background: `linear-gradient(160deg, ${shown.color}14, rgba(255,255,255,0.02))`,
                      boxShadow: `0 0 32px ${shown.color}1c`,
                    }}
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <span
                        className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                        style={{ backgroundColor: `${shown.color}26`, color: shown.color }}
                      >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.6}>
                          {ICONS[shown.icon]}
                        </svg>
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="text-base font-extrabold text-white leading-tight">{shown.label}</div>
                        <div className="text-[11px] text-ink-faint">
                          {activeKey ? 'Your score' : 'Hover a strand to explore'}
                        </div>
                      </div>
                      <div className="text-2xl font-extrabold tabular-nums" style={{ color: shown.color }}>
                        {shown.score}
                      </div>
                    </div>
                    <div className="h-2 rounded-full bg-white/[0.08] overflow-hidden mb-4">
                      <motion.div
                        className="h-full rounded-full"
                        style={{ background: shown.color }}
                        initial={{ width: 0 }}
                        animate={{ width: `${shown.score}%` }}
                        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                      />
                    </div>
                    <div className="text-[10px] font-bold uppercase tracking-[0.2em] mb-1.5" style={{ color: shown.color }}>
                      Why it matters
                    </div>
                    <p className="text-[13px] text-white/75 leading-relaxed overflow-hidden">{shown.why}</p>
                  </motion.div>
                </AnimatePresence>
              </div>
            </div>
          </Card>
        </Reveal>

        {/* ── Why your voice is the signal (research-grounded) ── */}
        <Reveal delay={0.15} className="mt-14">
          <div className="text-center mb-6">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-brand mb-3">
              Why your voice is the signal
            </p>
            <h3 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              The way you speak is measurable — and trainable
            </h3>
            <p className="text-sm sm:text-base text-ink-muted max-w-2xl mx-auto mt-4 leading-relaxed">
              Decades of second-language research show that the acoustic signal carries real,
              quantifiable information about how proficient — and how easy to understand — a speaker is.
              Hover any strand above to see what it tells us.
            </p>
          </div>

          {/* honest sourcing note — no overclaiming */}
          <div className="mt-2 text-center">
            <p className="text-[11px] text-ink-faint max-w-3xl mx-auto leading-relaxed">
              Grounded in peer-reviewed L2 speech research — including work on intelligibility &amp;
              comprehensibility (Munro &amp; Derwing; Kennedy &amp; Trofimovich), utterance-fluency
              prediction of perceived proficiency, and a meta-analysis finding computer-assisted
              pronunciation training outperforms traditional methods (Cohen&apos;s <em>d</em> ≈ 0.68).
              Voice-derived measures are meaningful, partial signals of speaking ability — a guide for
              practice, not a verdict.
            </p>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
