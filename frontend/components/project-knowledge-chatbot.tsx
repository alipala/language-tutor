'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getApiUrl } from '@/lib/api-utils';

// Check if user is logged in (you can replace this with your actual auth logic)
const isUserLoggedIn = () => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('authToken') !== null;
  }
  return false;
};

// Save conversation to localStorage for logged-in users
const saveConversation = (messages: Message[]) => {
  if (isUserLoggedIn() && typeof window !== 'undefined') {
    localStorage.setItem('chatbot_conversation', JSON.stringify(messages));
  }
};

// Load conversation from localStorage for logged-in users
const loadConversation = (): Message[] => {
  if (isUserLoggedIn() && typeof window !== 'undefined') {
    const saved = localStorage.getItem('chatbot_conversation');
    if (saved) {
      return JSON.parse(saved);
    }
  }
  return [
    {
      id: '1',
      text: 'Hi! I\'m your Language Tutor assistant. I can help you learn about our features, pricing, and how to get started. What would you like to know?',
      isBot: true,
      timestamp: new Date()
    }
  ];
};

// Enhanced text formatter with proper line breaks and list formatting
const formatText = (text: string): React.ReactNode => {
  // Split by line breaks first
  const lines = text.split('\n');
  
  return lines.map((line, lineIndex) => {
    if (line.trim() === '') {
      return <br key={lineIndex} />;
    }
    
    // Process each line for markdown formatting
    const parts = line.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);
    
    const formattedLine = parts.map((part, partIndex) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={partIndex}>{part.slice(2, -2)}</strong>;
      } else if (part.startsWith('*') && part.endsWith('*')) {
        return <em key={partIndex}>{part.slice(1, -1)}</em>;
      }
      return part;
    });
    
    // Check if line starts with bullet point
    if (line.trim().startsWith('•')) {
      // Remove the bullet point from the original text since we're adding our own
      const lineWithoutBullet = line.trim().substring(1).trim();
      const partsWithoutBullet = lineWithoutBullet.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);
      
      const formattedLineWithoutBullet = partsWithoutBullet.map((part, partIndex) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={partIndex}>{part.slice(2, -2)}</strong>;
        } else if (part.startsWith('*') && part.endsWith('*')) {
          return <em key={partIndex}>{part.slice(1, -1)}</em>;
        }
        return part;
      });
      
      return (
        <div key={lineIndex} className="flex items-start space-x-2 my-1">
          <span className="text-gray-600 mt-0.5">•</span>
          <span className="flex-1">{formattedLineWithoutBullet}</span>
        </div>
      );
    }
    
    // Regular line
    return (
      <div key={lineIndex} className={lineIndex > 0 ? 'mt-1' : ''}>
        {formattedLine}
      </div>
    );
  });
};

interface Message {
  id: string;
  text: string;
  isBot: boolean;
  timestamp: Date;
}

interface QuickAction {
  id: string;
  label: string;
  emoji: string;
  response: string;
}

const quickActions: QuickAction[] = [
  {
    id: 'features',
    label: 'Features',
    emoji: '✨',
    response: 'Tell me about the features'
  },
  {
    id: 'getting-started',
    label: 'Getting Started',
    emoji: '🚀',
    response: 'How do I get started?'
  },
  {
    id: 'pricing',
    label: 'Pricing',
    emoji: '💰',
    response: 'What are the pricing plans?'
  },
  {
    id: 'help',
    label: 'Help',
    emoji: '🎯',
    response: 'I need help'
  },
  {
    id: 'mobile',
    label: 'Mobile Support',
    emoji: '📱',
    response: 'How does it work on mobile?'
  }
];

interface ProjectKnowledgeChatbotProps {
  className?: string;
}

const ProjectKnowledgeChatbot: React.FC<ProjectKnowledgeChatbotProps> = ({ className = '' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>(loadConversation());
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentQuickActions, setCurrentQuickActions] = useState<QuickAction[]>(quickActions);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Save conversation when messages change
  useEffect(() => {
    saveConversation(messages);
  }, [messages]);

  // Generate dynamic follow-up buttons based on last bot message
  const generateFollowUpActions = (lastBotMessage: string): QuickAction[] => {
    const lowerMessage = lastBotMessage.toLowerCase();
    
    if (lowerMessage.includes('features') || lowerMessage.includes('real-time') || lowerMessage.includes('assessment')) {
      return [
        { id: 'speaking-details', label: 'Speaking Assessment', emoji: '🎤', response: 'Tell me more about the speaking assessment feature' },
        { id: 'languages-list', label: 'Supported Languages', emoji: '🌍', response: 'What languages do you support?' },
        { id: 'pricing-info', label: 'Pricing Plans', emoji: '💰', response: 'Show me the pricing plans' }
      ];
    }
    
    if (lowerMessage.includes('pricing') || lowerMessage.includes('plan') || lowerMessage.includes('$')) {
      return [
        { id: 'free-trial', label: 'Free Trial', emoji: '🆓', response: 'Tell me about the free trial' },
        { id: 'payment-methods', label: 'Payment Options', emoji: '💳', response: 'What payment methods do you accept?' },
        { id: 'cancel-anytime', label: 'Cancellation', emoji: '❌', response: 'Can I cancel my subscription anytime?' }
      ];
    }
    
    if (lowerMessage.includes('getting started') || lowerMessage.includes('begin') || lowerMessage.includes('journey')) {
      return [
        { id: 'demo-lesson', label: 'Try Demo', emoji: '▶️', response: 'Can I try a demo lesson?' },
        { id: 'account-setup', label: 'Create Account', emoji: '👤', response: 'How do I create an account?' },
        { id: 'first-steps', label: 'First Lesson', emoji: '📚', response: 'What happens in my first lesson?' }
      ];
    }
    
    // Default follow-up actions
    return [
      { id: 'more-info', label: 'Learn More', emoji: '📖', response: 'Tell me more details' },
      { id: 'get-started', label: 'Get Started', emoji: '🚀', response: 'How do I get started?' },
      { id: 'contact-support', label: 'Contact Us', emoji: '💬', response: 'How can I contact support?' }
    ];
  };

  const handleQuickAction = (action: QuickAction) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      text: action.response,
      isBot: false,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    // Simulate processing delay for better UX
    setTimeout(async () => {
      const botResponse = await generateResponse(action.response);
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: botResponse,
        isBot: true,
        timestamp: new Date()
      };
      const newMessages = [...messages, userMessage, botMessage];
      setMessages(newMessages);
      
      // Update quick actions based on bot response
      const followUpActions = generateFollowUpActions(botResponse);
      setCurrentQuickActions(followUpActions);
      setIsLoading(false);
    }, 1000);
  };

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      isBot: false,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const messageText = inputText;
    setInputText('');
    setIsLoading(true);

    // Simulate processing delay for better UX
    setTimeout(async () => {
      const botResponse = await generateResponse(messageText);
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: botResponse,
        isBot: true,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botMessage]);
      
      // Update quick actions based on bot response
      const followUpActions = generateFollowUpActions(botResponse);
      setCurrentQuickActions(followUpActions);
      setIsLoading(false);
    }, 1000);
  };

  // 🚀 USE VECTOR CHATBOT FOR ALL QUERIES
  const generateResponse = async (message: string): Promise<string> => {
    console.log(`🤖 [FRONTEND] Processing user query: "${message}"`);
    
    try {
      const response = await fetch(`${getApiUrl()}/api/chat/vector-knowledge`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: message }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();
      
      // Log similarity scores for debugging
      if (data.similarity_scores && data.similarity_scores.length > 0) {
        console.log(`🎯 Vector search results: Top similarity score: ${data.similarity_scores[0].toFixed(3)}`);
        console.log(`📚 Sources found: ${data.sources?.join(', ') || 'none'}`);
      }
      
      console.log(`✅ [FRONTEND] Vector chatbot response received`);
      return data.response || "I'm sorry, I couldn't find information about that. Please try asking about getting started, taking assessments, practicing conversations, saving progress, account help, mobile tips, or exporting data.";
    } catch (error) {
      console.error(`❌ [FRONTEND] Error with vector chatbot:`, error);
      return "I'm having trouble accessing my knowledge base right now. Please try asking about:\n\n🚀 Getting started with My Taco AI\n🎯 Taking speaking assessments\n💬 Practicing conversations\n📊 Saving and tracking progress\n🔐 Account and login help\n📱 Mobile usage tips\n📥 Exporting your data\n\nOr try refreshing the page and asking again!";
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <>
      {/* Simple Chat Bubble - Inspired by the attached image */}
      {!isOpen && (
        <motion.div
          className="fixed bottom-4 right-4 z-50 cursor-pointer"
          onClick={() => setIsOpen(true)}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <div className="bg-[#F75A5A] text-white px-4 py-3 rounded-2xl shadow-lg max-w-xs">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium">Talk to me!</span>
              <span className="text-lg">😊</span>
            </div>
            {/* Speech bubble tail */}
            <div className="absolute bottom-0 right-4 w-0 h-0 border-l-[8px] border-l-transparent border-r-[8px] border-r-transparent border-t-[8px] border-t-[#F75A5A] transform translate-y-full"></div>
          </div>
        </motion.div>
      )}

      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="fixed bottom-4 right-4 z-50 w-96 h-[500px] bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col overflow-hidden"
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
          >
            {/* Simple Header */}
            <div className="bg-[#F75A5A] p-4 text-white flex-shrink-0 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                  <span className="text-sm">💬</span>
                </div>
                <div>
                  <h3 className="font-medium text-sm">Language Tutor</h3>
                  <p className="text-xs text-white/80">Ask me anything!</p>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="w-6 h-6 flex items-center justify-center rounded-full hover:bg-white/20 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0 bg-gray-50">
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  className={`flex ${message.isBot ? 'justify-start' : 'justify-end'}`}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <div
                    className={`max-w-[80%] p-3 rounded-2xl text-sm ${
                      message.isBot
                        ? 'bg-white text-gray-800 shadow-sm'
                        : 'bg-[#F75A5A] text-white'
                    }`}
                  >
                    <div className="leading-relaxed">
                      {formatText(message.text)}
                    </div>
                  </div>
                </motion.div>
              ))}
              
              {isLoading && (
                <motion.div
                  className="flex justify-start"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  <div className="bg-white p-3 rounded-2xl shadow-sm">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </motion.div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Quick Actions */}
            <div className="p-2 border-t border-gray-200 bg-white flex-shrink-0">
              <div className="grid grid-cols-3 gap-1 mb-2">
                {currentQuickActions.slice(0, 3).map((action) => (
                  <button
                    key={action.id}
                    onClick={() => handleQuickAction(action)}
                    className="text-xs p-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors flex flex-col items-center"
                  >
                    <span className="text-xs mb-0.5">{action.emoji}</span>
                    <span className="text-gray-700 text-center leading-tight text-[10px]">{action.label}</span>
                  </button>
                ))}
              </div>
              {currentQuickActions.length > 3 && (
                <div className="grid grid-cols-2 gap-1 mb-2">
                  {currentQuickActions.slice(3).map((action) => (
                    <button
                      key={action.id}
                      onClick={() => handleQuickAction(action)}
                      className="text-xs p-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors flex flex-col items-center"
                    >
                      <span className="text-xs mb-0.5">{action.emoji}</span>
                      <span className="text-gray-700 text-center leading-tight text-[10px]">{action.label}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Input */}
            <div className="p-4 border-t border-gray-200 bg-white flex-shrink-0">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message..."
                  className="flex-1 p-3 border border-gray-300 rounded-2xl text-sm text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#F75A5A] focus:border-transparent"
                  disabled={isLoading}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!inputText.trim() || isLoading}
                  className="p-3 bg-[#F75A5A] text-white rounded-2xl hover:bg-[#F54242] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default ProjectKnowledgeChatbot;
