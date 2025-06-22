'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Heart, Users, Globe, Zap, Target, Award, Mail, Phone, MapPin } from 'lucide-react';

const AboutUs: React.FC = () => {
  const values = [
    {
      title: "Personalized Learning",
      icon: Target,
      description: "We believe every learner is unique. Our AI-powered platform adapts to your learning style, pace, and goals to provide a truly personalized experience."
    },
    {
      title: "Real Conversations",
      icon: Users,
      description: "Practice with our advanced AI tutor that engages in natural, meaningful conversations to build your confidence and fluency."
    },
    {
      title: "Global Accessibility",
      icon: Globe,
      description: "Language learning should be accessible to everyone, everywhere. Our platform works on any device, making learning convenient and flexible."
    },
    {
      title: "Continuous Innovation",
      icon: Zap,
      description: "We're constantly improving our technology and methods based on the latest research in language acquisition and AI."
    }
  ];

  const team = [
    {
      name: "Dr. Sarah Chen",
      role: "Chief Executive Officer",
      description: "Former Google AI researcher with a PhD in Computational Linguistics. Passionate about making language learning accessible to everyone."
    },
    {
      name: "Michael Rodriguez",
      role: "Chief Technology Officer",
      description: "15+ years in AI and machine learning. Previously led engineering teams at Duolingo and Babbel."
    },
    {
      name: "Dr. Emma Thompson",
      role: "Head of Learning Sciences",
      description: "Educational psychologist specializing in second language acquisition. Former professor at Stanford University."
    },
    {
      name: "David Kim",
      role: "Head of Product",
      description: "Product leader with experience at top tech companies. Focused on creating intuitive and engaging user experiences."
    }
  ];

  const stats = [
    { number: "500K+", label: "Active Learners" },
    { number: "25+", label: "Languages Supported" },
    { number: "10M+", label: "Conversations Completed" },
    { number: "95%", label: "User Satisfaction" }
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
              <Heart className="w-12 h-12 mr-4" />
              <h1 className="text-4xl font-bold">About Language Tutor</h1>
            </div>
            <p className="text-xl text-white/90 mb-4">
              Empowering millions of learners worldwide to master new languages through AI-powered conversations.
            </p>
          </motion.div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-6 py-16">
        {/* Mission */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mb-16"
        >
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">Our Mission</h2>
            <p className="text-lg text-gray-600 leading-relaxed text-center mb-6">
              To break down language barriers and connect people across cultures by providing the most effective, 
              accessible, and engaging language learning experience powered by artificial intelligence.
            </p>
            <p className="text-gray-600 leading-relaxed text-center">
              We believe that language learning should be conversational, practical, and fun. Our AI tutor provides 
              real-time feedback, adapts to your learning style, and helps you build confidence through natural conversations.
            </p>
          </div>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mb-16"
        >
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {stats.map((stat, index) => (
              <div key={stat.label} className="text-center">
                <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-200">
                  <div className="text-3xl font-bold text-[#4ECFBF] mb-2">{stat.number}</div>
                  <div className="text-gray-600 font-medium">{stat.label}</div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Values */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="mb-16"
        >
          <h2 className="text-3xl font-bold text-gray-800 mb-8 text-center">Our Values</h2>
          <div className="grid md:grid-cols-2 gap-8">
            {values.map((value, index) => (
              <motion.div
                key={value.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 * (index + 5) }}
              >
                <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200 h-full">
                  <div className="flex items-center mb-4">
                    <div className="w-12 h-12 bg-[#4ECFBF]/10 rounded-xl flex items-center justify-center mr-4">
                      <value.icon className="w-6 h-6 text-[#4ECFBF]" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-800">{value.title}</h3>
                  </div>
                  <p className="text-gray-600 leading-relaxed">{value.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Story */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
          className="mb-16"
        >
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">Our Story</h2>
            <div className="space-y-6 text-gray-600 leading-relaxed">
              <p>
                Language Tutor was founded in 2023 by a team of AI researchers, linguists, and educators who shared 
                a common frustration: traditional language learning methods weren't keeping up with the digital age.
              </p>
              <p>
                After experiencing the challenges of learning new languages themselves, our founders realized that 
                the key to effective language learning wasn't just memorizing vocabulary or grammar rules—it was 
                having meaningful conversations and receiving personalized feedback.
              </p>
              <p>
                Combining cutting-edge AI technology with proven language learning methodologies, we created an 
                intelligent tutor that can engage learners in natural conversations, provide instant feedback, 
                and adapt to individual learning styles and goals.
              </p>
              <p>
                Today, Language Tutor serves hundreds of thousands of learners worldwide, helping them achieve 
                their language learning goals through personalized, conversational AI tutoring.
              </p>
            </div>
          </div>
        </motion.div>

        {/* Team */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.9 }}
          className="mb-16"
        >
          <h2 className="text-3xl font-bold text-gray-800 mb-8 text-center">Meet Our Team</h2>
          <div className="grid md:grid-cols-2 gap-8">
            {team.map((member, index) => (
              <motion.div
                key={member.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 * (index + 10) }}
              >
                <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
                  <div className="flex items-center mb-4">
                    <div className="w-16 h-16 bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] rounded-full flex items-center justify-center mr-4">
                      <span className="text-white font-bold text-xl">
                        {member.name.split(' ').map(n => n[0]).join('')}
                      </span>
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-800">{member.name}</h3>
                      <p className="text-[#4ECFBF] font-medium">{member.role}</p>
                    </div>
                  </div>
                  <p className="text-gray-600 leading-relaxed">{member.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Awards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 1.0 }}
          className="mb-16"
        >
          <div className="bg-gradient-to-r from-[#4ECFBF]/10 to-[#3a9e92]/10 rounded-2xl p-8 border border-[#4ECFBF]/20">
            <div className="flex items-center justify-center mb-6">
              <Award className="w-8 h-8 text-[#4ECFBF] mr-3" />
              <h2 className="text-2xl font-bold text-gray-800">Recognition & Awards</h2>
            </div>
            <div className="grid md:grid-cols-3 gap-6 text-center">
              <div>
                <h3 className="font-bold text-gray-800 mb-2">EdTech Innovation Award</h3>
                <p className="text-gray-600">2024 - Best AI-Powered Learning Platform</p>
              </div>
              <div>
                <h3 className="font-bold text-gray-800 mb-2">App Store Editor's Choice</h3>
                <p className="text-gray-600">2024 - Featured in Education Category</p>
              </div>
              <div>
                <h3 className="font-bold text-gray-800 mb-2">TechCrunch Startup of the Year</h3>
                <p className="text-gray-600">2023 - Finalist in Education Technology</p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Contact */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 1.1 }}
        >
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">Get in Touch</h2>
            <p className="text-gray-600 mb-6 text-center">
              Have questions about our mission or want to learn more about Language Tutor? We'd love to hear from you.
            </p>
            
            <div className="grid md:grid-cols-3 gap-6">
              <div className="flex items-center justify-center">
                <Mail className="w-5 h-5 text-[#4ECFBF] mr-3" />
                <div className="text-center">
                  <p className="font-medium text-gray-800">Email</p>
                  <a href="mailto:hello@languagetutor.ai" className="text-[#4ECFBF] hover:underline">
                    hello@languagetutor.ai
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

export default AboutUs;
