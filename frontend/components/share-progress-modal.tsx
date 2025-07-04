'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { 
  X, 
  Share2, 
  Download, 
  Instagram, 
  MessageCircle, 
  Copy, 
  Loader2,
  CheckCircle,
  AlertCircle,
  Sparkles,
  Trophy,
  Star,
  Zap,
  ArrowRight,
  ArrowLeft
} from 'lucide-react';

interface ShareProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  assessmentData?: any;
  learningPlanData?: any;
  assessmentId?: string;
  learningPlanId?: string;
}

interface ShareResponse {
  success: boolean;
  image_url: string;
  image_base64?: string;
  share_text: string;
  download_url?: string;
  qr_code?: string;
}

interface WeekData {
  week_number: number;
  sessions_completed: number;
  total_sessions: number;
  is_completed: boolean;
}

// Soundwave animation component
const SoundwaveLoader = () => {
  return (
    <div className="flex items-center justify-center space-x-2">
      {[...Array(7)].map((_, i) => (
        <div
          key={i}
          className="w-2 bg-[#4ECFBF] rounded-full animate-pulse"
          style={{
            height: `${Math.random() * 60 + 30}px`,
            animationDelay: `${i * 0.15}s`,
            animationDuration: '1.2s'
          }}
        />
      ))}
    </div>
  );
};

export const ShareProgressModal: React.FC<ShareProgressModalProps> = ({
  isOpen,
  onClose,
  assessmentData,
  learningPlanData,
  assessmentId,
  learningPlanId
}) => {
  const [step, setStep] = useState<'selection' | 'generation' | 'sharing'>('selection');
  const [isGenerating, setIsGenerating] = useState(false);
  const [shareData, setShareData] = useState<ShareResponse | null>(null);
  const [selectedWeek, setSelectedWeek] = useState<number | null>(null);
  const [availableWeeks, setAvailableWeeks] = useState<WeekData[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState<string | null>(null);

  // Reset state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setStep('selection');
      setShareData(null);
      setError(null);
      setCopySuccess(null);
      setSelectedWeek(null);
      loadAvailableWeeks();
    }
  }, [isOpen]);

  const loadAvailableWeeks = async () => {
    try {
      // Get real user weeks data from backend
      const response = await fetch('http://localhost:8000/api/share/user-weeks', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        const completedWeeks = data.completed_weeks || [];
        const totalWeeks = data.total_weeks || 24; // 6 months * 4 weeks
        
        // Create array with all weeks (completed and not completed)
        const allWeeks = [];
        for (let i = 1; i <= Math.max(totalWeeks, 12); i++) {
          const completedWeek = completedWeeks.find((w: WeekData) => w.week_number === i);
          allWeeks.push({
            week_number: i,
            sessions_completed: completedWeek?.sessions_completed || 0,
            total_sessions: 2,
            is_completed: !!completedWeek
          });
        }
        
        setAvailableWeeks(allWeeks);
      } else {
        // Fallback: show weeks 1-12 with only week 1 completed
        const fallbackWeeks = [];
        for (let i = 1; i <= 12; i++) {
          fallbackWeeks.push({
            week_number: i,
            sessions_completed: i === 1 ? 2 : 0,
            total_sessions: 2,
            is_completed: i === 1
          });
        }
        setAvailableWeeks(fallbackWeeks);
      }
    } catch (error) {
      console.error('Error loading weeks:', error);
      // Fallback
      const fallbackWeeks = [];
      for (let i = 1; i <= 12; i++) {
        fallbackWeeks.push({
          week_number: i,
          sessions_completed: i === 1 ? 2 : 0,
          total_sessions: 2,
          is_completed: i === 1
        });
      }
      setAvailableWeeks(fallbackWeeks);
    }
  };

  const handleWeekSelect = async (week: WeekData) => {
    if (!week.is_completed) return; // Don't allow selection of incomplete weeks
    
    setSelectedWeek(week.week_number);
    setStep('generation');
    setIsGenerating(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/share/generate-progress-image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          assessment_id: assessmentId,
          learning_plan_id: learningPlanId,
          share_type: 'progress',
          platform: 'instagram',
          week_number: week.week_number
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate progress image');
      }

      const data: ShareResponse = await response.json();
      setShareData(data);
      setStep('sharing');
    } catch (err) {
      console.error('Error generating progress image:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate progress image');
      setStep('selection');
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadImage = async () => {
    if (!shareData) {
      setError('No image data available for download');
      return;
    }

    try {
      // ALWAYS try base64 first if available (this should work since we fixed the backend)
      if (shareData.image_base64) {
        console.log('Using base64 download method');
        // Convert base64 to blob and download
        const byteCharacters = atob(shareData.image_base64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'image/png' });
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `tacoai-week${selectedWeek}-progress-${Date.now()}.png`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        setCopySuccess('Image downloaded successfully!');
        setTimeout(() => setCopySuccess(null), 3000);
        return;
      }
      
      // If no base64, show error message suggesting right-click
      console.log('No base64 data available, suggesting right-click download');
      setError('Image download not available. Please right-click the image above and select "Save image as..." to download.');
      
    } catch (err) {
      console.error('Error downloading image:', err);
      setError('Failed to download image. Try right-clicking the image and selecting "Save image as..."');
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopySuccess('Text copied to clipboard!');
      setTimeout(() => setCopySuccess(null), 3000);
    } catch (err) {
      console.error('Error copying to clipboard:', err);
      setError('Failed to copy to clipboard');
    }
  };

  const openWhatsAppWeb = async () => {
    if (shareData) {
      try {
        console.log('[WHATSAPP] Starting WhatsApp share with URL shortening...');
        
        // Import the shortener function
        const { shortenImageUrl } = await import('@/lib/image-utils');
        
        // Shorten the image URL for WhatsApp
        const shortImageUrl = await shortenImageUrl(shareData.image_url);
        console.log('[WHATSAPP] Original URL length:', shareData.image_url.length);
        console.log('[WHATSAPP] Shortened URL length:', shortImageUrl.length);
        console.log('[WHATSAPP] Shortened URL:', shortImageUrl);
        
        // Create message with shortened URL
        const messageWithImage = `${shareData.share_text}\n\n📸 View my progress image: ${shortImageUrl}`;
        const whatsappUrl = `https://web.whatsapp.com/send?text=${encodeURIComponent(messageWithImage)}`;
        
        console.log('[WHATSAPP] Final message length:', messageWithImage.length);
        console.log('[WHATSAPP] Opening WhatsApp with shortened URL...');
        
        window.open(whatsappUrl, '_blank');
        setCopySuccess(`WhatsApp opened with shortened URL! (${shortImageUrl.length} chars vs ${shareData.image_url.length} chars)`);
        setTimeout(() => setCopySuccess(null), 5000);
      } catch (error) {
        console.error('[WHATSAPP] Error shortening URL:', error);
        
        // Fallback to original URL if shortening fails
        const messageWithImage = `${shareData.share_text}\n\n📸 View my progress image: ${shareData.image_url}`;
        const whatsappUrl = `https://web.whatsapp.com/send?text=${encodeURIComponent(messageWithImage)}`;
        window.open(whatsappUrl, '_blank');
        setCopySuccess('WhatsApp opened (URL shortening failed, using original URL)');
        setTimeout(() => setCopySuccess(null), 5000);
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-3xl w-full max-w-5xl h-[85vh] flex flex-col shadow-2xl overflow-hidden relative">
        
        {/* Full Screen Soundwave Overlay */}
        {step === 'generation' && (
          <div className="absolute inset-0 bg-white/95 backdrop-blur-sm z-50 flex items-center justify-center">
            <div className="text-center space-y-8">
              <SoundwaveLoader />
              <div>
                <div className="text-2xl font-bold text-gray-800 mb-2">
                  Creating your achievement badge...
                </div>
                <p className="text-gray-600">Week {selectedWeek} progress image</p>
              </div>
            </div>
          </div>
        )}

        {/* Header */}
        <div className="bg-[#4ECFBF] p-6 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-white rounded-2xl">
              <Sparkles className="h-6 w-6 text-[#4ECFBF]" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">
                Share Your Achievement
              </h2>
              <p className="text-white/80 text-sm">Celebrate your learning journey</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/20 rounded-xl transition-colors text-white"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Step 1: Week Selection */}
        {step === 'selection' && (
          <div className="flex-1 p-8">
            <div className="max-w-2xl mx-auto">
              
              {/* Week Selection Header */}
              <div className="text-center mb-8">
                <div className="flex items-center justify-center space-x-3 mb-4">
                  <Trophy className="h-8 w-8 text-[#FFD63A]" />
                  <h3 className="text-2xl font-bold text-gray-800">Choose Your Achievement</h3>
                </div>
                <p className="text-gray-600">Select which completed week you'd like to share</p>
              </div>
              
              {/* Week Grid */}
              {availableWeeks.length > 0 ? (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 max-h-96 overflow-y-auto">
                  {availableWeeks.map((week) => (
                    <button
                      key={week.week_number}
                      onClick={() => handleWeekSelect(week)}
                      disabled={!week.is_completed}
                      className={`p-6 rounded-2xl border-2 transition-all duration-300 ${
                        week.is_completed
                          ? 'border-gray-200 bg-white text-gray-700 hover:border-[#4ECFBF] hover:shadow-md cursor-pointer'
                          : 'border-gray-100 bg-gray-50 text-gray-400 cursor-not-allowed opacity-60'
                      }`}
                    >
                      <div className="text-center">
                        <div className="text-xl font-bold mb-2">
                          Week {week.week_number}
                        </div>
                        <div className="flex items-center justify-center">
                          <Star className="h-4 w-4 mr-1" />
                          <span className="text-sm">
                            {week.is_completed ? 'Complete' : 'Locked'}
                          </span>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <AlertCircle className="h-12 w-12 mx-auto mb-4" />
                  <p className="text-lg">No weeks found</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Step 3: Sharing */}
        {step === 'sharing' && shareData && (
          <div className="flex-1 overflow-auto">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
              
              {/* Left Column - Image Preview */}
              <div className="flex flex-col">
                <div className="bg-gray-50 rounded-2xl p-6 flex flex-col">
                  <div className="flex items-center space-x-3 mb-4">
                    <Share2 className="h-5 w-5 text-[#FFD63A]" />
                    <h3 className="text-lg font-semibold text-gray-800">Your Achievement Badge</h3>
                  </div>
                  
                  <div className="flex items-center justify-center mb-4">
                    <div className="w-full max-w-xs mx-auto">
                      {shareData.image_base64 ? (
                        <img
                          src={`data:image/png;base64,${shareData.image_base64}`}
                          alt={`Week ${selectedWeek} progress sharing image`}
                          className="w-full rounded-2xl shadow-lg"
                        />
                      ) : (
                        <img
                          src={shareData.image_url}
                          alt={`Week ${selectedWeek} progress sharing image`}
                          className="w-full rounded-2xl shadow-lg"
                        />
                      )}
                    </div>
                  </div>

                  {/* Back Button - Centered below image */}
                  <div className="flex justify-center">
                    <Button
                      onClick={() => setStep('selection')}
                      className="bg-white border-2 border-[#4ECFBF] text-[#4ECFBF] hover:bg-[#4ECFBF] hover:text-white transition-colors px-6 py-2 rounded-xl font-medium"
                    >
                      <ArrowLeft className="h-4 w-4 mr-2" />
                      Choose Different Week
                    </Button>
                  </div>
                </div>
              </div>

              {/* Right Column - Share Options */}
              <div className="space-y-4 flex flex-col">
                
                {/* Share Text */}
                <div className="bg-gray-50 rounded-2xl p-4">
                  <div className="flex items-center space-x-3 mb-3">
                    <Zap className="h-5 w-5 text-[#4ECFBF]" />
                    <h3 className="text-lg font-semibold text-gray-800">Share Your Success</h3>
                  </div>
                  
                  <div className="bg-white rounded-xl p-3 mb-3 border border-gray-200">
                    <p className="text-gray-700 text-sm whitespace-pre-line leading-relaxed">{shareData.share_text}</p>
                    <button
                      onClick={() => copyToClipboard(shareData.share_text)}
                      className="mt-2 text-xs text-[#4ECFBF] hover:text-[#4ECFBF]/80 flex items-center transition-colors"
                    >
                      <Copy className="h-3 w-3 mr-1" />
                      Copy text
                    </button>
                  </div>
                </div>
                
                {/* Action Buttons */}
                <div className="space-y-3">
                  <Button
                    onClick={downloadImage}
                    className="w-full bg-[#E4405F] hover:bg-[#E4405F]/90 text-white font-medium py-3 rounded-xl"
                  >
                    <Instagram className="h-5 w-5 mr-3" />
                    Download for Instagram
                  </Button>
                  
                  <Button
                    onClick={openWhatsAppWeb}
                    className="w-full bg-[#25D366] hover:bg-[#25D366]/90 text-white font-medium py-3 rounded-xl"
                  >
                    <svg className="h-5 w-5 mr-3" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893A11.821 11.821 0 0020.885 3.488"/>
                    </svg>
                    Share on WhatsApp
                  </Button>
                </div>

                {/* Tips */}
                <div className="bg-blue-50 border border-blue-200 rounded-2xl p-4">
                  <div className="flex items-start space-x-3">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <Sparkles className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <h4 className="text-gray-800 font-semibold mb-2">Sharing Tips</h4>
                      <ul className="text-gray-600 text-sm space-y-1">
                        <li>• Download and upload to your favorite social platform</li>
                        <li>• Copy the text for your caption</li>
                        <li>• Share your learning journey with friends</li>
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Success/Error Messages */}
                {copySuccess && (
                  <div className="p-3 bg-green-50 border border-green-200 rounded-xl flex items-center">
                    <CheckCircle className="h-5 w-5 text-green-600 mr-3" />
                    <span className="text-green-700 font-medium text-sm">{copySuccess}</span>
                  </div>
                )}

                {error && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-xl flex items-center">
                    <AlertCircle className="h-5 w-5 text-red-600 mr-3" />
                    <span className="text-red-700 font-medium text-sm">{error}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ShareProgressModal;
