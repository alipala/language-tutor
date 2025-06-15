'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { BookOpen, Scale, AlertTriangle, Users, Shield, Mail, Phone, MapPin } from 'lucide-react';

const TermsOfService: React.FC = () => {
  const lastUpdated = "January 15, 2025";

  const sections = [
    {
      title: "Acceptance of Terms",
      icon: BookOpen,
      content: [
        {
          subtitle: "Agreement to Terms",
          text: "By accessing and using Language Tutor's services, you accept and agree to be bound by the terms and provision of this agreement. If you do not agree to abide by the above, please do not use this service."
        },
        {
          subtitle: "Eligibility",
          text: "You must be at least 13 years old to use our services. If you are under 18, you must have your parent or guardian's permission to use our services."
        }
      ]
    },
    {
      title: "Use of Services",
      icon: Users,
      content: [
        {
          subtitle: "Permitted Use",
          text: "You may use our services for personal, non-commercial language learning purposes. You agree to use the services in compliance with all applicable laws and regulations."
        },
        {
          subtitle: "Account Responsibility",
          text: "You are responsible for maintaining the confidentiality of your account and password. You agree to accept responsibility for all activities that occur under your account."
        },
        {
          subtitle: "Prohibited Activities",
          text: "You may not use our services to engage in illegal activities, harass other users, distribute malware, or attempt to gain unauthorized access to our systems."
        }
      ]
    },
    {
      title: "Intellectual Property",
      icon: Shield,
      content: [
        {
          subtitle: "Our Content",
          text: "All content, features, and functionality of our services, including but not limited to text, graphics, logos, and software, are owned by Language Tutor and are protected by copyright and other intellectual property laws."
        },
        {
          subtitle: "User Content",
          text: "You retain ownership of any content you create or upload to our services. By using our services, you grant us a license to use, modify, and display your content for the purpose of providing our services."
        },
        {
          subtitle: "Feedback",
          text: "Any feedback, suggestions, or ideas you provide to us may be used by us without any obligation to compensate you."
        }
      ]
    },
    {
      title: "Privacy and Data",
      icon: Scale,
      content: [
        {
          subtitle: "Data Collection",
          text: "Our collection and use of personal information is governed by our Privacy Policy. By using our services, you consent to the collection and use of information as outlined in our Privacy Policy."
        },
        {
          subtitle: "Learning Data",
          text: "We may use aggregated and anonymized learning data to improve our services and develop new features. Individual user data is never shared without explicit consent."
        }
      ]
    },
    {
      title: "Service Availability",
      icon: AlertTriangle,
      content: [
        {
          subtitle: "Service Uptime",
          text: "While we strive to maintain high availability, we do not guarantee that our services will be available 100% of the time. We may experience downtime for maintenance, updates, or unforeseen circumstances."
        },
        {
          subtitle: "Modifications",
          text: "We reserve the right to modify, suspend, or discontinue any part of our services at any time. We will provide reasonable notice of significant changes when possible."
        },
        {
          subtitle: "Third-Party Services",
          text: "Our services may integrate with third-party services. We are not responsible for the availability, content, or practices of these third-party services."
        }
      ]
    },
    {
      title: "Limitation of Liability",
      icon: Shield,
      content: [
        {
          subtitle: "Disclaimer",
          text: "Our services are provided 'as is' without warranties of any kind. We disclaim all warranties, express or implied, including but not limited to merchantability and fitness for a particular purpose."
        },
        {
          subtitle: "Limitation",
          text: "In no event shall Language Tutor be liable for any indirect, incidental, special, or consequential damages arising out of or in connection with your use of our services."
        },
        {
          subtitle: "Maximum Liability",
          text: "Our total liability to you for any claims arising from your use of our services shall not exceed the amount you paid us in the twelve months preceding the claim."
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
              <Scale className="w-12 h-12 mr-4" />
              <h1 className="text-4xl font-bold">Terms of Service</h1>
            </div>
            <p className="text-xl text-white/90 mb-4">
              Please read these terms carefully before using our language learning platform.
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
              These Terms of Service ("Terms") govern your use of Language Tutor's website, mobile applications, and related services 
              (collectively, the "Services") operated by Language Tutor ("we," "us," or "our"). Please read these Terms carefully 
              before using our Services.
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

        {/* Termination */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.7 }}
          className="mb-8"
        >
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <div className="flex items-center mb-6">
              <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center mr-4">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-800">Termination</h2>
            </div>
            
            <div className="space-y-4">
              <p className="text-gray-600 leading-relaxed">
                We may terminate or suspend your account and access to our services immediately, without prior notice or liability, 
                for any reason whatsoever, including without limitation if you breach the Terms.
              </p>
              <p className="text-gray-600 leading-relaxed">
                You may terminate your account at any time by contacting us or using the account deletion feature in your settings. 
                Upon termination, your right to use the services will cease immediately.
              </p>
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
              If you have any questions about these Terms of Service, please contact us:
            </p>
            
            <div className="grid md:grid-cols-3 gap-6">
              <div className="flex items-center">
                <Mail className="w-5 h-5 text-[#4ECFBF] mr-3" />
                <div>
                  <p className="font-medium text-gray-800">Email</p>
                  <a href="mailto:legal@languagetutor.ai" className="text-[#4ECFBF] hover:underline">
                    legal@languagetutor.ai
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
          <div className="bg-blue-50 border border-blue-200 rounded-2xl p-6">
            <h3 className="text-lg font-semibold text-blue-800 mb-2">Changes to Terms</h3>
            <p className="text-blue-700">
              We reserve the right to modify or replace these Terms at any time. If a revision is material, we will try to provide 
              at least 30 days notice prior to any new terms taking effect. What constitutes a material change will be determined 
              at our sole discretion.
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default TermsOfService;
