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
  Smartphone,
  Monitor,
  QrCode,
  ExternalLink
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

export const ShareProgressModal: React.FC<ShareProgressModalProps> = ({
  isOpen,
  onClose,
  assessmentData,
  learningPlanData,
  assessmentId,
  learningPlanId
}) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [shareData, setShareData] = useState<ShareResponse | null>(null);
  const [selectedPlatform, setSelectedPlatform] = useState<'instagram' | 'whatsapp' | 'general'>('instagram');
  const [shareType, setShareType] = useState<'progress' | 'achievement' | 'milestone'>('progress');
  const [error, setError] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState<string | null>(null);
  const [customMessage, setCustomMessage] = useState('');

  // Reset state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setShareData(null);
      setError(null);
      setCopySuccess(null);
      setCustomMessage('');
    }
  }, [isOpen]);

  // Auto-generate image when modal opens
  useEffect(() => {
    if (isOpen && !shareData && !isGenerating) {
      generateProgressImage();
    }
  }, [isOpen, selectedPlatform, shareType]);

  const generateProgressImage = async () => {
    setIsGenerating(true);
    setError(null);

    try {
      const response = await fetch('/api/share/generate-progress-image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          assessment_id: assessmentId,
          learning_plan_id: learningPlanId,
          share_type: shareType,
          platform: selectedPlatform,
          custom_message: customMessage || undefined
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate progress image');
      }

      const data: ShareResponse = await response.json();
      setShareData(data);
    } catch (err) {
      console.error('Error generating progress image:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate progress image');
    } finally {
      setIsGenerating(false);
    }
  };

  const handlePlatformChange = (platform: 'instagram' | 'whatsapp' | 'general') => {
    setSelectedPlatform(platform);
    setShareData(null); // Reset to regenerate with new platform
  };

  const handleShareTypeChange = (type: 'progress' | 'achievement' | 'milestone') => {
    setShareType(type);
    setShareData(null); // Reset to regenerate with new type
  };

  const downloadImage = async () => {
    if (!shareData?.image_url) return;

    try {
      const response = await fetch(shareData.image_url);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `tacoai-progress-${selectedPlatform}-${Date.now()}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error downloading image:', err);
      setError('Failed to download image');
    }
  };

  const copyToClipboard = async (text: string, type: 'text' | 'image' = 'text') => {
    try {
      if (type === 'image' && shareData?.image_base64) {
        // Copy image to clipboard (modern browsers)
        if (navigator.clipboard && window.ClipboardItem) {
          const response = await fetch(shareData.image_url);
          const blob = await response.blob();
          await navigator.clipboard.write([
            new ClipboardItem({ [blob.type]: blob })
          ]);
          setCopySuccess('Image copied to clipboard!');
        } else {
          // Fallback: copy image URL
          await navigator.clipboard.writeText(shareData.image_url);
          setCopySuccess('Image URL copied to clipboard!');
        }
      } else {
        // Copy text
        await navigator.clipboard.writeText(text);
        setCopySuccess('Text copied to clipboard!');
      }
      
      setTimeout(() => setCopySuccess(null), 3000);
    } catch (err) {
      console.error('Error copying to clipboard:', err);
      setError('Failed to copy to clipboard');
    }
  };

  const shareViaWebAPI = async () => {
    if (!shareData || !navigator.share) {
      setError('Web Share API not supported on this device');
      return;
    }

    try {
      // Fetch the image as a blob
      const response = await fetch(shareData.image_url);
      const blob = await response.blob();
      const file = new File([blob], 'tacoai-progress.png', { type: blob.type });

      await navigator.share({
        title: 'My Language Learning Progress',
        text: shareData.share_text,
        files: [file]
      });
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        console.error('Error sharing via Web API:', err);
        setError('Failed to share via Web Share API');
      }
    }
  };

  const openInstagramWeb = () => {
    // Instagram doesn't support direct posting from web, but we can guide users
    const instagramUrl = 'https://www.instagram.com/';
    window.open(instagramUrl, '_blank');
    setCopySuccess('Download the image and upload it to Instagram!');
  };

  const openWhatsAppWeb = () => {
    if (shareData) {
      const whatsappUrl = `https://web.whatsapp.com/send?text=${encodeURIComponent(shareData.share_text)}`;
      window.open(whatsappUrl, '_blank');
      setCopySuccess('Image copied! Paste it in WhatsApp Web.');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center">
            <Share2 className="h-6 w-6 mr-3" style={{ color: '#4ECFBF' }} />
            <h2 className="text-xl font-bold text-gray-800">Share Your Progress</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        <div className="p-6">
          {/* Platform Selection */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Choose Platform</h3>
            <div className="grid grid-cols-3 gap-3">
              <button
                onClick={() => handlePlatformChange('instagram')}
                className={`p-4 rounded-xl border-2 transition-all ${
                  selectedPlatform === 'instagram'
                    ? 'border-pink-500 bg-pink-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <Instagram className="h-6 w-6 mx-auto mb-2 text-pink-500" />
                <div className="text-sm font-medium">Instagram</div>
              </button>
              <button
                onClick={() => handlePlatformChange('whatsapp')}
                className={`p-4 rounded-xl border-2 transition-all ${
                  selectedPlatform === 'whatsapp'
                    ? 'border-green-500 bg-green-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <MessageCircle className="h-6 w-6 mx-auto mb-2 text-green-500" />
                <div className="text-sm font-medium">WhatsApp</div>
              </button>
              <button
                onClick={() => handlePlatformChange('general')}
                className={`p-4 rounded-xl border-2 transition-all ${
                  selectedPlatform === 'general'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <Share2 className="h-6 w-6 mx-auto mb-2 text-blue-500" />
                <div className="text-sm font-medium">General</div>
              </button>
            </div>
          </div>

          {/* Share Type Selection */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Share Type</h3>
            <div className="grid grid-cols-3 gap-3">
              <button
                onClick={() => handleShareTypeChange('progress')}
                className={`p-3 rounded-lg border-2 transition-all text-sm ${
                  shareType === 'progress'
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                Progress Update
              </button>
              <button
                onClick={() => handleShareTypeChange('achievement')}
                className={`p-3 rounded-lg border-2 transition-all text-sm ${
                  shareType === 'achievement'
                    ? 'border-yellow-500 bg-yellow-50 text-yellow-700'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                Achievement
              </button>
              <button
                onClick={() => handleShareTypeChange('milestone')}
                className={`p-3 rounded-lg border-2 transition-all text-sm ${
                  shareType === 'milestone'
                    ? 'border-purple-500 bg-purple-50 text-purple-700'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                Milestone
              </button>
            </div>
          </div>

          {/* Generated Image Preview */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Preview</h3>
            <div className="bg-gray-50 rounded-xl p-4 min-h-[300px] flex items-center justify-center">
              {isGenerating ? (
                <div className="text-center">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto mb-3" style={{ color: '#4ECFBF' }} />
                  <p className="text-gray-600">Generating your progress image...</p>
                </div>
              ) : error ? (
                <div className="text-center">
                  <AlertCircle className="h-8 w-8 mx-auto mb-3 text-red-500" />
                  <p className="text-red-600 mb-3">{error}</p>
                  <Button
                    onClick={generateProgressImage}
                    variant="outline"
                    size="sm"
                  >
                    Try Again
                  </Button>
                </div>
              ) : shareData ? (
                <div className="w-full">
                  <img
                    src={shareData.image_url}
                    alt="Progress sharing image"
                    className="w-full max-w-md mx-auto rounded-lg shadow-lg"
                  />
                </div>
              ) : null}
            </div>
          </div>

          {/* Share Text Preview */}
          {shareData && (
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Share Text</h3>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-700 whitespace-pre-line">{shareData.share_text}</p>
                <button
                  onClick={() => copyToClipboard(shareData.share_text)}
                  className="mt-2 text-xs text-blue-600 hover:text-blue-700 flex items-center"
                >
                  <Copy className="h-3 w-3 mr-1" />
                  Copy text
                </button>
              </div>
            </div>
          )}

          {/* Success/Error Messages */}
          {copySuccess && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-center">
              <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
              <span className="text-sm text-green-700">{copySuccess}</span>
            </div>
          )}

          {/* Desktop Sharing Instructions */}
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start">
              <Monitor className="h-5 w-5 text-blue-600 mr-3 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-blue-800 mb-1">Desktop Sharing Tips</h4>
                <ul className="text-xs text-blue-700 space-y-1">
                  <li>• Download the image and upload it manually to your social media</li>
                  <li>• Copy the text and paste it as your caption</li>
                  <li>• Use the Web Share API if your browser supports it</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          {shareData && (
            <div className="space-y-3">
              {/* Primary sharing options */}
              <div className="grid grid-cols-2 gap-3">
                {typeof navigator !== 'undefined' && navigator.share && (
                  <Button
                    onClick={shareViaWebAPI}
                    className="flex items-center justify-center"
                    style={{ backgroundColor: '#4ECFBF' }}
                  >
                    <Share2 className="h-4 w-4 mr-2" />
                    Share via System
                  </Button>
                )}
                <Button
                  onClick={downloadImage}
                  variant="outline"
                  className="flex items-center justify-center"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download Image
                </Button>
              </div>

              {/* Platform-specific actions */}
              <div className="grid grid-cols-2 gap-3">
                {selectedPlatform === 'instagram' && (
                  <Button
                    onClick={openInstagramWeb}
                    variant="outline"
                    className="flex items-center justify-center border-pink-200 text-pink-600 hover:bg-pink-50"
                  >
                    <Instagram className="h-4 w-4 mr-2" />
                    Open Instagram
                  </Button>
                )}
                {selectedPlatform === 'whatsapp' && (
                  <Button
                    onClick={openWhatsAppWeb}
                    variant="outline"
                    className="flex items-center justify-center border-green-200 text-green-600 hover:bg-green-50"
                  >
                    <MessageCircle className="h-4 w-4 mr-2" />
                    Open WhatsApp Web
                  </Button>
                )}
                <Button
                  onClick={() => copyToClipboard('', 'image')}
                  variant="outline"
                  className="flex items-center justify-center"
                >
                  <Copy className="h-4 w-4 mr-2" />
                  Copy Image
                </Button>
              </div>

              {/* Mobile QR Code option (future enhancement) */}
              <div className="pt-3 border-t border-gray-200">
                <div className="flex items-center justify-center text-xs text-gray-500">
                  <Smartphone className="h-3 w-3 mr-1" />
                  For easier mobile sharing, scan with your phone camera
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ShareProgressModal;
