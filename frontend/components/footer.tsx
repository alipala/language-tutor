'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Logo } from './logo';
import {
  Mail, Phone, MapPin,
  Linkedin, Youtube, Instagram,
  ChevronRight, Heart, Shield,
  Users, BookOpen, Globe, MessageSquare, Star,
} from 'lucide-react';

const NAV_SECTIONS = [
  {
    title: 'Company',
    links: [
      { name: 'About Us',   href: '/about',          icon: Users    },
      { name: 'Press Kit',  href: '/press',           icon: Star     },
      { name: 'Blog',       href: '/blog',            icon: BookOpen },
    ],
  },
  {
    title: 'Product',
    links: [
      { name: 'For Schools',    href: '/institution/login', icon: Users   },
      { name: 'Responsible AI', href: '/responsible-ai',    icon: Shield  },
      { name: 'Help Center',    href: '/help',              icon: MessageSquare },
    ],
  },
  {
    title: 'Legal',
    links: [
      { name: 'Privacy Policy',  href: '/privacy', icon: Shield   },
      { name: 'Terms of Service',href: '/terms',   icon: BookOpen },
      { name: 'Cookie Policy',   href: '/cookies', icon: Globe    },
      { name: 'GDPR',            href: '/gdpr',    icon: Shield   },
    ],
  },
];

const SOCIAL = [
  { name: 'LinkedIn',  href: 'https://www.linkedin.com/company/mytaco-ai', icon: Linkedin  },
  { name: 'Instagram', href: 'https://www.instagram.com/mytacoai/',        icon: Instagram },
  { name: 'YouTube',   href: 'https://www.youtube.com/@MyTacoAI',          icon: Youtube   },
];

const STORE_LINKS = [
  {
    label: 'App Store',
    href: 'https://apps.apple.com/br/app/mytaco/id6757149290?l=en-GB',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
        <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z" />
      </svg>
    ),
  },
  {
    label: 'Google Play',
    href: 'https://play.google.com/store/apps/details?id=com.bigdavinci.MyTacoAI',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
        <path d="M3.18 23.76c.34.19.73.23 1.1.12l12.02-12.02-2.49-2.49L3.18 23.76zM20.54 10.23l-2.93-1.65-2.81 2.81 2.81 2.81 2.96-1.67c.84-.47.84-1.83-.03-2.3zM1.91.17C1.65.45 1.5.86 1.5 1.38v21.24c0 .52.15.93.41 1.21l.07.06L13.17 12 1.98.11l-.07.06zM14.38 12l2.49-2.49L4.28.23c-.35-.2-.73-.24-1.1-.14L14.38 12z" />
      </svg>
    ),
  },
];

export default function Footer() {
  const [email, setEmail]               = useState('');
  const [isSubscribing, setIsSubscribing] = useState(false);
  const [subscribeState, setSubscribeState] = useState<'idle' | 'success' | 'error'>('idle');
  const [message, setMessage]           = useState('');

  const handleSubscribe = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;

    setIsSubscribing(true);
    try {
      const apiUrl = process.env.NODE_ENV === 'production'
        ? 'https://taco.up.railway.app'
        : 'http://localhost:8000';

      const res  = await fetch(`${apiUrl}/api/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim() }),
      });
      const data = await res.json();

      if (res.ok && data.success) {
        setSubscribeState('success');
        setMessage(data.already_subscribed ? 'Already subscribed!' : 'You\'re in! Welcome to the community.');
        setEmail('');
      } else {
        setSubscribeState('error');
        setMessage(data.detail || 'Something went wrong. Try again.');
      }
    } catch {
      setSubscribeState('error');
      setMessage('Network error. Check your connection.');
    } finally {
      setIsSubscribing(false);
      setTimeout(() => setSubscribeState('idle'), 5000);
    }
  };

  return (
    <footer
      className="relative border-t overflow-hidden"
      style={{ background: '#080810', borderColor: 'rgba(255,255,255,0.06)' }}
    >
      {/* Ambient top glow */}
      <div
        className="pointer-events-none absolute top-0 inset-x-0 h-px"
        style={{
          background: 'linear-gradient(to right, transparent 0%, rgba(78,207,191,0.5) 30%, rgba(124,58,237,0.4) 70%, transparent 100%)',
          boxShadow: '0 0 40px 6px rgba(78,207,191,0.15)',
        }}
      />

      {/* ── Main grid ─────────────────────────────────────────── */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 pt-12 sm:pt-16 pb-8 sm:pb-10">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-8 lg:gap-12">

          {/* Brand column */}
          <div className="md:col-span-2 lg:col-span-4">
            <div className="mb-5 scale-90 origin-left">
              <Logo variant="full" context="footer" />
            </div>

            <p className="text-white/40 text-sm leading-relaxed mb-8 max-w-xs">
              AI-powered language learning built from your Voice DNA.
              Personalised plans, daily missions, and real conversations
              that evolve with every word you speak.
            </p>

            {/* Contact */}
            <div className="space-y-3 mb-8">
              {[
                { icon: Mail,    text: 'hello@mytacoai.com',  href: 'mailto:hello@mytacoai.com'  },
                { icon: Phone,   text: '+31 6 21 18 55 93',   href: 'tel:+31621185593'            },
                { icon: MapPin,  text: 'Amsterdam, NL',       href: null                          },
              ].map(({ icon: Icon, text, href }) => (
                <div key={text} className="flex items-center gap-3 text-sm">
                  <Icon className="w-4 h-4 text-brand shrink-0" />
                  {href
                    ? <a href={href} className="text-white/40 hover:text-white/80 transition-colors">{text}</a>
                    : <span className="text-white/40">{text}</span>
                  }
                </div>
              ))}
            </div>

            {/* Social icons */}
            <div className="flex gap-3">
              {SOCIAL.map(s => (
                <a
                  key={s.name}
                  href={s.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={s.name}
                  className="w-9 h-9 rounded-xl border border-white/[0.08] bg-white/[0.04] flex items-center justify-center text-white/40 hover:text-white hover:border-brand/40 hover:bg-brand/10 transition-all duration-200"
                >
                  <s.icon className="w-4 h-4" />
                </a>
              ))}
            </div>
          </div>

          {/* Nav columns */}
          <div className="md:col-span-2 lg:col-span-5 grid grid-cols-2 sm:grid-cols-3 gap-4 sm:gap-6 lg:gap-8">
            {NAV_SECTIONS.map(section => (
              <div key={section.title}>
                <h4 className="text-[11px] font-bold uppercase tracking-[0.2em] text-white/30 mb-5">
                  {section.title}
                </h4>
                <ul className="space-y-3">
                  {section.links.map(link => (
                    <li key={link.name}>
                      <a
                        href={link.href}
                        className="group flex items-center gap-2 text-sm text-white/45 hover:text-white transition-colors duration-200"
                      >
                        <ChevronRight className="w-3 h-3 opacity-0 group-hover:opacity-100 -ml-1 transition-all duration-200 group-hover:translate-x-0.5 text-brand" />
                        {link.name}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* Newsletter + Store */}
          <div className="md:col-span-2 lg:col-span-3">
            <h4 className="text-[11px] font-bold uppercase tracking-[0.2em] text-white/30 mb-5">
              Stay Updated
            </h4>
            <p className="text-sm text-white/40 mb-4 leading-relaxed">
              Language tips, feature drops, and exclusive content.
            </p>

            <form onSubmit={handleSubscribe} className="mb-6">
              <div className="flex flex-col gap-2">
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  disabled={isSubscribing}
                  required
                  className="w-full px-4 py-2.5 rounded-xl text-sm text-white placeholder-white/25 border border-white/[0.08] bg-white/[0.04] focus:outline-none focus:border-brand/50 focus:bg-white/[0.06] transition-all duration-200 disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={isSubscribing}
                  className="w-full py-2.5 rounded-xl text-sm font-semibold bg-brand text-[#080810] hover:bg-[#3dc4b5] active:scale-[0.98] transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {isSubscribing ? 'Subscribing…' : 'Subscribe'}
                </button>
              </div>

              <AnimatePresence>
                {subscribeState !== 'idle' && (
                  <motion.p
                    initial={{ opacity: 0, y: -6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className={`mt-2 text-xs ${subscribeState === 'success' ? 'text-cat-news' : 'text-cat-hearts'}`}
                  >
                    {message}
                  </motion.p>
                )}
              </AnimatePresence>
            </form>

            {/* App store badges */}
            <h4 className="text-[11px] font-bold uppercase tracking-[0.2em] text-white/30 mb-4">
              Download the App
            </h4>
            <div className="flex flex-col gap-2">
              {STORE_LINKS.map(s => (
                <a
                  key={s.label}
                  href={s.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 px-4 py-2.5 rounded-xl border border-white/[0.08] bg-white/[0.03] text-sm font-semibold text-white/70 hover:text-white hover:border-brand/30 hover:bg-brand/8 transition-all duration-200 group"
                >
                  <span className="text-brand group-hover:scale-110 transition-transform">{s.icon}</span>
                  {s.label}
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Divider ────────────────────────────────────────────── */}
      <div
        className="mx-6"
        style={{ height: 1, background: 'linear-gradient(to right, transparent, rgba(255,255,255,0.06) 20%, rgba(255,255,255,0.06) 80%, transparent)' }}
      />

      {/* ── Bottom bar ─────────────────────────────────────────── */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-5 sm:py-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">

          <div className="flex flex-col sm:flex-row items-center gap-1 sm:gap-3 text-xs text-white/25">
            <span className="flex items-center gap-1.5">
              © {new Date().getFullYear()} MyTaco AI · Made with
              <Heart className="w-3 h-3 text-cat-hearts fill-current" />
              for language learners worldwide
            </span>
            <span className="hidden sm:inline opacity-40">·</span>
            <span>Big Davinci · KVK 90200004</span>
          </div>

          <div className="flex flex-wrap items-center gap-3 sm:gap-4">
            {[
              { label: 'Privacy',  href: '/privacy' },
              { label: 'Terms',    href: '/terms'   },
              { label: 'Cookies',  href: '/cookies' },
              { label: 'GDPR',     href: '/gdpr'    },
            ].map(l => (
              <a
                key={l.label}
                href={l.href}
                className="text-xs text-white/25 hover:text-white/60 transition-colors duration-200"
              >
                {l.label}
              </a>
            ))}
            <a
              href="/gdpr"
              className="hidden sm:flex items-center gap-1.5 text-xs text-white/25 hover:text-white/60 transition-colors duration-200"
            >
              <Shield className="w-3 h-3 text-brand" />
              GDPR · EU
            </a>
          </div>

        </div>
      </div>

      {/* Scroll-to-top button — sits ABOVE the chat FAB on mobile (bottom-20)
          so the two fixed bottom-right widgets don't collide; 44px touch target */}
      <motion.button
        className="fixed bottom-20 right-4 sm:bottom-8 sm:right-8 w-11 h-11 rounded-full border border-brand/30 bg-brand/10 backdrop-blur-md flex items-center justify-center text-brand hover:bg-brand hover:text-[#080810] hover:scale-110 active:scale-95 transition-all duration-200 z-50"
        onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1 }}
        aria-label="Scroll to top"
      >
        <ChevronRight className="w-4 h-4 -rotate-90" />
      </motion.button>
    </footer>
  );
}
