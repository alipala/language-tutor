'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { BookOpen, Users, BarChart3, Zap, Download, ExternalLink } from 'lucide-react';

const Research: React.FC = () => {
  const publications = [
    {
      title: "Adaptive AI Tutoring for Second Language Acquisition",
      authors: "Dr. Elena Petrov, Sarah Chen, Marcus Rodriguez",
      journal: "Journal of Educational Technology Research",
      year: "2024",
      abstract: "This study examines the effectiveness of adaptive AI tutoring systems in accelerating second language acquisition through personalized conversation practice."
    },
    {
      title: "Real-time Pronunciation Assessment Using Deep Learning",
      authors: "Marcus Rodriguez, Dr. Elena Petrov",
      journal: "Computer Speech & Language",
      year: "2024",
      abstract: "We present a novel approach to real-time pronunciation assessment using deep neural networks trained on multilingual speech data."
    },
    {
      title: "Measuring Language Learning Progress in AI-Mediated Conversations",
      authors: "Dr. Elena Petrov, James Kim",
      journal: "Language Learning & Technology",
      year: "2023",
      abstract: "This paper introduces new metrics for evaluating language learning progress in AI-mediated conversational environments."
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
      <div className="bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white py-20">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <h1 className="text-5xl font-bold mb-6">Research</h1>
            <p className="text-xl text-white/90 max-w-3xl mx-auto leading-relaxed">
              Advancing the science of language learning through cutting-edge research in AI, linguistics, and educational technology.
            </p>
          </motion.div>
        </div>
      </div>

      <div className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold text-gray-800 mb-6">Recent Publications</h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Our research team publishes findings in top-tier academic journals and conferences.
            </p>
          </motion.div>

          <div className="space-y-8">
            {publications.map((pub, index) => (
              <motion.div
                key={pub.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 * (index + 3) }}
                className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200"
              >
                <h3 className="text-2xl font-bold text-gray-800 mb-3">{pub.title}</h3>
                <p className="text-gray-600 mb-2">{pub.authors}</p>
                <p className="text-[#4ECFBF] font-medium mb-4">{pub.journal} ({pub.year})</p>
                <p className="text-gray-600 leading-relaxed mb-4">{pub.abstract}</p>
                <div className="flex gap-4">
                  <button className="flex items-center px-4 py-2 bg-[#4ECFBF] text-white rounded-lg hover:bg-[#3a9e92] transition-colors">
                    <Download className="w-4 h-4 mr-2" />
                    Download PDF
                  </button>
                  <button className="flex items-center px-4 py-2 border border-[#4ECFBF] text-[#4ECFBF] rounded-lg hover:bg-[#4ECFBF] hover:text-white transition-all">
                    <ExternalLink className="w-4 h-4 mr-2" />
                    View Online
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      <div className="py-20 bg-gradient-to-r from-[#4ECFBF]/10 to-[#3a9e92]/10">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <h2 className="text-4xl font-bold text-gray-800 mb-6">Research Collaboration</h2>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Interested in collaborating on language learning research? We welcome partnerships with academic institutions and researchers.
            </p>
            <a
              href="mailto:research@languagetutor.ai"
              className="px-8 py-4 bg-[#4ECFBF] hover:bg-[#3a9e92] text-white font-medium rounded-lg transition-colors duration-300"
            >
              Contact Research Team
            </a>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default Research;
