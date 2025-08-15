'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { StoryWorld, LANGUAGE_OPTIONS, LEVEL_OPTIONS, GENRE_OPTIONS, worldBuildingAPI } from '@/lib/world-building-api';
import { 
  X, Users, Clock, Star, Globe, BookOpen, MapPin, User, Package, Target, 
  Calendar, TrendingUp, Mic, Play, Volume2, Edit, Save, XCircle, Plus, Trash2, Loader
} from 'lucide-react';
import StoryConversationInterface from './StoryConversationInterface';

interface WorldDetailsModalProps {
  world: StoryWorld;
  isOpen: boolean;
  onClose: () => void;
  onUpdate?: (updatedWorld: StoryWorld) => void;
}

export default function WorldDetailsModal({ world, isOpen, onClose, onUpdate }: WorldDetailsModalProps) {
  const router = useRouter();
  const { user } = useAuth();
  const [showStorySession, setShowStorySession] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form state for editing
  const [formData, setFormData] = useState({
    title: world.title,
    description: world.description,
    language: world.language,
    target_level: world.target_level,
    genre: world.genre,
    privacy_setting: world.privacy_setting,
    current_plot_point: world.world_state.current_plot_point,
    characters: [...world.world_state.active_characters],
    locations: [...world.world_state.locations],
    important_items: [...world.world_state.important_items],
    primary_focus: world.learning_objectives.primary_focus,
    target_structures: [...world.learning_objectives.target_structures],
    vocabulary_themes: [...world.learning_objectives.vocabulary_themes],
    max_contributors: world.collaboration_settings.max_contributors,
    session_duration_minutes: world.collaboration_settings.session_duration_minutes,
    requires_approval: world.collaboration_settings.requires_approval,
    tags: [...world.tags]
  });

  // Check if user can edit this world
  const canEdit = user && world && user._id === world.creator_id;

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

  // Handle form input changes
  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  // Handle array item changes (for characters, locations, items)
  const handleArrayItemChange = (arrayField: string, index: number, field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [arrayField]: (prev[arrayField as keyof typeof prev] as any[]).map((item, i) => 
        i === index ? { ...item, [field]: value } : item
      )
    }));
  };

  // Handle string array changes (for target_structures, vocabulary_themes, tags)
  const handleStringArrayChange = (arrayField: string, index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      [arrayField]: (prev[arrayField as keyof typeof prev] as string[]).map((item, i) => 
        i === index ? value : item
      )
    }));
  };

  // Add array item
  const addArrayItem = (arrayField: string, defaultItem: any) => {
    setFormData(prev => ({
      ...prev,
      [arrayField]: [...(prev[arrayField as keyof typeof prev] as any[]), defaultItem]
    }));
  };

  // Remove array item
  const removeArrayItem = (arrayField: string, index: number) => {
    setFormData(prev => ({
      ...prev,
      [arrayField]: (prev[arrayField as keyof typeof prev] as any[]).filter((_, i) => i !== index)
    }));
  };

  // Handle edit mode toggle
  const handleEditToggle = () => {
    if (isEditing) {
      // Reset form data to original values
      setFormData({
        title: world.title,
        description: world.description,
        language: world.language,
        target_level: world.target_level,
        genre: world.genre,
        privacy_setting: world.privacy_setting,
        current_plot_point: world.world_state.current_plot_point,
        characters: [...world.world_state.active_characters],
        locations: [...world.world_state.locations],
        important_items: [...world.world_state.important_items],
        primary_focus: world.learning_objectives.primary_focus,
        target_structures: [...world.learning_objectives.target_structures],
        vocabulary_themes: [...world.learning_objectives.vocabulary_themes],
        max_contributors: world.collaboration_settings.max_contributors,
        session_duration_minutes: world.collaboration_settings.session_duration_minutes,
        requires_approval: world.collaboration_settings.requires_approval,
        tags: [...world.tags]
      });
      setError(null);
      setSuccessMessage(null);
    }
    setIsEditing(!isEditing);
  };

  // Handle save
  const handleSave = async () => {
    if (!canEdit) return;

    setLoading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      // Create update payload
      const updateData = {
        title: formData.title,
        description: formData.description,
        language: formData.language,
        target_level: formData.target_level,
        genre: formData.genre,
        privacy_setting: formData.privacy_setting,
        current_plot_point: formData.current_plot_point,
        characters: formData.characters.filter(char => char.name.trim()),
        locations: formData.locations.filter(loc => loc.name.trim()),
        important_items: formData.important_items.filter(item => item.name.trim()),
        primary_focus: formData.primary_focus,
        target_structures: formData.target_structures.filter(struct => struct.trim()),
        vocabulary_themes: formData.vocabulary_themes.filter(theme => theme.trim()),
        max_contributors: formData.max_contributors,
        session_duration_minutes: formData.session_duration_minutes,
        requires_approval: formData.requires_approval,
        tags: formData.tags.filter(tag => tag.trim())
      };

      // Call API to update the world
      const updatedWorld = await worldBuildingAPI.updateStoryWorld(world.id, updateData);
      
      // Update parent component if callback provided
      if (onUpdate) {
        onUpdate(updatedWorld);
      }

      setSuccessMessage('Story updated successfully!');
      setIsEditing(false);
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
      
    } catch (err) {
      console.error('Error updating story:', err);
      setError(err instanceof Error ? err.message : 'Failed to update story');
    } finally {
      setLoading(false);
    }
  };

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

          {/* Success/Error Messages */}
          {(error || successMessage) && (
            <div className="px-6 pt-4">
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-center gap-2 text-red-700 text-sm">
                  <XCircle className="h-4 w-4 flex-shrink-0" />
                  {error}
                </div>
              )}
              {successMessage && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-3 flex items-center gap-2 text-green-700 text-sm">
                  <Save className="h-4 w-4 flex-shrink-0" />
                  {successMessage}
                </div>
              )}
            </div>
          )}

          {/* Content */}
          <div className="overflow-y-auto max-h-[calc(90vh-80px)]">
            <div className="p-6 space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Language */}
                <div className="flex items-center gap-2 p-3 bg-[#4ECFBF]/10 rounded-lg">
                  <span className="text-2xl">{languageInfo?.flag}</span>
                  <div className="flex-1">
                    <p className="text-sm text-gray-600">Language</p>
                    {isEditing ? (
                      <select
                        value={formData.language}
                        onChange={(e) => handleInputChange('language', e.target.value)}
                        className="font-semibold text-[#4ECFBF] bg-transparent border-none focus:outline-none"
                      >
                        {LANGUAGE_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.flag} {option.label}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <p className="font-semibold text-[#4ECFBF]">{languageInfo?.label}</p>
                    )}
                  </div>
                </div>
                
                {/* Level */}
                <div className="flex items-center gap-2 p-3 rounded-lg" style={{ backgroundColor: `${levelInfo?.color}20` }}>
                  <div 
                    className="w-6 h-6 rounded-full"
                    style={{ backgroundColor: levelInfo?.color }}
                  />
                  <div className="flex-1">
                    <p className="text-sm text-gray-600">Level</p>
                    {isEditing ? (
                      <select
                        value={formData.target_level}
                        onChange={(e) => handleInputChange('target_level', e.target.value)}
                        className="font-semibold bg-transparent border-none focus:outline-none"
                        style={{ color: levelInfo?.color }}
                      >
                        {LEVEL_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <p className="font-semibold" style={{ color: levelInfo?.color }}>
                        {levelInfo?.label}
                      </p>
                    )}
                  </div>
                </div>
                
                {/* Genre */}
                <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
                  <span className="text-2xl">{genreInfo?.icon}</span>
                  <div className="flex-1">
                    <p className="text-sm text-gray-600">Genre</p>
                    {isEditing ? (
                      <select
                        value={formData.genre}
                        onChange={(e) => handleInputChange('genre', e.target.value)}
                        className="font-semibold text-gray-800 bg-transparent border-none focus:outline-none"
                      >
                        {GENRE_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.icon} {option.label}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <p className="font-semibold text-gray-800">{genreInfo?.label}</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Privacy Setting (only show in edit mode) */}
              {isEditing && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Privacy Setting
                  </label>
                  <select
                    value={formData.privacy_setting}
                    onChange={(e) => handleInputChange('privacy_setting', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent text-gray-800"
                  >
                    <option value="public">🌍 Public - Anyone can discover and join</option>
                    <option value="private">🔒 Private - Invite only</option>
                  </select>
                </div>
              )}

              {/* Description */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">Story Description</h3>
                {isEditing ? (
                  <textarea
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent text-gray-800"
                    placeholder="Describe your story world and what makes it interesting"
                  />
                ) : (
                  <p className="text-gray-700 leading-relaxed">{world.description}</p>
                )}
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
                    {isEditing ? (
                      <select
                        value={formData.primary_focus}
                        onChange={(e) => handleInputChange('primary_focus', e.target.value)}
                        className="px-3 py-1 bg-[#4ECFBF] text-white rounded-full text-sm font-medium"
                      >
                        <option value="grammar">Grammar</option>
                        <option value="vocabulary">Vocabulary</option>
                        <option value="pronunciation">Pronunciation</option>
                        <option value="cultural">Cultural</option>
                      </select>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-3 py-1 bg-[#4ECFBF] text-white rounded-full text-sm font-medium">
                        <BookOpen className="h-4 w-4" />
                        {world.learning_objectives.primary_focus.charAt(0).toUpperCase() + world.learning_objectives.primary_focus.slice(1)}
                      </span>
                    )}
                  </div>
                  
                  {/* Target Grammar Structures */}
                  <div>
                    <p className="text-sm font-medium text-gray-800 mb-2">Target Grammar Structures</p>
                    {isEditing ? (
                      <div className="space-y-2">
                        {formData.target_structures.map((structure, index) => (
                          <div key={index} className="flex gap-2">
                            <input
                              type="text"
                              value={structure}
                              onChange={(e) => handleStringArrayChange('target_structures', index, e.target.value)}
                              className="flex-1 px-2 py-1 border border-gray-200 rounded-md text-sm text-gray-800"
                              placeholder="Grammar structure"
                            />
                            {formData.target_structures.length > 1 && (
                              <button
                                type="button"
                                onClick={() => removeArrayItem('target_structures', index)}
                                className="text-red-500 hover:text-red-700 p-1"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            )}
                          </div>
                        ))}
                        <button
                          type="button"
                          onClick={() => addArrayItem('target_structures', '')}
                          className="text-[#4ECFBF] hover:text-[#3a9e92] font-medium text-sm flex items-center gap-1"
                        >
                          <Plus className="h-4 w-4" />
                          Add Structure
                        </button>
                      </div>
                    ) : (
                      <div className="flex flex-wrap gap-2">
                        {world.learning_objectives.target_structures.map((structure, index) => (
                          <span key={index} className="px-2 py-1 bg-white border border-gray-200 rounded-md text-sm text-gray-700">
                            {structure}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  {/* Vocabulary Themes */}
                  <div>
                    <p className="text-sm font-medium text-gray-800 mb-2">Vocabulary Themes</p>
                    {isEditing ? (
                      <div className="space-y-2">
                        {formData.vocabulary_themes.map((theme, index) => (
                          <div key={index} className="flex gap-2">
                            <input
                              type="text"
                              value={theme}
                              onChange={(e) => handleStringArrayChange('vocabulary_themes', index, e.target.value)}
                              className="flex-1 px-2 py-1 border border-gray-200 rounded-md text-sm text-gray-800"
                              placeholder="Vocabulary theme"
                            />
                            {formData.vocabulary_themes.length > 1 && (
                              <button
                                type="button"
                                onClick={() => removeArrayItem('vocabulary_themes', index)}
                                className="text-red-500 hover:text-red-700 p-1"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            )}
                          </div>
                        ))}
                        <button
                          type="button"
                          onClick={() => addArrayItem('vocabulary_themes', '')}
                          className="text-[#4ECFBF] hover:text-[#3a9e92] font-medium text-sm flex items-center gap-1"
                        >
                          <Plus className="h-4 w-4" />
                          Add Theme
                        </button>
                      </div>
                    ) : (
                      <div className="flex flex-wrap gap-2">
                        {world.learning_objectives.vocabulary_themes.map((theme, index) => (
                          <span key={index} className="px-2 py-1 bg-white border border-gray-200 rounded-md text-sm text-gray-700">
                            {theme}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
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
                    {isEditing ? (
                      <textarea
                        value={formData.current_plot_point}
                        onChange={(e) => handleInputChange('current_plot_point', e.target.value)}
                        rows={3}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent text-sm text-gray-800"
                        placeholder="Describe the current situation in your story..."
                      />
                    ) : (
                      <p className="text-gray-800 italic">"{world.world_state.current_plot_point}"</p>
                    )}
                  </div>

                  {/* Characters, Locations, Items */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Characters */}
                    <div>
                      <p className="text-sm font-medium text-gray-800 mb-2 flex items-center gap-1">
                        <User className="h-4 w-4" />
                        Active Characters ({isEditing ? formData.characters.length : world.world_state.active_characters.length})
                      </p>
                      {isEditing ? (
                        <div className="space-y-2">
                          {formData.characters.map((character, index) => (
                            <div key={index} className="bg-white rounded-md p-2 border border-gray-200 space-y-1">
                              <input
                                type="text"
                                value={character.name}
                                onChange={(e) => handleArrayItemChange('characters', index, 'name', e.target.value)}
                                placeholder="Character name"
                                className="w-full text-sm font-medium text-gray-700 bg-transparent border-none focus:outline-none"
                              />
                              <input
                                type="text"
                                value={character.role}
                                onChange={(e) => handleArrayItemChange('characters', index, 'role', e.target.value)}
                                placeholder="Role"
                                className="w-full text-xs text-gray-600 bg-transparent border-none focus:outline-none"
                              />
                              {formData.characters.length > 1 && (
                                <button
                                  type="button"
                                  onClick={() => removeArrayItem('characters', index)}
                                  className="text-red-500 hover:text-red-700 text-xs"
                                >
                                  Remove
                                </button>
                              )}
                            </div>
                          ))}
                          <button
                            type="button"
                            onClick={() => addArrayItem('characters', { name: '', role: '', description: '' })}
                            className="text-[#4ECFBF] hover:text-[#3a9e92] font-medium text-xs flex items-center gap-1"
                          >
                            <Plus className="h-3 w-3" />
                            Add Character
                          </button>
                        </div>
                      ) : (
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
                      )}
                    </div>

                    {/* Locations */}
                    <div>
                      <p className="text-sm font-medium text-gray-800 mb-2 flex items-center gap-1">
                        <MapPin className="h-4 w-4" />
                        Locations ({isEditing ? formData.locations.length : world.world_state.locations.length})
                      </p>
                      {isEditing ? (
                        <div className="space-y-2">
                          {formData.locations.map((location, index) => (
                            <div key={index} className="bg-white rounded-md p-2 border border-gray-200 space-y-1">
                              <input
                                type="text"
                                value={location.name}
                                onChange={(e) => handleArrayItemChange('locations', index, 'name', e.target.value)}
                                placeholder="Location name"
                                className="w-full text-sm font-medium text-gray-700 bg-transparent border-none focus:outline-none"
                              />
                              {formData.locations.length > 1 && (
                                <button
                                  type="button"
                                  onClick={() => removeArrayItem('locations', index)}
                                  className="text-red-500 hover:text-red-700 text-xs"
                                >
                                  Remove
                                </button>
                              )}
                            </div>
                          ))}
                          <button
                            type="button"
                            onClick={() => addArrayItem('locations', { name: '', description: '' })}
                            className="text-[#4ECFBF] hover:text-[#3a9e92] font-medium text-xs flex items-center gap-1"
                          >
                            <Plus className="h-3 w-3" />
                            Add Location
                          </button>
                        </div>
                      ) : (
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
                      )}
                    </div>

                    {/* Important Items */}
                    <div>
                      <p className="text-sm font-medium text-gray-800 mb-2 flex items-center gap-1">
                        <Package className="h-4 w-4" />
                        Key Items ({isEditing ? formData.important_items.length : world.world_state.important_items.length})
                      </p>
                      {isEditing ? (
                        <div className="space-y-2">
                          {formData.important_items.map((item, index) => (
                            <div key={index} className="bg-white rounded-md p-2 border border-gray-200 space-y-1">
                              <input
                                type="text"
                                value={item.name}
                                onChange={(e) => handleArrayItemChange('important_items', index, 'name', e.target.value)}
                                placeholder="Item name"
                                className="w-full text-sm font-medium text-gray-700 bg-transparent border-none focus:outline-none"
                              />
                              {formData.important_items.length > 1 && (
                                <button
                                  type="button"
                                  onClick={() => removeArrayItem('important_items', index)}
                                  className="text-red-500 hover:text-red-700 text-xs"
                                >
                                  Remove
                                </button>
                              )}
                            </div>
                          ))}
                          <button
                            type="button"
                            onClick={() => addArrayItem('important_items', { name: '', significance: '' })}
                            className="text-[#4ECFBF] hover:text-[#3a9e92] font-medium text-xs flex items-center gap-1"
                          >
                            <Plus className="h-3 w-3" />
                            Add Item
                          </button>
                        </div>
                      ) : (
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
                      )}
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
                    {isEditing ? (
                      <select
                        value={formData.max_contributors}
                        onChange={(e) => handleInputChange('max_contributors', parseInt(e.target.value))}
                        className="font-semibold text-gray-800 bg-transparent border-none focus:outline-none text-center"
                      >
                        {[3, 5, 8, 10, 15, 20].map(num => (
                          <option key={num} value={num}>{num}</option>
                        ))}
                      </select>
                    ) : (
                      <p className="font-semibold text-gray-800">{world.collaboration_settings.max_contributors}</p>
                    )}
                  </div>
                  
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <Clock className="h-6 w-6 text-[#FFD63A] mx-auto mb-1" />
                    <p className="text-sm text-gray-600">Session Length</p>
                    {isEditing ? (
                      <select
                        value={formData.session_duration_minutes}
                        onChange={(e) => handleInputChange('session_duration_minutes', parseInt(e.target.value))}
                        className="font-semibold text-gray-800 bg-transparent border-none focus:outline-none text-center"
                      >
                        {[5, 10, 15, 20, 30, 45, 60].map(num => (
                          <option key={num} value={num}>{num} min</option>
                        ))}
                      </select>
                    ) : (
                      <p className="font-semibold text-gray-800">{world.collaboration_settings.session_duration_minutes} min</p>
                    )}
                  </div>
                  
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <div className={`h-6 w-6 mx-auto mb-1 rounded-full ${world.collaboration_settings.requires_approval ? 'bg-yellow-400' : 'bg-green-400'}`} />
                    <p className="text-sm text-gray-600">Approval</p>
                    {isEditing ? (
                      <label className="flex items-center justify-center gap-2">
                        <input
                          type="checkbox"
                          checked={formData.requires_approval}
                          onChange={(e) => handleInputChange('requires_approval', e.target.checked)}
                          className="rounded border-gray-300 text-[#4ECFBF] focus:ring-[#4ECFBF]"
                        />
                        <span className="text-xs">Required</span>
                      </label>
                    ) : (
                      <p className="font-semibold text-gray-800">{world.collaboration_settings.requires_approval ? 'Required' : 'Open'}</p>
                    )}
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
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">Tags</h3>
                {isEditing ? (
                  <div className="space-y-2">
                    {formData.tags.map((tag, index) => (
                      <div key={index} className="flex gap-2">
                        <input
                          type="text"
                          value={tag}
                          onChange={(e) => handleStringArrayChange('tags', index, e.target.value)}
                          className="flex-1 px-2 py-1 border border-gray-200 rounded-md text-sm text-gray-800"
                          placeholder="Tag"
                        />
                        {formData.tags.length > 1 && (
                          <button
                            type="button"
                            onClick={() => removeArrayItem('tags', index)}
                            className="text-red-500 hover:text-red-700 p-1"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    ))}
                    <button
                      type="button"
                      onClick={() => addArrayItem('tags', '')}
                      className="text-[#4ECFBF] hover:text-[#3a9e92] font-medium text-sm flex items-center gap-1"
                    >
                      <Plus className="h-4 w-4" />
                      Add Tag
                    </button>
                  </div>
                ) : (
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
                )}
              </div>

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
                {/* Edit/Save/Cancel buttons (only show for creators) */}
                {canEdit && (
                  <>
                    {isEditing ? (
                      <>
                        <button
                          onClick={handleEditToggle}
                          disabled={loading}
                          className="px-4 py-2 bg-gray-500 text-white border border-gray-500 rounded-lg hover:bg-gray-600 transition-colors disabled:opacity-50"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handleSave}
                          disabled={loading}
                          className="flex items-center gap-2 px-4 py-2 bg-[#4ECFBF] text-white border border-[#4ECFBF] rounded-lg hover:bg-[#3a9e92] transition-colors disabled:opacity-50"
                        >
                          {loading ? (
                            <>
                              <Loader className="h-4 w-4 animate-spin" />
                              Saving...
                            </>
                          ) : (
                            <>
                              <Save className="h-4 w-4" />
                              Save Changes
                            </>
                          )}
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={handleEditToggle}
                        className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-200 transition-colors"
                      >
                        <Edit className="h-4 w-4" />
                        Edit
                      </button>
                    )}
                  </>
                )}
                
                <button
                  onClick={onClose}
                  className="px-4 py-2 bg-[#F75A5A] text-white border border-[#F75A5A] rounded-lg hover:bg-[#e54545] transition-colors"
                >
                  Close
                </button>
                
                {/* Story Conversation Button (only show when not editing) */}
                {!isEditing && (
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
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
