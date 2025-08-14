'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { StoryWorld, LANGUAGE_OPTIONS, LEVEL_OPTIONS, GENRE_OPTIONS } from '@/lib/world-building-api';
import { X, Users, Clock, Star, Globe, BookOpen, MapPin, User, Package, Target, Calendar, TrendingUp, Mic, Play, Volume2 } from 'lucide-react';
import StoryConversationInterface from './StoryConversationInterface';

interface WorldDetailsModalProps {
  world: StoryWorld;
  isOpen: boolean;
  onClose: () => void;
}

export default function WorldDetailsModal({ world, isOpen, onClose }: WorldDetailsModalProps) {
  const router = useRouter();
  const [showStorySession, setShowStorySession] = useState(false);

  if (!isOpen) return null;

  // If story session is shown, render it instead of the modal
  if (showStorySession) {
    return (
      <StoryConversationInterface
        world={world}
        onComplete={(result: { success: boolean; message: string; duration_seconds: number }) => {
          console.log('Story session completed:', result);
          setShowStorySession(false);
          // TODO: Handle session completion (refresh world data, show success message, etc.)
        }}
        onCancel={() => setShowStorySession(false)}
      />
    );
  }

  // Get display info for language, level, and genre
  const languageInfo = LANGUAGE_OPTIONS.find(lang => lang.value === world.language);
  const levelInfo = LEVEL_OPTIONS.find(level => level.value === world.target_level);
  const genreInfo = GENRE_OPTIONS.find(genre => genre.value === world.genre);

  // Format dates
  const createdDate = new Date(world.created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
  
  const lastContributionDate = world.last_contribution_at 
    ? new Date(world.last_contribution_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    : null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div 
          className="relative bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Globe className="h-6 w-6 text-[#4ECFBF]" />
              <h2 className="text-2xl font-bold text-gray-800">{world.title}</h2>
              {world.featured && (
                <Star className="h-5 w-5 text-[#FFD63A] fill-current" />
              )}
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            >
              <X className="h-6 w-6 text-gray-500" />
            </button>
          </div>

          {/* Content */}
          <div className="overflow-y-auto max-h-[calc(90vh-80px)]">
            <div className="p-6 space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center gap-2 p-3 bg-[#4ECFBF]/10 rounded-lg">
                  <span className="text-2xl">{languageInfo?.flag}</span>
                  <div>
                    <p className="text-sm text-gray-600">Language</p>
                    <p className="font-semibold text-[#4ECFBF]">{languageInfo?.label}</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-2 p-3 rounded-lg" style={{ backgroundColor: `${levelInfo?.color}20` }}>
                  <div 
                    className="w-6 h-6 rounded-full"
                    style={{ backgroundColor: levelInfo?.color }}
                  />
                  <div>
                    <p className="text-sm text-gray-600">Level</p>
                    <p className="font-semibold" style={{ color: levelInfo?.color }}>
                      {levelInfo?.label}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
                  <span className="text-2xl">{genreInfo?.icon}</span>
                  <div>
                    <p className="text-sm text-gray-600">Genre</p>
                    <p className="font-semibold text-gray-800">{genreInfo?.label}</p>
                  </div>
                </div>
              </div>

              {/* Description */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">Story Description</h3>
                <p className="text-gray-700 leading-relaxed">{world.description}</p>
              </div>

              {/* Learning Objectives */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  <Target className="h-5 w-5 text-[#4ECFBF]" />
                  Learning Objectives
                </h3>
                <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                  <div>
                    <p className="text-sm font-medium text-gray-600 mb-1">Primary Focus</p>
                    <span className="inline-flex items-center gap-1 px-3 py-1 bg-[#4ECFBF] text-white rounded-full text-sm font-medium">
                      <BookOpen className="h-4 w-4" />
                      {world.learning_objectives.primary_focus.charAt(0).toUpperCase() + world.learning_objectives.primary_focus.slice(1)}
                    </span>
                  </div>
                  
                  {world.learning_objectives.target_structures.length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-gray-800 mb-2">Target Grammar Structures</p>
                      <div className="flex flex-wrap gap-2">
                        {world.learning_objectives.target_structures.map((structure, index) => (
                          <span key={index} className="px-2 py-1 bg-white border border-gray-200 rounded-md text-sm text-gray-700">
                            {structure}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {world.learning_objectives.vocabulary_themes.length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-gray-800 mb-2">Vocabulary Themes</p>
                      <div className="flex flex-wrap gap-2">
                        {world.learning_objectives.vocabulary_themes.map((theme, index) => (
                          <span key={index} className="px-2 py-1 bg-white border border-gray-200 rounded-md text-sm text-gray-700">
                            {theme}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Current World State */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  <Globe className="h-5 w-5 text-[#4ECFBF]" />
                  Current Story State
                </h3>
                <div className="bg-gradient-to-br from-[#4ECFBF]/5 to-[#FFD63A]/5 rounded-lg p-4 space-y-4">
                  {/* Current Plot Point */}
                  <div>
                    <p className="text-sm font-medium text-gray-600 mb-2">Current Scene</p>
                    <p className="text-gray-800 italic">"{world.world_state.current_plot_point}"</p>
                  </div>

                  {/* Characters, Locations, Items */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Characters */}
                    <div>
                      <p className="text-sm font-medium text-gray-800 mb-2 flex items-center gap-1">
                        <User className="h-4 w-4" />
                        Active Characters ({world.world_state.active_characters.length})
                      </p>
                      <div className="space-y-2">
                        {world.world_state.active_characters.slice(0, 3).map((character, index) => (
                          <div key={index} className="bg-white rounded-md p-2 border border-gray-200">
                            <p className="font-medium text-sm text-gray-700">{character.name}</p>
                            <p className="text-xs text-gray-600">{character.role}</p>
                          </div>
                        ))}
                        {world.world_state.active_characters.length > 3 && (
                          <p className="text-xs text-gray-500">+{world.world_state.active_characters.length - 3} more</p>
                        )}
                      </div>
                    </div>

                    {/* Locations */}
                    <div>
                      <p className="text-sm font-medium text-gray-800 mb-2 flex items-center gap-1">
                        <MapPin className="h-4 w-4" />
                        Locations ({world.world_state.locations.length})
                      </p>
                      <div className="space-y-2">
                        {world.world_state.locations.slice(0, 3).map((location, index) => (
                          <div key={index} className="bg-white rounded-md p-2 border border-gray-200">
                            <p className="font-medium text-sm text-gray-700">{location.name}</p>
                          </div>
                        ))}
                        {world.world_state.locations.length > 3 && (
                          <p className="text-xs text-gray-500">+{world.world_state.locations.length - 3} more</p>
                        )}
                      </div>
                    </div>

                    {/* Important Items */}
                    <div>
                      <p className="text-sm font-medium text-gray-800 mb-2 flex items-center gap-1">
                        <Package className="h-4 w-4" />
                        Key Items ({world.world_state.important_items.length})
                      </p>
                      <div className="space-y-2">
                        {world.world_state.important_items.slice(0, 3).map((item, index) => (
                          <div key={index} className="bg-white rounded-md p-2 border border-gray-200">
                            <p className="font-medium text-sm text-gray-700">{item.name}</p>
                          </div>
                        ))}
                        {world.world_state.important_items.length > 3 && (
                          <p className="text-xs text-gray-500">+{world.world_state.important_items.length - 3} more</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Collaboration Settings */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  <Users className="h-5 w-5 text-[#4ECFBF]" />
                  Collaboration Details
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <Users className="h-6 w-6 text-[#4ECFBF] mx-auto mb-1" />
                    <p className="text-sm text-gray-600">Max Contributors</p>
                    <p className="font-semibold text-gray-800">{world.collaboration_settings.max_contributors}</p>
                  </div>
                  
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <Clock className="h-6 w-6 text-[#FFD63A] mx-auto mb-1" />
                    <p className="text-sm text-gray-600">Session Length</p>
                    <p className="font-semibold text-gray-800">{world.collaboration_settings.session_duration_minutes} min</p>
                  </div>
                  
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <div className={`h-6 w-6 mx-auto mb-1 rounded-full ${world.collaboration_settings.requires_approval ? 'bg-yellow-400' : 'bg-green-400'}`} />
                    <p className="text-sm text-gray-600">Approval</p>
                    <p className="font-semibold text-gray-800">{world.collaboration_settings.requires_approval ? 'Required' : 'Open'}</p>
                  </div>
                  
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <TrendingUp className="h-6 w-6 text-[#F75A5A] mx-auto mb-1" />
                    <p className="text-sm text-gray-600">Order</p>
                    <p className="font-semibold text-gray-800 capitalize">{world.collaboration_settings.contribution_order}</p>
                  </div>
                </div>
              </div>

              {/* Statistics */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-[#4ECFBF]" />
                  World Statistics
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div className="text-center p-3 bg-gradient-to-br from-[#4ECFBF]/10 to-[#4ECFBF]/5 rounded-lg">
                    <p className="text-2xl font-bold text-[#4ECFBF]">{world.statistics.total_sessions}</p>
                    <p className="text-sm text-gray-600">Total Sessions</p>
                  </div>
                  
                  <div className="text-center p-3 bg-gradient-to-br from-[#FFD63A]/10 to-[#FFD63A]/5 rounded-lg">
                    <p className="text-2xl font-bold text-[#FFD63A]">{world.statistics.total_contributors}</p>
                    <p className="text-sm text-gray-600">Contributors</p>
                  </div>
                  
                  <div className="text-center p-3 bg-gradient-to-br from-[#F75A5A]/10 to-[#F75A5A]/5 rounded-lg">
                    <p className="text-2xl font-bold text-[#F75A5A]">{world.statistics.average_session_rating.toFixed(1)}</p>
                    <p className="text-sm text-gray-600">Avg Rating</p>
                  </div>
                  
                  <div className="text-center p-3 bg-gradient-to-br from-[#FFA955]/10 to-[#FFA955]/5 rounded-lg">
                    <p className="text-2xl font-bold text-[#FFA955]">{Math.round(world.statistics.completion_rate * 100)}%</p>
                    <p className="text-sm text-gray-600">Completion</p>
                  </div>
                  
                  <div className="text-center p-3 bg-gradient-to-br from-green-500/10 to-green-500/5 rounded-lg">
                    <p className="text-2xl font-bold text-green-600">{Math.round(world.statistics.learning_effectiveness_score * 100)}%</p>
                    <p className="text-sm text-gray-600">Effectiveness</p>
                  </div>
                </div>
              </div>

              {/* Tags */}
              {world.tags.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-3">Tags</h3>
                  <div className="flex flex-wrap gap-2">
                    {world.tags.map((tag, index) => (
                      <span 
                        key={index}
                        className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Meta Information */}
              <div className="border-t border-gray-200 pt-4">
                <div className="flex items-center justify-between text-sm text-gray-600">
                  <div className="flex items-center gap-4">
                    <span className="flex items-center gap-1">
                      <Calendar className="h-4 w-4" />
                      Created {createdDate}
                    </span>
                    <span>by {world.creator_name || 'Anonymous'}</span>
                  </div>
                  {lastContributionDate && (
                    <span>Last activity: {lastContributionDate}</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <div className={`w-3 h-3 rounded-full ${
                  world.status === 'active' ? 'bg-green-400' :
                  world.status === 'paused' ? 'bg-yellow-400' :
                  world.status === 'completed' ? 'bg-blue-400' :
                  'bg-gray-400'
                }`} />
                <span className="capitalize">{world.status}</span>
                <span>•</span>
                <span className="capitalize">{world.privacy_setting.replace('_', ' ')}</span>
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={onClose}
                  className="px-4 py-2 bg-[#F75A5A] text-white border border-[#F75A5A] rounded-lg hover:bg-[#e54545] transition-colors"
                >
                  Close
                </button>
                
                {/* Single Story Conversation Button */}
                <button
                  onClick={() => {
                    const worldId = world.id || (world as any)._id;
                    router.push(`/story-conversation?world=${worldId}`);
                  }}
                  className="flex items-center gap-3 px-6 py-3 bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white rounded-lg font-medium hover:from-[#3a9e92] hover:to-[#2d7a6e] transition-all duration-300 shadow-lg"
                  title="Join the collaborative story conversation - Practice language skills while contributing to the story"
                >
                  <Mic className="h-5 w-5" />
                  Join Story Conversation
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
