'use client';

import Image from 'next/image';

/**
 * B2BBrandBar — minimal, NON-clickable brand bar for auth (login/signup) pages.
 *
 * Deliberately NOT a <Link>: on the B2B auth screens the logo must not navigate
 * back to the consumer landing page. It is a plain, static brand mark plus a
 * "for Schools" tag so the portal reads as a distinct B2B surface.
 */
export function B2BBrandBar() {
  return (
    <header className="w-full border-b border-white/10 bg-[#0A0A0F]">
      <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3 sm:px-6">
        {/* Non-clickable logo — no href, no onClick, cursor stays default */}
        <div className="flex select-none items-center" aria-label="MyTaCo AI">
          <Image
            src="/logos/mytacologo.svg"
            alt="MyTaCo AI"
            width={150}
            height={38}
            className="h-[38px] w-auto object-contain"
            priority
          />
        </div>
        <span className="rounded-full bg-[#4ECFBF]/15 px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-[#4ECFBF]">
          for Schools
        </span>
      </div>
    </header>
  );
}
