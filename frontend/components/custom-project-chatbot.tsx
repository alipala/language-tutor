'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

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
    response: 'Our Language Tutor offers:\n\n• Real-time AI conversations with instant feedback\n• Speaking assessment with CEFR level evaluation\n• 6 languages: English, Spanish, French, German, Italian, Portuguese\n• Personalized learning plans based on your level\n• Progress tracking with detailed analytics\n• Mobile-friendly design for learning anywhere\n\nWould you like to know more about any specific feature?'
  },
  {
    id: 'getting-started',
    label: 'Getting Started',
    emoji: '🚀',
    response: 'Getting started is easy!\n\n1. **Choose your language** - Select from 6 available languages\n2. **Take the assessment** - Speak for 15-60 seconds to get your CEFR level\n3. **Start practicing** - Begin real-time conversations with your AI tutor\n4. **Track progress** - Monitor your improvement with detailed analytics\n\nYou can start as a guest or create an account to save your progress. Ready to begin your language journey?'
  },
  {
    id: 'pricing',
    label: 'Pricing',
    emoji: '💰',
    response: 'We offer flexible pricing plans:\n\n**Basic ($9/month)**\n• 2 languages, 2 daily sessions\n• Basic progress tracking\n\n**Premium ($19/month)** - Most Popular\n• All 6 languages, unlimited sessions\n• Advanced analytics, downloadable lessons\n\n**Business ($49/month)**\n• All Premium features + team management\n• Up to 5 team members, custom learning paths\n\nAll plans include unlimited AI conversations and personalized feedback!'
  },
  {
    id: 'tech-stack',
    label: 'Tech Stack',
    emoji: '🔧',
    response: 'Our platform is built with cutting-edge technology:\n\n**Frontend:** Next.js 14, React, TypeScript, Tailwind CSS\n**Backend:** Python FastAPI, MongoDB\n**AI:** OpenAI GPT-4o-mini for conversations and analysis\n**Speech:** WebRTC for real-time voice interaction\n**Assessment:** Advanced pronunciation and grammar analysis\n**Deployment:** Railway with Docker containers\n\nThis ensures fast, reliable, and scalable language learning experiences!'
  },
  {
    id: 'mobile',
    label: 'Mobile Support',
    emoji: '📱',
    response: 'Yes! Our platform is fully mobile-optimized:\n\n• **Responsive design** - Works perfectly on phones and tablets\n• **Touch-friendly interface** - Easy navigation on mobile devices\n• **Voice recording** - Seamless speech input on mobile browsers\n• **Offline-ready** - Progressive Web App capabilities\n• **Cross-platform** - Works on iOS, Android, and desktop\n\nYou can practice your language skills anywhere, anytime!'
  }
];

const CustomProjectChatbot: React.FC = () => {
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
    
    if (lowerMessage.includes('technology') || lowerMessage.includes('ai') || lowerMessage.includes('speech')) {
      return [
        { id: 'ai-accuracy', label: 'AI Accuracy', emoji: '🎯', response: 'How accurate is your AI assessment?' },
        { id: 'privacy-data', label: 'Data Privacy', emoji: '🔒', response: 'How do you protect my data?' },
        { id: 'offline-mode', label: 'Offline Use', emoji: '📱', response: 'Can I use it offline?' }
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
    setTimeout(() => {
      const botResponse = generateResponse(action.response);
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
    setTimeout(() => {
      const botResponse = generateResponse(messageText);
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

  const generateResponse = (message: string): string => {
    const lowerMessage = message.toLowerCase();
    
    // Knowledge base responses - concise versions (max 6 lines)
    if (lowerMessage.includes('speaking') || lowerMessage.includes('assessment') || lowerMessage.includes('pronunciation')) {
      return 'Our AI speaking assessment evaluates your pronunciation, fluency, and grammar in real-time.\n\n• **CEFR Level Assessment** (A1-C2)\n• **Pronunciation Analysis** with specific feedback\n• **Grammar & Fluency Scoring**\n• **Personalized Recommendations**';
    }
    
    if (lowerMessage.includes('language') || lowerMessage.includes('supported') || lowerMessage.includes('available')) {
      return 'We support **6 languages** for comprehensive learning:\n\n🇬🇧 **English** • 🇪🇸 **Spanish** • 🇫🇷 **French**\n🇩🇪 **German** • 🇮🇹 **Italian** • 🇵🇹 **Portuguese**\n\nEach includes native speaker models and cultural context.';
    }
    
    if (lowerMessage.includes('price') || lowerMessage.includes('cost') || lowerMessage.includes('plan') || lowerMessage.includes('subscription')) {
      return 'Flexible pricing plans for every learner:\n\n💰 **Basic** - $9/month (2 languages, basic tracking)\n🌟 **Premium** - $19/month (All languages, unlimited sessions)\n🏢 **Business** - $49/month (Team features, up to 5 members)\n\n**All plans include 7-day free trial!**';
    }
    
    if (lowerMessage.includes('tech') || lowerMessage.includes('technology') || lowerMessage.includes('how') || lowerMessage.includes('work')) {
      return 'Built with cutting-edge technology:\n\n🔧 **Frontend:** Next.js, React, TypeScript, Tailwind\n⚙️ **Backend:** Python FastAPI, MongoDB, WebRTC\n🤖 **AI:** OpenAI GPT-4o-mini, advanced speech recognition\n☁️ **Infrastructure:** Railway deployment, global CDN';
    }
    
    if (lowerMessage.includes('mobile') || lowerMessage.includes('phone') || lowerMessage.includes('app') || lowerMessage.includes('device')) {
      return 'Yes! Fully mobile-optimized:\n\n📱 **Responsive design** for phones & tablets\n🎤 **Voice recording** on mobile browsers\n📲 **Progressive Web App** - install like native app\n🌐 **Cross-platform** - iOS, Android, desktop browsers';
    }
    
    if (lowerMessage.includes('start') || lowerMessage.includes('begin') || lowerMessage.includes('getting started') || lowerMessage.includes('how to')) {
      return 'Getting started is easy:\n\n1. **Choose your language** from 6 options\n2. **Take assessment** - speak for 15-60 seconds\n3. **Start practicing** with AI conversations\n4. **Track progress** with detailed analytics\n\n💡 **Tip:** Start as guest, create account to save progress!';
    }
    
    if (lowerMessage.includes('hello') || lowerMessage.includes('hi') || lowerMessage.includes('hey') || lowerMessage.includes('naber')) {
      return 'Hello! 👋 Welcome to Language Tutor!\n\nI can help with:\n• 🌟 **Features** - AI conversations & assessments\n• 🚀 **Getting Started** - Quick setup guide\n• 💰 **Pricing** - Plans from $9/month\n• 🔧 **Technology** & 📱 **Mobile Support**';
    }
    
    if (lowerMessage.includes('feature') || lowerMessage.includes('what') || lowerMessage.includes('offer')) {
      return 'Key features for effective learning:\n\n✨ **Real-time AI Conversations** with instant feedback\n🎯 **Speaking Assessment** - CEFR level evaluation\n🌍 **6 Languages** - English, Spanish, French, German, Italian, Portuguese\n📊 **Progress Tracking** with detailed analytics\n📱 **Mobile-friendly** design';
    }
    
    // Default response for unrecognized queries
    return 'I can help with Language Tutor info:\n\n• **Features** - AI conversations & assessment tools\n• **Getting Started** - Setup and first steps\n• **Pricing** - Plans and subscription options\n• **Technology** & **Mobile Support**\n\nTry the quick action buttons above for instant answers!';
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

export default CustomProjectChatbot;
