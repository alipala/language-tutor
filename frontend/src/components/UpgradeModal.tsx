'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, CheckCircle, AlertCircle } from 'lucide-react';

interface UpgradeOption {
  type: string;
  title: string;
  current_price?: number;
  new_price?: number;
  annual_total?: number;
  savings_amount?: number;
  savings_percentage?: number;
  price_difference?: number;
  immediate_benefit: string;
  features: string[];
  stripe_price_id?: string;
  recommended: boolean;
  renewal_date?: string;
  days_remaining?: number;
  new_minutes_on_renewal?: number;
}

interface CurrentPlan {
  name: string;
  price: number;
  billing_period: string;
  minutes_total: number;
  minutes_used: number;
  minutes_remaining: number;
  renewal_date: string;
  days_until_renewal: number;
}

interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpgradeSuccess?: () => void;
}

export default function UpgradeModal({ isOpen, onClose, onUpgradeSuccess }: UpgradeModalProps) {
  const [options, setOptions] = useState<UpgradeOption[]>([]);
  const [currentPlan, setCurrentPlan] = useState<CurrentPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedOption, setSelectedOption] = useState<UpgradeOption | null>(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [processingUpgrade, setProcessingUpgrade] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchUpgradeOptions();
    }
  }, [isOpen]);

  const fetchUpgradeOptions = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/upgrade/options`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch upgrade options');
      }

      const data = await response.json();
      setCurrentPlan(data.current_plan);
      setOptions(data.upgrade_options);
    } catch (err) {
      console.error('Error fetching upgrade options:', err);
      setError('Unable to load upgrade options. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpgradeClick = (option: UpgradeOption) => {
    if (option.type === 'wait_renewal') {
      onClose();
      return;
    }

    // Show confirmation dialog
    setSelectedOption(option);
    setShowConfirmation(true);
  };

  const handleConfirmUpgrade = async () => {
    if (!selectedOption || !selectedOption.stripe_price_id) {
      return;
    }

    setProcessingUpgrade(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/upgrade/process`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          price_id: selectedOption.stripe_price_id,
          upgrade_type: selectedOption.type,
        }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.detail || data.error || 'Upgrade failed');
      }

      // Success!
      const minutesText = data.unlimited ? 'unlimited' : data.minutes_total;
      alert(`✅ Successfully upgraded! Your usage has been reset and you now have ${minutesText} minutes.`);
      
      if (onUpgradeSuccess) {
        onUpgradeSuccess();
      }
      
      // Close all modals and refresh
      setShowConfirmation(false);
      onClose();
      window.location.reload();
    } catch (err: any) {
      console.error('Error processing upgrade:', err);
      setError(err.message || 'Failed to process upgrade. Please try again.');
      setShowConfirmation(false);
    } finally {
      setProcessingUpgrade(false);
    }
  };

  const handleCancelConfirmation = () => {
    setShowConfirmation(false);
    setSelectedOption(null);
  };

  return (
    <>
      {/* Main Upgrade Modal */}
      <AnimatePresence>
        {isOpen && !showConfirmation && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={onClose}
              className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            />

            {/* Modal Content */}
            <motion.div
              initial={{ scale: 0.9, y: 20, opacity: 0 }}
              animate={{ scale: 1, y: 0, opacity: 1 }}
              exit={{ scale: 0.9, y: 20, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto bg-white rounded-2xl shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Close Button */}
              <button
                onClick={onClose}
                className="absolute top-4 right-4 z-10 p-2 text-white hover:bg-white/20 rounded-full transition-colors"
              >
                <X className="w-6 h-6" />
              </button>

              {/* Header */}
              <div className="bg-gradient-to-r from-teal-500 to-cyan-600 p-6 text-white">
                <div className="text-4xl mb-2">🎉</div>
                <h2 className="text-3xl font-bold mb-2">Ready to Continue Learning?</h2>
                <p className="text-lg opacity-90">
                  Choose an upgrade option to keep practicing and improving your language skills!
                </p>
              </div>

              {/* Current Usage Summary */}
              {currentPlan && (
                <div className="bg-gray-50 p-4 border-b border-gray-200">
                  <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
                    <span className="font-semibold text-gray-700">
                      {currentPlan.name} (€{currentPlan.price})
                    </span>
                    <div className="flex items-center gap-4">
                      <span className="text-green-600">
                        ✓ {currentPlan.minutes_used} minutes used
                      </span>
                      <span className="text-red-600">
                        ❌ {currentPlan.minutes_remaining} minutes remaining
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Error Message */}
              {error && (
                <div className="mx-6 mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-red-800">{error}</p>
                </div>
              )}

              {/* Loading State */}
              {loading && (
                <div className="p-12 text-center">
                  <div className="inline-block w-12 h-12 border-4 border-teal-500 border-t-transparent rounded-full animate-spin"></div>
                  <p className="mt-4 text-gray-600">Loading upgrade options...</p>
                </div>
              )}

              {/* Upgrade Options */}
              {!loading && !error && options.length > 0 && (
                <div className="p-6 space-y-4">
                  {options.map((option, index) => (
                    <motion.div
                      key={option.type}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className={`relative border-2 rounded-xl p-6 transition-all hover:shadow-lg ${
                        option.recommended
                          ? 'border-teal-500 bg-teal-50'
                          : 'border-gray-200 bg-white'
                      }`}
                    >
                      {/* Best Value Badge */}
                      {option.recommended && (
                        <div className="absolute -top-3 right-6 bg-gradient-to-r from-yellow-400 to-orange-500 text-white px-4 py-1 rounded-full text-sm font-bold shadow-lg">
                          BEST VALUE
                        </div>
                      )}

                      {/* Option Title */}
                      <h3 className="text-xl font-bold mb-3 text-gray-900">
                        {option.title}
                      </h3>

                      {/* Pricing Display */}
                      {option.new_price !== undefined && (
                        <div className="flex items-center gap-3 mb-4">
                          {option.current_price && (
                            <span className="text-gray-400 line-through text-lg">
                              €{option.current_price.toFixed(2)}
                            </span>
                          )}
                          <span className="text-3xl font-bold text-teal-600">
                            €{option.new_price.toFixed(2)}
                            {option.annual_total && (
                              <span className="text-base text-gray-600">/month</span>
                            )}
                          </span>
                          {option.savings_percentage && (
                            <span className="bg-green-500 text-white px-3 py-1 rounded-full text-sm font-bold">
                              SAVE {option.savings_percentage}%
                            </span>
                          )}
                        </div>
                      )}

                      {/* Immediate Benefit Box */}
                      <div className="bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-200 rounded-lg p-4 mb-4">
                        <p className="text-blue-900 font-semibold">
                          ✨ {option.immediate_benefit}
                        </p>
                      </div>

                      {/* Features List */}
                      <ul className="space-y-2 mb-6">
                        {option.features.map((feature, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <svg
                              className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M5 13l4 4L19 7"
                              />
                            </svg>
                            <span className="text-gray-700">{feature}</span>
                          </li>
                        ))}
                      </ul>

                      {/* Action Button */}
                      <button
                        onClick={() => handleUpgradeClick(option)}
                        disabled={processingUpgrade}
                        className={`w-full py-3 rounded-lg font-bold transition-all ${
                          option.type === 'wait_renewal'
                            ? 'border-2 border-gray-300 bg-transparent hover:bg-gray-50 text-gray-700'
                            : option.recommended
                            ? 'bg-gradient-to-r from-teal-500 to-cyan-600 hover:from-teal-600 hover:to-cyan-700 text-white shadow-lg hover:shadow-xl'
                            : 'bg-gray-700 hover:bg-gray-800 text-white'
                        } ${
                          processingUpgrade
                            ? 'opacity-50 cursor-not-allowed'
                            : 'hover:scale-[1.02]'
                        }`}
                      >
                        {option.type === 'wait_renewal' ? "I'll Wait" : 'Review Upgrade'}
                      </button>
                    </motion.div>
                  ))}
                </div>
              )}

              {/* Footer */}
              <div className="bg-gray-50 p-4 text-center border-t border-gray-200">
                <p className="text-sm text-gray-600">
                  All plans include full access to your learning progress and achievements
                </p>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Confirmation Dialog */}
      <AnimatePresence>
        {showConfirmation && selectedOption && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[60] flex items-center justify-center p-4"
            onClick={handleCancelConfirmation}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Confirmation Header */}
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-gradient-to-r from-teal-500 to-cyan-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">
                  Confirm Your Upgrade
                </h3>
                <p className="text-gray-600">
                  Please review the details before confirming
                </p>
              </div>

              {/* Upgrade Details */}
              <div className="bg-gray-50 rounded-lg p-4 mb-6 space-y-3">
                <div className="flex justify-between items-start">
                  <span className="text-gray-600">Plan:</span>
                  <span className="font-bold text-gray-900 text-right">
                    {selectedOption.title}
                  </span>
                </div>

                {selectedOption.new_price && (
                  <div className="flex justify-between items-start">
                    <span className="text-gray-600">Price:</span>
                    <div className="text-right">
                      <span className="font-bold text-teal-600 text-xl">
                        €{selectedOption.new_price.toFixed(2)}
                      </span>
                      <span className="text-gray-600 text-sm ml-1">
                        /month
                      </span>
                    </div>
                  </div>
                )}

                {selectedOption.annual_total && (
                  <div className="flex justify-between items-start">
                    <span className="text-gray-600">Annual Total:</span>
                    <span className="font-bold text-gray-900">
                      €{selectedOption.annual_total.toFixed(2)}
                    </span>
                  </div>
                )}

                {selectedOption.savings_amount && (
                  <div className="flex justify-between items-start">
                    <span className="text-gray-600">Annual Savings:</span>
                    <span className="font-bold text-green-600">
                      €{selectedOption.savings_amount.toFixed(2)} ({selectedOption.savings_percentage}%)
                    </span>
                  </div>
                )}

                <div className="flex justify-between items-start">
                  <span className="text-gray-600">Immediate Benefit:</span>
                  <span className="font-semibold text-blue-600 text-right max-w-[60%]">
                    {selectedOption.immediate_benefit}
                  </span>
                </div>
              </div>

              {/* Important Notice */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-blue-900">
                    <p className="font-semibold mb-1">What happens next:</p>
                    <ul className="space-y-1 text-blue-800">
                      <li>• Your usage will be reset to 0</li>
                      <li>• You'll start fresh with your new plan</li>
                      <li>• Changes take effect immediately</li>
                      <li>• You can manage your subscription anytime</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Error in Confirmation */}
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
                  <p className="text-red-800 text-sm">{error}</p>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3">
                <button
                  onClick={handleCancelConfirmation}
                  disabled={processingUpgrade}
                  className="flex-1 py-3 px-4 rounded-lg font-semibold border-2 border-gray-300 text-gray-700 hover:bg-gray-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmUpgrade}
                  disabled={processingUpgrade}
                  className="flex-1 py-3 px-4 rounded-lg font-semibold bg-gradient-to-r from-teal-500 to-cyan-600 hover:from-teal-600 hover:to-cyan-700 text-white shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {processingUpgrade ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Processing...
                    </span>
                  ) : (
                    'Confirm Upgrade'
                  )}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
