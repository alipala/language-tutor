'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/auth';
import { assignPlanToUser } from '@/lib/learning-api';

/**
 * This component handles assigning pending learning plans to users after they sign in.
 * It should be included in the layout or pages where users are redirected after authentication.
 */
export default function PendingLearningPlanHandler() {
  const { user, loading } = useAuth();
  const [processed, setProcessed] = useState(false);
  
  useEffect(() => {
    // Only run this once when the user is loaded and not already processed
    if (!loading && user && !processed) {
      handlePendingLearningPlan();
    }
  }, [user, loading, processed]);
  
  const handlePendingLearningPlan = async () => {
    try {
      // Check if there's a pending learning plan ID in session storage
      const pendingPlanId = sessionStorage.getItem('pendingLearningPlanId');
      
      if (pendingPlanId) {
        console.log('Found pending learning plan ID:', pendingPlanId);
        
        // Assign the plan to the user
        const updatedPlan = await assignPlanToUser(pendingPlanId);
        console.log('Learning plan assigned to user:', updatedPlan);
        
        // Clear the pending plan ID from session storage
        sessionStorage.removeItem('pendingLearningPlanId');
        
        // Show a notification or toast message if needed
        // This could be implemented with a toast library
      }
    } catch (error) {
      console.error('Error assigning learning plan to user:', error);
    } finally {
      setProcessed(true);
    }
  };
  
  // This component doesn't render anything visible
  return null;
}
