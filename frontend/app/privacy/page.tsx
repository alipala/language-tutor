'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Shield, Lock, Eye, Database, Users, Mail, Phone, MapPin } from 'lucide-react';

const PrivacyPolicy: React.FC = () => {
  const lastUpdated = "January 15, 2025";

  const sections = [
    {
      title: "Information We Collect",
      icon: Database,
      content: [
        {
          subtitle: "Personal Information",
          text: "We collect information you provide directly to us, such as when you create an account, use our services, or contact us. This may include your name, email address, and language learning preferences."
        },
        {
          subtitle: "Usage Information",
          text: "We automatically collect information about your use of our services, including conversation transcripts, assessment results, learning progress, and interaction patterns to improve your learning experience."
        },
        {
          subtitle: "Audio Data",
          text: "When you use our speaking assessment features, we temporarily process audio recordings to provide feedback. Audio data is processed securely and is not stored permanently unless you explicitly save your progress."
        }
      ]
    },
    {
      title: "How We Use Your Information",
      icon: Eye,
      content: [
        {
          subtitle: "Service Provision",
          text: "We use your information to provide, maintain, and improve our language learning services, including personalized feedback, progress tracking, and adaptive learning experiences."
        },
        {
          subtitle: "Communication",
          text: "We may use your contact information to send you service-related communications, updates about new features, and educational content that may interest you."
        },
        {
          subtitle: "Analytics and Improvement",
          text: "We analyze usage patterns and learning outcomes to enhance our AI models, improve user experience, and develop new features that better serve our learning community."
        }
      ]
    },
    {
      title: "Information Sharing",
      icon: Users,
      content: [
        {
          subtitle: "No Sale of Personal Data",
          text: "We do not sell, rent, or trade your personal information to third parties for their commercial purposes."
        },
        {
          subtitle: "Service Providers",
          text: "We may share information with trusted service providers who assist us in operating our platform, such as cloud hosting services, analytics providers, and customer support tools."
        },
        {
          subtitle: "Legal Requirements",
          text: "We may disclose information when required by law, to protect our rights, or to ensure the safety and security of our users and services."
        }
      ]
    },
    {
      title: "Data Security",
      icon: Lock,
      content: [
        {
          subtitle: "Encryption",
          text: "All data transmission is encrypted using industry-standard TLS protocols. Personal information is encrypted at rest using AES-256 encryption."
        },
        {
          subtitle: "Access Controls",
          text: "We implement strict access controls and authentication mechanisms to ensure only authorized personnel can access user data, and only when necessary for service provision."
        },
        {
          subtitle: "Regular Audits",
          text: "Our security practices are regularly audited and updated to meet industry standards and regulatory requirements."
        }
      ]
    },
    {
      title: "Your Rights and Choices",
      icon: Shield,
      content: [
        {
          subtitle: "Access and Correction",
          text: "You have the right to access, update, or correct your personal information at any time through your account settings or by contacting us."
        },
        {
          subtitle: "Data Deletion",
          text: "You may request deletion of your account and associated data. Some information may be retained for legal or legitimate business purposes as outlined in our retention policy."
        },
        {
          subtitle: "Communication Preferences",
          text: "You can opt out of non-essential communications at any time by updating your preferences or using the unsubscribe link in our emails."
        }
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white pt-32 pb-16">
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
              Your privacy is important to us. This policy explains how we collect, use, and protect your information.
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
              Language Tutor ("we," "our," or "us") is committed to protecting your privacy and ensuring the security of your personal information. 
              This Privacy Policy describes how we collect, use, disclose, and safeguard your information when you use our language learning platform and services.
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
              If you have any questions about this Privacy Policy or our data practices, please contact us:
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
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6">
            <h3 className="text-lg font-semibold text-amber-800 mb-2">Policy Updates</h3>
            <p className="text-amber-700">
              We may update this Privacy Policy from time to time. We will notify you of any material changes by posting the new policy on this page 
              and updating the "Last updated" date. We encourage you to review this policy periodically.
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default PrivacyPolicy;
