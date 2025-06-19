'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, MessageSquare, BookOpen, Settings, Users, ChevronDown, ChevronRight } from 'lucide-react';

const HelpCenter: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null);

  const categories = [
    { title: "Getting Started", icon: BookOpen, count: 12 },
    { title: "Account & Billing", icon: Users, count: 8 },
    { title: "Technical Support", icon: Settings, count: 15 },
    { title: "Learning Features", icon: MessageSquare, count: 10 }
  ];

  const faqs = [
    {
      question: "How do I start my first conversation?",
      answer: "Simply select your target language and proficiency level, then click 'Start Conversation'. Our AI tutor will guide you through a natural conversation practice session."
    },
    {
      question: "What languages are supported?",
      answer: "We currently support English, Spanish, French, German, Portuguese, and Dutch. More languages are being added regularly."
    },
    {
      question: "How accurate is the pronunciation assessment?",
      answer: "Our AI uses advanced speech recognition technology with 95%+ accuracy. It provides real-time feedback on pronunciation, grammar, and fluency."
    },
    {
      question: "Can I use Language Tutor offline?",
      answer: "Currently, Language Tutor requires an internet connection for AI conversations and real-time assessment. We're working on offline features for future releases."
    },
    {
      question: "How do I track my learning progress?",
      answer: "Your progress is automatically tracked and displayed in your profile. You can view conversation history, achievements, and detailed analytics."
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
      <div className="bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white pt-32 pb-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center">
            <h1 className="text-5xl font-bold mb-6">Help Center</h1>
            <p className="text-xl text-white/90 max-w-3xl mx-auto leading-relaxed mb-8">
              Find answers to common questions and get the most out of your language learning experience.
            </p>
            <div className="max-w-2xl mx-auto relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search for help articles..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-12 pr-4 py-4 bg-white text-gray-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-800 mb-6">Browse by Category</h2>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mb-20">
            {categories.map((category, index) => (
              <div
                key={category.title}
                className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200 text-center hover:shadow-xl transition-shadow cursor-pointer"
              >
                <div className="w-16 h-16 bg-[#4ECFBF]/10 rounded-xl flex items-center justify-center mx-auto mb-6">
                  <category.icon className="w-8 h-8 text-[#4ECFBF]" />
                </div>
                <h3 className="text-xl font-bold text-gray-800 mb-2">{category.title}</h3>
                <p className="text-gray-600">{category.count} articles</p>
              </div>
            ))}
          </div>

          <div>
            <h2 className="text-4xl font-bold text-gray-800 mb-8 text-center">Frequently Asked Questions</h2>
            <div className="space-y-4">
              {faqs.map((faq, index) => (
                <div key={index} className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
                  <button
                    onClick={() => setExpandedFaq(expandedFaq === index ? null : index)}
                    className="w-full p-6 text-left flex items-center justify-between hover:bg-gray-50 transition-colors"
                  >
                    <h3 className="text-lg font-semibold text-gray-800">{faq.question}</h3>
                    {expandedFaq === index ? (
                      <ChevronDown className="w-5 h-5 text-gray-500" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-gray-500" />
                    )}
                  </button>
                  {expandedFaq === index && (
                    <div className="px-6 pb-6">
                      <p className="text-gray-600 leading-relaxed">{faq.answer}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="py-20 bg-gradient-to-r from-[#4ECFBF]/10 to-[#3a9e92]/10">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <div>
            <h2 className="text-4xl font-bold text-gray-800 mb-6">Still Need Help?</h2>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Can't find what you're looking for? Our support team is here to help you succeed.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a
                href="mailto:support@languagetutor.ai"
                className="px-8 py-4 bg-[#4ECFBF] hover:bg-[#3a9e92] text-white font-medium rounded-lg transition-colors duration-300"
              >
                Contact Support
              </a>
              <a
                href="/community"
                className="px-8 py-4 border-2 border-[#4ECFBF] text-[#4ECFBF] hover:bg-[#4ECFBF] hover:text-white font-medium rounded-lg transition-all duration-300"
              >
                Join Community
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HelpCenter;
