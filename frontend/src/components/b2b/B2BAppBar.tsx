'use client';

import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { B2BLogoutButton } from './B2BLogoutButton';

interface B2BAppBarProps {
  /** Portal type — drives the label + where the logo/home link points. */
  portal: 'institution' | 'tutor';
  /** Display name shown in the account dropdown (institution name or tutor name). */
  name?: string;
  /** Account email shown in the account dropdown (optional). */
  email?: string;
  /** Where the logo navigates. Defaults to the portal's own dashboard — NEVER the landing page. */
  homeHref?: string;
}

/**
 * B2BAppBar — top app bar for the signed-in B2B dashboards (institution & tutor).
 *
 * Logo links to the portal's OWN dashboard (homeHref), not the consumer landing
 * page. Right side shows the account name and a Logout action.
 */
export function B2BAppBar({ portal, name, email, homeHref }: B2BAppBarProps) {
  const router = useRouter();
  const label = portal === 'institution' ? 'School Portal' : 'Tutor Portal';
  const home = homeHref ?? (portal === 'institution' ? '/institution/dashboard' : '/tutor/login');

  return (
    <header className="sticky top-0 z-40 w-full border-b border-white/10 bg-[#0A0A0F]/95 backdrop-blur-sm">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
        {/* Logo → own dashboard (not landing) */}
        <button
          type="button"
          onClick={() => router.push(home)}
          className="flex items-center gap-3 rounded-lg px-1 py-1 transition-opacity hover:opacity-80 focus:outline-none focus:ring-2 focus:ring-[#4ECFBF]"
          aria-label={`${label} home`}
        >
          <Image
            src="/logos/mytacologo.svg"
            alt="MyTaCo AI"
            width={130}
            height={33}
            className="h-[33px] w-auto object-contain"
            priority
          />
          <span className="hidden rounded-full bg-[#4ECFBF]/15 px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-[#4ECFBF] sm:inline">
            {label}
          </span>
        </button>

        {/* Account — avatar dropdown (name/email live inside the dropdown) */}
        <B2BLogoutButton portal={portal} name={name} email={email} />
      </div>
    </header>
  );
}
