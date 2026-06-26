/**
 * Bounded category-color system (the "Duolingo-disciplined" palette).
 *
 * Each landing-page feature owns exactly ONE color, used consistently
 * everywhere that feature appears. Color carries IDENTITY, never elevation —
 * elevation comes from the shared surface + shadow ramp (see <Card />).
 *
 * Hex values are kept here (not Tailwind classes) so the Card primitive can
 * apply them via inline style/CSS-vars without Tailwind purging dynamic
 * class names. They mirror the --cat-* tokens in globals.css.
 */

export type CategoryKey =
  | 'dna'
  | 'missions'
  | 'challenge'
  | 'hearts'
  | 'news'
  | 'story'
  | 'conversation';

export interface CategoryDef {
  /** Solid accent (text, icons, data-viz). */
  color: string;
  /** Faint fill behind icon chips / pills. */
  tint: string;
  /** Resting border tint. */
  line: string;
  /** Hover glow. */
  glow: string;
  label: string;
}

export const CATEGORY: Record<CategoryKey, CategoryDef> = {
  dna: {
    color: '#4ECFBF',
    tint: 'rgba(78,207,191,0.12)',
    line: 'rgba(78,207,191,0.22)',
    glow: '0 0 28px rgba(78,207,191,0.18)',
    label: 'Speaking DNA',
  },
  conversation: {
    color: '#4ECFBF',
    tint: 'rgba(78,207,191,0.12)',
    line: 'rgba(78,207,191,0.22)',
    glow: '0 0 28px rgba(78,207,191,0.18)',
    label: 'Real-Time Conversation',
  },
  missions: {
    color: '#F59E0B',
    tint: 'rgba(245,158,11,0.12)',
    line: 'rgba(245,158,11,0.22)',
    glow: '0 0 28px rgba(245,158,11,0.16)',
    label: 'Daily Missions',
  },
  challenge: {
    color: '#7C3AED',
    tint: 'rgba(124,58,237,0.14)',
    line: 'rgba(124,58,237,0.24)',
    glow: '0 0 28px rgba(124,58,237,0.18)',
    label: 'Challenges',
  },
  hearts: {
    color: '#EF4444',
    tint: 'rgba(239,68,68,0.12)',
    line: 'rgba(239,68,68,0.22)',
    glow: '0 0 28px rgba(239,68,68,0.16)',
    label: 'Heart System',
  },
  news: {
    color: '#10B981',
    tint: 'rgba(16,185,129,0.12)',
    line: 'rgba(16,185,129,0.22)',
    glow: '0 0 28px rgba(16,185,129,0.16)',
    label: 'News Sessions',
  },
  story: {
    color: '#E84C88',
    tint: 'rgba(232,76,136,0.14)',
    line: 'rgba(232,76,136,0.26)',
    glow: '0 0 32px rgba(232,76,136,0.20)',
    label: 'Story Worlds',
  },
};
