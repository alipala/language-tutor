'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Code, Book, Key, Shield, ExternalLink } from 'lucide-react';

const ApiDocs: React.FC = () => {
  const endpoints = [
    {
      method: "POST",
      path: "/api/auth/login",
      description: "Authenticate user and receive access token",
      params: ["email", "password"]
    },
    {
      method: "GET",
      path: "/api/assessment/speaking",
      description: "Get speaking assessment for audio input",
      params: ["audio_data", "language", "level"]
    },
    {
      method: "POST",
      path: "/api/conversation/start",
      description: "Start a new AI conversation session",
      params: ["language", "level", "topic"]
    },
    {
      method: "GET",
      path: "/api/progress/stats",
      description: "Get user learning progress statistics",
      params: ["user_id"]
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
            <h1 className="text-5xl font-bold mb-6">API Documentation</h1>
            <p className="text-xl text-white/90 max-w-3xl mx-auto leading-relaxed">
              Integrate Language Tutor's AI-powered language learning capabilities into your applications with our comprehensive API.
            </p>
          </motion.div>
        </div>
      </div>

      <div className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200 text-center"
            >
              <div className="w-16 h-16 bg-[#4ECFBF]/10 rounded-xl flex items-center justify-center mx-auto mb-6">
                <Key className="w-8 h-8 text-[#4ECFBF]" />
              </div>
              <h3 className="text-xl font-bold text-gray-800 mb-4">Authentication</h3>
              <p className="text-gray-600">Secure API access with JWT tokens</p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200 text-center"
            >
              <div className="w-16 h-16 bg-[#4ECFBF]/10 rounded-xl flex items-center justify-center mx-auto mb-6">
                <Code className="w-8 h-8 text-[#4ECFBF]" />
              </div>
              <h3 className="text-xl font-bold text-gray-800 mb-4">RESTful API</h3>
              <p className="text-gray-600">Clean, predictable REST endpoints</p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
              className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200 text-center"
            >
              <div className="w-16 h-16 bg-[#4ECFBF]/10 rounded-xl flex items-center justify-center mx-auto mb-6">
                <Shield className="w-8 h-8 text-[#4ECFBF]" />
              </div>
              <h3 className="text-xl font-bold text-gray-800 mb-4">Rate Limiting</h3>
              <p className="text-gray-600">Fair usage policies and limits</p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.8 }}
              className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200 text-center"
            >
              <div className="w-16 h-16 bg-[#4ECFBF]/10 rounded-xl flex items-center justify-center mx-auto mb-6">
                <Book className="w-8 h-8 text-[#4ECFBF]" />
              </div>
              <h3 className="text-xl font-bold text-gray-800 mb-4">Documentation</h3>
              <p className="text-gray-600">Comprehensive guides and examples</p>
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 1.0 }}
          >
            <h2 className="text-4xl font-bold text-gray-800 mb-8 text-center">API Endpoints</h2>
            <div className="space-y-6">
              {endpoints.map((endpoint, index) => (
                <div key={index} className="bg-white rounded-2xl p-6 shadow-lg border border-gray-200">
                  <div className="flex items-center mb-4">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium mr-4 ${
                      endpoint.method === 'GET' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
                    }`}>
                      {endpoint.method}
                    </span>
                    <code className="text-lg font-mono text-gray-800">{endpoint.path}</code>
                  </div>
                  <p className="text-gray-600 mb-4">{endpoint.description}</p>
                  <div className="flex flex-wrap gap-2">
                    {endpoint.params.map((param, paramIndex) => (
                      <span key={paramIndex} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-sm font-mono">
                        {param}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>

      <div className="py-20 bg-gradient-to-r from-[#4ECFBF]/10 to-[#3a9e92]/10">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <h2 className="text-4xl font-bold text-gray-800 mb-6">Get Started</h2>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Ready to integrate Language Tutor into your application? Get your API key and start building.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a
                href="mailto:api@languagetutor.ai"
                className="px-8 py-4 bg-[#4ECFBF] hover:bg-[#3a9e92] text-white font-medium rounded-lg transition-colors duration-300"
              >
                Request API Key
              </a>
              <a
                href="#"
                className="px-8 py-4 border-2 border-[#4ECFBF] text-[#4ECFBF] hover:bg-[#4ECFBF] hover:text-white font-medium rounded-lg transition-all duration-300 flex items-center justify-center"
              >
                View Full Docs <ExternalLink className="w-4 h-4 ml-2" />
              </a>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default ApiDocs;
