'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MessageSquare, 
  Globe, 
  Shield, 
  Users, 
  BookOpen, 
  Award,
  Mail,
  Phone,
  MapPin,
  Twitter,
  Linkedin,
  Github,
  Youtube,
  ChevronRight,
  Heart,
  Zap,
  Star,
  TrendingUp
} from 'lucide-react';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();
  const [showScrollButton, setShowScrollButton] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const footer = document.querySelector('footer');
      if (footer) {
        const footerRect = footer.getBoundingClientRect();
        const windowHeight = window.innerHeight;
        
        // Show button only when footer is visible (at least 100px of footer is visible)
        const isFooterVisible = footerRect.top < windowHeight - 100;
        setShowScrollButton(isFooterVisible);
      }
    };

    window.addEventListener('scroll', handleScroll);
    handleScroll(); // Check initial state

    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const footerSections = [
    {
      title: "Languages",
      links: [
        { name: "English", href: "/language-selection?lang=english", icon: Globe },
        { name: "Spanish", href: "/language-selection?lang=spanish", icon: Globe },
        { name: "French", href: "/language-selection?lang=french", icon: Globe },
        { name: "German", href: "/language-selection?lang=german", icon: Globe },
        { name: "Portuguese", href: "/language-selection?lang=portuguese", icon: Globe },
        { name: "Dutch", href: "/language-selection?lang=dutch", icon: Globe }
      ]
    },
    {
      title: "Company",
      links: [
        { name: "About Us", href: "/about", icon: Users },
        { name: "Careers", href: "/careers", icon: Award, badge: "We're hiring!" },
        { name: "Press Kit", href: "/press", icon: Star },
        { name: "Blog", href: "/blog", icon: BookOpen },
        { name: "Research", href: "/research", icon: Zap }
      ]
    },
    {
      title: "Legal",
      links: [
        { name: "Privacy Policy", href: "/privacy", icon: Shield },
        { name: "Terms of Service", href: "/terms", icon: BookOpen },
        { name: "Cookie Policy", href: "/cookies", icon: Globe },
        { name: "GDPR Compliance", href: "/gdpr", icon: Shield }
      ]
    },
    {
      title: "Support",
      links: [
        { name: "Help Center", href: "/help", icon: MessageSquare },
        { name: "Community", href: "/community", icon: Users },
        { name: "API Documentation", href: "/docs/api", icon: BookOpen },
        { name: "System Status", href: "/status", icon: Shield }
      ]
    }
  ];

  const socialLinks = [
    { name: "Twitter", href: "https://twitter.com/languagetutor", icon: Twitter },
    { name: "LinkedIn", href: "https://linkedin.com/company/languagetutor", icon: Linkedin },
    { name: "GitHub", href: "https://github.com/languagetutor", icon: Github },
    { name: "YouTube", href: "https://youtube.com/@languagetutor", icon: Youtube }
  ];

  const legalLinks = [
    { name: "Privacy Policy", href: "/privacy" },
    { name: "Terms of Service", href: "/terms" },
    { name: "Cookie Policy", href: "/cookies" },
    { name: "GDPR Compliance", href: "/gdpr" }
  ];

  const stats = [
    { label: "Active Learners", value: "50K+", icon: Users },
    { label: "Languages Supported", value: "6", icon: Globe },
    { label: "Conversations Daily", value: "10K+", icon: MessageSquare },
    { label: "Success Rate", value: "94%", icon: Award }
  ];

  return (
    <footer className="relative bg-gradient-to-br from-[#4ECFBF] via-[#3a9e92] to-[#2d7a6e] text-white overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-transparent"></div>
        <svg className="absolute inset-0 w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="footer-pattern" x="0" y="0" width="60" height="60" patternUnits="userSpaceOnUse">
              <circle cx="30" cy="30" r="1.5" fill="currentColor" opacity="0.2"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#footer-pattern)"/>
        </svg>
      </div>

      {/* Main Footer Content */}
      <div className="relative max-w-7xl mx-auto px-6 py-16">
        <div className="grid grid-cols-1 lg:grid-cols-6 gap-12">
          {/* Company Info */}
          <motion.div
            className="lg:col-span-2"
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <div className="flex items-center mb-6">
              <div className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center mr-4 border border-white/30">
                <MessageSquare className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-bold">Language Tutor</h3>
                <p className="text-white/90 text-sm font-medium">Your Smart Language Coach</p>
              </div>
            </div>
            
            <p className="text-white/70 mb-6 leading-relaxed">
              Revolutionizing language learning through AI-powered conversations, personalized feedback, 
              and adaptive learning experiences. Master any language with confidence.
            </p>

            {/* Contact Info */}
            <div className="space-y-3 mb-8">
              <div className="flex items-center text-white/70 hover:text-white transition-colors">
                <Mail className="w-5 h-5 mr-3 text-white/90" />
                <a href="mailto:support@languagetutor.ai" className="hover:underline">
                  support@languagetutor.ai
                </a>
              </div>
              <div className="flex items-center text-white/70 hover:text-white transition-colors">
                <Phone className="w-5 h-5 mr-3 text-white/90" />
                <a href="tel:+1-555-0123" className="hover:underline">
                  +1 (555) 012-3456
                </a>
              </div>
              <div className="flex items-center text-white/70">
                <MapPin className="w-5 h-5 mr-3 text-white/90" />
                <span>San Francisco, CA</span>
              </div>
            </div>

            {/* Social Links */}
            <div className="flex space-x-4">
              {socialLinks.map((social) => (
                <motion.a
                  key={social.name}
                  href={social.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-10 h-10 bg-white/10 hover:bg-[#4ECFBF] rounded-lg flex items-center justify-center transition-all duration-300 group"
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <social.icon className="w-5 h-5 text-white/70 group-hover:text-white transition-colors" />
                </motion.a>
              ))}
            </div>
          </motion.div>

          {/* Footer Links */}
          {footerSections.map((section, sectionIndex) => (
            <motion.div
              key={section.title}
              className="lg:col-span-1"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: sectionIndex * 0.1 }}
              viewport={{ once: true }}
            >
              <h4 className="text-lg font-semibold mb-6 text-white">
                {section.title}
              </h4>
              <ul className="space-y-3">
                {section.links.map((link) => (
                  <li key={link.name}>
                    <a
                      href={link.href}
                      className="group flex items-center text-white/70 hover:text-[#4ECFBF] transition-all duration-300"
                    >
                      <link.icon className="w-4 h-4 mr-3 opacity-60 group-hover:opacity-100 transition-opacity" />
                      <span className="group-hover:translate-x-1 transition-transform duration-300">
                        {link.name}
                      </span>
                      {link.badge && (
                        <span className="ml-2 px-2 py-0.5 bg-[#4ECFBF] text-white text-xs rounded-full font-medium">
                          {link.badge}
                        </span>
                      )}
                      <ChevronRight className="w-3 h-3 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                    </a>
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>

        {/* Newsletter Signup */}
        <motion.div
          className="mt-16 p-8 bg-white rounded-2xl border border-gray-200 shadow-lg"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          viewport={{ once: true }}
        >
          <div className="max-w-2xl mx-auto text-center">
            <h4 className="text-xl font-bold mb-3 text-gray-800">Stay Updated</h4>
            <p className="text-gray-600 mb-6">
              Get the latest language learning tips, feature updates, and exclusive content delivered to your inbox.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
              <input
                type="email"
                placeholder="Enter your email"
                className="flex-1 px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent"
              />
              <button className="px-6 py-3 bg-white border-2 border-[#4ECFBF] hover:bg-[#4ECFBF] text-[#4ECFBF] hover:text-white font-medium rounded-lg transition-all duration-300 flex items-center justify-center">
                Subscribe
                <ChevronRight className="w-4 h-4 ml-2" />
              </button>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Bottom Bar */}
      <div className="relative border-t border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            {/* Copyright */}
            <motion.div
              className="flex items-center text-white/70"
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              <span>© {currentYear} Language Tutor. Made with</span>
              <Heart className="w-4 h-4 mx-2 text-red-400 fill-current" />
              <span>for language learners worldwide.</span>
            </motion.div>

            {/* Legal Links */}
            <motion.div
              className="flex flex-wrap items-center gap-6"
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              viewport={{ once: true }}
            >
              {legalLinks.map((link, index) => (
                <a
                  key={link.name}
                  href={link.href}
                  className="text-white/70 hover:text-[#4ECFBF] transition-colors duration-300 text-sm"
                >
                  {link.name}
                </a>
              ))}
            </motion.div>

            {/* Security Badge */}
            <motion.div
              className="flex items-center text-white/70"
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              viewport={{ once: true }}
            >
              <Shield className="w-4 h-4 mr-2 text-[#4ECFBF]" />
              <span className="text-sm">SOC 2 Compliant</span>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Floating Action Button - Only visible when footer is in view */}
      <AnimatePresence>
        {showScrollButton && (
          <motion.button
            className="fixed bottom-8 right-8 w-14 h-14 bg-gradient-to-br from-[#4ECFBF] to-[#3a9e92] rounded-full shadow-lg flex items-center justify-center text-white hover:scale-110 transition-transform duration-300 z-50"
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0 }}
            transition={{ duration: 0.3 }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          >
            <ChevronRight className="w-6 h-6 rotate-[-90deg]" />
          </motion.button>
        )}
      </AnimatePresence>
    </footer>
  );
};

export default Footer;
