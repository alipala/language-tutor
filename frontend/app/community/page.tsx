'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Users, MessageSquare, Globe, Award, Calendar, ExternalLink } from 'lucide-react';

const Community: React.FC = () => {
  return (
    <div className="min-h-screen pt-20 sm:pt-24" style={{ backgroundColor: '#0A0A0F' }}>
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-brand/20 to-[#3a9e92]/20 border-b border-white/[0.08] py-20">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <h1 className="text-5xl font-bold text-white mb-6">Community</h1>
            <p className="text-xl text-white/60 max-w-3xl mx-auto leading-relaxed">
              Connect with fellow language learners, share experiences, and practice together in our vibrant global community.
            </p>
          </motion.div>
        </div>
      </div>

      {/* Community Cards */}
      <div className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="rounded-2xl p-8 border border-white/[0.10] text-center hover:border-brand/30 transition-all duration-300"
              style={{ backgroundColor: '#13131F' }}
            >
              <div className="w-16 h-16 bg-brand/10 rounded-xl flex items-center justify-center mx-auto mb-6">
                <MessageSquare className="w-8 h-8 text-brand" />
              </div>
              <h3 className="text-xl font-bold text-white mb-4">Discord Server</h3>
              <p className="text-white/60 mb-6">Join our active Discord community for real-time chat and language exchange.</p>
              <a href="#" className="flex items-center justify-center px-6 py-3 bg-brand text-white rounded-lg hover:bg-[#3a9e92] transition-colors">
                Join Discord <ExternalLink className="w-4 h-4 ml-2" />
              </a>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="rounded-2xl p-8 border border-white/[0.10] text-center hover:border-brand/30 transition-all duration-300"
              style={{ backgroundColor: '#13131F' }}
            >
              <div className="w-16 h-16 bg-brand/10 rounded-xl flex items-center justify-center mx-auto mb-6">
                <Users className="w-8 h-8 text-brand" />
              </div>
              <h3 className="text-xl font-bold text-white mb-4">Study Groups</h3>
              <p className="text-white/60 mb-6">Find study partners and join language-specific practice groups.</p>
              <a href="#" className="flex items-center justify-center px-6 py-3 bg-brand text-white rounded-lg hover:bg-[#3a9e92] transition-colors">
                Find Groups <ExternalLink className="w-4 h-4 ml-2" />
              </a>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
              className="rounded-2xl p-8 border border-white/[0.10] text-center hover:border-brand/30 transition-all duration-300"
              style={{ backgroundColor: '#13131F' }}
            >
              <div className="w-16 h-16 bg-brand/10 rounded-xl flex items-center justify-center mx-auto mb-6">
                <Calendar className="w-8 h-8 text-brand" />
              </div>
              <h3 className="text-xl font-bold text-white mb-4">Events</h3>
              <p className="text-white/60 mb-6">Participate in virtual language meetups and learning challenges.</p>
              <a href="#" className="flex items-center justify-center px-6 py-3 bg-brand text-white rounded-lg hover:bg-[#3a9e92] transition-colors">
                View Events <ExternalLink className="w-4 h-4 ml-2" />
              </a>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Community Guidelines */}
      <div className="py-20 border-t border-white/[0.08]" style={{ backgroundColor: '#0E0E1A' }}>
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <h2 className="text-4xl font-bold text-white mb-6">Community Guidelines</h2>
            <p className="text-xl text-white/60 mb-8 max-w-2xl mx-auto">
              Our community is built on respect, support, and shared learning. Please follow our guidelines to maintain a positive environment for everyone.
            </p>
            <a
              href="/community/guidelines"
              className="px-8 py-4 bg-brand hover:bg-[#3a9e92] text-white font-medium rounded-lg transition-colors duration-300"
            >
              Read Guidelines
            </a>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default Community;
