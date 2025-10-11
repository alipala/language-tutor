'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { usePlanModal } from '../../components/modals/plan-modal-context';

/**
 * Special route for handling post-login modal opening from pricing page
 * This route opens the plan modal and redirects to home with #pricing
 * so the modal is visible over the pricing section
 */
export default function PricingCheckoutPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { openPlanModal } = usePlanModal();

  useEffect(() => {
    const planId = searchParams?.get('plan');
    const period = searchParams?.get('period') === 'annual' ? 'annual' : 'monthly';

    // Open the plan modal with preselected plan/period if provided
    openPlanModal({ planId: planId || undefined, period });

    // Redirect to home with #pricing so modal is visible over pricing section
    router.replace('/#pricing');
    // eslint-disable-next-line
  }, []);

  // No UI needed, modal is handled globally
  return null;
}
