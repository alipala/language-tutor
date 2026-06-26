'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { CATEGORY, type CategoryKey } from '@/lib/categories';

/**
 * Card — the single elevated-surface primitive for the marketing site.
 *
 * THE FIX for the "rainbow bento": elevation (depth) comes from a SHARED
 * surface + shadow ramp identical for every card. A `category` only tints
 * the border + icon chip + hover glow — it never changes the surface and is
 * never used as a fake inset elevation. So every card reads as one family,
 * with color signalling which feature it is.
 */

type Elevation = 'rest' | 'raised' | 'hero';

const ELEVATION: Record<Elevation, string> = {
  rest: 'bg-surface-1 shadow-e1',
  raised: 'bg-surface-2 shadow-e2',
  hero: 'bg-surface-1 shadow-e3',
};

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  elevation?: Elevation;
  category?: CategoryKey;
  interactive?: boolean;
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, elevation = 'rest', category, interactive, style, ...props }, ref) => {
    const cat = category ? CATEGORY[category] : null;
    const [hovered, setHovered] = React.useState(false);

    return (
      <div
        ref={ref}
        onMouseEnter={interactive ? () => setHovered(true) : undefined}
        onMouseLeave={interactive ? () => setHovered(false) : undefined}
        className={cn(
          'relative rounded-card border p-5 sm:p-6 transition-all duration-300 overflow-hidden',
          ELEVATION[elevation],
          interactive && 'hover:-translate-y-0.5',
          className
        )}
        style={{
          borderColor: cat ? cat.line : 'rgba(255,255,255,0.08)',
          boxShadow:
            interactive && hovered && cat
              ? `var(--shadow-2), ${cat.glow}`
              : undefined,
          ...style,
        }}
        {...props}
      />
    );
  }
);
Card.displayName = 'Card';

/** Tinted rounded icon chip (10x10) — uses the category color. */
const CardIcon = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { category?: CategoryKey }
>(({ className, category, style, ...props }, ref) => {
  const cat = category ? CATEGORY[category] : null;
  return (
    <div
      ref={ref}
      className={cn(
        'w-10 h-10 rounded-2xl flex items-center justify-center',
        className
      )}
      style={{
        backgroundColor: cat ? cat.tint : 'rgba(255,255,255,0.06)',
        color: cat ? cat.color : undefined,
        ...style,
      }}
      {...props}
    />
  );
});
CardIcon.displayName = 'CardIcon';

const CardHeader = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn('flex items-center gap-3 mb-4', className)} {...props} />
);

const CardEyebrow = ({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) => (
  <p
    className={cn(
      'text-[10px] font-bold uppercase tracking-[0.2em] text-ink-faint mb-1',
      className
    )}
    {...props}
  />
);

const CardTitle = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn('text-white font-bold text-lg leading-tight', className)} {...props} />
);

const CardBody = ({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) => (
  <p className={cn('text-ink-muted text-sm leading-relaxed', className)} {...props} />
);

export { Card, CardIcon, CardHeader, CardEyebrow, CardTitle, CardBody };
