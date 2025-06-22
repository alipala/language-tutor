'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Cookie, Settings, Eye, Shield, ToggleLeft, Mail, Phone, MapPin } from 'lucide-react';

const CookiePolicy: React.FC = () => {
  const lastUpdated = "January 15, 2025";

  const cookieTypes = [
    {
      title: "Essential Cookies",
      icon: Shield,
      description: "These cookies are necessary for the website to function and cannot be switched off in our systems.",
      examples: [
        "Authentication cookies to keep you logged in",
        "Security cookies to prevent fraud",
        "Session cookies to maintain your preferences"
      ],
      canDisable: false
    },
    {
      title: "Analytics Cookies",
      icon: Eye,
      description: "These cookies help us understand how visitors interact with our website by collecting and reporting information anonymously.",
      examples: [
        "Google Analytics to track page views",
        "User behavior tracking for improvements",
        "Performance monitoring cookies"
      ],
      canDisable: true
    },
    {
      title: "Functional Cookies",
      icon: Settings,
      description: "These cookies enable the website to provide enhanced functionality and personalization.",
      examples: [
        "Language preference cookies",
        "Learning progress tracking",
        "User interface customization"
      ],
      canDisable: true
    },
    {
      title: "Marketing Cookies",
      icon: ToggleLeft,
      description: "These cookies may be set through our site by our advertising partners to build a profile of your interests.",
      examples: [
        "Advertising targeting cookies",
        "Social media integration cookies",
        "Remarketing and conversion tracking"
      ],
      canDisable: true
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
              Learn about how we use cookies and similar technologies on our platform.
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
            <h2 className="text-2xl font-bold text-gray-800 mb-4">What Are Cookies?</h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              Cookies are small text files that are placed on your computer or mobile device when you visit our website. 
              They are widely used to make websites work more efficiently and to provide information to website owners.
            </p>
            <p className="text-gray-600 leading-relaxed">
              We use cookies and similar technologies to enhance your experience on Language Tutor, remember your preferences, 
              and provide personalized content and advertisements.
            </p>
          </div>
        </motion.div>

        {/* Cookie Types */}
        <div className="mb-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mb-8"
          >
            <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">Types of Cookies We Use</h2>
          </motion.div>

          {cookieTypes.map((cookieType, index) => (
            <motion.div
              key={cookieType.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 * (index + 4) }}
              className="mb-8"
            >
              <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center">
                    <div className="w-12 h-12 bg-[#4ECFBF]/10 rounded-xl flex items-center justify-center mr-4">
                      <cookieType.icon className="w-6 h-6 text-[#4ECFBF]" />
                    </div>
                    <h3 className="text-2xl font-bold text-gray-800">{cookieType.title}</h3>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                    cookieType.canDisable 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {cookieType.canDisable ? 'Optional' : 'Required'}
                  </div>
                </div>
                
                <p className="text-gray-600 leading-relaxed mb-4">
                  {cookieType.description}
                </p>
                
                <div>
                  <h4 className="text-lg font-semibold text-gray-800 mb-3">Examples:</h4>
                  <ul className="space-y-2">
                    {cookieType.examples.map((example, exampleIndex) => (
                      <li key={exampleIndex} className="flex items-start">
                        <span className="w-2 h-2 bg-[#4ECFBF] rounded-full mt-2 mr-3 flex-shrink-0"></span>
                        <span className="text-gray-600">{example}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Managing Cookies */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
          className="mb-8"
        >
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <div className="flex items-center mb-6">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mr-4">
                <Settings className="w-6 h-6 text-blue-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-800">Managing Your Cookie Preferences</h2>
            </div>
            
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Browser Settings</h3>
                <p className="text-gray-600 leading-relaxed">
                  You can control and/or delete cookies as you wish. You can delete all cookies that are already on your 
                  computer and you can set most browsers to prevent them from being placed.
                </p>
              </div>
              
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Cookie Consent</h3>
                <p className="text-gray-600 leading-relaxed">
                  When you first visit our website, you'll see a cookie consent banner. You can choose which types of 
                  cookies to accept or reject. You can change your preferences at any time through our cookie settings.
                </p>
              </div>
              
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Impact of Disabling Cookies</h3>
                <p className="text-gray-600 leading-relaxed">
                  Please note that if you disable cookies, some features of our website may not function properly, 
                  and your user experience may be affected.
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Third-Party Cookies */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.9 }}
          className="mb-8"
        >
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Third-Party Cookies</h2>
            
            <div className="space-y-4">
              <p className="text-gray-600 leading-relaxed">
                We may also use third-party services that set cookies on our website. These include:
              </p>
              
              <ul className="space-y-3">
                <li className="flex items-start">
                  <span className="w-2 h-2 bg-[#4ECFBF] rounded-full mt-2 mr-3 flex-shrink-0"></span>
                  <div>
                    <span className="font-medium text-gray-800">Google Analytics:</span>
                    <span className="text-gray-600 ml-2">For website analytics and performance monitoring</span>
                  </div>
                </li>
                <li className="flex items-start">
                  <span className="w-2 h-2 bg-[#4ECFBF] rounded-full mt-2 mr-3 flex-shrink-0"></span>
                  <div>
                    <span className="font-medium text-gray-800">Social Media Platforms:</span>
                    <span className="text-gray-600 ml-2">For social sharing and login functionality</span>
                  </div>
                </li>
                <li className="flex items-start">
                  <span className="w-2 h-2 bg-[#4ECFBF] rounded-full mt-2 mr-3 flex-shrink-0"></span>
                  <div>
                    <span className="font-medium text-gray-800">Payment Processors:</span>
                    <span className="text-gray-600 ml-2">For secure payment processing</span>
                  </div>
                </li>
              </ul>
              
              <p className="text-gray-600 leading-relaxed">
                These third parties have their own privacy policies and cookie policies, which we encourage you to review.
              </p>
            </div>
          </div>
        </motion.div>

        {/* Contact Information */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 1.0 }}
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
          transition={{ duration: 0.6, delay: 1.1 }}
        >
          <div className="bg-orange-50 border border-orange-200 rounded-2xl p-6">
            <h3 className="text-lg font-semibold text-orange-800 mb-2">Policy Updates</h3>
            <p className="text-orange-700">
              We may update this Cookie Policy from time to time to reflect changes in our practices or for other 
              operational, legal, or regulatory reasons. Please revisit this page regularly to stay informed about 
              our use of cookies.
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default CookiePolicy;
