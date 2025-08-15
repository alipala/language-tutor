'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { worldBuildingAPI, type StoryWorld } from '@/lib/world-building-api';
import { 
  Globe, 
  Users, 
  Clock, 
  BookOpen, 
  MessageCircle, 
  Star, 
  ArrowLeft,
  Play,
  UserPlus,
  Settings,
  Share2,
  Flag,
  Edit
} from 'lucide-react';
import StoryEditModal from '@/components/world-building/StoryEditModal';

export default function WorldDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const worldId = params.worldId as string;

  const [world, setWorld] = useState<StoryWorld | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isJoining, setIsJoining] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);

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

  // Handle joining world
  const handleJoinWorld = async () => {
    if (!world || !user) return;
    
    try {
      setIsJoining(true);
      
      const updatedWorld = await worldBuildingAPI.joinWorld(worldId, user._id);
      if (updatedWorld) {
        setWorld(updatedWorld);
      }
      
    } catch (err) {
      console.error('Error joining world:', err);
      setError(err instanceof Error ? err.message : 'Failed to join world');
    } finally {
      setIsJoining(false);
    }
  };

  // Handle start conversation
  const handleStartConversation = () => {
    router.push(`/worlds/${worldId}/conversation`);
  };

  // Handle edit success
  const handleEditSuccess = (updatedWorld: StoryWorld) => {
    setWorld(updatedWorld);
    setShowEditModal(false);
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#4ECFBF]/10 to-[#FFD63A]/10 navbar-compensated">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#4ECFBF] mx-auto mb-4"></div>
            <p className="text-gray-600">Loading story world...</p>
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
            <Globe className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-800 mb-2">World Not Found</h2>
            <p className="text-gray-600 mb-4">
              {error || 'The story world you\'re looking for doesn\'t exist or is no longer available.'}
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

  const isCreator = user && world.creator_id === user._id;
  const isContributor = user && world.contributors.includes(user._id);
  const canJoin = user && !isContributor && world.contributors.length < world.collaboration_settings.max_contributors;

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#4ECFBF]/10 to-[#FFD63A]/10 navbar-compensated">
      <div className="container mx-auto px-4 py-8">
        {/* Back Button */}
        <button
          onClick={() => router.push('/worlds')}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-800 mb-6 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Worlds
        </button>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Header */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h1 className="text-3xl font-bold text-gray-800 mb-2">{world.title}</h1>
                  <p className="text-gray-600 text-lg">{world.description}</p>
                </div>
                {world.featured && (
                  <div className="flex items-center gap-1 bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-sm">
                    <Star className="h-3 w-3" />
                    Featured
                  </div>
                )}
              </div>

              {/* Metadata */}
              <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                <div className="flex items-center gap-1">
                  <Globe className="h-4 w-4" />
                  {world.language.toUpperCase()}
                </div>
                <div className="flex items-center gap-1">
                  <BookOpen className="h-4 w-4" />
                  {world.target_level}
                </div>
                <div className="flex items-center gap-1">
                  <Users className="h-4 w-4" />
                  {world.contributors.length}/{world.collaboration_settings.max_contributors} contributors
                </div>
                <div className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  {world.collaboration_settings.session_duration_minutes} min sessions
                </div>
              </div>

              {/* Tags */}
              {world.tags.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-4">
                  {world.tags.map((tag, index) => (
                    <span
                      key={index}
                      className="bg-gray-100 text-gray-700 px-2 py-1 rounded-full text-xs"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Current Plot */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <MessageCircle className="h-5 w-5 text-[#4ECFBF]" />
                Current Story
              </h2>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-gray-700 leading-relaxed">
                  {world.world_state.current_plot_point}
                </p>
              </div>
            </div>

            {/* Characters */}
            {world.world_state.active_characters.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h2 className="text-xl font-semibold text-gray-800 mb-4">Characters</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {world.world_state.active_characters.map((character, index) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-4">
                      <h3 className="font-semibold text-gray-800">{character.name}</h3>
                      <p className="text-sm text-[#4ECFBF] mb-2">{character.role}</p>
                      <p className="text-gray-600 text-sm">{character.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Locations */}
            {world.world_state.locations.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h2 className="text-xl font-semibold text-gray-800 mb-4">Locations</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {world.world_state.locations.map((location, index) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-4">
                      <h3 className="font-semibold text-gray-800">{location.name}</h3>
                      <p className="text-gray-600 text-sm">{location.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Important Items */}
            {world.world_state.important_items.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h2 className="text-xl font-semibold text-gray-800 mb-4">Important Items</h2>
                <div className="space-y-3">
                  {world.world_state.important_items.map((item, index) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-4">
                      <h3 className="font-semibold text-gray-800">{item.name}</h3>
                      <p className="text-gray-600 text-sm">{item.significance}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Action Buttons */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="space-y-3">
                {isContributor ? (
                  <button
                    onClick={handleStartConversation}
                    className="w-full bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white py-3 px-4 rounded-lg hover:from-[#3a9e92] hover:to-[#2d7a6e] transition-all duration-300 flex items-center justify-center gap-2 font-medium"
                  >
                    <Play className="h-4 w-4" />
                    Start Conversation
                  </button>
                ) : canJoin ? (
                  <button
                    onClick={handleJoinWorld}
                    disabled={isJoining}
                    className="w-full bg-[#4ECFBF] text-white py-3 px-4 rounded-lg hover:bg-[#3a9e92] transition-colors flex items-center justify-center gap-2 font-medium disabled:opacity-50"
                  >
                    {isJoining ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                    ) : (
                      <UserPlus className="h-4 w-4" />
                    )}
                    {isJoining ? 'Joining...' : 'Join World'}
                  </button>
                ) : !user ? (
                  <button
                    onClick={() => router.push('/auth/login')}
                    className="w-full bg-[#4ECFBF] text-white py-3 px-4 rounded-lg hover:bg-[#3a9e92] transition-colors flex items-center justify-center gap-2 font-medium"
                  >
                    <UserPlus className="h-4 w-4" />
                    Login to Join
                  </button>
                ) : (
                  <div className="text-center text-gray-600 py-3">
                    <Users className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                    <p className="text-sm">World is full</p>
                  </div>
                )}

                {/* Additional Actions */}
                <div className="flex gap-2">
                  <button className="flex-1 bg-gray-100 text-gray-700 py-2 px-3 rounded-lg hover:bg-gray-200 transition-colors flex items-center justify-center gap-2 text-sm">
                    <Share2 className="h-4 w-4" />
                    Share
                  </button>
                  <button className="flex-1 bg-gray-100 text-gray-700 py-2 px-3 rounded-lg hover:bg-gray-200 transition-colors flex items-center justify-center gap-2 text-sm">
                    <Flag className="h-4 w-4" />
                    Report
                  </button>
                </div>

                {isCreator && (
                  <button 
                    onClick={() => setShowEditModal(true)}
                    className="w-full bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200 transition-colors flex items-center justify-center gap-2 text-sm"
                  >
                    <Edit className="h-4 w-4" />
                    Edit Story
                  </button>
                )}
              </div>
            </div>

            {/* Learning Objectives */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Learning Focus</h3>
              
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-700 mb-2">Primary Focus</h4>
                  <span className="bg-[#4ECFBF]/10 text-[#4ECFBF] px-2 py-1 rounded-full text-sm capitalize">
                    {world.learning_objectives.primary_focus}
                  </span>
                </div>

                {world.learning_objectives.vocabulary_themes.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">Vocabulary Themes</h4>
                    <div className="flex flex-wrap gap-1">
                      {world.learning_objectives.vocabulary_themes.map((theme, index) => (
                        <span
                          key={index}
                          className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs"
                        >
                          {theme}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {world.learning_objectives.target_structures.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">Grammar Structures</h4>
                    <div className="flex flex-wrap gap-1">
                      {world.learning_objectives.target_structures.map((structure, index) => (
                        <span
                          key={index}
                          className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs"
                        >
                          {structure}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Statistics */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Statistics</h3>
              
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Sessions</span>
                  <span className="font-medium">{world.statistics.total_sessions}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Contributors</span>
                  <span className="font-medium">{world.statistics.total_contributors}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Average Rating</span>
                  <span className="font-medium">
                    {world.statistics.average_session_rating > 0 
                      ? `${world.statistics.average_session_rating.toFixed(1)}/5` 
                      : 'No ratings yet'
                    }
                  </span>
                </div>
              </div>
            </div>

            {/* World Info */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">World Info</h3>
              
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Created</span>
                  <span className="font-medium">
                    {new Date(world.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Last Updated</span>
                  <span className="font-medium">
                    {new Date(world.updated_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Status</span>
                  <span className={`font-medium capitalize ${
                    world.status === 'active' ? 'text-green-600' : 'text-gray-600'
                  }`}>
                    {world.status}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Privacy</span>
                  <span className="font-medium capitalize">
                    {world.privacy_setting.replace('_', ' ')}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Edit Modal */}
      {world && (
        <StoryEditModal
          world={world}
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
          onSuccess={handleEditSuccess}
        />
      )}
    </div>
  );
}
