'use client';

import { useEffect, useState, useRef } from 'react';
import { useAuth } from '@/lib/auth';
import { assignPlanToUser } from '@/lib/learning-api';
import { useRouter } from 'next/navigation';

/**
 * This component handles assigning pending learning plans to users after they sign in.
 * It should be included in the layout or pages where users are redirected after authentication.
 */
export default function PendingLearningPlanHandler() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [processed, setProcessed] = useState(false);
  const processingRef = useRef(false);
  
  useEffect(() => {
    // Only run this once when the user is loaded and not already processed
    // Use ref to prevent multiple simultaneous executions
    if (!loading && user && !processed && !processingRef.current) {
      processingRef.current = true;
      handlePendingLearningPlan();
    }
  }, [user, loading, processed]);
  
  const handlePendingLearningPlan = async () => {
    try {
      // Check if there's a pending learning plan ID in session storage
      const pendingPlanId = sessionStorage.getItem('pendingLearningPlanId');
      
      if (pendingPlanId) {
        console.log('[PendingLearningPlanHandler] Found pending learning plan ID:', pendingPlanId);
        
        try {
          // Assign the plan to the user
          const updatedPlan = await assignPlanToUser(pendingPlanId);
          console.log('[PendingLearningPlanHandler] Learning plan assigned to user:', updatedPlan);
          
          // Store the assigned plan ID in localStorage for persistence across sessions
          // This helps with recovery if the session is lost
          const assignedPlans = JSON.parse(localStorage.getItem('assignedLearningPlans') || '[]');
          if (!assignedPlans.includes(pendingPlanId)) {
            assignedPlans.push(pendingPlanId);
            localStorage.setItem('assignedLearningPlans', JSON.stringify(assignedPlans));
          }
          
          // Clear the pending plan ID from session storage
          sessionStorage.removeItem('pendingLearningPlanId');
          
          // Check if we need to redirect to the speech page with this plan
          const redirectWithPlan = sessionStorage.getItem('redirectWithPlanId') === pendingPlanId;
          if (redirectWithPlan) {
            console.log('[PendingLearningPlanHandler] Redirecting to speech page with plan:', pendingPlanId);
            sessionStorage.removeItem('redirectWithPlanId');
            
            // Use a timeout to ensure state updates complete before navigation
            setTimeout(() => {
              window.location.href = `/speech?plan=${pendingPlanId}`;
            }, 100);
            return;
          }
        } catch (assignError) {
          console.error('[PendingLearningPlanHandler] Error assigning plan:', assignError);
          // If assignment fails but it's not an auth error, we'll clear the pending plan
          // to prevent endless retries
          if (!(assignError instanceof Error && assignError.message.includes('Authentication required'))) {
            console.log('[PendingLearningPlanHandler] Clearing invalid pending plan ID');
            sessionStorage.removeItem('pendingLearningPlanId');
          }
        }
      } else {
        console.log('[PendingLearningPlanHandler] No pending learning plan found');
      }
    } catch (error) {
      console.error('[PendingLearningPlanHandler] Unexpected error:', error);
    } finally {
      processingRef.current = false;
      setProcessed(true);
    }
  };
  
  // This component doesn't render anything visible
  return null;
}
