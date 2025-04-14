'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Accordion, AccordionItem } from '@/components/ui/accordion';

// Custom icons for the FAQ accordion
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
      <path
        d="M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10zm0-2a8 8 0 1 0 0-16 8 8 0 0 0 0 16zm-1-5h2v2h-2v-2zm2-1.645V14h-2v-1.5a1 1 0 0 1 1-1 1.5 1.5 0 1 0-1.471-1.794l-1.962-.393A3.5 3.5 0 1 1 13 13.355z"
        fill="currentColor"
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
      <path
        d="M12 1a5 5 0 0 1 5 5v6a5 5 0 0 1-10 0V6a5 5 0 0 1 5-5zm0 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3zm7 9h-2a7.01 7.01 0 0 1-5 6.72V21h-2v-2.28A7.01 7.01 0 0 1 5 12H3v-2h16v2z"
        fill="currentColor"
      />
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
      <path
        d="M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10zm0-2a8 8 0 1 0 0-16 8 8 0 0 0 0 16zm-3.5-6H14a.5.5 0 1 0 0-1h-4a2.5 2.5 0 1 1 0-5h1V6h2v2h2.5v2H10a.5.5 0 1 0 0 1h4a2.5 2.5 0 1 1 0 5h-1v2h-2v-2H8.5v-2z"
        fill="currentColor"
      />
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
      <path
        d="M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10zm-4.987-3.744A7.966 7.966 0 0 0 12 20c1.97 0 3.773-.712 5.167-1.892A6.979 6.979 0 0 0 12.16 16a6.981 6.981 0 0 0-5.147 2.256zM5.616 16.82A8.975 8.975 0 0 1 12.16 14a8.972 8.972 0 0 1 6.362 2.634 8 8 0 1 0-12.906.187zM12 13a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm0-2a2 2 0 1 0 0-4 2 2 0 0 0 0 4z"
        fill="currentColor"
      />
    </svg>
  );
};

const FAQSection: React.FC = () => {
  return (
    <div className="w-full max-w-3xl mx-auto mt-12 faq-section">
      <motion.h3 
        className="text-2xl font-bold text-white mb-6 text-center"
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        viewport={{ once: true }}
      >
        Frequently Asked Questions
      </motion.h3>
      
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        viewport={{ once: true }}
      >
        <Accordion>
          <AccordionItem 
            key="how-it-works" 
            aria-label="How does Language Tutor work?" 
            indicator={<QuestionIcon />} 
            title="How does Language Tutor work?"
          >
            Language Tutor uses advanced AI to create personalized language learning experiences. 
            Our system adapts to your learning style, proficiency level, and interests to provide 
            customized lessons and conversation practice. The AI tutor provides real-time feedback 
            on pronunciation, grammar, and vocabulary, helping you improve faster than traditional 
            methods.
          </AccordionItem>
          
          <AccordionItem 
            key="speaking-practice" 
            aria-label="How does the speaking practice work?" 
            indicator={<SpeakingIcon />} 
            title="How does the speaking practice work?"
          >
            Our speaking practice feature uses speech recognition technology to analyze your 
            pronunciation and fluency. You'll engage in natural conversations with our AI tutor, 
            which responds to your speech in real-time. The system provides immediate feedback on 
            your pronunciation, suggests corrections, and adapts the difficulty based on your 
            performance, creating a supportive environment for improving your speaking skills.
          </AccordionItem>
          
          <AccordionItem 
            key="pricing" 
            aria-label="What are the pricing options?" 
            indicator={<PricingIcon />} 
            title="What are the pricing options?"
          >
            Language Tutor offers a free tier that gives you access to basic features and limited 
            lessons. Our premium subscription unlocks unlimited lessons, advanced speaking practice, 
            personalized learning paths, and detailed progress tracking. We also offer special rates 
            for students and educational institutions. Check our pricing page for the most current 
            information on our plans and features.
          </AccordionItem>
          
          <AccordionItem 
            key="privacy" 
            aria-label="How is my data handled?" 
            indicator={<PrivacyIcon />} 
            title="How is my data handled?"
          >
            We take your privacy seriously. Your personal information and learning data are 
            encrypted and stored securely. We use your data only to improve your learning 
            experience and never share it with third parties without your explicit consent. 
            Voice recordings for speaking practice are processed in real-time and are not 
            permanently stored unless you choose to save them for your own review. You can 
            request deletion of your data at any time through your account settings.
          </AccordionItem>
        </Accordion>
      </motion.div>
    </div>
  );
};

export default FAQSection;
