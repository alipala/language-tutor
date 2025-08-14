'use client';

import { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Send, Clock, FileText, Volume2, Play, Pause } from 'lucide-react';
import { useRealtime } from '@/lib/useRealtime';

interface ContributionFormProps {
  worldId: string;
  previousContribution?: {
    transcript: string;
    contributor_name: string;
    created_at: string;
  };
  onSubmit: (data: {
    transcript?: string;
    audioBlob?: Blob;
    duration: number;
  }) => Promise<void>;
  onCancel: () => void;
  isSubmitting?: boolean;
  minWords?: number;
  maxWords?: number;
  minDuration?: number;
  maxDuration?: number;
}

export default function ContributionForm({
  worldId,
  previousContribution,
  onSubmit,
  onCancel,
  isSubmitting = false,
  minWords = 50,
  maxWords = 500,
  minDuration = 30,
  maxDuration = 300
}: ContributionFormProps) {
  const [transcript, setTranscript] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [contributionMode, setContributionMode] = useState<'text' | 'voice' | 'mixed'>('mixed');
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const recordingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Word and character counting
  const wordCount = transcript.trim().split(/\s+/).filter(word => word.length > 0).length;
  const charCount = transcript.length;
  const isValidLength = wordCount >= minWords && wordCount <= maxWords;
  const isValidDuration = recordingDuration >= minDuration && recordingDuration <= maxDuration;

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current);
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        }
      });
      
      streamRef.current = stream;
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      const chunks: BlobPart[] = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm;codecs=opus' });
        setAudioBlob(blob);
        
        // Create audio URL for playback
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      setRecordingDuration(0);
      
      // Start duration counter
      recordingIntervalRef.current = setInterval(() => {
        setRecordingDuration(prev => {
          const newDuration = prev + 1;
          // Auto-stop at max duration
          if (newDuration >= maxDuration) {
            stopRecording();
          }
          return newDuration;
        });
      }, 1000);
      
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Could not access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current);
        recordingIntervalRef.current = null;
      }
    }
  };

  const playAudio = () => {
    if (audioUrl && audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
      } else {
        audioRef.current.play();
        setIsPlaying(true);
      }
    }
  };

  const handleSubmit = async () => {
    if (isSubmitting) return;

    // Validation
    if (contributionMode === 'text' || contributionMode === 'mixed') {
      if (!transcript.trim()) {
        alert('Please enter your contribution text.');
        return;
      }
      if (!isValidLength) {
        alert(`Your contribution must be between ${minWords} and ${maxWords} words.`);
        return;
      }
    }

    if (contributionMode === 'voice' || contributionMode === 'mixed') {
      if (!audioBlob) {
        alert('Please record your voice contribution.');
        return;
      }
      if (!isValidDuration) {
        alert(`Your recording must be between ${minDuration} and ${maxDuration} seconds.`);
        return;
      }
    }

    try {
      await onSubmit({
        transcript: transcript.trim() || undefined,
        audioBlob: audioBlob || undefined,
        duration: recordingDuration
      });
    } catch (error) {
      console.error('Error submitting contribution:', error);
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Add Your Contribution</h2>
        <p className="text-gray-600">
          Continue the story with your creative input. You can write, record, or do both!
        </p>
      </div>

      {/* Previous Contribution Context */}
      {previousContribution && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg border-l-4 border-blue-500">
          <h3 className="font-semibold text-gray-800 mb-2">Previous Contribution</h3>
          <p className="text-sm text-gray-600 mb-2">
            By {previousContribution.contributor_name} • {new Date(previousContribution.created_at).toLocaleString()}
          </p>
          <p className="text-gray-700 italic">"{previousContribution.transcript}"</p>
        </div>
      )}

      {/* Contribution Mode Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Contribution Mode
        </label>
        <div className="flex space-x-4">
          <button
            onClick={() => setContributionMode('text')}
            className={`flex items-center px-4 py-2 rounded-lg border transition-colors ${
              contributionMode === 'text'
                ? 'bg-blue-500 text-white border-blue-500'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
          >
            <FileText className="h-4 w-4 mr-2" />
            Text Only
          </button>
          <button
            onClick={() => setContributionMode('voice')}
            className={`flex items-center px-4 py-2 rounded-lg border transition-colors ${
              contributionMode === 'voice'
                ? 'bg-blue-500 text-white border-blue-500'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
          >
            <Mic className="h-4 w-4 mr-2" />
            Voice Only
          </button>
          <button
            onClick={() => setContributionMode('mixed')}
            className={`flex items-center px-4 py-2 rounded-lg border transition-colors ${
              contributionMode === 'mixed'
                ? 'bg-blue-500 text-white border-blue-500'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
          >
            <FileText className="h-4 w-4 mr-1" />
            <Mic className="h-4 w-4 mr-2" />
            Both
          </button>
        </div>
      </div>

      {/* Text Input */}
      {(contributionMode === 'text' || contributionMode === 'mixed') && (
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Your Contribution Text
          </label>
          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder="Continue the story... What happens next?"
            className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            disabled={isSubmitting}
          />
          <div className="flex justify-between items-center mt-2 text-sm">
            <span className={`${isValidLength ? 'text-green-600' : 'text-red-500'}`}>
              {wordCount} / {minWords}-{maxWords} words
            </span>
            <span className="text-gray-500">
              {charCount} characters
            </span>
          </div>
        </div>
      )}

      {/* Voice Recording */}
      {(contributionMode === 'voice' || contributionMode === 'mixed') && (
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Voice Recording
          </label>
          
          <div className="border border-gray-300 rounded-lg p-4">
            {/* Recording Controls */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-4">
                <button
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={isSubmitting}
                  className={`flex items-center px-4 py-2 rounded-lg font-medium transition-colors ${
                    isRecording
                      ? 'bg-red-500 text-white hover:bg-red-600'
                      : 'bg-blue-500 text-white hover:bg-blue-600'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {isRecording ? (
                    <>
                      <MicOff className="h-4 w-4 mr-2" />
                      Stop Recording
                    </>
                  ) : (
                    <>
                      <Mic className="h-4 w-4 mr-2" />
                      Start Recording
                    </>
                  )}
                </button>

                {audioBlob && (
                  <button
                    onClick={playAudio}
                    className="flex items-center px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50"
                  >
                    {isPlaying ? (
                      <>
                        <Pause className="h-4 w-4 mr-2" />
                        Pause
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4 mr-2" />
                        Play
                      </>
                    )}
                  </button>
                )}
              </div>

              <div className="flex items-center text-sm text-gray-600">
                <Clock className="h-4 w-4 mr-1" />
                <span className={`font-mono ${isValidDuration ? 'text-green-600' : 'text-red-500'}`}>
                  {formatDuration(recordingDuration)} / {formatDuration(minDuration)}-{formatDuration(maxDuration)}
                </span>
              </div>
            </div>

            {/* Recording Status */}
            {isRecording && (
              <div className="flex items-center justify-center py-4">
                <div className="flex items-center space-x-2 text-red-500">
                  <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                  <span className="font-medium">Recording in progress...</span>
                </div>
              </div>
            )}

            {/* Audio Playback */}
            {audioUrl && (
              <audio
                ref={audioRef}
                src={audioUrl}
                onEnded={() => setIsPlaying(false)}
                className="hidden"
              />
            )}
          </div>
        </div>
      )}

      {/* Guidelines */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg">
        <h4 className="font-medium text-blue-800 mb-2">Contribution Guidelines</h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Build upon the previous contribution naturally</li>
          <li>• Stay consistent with the story's tone and characters</li>
          <li>• Add meaningful development to the plot</li>
          <li>• Keep within the word/time limits</li>
          <li>• Be creative but respectful</li>
        </ul>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-4">
        <button
          onClick={onCancel}
          disabled={isSubmitting}
          className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          disabled={
            isSubmitting || 
            isRecording ||
            (contributionMode !== 'voice' && !isValidLength) ||
            (contributionMode !== 'text' && !isValidDuration) ||
            (contributionMode === 'text' && !transcript.trim()) ||
            (contributionMode === 'voice' && !audioBlob)
          }
          className="flex items-center px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Submitting...
            </>
          ) : (
            <>
              <Send className="h-4 w-4 mr-2" />
              Submit Contribution
            </>
          )}
        </button>
      </div>
    </div>
  );
}
