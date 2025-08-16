'use client';

import { StoryWorld, LANGUAGE_OPTIONS, LEVEL_OPTIONS, GENRE_OPTIONS } from '@/lib/world-building-api';
import { Users, Clock, Star, Globe, BookOpen } from 'lucide-react';

interface WorldCardProps {
  world: StoryWorld;
  onClick: () => void;
}

export default function WorldCard({ world, onClick }: WorldCardProps) {
  // Get display info for language, level, and genre
  const languageInfo = LANGUAGE_OPTIONS.find(lang => lang.value === world.language);
  const levelInfo = LEVEL_OPTIONS.find(level => level.value === world.target_level);
  const genreInfo = GENRE_OPTIONS.find(genre => genre.value === world.genre);

  // Format creation date
  const createdDate = new Date(world.created_at).toLocaleDateString();

  // Truncate description
  const truncatedDescription = world.description.length > 120 
    ? world.description.substring(0, 120) + '...'
    : world.description;

  return (
    <div 
      onClick={onClick}
      className="group relative overflow-hidden rounded-2xl bg-white border border-gray-200 shadow-lg hover:shadow-2xl transition-all duration-300 hover:scale-[1.02] hover:-translate-y-1 cursor-pointer hover:border-[#4ECFBF]/50 flex flex-col h-full"
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-start justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-800 group-hover:text-[#4ECFBF] transition-colors line-clamp-2">
            {world.title}
          </h3>
          {world.featured && (
            <div className="flex-shrink-0 ml-2">
              <Star className="h-5 w-5 text-[#FFD63A] fill-current" />
            </div>
          )}
        </div>
        
        {/* Language and Level Badges */}
        <div className="flex items-center gap-2 mb-3">
          <div className="flex items-center gap-1 px-2 py-1 bg-[#4ECFBF]/10 rounded-full text-xs font-medium text-[#4ECFBF]">
            <span>{languageInfo?.flag}</span>
            <span>{languageInfo?.label}</span>
          </div>
          <div 
            className="px-2 py-1 rounded-full text-xs font-medium text-white"
            style={{ backgroundColor: levelInfo?.color || '#4ECFBF' }}
          >
            {world.target_level}
          </div>
        </div>

        {/* Description */}
        <p className="text-gray-600 text-sm leading-relaxed">
          {truncatedDescription}
        </p>
      </div>

      {/* Content - Flexible area that grows */}
      <div className="p-4 flex-grow flex flex-col">
        {/* Genre, Focus, and Status */}
        <div className="flex items-center gap-3 mb-3 text-sm flex-wrap">
          <div className="flex items-center gap-1 text-gray-600">
            <span>{genreInfo?.icon}</span>
            <span>{genreInfo?.label}</span>
          </div>
          <div className="flex items-center gap-1 text-gray-600">
            <BookOpen className="h-4 w-4" />
            <span className="capitalize">{world.learning_objectives.primary_focus}</span>
          </div>
          {/* Status Indicator with Text */}
          <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${
            world.status === 'active' ? 'bg-green-100 text-green-700' :
            world.status === 'paused' ? 'bg-yellow-100 text-yellow-700' :
            world.status === 'completed' ? 'bg-blue-100 text-blue-700' :
            'bg-gray-100 text-gray-700'
          }`}>
            <div className={`w-2 h-2 rounded-full ${
              world.status === 'active' ? 'bg-green-500' :
              world.status === 'paused' ? 'bg-yellow-500' :
              world.status === 'completed' ? 'bg-blue-500' :
              'bg-gray-500'
            }`} />
            <span className="capitalize">
              {world.status === 'active' ? 'Active' :
               world.status === 'paused' ? 'Paused' :
               world.status === 'completed' ? 'Completed' :
               'Inactive'}
            </span>
          </div>
        </div>

        {/* Current Plot Point - Flexible content area */}
        <div className="flex-grow">
          {world.world_state.current_plot_point && (
            <div className="mb-3">
              <p className="text-xs text-gray-500 mb-1">Current Scene:</p>
              <p className="text-sm text-gray-700 italic line-clamp-2">
                "{world.world_state.current_plot_point}"
              </p>
            </div>
          )}
        </div>

        {/* Statistics - Fixed position from bottom */}
        <div className="flex items-center justify-between text-sm text-gray-600 mb-3">
          <div className="flex items-center gap-1">
            <Users className="h-4 w-4" />
            <span>{world.statistics.total_contributors} contributors</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="h-4 w-4" />
            <span>{world.collaboration_settings.session_duration_minutes}min sessions</span>
          </div>
        </div>

        {/* Creator and Date - Fixed position from bottom */}
        <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
          <span>by {world.creator_name || 'Anonymous'}</span>
          <span>{createdDate}</span>
        </div>

        {/* Action Button - Always at bottom */}
        <button className="w-full bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white py-2 px-4 rounded-lg font-medium hover:from-[#3a9e92] hover:to-[#2d7a6e] transition-all duration-300 group-hover:shadow-md">
          Preview World
        </button>
      </div>

      {/* Tags - Fixed at bottom */}
      {world.tags.length > 0 && (
        <div className="px-4 pb-4">
          <div className="flex flex-wrap gap-1">
            {world.tags.slice(0, 3).map((tag, index) => (
              <span 
                key={index}
                className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full"
              >
                #{tag}
              </span>
            ))}
            {world.tags.length > 3 && (
              <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                +{world.tags.length - 3}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
