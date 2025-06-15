'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Download, Image, FileText, Users, Award, Globe, MessageSquare, Calendar } from 'lucide-react';

const PressKit: React.FC = () => {
  const assets = [
    {
      title: "Logo Package",
      description: "High-resolution logos in various formats (PNG, SVG, EPS)",
      size: "2.3 MB",
      icon: Image
    },
    {
      title: "Brand Guidelines",
      description: "Complete brand style guide and usage instructions",
      size: "1.8 MB", 
      icon: FileText
    },
    {
      title: "Product Screenshots",
      description: "High-quality screenshots of our platform and features",
      size: "5.2 MB",
      icon: Image
    },
    {
      title: "Executive Photos",
      description: "Professional headshots of our leadership team",
      size: "3.1 MB",
      icon: Users
    }
  ];

  const stats = [
    { number: "50K+", label: "Active Learners", icon: Users },
    { number: "6", label: "Languages Supported", icon: Globe },
    { number: "10K+", label: "Daily Conversations", icon: MessageSquare },
    { number: "94%", label: "Success Rate", icon: Award }
  ];

  const newsItems = [
    {
      date: "January 2025",
      title: "Language Tutor Raises $15M Series A to Expand AI-Powered Language Learning",
      outlet: "TechCrunch"
    },
    {
      date: "December 2024", 
      title: "The Future of Language Learning: How AI is Revolutionizing Education",
      outlet: "EdTech Magazine"
    },
    {
      date: "November 2024",
      title: "Language Tutor Named 'Best AI Education Platform' at EdTech Awards",
      outlet: "Education Week"
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
            <h1 className="text-5xl font-bold mb-6">Press Kit</h1>
            <p className="text-xl text-white/90 max-w-3xl mx-auto leading-relaxed">
              Resources for journalists, bloggers, and media professionals covering Language Tutor 
              and the future of AI-powered language learning.
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
              <h3 className="text-2xl font-bold text-gray-800 mb-6">About Language Tutor</h3>
              <p className="text-gray-600 leading-relaxed mb-4">
                Language Tutor is revolutionizing language learning through AI-powered conversations that provide 
                personalized, real-time feedback. Our platform makes language acquisition more natural and effective 
                by simulating real-world conversations with advanced AI technology.
              </p>
              <p className="text-gray-600 leading-relaxed mb-6">
                Founded in 2023, we've quickly grown to serve over 50,000 active learners across 6 languages, 
                with a 94% success rate in helping users achieve their language learning goals.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <a
                  href="mailto:press@languagetutor.ai"
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
              <h4 className="text-xl font-bold text-gray-800 mb-6">Key Statistics</h4>
              <div className="grid grid-cols-2 gap-6">
                {stats.map((stat, index) => (
                  <div key={stat.label} className="text-center">
                    <stat.icon className="w-8 h-8 text-[#4ECFBF] mx-auto mb-2" />
                    <div className="text-2xl font-bold text-gray-800 mb-1">{stat.number}</div>
                    <div className="text-gray-600 text-sm">{stat.label}</div>
                  </div>
                ))}
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
              Download high-quality assets for your stories and coverage.
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
                  <button className="p-2 bg-[#4ECFBF] hover:bg-[#3a9e92] text-white rounded-lg transition-colors duration-300">
                    <Download className="w-5 h-5" />
                  </button>
                </div>
                <p className="text-gray-600 leading-relaxed">{asset.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent News */}
      <div className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold text-gray-800 mb-6">Recent Coverage</h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Latest news and media coverage about Language Tutor.
            </p>
          </motion.div>

          <div className="space-y-6">
            {newsItems.map((item, index) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 * (index + 3) }}
                className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <Calendar className="w-4 h-4 text-[#4ECFBF] mr-2" />
                      <span className="text-sm text-gray-500">{item.date}</span>
                      <span className="mx-2 text-gray-300">•</span>
                      <span className="text-sm font-medium text-[#4ECFBF]">{item.outlet}</span>
                    </div>
                    <h3 className="text-xl font-bold text-gray-800">{item.title}</h3>
                  </div>
                </div>
              </motion.div>
            ))}
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
              For press inquiries, interviews, or additional information, please contact our media team.
            </p>
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200 max-w-md mx-auto">
              <h3 className="text-lg font-bold text-gray-800 mb-4">Press Contact</h3>
              <p className="text-gray-600 mb-2">Sarah Chen, CEO</p>
              <p className="text-[#4ECFBF] mb-2">press@languagetutor.ai</p>
              <p className="text-gray-600">+1 (555) 012-3456</p>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default PressKit;
