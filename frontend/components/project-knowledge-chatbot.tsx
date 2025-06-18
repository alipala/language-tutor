'use client';

import React, { useState, useEffect, useRef } from 'react';
import ChatBot from 'react-chatbotify';
import { getApiUrl } from '@/lib/api-utils';

interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

interface ProjectKnowledgeChatbotProps {
  className?: string;
}

const ProjectKnowledgeChatbot: React.FC<ProjectKnowledgeChatbotProps> = ({ className = '' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Chatbot settings with turquoise theme
  const settings = {
    general: {
      primaryColor: '#4ECFBF',
      secondaryColor: '#3a9e92',
      fontFamily: 'Inter, system-ui, sans-serif',
      showHeader: true,
      showFooter: false,
      embedded: false,
    },
    header: {
      title: 'Language Tutor Assistant',
      showAvatar: true,
      avatar: '🤖',
      buttons: [],
    },
    chatButton: {
      icon: '💬',
    },
    chatWindow: {
      showScrollbar: true,
      autoJumpToBottom: true,
      showMessagePrompt: true,
      messagePromptText: 'Ask me anything about Language Tutor...',
      defaultOpen: false,
    },
    botBubble: {
      showAvatar: true,
      avatar: '🤖',
      simStream: true,
      streamSpeed: 30,
    },
    userBubble: {
      showAvatar: false,
      animate: true,
    },
    voice: {
      disabled: true,
    },
    audio: {
      disabled: true,
    },
    notification: {
      disabled: true,
    },
    tooltip: {
      mode: 'CLOSE',
      text: 'Ask me about Language Tutor features!',
    },
    advance: {
      useAdvancedMessages: true,
    },
  };

  // Predefined conversation flow with basic questions
  const flow = {
    start: {
      message: "Hi! I'm your Language Tutor assistant. I can help you learn about our features, getting started, pricing, tech stack, and mobile support. What would you like to know?",
      options: [
        "🚀 Getting Started",
        "✨ Features",
        "💰 Pricing",
        "🔧 Tech Stack",
        "📱 Mobile Support"
      ],
      chatDisabled: false,
      path: "handle_selection"
    },
    handle_selection: {
      message: async (params: any) => {
        const userInput = params.userInput;
        
        // Handle predefined options
        if (userInput === "🚀 Getting Started") {
          return "To get started with Language Tutor:\n\n1. **Choose Your Language** - Select from English, Dutch, Spanish, French, German, or Portuguese\n2. **Take Assessment** - Complete a quick speaking assessment to determine your level\n3. **Start Practicing** - Begin conversations with our AI tutor\n4. **Track Progress** - Save your sessions and monitor improvement\n\nGuests can try 15-second assessments and 1-minute conversations. Sign up for unlimited access!\n\nWould you like to know more about any specific feature?";
        }
        
        if (userInput === "✨ Features") {
          return "Language Tutor offers powerful features:\n\n🎯 **Speaking Assessment** - AI-powered CEFR level evaluation\n💬 **Real-time Conversations** - WebRTC voice chat with AI tutor\n📊 **Progress Tracking** - Save sessions, view history, earn achievements\n🎨 **Personalized Learning** - Custom plans based on your assessment\n🌍 **Multi-language Support** - 6 languages available\n📱 **Mobile Friendly** - Works on all devices\n\n**Guest vs Registered Users:**\n- Guests: 15s assessments, 1min conversations\n- Registered: 60s assessments, 5min conversations, unlimited sessions\n\nWhat specific feature interests you most?";
        }
        
        if (userInput === "💰 Pricing") {
          return "Our pricing plans:\n\n**Free Trial (Guest)**\n- 15-second assessments\n- 1-minute conversations\n- Basic features\n\n**Basic Plan - $9/month**\n- 2 languages\n- 2 sessions daily\n- Basic progress tracking\n\n**Premium Plan - $19/month** ⭐ Most Popular\n- All 6 languages\n- Unlimited sessions\n- Advanced progress tracking\n- Priority support\n\n**Business Plan - $49/month**\n- All Premium features\n- Up to 5 team members\n- Team dashboard\n- Dedicated account manager\n\nAll plans include AI conversations and personalized feedback. Ready to start your free trial?";
        }
        
        if (userInput === "🔧 Tech Stack") {
          return "Language Tutor is built with modern technology:\n\n**Frontend:**\n- Next.js 14 with App Router\n- TypeScript for type safety\n- Tailwind CSS for styling\n- React ChatBotify (this chatbot!)\n\n**Backend:**\n- FastAPI (Python)\n- MongoDB for data storage\n- OpenAI GPT-4o for conversations\n- Whisper API for speech recognition\n\n**Real-time Features:**\n- WebRTC for voice streaming\n- OpenAI Realtime API\n- JWT authentication\n\n**Deployment:**\n- Railway for hosting\n- Docker containerization\n- HTTPS encryption\n\nInterested in the technical implementation of any specific feature?";
        }
        
        if (userInput === "📱 Mobile Support") {
          return "Language Tutor works great on mobile devices:\n\n📱 **Mobile Features:**\n- Responsive design for all screen sizes\n- Touch-optimized interface\n- Mobile microphone access\n- Offline-capable PWA features\n\n🎤 **Voice on Mobile:**\n- WebRTC works on iOS Safari and Android Chrome\n- Automatic microphone permission handling\n- Optimized for mobile networks\n\n💡 **Mobile Tips:**\n- Use headphones for better audio quality\n- Ensure stable internet connection\n- Allow microphone permissions when prompted\n- Works best in landscape mode for conversations\n\n**Browser Compatibility:**\n- iOS Safari 11+\n- Android Chrome 55+\n- Mobile Firefox 44+\n\nTry it now on your mobile device!";
        }
        
        // For any other input, use the RAG system
        return await handleRAGQuery(userInput);
      },
      options: [
        "🚀 Getting Started",
        "✨ Features", 
        "💰 Pricing",
        "🔧 Tech Stack",
        "📱 Mobile Support",
        "❓ Ask Custom Question"
      ],
      chatDisabled: false,
      path: "handle_selection"
    }
  };

  // Handle RAG queries for complex questions
  const handleRAGQuery = async (query: string): Promise<string> => {
    try {
      setIsLoading(true);
      
      const response = await fetch(`${getApiUrl()}/api/chat/project-knowledge`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();
      return data.response || "I'm sorry, I couldn't find information about that. Please try asking about our features, getting started, pricing, tech stack, or mobile support.";
    } catch (error) {
      console.error('Error querying RAG system:', error);
      return "I'm having trouble accessing that information right now. Please try asking about our main features like speaking assessment, real-time conversations, or progress tracking.";
    } finally {
      setIsLoading(false);
    }
  };

  // Custom styles for the chatbot
  const customStyles = `
    .rcb-chat-bot {
      font-family: 'Inter', system-ui, sans-serif;
    }
    
    .rcb-chat-button {
      background: linear-gradient(135deg, #4ECFBF 0%, #3a9e92 100%);
      border: none;
      box-shadow: 0 4px 12px rgba(78, 207, 191, 0.3);
      transition: all 0.3s ease;
    }
    
    .rcb-chat-button:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(78, 207, 191, 0.4);
    }
    
    .rcb-chat-window {
      border-radius: 16px;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
      border: 1px solid rgba(78, 207, 191, 0.2);
    }
    
    .rcb-chat-header {
      background: linear-gradient(135deg, #4ECFBF 0%, #3a9e92 100%);
      border-radius: 16px 16px 0 0;
      color: white;
      font-weight: 600;
    }
    
    .rcb-bot-message {
      background: #f0fdfa;
      border: 1px solid rgba(78, 207, 191, 0.2);
      border-radius: 12px;
      color: #1f2937;
    }
    
    .rcb-user-message {
      background: linear-gradient(135deg, #4ECFBF 0%, #3a9e92 100%);
      border-radius: 12px;
      color: white;
    }
    
    .rcb-options-container {
      gap: 8px;
    }
    
    .rcb-options {
      background: white;
      border: 2px solid #4ECFBF;
      color: #4ECFBF;
      border-radius: 20px;
      padding: 8px 16px;
      font-size: 14px;
      font-weight: 500;
      transition: all 0.2s ease;
    }
    
    .rcb-options:hover {
      background: #4ECFBF;
      color: white;
      transform: translateY(-1px);
    }
    
    .rcb-chat-input {
      border: 2px solid #e5e7eb;
      border-radius: 12px;
      padding: 12px 16px;
      transition: border-color 0.2s ease;
    }
    
    .rcb-chat-input:focus {
      border-color: #4ECFBF;
      outline: none;
      box-shadow: 0 0 0 3px rgba(78, 207, 191, 0.1);
    }
    
    .rcb-send-button {
      background: #4ECFBF;
      border-radius: 8px;
      transition: background-color 0.2s ease;
    }
    
    .rcb-send-button:hover {
      background: #3a9e92;
    }
  `;

  // Inject custom styles
  useEffect(() => {
    const styleElement = document.createElement('style');
    styleElement.textContent = customStyles;
    document.head.appendChild(styleElement);

    return () => {
      document.head.removeChild(styleElement);
    };
  }, []);

  return (
    <div className={`project-knowledge-chatbot ${className}`}>
      <ChatBot
        settings={settings}
        flow={flow}
      />
    </div>
  );
};

export default ProjectKnowledgeChatbot;
