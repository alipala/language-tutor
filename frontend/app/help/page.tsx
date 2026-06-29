'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { HelpCircle, MessageCircle, Mail, Phone } from 'lucide-react';

const HelpSupport: React.FC = () => {
  const faqs = [
    {
      question: "How does the AI-powered conversation system work?",
      answer: "MyTaco AI uses OpenAI's advanced Realtime API to enable natural voice conversations. The AI tutor listens to your speech, provides instant feedback on pronunciation and grammar, and adapts to your current language level. You can practice speaking in real-time with immediate corrections and suggestions."
    },
    {
      question: "What languages are supported?",
      answer: "We currently support 6 languages: English, Dutch, Spanish, German, French, and Portuguese. Each language includes multiple proficiency levels from A1 (beginner) to C2 (advanced), following the CEFR framework."
    },
    {
      question: "How does the speaking assessment work?",
      answer: "Our speaking assessment uses OpenAI's Whisper API for speech-to-text conversion and GPT-4o for analysis. You'll speak for 15 seconds (guests) or 60 seconds (registered users), and receive detailed feedback on pronunciation, grammar, vocabulary, fluency, and coherence with a CEFR level rating."
    },
    {
      question: "What's the difference between guest and registered users?",
      answer: "Guest users can: complete 15-second assessments, have 1-minute conversations, and try up to 3 assessments per session. Registered users get: 60-second assessments, 5-minute conversations, unlimited practice sessions, progress tracking, learning plans, and conversation history."
    },
    {
      question: "How do learning plans work?",
      answer: "After completing an assessment, you can create a personalized learning plan based on your proficiency level and goals. Learning plans include weekly schedules with specific focus areas, session goals, and progress tracking. Plans are generated using AI and can include custom topics based on your interests."
    },
    {
      question: "What subscription plans are available?",
      answer: "We offer three plans: Try & Learn (Free) with basic features, Fluency Builder (€19.99/month or €199.99/year) for serious learners with 30 practice sessions and 2 assessments monthly, and Team Mastery (€39.99/month or €399.99/year) for teams with unlimited sessions and assessments."
    },
    {
      question: "How does conversation memory work?",
      answer: "For registered users, conversations are automatically saved with AI-generated summaries. Your conversation history is preserved, and you can view detailed analytics of your practice sessions. Progress is tracked across sessions to show your improvement over time."
    },
    {
      question: "What topics can I practice with?",
      answer: "You can choose from predefined topics like Travel & Tourism, Food & Cooking, Work & Career, Hobbies & Interests, Family & Relationships, Movies & Entertainment, Music & Arts, Technology, and Environment. You can also create custom topics with web research integration for current information."
    },
    {
      question: "How accurate is the speech recognition and feedback?",
      answer: "We use OpenAI's Whisper-1 model for speech recognition, which provides high accuracy across multiple languages and accents. The AI feedback is powered by GPT-4o, offering detailed analysis of your speaking performance with specific suggestions for improvement."
    },
    {
      question: "Can I use MyTaco AI on mobile devices?",
      answer: "Yes! MyTaco AI works on all modern browsers including Chrome, Firefox, Safari, and Edge on both desktop and mobile devices. The interface is fully responsive and optimized for touch interaction on mobile devices."
    },
    {
      question: "Is my conversation data private and secure?",
      answer: "Absolutely. We take privacy seriously and implement enterprise-grade security. Your conversations are encrypted, stored securely, and used only to improve your personalized learning experience. We comply with GDPR and data protection regulations."
    },
    {
      question: "How do I track my learning progress?",
      answer: "Registered users can view comprehensive progress tracking in their profile, including total practice time, session history, CEFR level advancement, conversation summaries, achievements earned, and detailed analytics of their speaking improvement over time."
    }
  ];

  const contactMethods = [
    {
      title: "AI Chat Assistant",
      icon: MessageCircle,
      description: "Chat with our AI assistant on the homepage for instant help",
      availability: "Available 24/7",
      info: "Visit mytacoai.com and use the chat widget"
    },
    {
      title: "Email Support",
      icon: Mail,
      description: "Send us a detailed message for personalized assistance",
      availability: "Response within 24 hours",
      info: "hello@mytacoai.com"
    },
    {
      title: "Phone Support",
      icon: Phone,
      description: "Speak directly with our team",
      availability: "Available during business hours",
      info: "+31 6 21 18 55 93"
    }
  ];

  return (
    <div className="min-h-screen pt-20 sm:pt-24" style={{ backgroundColor: '#0A0A0F' }}>
      {/* Header */}
      <div className="py-16 px-4">
        <div className="max-w-4xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <div className="flex items-center justify-center mb-6">
              <div className="w-14 h-14 rounded-2xl bg-brand/10 border border-brand/20 flex items-center justify-center mr-4">
                <HelpCircle className="w-8 h-8 text-brand" />
              </div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-brand to-[#FFD63A] bg-clip-text text-transparent">
                Help &amp; Support
              </h1>
            </div>
            <p className="text-xl text-white/60 mb-4">
              Get the help you need to make the most of your AI-powered language learning journey.
            </p>
          </motion.div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-16">
        {/* FAQs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mb-16"
        >
          <h2 className="text-3xl font-bold text-white mb-8 text-center">Frequently Asked Questions</h2>
          <div className="space-y-6">
            {faqs.map((faq, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 * (index + 3) }}
              >
                <div className="bg-surface-1 rounded-2xl border border-white/[0.10] p-8">
                  <h3 className="text-lg font-semibold text-white mb-3">{faq.question}</h3>
                  <p className="text-white/60 leading-relaxed">{faq.answer}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Contact Methods */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
          className="mb-16"
        >
          <h2 className="text-3xl font-bold text-white mb-8 text-center">Contact Support</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {contactMethods.map((method, index) => (
              <motion.div
                key={method.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 * (index + 15) }}
              >
                <div className="bg-surface-1 rounded-2xl border border-white/[0.10] p-8 hover:border-brand/30 transition-colors h-full">
                  <div className="flex items-center mb-4">
                    <div className="w-12 h-12 bg-brand/10 rounded-xl flex items-center justify-center mr-4">
                      <method.icon className="w-6 h-6 text-brand" />
                    </div>
                    <h3 className="text-xl font-bold text-white">{method.title}</h3>
                  </div>
                  <p className="text-white/60 leading-relaxed mb-4">{method.description}</p>
                  <p className="text-sm text-white/40 mb-4">{method.availability}</p>
                  <div className="text-brand font-medium">
                    {method.info}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Quick Tips */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 1.0 }}
        >
          <div className="bg-brand/5 rounded-2xl p-8 border border-brand/20">
            <h2 className="text-2xl font-bold text-white mb-6 text-center">Quick Tips for Better Learning</h2>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="w-16 h-16 bg-brand/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">🎯</span>
                </div>
                <h3 className="font-semibold text-white mb-2">Practice Daily</h3>
                <p className="text-white/60 text-sm">Consistent 5-10 minute daily sessions are more effective than longer, infrequent practice.</p>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-brand/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">🎧</span>
                </div>
                <h3 className="font-semibold text-white mb-2">Use Good Audio</h3>
                <p className="text-white/60 text-sm">Ensure clear microphone quality for accurate speech recognition and better feedback.</p>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-brand/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">📱</span>
                </div>
                <h3 className="font-semibold text-white mb-2">Create Learning Plans</h3>
                <p className="text-white/60 text-sm">Take assessments and create personalized learning plans for structured progress.</p>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default HelpSupport;
