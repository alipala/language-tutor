'use client';

import dynamic from 'next/dynamic';
import { Suspense } from 'react';

// Dynamically import the chatbot with no SSR to avoid React DOM server issues
const ProjectKnowledgeChatbot = dynamic(
  () => import('./project-knowledge-chatbot'),
  {
    ssr: false,
    loading: () => (
      <div className="fixed bottom-4 right-4 z-50">
        <div className="w-14 h-14 bg-gradient-to-br from-[#4ECFBF] to-[#3a9e92] rounded-full flex items-center justify-center shadow-lg animate-pulse">
          <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
      </div>
    )
  }
);

interface ProjectKnowledgeChatbotWrapperProps {
  className?: string;
}

const ProjectKnowledgeChatbotWrapper: React.FC<ProjectKnowledgeChatbotWrapperProps> = ({ className = '' }) => {
  return (
    <Suspense fallback={
      <div className="fixed bottom-4 right-4 z-50">
        <div className="w-14 h-14 bg-gradient-to-br from-[#4ECFBF] to-[#3a9e92] rounded-full flex items-center justify-center shadow-lg animate-pulse">
          <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
      </div>
    }>
      <div className={className}>
        <ProjectKnowledgeChatbot />
      </div>
    </Suspense>
  );
};

export default ProjectKnowledgeChatbotWrapper;
