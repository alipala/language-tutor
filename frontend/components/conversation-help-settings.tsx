'use client';

import React, { useState, useEffect } from 'react';
import { Settings, HelpCircle, Globe, Volume2, BookOpen, MessageCircle } from 'lucide-react';

interface HelpSettings {
  help_enabled: boolean;
  help_language: string;
  show_pronunciation: boolean;
  show_grammar_tips: boolean;
  show_cultural_notes: boolean;
  show_vocabulary: boolean;
}

interface ConversationHelpSettingsProps {
  onSettingsChange: (settings: HelpSettings) => void;
  initialSettings?: HelpSettings;
  className?: string;
  compact?: boolean;
}

const SUPPORTED_HELP_LANGUAGES = [
  { code: "english", name: "English", native_name: "English" },
  { code: "spanish", name: "Spanish", native_name: "Español" },
  { code: "french", name: "French", native_name: "Français" },
  { code: "german", name: "German", native_name: "Deutsch" },
  { code: "italian", name: "Italian", native_name: "Italiano" },
  { code: "portuguese", name: "Portuguese", native_name: "Português" },
  { code: "dutch", name: "Dutch", native_name: "Nederlands" },
  { code: "russian", name: "Russian", native_name: "Русский" },
  { code: "chinese", name: "Chinese", native_name: "中文" },
  { code: "japanese", name: "Japanese", native_name: "日本語" },
  { code: "korean", name: "Korean", native_name: "한국어" },
  { code: "arabic", name: "Arabic", native_name: "العربية" },
  { code: "hindi", name: "Hindi", native_name: "हिन्दी" },
  { code: "turkish", name: "Turkish", native_name: "Türkçe" }
];

const ConversationHelpSettings: React.FC<ConversationHelpSettingsProps> = ({
  onSettingsChange,
  initialSettings,
  className = "",
  compact = false
}) => {
  const [settings, setSettings] = useState<HelpSettings>({
    help_enabled: true,
    help_language: "english",
    show_pronunciation: true,
    show_grammar_tips: true,
    show_cultural_notes: true,
    show_vocabulary: true,
    ...initialSettings
  });

  const [isExpanded, setIsExpanded] = useState(false);

  // Track if this is the initial load to prevent calling onSettingsChange on mount
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    if (initialSettings && !isInitialized) {
      setSettings(prev => ({
        ...prev,
        ...initialSettings
      }));
      setIsInitialized(true);
    }
  }, [initialSettings, isInitialized]);

  useEffect(() => {
    // Only call onSettingsChange after initialization and when settings actually change
    // Don't include onSettingsChange in dependencies to prevent infinite loops
    if (isInitialized) {
      onSettingsChange(settings);
    }
  }, [settings, isInitialized]);

  const updateSetting = (key: keyof HelpSettings, value: boolean | string) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const getLanguageDisplayName = (code: string) => {
    const lang = SUPPORTED_HELP_LANGUAGES.find(l => l.code === code);
    return lang ? `${lang.name} (${lang.native_name})` : code;
  };

  // Compact version for control panel
  if (compact) {
    return (
      <div className={`flex items-center gap-3 ${className}`}>
        {/* Help Label with Toggle */}
        <div className="flex items-center gap-2">
          <span className="font-semibold text-lg">Help</span>
          
          {/* Modern Toggle Switch - Next to Help */}
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.help_enabled}
              onChange={(e) => updateSetting('help_enabled', e.target.checked)}
              className="sr-only peer"
            />
            <div className={`relative w-11 h-6 rounded-full peer transition-colors duration-200 ease-in-out ${
              settings.help_enabled 
                ? 'bg-gradient-to-r from-indigo-500 to-purple-600' 
                : 'bg-gray-300'
            }`}>
              <div className={`absolute top-0.5 left-0.5 bg-white rounded-full h-5 w-5 transition-transform duration-200 ease-in-out shadow-md ${
                settings.help_enabled ? 'translate-x-5' : 'translate-x-0'
              }`}></div>
            </div>
          </label>
        </div>
        
        {/* Language Selection Dropdown - Only show when enabled */}
        {settings.help_enabled && (
          <div className="relative animate-fadeIn">
            <select
              value={settings.help_language}
              onChange={(e) => updateSetting('help_language', e.target.value)}
              className="text-sm font-medium rounded-md px-3 py-1 border-2 transition-all duration-200 min-w-[80px] bg-white border-indigo-200 text-gray-800 hover:border-indigo-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              style={{ 
                appearance: 'none',
                WebkitAppearance: 'none',
                MozAppearance: 'none',
                backgroundImage: 'none'
              }}
            >
              {SUPPORTED_HELP_LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code} className="bg-white text-gray-800 py-2">
                  {lang.native_name}
                </option>
              ))}
            </select>
            {/* Custom dropdown arrow - Mobile optimized */}
            <div className="absolute right-2 top-1/2 transform -translate-y-1/2 pointer-events-none transition-colors duration-200 text-gray-600">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Full version for settings panel
  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div 
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full flex items-center justify-center shadow-sm">
            <HelpCircle className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">Conversation Help</h3>
            <p className="text-sm text-gray-600">
              {settings.help_enabled ? 'Enabled' : 'Disabled'} • {getLanguageDisplayName(settings.help_language)}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Main toggle */}
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.help_enabled}
              onChange={(e) => updateSetting('help_enabled', e.target.checked)}
              className="sr-only peer"
              onClick={(e) => e.stopPropagation()}
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
          <Settings className={`w-4 h-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
        </div>
      </div>

      {/* Expanded Settings */}
      {isExpanded && settings.help_enabled && (
        <div className="border-t border-gray-200 p-4 space-y-4">
          {/* Help Language Selection */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <Globe className="w-4 h-4" />
              Help Language
            </label>
            <select
              value={settings.help_language}
              onChange={(e) => updateSetting('help_language', e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            >
              {SUPPORTED_HELP_LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.name} ({lang.native_name})
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Choose your native language for help explanations
            </p>
          </div>

          {/* Feature Toggles */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-gray-700">Show in Help Modal:</h4>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* Pronunciation Guide */}
              <label className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                <Volume2 className="w-4 h-4 text-blue-600 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-900">Pronunciation</div>
                  <div className="text-xs text-gray-500">Audio playback & phonetic guides</div>
                </div>
                <input
                  type="checkbox"
                  checked={settings.show_pronunciation}
                  onChange={(e) => updateSetting('show_pronunciation', e.target.checked)}
                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                />
              </label>

              {/* Vocabulary Highlights */}
              <label className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                <BookOpen className="w-4 h-4 text-green-600 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-900">Vocabulary</div>
                  <div className="text-xs text-gray-500">Key words with definitions</div>
                </div>
                <input
                  type="checkbox"
                  checked={settings.show_vocabulary}
                  onChange={(e) => updateSetting('show_vocabulary', e.target.checked)}
                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                />
              </label>

              {/* Grammar Tips */}
              <label className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                <MessageCircle className="w-4 h-4 text-purple-600 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-900">Grammar Tips</div>
                  <div className="text-xs text-gray-500">Pattern explanations & examples</div>
                </div>
                <input
                  type="checkbox"
                  checked={settings.show_grammar_tips}
                  onChange={(e) => updateSetting('show_grammar_tips', e.target.checked)}
                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                />
              </label>

              {/* Cultural Notes */}
              <label className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                <Globe className="w-4 h-4 text-orange-600 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-900">Cultural Context</div>
                  <div className="text-xs text-gray-500">Cultural insights & relevance</div>
                </div>
                <input
                  type="checkbox"
                  checked={settings.show_cultural_notes}
                  onChange={(e) => updateSetting('show_cultural_notes', e.target.checked)}
                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                />
              </label>
            </div>
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <HelpCircle className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-blue-800">
                <p className="font-medium mb-1">How it works:</p>
                <p>After each AI tutor response, a help modal will appear with personalized assistance in your chosen language. You can close it anytime to continue the conversation.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Disabled State Message */}
      {isExpanded && !settings.help_enabled && (
        <div className="border-t border-gray-200 p-4">
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <div className="flex items-center gap-2">
              <HelpCircle className="w-4 h-4 text-gray-400" />
              <p className="text-sm text-gray-600">
                Conversation help is disabled. Toggle the switch above to enable AI-powered assistance during your conversations.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConversationHelpSettings;
