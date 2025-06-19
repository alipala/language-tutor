'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Users, Target, Globe, Award, Heart, Zap, MessageSquare, BookOpen } from 'lucide-react';

const AboutUs: React.FC = () => {
  const team = [
    {
      name: "Sarah Chen",
      role: "CEO & Co-Founder",
      bio: "Former Google AI researcher with 10+ years in language technology and machine learning.",
      image: "/images/team/sarah.jpg"
    },
    {
      name: "Marcus Rodriguez",
      role: "CTO & Co-Founder", 
      bio: "Ex-Microsoft engineer specializing in real-time communication and AI-powered education platforms.",
      image: "/images/team/marcus.jpg"
    },
    {
      name: "Dr. Elena Petrov",
      role: "Head of Linguistics",
      bio: "PhD in Applied Linguistics from Stanford, expert in second language acquisition and assessment.",
      image: "/images/team/elena.jpg"
    },
    {
      name: "James Kim",
      role: "Head of Product",
      bio: "Former Duolingo product manager with expertise in gamification and user engagement.",
      image: "/images/team/james.jpg"
    }
  ];

  const values = [
    {
      icon: Users,
      title: "Accessibility",
      description: "Making quality language education accessible to everyone, regardless of background or location."
    },
    {
      icon: Target,
      title: "Personalization",
      description: "Tailoring learning experiences to individual needs, goals, and learning styles."
    },
    {
      icon: Globe,
      title: "Cultural Bridge",
      description: "Connecting people across cultures through the power of language and communication."
    },
    {
      icon: Award,
      title: "Excellence",
      description: "Maintaining the highest standards in AI technology, pedagogy, and user experience."
    }
  ];

  const stats = [
    { number: "50K+", label: "Active Learners" },
    { number: "6", label: "Languages Supported" },
    { number: "10K+", label: "Daily Conversations" },
    { number: "94%", label: "Success Rate" }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white pt-32 pb-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center">
            <h1 className="text-5xl font-bold mb-6">About Language Tutor</h1>
            <p className="text-xl text-white/90 max-w-3xl mx-auto leading-relaxed">
              We're on a mission to revolutionize language learning through AI-powered conversations, 
              making fluency accessible to everyone, everywhere.
            </p>
          </div>
        </div>
      </div>

      {/* Mission Section */}
      <div className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid md:grid-cols-2 gap-16 items-center">
            <h2 className="text-4xl font-bold text-gray-800 mb-6">Our Mission</h2>
            <p className="text-xl text-gray-600 max-w-4xl mx-auto leading-relaxed">
              To break down language barriers and connect people worldwide through innovative AI technology 
              that makes language learning natural, engaging, and effective.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h3 className="text-2xl font-bold text-gray-800 mb-6">Why We Started</h3>
              <p className="text-gray-600 leading-relaxed mb-4">
                Traditional language learning methods often fail to provide the real-world practice needed for fluency. 
                We founded Language Tutor to bridge this gap using cutting-edge AI technology.
              </p>
              <p className="text-gray-600 leading-relaxed">
                Our platform provides personalized, conversational practice that adapts to each learner's pace and style, 
                making language acquisition more natural and effective than ever before.
              </p>
            </div>

            <div className="relative">
              <div className="grid grid-cols-2 gap-6">
                {stats.map((stat, index) => (
                  <div key={stat.label} className="text-center">
                    <div className="text-3xl font-bold text-[#4ECFBF] mb-2">{stat.number}</div>
                    <div className="text-gray-600 text-sm">{stat.label}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Values Section */}
      <div className="py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-800 mb-6">Our Values</h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              The principles that guide everything we do at Language Tutor.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {values.map((value, index) => (
              <div
                key={value.title}
                className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200 text-center"
              >
                <div className="w-16 h-16 bg-[#4ECFBF]/10 rounded-xl flex items-center justify-center mx-auto mb-6">
                  <value.icon className="w-8 h-8 text-[#4ECFBF]" />
                </div>
                <h3 className="text-xl font-bold text-gray-800 mb-4">{value.title}</h3>
                <p className="text-gray-600 leading-relaxed">{value.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Team Section */}
      <div className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-800 mb-6">Meet Our Team</h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Passionate experts in AI, linguistics, and education working together to transform language learning.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {team.map((member, index) => (
              <div
                key={member.name}
                className="bg-white rounded-2xl p-6 shadow-lg border border-gray-200 text-center"
              >
                <div className="w-24 h-24 bg-gradient-to-br from-[#4ECFBF] to-[#3a9e92] rounded-full mx-auto mb-6 flex items-center justify-center">
                  <Users className="w-12 h-12 text-white" />
                </div>
                <h3 className="text-xl font-bold text-gray-800 mb-2">{member.name}</h3>
                <p className="text-[#4ECFBF] font-medium mb-4">{member.role}</p>
                <p className="text-gray-600 text-sm leading-relaxed">{member.bio}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Technology Section */}
      <div className="py-20 bg-gradient-to-r from-[#4ECFBF]/10 to-[#3a9e92]/10">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-800 mb-6">Our Technology</h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Powered by state-of-the-art AI and machine learning technologies.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200">
              <MessageSquare className="w-12 h-12 text-[#4ECFBF] mb-6" />
              <h3 className="text-xl font-bold text-gray-800 mb-4">AI Conversations</h3>
              <p className="text-gray-600 leading-relaxed">
                Advanced natural language processing enables realistic, contextual conversations 
                that adapt to your learning level and interests.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200">
              <Zap className="w-12 h-12 text-[#4ECFBF] mb-6" />
              <h3 className="text-xl font-bold text-gray-800 mb-4">Real-time Assessment</h3>
              <p className="text-gray-600 leading-relaxed">
                Instant feedback on pronunciation, grammar, and fluency using cutting-edge 
                speech recognition and language analysis.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200">
              <BookOpen className="w-12 h-12 text-[#4ECFBF] mb-6" />
              <h3 className="text-xl font-bold text-gray-800 mb-4">Adaptive Learning</h3>
              <p className="text-gray-600 leading-relaxed">
                Machine learning algorithms personalize your learning path, adjusting difficulty 
                and content based on your progress and preferences.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Contact CTA */}
      <div className="py-20">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <div>
            <h2 className="text-4xl font-bold text-gray-800 mb-6">Join Our Mission</h2>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Ready to experience the future of language learning? Start your journey with Language Tutor today.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a
                href="/language-selection"
                className="px-8 py-4 bg-[#4ECFBF] hover:bg-[#3a9e92] text-white font-medium rounded-lg transition-colors duration-300"
              >
                Start Learning
              </a>
              <a
                href="/careers"
                className="px-8 py-4 border-2 border-[#4ECFBF] text-[#4ECFBF] hover:bg-[#4ECFBF] hover:text-white font-medium rounded-lg transition-all duration-300"
              >
                Join Our Team
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AboutUs;
