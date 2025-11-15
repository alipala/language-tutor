'use client';

import { useState } from 'react';
import UpgradeModal from '../../src/components/UpgradeModal';

export default function TestUpgradePage() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Upgrade Modal Test Page
        </h1>
        
        <p className="text-gray-600 mb-6">
          Click the button below to test the upgrade modal with your account.
        </p>

        <div className="space-y-4">
          <button
            onClick={() => setIsModalOpen(true)}
            className="w-full bg-gradient-to-r from-teal-500 to-cyan-600 hover:from-teal-600 hover:to-cyan-700 text-white font-bold py-3 px-6 rounded-lg shadow-lg hover:shadow-xl transition-all"
          >
            Open Upgrade Modal
          </button>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-blue-900 mb-2">Test Instructions:</h3>
            <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
              <li>Make sure you're logged in</li>
              <li>Click "Open Upgrade Modal"</li>
              <li>Review the 3 upgrade options</li>
              <li>Test the "I'll Wait" button (closes modal)</li>
              <li>Test responsive design (resize window)</li>
            </ol>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h3 className="font-semibold text-yellow-900 mb-2">⚠️ Important:</h3>
            <p className="text-sm text-yellow-800">
              The "Upgrade Now" buttons will process real Stripe payments. 
              Only click if you actually want to upgrade your subscription!
            </p>
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-2">Your Account:</h3>
            <p className="text-sm text-gray-600">
              User: Ali Pala (alipala.ist@gmail.com)<br />
              Plan: Fluency Builder Monthly<br />
              Minutes: 147/150 used
            </p>
          </div>
        </div>
      </div>

      {/* Upgrade Modal */}
      <UpgradeModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onUpgradeSuccess={() => {
          console.log('Upgrade successful!');
        }}
      />
    </div>
  );
}
