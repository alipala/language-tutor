'use client';

import React, { useState, useEffect, useRef } from 'react';
import { HelpCircle, MessageCircle, BookOpen, X, Volume2, ChevronDown, ChevronUp } from 'lucide-react';
import { getApiUrl } from '@/lib/api-utils';

interface SuggestedResponse {
  text: string;
  pronunciation: string;
  explanation: string;
}

interface VocabularyItem {
  word: string;
  definition: string;
  pronunciation: string;
  example_sentence: string;
}

interface ConversationHelpData {
  ai_response_summary: string;
  suggested_responses: SuggestedResponse[];
  vocabulary_highlights: VocabularyItem[];
  generated_at: string;
}

interface ConversationHelpAfterAiProps {
  isEnabled: boolean;
  targetLanguage: string;
  helpLanguage: string;
  userLevel: string;
  conversationTopic: string;
  messages: Array<{ role: string; content: string; timestamp?: string }>;
}

const ConversationHelpAfterAi: React.FC<ConversationHelpAfterAiProps> = ({
  isEnabled,
  targetLanguage,
  helpLanguage,
  userLevel,
  conversationTopic,
  messages
}) => {
  const [showCountdown, setShowCountdown] = useState(false);
  const [countdown, setCountdown] = useState(5);
  const [showHelp, setShowHelp] = useState(false);
  const [helpData, setHelpData] = useState<ConversationHelpData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [lastAiMessage, setLastAiMessage] = useState<string>('');
  const [isExiting, setIsExiting] = useState(false);
  
  const countdownTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastProcessedMessageRef = useRef<string>('');
  const modalRef = useRef<HTMLDivElement>(null);

  // Multi-language UI text
  const getUIText = () => {
    const texts = {
      english: {
        conversationHelp: "Conversation Help",
        whatAiSaid: "What the AI said:",
        suggestedResponses: "Suggested responses:",
        keyVocabulary: "Key vocabulary:",
        generatingHelp: "Generating Personalized Help",
        analyzingConversation: "AI is analyzing the conversation...",
        creatingSuggestions: "Creating suggestions and explanations for you",
        more: "More",
        less: "Less"
      },
      spanish: {
        conversationHelp: "Ayuda de Conversación",
        whatAiSaid: "Lo que dijo la IA:",
        suggestedResponses: "Respuestas sugeridas:",
        keyVocabulary: "Vocabulario clave:",
        generatingHelp: "Generando Ayuda Personalizada",
        analyzingConversation: "La IA está analizando la conversación...",
        creatingSuggestions: "Creando sugerencias y explicaciones para ti",
        more: "Más",
        less: "Menos"
      },
      french: {
        conversationHelp: "Aide à la Conversation",
        whatAiSaid: "Ce que l'IA a dit:",
        suggestedResponses: "Réponses suggérées:",
        keyVocabulary: "Vocabulaire clé:",
        generatingHelp: "Génération d'Aide Personnalisée",
        analyzingConversation: "L'IA analyse la conversation...",
        creatingSuggestions: "Création de suggestions et d'explications pour vous",
        more: "Plus",
        less: "Moins"
      },
      german: {
        conversationHelp: "Gesprächshilfe",
        whatAiSaid: "Was die KI gesagt hat:",
        suggestedResponses: "Vorgeschlagene Antworten:",
        keyVocabulary: "Wichtige Vokabeln:",
        generatingHelp: "Personalisierte Hilfe wird generiert",
        analyzingConversation: "KI analysiert das Gespräch...",
        creatingSuggestions: "Erstelle Vorschläge und Erklärungen für dich",
        more: "Mehr",
        less: "Weniger"
      },
      italian: {
        conversationHelp: "Aiuto Conversazione",
        whatAiSaid: "Quello che ha detto l'IA:",
        suggestedResponses: "Risposte suggerite:",
        keyVocabulary: "Vocabolario chiave:",
        generatingHelp: "Generazione Aiuto Personalizzato",
        analyzingConversation: "L'IA sta analizzando la conversazione...",
        creatingSuggestions: "Creazione di suggerimenti e spiegazioni per te",
        more: "Di più",
        less: "Di meno"
      },
      portuguese: {
        conversationHelp: "Ajuda de Conversa",
        whatAiSaid: "O que a IA disse:",
        suggestedResponses: "Respostas sugeridas:",
        keyVocabulary: "Vocabulário chave:",
        generatingHelp: "Gerando Ajuda Personalizada",
        analyzingConversation: "IA está analisando a conversa...",
        creatingSuggestions: "Criando sugestões e explicações para você",
        more: "Mais",
        less: "Menos"
      },
      dutch: {
        conversationHelp: "Gesprekshulp",
        whatAiSaid: "Wat de AI zei:",
        suggestedResponses: "Voorgestelde antwoorden:",
        keyVocabulary: "Belangrijke woordenschat:",
        generatingHelp: "Gepersonaliseerde Hulp Genereren",
        analyzingConversation: "AI analyseert het gesprek...",
        creatingSuggestions: "Suggesties en uitleg voor jou maken",
        more: "Meer",
        less: "Minder"
      },
      turkish: {
        conversationHelp: "Konuşma Yardımı",
        whatAiSaid: "AI'nın söylediği:",
        suggestedResponses: "Önerilen yanıtlar:",
        keyVocabulary: "Anahtar kelimeler:",
        generatingHelp: "Kişiselleştirilmiş Yardım Oluşturuluyor",
        analyzingConversation: "AI konuşmayı analiz ediyor...",
        creatingSuggestions: "Sizin için öneriler ve açıklamalar oluşturuyor",
        more: "Daha fazla",
        less: "Daha az"
      }
    };
    
    return texts[helpLanguage as keyof typeof texts] || texts.english;
  };

  const uiText = getUIText();

  // 🚀 FIXED: Pass aiResponse directly to avoid React state timing issues
  const generateHelpContent = async (aiResponse: string) => {
    console.log('[HELP_AFTER_AI] 🚀 generateHelpContent called with aiResponse:', aiResponse);
    
    if (!aiResponse) {
      console.log('[HELP_AFTER_AI] ❌ No aiResponse provided, returning early');
      return;
    }

    console.log('[HELP_AFTER_AI] 🔄 Setting loading state and making API call...');
    // 🚀 SHOW MODAL IMMEDIATELY with loading state so user sees help is coming
    setIsLoading(true); // Show loading while we wait for AI
    setShowHelp(true);  // Show modal immediately with loading state
    
    // Auto-scroll to loading modal immediately when loading starts
    setTimeout(() => {
      if (modalRef.current) {
        modalRef.current.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'center',
          inline: 'nearest'
        });
      }
    }, 100);
    
    try {
      const conversationContext = messages.slice(-3).map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      console.log('[HELP_AFTER_AI] Generating AI help content...');

      const response = await fetch(`${getApiUrl()}/api/conversation-help/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ai_response: aiResponse.substring(0, 200),
          conversation_context: conversationContext,
          target_language: targetLanguage,
          user_language: helpLanguage,
          proficiency_level: userLevel,
          topic: conversationTopic
        }),
        signal: AbortSignal.timeout(10000) // 🚀 Increased to 10 seconds to prevent timeout
      });

      if (response.status === 204) {
        // 🚀 NEW: 204 No Content means no contextual help available
        console.log('[HELP_AFTER_AI] ✅ No contextual help available - not showing modal');
        setShowHelp(false);
        setIsLoading(false);
        return;
      }

      if (response.ok) {
        const data = await response.json();
        console.log('[HELP_AFTER_AI] ✅ Contextual help content generated successfully');
        console.log('[HELP_AFTER_AI] 🔍 Help data received:', data);
        
        // Show modal immediately with contextual content
        setHelpData(data);
        setShowHelp(true); // 🚀 SHOW MODAL IMMEDIATELY when content is ready
        setIsLoading(false);
        
        // Auto-scroll to modal after a short delay to ensure it's rendered
        setTimeout(() => {
          if (modalRef.current) {
            modalRef.current.scrollIntoView({ 
              behavior: 'smooth', 
              block: 'center',
              inline: 'nearest'
            });
          }
        }, 100);
        
        console.log('[HELP_AFTER_AI] 🎯 Modal state set - showHelp:', true, 'helpData:', !!data);
      } else {
        console.log('[HELP_AFTER_AI] ❌ API failed, not showing modal');
        // Don't show modal if API fails
        setShowHelp(false);
        setIsLoading(false);
      }
    } catch (error) {
      console.error('[HELP_AFTER_AI] ❌ Request failed with detailed error:', error);
      console.error('[HELP_AFTER_AI] ❌ Error type:', error instanceof Error ? error.constructor.name : typeof error);
      console.error('[HELP_AFTER_AI] ❌ Error message:', error instanceof Error ? error.message : String(error));
      console.error('[HELP_AFTER_AI] ❌ Error stack:', error instanceof Error ? error.stack : 'No stack trace');
      
      // Check if it's a network timeout
      if (error instanceof Error && error.name === 'AbortError') {
        console.error('[HELP_AFTER_AI] ❌ Request timed out after 10 seconds');
      } else if (error instanceof Error && error.message.includes('fetch')) {
        console.error('[HELP_AFTER_AI] ❌ Network fetch error');
      }
      
      // Don't show modal if request fails
      setShowHelp(false);
      setIsLoading(false);
    }
  };

  // Listen for AI response completion events (when AI finishes speaking)
  useEffect(() => {
    console.log('[HELP_AFTER_AI] 🔧 Setting up event listeners, isEnabled:', isEnabled);
    
    if (!isEnabled) {
      console.log('[HELP_AFTER_AI] ❌ Help is disabled, not setting up listeners');
      return;
    }

    const handleAIResponseComplete = (event: CustomEvent) => {
      console.log('[HELP_AFTER_AI] 🎯 AI response completion event received!', event.detail);
      
      const { aiResponse, conversationContext } = event.detail;
      
      if (!aiResponse) {
        console.log('[HELP_AFTER_AI] ❌ No AI response in event detail');
        return;
      }

      // Don't show help for the same message twice
      if (aiResponse === lastProcessedMessageRef.current) {
        console.log('[HELP_AFTER_AI] ⏭️ Skipping duplicate message:', aiResponse.substring(0, 50));
        return;
      }

      console.log('[HELP_AFTER_AI] ✅ AI response completion detected, generating help immediately...');
      console.log('[HELP_AFTER_AI] 📝 AI Response:', aiResponse.substring(0, 100));
      
      setLastAiMessage(aiResponse);
      lastProcessedMessageRef.current = aiResponse;

      // 🚀 IMMEDIATE HELP GENERATION - Pass aiResponse directly to avoid state timing issues
      generateHelpContent(aiResponse);
    };

    // Listen for user speaking start to begin exit animation
    const handleUserSpeakingStart = () => {
      if (showHelp && !isExiting) {
        console.log('[HELP_AFTER_AI] 🎤 User started speaking, beginning exit animation');
        setIsExiting(true);
        
        // Start exit animation, then hide modal after animation completes
        setTimeout(() => {
          setShowHelp(false);
          setHelpData(null);
          setIsLoading(false);
          setIsExiting(false);
        }, 300); // Match animation duration
      }
    };

    // Listen for user speaking completion to hide modal with proper animation
    const handleUserSpeakingComplete = () => {
      if (showHelp && !isExiting) {
        console.log('[HELP_AFTER_AI] 🎤 User finished speaking, hiding modal with smooth exit animation');
        setIsExiting(true);
        
        // Start exit animation, then hide modal after animation completes
        setTimeout(() => {
          setShowHelp(false);
          setHelpData(null);
          setIsLoading(false);
          setIsExiting(false);
        }, 300); // Match animation duration
      }
    };

    // Listen for input_audio_buffer.speech_stopped (when user finishes speaking)
    const handleInputAudioStop = () => {
      if (showHelp && !isExiting) {
        console.log('[HELP_AFTER_AI] 🎤 Audio input stopped, hiding modal with smooth exit animation');
        setIsExiting(true);
        
        // Start exit animation, then hide modal after animation completes
        setTimeout(() => {
          setShowHelp(false);
          setHelpData(null);
          setIsLoading(false);
          setIsExiting(false);
        }, 300); // Match animation duration
      }
    };

    // Listen for AI response completion events
    window.addEventListener('ai-response-complete', handleAIResponseComplete as EventListener);
    
    // Listen for user speech completion events to cancel help
    window.addEventListener('user-speaking-complete', handleUserSpeakingComplete as EventListener);
    
    // Listen for direct audio input stop events
    window.addEventListener('input-audio-stop', handleInputAudioStop as EventListener);

    return () => {
      window.removeEventListener('ai-response-complete', handleAIResponseComplete as EventListener);
      window.removeEventListener('user-speaking-complete', handleUserSpeakingComplete as EventListener);
      window.removeEventListener('input-audio-stop', handleInputAudioStop as EventListener);
    };
  }, [isEnabled, showHelp]);

  // 🚀 INSTANT RESPONSE TEMPLATES for immediate UI updates
  const getInstantFallback = () => {
    const templates = {
      dutch: [
        { text: "Ik begrijp het", pronunciation: "ɪk bəˈɣrɛip ət", explanation: "I understand" },
        { text: "Kun je dat herhalen?", pronunciation: "kʏn jə dɑt hərˈhaːlə", explanation: "Can you repeat that?" }
      ],
      spanish: [
        { text: "Entiendo", pronunciation: "en-tjen-do", explanation: "I understand" },
        { text: "¿Puedes repetir?", pronunciation: "pwe-des re-pe-tir", explanation: "Can you repeat?" }
      ],
      english: [
        { text: "I understand", pronunciation: "aɪ ˌʌndərˈstænd", explanation: "Shows comprehension" },
        { text: "Can you repeat that?", pronunciation: "kæn ju rɪˈpit ðæt", explanation: "Ask for repetition" }
      ]
    };

    const languageTemplates = templates[targetLanguage as keyof typeof templates] || templates.english;
    
    return {
      ai_response_summary: `The AI tutor provided guidance in ${targetLanguage}. They're helping you practice conversation skills.`,
      suggested_responses: languageTemplates,
      vocabulary_highlights: [],
      generated_at: new Date().toISOString()
    };
  };

  const playPronunciation = (text: string) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = targetLanguage === 'dutch' ? 'nl-NL' : 
                      targetLanguage === 'spanish' ? 'es-ES' :
                      targetLanguage === 'german' ? 'de-DE' :
                      targetLanguage === 'french' ? 'fr-FR' :
                      targetLanguage === 'portuguese' ? 'pt-PT' : 'en-US';
      utterance.rate = 0.8;
      speechSynthesis.speak(utterance);
    }
  };

  const handleGetHelp = () => {
    setShowCountdown(false);
    setShowHelp(true);
  };

  const handleClose = () => {
    setShowHelp(false);
    setShowCountdown(false);
    setIsExpanded(false);
    setHelpData(null);
  };

  // Don't show anything if help is disabled
  if (!isEnabled) {
    console.log('[HELP_AFTER_AI] 🚫 Component rendered but help is disabled');
    return null;
  }

  console.log('[HELP_AFTER_AI] 🎯 Component rendered with help enabled, showHelp:', showHelp, 'isLoading:', isLoading);

  // Show countdown timer
  if (showCountdown && countdown > 0) {
    return (
      <div className="w-full max-w-4xl mx-auto mt-4">
        <div className="flex items-center justify-center">
          <div className="flex items-center gap-3 bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 shadow-sm">
            <HelpCircle className="w-5 h-5 text-blue-600" />
            <span className="text-sm text-blue-700 font-medium">
              Need help? Getting assistance in {countdown}s
            </span>
            <button
              onClick={handleGetHelp}
              className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded-full hover:bg-blue-700 transition-colors font-medium"
            >
              Get Help Now
            </button>
          </div>
        </div>
      </div>
    );
  }


  // Show help content
  if (showHelp) {
    console.log('[HELP_AFTER_AI] 🎨 Rendering help modal with data:', helpData);
    return (
      <div ref={modalRef} className={`w-full mt-3 help-modal-container ${isExiting ? 'animate-slideOutDown' : 'animate-slideInUp'}`}>
        <div className="bg-gradient-to-br from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-3 shadow-md relative transition-all duration-500 ease-in-out transform">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                <HelpCircle className="w-4 h-4 text-white" />
              </div>
              <span className="text-base font-semibold text-gray-800">{uiText.conversationHelp}</span>
              {isLoading && (
                <div className="flex items-center gap-2 ml-2">
                  <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                  <span className="text-sm text-blue-600 font-medium">{uiText.generatingHelp}...</span>
                </div>
              )}
            </div>
            <button
              onClick={handleClose}
              className="p-1.5 rounded-full hover:bg-white/50 transition-colors"
            >
              <X className="w-5 h-5 text-gray-600" />
            </button>
          </div>

          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="relative mb-4">
                {/* Animated circles */}
                <div className="w-16 h-16 relative">
                  <div className="absolute inset-0 border-4 border-blue-200 rounded-full"></div>
                  <div className="absolute inset-0 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                  <div className="absolute inset-2 border-2 border-purple-300 rounded-full animate-pulse"></div>
                  <div className="absolute inset-4 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                    <MessageCircle className="w-4 h-4 text-white animate-pulse" />
                  </div>
                </div>
              </div>
              <div className="text-center">
                <h3 className="text-lg font-semibold text-gray-800 mb-2">{uiText.generatingHelp}</h3>
                <p className="text-sm text-gray-600 mb-1">{uiText.analyzingConversation}</p>
                <p className="text-xs text-gray-500">{uiText.creatingSuggestions}</p>
              </div>
              {/* Progress dots */}
              <div className="flex items-center gap-1 mt-4">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          ) : helpData ? (
            <div className="space-y-4">
              {/* AI Response Summary */}
              <div className="bg-white/70 rounded-lg p-4 border border-blue-100">
                <div className="flex items-start gap-2 mb-2">
                  <MessageCircle className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                  <h4 className="text-sm font-medium text-gray-800">{uiText.whatAiSaid}</h4>
                </div>
                <p className="text-sm text-gray-700 leading-relaxed">{helpData.ai_response_summary}</p>
              </div>

              {/* Suggested Responses */}
              <div className="bg-white/70 rounded-lg p-4 border border-green-100">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-medium text-gray-800">{uiText.suggestedResponses}</h4>
                  <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="flex items-center gap-1 text-xs text-gray-600 hover:text-gray-800"
                  >
                    {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                    {isExpanded ? uiText.less : uiText.more}
                  </button>
                </div>
                
                <div className="space-y-3">
                  {helpData.suggested_responses.slice(0, isExpanded ? undefined : 2).map((response, index) => (
                    <div key={index} className="bg-white rounded-md p-3 border border-gray-100 hover:border-green-300 transition-colors">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-800">{response.text}</p>
                          <p className="text-xs text-gray-500 mt-1">/{response.pronunciation}/</p>
                          {isExpanded && (
                            <p className="text-xs text-gray-600 mt-2">{response.explanation}</p>
                          )}
                        </div>
                        <button
                          onClick={() => playPronunciation(response.text)}
                          className="p-1.5 rounded-full hover:bg-green-100 transition-colors ml-3"
                        >
                          <Volume2 className="w-4 h-4 text-green-600" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Vocabulary (if expanded) */}
              {isExpanded && helpData.vocabulary_highlights.length > 0 && (
                <div className="bg-white/70 rounded-lg p-4 border border-yellow-100">
                  <h4 className="text-sm font-medium text-gray-800 mb-3">{uiText.keyVocabulary}</h4>
                  <div className="space-y-2">
                    {helpData.vocabulary_highlights.slice(0, 3).map((vocab, index) => (
                      <div key={index} className="bg-white rounded-md p-3 border border-gray-100">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p className="text-sm font-medium text-gray-800">{vocab.word}</p>
                            <p className="text-xs text-gray-600">{vocab.definition}</p>
                          </div>
                          <button
                            onClick={() => playPronunciation(vocab.word)}
                            className="p-1.5 rounded-full hover:bg-yellow-100 transition-colors ml-3"
                          >
                            <Volume2 className="w-4 h-4 text-yellow-600" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-6">
              <p className="text-sm text-gray-600">Unable to generate help content</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  return null;
};

export default ConversationHelpAfterAi;
