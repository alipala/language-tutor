'use client';

import { useState } from 'react';
import { worldBuildingAPI, LANGUAGE_OPTIONS, LEVEL_OPTIONS, GENRE_OPTIONS } from '@/lib/world-building-api';
import { X, BookOpen, Users, Target, Palette, Globe, Clock, Plus, Minus, Loader2, CheckCircle } from 'lucide-react';

interface StoryCreationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (worldId: string) => void;
}

interface Character {
  name: string;
  role: string;
  description: string;
}

interface Location {
  name: string;
  description: string;
}

interface ImportantItem {
  name: string;
  significance: string;
}

export default function StoryCreationModal({ isOpen, onClose, onSuccess }: StoryCreationModalProps) {
  const [step, setStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form data
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    language: 'en',
    target_level: 'B1',
    genre: 'adventure',
    privacy_setting: 'public' as 'public' | 'private',
    current_plot_point: '',
    characters: [{ name: '', role: '', description: '' }] as Character[],
    locations: [{ name: '', description: '' }] as Location[],
    important_items: [{ name: '', significance: '' }] as ImportantItem[],
    primary_focus: 'vocabulary' as 'vocabulary' | 'grammar' | 'pronunciation' | 'cultural',
    target_structures: [''],
    vocabulary_themes: [''],
    max_contributors: 6,
    session_duration_minutes: 15,
    requires_approval: false,
    tags: ['']
  });

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleArrayChange = (field: keyof typeof formData, index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: (prev[field] as string[]).map((item: string, i: number) => 
        i === index ? value : item
      )
    }));
  };

  const handleObjectArrayChange = (field: keyof typeof formData, index: number, subField: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: (prev[field] as any[]).map((item: any, i: number) => 
        i === index ? { ...item, [subField]: value } : item
      )
    }));
  };

  const addArrayItem = (field: keyof typeof formData, defaultValue: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: [...(prev[field] as any[]), defaultValue]
    }));
  };

  const removeArrayItem = (field: keyof typeof formData, index: number) => {
    setFormData(prev => ({
      ...prev,
      [field]: (prev[field] as any[]).filter((_: any, i: number) => i !== index)
    }));
  };

  const validateStep = (stepNumber: number): boolean => {
    switch (stepNumber) {
      case 1:
        return formData.title.trim() !== '' && formData.description.trim() !== '';
      case 2:
        return formData.current_plot_point.trim() !== '';
      case 3:
        return formData.characters.some(char => char.name.trim() !== '') &&
               formData.locations.some(loc => loc.name.trim() !== '');
      case 4:
        return formData.vocabulary_themes.some(theme => theme.trim() !== '');
      default:
        return true;
    }
  };

  const handleNext = () => {
    if (validateStep(step)) {
      setStep(prev => Math.min(prev + 1, 5));
      setError(null);
    } else {
      setError('Please fill in all required fields before continuing.');
    }
  };

  const handlePrevious = () => {
    setStep(prev => Math.max(prev - 1, 1));
    setError(null);
  };

  const handleSubmit = async () => {
    if (!validateStep(4)) {
      setError('Please complete all required fields.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      // Clean up form data
      const cleanedData = {
        ...formData,
        characters: formData.characters.filter(char => char.name.trim() !== ''),
        locations: formData.locations.filter(loc => loc.name.trim() !== ''),
        important_items: formData.important_items.filter(item => item.name.trim() !== ''),
        target_structures: formData.target_structures.filter(struct => struct.trim() !== ''),
        vocabulary_themes: formData.vocabulary_themes.filter(theme => theme.trim() !== ''),
        tags: formData.tags.filter(tag => tag.trim() !== '')
      };

      const result = await worldBuildingAPI.createStoryWorld(cleanedData);
      
      if (result.success) {
        setStep(5); // Success step
        setTimeout(() => {
          onSuccess(result.world_id);
          onClose();
        }, 2000);
      } else {
        setError(result.message || 'Failed to create story world');
      }
    } catch (err) {
      console.error('Error creating story:', err);
      setError('An unexpected error occurred. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  const stepTitles = [
    'Basic Information',
    'Story Setup',
    'World Building',
    'Learning Objectives',
    'Success!'
  ];

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <BookOpen className="h-6 w-6 text-white" />
              <div>
                <h2 className="text-xl font-bold text-white">Create New Story World</h2>
                <p className="text-white/80 text-sm">
                  Step {step} of {stepTitles.length}: {stepTitles[step - 1]}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-full transition-colors text-white"
              disabled={isSubmitting}
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          
          {/* Progress Bar */}
          <div className="mt-4 bg-white/20 rounded-full h-2">
            <div 
              className="bg-white rounded-full h-2 transition-all duration-300"
              style={{ width: `${(step / stepTitles.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Story Title *
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                  placeholder="Enter an engaging title for your story"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent text-gray-900 bg-white"
                  maxLength={100}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description *
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder="Describe your story world and what learners can expect"
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent text-gray-900 bg-white"
                  maxLength={500}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Globe className="inline h-4 w-4 mr-1" />
                    Language
                  </label>
                  <select
                    value={formData.language}
                    onChange={(e) => handleInputChange('language', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent text-gray-900 bg-white"
                  >
                    {LANGUAGE_OPTIONS.map(option => (
                      <option key={option.value} value={option.value} className="text-gray-900 bg-white">
                        {option.flag} {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Target className="inline h-4 w-4 mr-1" />
                    Level
                  </label>
                  <select
                    value={formData.target_level}
                    onChange={(e) => handleInputChange('target_level', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent text-gray-900 bg-white"
                  >
                    {LEVEL_OPTIONS.map(option => (
                      <option key={option.value} value={option.value} className="text-gray-900 bg-white">
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Palette className="inline h-4 w-4 mr-1" />
                    Genre
                  </label>
                  <select
                    value={formData.genre}
                    onChange={(e) => handleInputChange('genre', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent text-gray-900 bg-white"
                  >
                    {GENRE_OPTIONS.map(option => (
                      <option key={option.value} value={option.value} className="text-gray-900 bg-white">
                        {option.icon} {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Opening Scene *
                </label>
                <textarea
                  value={formData.current_plot_point}
                  onChange={(e) => handleInputChange('current_plot_point', e.target.value)}
                  placeholder="Describe the opening scene or situation that will start your collaborative story..."
                  rows={6}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent text-gray-900 bg-white"
                  maxLength={1000}
                />
                <p className="text-xs text-gray-500 mt-1">
                  This will be the starting point for all collaborators. Make it engaging and open-ended!
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Story Tags
                </label>
                <div className="space-y-2">
                  {formData.tags.map((tag, index) => (
                    <div key={index} className="flex gap-2">
                      <input
                        type="text"
                        value={tag}
                        onChange={(e) => handleArrayChange('tags', index, e.target.value)}
                        placeholder="Add a tag (e.g., mystery, beginner-friendly)"
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent text-gray-900 bg-white"
                      />
                      {formData.tags.length > 1 && (
                        <button
                          onClick={() => removeArrayItem('tags', index)}
                          className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg"
                        >
                          <Minus className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  ))}
                  <button
                    onClick={() => addArrayItem('tags', '')}
                    className="flex items-center gap-2 px-3 py-2 text-[#4ECFBF] hover:bg-[#4ECFBF]/10 rounded-lg"
                  >
                    <Plus className="h-4 w-4" />
                    Add Tag
                  </button>
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-6">
              {/* Characters */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Characters *
                </label>
                <div className="space-y-4">
                  {formData.characters.map((character, index) => (
                    <div key={index} className="p-4 border border-gray-200 rounded-lg">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                        <input
                          type="text"
                          value={character.name}
                          onChange={(e) => handleObjectArrayChange('characters', index, 'name', e.target.value)}
                          placeholder="Character name"
                          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent text-gray-900 bg-white"
                        />
                        <input
                          type="text"
                          value={character.role}
                          onChange={(e) => handleObjectArrayChange('characters', index, 'role', e.target.value)}
                          placeholder="Role (e.g., Detective, Guide)"
                          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent text-gray-900 bg-white"
                        />
                      </div>
                      <textarea
                        value={character.description}
                        onChange={(e) => handleObjectArrayChange('characters', index, 'description', e.target.value)}
                        placeholder="Character description and personality"
                        rows={2}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent text-gray-900 bg-white"
                      />
                      {formData.characters.length > 1 && (
                        <button
                          onClick={() => removeArrayItem('characters', index)}
                          className="mt-2 px-3 py-1 text-red-600 hover:bg-red-50 rounded text-sm"
                        >
                          Remove Character
                        </button>
                      )}
                    </div>
                  ))}
                  <button
                    onClick={() => addArrayItem('characters', { name: '', role: '', description: '' })}
                    className="flex items-center gap-2 px-3 py-2 text-[#4ECFBF] hover:bg-[#4ECFBF]/10 rounded-lg"
                  >
                    <Plus className="h-4 w-4" />
                    Add Character
                  </button>
                </div>
              </div>

              {/* Locations */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Locations *
                </label>
                <div className="space-y-4">
                  {formData.locations.map((location, index) => (
                    <div key={index} className="p-4 border border-gray-200 rounded-lg">
                      <input
                        type="text"
                        value={location.name}
                        onChange={(e) => handleObjectArrayChange('locations', index, 'name', e.target.value)}
                        placeholder="Location name"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent mb-3 text-gray-900 bg-white"
                      />
                      <textarea
                        value={location.description}
                        onChange={(e) => handleObjectArrayChange('locations', index, 'description', e.target.value)}
                        placeholder="Location description and atmosphere"
                        rows={2}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent text-gray-900 bg-white"
                      />
                      {formData.locations.length > 1 && (
                        <button
                          onClick={() => removeArrayItem('locations', index)}
                          className="mt-2 px-3 py-1 text-red-600 hover:bg-red-50 rounded text-sm"
                        >
                          Remove Location
                        </button>
                      )}
                    </div>
                  ))}
                  <button
                    onClick={() => addArrayItem('locations', { name: '', description: '' })}
                    className="flex items-center gap-2 px-3 py-2 text-[#4ECFBF] hover:bg-[#4ECFBF]/10 rounded-lg"
                  >
                    <Plus className="h-4 w-4" />
                    Add Location
                  </button>
                </div>
              </div>

              {/* Important Items */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Important Items (Optional)
                </label>
                <div className="space-y-4">
                  {formData.important_items.map((item, index) => (
                    <div key={index} className="p-4 border border-gray-200 rounded-lg">
                      <input
                        type="text"
                        value={item.name}
                        onChange={(e) => handleObjectArrayChange('important_items', index, 'name', e.target.value)}
                        placeholder="Item name"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent mb-3 text-gray-900 bg-white"
                      />
                      <textarea
                        value={item.significance}
                        onChange={(e) => handleObjectArrayChange('important_items', index, 'significance', e.target.value)}
                        placeholder="Why is this item important to the story?"
                        rows={2}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent text-gray-900 bg-white"
                      />
                      <button
                        onClick={() => removeArrayItem('important_items', index)}
                        className="mt-2 px-3 py-1 text-red-600 hover:bg-red-50 rounded text-sm"
                      >
                        Remove Item
                      </button>
                    </div>
                  ))}
                  <button
                    onClick={() => addArrayItem('important_items', { name: '', significance: '' })}
                    className="flex items-center gap-2 px-3 py-2 text-[#4ECFBF] hover:bg-[#4ECFBF]/10 rounded-lg"
                  >
                    <Plus className="h-4 w-4" />
                    Add Important Item
                  </button>
                </div>
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Primary Learning Focus
                </label>
                <select
                  value={formData.primary_focus}
                  onChange={(e) => handleInputChange('primary_focus', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent text-gray-900 bg-white"
                >
                  <option value="vocabulary" className="text-gray-900 bg-white">Vocabulary Building</option>
                  <option value="grammar" className="text-gray-900 bg-white">Grammar Practice</option>
                  <option value="pronunciation" className="text-gray-900 bg-white">Pronunciation</option>
                  <option value="cultural" className="text-gray-900 bg-white">Cultural Learning</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Vocabulary Themes *
                </label>
                <div className="space-y-2">
                  {formData.vocabulary_themes.map((theme, index) => (
                    <div key={index} className="flex gap-2">
                      <input
                        type="text"
                        value={theme}
                        onChange={(e) => handleArrayChange('vocabulary_themes', index, e.target.value)}
                        placeholder="e.g., Travel vocabulary, Business terms"
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent text-gray-900 bg-white"
                      />
                      {formData.vocabulary_themes.length > 1 && (
                        <button
                          onClick={() => removeArrayItem('vocabulary_themes', index)}
                          className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg"
                        >
                          <Minus className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  ))}
                  <button
                    onClick={() => addArrayItem('vocabulary_themes', '')}
                    className="flex items-center gap-2 px-3 py-2 text-[#4ECFBF] hover:bg-[#4ECFBF]/10 rounded-lg"
                  >
                    <Plus className="h-4 w-4" />
                    Add Theme
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Target Grammar Structures (Optional)
                </label>
                <div className="space-y-2">
                  {formData.target_structures.map((structure, index) => (
                    <div key={index} className="flex gap-2">
                      <input
                        type="text"
                        value={structure}
                        onChange={(e) => handleArrayChange('target_structures', index, e.target.value)}
                        placeholder="e.g., Past perfect tense, Modal verbs"
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent text-gray-900 bg-white"
                      />
                      <button
                        onClick={() => removeArrayItem('target_structures', index)}
                        className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg"
                      >
                        <Minus className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                  <button
                    onClick={() => addArrayItem('target_structures', '')}
                    className="flex items-center gap-2 px-3 py-2 text-[#4ECFBF] hover:bg-[#4ECFBF]/10 rounded-lg"
                  >
                    <Plus className="h-4 w-4" />
                    Add Structure
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Users className="inline h-4 w-4 mr-1" />
                    Max Contributors
                  </label>
                  <select
                    value={formData.max_contributors}
                    onChange={(e) => handleInputChange('max_contributors', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent text-gray-900 bg-white"
                  >
                    {[2, 3, 4, 5, 6, 7, 8, 9, 10].map(num => (
                      <option key={num} value={num} className="text-gray-900 bg-white">{num} contributors</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Clock className="inline h-4 w-4 mr-1" />
                    Session Duration
                  </label>
                  <select
                    value={formData.session_duration_minutes}
                    onChange={(e) => handleInputChange('session_duration_minutes', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent text-gray-900 bg-white"
                  >
                    {[5, 10, 15, 20, 25, 30].map(mins => (
                      <option key={mins} value={mins} className="text-gray-900 bg-white">{mins} minutes</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}

          {step === 5 && (
            <div className="text-center py-12">
              <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
              <h3 className="text-2xl font-bold text-gray-800 mb-2">
                Story World Created Successfully!
              </h3>
              <p className="text-gray-600 mb-4">
                Your collaborative story world is now live and ready for contributors.
              </p>
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 max-w-md mx-auto">
                <p className="text-sm text-green-800">
                  <strong>"{formData.title}"</strong> has been created and is now available for discovery.
                  You'll be redirected to your new story world shortly.
                </p>
              </div>
            </div>
          )}

          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        {step < 5 && (
          <div className="border-t bg-gray-50 p-4 flex justify-between">
            <button
              onClick={handlePrevious}
              disabled={step === 1 || isSubmitting}
              className="px-4 py-2 border border-gray-300 rounded-lg bg-white hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-gray-700"
            >
              Previous
            </button>
            
            <div className="flex gap-3">
              <button
                onClick={onClose}
                disabled={isSubmitting}
                className="px-4 py-2 border border-gray-300 rounded-lg bg-white hover:bg-gray-50 transition-colors disabled:opacity-50 text-gray-700"
              >
                Cancel
              </button>
              
              {step < 4 ? (
                <button
                  onClick={handleNext}
                  disabled={!validateStep(step) || isSubmitting}
                  className="px-4 py-2 bg-[#4ECFBF] text-white rounded-lg hover:bg-[#3a9e92] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={!validateStep(4) || isSubmitting}
                  className="px-6 py-2 bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white rounded-lg hover:from-[#3a9e92] hover:to-[#2d7a6e] transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    'Create Story World'
                  )}
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
