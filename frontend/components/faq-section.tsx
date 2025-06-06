'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Accordion, AccordionItem } from '@/components/ui/accordion';

// Simple, universally recognizable icons for the FAQ accordion
const QuestionIcon = (props: any) => {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      height="24"
      role="presentation"
      viewBox="0 0 24 24"
      width="24"
      {...props}
    >
      <defs>
        <linearGradient id="questionGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#4ECFBF" />
          <stop offset="100%" stopColor="#3a9e92" />
        </linearGradient>
      </defs>
      {/* Simple gear/cog for "how it works" */}
      <path
        d="M12 15.5A3.5 3.5 0 0 1 8.5 12A3.5 3.5 0 0 1 12 8.5a3.5 3.5 0 0 1 3.5 3.5a3.5 3.5 0 0 1-3.5 3.5m7.43-2.53c.04-.32.07-.64.07-.97c0-.33-.03-.66-.07-1l2.11-1.63c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.39-.31-.61-.22l-2.49 1c-.52-.39-1.06-.73-1.69-.98l-.37-2.65A.506.506 0 0 0 14 2h-4c-.25 0-.46.18-.5.42l-.37 2.65c-.63.25-1.17.59-1.69.98l-2.49-1c-.22-.09-.49 0-.61.22l-2 3.46c-.13.22-.07.49.12.64L4.57 11c-.04.34-.07.67-.07 1c0 .33.03.65.07.97l-2.11 1.66c-.19.15-.25.42-.12.64l2 3.46c.12.22.39.3.61.22l2.49-1.01c.52.4 1.06.74 1.69.99l.37 2.65c.04.24.25.42.5.42h4c.25 0 .46-.18.5-.42l.37-2.65c.63-.26 1.17-.59 1.69-.99l2.49 1.01c.22.08.49 0 .61-.22l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.66Z"
        fill="url(#questionGradient)"
      />
    </svg>
  );
};

const SpeakingIcon = (props: any) => {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      height="24"
      role="presentation"
      viewBox="0 0 24 24"
      width="24"
      {...props}
    >
      <defs>
        <linearGradient id="speakingGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#4ECFBF" />
          <stop offset="100%" stopColor="#3a9e92" />
        </linearGradient>
      </defs>
      {/* Classic microphone icon */}
      <path
        d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"
        fill="url(#speakingGradient)"
      />
      <path
        d="M19 10v1a7 7 0 0 1-14 0v-1h2v1a5 5 0 0 0 10 0v-1h2z"
        fill="url(#speakingGradient)"
      />
      <rect x="11" y="18" width="2" height="4" fill="url(#speakingGradient)" />
      <rect x="8" y="22" width="8" height="1" fill="url(#speakingGradient)" />
    </svg>
  );
};

const PricingIcon = (props: any) => {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      height="24"
      role="presentation"
      viewBox="0 0 24 24"
      width="24"
      {...props}
    >
      <defs>
        <linearGradient id="pricingGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#4ECFBF" />
          <stop offset="100%" stopColor="#3a9e92" />
        </linearGradient>
      </defs>
      {/* Clean dollar sign */}
      <path
        d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm0-4h-2c0-3.25 2.75-3 2.75-5 0-.83-.67-1.5-1.5-1.5S10.75 7.17 10.75 8H9.25c0-1.93 1.57-3.5 3.5-3.5S16.25 6.07 16.25 8c0 2.5-2.75 2.75-2.75 5z"
        fill="url(#pricingGradient)"
        transform="scale(0.8) translate(3, 3)"
      />
      <text
        x="12"
        y="16"
        textAnchor="middle"
        fontSize="14"
        fontWeight="bold"
        fill="url(#pricingGradient)"
      >
        $
      </text>
    </svg>
  );
};

const PrivacyIcon = (props: any) => {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      height="24"
      role="presentation"
      viewBox="0 0 24 24"
      width="24"
      {...props}
    >
      <defs>
        <linearGradient id="privacyGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#4ECFBF" />
          <stop offset="100%" stopColor="#3a9e92" />
        </linearGradient>
      </defs>
      {/* Simple shield icon */}
      <path
        d="M12 2l8 3v6c0 5.55-3.84 10.74-9 12-5.16-1.26-9-6.45-9-12V5l8-3z"
        fill="url(#privacyGradient)"
      />
      <path
        d="M9 12l2 2 4-4"
        stroke="white"
        strokeWidth="2"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

const FAQSection: React.FC = () => {
  return (
    <div className="w-full max-w-3xl mx-auto mt-12 faq-section">
      <motion.h3 
        className="text-2xl font-bold text-gray-800 mb-6 text-center"
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        viewport={{ once: true }}
      >
        Frequently Asked Questions
      </motion.h3>
      
      <motion.div
        className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border-2 border-[#4ECFBF]/30 shadow-lg"
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        viewport={{ once: true }}
      >
        <Accordion>
          <AccordionItem 
            key="how-it-works" 
            aria-label="How does Your Smart Language Coach work?" 
            indicator={<QuestionIcon />} 
            title="How does Your Smart Language Coach work?"
          >
            <div className="text-justify leading-relaxed">
              Your Smart Language Coach uses OpenAI's advanced GPT-4o and Whisper models to provide real-time 
              AI conversations and speaking assessments. Simply choose your target language (English, Spanish, 
              French, German, Dutch, or Portuguese), select your proficiency level, pick a conversation topic, 
              and start practicing! Our AI tutor adapts to your level and provides instant feedback on 
              pronunciation, grammar, vocabulary, and fluency to help you improve naturally through conversation.
            </div>
          </AccordionItem>
          
          <AccordionItem 
            key="speaking-practice" 
            aria-label="How does the speaking practice work?" 
            indicator={<SpeakingIcon />} 
            title="How does the speaking practice work?"
          >
            <div className="text-justify leading-relaxed">
              Our speaking practice uses WebRTC technology for real-time voice conversations with your AI tutor. 
              You can take speaking assessments (15 seconds for guests, 60 seconds for registered users) to get 
              your CEFR level (A1-C2) with detailed feedback. For conversation practice, guests get 1-minute 
              sessions while registered users enjoy 5-minute conversations. The AI provides immediate responses 
              and corrections, making it feel like talking to a real language teacher.
            </div>
          </AccordionItem>
          
          <AccordionItem 
            key="pricing" 
            aria-label="What are the pricing options?" 
            indicator={<PricingIcon />} 
            title="What are the pricing options?"
          >
            <div className="text-justify leading-relaxed">
              Your Smart Language Coach is completely free! Guest users can try speaking assessments and 
              short conversations with limited time. By creating a free account, you unlock longer assessment 
              times (60 seconds vs 15 seconds), extended conversation sessions (5 minutes vs 1 minute), 
              unlimited practice sessions, progress tracking, conversation history, and achievement badges. 
              No premium subscription required - just sign up for free to access all features!
            </div>
          </AccordionItem>
          
          <AccordionItem 
            key="privacy" 
            aria-label="How is my data handled?" 
            indicator={<PrivacyIcon />} 
            title="How is my data handled?"
          >
            <div className="text-justify leading-relaxed">
              Your privacy is our priority. We use secure JWT authentication and encrypt all data in transit. 
              Conversation transcripts are processed using OpenAI's API and stored securely in our MongoDB 
              database for registered users to track their progress. Guest data is automatically cleaned up 
              after 7 days. Voice recordings are processed in real-time for speech recognition and are not 
              permanently stored. You can delete your account and all associated data anytime from your profile.
            </div>
          </AccordionItem>
        </Accordion>
      </motion.div>
    </div>
  );
};

export default FAQSection;
