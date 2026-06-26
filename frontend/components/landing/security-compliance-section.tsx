'use client';

import { motion } from 'framer-motion';
import { Card } from '@/components/ui/card';

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

// Honest, verifiable claims only — no fabricated certifications.
const ITEMS = [
  {
    title: 'GDPR-compliant',
    body: 'Built to GDPR from the ground up — lawful processing, data minimisation, and the right to erasure.',
    href: '/gdpr',
  },
  {
    title: 'Transparent data handling',
    body: 'Clear privacy and cookie policies set out exactly what we collect and why.',
    href: '/privacy',
  },
  {
    title: 'Responsible AI',
    body: 'How we use AI for tutoring, assessment, and content — and the guardrails around it.',
    href: '/responsible-ai',
  },
  {
    title: 'Registered company',
    body: 'Operated by Big Davinci · KVK 90200004, an EU-registered business.',
    href: null,
  },
];

export default function SecurityComplianceSection() {
  return (
    <section id="security" className="relative py-14 sm:py-20 px-4" style={{ background: '#0D0D18' }}>
      <div className="max-w-5xl mx-auto">
        <Reveal className="text-center mb-12">
          <div className="inline-flex items-center gap-2 rounded-full border border-brand/30 bg-brand/10 px-4 py-1.5 mb-4">
            <svg className="w-4 h-4 text-brand" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.746 3.746 0 0121 12z" />
            </svg>
            <span className="text-xs font-semibold uppercase tracking-widest text-brand">Security & Compliance</span>
          </div>
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-white tracking-tight">
            Safe for learners. Ready for institutions.
          </h2>
          <p className="text-sm sm:text-base text-ink-muted max-w-2xl mx-auto mt-4 leading-relaxed">
            We keep it honest: here&apos;s exactly how we handle your data and our AI.
          </p>
        </Reveal>

        <Reveal delay={0.1} className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {ITEMS.map((item) => {
            const inner = (
              <Card elevation="rest" interactive={!!item.href} className="h-full min-h-[160px]">
                <div className="text-white font-bold text-sm mb-2">{item.title}</div>
                <p className="text-ink-muted text-xs leading-relaxed">{item.body}</p>
                {item.href && (
                  <div className="text-brand text-xs font-semibold mt-3">Learn more →</div>
                )}
              </Card>
            );
            return item.href ? (
              <a key={item.title} href={item.href} className="block">
                {inner}
              </a>
            ) : (
              <div key={item.title}>{inner}</div>
            );
          })}
        </Reveal>
      </div>
    </section>
  );
}
