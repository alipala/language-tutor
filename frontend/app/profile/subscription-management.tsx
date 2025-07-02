'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '../../lib/auth';
import { LoadingSpinner } from '../../components/ui/loading-spinner';
import ConfirmationModal from '../../components/ui/confirmation-modal';

interface SubscriptionStatus {
  status: string | null;
  plan: string | null;
  period: string | null;
  price_id: string | null;
  is_in_trial: boolean;
  trial_end_date: string | null;
  trial_days_remaining: number | null;
}

export default function SubscriptionManagement() {
  const [isLoading, setIsLoading] = useState(false);
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [showSuccessMessage, setShowSuccessMessage] = useState<string | null>(null);
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchSubscriptionStatus();
    }
  }, [user]);

  const fetchSubscriptionStatus = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch('/api/stripe/subscription-status', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch subscription status');
      }

      const data = await response.json();
      setSubscription(data);
    } catch (error) {
      console.error('Error fetching subscription status:', error);
      setError('Failed to load subscription information. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancelClick = () => {
    setShowCancelModal(true);
  };

  const handleCancelConfirm = async () => {
    setShowCancelModal(false);
    setIsLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch('/api/stripe/cancel-subscription', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(errorData.error || 'Failed to cancel subscription');
      }

      // Refresh subscription status
      await fetchSubscriptionStatus();
      
      // Show success message
      setError(null);
      setShowSuccessMessage('Your subscription has been canceled successfully. You will retain access until the end of your current billing period.');
      
      // Hide success message after 5 seconds
      setTimeout(() => setShowSuccessMessage(null), 5000);
      
    } catch (error: any) {
      console.error('Error canceling subscription:', error);
      setError(error.message || 'Failed to cancel subscription. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReactivateSubscription = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch('/api/stripe/reactivate-subscription', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(errorData.error || 'Failed to reactivate subscription');
      }

      // Refresh subscription status
      await fetchSubscriptionStatus();
      
      // Show success message
      setError(null);
      setShowSuccessMessage('Your subscription has been reactivated successfully!');
      
      // Hide success message after 5 seconds
      setTimeout(() => setShowSuccessMessage(null), 5000);
      
    } catch (error: any) {
      console.error('Error reactivating subscription:', error);
      setError(error.message || 'Failed to reactivate subscription. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  const formatPlanName = (plan: string | null) => {
    if (!plan) return 'No Plan';
    
    return plan
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const formatPeriod = (period: string | null) => {
    if (!period) return '';
    
    return period === 'monthly' ? 'Monthly' : 'Annual';
  };

  const getStatusBadgeColor = (status: string | null) => {
    if (!status) return 'bg-gray-100 text-gray-800';
    
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'trialing':
        return 'bg-blue-100 text-blue-800';
      case 'canceling':
        return 'bg-orange-100 text-orange-800';
      case 'canceled':
        return 'bg-red-100 text-red-800';
      case 'past_due':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusDisplayText = (status: string | null) => {
    if (!status) return 'Unknown';
    
    switch (status) {
      case 'trialing':
        return 'Free Trial';
      case 'active':
        return 'Active';
      case 'canceling':
        return 'Canceling';
      case 'canceled':
        return 'Canceled';
      case 'past_due':
        return 'Past Due';
      default:
        return status;
    }
  };

  if (isLoading && !subscription) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-2xl font-bold mb-4 text-gray-900">Subscription</h2>
        <div className="flex justify-center items-center py-8">
          <LoadingSpinner size="lg" />
        </div>
      </div>
    );
  }

  if (error && !subscription) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-2xl font-bold mb-4 text-gray-900">Subscription</h2>
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          {error}
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-2xl font-bold mb-4 text-gray-900">Subscription</h2>
        
        {/* Success Message */}
        {showSuccessMessage && (
          <div className="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm">{showSuccessMessage}</p>
              </div>
            </div>
          </div>
        )}
        
        {subscription && subscription.status ? (
        <div className="space-y-6">
          {/* Trial Banner */}
          {subscription.is_in_trial && subscription.trial_days_remaining !== null && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3 flex-1">
                  <h3 className="text-sm font-medium text-blue-800">
                    🎉 Free Trial Active
                  </h3>
                  <div className="mt-1 text-sm text-blue-700">
                    <p>
                      <strong>{subscription.trial_days_remaining} days remaining</strong> in your free trial.
                      {subscription.trial_end_date && (
                        <span className="block mt-1">
                          Trial ends on {new Date(subscription.trial_end_date).toLocaleDateString('en-US', { 
                            weekday: 'long', 
                            year: 'numeric', 
                            month: 'long', 
                            day: 'numeric' 
                          })}
                        </span>
                      )}
                    </p>
                    <p className="mt-2 text-xs">
                      Cancel anytime during trial - no charges will be applied.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-medium text-gray-500">Current Plan</h3>
              <p className="mt-1 text-lg font-semibold text-gray-800">
                {formatPlanName(subscription.plan)} {formatPeriod(subscription.period)}
                {subscription.is_in_trial && (
                  <span className="ml-2 text-sm font-normal text-blue-600">(Free Trial)</span>
                )}
              </p>
            </div>
            
            <div>
              <h3 className="text-sm font-medium text-gray-500">Status</h3>
              <div className="mt-1">
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusBadgeColor(subscription.status)}`}>
                  {getStatusDisplayText(subscription.status)}
                </span>
              </div>
            </div>
          </div>
          
          <div className="border-t border-gray-200 pt-4">
            <div className="flex flex-wrap gap-3">
              {(subscription.status === 'active' || subscription.status === 'trialing') && (
                <button
                  onClick={handleCancelClick}
                  disabled={isLoading}
                  className="inline-flex items-center px-4 py-2 border border-red-300 rounded-md shadow-sm text-sm font-medium text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <>
                      <LoadingSpinner size="sm" className="mr-2" />
                      Processing...
                    </>
                  ) : (
                    subscription.is_in_trial ? 'Cancel Trial' : 'Cancel Subscription'
                  )}
                </button>
              )}
              
              {(subscription.status === 'canceling' || subscription.status === 'canceled') && (
                <button
                  onClick={handleReactivateSubscription}
                  disabled={isLoading}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <>
                      <LoadingSpinner size="sm" className="mr-2" />
                      Processing...
                    </>
                  ) : (
                    'Reactivate Subscription'
                  )}
                </button>
              )}
              
              {subscription.status === 'past_due' && (
                <a
                  href="/#pricing"
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-yellow-600 hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500"
                >
                  Update Payment Method
                </a>
              )}
            </div>
            
            {error && (
              <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
                {error}
              </div>
            )}
          </div>
          
          {subscription.status === 'canceling' && (
            <div className="mt-4 bg-orange-50 border-l-4 border-orange-400 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-orange-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-orange-700">
                    Your subscription is scheduled for cancellation and will end at the end of your current billing period. You can reactivate it anytime before then.
                  </p>
                </div>
              </div>
            </div>
          )}

          {subscription.status === 'canceled' && (
            <div className="mt-4 bg-yellow-50 border-l-4 border-yellow-400 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-yellow-700">
                    Your subscription has been canceled and will end at the end of your current billing period.
                  </p>
                </div>
              </div>
            </div>
          )}
          
          {subscription.status === 'past_due' && (
            <div className="mt-4 bg-red-50 border-l-4 border-red-400 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-700">
                    Your payment is past due. Please update your payment method to continue using premium features.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="py-4">
          <p className="text-gray-600 mb-4">
            You don't have an active subscription. Upgrade to a premium plan to access all features.
          </p>
          <a
            href="/#pricing"
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            View Plans
          </a>
        </div>
      )}
      </div>
      
      {/* Confirmation Modal */}
      <ConfirmationModal
        isOpen={showCancelModal}
        onClose={() => setShowCancelModal(false)}
        onConfirm={handleCancelConfirm}
        title={subscription?.is_in_trial ? "Cancel Trial" : "Cancel Subscription"}
        message={
          subscription?.is_in_trial 
            ? "Are you sure you want to cancel your free trial? You will immediately lose access to premium features and no charges will be applied."
            : "Are you sure you want to cancel your subscription? You will lose access to premium features at the end of your current billing period."
        }
        confirmText={subscription?.is_in_trial ? "Yes, Cancel Trial" : "Yes, Cancel Subscription"}
        cancelText={subscription?.is_in_trial ? "Keep Trial" : "Keep Subscription"}
        type="danger"
        isLoading={isLoading}
      />
    </>
  );
}
