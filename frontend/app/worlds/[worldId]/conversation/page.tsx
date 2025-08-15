'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { worldBuildingAPI, type StoryWorld } from '@/lib/world-building-api';
import { ArrowLeft, MessageCircle, Users, Clock, Globe } from 'lucide-react';

export default function WorldConversationPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const worldId = params.worldId as string;

  const [world, setWorld] = useState<StoryWorld | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load world details
  useEffect(() => {
    const loadWorld = async () => {
      if (!worldId) return;
      
      try {
        setLoading(true);
        setError(null);
        
        const worldData = await worldBuildingAPI.getWorldDetails(worldId);
        setWorld(worldData);
        
      } catch (err) {
        console.error('Error loading world:', err);
        setError(err instanceof Error ? err.message : 'Failed to load world details');
      } finally {
        setLoading(false);
      }
    };

    loadWorld();
  }, [worldId]);

  // Check if user can access conversation
  const canStartConversation = user && world && (
    world.creator_id === user._id || 
    world.contributors.includes(user._id)
  );

  // Handle back navigation
  const handleGoBack = () => {
    router.push(`/worlds/${worldId}`);
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#4ECFBF]/10 to-[#FFD63A]/10 navbar-compensated">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#4ECFBF] mx-auto mb-4"></div>
            <p className="text-gray-600">Loading conversation...</p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !world) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#4ECFBF]/10 to-[#FFD63A]/10 navbar-compensated">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center py-20">
            <MessageCircle className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Conversation Not Available</h2>
            <p className="text-gray-600 mb-4">
              {error || 'Unable to start conversation for this world.'}
            </p>
            <button
              onClick={() => router.push('/worlds')}
              className="bg-[#4ECFBF] text-white px-6 py-2 rounded-lg hover:bg-[#3a9e92] transition-colors"
            >
              <ArrowLeft className="h-4 w-4 inline mr-2" />
              Back to Worlds
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Access denied state
  if (!canStartConversation) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#4ECFBF]/10 to-[#FFD63A]/10 navbar-compensated">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center py-20">
            <Users className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Access Restricted</h2>
            <p className="text-gray-600 mb-4">
              You need to be a contributor or creator of this world to start conversations.
            </p>
            <div className="flex gap-4 justify-center">
              <button
                onClick={() => router.push(`/worlds/${worldId}`)}
                className="bg-[#4ECFBF] text-white px-6 py-2 rounded-lg hover:bg-[#3a9e92] transition-colors"
              >
                View World Details
              </button>
              <button
                onClick={() => router.push('/worlds')}
                className="bg-gray-100 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Back to Worlds
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#4ECFBF]/10 to-[#FFD63A]/10 navbar-compensated">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <button
            onClick={handleGoBack}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-800 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to World
          </button>
          
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">
              Conversation: {world.title}
            </h1>
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <div className="flex items-center gap-1">
                <Globe className="h-4 w-4" />
                {world.language.toUpperCase()}
              </div>
              <div className="flex items-center gap-1">
                <Users className="h-4 w-4" />
                {world.contributors.length} contributors
              </div>
              <div className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                {world.collaboration_settings.session_duration_minutes} min sessions
              </div>
            </div>
          </div>
        </div>

        {/* Coming Soon Message */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
          <MessageCircle className="h-16 w-16 text-[#4ECFBF] mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            Story Conversation Interface Coming Soon
          </h2>
          <p className="text-gray-600 mb-6 max-w-2xl mx-auto">
            The interactive voice conversation feature for story worlds is currently being developed. 
            This will allow you to practice your language skills through immersive storytelling with AI tutors 
            and other contributors.
          </p>
          
          {/* Current Story Context */}
          <div className="bg-gray-50 rounded-lg p-6 mb-6 text-left">
            <h3 className="font-semibold text-gray-800 mb-3">Current Story Context:</h3>
            <p className="text-gray-700 leading-relaxed">
              {world.world_state.current_plot_point}
            </p>
          </div>

          {/* Characters */}
          {world.world_state.active_characters.length > 0 && (
            <div className="bg-gray-50 rounded-lg p-6 mb-6 text-left">
              <h3 className="font-semibold text-gray-800 mb-3">Active Characters:</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {world.world_state.active_characters.map((character, index) => (
                  <div key={index} className="bg-white rounded-lg p-3 border">
                    <h4 className="font-medium text-gray-800">{character.name}</h4>
                    <p className="text-sm text-[#4ECFBF] mb-1">{character.role}</p>
                    <p className="text-gray-600 text-sm">{character.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-4 justify-center">
            <button
              onClick={() => router.push(`/worlds/${worldId}`)}
              className="bg-[#4ECFBF] text-white px-6 py-3 rounded-lg hover:bg-[#3a9e92] transition-colors font-medium"
            >
              Back to World Details
            </button>
            <button
              onClick={() => router.push('/worlds')}
              className="bg-gray-100 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-200 transition-colors font-medium"
            >
              Explore Other Worlds
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
