'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Shield, Eye, Download, Trash2, Edit, Lock, Users, Mail, Phone, MapPin } from 'lucide-react';

const GDPRCompliance: React.FC = () => {
  const lastUpdated = "January 15, 2025";

  const rights = [
    {
      title: "Right to Information",
      icon: Eye,
      description: "You have the right to know what personal data we collect, how we use it, and who we share it with.",
      actions: [
        "View our Privacy Policy for detailed information",
        "Contact us for specific questions about data processing",
        "Request a summary of your data processing activities"
      ]
    },
    {
      title: "Right of Access",
      icon: Download,
      description: "You have the right to access your personal data and receive a copy of it.",
      actions: [
        "Download your data through your account settings",
        "Request a complete data export via email",
        "Access your learning history and progress data"
      ]
    },
    {
      title: "Right to Rectification",
      icon: Edit,
      description: "You have the right to correct inaccurate or incomplete personal data.",
      actions: [
        "Update your profile information directly",
        "Contact us to correct data you cannot edit yourself",
        "Request verification of corrected information"
      ]
    },
    {
      title: "Right to Erasure",
      icon: Trash2,
      description: "You have the right to request deletion of your personal data under certain circumstances.",
      actions: [
        "Delete your account through account settings",
        "Request specific data deletion via email",
        "Understand data retention requirements"
      ]
    },
    {
      title: "Right to Data Portability",
      icon: Download,
      description: "You have the right to receive your data in a structured, machine-readable format.",
      actions: [
        "Export your data in JSON or CSV format",
        "Transfer your learning progress to another service",
        "Receive your conversation history and assessments"
      ]
    },
    {
      title: "Right to Object",
      icon: Shield,
      description: "You have the right to object to certain types of data processing.",
      actions: [
        "Opt out of marketing communications",
        "Object to automated decision-making",
        "Withdraw consent for optional data processing"
      ]
    }
  ];

  const principles = [
    {
      title: "Lawfulness, Fairness, and Transparency",
      description: "We process personal data lawfully, fairly, and in a transparent manner. We clearly explain our data practices and obtain appropriate consent."
    },
    {
      title: "Purpose Limitation",
      description: "We collect personal data for specified, explicit, and legitimate purposes and do not process it in ways incompatible with those purposes."
    },
    {
      title: "Data Minimization",
      description: "We only collect and process personal data that is adequate, relevant, and limited to what is necessary for our purposes."
    },
    {
      title: "Accuracy",
      description: "We take reasonable steps to ensure that personal data is accurate and, where necessary, kept up to date."
    },
    {
      title: "Storage Limitation",
      description: "We keep personal data in a form that permits identification only for as long as necessary for our legitimate purposes."
    },
    {
      title: "Integrity and Confidentiality",
      description: "We process personal data securely using appropriate technical and organizational measures to protect against unauthorized access, loss, or damage."
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
              Language Tutor is committed to protecting your personal data and respecting your privacy rights under the 
              General Data Protection Regulation (GDPR). This page explains your rights under GDPR and how we ensure compliance 
              with these important data protection standards.
            </p>
            <p className="text-gray-600 leading-relaxed">
              The GDPR gives individuals in the European Union comprehensive rights over their personal data and imposes 
              strict obligations on organizations that process such data. We take these responsibilities seriously and have 
              implemented robust measures to ensure full compliance.
            </p>
          </div>
        </motion.div>

        {/* GDPR Principles */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mb-12"
        >
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-800 mb-8">GDPR Principles We Follow</h2>
            
            <div className="space-y-6">
              {principles.map((principle, index) => (
                <div key={principle.title} className="border-l-4 border-[#4ECFBF] pl-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">{principle.title}</h3>
                  <p className="text-gray-600 leading-relaxed">{principle.description}</p>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Your Rights */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="mb-12"
        >
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-800 mb-8">Your GDPR Rights</h2>
            
            <div className="grid gap-8">
              {rights.map((right, index) => (
                <div key={right.title} className="border border-gray-200 rounded-xl p-6">
                  <div className="flex items-start mb-4">
                    <div className="w-12 h-12 bg-[#4ECFBF]/10 rounded-xl flex items-center justify-center mr-4 flex-shrink-0">
                      <right.icon className="w-6 h-6 text-[#4ECFBF]" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-xl font-semibold text-gray-800 mb-2">{right.title}</h3>
                      <p className="text-gray-600 mb-4">{right.description}</p>
                      
                      <div>
                        <h4 className="font-medium text-gray-800 mb-2">How to exercise this right:</h4>
                        <ul className="space-y-1">
                          {right.actions.map((action, actionIndex) => (
                            <li key={actionIndex} className="text-gray-600 text-sm flex items-center">
                              <span className="w-1.5 h-1.5 bg-[#4ECFBF] rounded-full mr-2 flex-shrink-0"></span>
                              {action}
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

        {/* Data Processing */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="mb-8"
        >
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Legal Basis for Data Processing</h2>
            
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Consent</h3>
                <p className="text-gray-600 leading-relaxed">
                  We process your personal data based on your explicit consent for marketing communications, 
                  optional features, and analytics that improve your learning experience.
                </p>
              </div>
              
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Contract Performance</h3>
                <p className="text-gray-600 leading-relaxed">
                  We process your data to provide our language learning services, manage your account, 
                  and fulfill our contractual obligations to you.
                </p>
              </div>
              
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Legitimate Interest</h3>
                <p className="text-gray-600 leading-relaxed">
                  We may process your data for our legitimate business interests, such as improving our services, 
                  preventing fraud, and ensuring the security of our platform.
                </p>
              </div>
              
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Legal Obligation</h3>
                <p className="text-gray-600 leading-relaxed">
                  We process certain data to comply with legal obligations, such as tax requirements, 
                  regulatory compliance, and law enforcement requests.
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Data Protection Officer */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="mb-8"
        >
          <div className="bg-gradient-to-r from-[#4ECFBF]/10 to-[#3a9e92]/10 rounded-2xl p-8 border border-[#4ECFBF]/20">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Contact Our Data Protection Officer</h2>
            <p className="text-gray-600 mb-6">
              If you have any questions about your GDPR rights or our data protection practices, you can contact our 
              Data Protection Officer (DPO):
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

        {/* Supervisory Authority */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.7 }}
          className="mb-8"
        >
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Right to Lodge a Complaint</h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              If you believe that our processing of your personal data violates GDPR, you have the right to lodge a complaint 
              with a supervisory authority. You can contact the supervisory authority in your EU member state or the authority 
              where the alleged violation occurred.
            </p>
            <p className="text-gray-600 leading-relaxed">
              We encourage you to contact us first so we can address your concerns directly. However, you have the right to 
              contact a supervisory authority at any time without first contacting us.
            </p>
          </div>
        </motion.div>

        {/* Response Times */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
        >
          <div className="bg-blue-50 border border-blue-200 rounded-2xl p-6">
            <h3 className="text-lg font-semibold text-blue-800 mb-2">Response Times</h3>
            <p className="text-blue-700">
              We will respond to your GDPR requests within one month of receiving your request. In complex cases, 
              we may extend this period by up to two additional months, and we will inform you of any such extension 
              within the first month along with the reasons for the delay.
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default GDPRCompliance;
