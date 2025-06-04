'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { 
  Clock, MessageSquare, Zap, Brain, Target, 
  CheckCircle, AlertTriangle, TrendingUp, Star
} from 'lucide-react';

interface SessionQualityNotificationProps {
  isOpen: boolean;
  onClose: () => void;
  onContinue: () => void;
  onSaveAndLeave: () => void;
  sessionData: {
    duration_minutes: number;
    message_count: number;
    language: string;
    level: string;
    topic?: string;
  };
}

export default function SessionQualityNotification({
  isOpen,
  onClose,
  onContinue,
  onSaveAndLeave,
  sessionData
}: SessionQualityNotificationProps) {
  const [timeToEnhanced, setTimeToEnhanced] = useState(0);
  const [messagesToEnhanced, setMessagesToEnhanced] = useState(0);

  useEffect(() => {
    // Calculate what's needed for enhanced analysis
    const minDuration = 5.0;
    const minMessages = 10;
    
    const durationNeeded = Math.max(0, minDuration - sessionData.duration_minutes);
    const messagesNeeded = Math.max(0, minMessages - sessionData.message_count);
    
    setTimeToEnhanced(durationNeeded);
    setMessagesToEnhanced(messagesNeeded);
  }, [sessionData]);

  const isQualifyingForEnhanced = () => {
    return (sessionData.duration_minutes >= 5.0 && sessionData.message_count >= 10) ||
           (sessionData.duration_minutes >= 3.0 && sessionData.message_count >= 15);
  };

  const getQualityLevel = () => {
    if (isQualifyingForEnhanced()) {
      return 'enhanced';
    }
    return 'basic';
  };

  const getProgressPercentage = () => {
    const durationProgress = Math.min(100, (sessionData.duration_minutes / 5.0) * 100);
    const messageProgress = Math.min(100, (sessionData.message_count / 10) * 100);
    return Math.max(durationProgress, messageProgress);
  };

  const qualityLevel = getQualityLevel();
  const progressPercentage = getProgressPercentage();

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center text-lg font-semibold">
            {qualityLevel === 'enhanced' ? (
              <>
                <CheckCircle className="h-5 w-5 mr-2 text-green-500" />
                Great Session Quality!
              </>
            ) : (
              <>
                <AlertTriangle className="h-5 w-5 mr-2 text-amber-500" />
                Continue for Enhanced Analysis?
              </>
            )}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Current Session Stats */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-medium text-gray-800 mb-3">Current Session</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <Clock className="h-6 w-6 mx-auto mb-1 text-blue-500" />
                <div className="text-lg font-bold text-gray-800">
                  {Math.floor(sessionData.duration_minutes)}:{((sessionData.duration_minutes % 1) * 60).toFixed(0).padStart(2, '0')}
                </div>
                <div className="text-xs text-gray-600">Minutes</div>
              </div>
              <div className="text-center">
                <MessageSquare className="h-6 w-6 mx-auto mb-1 text-green-500" />
                <div className="text-lg font-bold text-gray-800">{sessionData.message_count}</div>
                <div className="text-xs text-gray-600">Messages</div>
              </div>
            </div>
          </div>

          {/* Analysis Level Indicator */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Analysis Level</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                qualityLevel === 'enhanced' 
                  ? 'bg-green-100 text-green-700' 
                  : 'bg-amber-100 text-amber-700'
              }`}>
                {qualityLevel === 'enhanced' ? 'Enhanced' : 'Basic'}
              </span>
            </div>
            
            <Progress value={progressPercentage} className="h-2" />
            
            <div className="text-xs text-gray-600">
              {qualityLevel === 'enhanced' 
                ? 'Your session qualifies for detailed AI analysis!'
                : `${Math.round(progressPercentage)}% towards enhanced analysis`
              }
            </div>
          </div>

          {/* What You'll Get */}
          <div className="space-y-4">
            <h3 className="font-medium text-gray-800">What you'll receive:</h3>
            
            {qualityLevel === 'enhanced' ? (
              <div className="space-y-3">
                <div className="flex items-start space-x-3 p-3 bg-green-50 rounded-lg">
                  <Brain className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="font-medium text-green-800 text-sm">Enhanced AI Analysis</div>
                    <div className="text-green-700 text-xs">Detailed insights, progress tracking, and personalized recommendations</div>
                  </div>
                </div>
                <div className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
                  <Target className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="font-medium text-blue-800 text-sm">Quality Metrics</div>
                    <div className="text-blue-700 text-xs">Engagement score, topic depth, and conversation quality</div>
                  </div>
                </div>
                <div className="flex items-start space-x-3 p-3 bg-purple-50 rounded-lg">
                  <TrendingUp className="h-5 w-5 text-purple-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="font-medium text-purple-800 text-sm">Progress Indicators</div>
                    <div className="text-purple-700 text-xs">Learning trends and improvement suggestions</div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                  <MessageSquare className="h-5 w-5 text-gray-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="font-medium text-gray-800 text-sm">Basic Summary</div>
                    <div className="text-gray-600 text-xs">Conversation overview and key topics discussed</div>
                  </div>
                </div>
                
                {timeToEnhanced > 0 && (
                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                    <div className="flex items-center space-x-2 mb-2">
                      <Zap className="h-4 w-4 text-amber-600" />
                      <span className="font-medium text-amber-800 text-sm">Continue for Enhanced Analysis</span>
                    </div>
                    <div className="text-amber-700 text-xs space-y-1">
                      {timeToEnhanced > 0 && (
                        <div>• Practice for {Math.ceil(timeToEnhanced)} more minutes</div>
                      )}
                      {messagesToEnhanced > 0 && (
                        <div>• Have {messagesToEnhanced} more conversation exchanges</div>
                      )}
                      <div className="mt-2 font-medium">Get detailed AI insights, progress tracking, and personalized recommendations!</div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col space-y-3">
            {qualityLevel === 'enhanced' ? (
              <>
                <Button
                  onClick={onSaveAndLeave}
                  className="w-full bg-green-600 hover:bg-green-700 text-white"
                >
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Save with Enhanced Analysis
                </Button>
                <Button
                  onClick={onContinue}
                  variant="outline"
                  className="w-full"
                >
                  Continue Practicing
                </Button>
              </>
            ) : (
              <>
                <Button
                  onClick={onContinue}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                >
                  <Star className="h-4 w-4 mr-2" />
                  Continue for Enhanced Analysis
                </Button>
                <Button
                  onClick={onSaveAndLeave}
                  variant="outline"
                  className="w-full"
                >
                  Save with Basic Summary
                </Button>
              </>
            )}
          </div>

          {/* Benefits Reminder */}
          {qualityLevel === 'basic' && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="text-center">
                <Brain className="h-6 w-6 mx-auto mb-2 text-blue-600" />
                <div className="font-medium text-blue-800 text-sm mb-1">
                  Enhanced Analysis Benefits
                </div>
                <div className="text-blue-700 text-xs">
                  Get the same detailed insights as our sentence assessment tool, but for your entire conversation!
                </div>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
