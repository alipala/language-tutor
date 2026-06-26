'use client';

import { motion } from 'framer-motion';
import { Card } from '@/components/ui/card';

const STORY = '#E84C88'; // Story Worlds magenta

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

// Mock episode-drip rail: 5 episodes, today's unlocked, rest time-locked
const EPISODES = [
  { n: 1, state: 'done' as const },
  { n: 2, state: 'done' as const },
  { n: 3, state: 'today' as const },
  { n: 4, state: 'locked' as const },
  { n: 5, state: 'finale' as const },
];

const GENRES = [
  'Mystery', 'Romance', 'Sci-Fi', 'Fantasy', 'Adventure', 'Thriller',
  'Horror', 'Comedy', 'Drama', 'Detective', 'Travel', 'School Life',
];

export default function StoryWorldsSection() {
  return (
    <section id="story-worlds" className="relative py-16 sm:py-24 px-4" style={{ background: '#0D0D18' }}>
      {/* magenta ambient glow */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            'radial-gradient(ellipse 60% 50% at 80% 0%, rgba(232,76,136,0.10) 0%, transparent 60%)',
        }}
      />
      <div className="relative max-w-6xl mx-auto">
        <Reveal className="text-center mb-12">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] mb-4" style={{ color: STORY }}>
            New · Flagship game
          </p>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white leading-tight tracking-tight">
            Live a story in the language{' '}
            <br className="hidden sm:block" />
            <span
              style={{
                background: `linear-gradient(90deg, ${STORY}, #F75A5A)`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              you&apos;re learning
            </span>
          </h2>
          <p className="text-base sm:text-lg text-ink-muted max-w-2xl mx-auto mt-5 leading-relaxed">
            Story Worlds is a single-player, Netflix-style story game. Pick a genre, then work your way
            through the plot scene by scene — your AI scene partner reacts to every line you write in the
            target language. A new episode unlocks every day.
          </p>
        </Reveal>

        <Reveal delay={0.1}>
          <Card elevation="hero" category="story" className="overflow-hidden">
            <div className="grid lg:grid-cols-2 gap-6 lg:gap-8 items-center">
              {/* ── Left: cover-art mock ── */}
              <div className="relative">
                <div
                  className="relative aspect-[4/3] rounded-2xl overflow-hidden border"
                  style={{
                    borderColor: 'rgba(232,76,136,0.30)',
                    background:
                      'linear-gradient(160deg, #3a1f2e 0%, #2a1420 55%, #1a0e16 100%)',
                  }}
                >
                  {/* faux illustration: layered glows + skyline */}
                  <div
                    className="absolute inset-0"
                    style={{
                      background:
                        'radial-gradient(circle at 30% 30%, rgba(247,90,90,0.35) 0%, transparent 45%), radial-gradient(circle at 75% 60%, rgba(232,76,136,0.40) 0%, transparent 50%)',
                    }}
                  />
                  <div className="absolute bottom-0 left-0 right-0 h-1/2 flex items-end justify-center gap-1 px-6 opacity-60">
                    {[40, 70, 55, 90, 50, 80, 60, 100, 45, 75].map((h, i) => (
                      <div
                        key={i}
                        className="flex-1 rounded-t-sm"
                        style={{ height: `${h}%`, background: 'rgba(0,0,0,0.55)' }}
                      />
                    ))}
                  </div>
                  {/* episode badge */}
                  <div
                    className="absolute top-3 left-3 text-[10px] font-bold uppercase tracking-wider rounded-full px-3 py-1"
                    style={{ background: 'rgba(0,0,0,0.5)', color: STORY }}
                  >
                    Episode 3 · The Night Market
                  </div>
                  {/* title */}
                  <div className="absolute bottom-4 left-4 right-4">
                    <div className="text-white font-extrabold text-xl sm:text-2xl leading-tight drop-shadow-lg">
                      Whispers in Lisbon
                    </div>
                    <div className="text-white/70 text-xs mt-1">A mystery series · B1 · 🇵🇹 Portuguese</div>
                  </div>
                </div>
                <div className="text-center text-[10px] text-ink-faint mt-2">
                  Every episode ships with its own AI-generated cover art
                </div>
              </div>

              {/* ── Right: mechanics ── */}
              <div>
                {/* daily-drip rail */}
                <div className="mb-6">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-ink-faint mb-3">
                    One new episode per day
                  </div>
                  <div className="flex items-center gap-2">
                    {EPISODES.map((ep) => {
                      const isActive = ep.state === 'today';
                      const isDone = ep.state === 'done';
                      const isFinale = ep.state === 'finale';
                      return (
                        <div key={ep.n} className="flex-1 flex flex-col items-center gap-1.5">
                          <div
                            className="w-full h-1.5 rounded-full"
                            style={{
                              background: isDone || isActive ? STORY : 'rgba(255,255,255,0.10)',
                            }}
                          />
                          <div
                            className="w-9 h-9 rounded-xl flex items-center justify-center text-xs font-bold border"
                            style={{
                              background: isActive ? STORY : 'rgba(255,255,255,0.04)',
                              color: isActive ? '#0A0A0F' : isDone ? STORY : 'rgba(255,255,255,0.40)',
                              borderColor: isActive || isDone ? 'rgba(232,76,136,0.40)' : 'rgba(255,255,255,0.10)',
                            }}
                          >
                            {isDone ? '✓' : isFinale ? '★' : ep.n}
                          </div>
                          <span className="text-[10px] text-ink-faint">
                            {isActive ? 'Today' : isFinale ? 'Finale' : isDone ? 'Done' : 'Soon'}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* feature bullets */}
                <ul className="space-y-3 mb-6">
                  {[
                    'CEFR level-adaptive — the same world plays harder at B1 than A1',
                    'Press-and-hold Reveal hints — peek, then recall and type it yourself',
                    'Earn XP and level up · cinematic finale when you complete a season',
                    'You can never get stuck — gentle escalation rescues every scene',
                  ].map((t) => (
                    <li key={t} className="flex items-start gap-2.5 text-sm text-ink-muted">
                      <span
                        className="mt-0.5 shrink-0 w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold"
                        style={{ background: 'rgba(232,76,136,0.15)', color: STORY }}
                      >
                        ✓
                      </span>
                      {t}
                    </li>
                  ))}
                </ul>

                {/* genre chips */}
                <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-ink-faint mb-2">
                  Dozens of AI-generated stories across 20 genres
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {GENRES.map((g) => (
                    <span
                      key={g}
                      className="text-[10px] rounded-full px-2.5 py-1 font-medium border"
                      style={{
                        borderColor: 'rgba(232,76,136,0.25)',
                        color: 'rgba(255,255,255,0.65)',
                        background: 'rgba(232,76,136,0.08)',
                      }}
                    >
                      {g}
                    </span>
                  ))}
                  <span className="text-[10px] rounded-full px-2.5 py-1 font-medium text-ink-faint">
                    + more, and growing
                  </span>
                </div>
              </div>
            </div>
          </Card>
        </Reveal>
      </div>
    </section>
  );
}
