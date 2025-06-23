'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Shield, FileText, Eye, Lock, Users, CheckCircle, Mail, Phone, MapPin } from 'lucide-react';

const GDPRCompliance: React.FC = () => {
  const lastUpdated = "January 15, 2025";

  const rights = [
    {
      title: "Right to Information",
      icon: FileText,
      description: "You have the right to be informed about how we collect and use your personal data."
    },
    {
      title: "Right of Access",
      icon: Eye,
      description: "You can request copies of your personal data and information about how we process it."
    },
    {
      title: "Right to Rectification",
      icon: CheckCircle,
      description: "You can request that we correct any inaccurate or incomplete personal data."
    },
    {
      title: "Right to Erasure",
      icon: Shield,
      description: "You can request that we delete your personal data under certain circumstances."
    },
    {
      title: "Right to Restrict Processing",
      icon: Lock,
      description: "You can request that we limit how we process your personal data in certain situations."
    },
    {
      title: "Right to Data Portability",
      icon: Users,
      description: "You can request that we transfer your data to another organization or provide it in a machine-readable format."
    }
  ];

  const lawfulBases = [
    {
      title: "Consent",
      description: "We process your data when you have given clear consent for us to do so for specific purposes."
    },
    {
      title: "Contract",
      description: "We process your data when it's necessary for the performance of a contract with you."
    },
    {
      title: "Legal Obligation",
      description: "We process your data when we need to comply with a legal obligation."
    },
    {
      title: "Legitimate Interest",
      description: "We process your data when it's necessary for our legitimate interests, provided your rights are protected."
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
              <h1 className="text-4xl font-bold">GDPR Compliance</h1>
            </div>
            <p className="text-xl text-white/90 mb-4">
              Your data protection rights under the General Data Protection Regulation.
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
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Our Commitment to GDPR</h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              Language Tutor is committed to protecting your personal data and respecting your privacy rights. 
              We comply with the General Data Protection Regulation (GDPR) and other applicable data protection laws.
            </p>
            <p className="text-gray-600 leading-relaxed">
              This page explains your rights under GDPR and how we ensure compliance with these important regulations 
              that protect your personal information.
            </p>
          </div>
        </motion.div>

        {/* Your Rights */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mb-12"
        >
          <h2 className="text-3xl font-bold text-gray-800 mb-8 text-center">Your Data Protection Rights</h2>
          <div className="grid md:grid-cols-2 gap-8">
            {rights.map((right, index) => (
              <motion.div
                key={right.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 * (index + 4) }}
              >
                <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200 h-full">
                  <div className="flex items-center mb-4">
                    <div className="w-12 h-12 bg-[#4ECFBF]/10 rounded-xl flex items-center justify-center mr-4">
                      <right.icon className="w-6 h-6 text-[#4ECFBF]" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-800">{right.title}</h3>
                  </div>
                  <p className="text-gray-600 leading-relaxed">{right.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Lawful Basis */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.7 }}
          className="mb-12"
        >
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Lawful Basis for Processing</h2>
            <p className="text-gray-600 leading-relaxed mb-6">
              Under GDPR, we must have a lawful basis for processing your personal data. We rely on the following lawful bases:
            </p>
            
            <div className="grid md:grid-cols-2 gap-6">
              {lawfulBases.map((basis, index) => (
                <div key={basis.title} className="border border-gray-200 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">{basis.title}</h3>
                  <p className="text-gray-600 leading-relaxed">{basis.description}</p>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Data Processing */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
          className="mb-12"
        >
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">How We Process Your Data</h2>
            
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Data Collection</h3>
                <p className="text-gray-600 leading-relaxed">
                  We collect personal data only when necessary for providing our language learning services. 
                  This includes account information, learning progress, and usage analytics.
                </p>
              </div>
              
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Data Storage</h3>
                <p className="text-gray-600 leading-relaxed">
                  Your data is stored securely using industry-standard encryption and security measures. 
                  We retain data only for as long as necessary to provide our services or as required by law.
                </p>
              </div>
              
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Data Sharing</h3>
                <p className="text-gray-600 leading-relaxed">
                  We do not sell your personal data. We may share data with trusted service providers who help us 
                  operate our platform, but only under strict contractual obligations to protect your privacy.
                </p>
              </div>
              
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">International Transfers</h3>
                <p className="text-gray-600 leading-relaxed">
                  If we transfer your data outside the EU, we ensure appropriate safeguards are in place, 
                  such as adequacy decisions or standard contractual clauses.
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Exercising Your Rights */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.9 }}
          className="mb-12"
        >
          <div className="bg-gradient-to-r from-[#4ECFBF]/10 to-[#3a9e92]/10 rounded-2xl p-8 border border-[#4ECFBF]/20">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">How to Exercise Your Rights</h2>
            
            <div className="space-y-4">
              <p className="text-gray-600 leading-relaxed">
                To exercise any of your GDPR rights, please contact us using the information below. We will respond 
                to your request within one month, or sooner when possible.
              </p>
              
              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-800 mb-3">What to Include in Your Request</h3>
                <ul className="space-y-2 text-gray-600">
                  <li className="flex items-start">
                    <span className="w-2 h-2 bg-[#4ECFBF] rounded-full mt-2 mr-3 flex-shrink-0"></span>
                    <span>Your full name and email address associated with your account</span>
                  </li>
                  <li className="flex items-start">
                    <span className="w-2 h-2 bg-[#4ECFBF] rounded-full mt-2 mr-3 flex-shrink-0"></span>
                    <span>Clear description of the right you wish to exercise</span>
                  </li>
                  <li className="flex items-start">
                    <span className="w-2 h-2 bg-[#4ECFBF] rounded-full mt-2 mr-3 flex-shrink-0"></span>
                    <span>Any specific information or data you're referring to</span>
                  </li>
                  <li className="flex items-start">
                    <span className="w-2 h-2 bg-[#4ECFBF] rounded-full mt-2 mr-3 flex-shrink-0"></span>
                    <span>Proof of identity (to protect your data from unauthorized access)</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Data Protection Officer */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 1.0 }}
          className="mb-12"
        >
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Data Protection Officer</h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              We have appointed a Data Protection Officer (DPO) to oversee our data protection practices and 
              ensure compliance with GDPR requirements.
            </p>
            <p className="text-gray-600 leading-relaxed">
              You can contact our DPO directly for any data protection concerns or questions about how we 
              handle your personal information.
            </p>
          </div>
        </motion.div>

        {/* Contact Information */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 1.1 }}
          className="mb-8"
        >
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Contact Us</h2>
            <p className="text-gray-600 mb-6">
              For any GDPR-related questions or to exercise your rights, please contact us:
            </p>
            
            <div className="grid md:grid-cols-3 gap-6">
              <div className="flex items-center">
                <Mail className="w-5 h-5 text-[#4ECFBF] mr-3" />
                <div>
                  <p className="font-medium text-gray-800">Email</p>
                  <a href="mailto:dpo@languagetutor.ai" className="text-[#4ECFBF] hover:underline">
                    dpo@languagetutor.ai
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

        {/* Complaints */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 1.2 }}
        >
          <div className="bg-blue-50 border border-blue-200 rounded-2xl p-6">
            <h3 className="text-lg font-semibold text-blue-800 mb-2">Right to Lodge a Complaint</h3>
            <p className="text-blue-700">
              If you believe we have not handled your personal data in accordance with GDPR, you have the right to 
              lodge a complaint with your local data protection authority. However, we encourage you to contact us 
              first so we can try to resolve any concerns directly.
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default GDPRCompliance;
