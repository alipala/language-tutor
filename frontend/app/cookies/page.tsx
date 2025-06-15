'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Cookie, Settings, BarChart3, Shield, Users, Mail, Phone, MapPin } from 'lucide-react';

const CookiePolicy: React.FC = () => {
  const lastUpdated = "January 15, 2025";

  const cookieTypes = [
    {
      title: "Essential Cookies",
      icon: Shield,
      description: "These cookies are necessary for the website to function and cannot be switched off in our systems.",
      examples: [
        "Authentication cookies to keep you logged in",
        "Security cookies to protect against fraud",
        "Session cookies to maintain your preferences"
      ],
      canDisable: false
    },
    {
      title: "Analytics Cookies",
      icon: BarChart3,
      description: "These cookies help us understand how visitors interact with our website by collecting and reporting information anonymously.",
      examples: [
        "Google Analytics to track page views and user behavior",
        "Performance monitoring to identify technical issues",
        "Usage statistics to improve our services"
      ],
      canDisable: true
    },
    {
      title: "Functional Cookies",
      icon: Settings,
      description: "These cookies enable the website to provide enhanced functionality and personalization.",
      examples: [
        "Language preferences",
        "Learning progress tracking",
        "User interface customizations"
      ],
      canDisable: true
    },
    {
      title: "Marketing Cookies",
      icon: Users,
      description: "These cookies may be set through our site by our advertising partners to build a profile of your interests.",
      examples: [
        "Advertising targeting cookies",
        "Social media integration cookies",
        "Conversion tracking pixels"
      ],
      canDisable: true
    }
  ];

  const sections = [
    {
      title: "What Are Cookies",
      content: "Cookies are small text files that are placed on your computer or mobile device when you visit a website. They are widely used to make websites work more efficiently and to provide information to website owners about how users interact with their sites."
    },
    {
      title: "How We Use Cookies",
      content: "We use cookies to enhance your experience on our language learning platform, remember your preferences, analyze site traffic, and provide personalized content. Cookies help us understand which features are most popular and how we can improve our services."
    },
    {
      title: "Third-Party Cookies",
      content: "Some cookies on our site are set by third-party services that appear on our pages. These include analytics services like Google Analytics, social media platforms, and advertising networks. We do not control these cookies, and you should check the relevant third party's website for more information."
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
              <Cookie className="w-12 h-12 mr-4" />
              <h1 className="text-4xl font-bold">Cookie Policy</h1>
            </div>
            <p className="text-xl text-white/90 mb-4">
              Learn about how we use cookies to improve your learning experience.
            </p>
            <p className="text-white/80">
              Last updated: {lastUpdated}
            </p>
          </motion.div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-6 py-16">
        {/* Introduction */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mb-12"
        >
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Introduction</h2>
            <p className="text-gray-600 leading-relaxed">
              This Cookie Policy explains how Language Tutor uses cookies and similar technologies when you visit our website 
              or use our services. It explains what these technologies are, why we use them, and your rights to control our use of them.
            </p>
          </div>
        </motion.div>

        {/* General Sections */}
        {sections.map((section, index) => (
          <motion.div
            key={section.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 * (index + 3) }}
            className="mb-8"
          >
            <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">{section.title}</h2>
              <p className="text-gray-600 leading-relaxed">{section.content}</p>
            </div>
          </motion.div>
        ))}

        {/* Cookie Types */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="mb-12"
        >
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-800 mb-8">Types of Cookies We Use</h2>
            
            <div className="grid gap-8">
              {cookieTypes.map((type, index) => (
                <div key={type.title} className="border border-gray-200 rounded-xl p-6">
                  <div className="flex items-start mb-4">
                    <div className="w-12 h-12 bg-[#4ECFBF]/10 rounded-xl flex items-center justify-center mr-4 flex-shrink-0">
                      <type.icon className="w-6 h-6 text-[#4ECFBF]" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-xl font-semibold text-gray-800">{type.title}</h3>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          type.canDisable 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-red-100 text-red-700'
                        }`}>
                          {type.canDisable ? 'Optional' : 'Required'}
                        </span>
                      </div>
                      <p className="text-gray-600 mb-4">{type.description}</p>
                      
                      <div>
                        <h4 className="font-medium text-gray-800 mb-2">Examples:</h4>
                        <ul className="space-y-1">
                          {type.examples.map((example, exampleIndex) => (
                            <li key={exampleIndex} className="text-gray-600 text-sm flex items-center">
                              <span className="w-1.5 h-1.5 bg-[#4ECFBF] rounded-full mr-2 flex-shrink-0"></span>
                              {example}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Cookie Management */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.7 }}
          className="mb-8"
        >
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Managing Your Cookie Preferences</h2>
            
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Browser Settings</h3>
                <p className="text-gray-600 leading-relaxed">
                  Most web browsers allow you to control cookies through their settings preferences. You can set your browser to 
                  refuse cookies or to alert you when cookies are being sent. However, if you disable cookies, some features of 
                  our website may not function properly.
                </p>
              </div>
              
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Cookie Consent</h3>
                <p className="text-gray-600 leading-relaxed">
                  When you first visit our website, you'll see a cookie consent banner that allows you to accept or decline 
                  non-essential cookies. You can change your preferences at any time by clicking the "Cookie Settings" link 
                  in our footer.
                </p>
              </div>
              
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Third-Party Opt-Outs</h3>
                <p className="text-gray-600 leading-relaxed">
                  For analytics cookies, you can opt out of Google Analytics by visiting the 
                  <a href="https://tools.google.com/dlpage/gaoptout" className="text-[#4ECFBF] hover:underline ml-1" target="_blank" rel="noopener noreferrer">
                    Google Analytics opt-out page
                  </a>.
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Contact Information */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
          className="mb-8"
        >
          <div className="bg-gradient-to-r from-[#4ECFBF]/10 to-[#3a9e92]/10 rounded-2xl p-8 border border-[#4ECFBF]/20">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Contact Us</h2>
            <p className="text-gray-600 mb-6">
              If you have any questions about our use of cookies, please contact us:
            </p>
            
            <div className="grid md:grid-cols-3 gap-6">
              <div className="flex items-center">
                <Mail className="w-5 h-5 text-[#4ECFBF] mr-3" />
                <div>
                  <p className="font-medium text-gray-800">Email</p>
                  <a href="mailto:privacy@languagetutor.ai" className="text-[#4ECFBF] hover:underline">
                    privacy@languagetutor.ai
                  </a>
                </div>
              </div>
              
              <div className="flex items-center">
                <Phone className="w-5 h-5 text-[#4ECFBF] mr-3" />
                <div>
                  <p className="font-medium text-gray-800">Phone</p>
                  <a href="tel:+1-555-0123" className="text-[#4ECFBF] hover:underline">
                    +1 (555) 012-3456
                  </a>
                </div>
              </div>
              
              <div className="flex items-center">
                <MapPin className="w-5 h-5 text-[#4ECFBF] mr-3" />
                <div>
                  <p className="font-medium text-gray-800">Address</p>
                  <p className="text-gray-600">San Francisco, CA</p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Updates Notice */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.9 }}
        >
          <div className="bg-orange-50 border border-orange-200 rounded-2xl p-6">
            <h3 className="text-lg font-semibold text-orange-800 mb-2">Policy Updates</h3>
            <p className="text-orange-700">
              We may update this Cookie Policy from time to time to reflect changes in our practices or for other operational, 
              legal, or regulatory reasons. We encourage you to review this policy periodically to stay informed about our use of cookies.
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default CookiePolicy;
