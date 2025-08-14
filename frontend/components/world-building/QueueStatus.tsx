'use client';

import { useState, useEffect } from 'react';
import { Clock, Users, Play, SkipForward, AlertCircle, CheckCircle } from 'lucide-react';

interface QueueStatusProps {
  worldId: string;
  onContribute: () => void;
  onSkipTurn: () => void;
  refreshInterval?: number;
}

interface QueueData {
  queue_type: 'sequential' | 'random' | 'scheduled';
  can_contribute: boolean;
  your_turn: boolean;
  position: number;
  total_contributors: number;
  estimated_wait_minutes: number;
  message: string;
  current_contributor?: {
    id: string;
    name: string;
    email: string;
  };
  session_duration_minutes?: number;
  slot_end?: string;
  remaining_minutes?: number;
  next_slot_start?: string;
  wait_minutes?: number;
}

export default function QueueStatus({
  worldId,
  onContribute,
  onSkipTurn,
  refreshInterval = 30000 // 30 seconds
}: QueueStatusProps) {
  const [queueData, setQueueData] = useState<QueueData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSkipping, setIsSkipping] = useState(false);

  const fetchQueueStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch(`/api/v2/worlds/${worldId}/queue/status`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch queue status');
      }

      const data = await response.json();
      setQueueData(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching queue status:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch queue status');
    } finally {
      setLoading(false);
    }
  };

  const handleSkipTurn = async () => {
    if (!queueData?.your_turn || isSkipping) return;

    setIsSkipping(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch(`/api/v2/worlds/${worldId}/queue/skip`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to skip turn');
      }

      // Refresh queue status after skipping
      await fetchQueueStatus();
      onSkipTurn();
    } catch (err) {
      console.error('Error skipping turn:', err);
      setError(err instanceof Error ? err.message : 'Failed to skip turn');
    } finally {
      setIsSkipping(false);
    }
  };

  useEffect(() => {
    fetchQueueStatus();

    // Set up polling for queue status updates
    const interval = setInterval(fetchQueueStatus, refreshInterval);

    return () => clearInterval(interval);
  }, [worldId, refreshInterval]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <span className="ml-3 text-gray-600">Loading queue status...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center text-red-600 mb-4">
          <AlertCircle className="h-5 w-5 mr-2" />
          <span className="font-medium">Error loading queue status</span>
        </div>
        <p className="text-gray-600 mb-4">{error}</p>
        <button
          onClick={fetchQueueStatus}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!queueData) {
    return null;
  }

  const formatTimeRemaining = (minutes: number) => {
    if (minutes < 60) {
      return `${minutes} minute${minutes !== 1 ? 's' : ''}`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}h ${remainingMinutes}m`;
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-gray-800">Contribution Queue</h3>
        <div className="flex items-center text-sm text-gray-500">
          <Clock className="h-4 w-4 mr-1" />
          <span>Updates every {refreshInterval / 1000}s</span>
        </div>
      </div>

      {/* Queue Type Badge */}
      <div className="mb-4">
        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
          queueData.queue_type === 'sequential' 
            ? 'bg-blue-100 text-blue-800'
            : queueData.queue_type === 'scheduled'
            ? 'bg-purple-100 text-purple-800'
            : 'bg-green-100 text-green-800'
        }`}>
          {queueData.queue_type === 'sequential' && 'Sequential Order'}
          {queueData.queue_type === 'scheduled' && 'Scheduled Slots'}
          {queueData.queue_type === 'random' && 'Open Contribution'}
        </span>
      </div>

      {/* Your Turn Status */}
      {queueData.your_turn ? (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center mb-3">
            <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
            <span className="font-semibold text-green-800">It's your turn!</span>
          </div>
          <p className="text-green-700 mb-4">{queueData.message}</p>
          
          {/* Scheduled slot countdown */}
          {queueData.queue_type === 'scheduled' && queueData.remaining_minutes !== undefined && (
            <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
              <div className="flex items-center text-yellow-800">
                <Clock className="h-4 w-4 mr-2" />
                <span className="font-medium">
                  Time remaining: {formatTimeRemaining(queueData.remaining_minutes)}
                </span>
              </div>
            </div>
          )}

          <div className="flex space-x-3">
            <button
              onClick={onContribute}
              className="flex items-center px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 font-medium"
            >
              <Play className="h-4 w-4 mr-2" />
              Start Contributing
            </button>
            
            {queueData.queue_type === 'sequential' && (
              <button
                onClick={handleSkipTurn}
                disabled={isSkipping}
                className="flex items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSkipping ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600 mr-2"></div>
                    Skipping...
                  </>
                ) : (
                  <>
                    <SkipForward className="h-4 w-4 mr-2" />
                    Skip Turn
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="flex items-center mb-3">
            <Clock className="h-5 w-5 text-gray-600 mr-2" />
            <span className="font-semibold text-gray-800">Waiting for your turn</span>
          </div>
          <p className="text-gray-700 mb-4">{queueData.message}</p>

          {/* Queue Position Info */}
          {queueData.queue_type === 'sequential' && queueData.position > 0 && (
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="text-center p-3 bg-white rounded border">
                <div className="text-2xl font-bold text-blue-600">{queueData.position}</div>
                <div className="text-sm text-gray-600">Position in queue</div>
              </div>
              <div className="text-center p-3 bg-white rounded border">
                <div className="text-2xl font-bold text-purple-600">
                  {formatTimeRemaining(queueData.estimated_wait_minutes)}
                </div>
                <div className="text-sm text-gray-600">Estimated wait</div>
              </div>
            </div>
          )}

          {/* Scheduled slot info */}
          {queueData.queue_type === 'scheduled' && queueData.next_slot_start && (
            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
              <div className="flex items-center text-blue-800">
                <Clock className="h-4 w-4 mr-2" />
                <span className="font-medium">
                  Next slot: {new Date(queueData.next_slot_start).toLocaleString()}
                </span>
              </div>
              {queueData.wait_minutes !== undefined && (
                <div className="text-sm text-blue-600 mt-1">
                  Starts in {formatTimeRemaining(queueData.wait_minutes)}
                </div>
              )}
            </div>
          )}

          {/* Current contributor info */}
          {queueData.current_contributor && (
            <div className="p-3 bg-yellow-50 border border-yellow-200 rounded">
              <div className="text-sm text-yellow-800">
                <span className="font-medium">Current contributor:</span> {queueData.current_contributor.name}
              </div>
              {queueData.session_duration_minutes && (
                <div className="text-sm text-yellow-600 mt-1">
                  Session duration: {queueData.session_duration_minutes} minutes
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Queue Overview */}
      {queueData.queue_type !== 'random' && (
        <div className="border-t pt-4">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div className="flex items-center">
              <Users className="h-4 w-4 mr-1" />
              <span>{queueData.total_contributors} contributors</span>
            </div>
            <div className="flex items-center">
              <Clock className="h-4 w-4 mr-1" />
              <span>
                {queueData.session_duration_minutes || 10} min sessions
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Random contribution mode */}
      {queueData.queue_type === 'random' && queueData.can_contribute && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center mb-3">
            <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
            <span className="font-semibold text-green-800">Open Contribution</span>
          </div>
          <p className="text-green-700 mb-4">Anyone can contribute at any time!</p>
          <button
            onClick={onContribute}
            className="flex items-center px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 font-medium"
          >
            <Play className="h-4 w-4 mr-2" />
            Add Your Contribution
          </button>
        </div>
      )}
    </div>
  );
}
