'use client';

import React, { useState } from 'react';
import LoadingModal from '@/components/loading-modal';
import { Button } from '@/components/ui/button';

export default function LoadingModalDemo() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [customMessage, setCustomMessage] = useState('');

  const showModal = () => {
    setIsModalOpen(true);
  };

  const showCustomModal = () => {
    setCustomMessage('Custom loading message for demonstration!');
    setIsModalOpen(true);
  };

  const hideModal = () => {
    setIsModalOpen(false);
    setCustomMessage('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-8">
      <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 max-w-md w-full border border-white/20 shadow-2xl">
        <h1 className="text-3xl font-bold text-white mb-6 text-center">
          Loading Modal Demo
        </h1>
        
        <p className="text-white/80 mb-8 text-center">
          Test the new loading modal component with the taalcoach message and modern design.
        </p>
        
        <div className="space-y-4">
          <Button 
            onClick={showModal}
            className="w-full bg-[#4ECFBF] hover:bg-[#5CCFC0] text-white font-medium py-3 rounded-lg shadow-lg transition-all hover:shadow-xl hover:scale-105"
          >
            Show Default Loading Modal
          </Button>
          
          <Button 
            onClick={showCustomModal}
            className="w-full bg-[#FFD63A] hover:bg-[#ECC235] text-gray-800 font-medium py-3 rounded-lg shadow-lg transition-all hover:shadow-xl hover:scale-105"
          >
            Show Custom Message Modal
          </Button>
          
          {isModalOpen && (
            <Button 
              onClick={hideModal}
              className="w-full bg-[#F75A5A] hover:bg-[#E55252] text-white font-medium py-3 rounded-lg shadow-lg transition-all hover:shadow-xl hover:scale-105"
            >
              Hide Modal
            </Button>
          )}
        </div>
        
        <div className="mt-8 p-4 bg-white/5 rounded-lg border border-white/10">
          <h3 className="text-white font-semibold mb-2">Features:</h3>
          <ul className="text-white/70 text-sm space-y-1">
            <li>• Animated brain icon with pulsing rings</li>
            <li>• Gradient progress bar animation</li>
            <li>• Bouncing dots loader</li>
            <li>• Glass-morphism design</li>
            <li>• Consistent with app color scheme</li>
            <li>• Customizable message</li>
          </ul>
        </div>
      </div>
      
      <LoadingModal 
        isOpen={isModalOpen} 
        message={customMessage || undefined}
      />
    </div>
  );
}
