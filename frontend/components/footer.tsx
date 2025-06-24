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
import { Logo } from './logo';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [email, setEmail] = useState('');
  const [isSubscribing, setIsSubscribing] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [subscriptionMessage, setSubscriptionMessage] = useState('');

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

  // Handle newsletter subscription
  const handleSubscribe = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email.trim()) {
      setSubscriptionMessage('Please enter your email address');
      return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setSubscriptionMessage('Please enter a valid email address');
      return;
    }

    setIsSubscribing(true);
    
    try {
      // Get the API URL based on environment
      const apiUrl = process.env.NODE_ENV === 'production' 
        ? 'https://taco.up.railway.app' 
        : 'http://localhost:8000';
      
      console.log('🔄 Newsletter subscription attempt:', {
        email: email.trim(),
        apiUrl,
        timestamp: new Date().toISOString()
      });
      
      const response = await fetch(`${apiUrl}/api/subscribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: email.trim() }),
      });

      console.log('📡 API Response:', {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok
      });

      const data = await response.json();
      console.log('📊 Response data:', data);

      if (response.ok && data.success) {
        if (data.already_subscribed) {
          setSubscriptionMessage('You are already subscribed to our newsletter!');
        } else {
          setSubscriptionMessage('Successfully subscribed! Thank you for joining our newsletter.');
        }
        setEmail(''); // Clear the email input
        setShowSuccessModal(true);
        
        // Auto-hide modal after 5 seconds
        setTimeout(() => {
          setShowSuccessModal(false);
        }, 5000);
      } else {
        setSubscriptionMessage(data.detail || 'Failed to subscribe. Please try again.');
      }
    } catch (error) {
      console.error('Subscription error:', error);
      setSubscriptionMessage('Network error. Please check your connection and try again.');
    } finally {
      setIsSubscribing(false);
    }
  };

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
          <div className="lg:col-span-2">
            <div className="mb-6">
              <Logo variant="full" className="scale-75 origin-left" />
              <p className="text-white/90 text-sm font-medium mt-2">AI Language Coach</p>
            </div>
            
            <p className="text-white/70 mb-6 leading-relaxed">
              Revolutionizing language learning through AI-powered conversations, personalized feedback, 
              and adaptive learning experiences. Master any language with confidence.
            </p>

            {/* Contact Info */}
            <div className="space-y-3 mb-8">
              <div className="flex items-center text-white/70 hover:text-white transition-colors">
                <Mail className="w-5 h-5 mr-3 text-white/90" />
                <a href="mailto:hello@mytacoai.com" className="hover:underline">
                  hello@mytacoai.com
                </a>
              </div>
              <div className="flex items-center text-white/70 hover:text-white transition-colors">
                <Phone className="w-5 h-5 mr-3 text-white/90" />
                <a href="tel:+31657126162" className="hover:underline">
                  +31(6)57 126 162
                </a>
              </div>
              <div className="flex items-center text-white/70">
                <MapPin className="w-5 h-5 mr-3 text-white/90" />
                <span>Amsterdam, NL</span>
              </div>
            </div>

            {/* Social Links */}
            <div className="flex space-x-4">
              {socialLinks.map((social) => (
                <a
                  key={social.name}
                  href={social.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-10 h-10 bg-white/10 hover:bg-[#4ECFBF] rounded-lg flex items-center justify-center transition-all duration-300 group hover:scale-110 active:scale-95"
                >
                  <social.icon className="w-5 h-5 text-white/70 group-hover:text-white transition-colors" />
                </a>
              ))}
            </div>
          </div>

          {/* Footer Links */}
          {footerSections.map((section, sectionIndex) => (
            <div
              key={section.title}
              className="lg:col-span-1"
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
                      <ChevronRight className="w-3 h-3 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Newsletter Signup */}
        <div className="mt-16 p-8 bg-white rounded-2xl border border-gray-200 shadow-lg">
          <div className="max-w-2xl mx-auto text-center">
            <h4 className="text-xl font-bold mb-3 text-gray-800">Stay Updated</h4>
            <p className="text-gray-600 mb-6">
              Get the latest language learning tips, feature updates, and exclusive content delivered to your inbox.
            </p>
            <form onSubmit={handleSubscribe} className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
              <input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isSubscribing}
                className="flex-1 px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
                required
              />
              <button 
                type="submit"
                disabled={isSubscribing}
                className="px-6 py-3 bg-white border-2 border-[#4ECFBF] hover:bg-[#4ECFBF] text-[#4ECFBF] hover:text-white font-medium rounded-lg transition-all duration-300 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubscribing ? (
                  <>
                    <div className="animate-spin h-4 w-4 border-2 border-[#4ECFBF] border-t-transparent rounded-full mr-2"></div>
                    Subscribing...
                  </>
                ) : (
                  <>
                    Subscribe
                    <ChevronRight className="w-4 h-4 ml-2" />
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="relative border-t border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            {/* Copyright */}
            <div className="flex items-center text-white/70">
              <span>© {currentYear} My TaCo. Made with</span>
              <Heart className="w-4 h-4 mx-2 text-red-400 fill-current" />
              <span>for language learners worldwide.</span>
            </div>

            {/* Legal Links */}
            <div className="flex flex-wrap items-center gap-6">
              {legalLinks.map((link, index) => (
                <a
                  key={link.name}
                  href={link.href}
                  className="text-white/70 hover:text-[#4ECFBF] transition-colors duration-300 text-sm"
                >
                  {link.name}
                </a>
              ))}
            </div>

            {/* Security Badge */}
            <div className="flex items-center text-white/70">
              <Shield className="w-4 h-4 mr-2 text-[#4ECFBF]" />
              <span className="text-sm">SOC 2 Compliant</span>
            </div>
          </div>
        </div>
      </div>

      {/* Floating Action Button - Only visible when footer is in view */}
      <AnimatePresence>
        {showScrollButton && (
          <button
            className="fixed bottom-8 right-8 w-14 h-14 bg-gradient-to-br from-[#4ECFBF] to-[#3a9e92] rounded-full shadow-lg flex items-center justify-center text-white hover:scale-110 active:scale-95 transition-transform duration-300 z-50"
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          >
            <ChevronRight className="w-6 h-6 rotate-[-90deg]" />
          </button>
        )}
      </AnimatePresence>

      {/* Success Modal */}
      <AnimatePresence>
        {showSuccessModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-[100] p-4"
            onClick={() => setShowSuccessModal(false)}
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ type: "spring", duration: 0.5 }}
              className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="text-center">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-gray-800 mb-2">Success!</h3>
                <p className="text-gray-600 mb-6">{subscriptionMessage}</p>
                <button
                  onClick={() => setShowSuccessModal(false)}
                  className="px-6 py-3 bg-[#4ECFBF] text-white font-medium rounded-lg hover:bg-[#3a9e92] transition-colors duration-300"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </footer>
  );
};

export default Footer;
