'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Shield, Lock, Eye, Users, FileText, Mail, Phone, MapPin } from 'lucide-react';

const PrivacyPolicy: React.FC = () => {
  const lastUpdated = "January 15, 2025";

  const sections = [
    {
      title: "Information We Collect",
      icon: FileText,
      content: [
        {
          subtitle: "Personal Information",
          text: "We collect information you provide directly to us, such as when you create an account, use our language learning services, or contact us for support. This includes your name, email address, and learning preferences."
        },
        {
          subtitle: "Learning Data",
          text: "To provide personalized learning experiences, we collect data about your progress, conversation transcripts, assessment results, and usage patterns within our platform."
        },
        {
          subtitle: "Technical Information",
          text: "We automatically collect certain technical information, including your device type, browser information, IP address, and how you interact with our services."
        }
      ]
    },
    {
      title: "How We Use Your Information",
      icon: Users,
      content: [
        {
          subtitle: "Service Provision",
          text: "We use your information to provide, maintain, and improve our language learning services, including personalizing your learning experience and tracking your progress."
        },
        {
          subtitle: "Communication",
          text: "We may use your contact information to send you important updates about our services, respond to your inquiries, and provide customer support."
        },
        {
          subtitle: "Analytics and Improvement",
          text: "We analyze usage patterns and feedback to improve our platform, develop new features, and enhance the overall learning experience."
        }
      ]
    },
    {
      title: "Information Sharing",
      icon: Eye,
      content: [
        {
          subtitle: "No Sale of Data",
          text: "We do not sell, trade, or otherwise transfer your personal information to third parties for commercial purposes."
        },
        {
          subtitle: "Service Providers",
          text: "We may share information with trusted third-party service providers who assist us in operating our platform, conducting our business, or serving our users."
        },
        {
          subtitle: "Legal Requirements",
          text: "We may disclose your information when required by law, court order, or other legal process, or when we believe disclosure is necessary to protect our rights or the safety of others."
        }
      ]
    },
    {
      title: "Data Security",
      icon: Lock,
      content: [
        {
          subtitle: "Security Measures",
          text: "We implement appropriate technical and organizational security measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction."
        },
        {
          subtitle: "Encryption",
          text: "We use industry-standard encryption to protect sensitive data both in transit and at rest on our servers."
        },
        {
          subtitle: "Access Controls",
          text: "We maintain strict access controls and regularly review our security practices to ensure your data remains protected."
        }
      ]
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
              <Shield className="w-12 h-12 mr-4" />
              <h1 className="text-4xl font-bold">Privacy Policy</h1>
            </div>
            <p className="text-xl text-white/90 mb-4">
              Your privacy is important to us. Learn how we collect, use, and protect your information.
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
              Language Tutor ("we," "us," or "our") is committed to protecting your privacy. This Privacy Policy 
              explains how we collect, use, disclose, and safeguard your information when you use our language 
              learning platform and related services.
            </p>
          </div>
        </motion.div>

        {/* Sections */}
        {sections.map((section, index) => (
          <motion.div
            key={section.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 * (index + 3) }}
            className="mb-8"
          >
            <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
              <div className="flex items-center mb-6">
                <div className="w-12 h-12 bg-[#4ECFBF]/10 rounded-xl flex items-center justify-center mr-4">
                  <section.icon className="w-6 h-6 text-[#4ECFBF]" />
                </div>
                <h2 className="text-2xl font-bold text-gray-800">{section.title}</h2>
              </div>
              
              <div className="space-y-6">
                {section.content.map((item, itemIndex) => (
                  <div key={itemIndex}>
                    <h3 className="text-lg font-semibold text-gray-800 mb-2">{item.subtitle}</h3>
                    <p className="text-gray-600 leading-relaxed">{item.text}</p>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        ))}

        {/* Your Rights */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.7 }}
          className="mb-8"
        >
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <div className="flex items-center mb-6">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mr-4">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-800">Your Rights</h2>
            </div>
            
            <div className="space-y-4">
              <p className="text-gray-600 leading-relaxed">
                You have the right to access, update, or delete your personal information. You may also opt out of 
                certain communications from us. To exercise these rights, please contact us using the information below.
              </p>
              <ul className="space-y-2 text-gray-600">
                <li className="flex items-start">
                  <span className="w-2 h-2 bg-[#4ECFBF] rounded-full mt-2 mr-3 flex-shrink-0"></span>
                  <span>Access and review your personal data</span>
                </li>
                <li className="flex items-start">
                  <span className="w-2 h-2 bg-[#4ECFBF] rounded-full mt-2 mr-3 flex-shrink-0"></span>
                  <span>Request corrections to inaccurate information</span>
                </li>
                <li className="flex items-start">
                  <span className="w-2 h-2 bg-[#4ECFBF] rounded-full mt-2 mr-3 flex-shrink-0"></span>
                  <span>Delete your account and associated data</span>
                </li>
                <li className="flex items-start">
                  <span className="w-2 h-2 bg-[#4ECFBF] rounded-full mt-2 mr-3 flex-shrink-0"></span>
                  <span>Opt out of marketing communications</span>
                </li>
              </ul>
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
              If you have any questions about this Privacy Policy or our privacy practices, please contact us:
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

        {/* Changes Notice */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.9 }}
        >
          <div className="bg-yellow-50 border border-yellow-200 rounded-2xl p-6">
            <h3 className="text-lg font-semibold text-yellow-800 mb-2">Policy Updates</h3>
            <p className="text-yellow-700">
              We may update this Privacy Policy from time to time. We will notify you of any material changes by 
              posting the new Privacy Policy on this page and updating the "Last updated" date above.
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default PrivacyPolicy;
