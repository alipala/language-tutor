'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Card } from '@/components/ui/card';

/* ─────────────────────────────────────────────────────────────
 *  Research page — engineering-first, honest, no academic theatre.
 *  Everything here reflects what is actually in the codebase
 *  (acoustic DSP, Azure phoneme scoring, transcript/LLM split,
 *  the real iterations we shipped). No invented papers/authors,
 *  no overclaimed science. Tone: builders who measured, tested,
 *  got it wrong, and fixed it.
 * ─────────────────────────────────────────────────────────────*/

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
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true, amount: 0 }}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

/* The six Speaking DNA dimensions, with the honest "how we measure it" line. */
const DIMENSIONS = [
  {
    name: 'Rhythm',
    color: '#4ECFBF',
    how: 'Speaking pace and pause patterns — when audio is available, blended with the real speaking-vs-silence ratio measured from the waveform.',
  },
  {
    name: 'Pronunciation',
    color: '#FFA955',
    how: 'Phoneme-level scoring from a dedicated speech engine (Azure Speech). It runs on assessments and voice checks, where we actually have your audio — not on every casual chat.',
  },
  {
    name: 'Fluency',
    color: '#5B9DFF',
    how: 'A weighted mix of hesitation markers, pace variance and pausing — the things listeners actually perceive as "flow".',
  },
  {
    name: 'Accuracy',
    color: '#FFD63A',
    how: 'Grammar correctness per turn, cross-checked against a model-graded score, plus the five error patterns that show up most for you.',
  },
  {
    name: 'Vocabulary',
    color: '#34D399',
    how: 'How varied and precise the words you reach for are — the unique-word rate across what you actually say.',
  },
  {
    name: 'Confidence',
    color: '#A78BFA',
    how: 'A proxy — not a clinical measure — built from response latency, fillers and self-corrections. We label it an estimate, because that is what it is.',
  },
];

/* The acoustic "Voice Fingerprint" signals we genuinely measure from the waveform.
   Each is a real DSP/transcript measurement, captured on assessments and voice
   checks and anchored against your first-session baseline. No invented metrics. */
const FINGERPRINT = [
  {
    name: 'Vocal Pitch',
    unit: 'Hz',
    color: '#4ECFBF',
    how: 'Your fundamental frequency — average and how much it moves. Flat pitch reads as monotone; range reads as expressive. Measured with Praat.',
  },
  {
    name: 'Voice Quality',
    unit: '%',
    color: '#A78BFA',
    how: 'Steadiness of your voice across a phrase, derived from period-level variation. Treated as an internal signal, not a clinical verdict.',
  },
  {
    name: 'Speaking Rate',
    unit: 'WPM',
    color: '#FFA955',
    how: 'Words per minute, from your transcript and the clip length. Too slow can mean searching for words; too fast can hurt clarity.',
  },
  {
    name: 'Vocal Energy',
    unit: 'dB',
    color: '#FFD63A',
    how: 'How much you project, and how much it varies. Measured as frame-by-frame loudness from the audio itself.',
  },
  {
    name: 'Speech Fluency',
    unit: 'fillers/min',
    color: '#5B9DFF',
    how: 'Hesitation markers and where you pause. Mid-sentence pauses signal formulation effort; pauses at boundaries are natural.',
  },
  {
    name: 'Voice Stability',
    unit: 'shimmer %',
    color: '#34D399',
    how: 'Amplitude consistency across the signal, from Praat. A vocal-characteristics signal we use internally — never sold as a "confidence score".',
  },
];

/* The iterations that actually happened — trial, error, fix. */
const ITERATIONS = [
  {
    tag: 'Honest scoring',
    title: 'When the numbers were too kind, we tore them up',
    body:
      'An early version of Speaking DNA produced strands sitting at 66–100% while the underlying assessment said 12–30%. The scores felt great and meant nothing. We rebuilt the pronunciation strand on a real phoneme-scoring engine so the number you see reflects how you actually sounded — even when that number is lower than you hoped.',
  },
  {
    tag: 'Transcription',
    title: 'A model that understood you but wrote down nonsense',
    body:
      'Our voice model replied perfectly to a beginner saying "Ik kijk vaak" — yet the separate transcription layer wrote "Ikkaikvak". Garbage transcripts quietly broke the displayed text, the grammar corrections, and the DNA itself. We tested transcription models on real beginner, accented speech and switched to ones that hold up on short, imperfect utterances — with an environment switch to roll back in minutes if a model regresses.',
  },
  {
    tag: 'Anti-drift',
    title: 'Refusing to score what we did not hear',
    body:
      'Live conversations stream peer-to-peer to the voice model — for privacy and latency, the raw audio never reaches our servers. That means we genuinely cannot measure your pitch or pauses from a casual chat. Rather than fake it, we "pin" the acoustic strands: they hold their last real value instead of drifting on guesses. Acoustic measurement happens on assessments and periodic voice checks, where we actually have the audio.',
  },
  {
    tag: 'Calibration',
    title: 'Tuned against real sessions, not a lab',
    body:
      'Energy thresholds, pause-length cutoffs, minimum-duration gates, smoothing rates — none of these came from a paper. They came from running the pipeline on real sessions across seven languages and adjusting until the output matched what a human would say about that recording. Every dimension updates as a slow moving average, so one odd session can never whiplash your profile.',
  },
];

/* The engineering principles we hold ourselves to. */
const PRINCIPLES = [
  {
    title: 'Measure, don’t guess',
    body:
      'Where we have your audio, we run genuine signal processing — pitch, energy, pauses, voice quality — not a language model guessing how you probably sounded. Where we only have text, we say so.',
  },
  {
    title: 'Audio never touches our disks',
    body:
      'Acoustic analysis happens entirely in memory. The only temporary file we ever write is the one a speech library strictly requires, and it is deleted the instant analysis finishes. We store numbers, never recordings.',
  },
  {
    title: 'No overclaiming',
    body:
      'We compute voice-quality signals like jitter and shimmer, but we treat them as internal heuristics — not as a "science of confidence". We will not dress up a vocal-health metric as a proficiency score.',
  },
  {
    title: 'Every change is reversible',
    body:
      'Models, thresholds and scoring methods sit behind switches. If a new transcription model or scoring change makes things worse for real learners, we roll it back in minutes — no redeploy, no waiting.',
  },
];

const Research: React.FC = () => {
  return (
    <div className="min-h-screen pt-20 sm:pt-24" style={{ backgroundColor: '#0A0A0F' }}>
      {/* ── Hero ── */}
      <section className="py-16 sm:py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <Reveal>
            <span className="inline-flex items-center gap-2 rounded-full border border-brand/30 bg-brand/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-brand mb-6">
              How we build it
            </span>
            <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-6">
              <span
                style={{
                  background: 'linear-gradient(90deg, #4ECFBF, #FFD63A)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                We’re engineers, not a research lab.
              </span>
            </h1>
            <p className="text-lg sm:text-xl text-ink-muted max-w-2xl mx-auto leading-relaxed">
              We didn’t arrive at Speaking DNA through a stack of papers. We built real speech
              pipelines, ran them on thousands of real sessions across seven languages, got plenty
              of things wrong, measured what actually happened, and fixed them. This page is an
              honest look at how the feature really works.
            </p>
          </Reveal>
        </div>
      </section>

      {/* ── What Speaking DNA actually measures ── */}
      <section className="py-12 sm:py-16 px-4" style={{ backgroundColor: '#0E0E1A' }}>
        <div className="max-w-5xl mx-auto">
          <Reveal className="text-center mb-12">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-brand mb-3">
              The measurement
            </p>
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-white tracking-tight">
              Six dimensions, and exactly how we get each one
            </h2>
            <p className="text-sm sm:text-base text-ink-muted max-w-2xl mx-auto mt-4 leading-relaxed">
              No black box. Some of these come from real acoustic measurement of your voice; others
              from analysing what you actually said. We tell you which is which.
            </p>
          </Reveal>

          <Reveal delay={0.1} className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {DIMENSIONS.map((d) => (
              <Card key={d.name} elevation="rest" className="h-full">
                <div className="flex items-center gap-2.5 mb-3">
                  <span
                    className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{ backgroundColor: d.color, boxShadow: `0 0 10px ${d.color}80` }}
                  />
                  <span className="text-white font-bold text-sm">{d.name}</span>
                </div>
                <p className="text-ink-muted text-xs leading-relaxed">{d.how}</p>
              </Card>
            ))}
          </Reveal>

          <Reveal delay={0.15}>
            <p className="text-[11px] text-ink-faint max-w-3xl mx-auto leading-relaxed text-center mt-8">
              Acoustic signals (pitch, energy, pauses, voice quality) are real digital-signal-processing
              measurements from your audio. Speaking rate and the proficiency scores are derived from your
              transcript and a language model. We never blur the line between the two.
            </p>
          </Reveal>
        </div>
      </section>

      {/* ── Voice Fingerprint (acoustic signals) ── */}
      <section className="py-16 sm:py-20 px-4" style={{ backgroundColor: '#0A0A0F' }}>
        <div className="max-w-5xl mx-auto">
          <Reveal className="text-center mb-12">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-brand mb-3">
              Your Voice Fingerprint
            </p>
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-white tracking-tight">
              Six signals we read straight from your voice
            </h2>
            <p className="text-sm sm:text-base text-ink-muted max-w-2xl mx-auto mt-4 leading-relaxed">
              When we have your audio — on speaking assessments and periodic voice checks — we run
              real signal processing over the waveform. These are the raw acoustic signals behind the
              six dimensions, captured and anchored against your very first session so we can see how
              you change.
            </p>
          </Reveal>

          <Reveal delay={0.1} className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {FINGERPRINT.map((s) => (
              <Card key={s.name} elevation="raised" className="h-full">
                <div className="flex items-baseline justify-between mb-3">
                  <div className="flex items-center gap-2.5">
                    <span
                      className="w-2.5 h-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: s.color, boxShadow: `0 0 10px ${s.color}80` }}
                    />
                    <span className="text-white font-bold text-sm">{s.name}</span>
                  </div>
                  <span
                    className="text-[10px] font-mono font-semibold uppercase tracking-wide"
                    style={{ color: s.color }}
                  >
                    {s.unit}
                  </span>
                </div>
                <p className="text-ink-muted text-xs leading-relaxed">{s.how}</p>
              </Card>
            ))}
          </Reveal>

          <Reveal delay={0.15}>
            <p className="text-[11px] text-ink-faint max-w-3xl mx-auto leading-relaxed text-center mt-8">
              We capture these where the audio actually reaches us — assessments and voice checks — and
              hold them against your baseline. We don’t pretend to measure your pitch or energy from a
              casual live chat that never leaves your device.
            </p>
          </Reveal>
        </div>
      </section>

      {/* ── How we got here (iterations) ── */}
      <section className="py-16 sm:py-20 px-4" style={{ backgroundColor: '#0E0E1A' }}>
        <div className="max-w-4xl mx-auto">
          <Reveal className="text-center mb-12">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-brand mb-3">
              Trial, error, fix
            </p>
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-white tracking-tight">
              The things we got wrong first
            </h2>
            <p className="text-sm sm:text-base text-ink-muted max-w-2xl mx-auto mt-4 leading-relaxed">
              The feature you use today is the version that survived contact with real learners.
              Here are four of the corrections that shaped it.
            </p>
          </Reveal>

          <div className="space-y-4">
            {ITERATIONS.map((it, i) => (
              <Reveal key={it.title} delay={0.05 * i}>
                <Card elevation="raised" className="relative overflow-hidden">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-brand">
                    {it.tag}
                  </span>
                  <h3 className="text-lg sm:text-xl font-bold text-white mt-1.5 mb-2">{it.title}</h3>
                  <p className="text-ink-muted text-sm leading-relaxed">{it.body}</p>
                </Card>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ── Principles ── */}
      <section className="py-16 sm:py-20 px-4" style={{ backgroundColor: '#0A0A0F' }}>
        <div className="max-w-5xl mx-auto">
          <Reveal className="text-center mb-12">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-brand mb-3">
              How we hold the line
            </p>
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-white tracking-tight">
              The rules we build by
            </h2>
          </Reveal>

          <Reveal delay={0.1} className="grid sm:grid-cols-2 gap-4">
            {PRINCIPLES.map((p) => (
              <Card key={p.title} elevation="rest" interactive className="h-full min-h-[140px]">
                <div className="text-white font-bold text-sm mb-2">{p.title}</div>
                <p className="text-ink-muted text-xs leading-relaxed">{p.body}</p>
              </Card>
            ))}
          </Reveal>
        </div>
      </section>

      {/* ── Honest footer note ── */}
      <section className="py-16 sm:py-20 px-4" style={{ backgroundColor: '#0E0E1A' }}>
        <div className="max-w-3xl mx-auto text-center">
          <Reveal>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white mb-5 tracking-tight">
              Grounded in the field, honest about the limits
            </h2>
            <p className="text-ink-muted leading-relaxed mb-4">
              Our choices line up with what second-language research consistently finds: that
              pronunciation feedback works, that fluency is really about pace and where you pause,
              and that intelligibility matters far more than erasing an accent. We lean on that
              evidence — but the engineering, the testing, and the calibration are ours.
            </p>
            <p className="text-sm text-ink-faint leading-relaxed">
              And where the science gets thin, we stop. We don’t claim to read your emotions from
              your voice or score your character. We measure speaking, carefully, and we tell you the
              truth about what the numbers mean.
            </p>
          </Reveal>
        </div>
      </section>
    </div>
  );
};

export default Research;
