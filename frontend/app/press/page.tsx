'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Download, Image, FileText, Users, Award, Globe, MessageSquare, Calendar, Clock, Star } from 'lucide-react';

const PressKit: React.FC = () => {
  const assets = [
    {
      title: "Logo Package",
      description: "High-resolution MyTaco AI logos in various formats (PNG, SVG, EPS)",
      size: "2.1 MB",
      icon: Image,
      available: true
    },
    {
      title: "Brand Guidelines",
      description: "Complete brand style guide and usage instructions",
      size: "1.5 MB", 
      icon: FileText,
      available: true
    },
    {
      title: "Product Screenshots",
      description: "High-quality screenshots of our AI language learning platform",
      size: "4.8 MB",
      icon: Image,
      available: true
    },
    {
      title: "Founder Photos",
      description: "Professional headshots of Gamze and Ali Pala",
      size: "2.3 MB",
      icon: Users,
      available: true
    }
  ];

  const stats = [
    { number: "2025", label: "Founded", icon: Calendar },
    { number: "6", label: "Languages Supported", icon: Globe },
    { number: "AI-Powered", label: "Real-time Conversations", icon: MessageSquare },
    { number: "24/7", label: "Available Learning", icon: Clock }
  ];

  const upcomingMilestones = [
    {
      timeline: "Q2 2025",
      title: "MyTaco AI Official Launch - Revolutionizing Language Learning for Busy Parents",
      description: "Public launch of our AI-powered language learning platform designed specifically for time-constrained learners"
    },
    {
      timeline: "Q3 2025", 
      title: "European Expansion - Bringing Accessible Language Learning to More Communities",
      description: "Expanding our services across European markets with localized content and community partnerships"
    },
    {
      timeline: "Q4 2025",
      title: "Advanced AI Features - Enhanced Personalization and Learning Analytics",
      description: "Introduction of next-generation AI capabilities for even more personalized learning experiences"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white py-20">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <h1 className="text-5xl font-bold mb-6">MyTaco AI Press Kit</h1>
            <p className="text-xl text-white/90 max-w-3xl mx-auto leading-relaxed">
              Resources for journalists, bloggers, and media professionals covering MyTaco AI 
              and the future of accessible AI-powered language learning.
            </p>
          </motion.div>
        </div>
      </div>

      {/* Company Overview */}
      <div className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold text-gray-800 mb-6">Company Overview</h2>
          </motion.div>

          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
            >
              <h3 className="text-2xl font-bold text-gray-800 mb-6">About MyTaco AI</h3>
              <p className="text-gray-600 leading-relaxed mb-4">
                My Taco - AI Language Coach revolutionises language learning by offering AI-powered conversations, 
                personalised feedback, and adaptive learning experiences. It enables users to master any language 
                confidently through tailored practice and skill development.
              </p>
              <p className="text-gray-600 leading-relaxed mb-4">
                Imagine mastering a new language just by having real conversations, right from home. My Taco AI 
                combines advanced AI with live, voice-based tutors, providing instant feedback and tailored learning 
                plans based on your speaking skills.
              </p>
              <p className="text-gray-600 leading-relaxed mb-6">
                Founded in 2025 by immigrant parents Gamze Dede Pala and Ali Pala in Amsterdam, MyTaco AI was born 
                from personal experience struggling to find time for language learning while juggling work, family, 
                and community integration in the Netherlands.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <a
                  href="mailto:hello@mytacoai.com"
                  className="px-6 py-3 bg-[#4ECFBF] hover:bg-[#3a9e92] text-white font-medium rounded-lg transition-colors duration-300 text-center"
                >
                  Contact Press Team
                </a>
                <a
                  href="/about"
                  className="px-6 py-3 border-2 border-[#4ECFBF] text-[#4ECFBF] hover:bg-[#4ECFBF] hover:text-white font-medium rounded-lg transition-all duration-300 text-center"
                >
                  Learn More
                </a>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
              className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200"
            >
              <h4 className="text-xl font-bold text-gray-800 mb-6">Key Facts</h4>
              <div className="grid grid-cols-2 gap-6">
                {stats.map((stat, index) => (
                  <div key={stat.label} className="text-center">
                    <stat.icon className="w-8 h-8 text-[#4ECFBF] mx-auto mb-2" />
                    <div className="text-2xl font-bold text-gray-800 mb-1">{stat.number}</div>
                    <div className="text-gray-600 text-sm">{stat.label}</div>
                  </div>
                ))}
              </div>
              
              <div className="mt-8 pt-6 border-t border-gray-200">
                <h5 className="font-bold text-gray-800 mb-3">Mission</h5>
                <p className="text-gray-600 text-sm leading-relaxed">
                  Making language learning accessible to busy parents, professionals, and immigrants who want to learn 
                  but can't find the time or afford expensive traditional methods.
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Press Assets */}
      <div className="py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold text-gray-800 mb-6">Press Assets</h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Download high-quality assets for your stories and coverage about MyTaco AI.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-8">
            {assets.map((asset, index) => (
              <motion.div
                key={asset.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 * (index + 3) }}
                className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center">
                    <div className="w-12 h-12 bg-[#4ECFBF]/10 rounded-xl flex items-center justify-center mr-4">
                      <asset.icon className="w-6 h-6 text-[#4ECFBF]" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-800">{asset.title}</h3>
                      <p className="text-gray-500 text-sm">{asset.size}</p>
                    </div>
                  </div>
                  <button 
                    className="p-2 bg-[#4ECFBF] hover:bg-[#3a9e92] text-white rounded-lg transition-colors duration-300"
                    onClick={() => alert('Asset download will be available soon. Please contact hello@mytacoai.com for immediate access.')}
                  >
                    <Download className="w-5 h-5" />
                  </button>
                </div>
                <p className="text-gray-600 leading-relaxed">{asset.description}</p>
              </motion.div>
            ))}
          </div>

          <div className="mt-12 text-center">
            <div className="bg-[#FFD63A]/10 border border-[#FFD63A]/20 rounded-2xl p-6 max-w-2xl mx-auto">
              <h4 className="text-lg font-bold text-gray-800 mb-2">Need Additional Assets?</h4>
              <p className="text-gray-600 text-sm">
                For immediate access to press assets or custom materials, please contact our press team at 
                <a href="mailto:hello@mytacoai.com" className="text-[#4ECFBF] font-medium"> hello@mytacoai.com</a>
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Upcoming Milestones */}
      <div className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold text-gray-800 mb-6">Upcoming Milestones</h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Key developments and announcements to watch for from MyTaco AI.
            </p>
          </motion.div>

          <div className="space-y-6">
            {upcomingMilestones.map((item, index) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 * (index + 3) }}
                className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-3">
                      <Star className="w-4 h-4 text-[#FFD63A] mr-2" />
                      <span className="text-sm font-medium text-[#4ECFBF] bg-[#4ECFBF]/10 px-3 py-1 rounded-full">
                        {item.timeline}
                      </span>
                    </div>
                    <h3 className="text-xl font-bold text-gray-800 mb-2">{item.title}</h3>
                    <p className="text-gray-600 leading-relaxed">{item.description}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          <div className="mt-12 text-center">
            <div className="bg-gradient-to-r from-[#4ECFBF]/10 to-[#FFD63A]/10 border border-[#4ECFBF]/20 rounded-2xl p-8 max-w-3xl mx-auto">
              <h4 className="text-xl font-bold text-gray-800 mb-3">Stay Updated</h4>
              <p className="text-gray-600 mb-4">
                Be the first to know about MyTaco AI's major announcements, product launches, and company news.
              </p>
              <a
                href="mailto:hello@mytacoai.com?subject=Press Updates Subscription"
                className="inline-flex items-center px-6 py-3 bg-[#4ECFBF] hover:bg-[#3a9e92] text-white font-medium rounded-lg transition-colors duration-300"
              >
                Subscribe to Press Updates
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Contact */}
      <div className="py-20 bg-gradient-to-r from-[#4ECFBF]/10 to-[#3a9e92]/10">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <h2 className="text-4xl font-bold text-gray-800 mb-6">Media Inquiries</h2>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              For press inquiries, interviews, or additional information about MyTaco AI, please contact our team.
            </p>
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200 max-w-md mx-auto">
              <h3 className="text-lg font-bold text-gray-800 mb-4">Press Contact</h3>
              <p className="text-gray-600 mb-2">Gamze Dede Pala & Ali Pala</p>
              <p className="text-gray-600 mb-2">Co-Founders</p>
              <p className="text-[#4ECFBF] mb-2 font-medium">hello@mytacoai.com</p>
              <p className="text-gray-600 mb-2">+31 0657126162</p>
              <p className="text-gray-500 text-sm">Amsterdam, Netherlands</p>
            </div>

            <div className="mt-8 grid md:grid-cols-2 gap-6 max-w-2xl mx-auto">
              <div className="bg-white rounded-xl p-6 shadow-md border border-gray-200">
                <h4 className="font-bold text-gray-800 mb-2">Gamze Dede Pala</h4>
                <p className="text-sm text-gray-600 mb-2">Co-Founder</p>
                <p className="text-xs text-gray-500">
                  Expert in Prompt Engineering, Context Engineering, and accessible learning solutions
                </p>
              </div>
              <div className="bg-white rounded-xl p-6 shadow-md border border-gray-200">
                <h4 className="font-bold text-gray-800 mb-2">Ali Pala</h4>
                <p className="text-sm text-gray-600 mb-2">Co-Founder</p>
                <p className="text-xs text-gray-500">
                  GenAI Expert, 15+ years software development, AI Agents & Real-time Voice Chat specialist
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default PressKit;