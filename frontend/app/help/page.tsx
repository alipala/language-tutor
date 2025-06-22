'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { HelpCircle, MessageCircle, Book, Video, Users, Mail, Phone, MapPin, Search, Headphones } from 'lucide-react';

const HelpSupport: React.FC = () => {
  const helpCategories = [
    {
      title: "Getting Started",
      icon: Book,
      description: "Learn the basics of using Language Tutor",
      topics: [
        "Creating your account",
        "Setting up your learning profile",
        "Choosing your first language",
        "Understanding skill levels",
        "Taking your first assessment"
      ]
    },
    {
      title: "Using the AI Tutor",
      icon: MessageCircle,
      description: "Make the most of your conversation practice",
      topics: [
        "Starting a conversation",
        "Understanding feedback",
        "Improving pronunciation",
        "Grammar corrections",
        "Vocabulary building"
      ]
    },
    {
      title: "Technical Support",
      icon: Headphones,
      description: "Troubleshooting and technical issues",
      topics: [
        "Audio and microphone issues",
        "Browser compatibility",
        "Mobile app problems",
        "Account access issues",
        "Payment and billing"
      ]
    },
    {
      title: "Learning Tips",
      icon: Video,
      description: "Expert advice for effective language learning",
      topics: [
        "Daily practice routines",
        "Setting realistic goals",
        "Tracking your progress",
        "Overcoming learning plateaus",
        "Building confidence"
      ]
    }
  ];

  const faqs = [
    {
      question: "How does the AI tutor work?",
      answer: "Our AI tutor uses advanced natural language processing to engage in real-time conversations with you. It listens to your speech, provides instant feedback on pronunciation and grammar, and adapts to your learning level and goals."
    },
    {
      question: "What languages are supported?",
      answer: "We currently support over 25 languages including English, Spanish, French, German, Italian, Portuguese, Dutch, Chinese, Japanese, Korean, and many more. New languages are added regularly based on user demand."
    },
    {
      question: "Can I use Language Tutor on my mobile device?",
      answer: "Yes! Language Tutor works on all modern browsers and devices. We also have dedicated mobile apps for iOS and Android that provide the full learning experience optimized for mobile use."
    },
    {
      question: "How accurate is the speech recognition?",
      answer: "Our speech recognition technology is highly accurate and continuously improving. It can understand various accents and speaking speeds, and provides detailed feedback to help you improve your pronunciation."
    },
    {
      question: "Is my learning data private and secure?",
      answer: "Absolutely. We take your privacy seriously and comply with GDPR and other data protection regulations. Your learning data is encrypted and used only to improve your personalized learning experience."
    },
    {
      question: "Can I track my learning progress?",
      answer: "Yes, we provide detailed progress tracking including conversation time, vocabulary learned, grammar improvements, and skill level advancement. You can view your progress in your dashboard."
    }
  ];

  const contactMethods = [
    {
      title: "Live Chat",
      icon: MessageCircle,
      description: "Get instant help from our support team",
      availability: "24/7",
      action: "Start Chat"
    },
    {
      title: "Email Support",
      icon: Mail,
      description: "Send us a detailed message",
      availability: "Response within 24 hours",
      action: "Send Email"
    },
    {
      title: "Phone Support",
      icon: Phone,
      description: "Speak directly with our team",
      availability: "Mon-Fri, 9AM-6PM PST",
      action: "Call Now"
    },
    {
      title: "Community Forum",
      icon: Users,
      description: "Connect with other learners",
      availability: "Always active",
      action: "Join Forum"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white py-16">
        <div className="max-w-4xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <div className="flex items-center justify-center mb-6">
              <HelpCircle className="w-12 h-12 mr-4" />
              <h1 className="text-4xl font-bold">Help & Support</h1>
            </div>
            <p className="text-xl text-white/90 mb-4">
              Get the help you need to make the most of your language learning journey.
            </p>
          </motion.div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-6 py-16">
        {/* Search Bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mb-12"
        >
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">How can we help you?</h2>
            <div className="relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search for help topics, tutorials, or FAQs..."
                className="w-full pl-12 pr-4 py-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent outline-none text-gray-700"
              />
            </div>
          </div>
        </motion.div>

        {/* Help Categories */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mb-16"
        >
          <h2 className="text-3xl font-bold text-gray-800 mb-8 text-center">Browse Help Topics</h2>
          <div className="grid md:grid-cols-2 gap-8">
            {helpCategories.map((category, index) => (
              <motion.div
                key={category.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 * (index + 4) }}
              >
                <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200 h-full hover:shadow-xl transition-shadow cursor-pointer">
                  <div className="flex items-center mb-4">
                    <div className="w-12 h-12 bg-[#4ECFBF]/10 rounded-xl flex items-center justify-center mr-4">
                      <category.icon className="w-6 h-6 text-[#4ECFBF]" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-800">{category.title}</h3>
                  </div>
                  <p className="text-gray-600 leading-relaxed mb-4">{category.description}</p>
                  <ul className="space-y-2">
                    {category.topics.map((topic, topicIndex) => (
                      <li key={topicIndex} className="flex items-start">
                        <span className="w-2 h-2 bg-[#4ECFBF] rounded-full mt-2 mr-3 flex-shrink-0"></span>
                        <span className="text-gray-600 hover:text-[#4ECFBF] cursor-pointer">{topic}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* FAQs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.7 }}
          className="mb-16"
        >
          <h2 className="text-3xl font-bold text-gray-800 mb-8 text-center">Frequently Asked Questions</h2>
          <div className="space-y-6">
            {faqs.map((faq, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 * (index + 8) }}
              >
                <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3">{faq.question}</h3>
                  <p className="text-gray-600 leading-relaxed">{faq.answer}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Contact Methods */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 1.0 }}
          className="mb-16"
        >
          <h2 className="text-3xl font-bold text-gray-800 mb-8 text-center">Contact Support</h2>
          <div className="grid md:grid-cols-2 gap-8">
            {contactMethods.map((method, index) => (
              <motion.div
                key={method.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 * (index + 14) }}
              >
                <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200 hover:shadow-xl transition-shadow">
                  <div className="flex items-center mb-4">
                    <div className="w-12 h-12 bg-[#4ECFBF]/10 rounded-xl flex items-center justify-center mr-4">
                      <method.icon className="w-6 h-6 text-[#4ECFBF]" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-800">{method.title}</h3>
                  </div>
                  <p className="text-gray-600 leading-relaxed mb-4">{method.description}</p>
                  <p className="text-sm text-gray-500 mb-4">{method.availability}</p>
                  <button className="w-full bg-[#4ECFBF] text-white py-3 px-6 rounded-xl hover:bg-[#3a9e92] transition-colors font-medium">
                    {method.action}
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Quick Tips */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 1.2 }}
          className="mb-16"
        >
          <div className="bg-gradient-to-r from-[#4ECFBF]/10 to-[#3a9e92]/10 rounded-2xl p-8 border border-[#4ECFBF]/20">
            <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">Quick Tips for Better Learning</h2>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="w-16 h-16 bg-[#4ECFBF]/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">🎯</span>
                </div>
                <h3 className="font-semibold text-gray-800 mb-2">Set Daily Goals</h3>
                <p className="text-gray-600 text-sm">Practice for at least 15 minutes daily for consistent progress.</p>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-[#4ECFBF]/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">🎧</span>
                </div>
                <h3 className="font-semibold text-gray-800 mb-2">Use Good Audio</h3>
                <p className="text-gray-600 text-sm">Ensure clear audio for better speech recognition and feedback.</p>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-[#4ECFBF]/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">💪</span>
                </div>
                <h3 className="font-semibold text-gray-800 mb-2">Practice Regularly</h3>
                <p className="text-gray-600 text-sm">Consistency is key to building fluency and confidence.</p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Contact Information */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 1.3 }}
        >
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">Still Need Help?</h2>
            <p className="text-gray-600 mb-6 text-center">
              Our support team is here to help you succeed in your language learning journey.
            </p>
            
            <div className="grid md:grid-cols-3 gap-6">
              <div className="flex items-center justify-center">
                <Mail className="w-5 h-5 text-[#4ECFBF] mr-3" />
                <div className="text-center">
                  <p className="font-medium text-gray-800">Email</p>
                  <a href="mailto:support@languagetutor.ai" className="text-[#4ECFBF] hover:underline">
                    support@languagetutor.ai
                  </a>
                </div>
              </div>
              
              <div className="flex items-center justify-center">
                <Phone className="w-5 h-5 text-[#4ECFBF] mr-3" />
                <div className="text-center">
                  <p className="font-medium text-gray-800">Phone</p>
                  <a href="tel:+1-555-0123" className="text-[#4ECFBF] hover:underline">
                    +1 (555) 012-3456
                  </a>
                </div>
              </div>
              
              <div className="flex items-center justify-center">
                <MapPin className="w-5 h-5 text-[#4ECFBF] mr-3" />
                <div className="text-center">
                  <p className="font-medium text-gray-800">Location</p>
                  <p className="text-gray-600">San Francisco, CA</p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default HelpSupport;
