'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const FAQS = [
  {
    q: 'What is Speaking DNA and how does it work?',
    a: 'Speaking DNA is your unique voice profile. MyTaco AI analyses 6 dimensions of how you actually speak — Rhythm, Confidence, Vocabulary, Accuracy, Learning speed, and Emotional expression — and maps them into a radar profile. This profile updates after every conversation, so your plan always reflects where you really are, not where you started.',
  },
  {
    q: 'How does the real-time conversation work?',
    a: 'Your voice streams directly to your AI tutor in real time — no typing, no lag, just speak naturally. The AI responds instantly, corrects you mid-conversation if needed, and provides post-session feedback on pronunciation, grammar, and fluency.',
  },
  {
    q: 'What languages can I learn?',
    a: 'English, Spanish, French, German, Dutch, and Portuguese are currently available. Each language is supported across all 6 CEFR proficiency levels (A1 to C2), with daily news sessions, curated challenges, and personalised learning plans for every level.',
  },
  {
    q: 'What are Daily Missions and Hearts?',
    a: 'Every day MyTaco generates three missions — Bronze, Silver, and Gold — based on your weakest DNA strands. Hearts are your focus energy for challenges: you start with 5 per challenge type and lose one for each wrong answer. Build a 5-correct streak to earn a Streak Shield that protects you from losing a heart.',
  },
  {
    q: 'How is my voice data handled?',
    a: 'Your voice is processed in real time for speech recognition and never permanently stored as raw audio. Transcripts are saved to your profile so you can review session history. You can delete your account and all associated data at any time from the app settings.',
  },
];

export default function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <div className="w-full max-w-2xl mx-auto px-2 sm:px-0">
      <div className="space-y-2">
        {FAQS.map((faq, i) => {
          const isOpen = openIndex === i;
          return (
            <motion.div
              key={i}
              className="rounded-2xl border overflow-hidden"
              style={{ backgroundColor: '#13131F' }}
              animate={{ borderColor: isOpen ? 'rgba(78,207,191,0.4)' : 'rgba(255,255,255,0.10)' }}
              transition={{ duration: 0.2 }}
            >
              <button
                onClick={() => setOpenIndex(isOpen ? null : i)}
                aria-expanded={isOpen}
                aria-controls={`faq-panel-${i}`}
                id={`faq-trigger-${i}`}
                className="w-full flex items-center justify-between gap-3 px-4 sm:px-6 py-4 sm:py-5 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-inset rounded-2xl"
              >
                <span className="text-sm sm:text-base font-semibold text-white/85">{faq.q}</span>
                <motion.div
                  aria-hidden="true"
                  className="shrink-0 w-6 h-6 rounded-full border border-white/20 flex items-center justify-center"
                  animate={{ rotate: isOpen ? 45 : 0, borderColor: isOpen ? 'rgba(78,207,191,0.5)' : 'rgba(255,255,255,0.2)' }}
                  transition={{ duration: 0.25 }}
                >
                  <svg className="w-3 h-3 text-white/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                  </svg>
                </motion.div>
              </button>
              <AnimatePresence initial={false}>
                {isOpen && (
                  <motion.div
                    id={`faq-panel-${i}`}
                    role="region"
                    aria-labelledby={`faq-trigger-${i}`}
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                  >
                    <div className="px-4 sm:px-6 pb-4 sm:pb-5 text-sm text-ink-muted leading-relaxed border-t border-white/[0.06] pt-4">
                      {faq.a}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
