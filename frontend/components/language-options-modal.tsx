'use client';

import React, { useState, useEffect } from 'react';
import { Award, MessageSquare, ChevronRight, Volume2, X } from 'lucide-react';

/**
 * LanguageOptionsModal component
 * 
 * Displays a modal with options to either "Assess my speaking level" or "Do a Practice"
 * after a user selects a language
 * 
 * @param {Object} props - Component props
 * @param {boolean} props.isOpen - Whether the modal is open or closed
 * @param {Function} props.onClose - Function to call when closing the modal
 * @param {string} props.selectedLanguage - The language selected by the user
 * @param {Function} props.onContinue - Function to call with selected option when continuing
 */
const LanguageOptionsModal = ({ 
  isOpen, 
  onClose, 
  selectedLanguage, 
  onContinue 
}: {
  isOpen: boolean;
  onClose: () => void;
  selectedLanguage: string;
  onContinue: (option: string) => void;
}) => {
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [animationComplete, setAnimationComplete] = useState(false);
  
  useEffect(() => {
    if (isOpen) {
      // Start entry animation
      const timer = setTimeout(() => {
        setAnimationComplete(true);
      }, 300);
      
      return () => clearTimeout(timer);
    } else {
      setAnimationComplete(false);
      setSelectedOption(null);
    }
  }, [isOpen]);
  
  // Handle option selection
  const handleOptionSelect = (option: string) => {
    setSelectedOption(option);
  };
  
  // Handle continue to next screen
  const handleContinue = () => {
    if (selectedOption) {
      onContinue(selectedOption);
    }
    onClose();
  };
  
  // Get language display info based on selection
  const getLanguageInfo = () => {
    const languageMap: Record<string, { flag: string; description: string; learners: string }> = {
      'english': { 
        flag: '🇬🇧', 
        description: 'Practice English speaking and listening',
        learners: '10M+'
      },
      'spanish': { 
        flag: '🇪🇸', 
        description: 'Domina habilidades de conversación en español',
        learners: '8M+'
      },
      'french': { 
        flag: '🇫🇷', 
        description: 'Améliorez vos compétences en français',
        learners: '7M+'
      },
      'german': { 
        flag: '🇩🇪', 
        description: 'The most widely spoken language in the European Union',
        learners: '5M+'
      },
      'dutch': { 
        flag: '🇳🇱', 
        description: 'Leer Nederlandse woordenschat en conversatie',
        learners: '2M+'
      },
      'portuguese': { 
        flag: '🇵🇹', 
        description: 'Aprenda vocabulário e expressões em português',
        learners: '3M+'
      }
    };
    
    return languageMap[selectedLanguage.toLowerCase()] || { 
      flag: '🌐', 
      description: 'Select a language to start learning',
      learners: '0'
    };
  };
  
  const languageInfo = getLanguageInfo();
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div 
        className={`bg-white rounded-xl shadow-xl w-full max-w-2xl overflow-hidden transition-all duration-300 transform ${
          animationComplete ? 'scale-100 opacity-100' : 'scale-95 opacity-0'
        }`}
      >
        {/* Header */}
        <div className="p-6" style={{ backgroundColor: 'var(--turquoise)' }}>
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <div className="text-3xl mr-3">{languageInfo.flag}</div>
              <div>
                <h2 className="text-xl font-bold text-white">
                  {selectedLanguage ? `${selectedLanguage} Selected` : 'Select Your Path'}
                </h2>
                <p className="text-sm text-white opacity-80">Choose how you want to start your language journey</p>
              </div>
            </div>
            
            <button 
              className="text-white hover:text-white/70 transition-colors"
              onClick={onClose}
              aria-label="Close modal"
            >
              <X size={24} />
            </button>
          </div>
        </div>
        
        {/* Language Info */}
        <div className="px-6 py-4 border-b border-gray-100" style={{ backgroundColor: 'rgba(78, 207, 191, 0.1)' }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div 
                className="w-10 h-10 rounded-full flex items-center justify-center mr-3"
                style={{ backgroundColor: 'rgba(78, 207, 191, 0.2)', color: 'var(--turquoise)' }}
              >
                <Volume2 size={20} />
              </div>
              <p className="text-gray-600 text-sm">{languageInfo.description}</p>
            </div>
            <div 
              className="text-xs px-2 py-1 rounded-full"
              style={{ backgroundColor: 'rgba(78, 207, 191, 0.2)', color: 'var(--turquoise)' }}
            >
              {languageInfo.learners} learners
            </div>
          </div>
        </div>
        
        {/* Options */}
        <div className="p-6">
          <div className="text-sm font-medium text-gray-500 mb-3">What would you like to do?</div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
            {/* Assessment Option */}
            <div 
              className={`border rounded-xl p-5 transition-all duration-200 cursor-pointer hover:shadow-md ${
                selectedOption === 'assessment' 
                  ? 'border-[var(--turquoise)]' 
                  : 'border-gray-200 hover:border-[var(--turquoise)]'
              }`}
              style={{ 
                backgroundColor: selectedOption === 'assessment' ? 'rgba(78, 207, 191, 0.1)' : 'transparent'
              }}
              onClick={() => handleOptionSelect('assessment')}
            >
              <div className="flex items-start h-full">
                <div 
                  className="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0 mr-4"
                  style={{ backgroundColor: 'rgba(78, 207, 191, 0.2)', color: 'var(--turquoise)' }}
                >
                  <Award size={24} />
                </div>
                <div>
                  <h3 className="font-bold text-gray-800 mb-2">Assess my speaking level</h3>
                  <p className="text-gray-600 text-sm">Take a quick assessment to determine your current language proficiency level.</p>
                </div>
              </div>
            </div>
            
            {/* Practice Option */}
            <div 
              className={`border rounded-xl p-5 transition-all duration-200 cursor-pointer hover:shadow-md ${
                selectedOption === 'practice' 
                  ? 'border-[var(--turquoise)]' 
                  : 'border-gray-200 hover:border-[var(--turquoise)]'
              }`}
              style={{ 
                backgroundColor: selectedOption === 'practice' ? 'rgba(78, 207, 191, 0.1)' : 'transparent'
              }}
              onClick={() => handleOptionSelect('practice')}
            >
              <div className="flex items-start h-full">
                <div 
                  className="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0 mr-4"
                  style={{ backgroundColor: 'rgba(255, 214, 58, 0.2)', color: 'var(--yellow)' }}
                >
                  <MessageSquare size={24} />
                </div>
                <div>
                  <h3 className="font-bold text-gray-800 mb-2">Do a Practice</h3>
                  <p className="text-gray-600 text-sm">Start a conversation practice session on topics of your choice.</p>
                </div>
              </div>
            </div>
          </div>
          
          {/* Footer Actions */}
          <div className="flex justify-end">
            <button 
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors mr-3"
              onClick={onClose}
            >
              Cancel
            </button>
            <button 
              className={`px-4 py-2 rounded-lg transition-colors flex items-center ${
                selectedOption 
                  ? 'bg-[var(--turquoise)] text-white hover:bg-[#5CCFC0]' 
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
              onClick={handleContinue}
              disabled={!selectedOption}
            >
              Continue
              {selectedOption && <ChevronRight size={18} className="ml-1" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LanguageOptionsModal;
