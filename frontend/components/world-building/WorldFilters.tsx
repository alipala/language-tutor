'use client';

import { useState } from 'react';
import { WorldFilters as WorldFiltersType, LANGUAGE_OPTIONS, LEVEL_OPTIONS, GENRE_OPTIONS, SORT_OPTIONS } from '@/lib/world-building-api';
import { X, ChevronDown, ChevronUp, Filter, Sparkles, Globe, Target, Palette, Clock, ArrowUpDown } from 'lucide-react';

interface WorldFiltersProps {
  filters: WorldFiltersType;
  onFiltersChange: (filters: WorldFiltersType) => void;
  onClose: () => void;
}

export default function WorldFilters({ filters, onFiltersChange }: WorldFiltersProps) {
  const [expandedSections, setExpandedSections] = useState({
    language: false,
    level: false,
    genre: false,
    duration: false,
    sort: false
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const handleLanguageChange = (language: string, checked: boolean) => {
    const newLanguages = checked
      ? [...(filters.language || []), language]
      : (filters.language || []).filter(l => l !== language);
    
    onFiltersChange({
      ...filters,
      language: newLanguages
    });
  };

  const handleLevelChange = (level: string, checked: boolean) => {
    const newLevels = checked
      ? [...(filters.target_level || []), level]
      : (filters.target_level || []).filter(l => l !== level);
    
    onFiltersChange({
      ...filters,
      target_level: newLevels
    });
  };

  const handleGenreChange = (genre: string, checked: boolean) => {
    const newGenres = checked
      ? [...(filters.genre || []), genre]
      : (filters.genre || []).filter(g => g !== genre);
    
    onFiltersChange({
      ...filters,
      genre: newGenres
    });
  };

  const handleDurationChange = (min?: number, max?: number) => {
    onFiltersChange({
      ...filters,
      session_duration_min: min,
      session_duration_max: max
    });
  };

  const handleSortChange = (sortBy: string, sortOrder: 'asc' | 'desc') => {
    onFiltersChange({
      ...filters,
      sort_by: sortBy as any,
      sort_order: sortOrder
    });
  };

  const clearAllFilters = () => {
    onFiltersChange({
      language: [],
      target_level: [],
      genre: [],
      status: ['active'],
      sort_by: 'created_at',
      sort_order: 'desc'
    });
  };

  const hasActiveFilters = (filters.language?.length || 0) + (filters.target_level?.length || 0) + (filters.genre?.length || 0) > 0;

  return (
    <div className="w-80 bg-white border-r border-gray-200 h-full overflow-y-auto" style={{ maxHeight: 'calc(100vh - 80px)' }}>
      {/* Compact Header */}
      <div className="sticky top-0 bg-white border-b border-gray-100 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-[#4ECFBF]" />
          <h3 className="font-semibold text-gray-900 text-sm">
            Filters {hasActiveFilters && <Sparkles className="inline h-3 w-3 text-[#FFD63A] ml-1" />}
          </h3>
        </div>
        {hasActiveFilters && (
          <button
            onClick={clearAllFilters}
            className="px-2 py-1 bg-[#F75A5A] text-white text-xs font-medium rounded-md hover:bg-[#e54545] transition-colors"
          >
            Clear All
          </button>
        )}
      </div>

      {/* Compact Filter Sections */}
      <div className="p-4 space-y-3">
        {/* Language Filter */}
        <div className="border border-gray-200 rounded-lg">
          <button
            onClick={() => toggleSection('language')}
            className="w-full px-3 py-2 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Globe className="h-3 w-3 text-[#4ECFBF]" />
              <span className="text-sm font-medium text-gray-900">Languages</span>
              {filters.language && filters.language.length > 0 && (
                <span className="text-xs bg-[#4ECFBF] text-white px-1.5 py-0.5 rounded-full">
                  {filters.language.length}
                </span>
              )}
            </div>
            {expandedSections.language ? (
              <ChevronUp className="h-3 w-3 text-gray-500" />
            ) : (
              <ChevronDown className="h-3 w-3 text-gray-500" />
            )}
          </button>
          
          {expandedSections.language && (
            <div className="px-3 pb-3 space-y-1">
              {LANGUAGE_OPTIONS.map((option) => (
                <label 
                  key={option.value} 
                  className="flex items-center gap-2 py-1 px-2 rounded hover:bg-gray-50 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={filters.language?.includes(option.value) || false}
                    onChange={(e) => handleLanguageChange(option.value, e.target.checked)}
                    className="w-3 h-3 rounded text-[#4ECFBF] focus:ring-[#4ECFBF] focus:ring-offset-0"
                  />
                  <span className="text-sm">{option.flag}</span>
                  <span className="text-xs text-gray-700">{option.label}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Level Filter */}
        <div className="border border-gray-200 rounded-lg">
          <button
            onClick={() => toggleSection('level')}
            className="w-full px-3 py-2 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Target className="h-3 w-3 text-[#FFD63A]" />
              <span className="text-sm font-medium text-gray-900">Level</span>
              {filters.target_level && filters.target_level.length > 0 && (
                <span className="text-xs bg-[#FFD63A] text-white px-1.5 py-0.5 rounded-full">
                  {filters.target_level.length}
                </span>
              )}
            </div>
            {expandedSections.level ? (
              <ChevronUp className="h-3 w-3 text-gray-500" />
            ) : (
              <ChevronDown className="h-3 w-3 text-gray-500" />
            )}
          </button>
          
          {expandedSections.level && (
            <div className="px-3 pb-3 space-y-1">
              {LEVEL_OPTIONS.map((option) => (
                <label 
                  key={option.value} 
                  className="flex items-center gap-2 py-1 px-2 rounded hover:bg-gray-50 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={filters.target_level?.includes(option.value) || false}
                    onChange={(e) => handleLevelChange(option.value, e.target.checked)}
                    className="w-3 h-3 rounded text-[#FFD63A] focus:ring-[#FFD63A] focus:ring-offset-0"
                  />
                  <div 
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: option.color }}
                  />
                  <span className="text-xs text-gray-700">{option.label}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Genre Filter */}
        <div className="border border-gray-200 rounded-lg">
          <button
            onClick={() => toggleSection('genre')}
            className="w-full px-3 py-2 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Palette className="h-3 w-3 text-[#F75A5A]" />
              <span className="text-sm font-medium text-gray-900">Genre</span>
              {filters.genre && filters.genre.length > 0 && (
                <span className="text-xs bg-[#F75A5A] text-white px-1.5 py-0.5 rounded-full">
                  {filters.genre.length}
                </span>
              )}
            </div>
            {expandedSections.genre ? (
              <ChevronUp className="h-3 w-3 text-gray-500" />
            ) : (
              <ChevronDown className="h-3 w-3 text-gray-500" />
            )}
          </button>
          
          {expandedSections.genre && (
            <div className="px-3 pb-3 space-y-1">
              {GENRE_OPTIONS.map((option) => (
                <label 
                  key={option.value} 
                  className="flex items-center gap-2 py-1 px-2 rounded hover:bg-gray-50 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={filters.genre?.includes(option.value) || false}
                    onChange={(e) => handleGenreChange(option.value, e.target.checked)}
                    className="w-3 h-3 rounded text-[#F75A5A] focus:ring-[#F75A5A] focus:ring-offset-0"
                  />
                  <span className="text-sm">{option.icon}</span>
                  <span className="text-xs text-gray-700">{option.label}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Sort Options */}
        <div className="border border-gray-200 rounded-lg">
          <button
            onClick={() => toggleSection('sort')}
            className="w-full px-3 py-2 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <ArrowUpDown className="h-3 w-3 text-purple-500" />
              <span className="text-sm font-medium text-gray-900">Sort</span>
            </div>
            {expandedSections.sort ? (
              <ChevronUp className="h-3 w-3 text-gray-500" />
            ) : (
              <ChevronDown className="h-3 w-3 text-gray-500" />
            )}
          </button>
          
          {expandedSections.sort && (
            <div className="px-3 pb-3 space-y-1">
              {SORT_OPTIONS.map((option) => (
                <label 
                  key={option.value} 
                  className="flex items-center gap-2 py-1 px-2 rounded hover:bg-gray-50 cursor-pointer"
                >
                  <input
                    type="radio"
                    name="sort"
                    checked={filters.sort_by === option.value}
                    onChange={() => handleSortChange(option.value, 'desc')}
                    className="w-3 h-3 text-purple-500 focus:ring-purple-500 focus:ring-offset-0"
                  />
                  <span className="text-xs text-gray-700">{option.label}</span>
                </label>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Active Filters Summary */}
      {hasActiveFilters && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <p className="text-sm text-gray-600 mb-2">Active filters:</p>
          <div className="flex flex-wrap gap-2">
            {filters.language?.map((lang) => {
              const option = LANGUAGE_OPTIONS.find(o => o.value === lang);
              return (
                <span key={lang} className="inline-flex items-center gap-1 px-2 py-1 bg-[#4ECFBF]/10 text-[#4ECFBF] text-xs rounded-full">
                  <span>{option?.flag}</span>
                  <span>{option?.label}</span>
                  <button
                    onClick={() => handleLanguageChange(lang, false)}
                    className="ml-1 hover:bg-[#4ECFBF]/20 rounded-full p-0.5"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              );
            })}
            
            {filters.target_level?.map((level) => (
              <span key={level} className="inline-flex items-center gap-1 px-2 py-1 bg-[#FFD63A]/10 text-[#FFD63A] text-xs rounded-full">
                <span>{level}</span>
                <button
                  onClick={() => handleLevelChange(level, false)}
                  className="ml-1 hover:bg-[#FFD63A]/20 rounded-full p-0.5"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
            
            {filters.genre?.map((genre) => {
              const option = GENRE_OPTIONS.find(o => o.value === genre);
              return (
                <span key={genre} className="inline-flex items-center gap-1 px-2 py-1 bg-[#F75A5A]/10 text-[#F75A5A] text-xs rounded-full">
                  <span>{option?.icon}</span>
                  <span>{option?.label}</span>
                  <button
                    onClick={() => handleGenreChange(genre, false)}
                    className="ml-1 hover:bg-[#F75A5A]/20 rounded-full p-0.5"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
