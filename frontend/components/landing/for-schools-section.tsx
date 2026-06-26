'use client';

import { motion } from 'framer-motion';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

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
      initial={{ opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

const VALUE_PROPS = [
  {
    title: 'Cohort dashboards',
    body: 'Track every learner’s minutes, streaks, and CEFR progress from one institution view.',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
      </svg>
    ),
  },
  {
    title: 'Tutor seats & AI reports',
    body: 'Give tutors their own portal with AI-generated session reports and learner notifications.',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
      </svg>
    ),
  },
  {
    title: 'CEFR-aligned content',
    body: 'Conversations, challenges, news and Story Worlds tuned A1–C2 to your curriculum.',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
      </svg>
    ),
  },
  {
    title: 'EU data handling',
    body: 'GDPR-compliant by design, with clear data processing for minors and institutions.',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.746 3.746 0 0121 12z" />
      </svg>
    ),
  },
];

const DEMO_MAILTO =
  'mailto:hello@mytacoai.com?subject=MyTaco%20for%20Schools%20%E2%80%94%20Demo%20request&body=Hi%20MyTaco%20team%2C%0A%0AWe%27d%20like%20a%20demo%20for%20our%20institution.%0A%0ASchool%2Forganisation%3A%0ANumber%20of%20learners%3A%0ATarget%20language(s)%3A%0APreferred%20time%3A%0A';

export default function ForSchoolsSection() {
  return (
    <section id="for-schools" className="relative py-24 px-4" style={{ background: '#0A0A0F' }}>
      <div className="max-w-6xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* ── Left: pitch ── */}
          <Reveal>
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-brand mb-4">
              For schools & institutions
            </p>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white leading-tight tracking-tight mb-5">
              Give every learner a{' '}
              <span
                style={{
                  background: 'linear-gradient(90deg, #4ECFBF, #7C3AED)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                speaking partner
              </span>
            </h2>
            <p className="text-base sm:text-lg text-ink-muted leading-relaxed mb-8 max-w-lg">
              Roll MyTaco out across your classes with cohort dashboards, tutor seats, AI session
              reports, and CEFR-aligned content — all on a GDPR-compliant, EU-friendly platform.
            </p>

            <div className="flex flex-col sm:flex-row gap-3">
              <Button asChild variant="primary" size="touch">
                <a href={DEMO_MAILTO}>Book a Demo</a>
              </Button>
            </div>
          </Reveal>

          {/* ── Right: value-prop cards ── */}
          <Reveal delay={0.1} className="grid sm:grid-cols-2 gap-4">
            {VALUE_PROPS.map((vp) => (
              <Card key={vp.title} elevation="raised" interactive className="min-h-[150px]">
                <div className="w-10 h-10 rounded-2xl bg-brand/12 text-brand flex items-center justify-center mb-3">
                  {vp.icon}
                </div>
                <div className="text-white font-bold text-sm mb-1.5">{vp.title}</div>
                <p className="text-ink-muted text-xs leading-relaxed">{vp.body}</p>
              </Card>
            ))}
          </Reveal>
        </div>
      </div>
    </section>
  );
}
