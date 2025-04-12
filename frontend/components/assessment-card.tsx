import React from 'react';
import { formatDate } from '@/lib/utils';

interface SkillData {
  score: number;
  feedback: string;
  examples?: string[];
}

interface AssessmentData {
  overall_score: number;
  confidence: number;
  pronunciation: SkillData;
  grammar: SkillData;
  vocabulary: SkillData;
  fluency: SkillData;
  coherence: SkillData;
  strengths?: string[];
  areas_for_improvement?: string[];
  next_steps?: string[];
  recommended_level?: string;
  recognized_text?: string;
  date?: string;
  source?: string;
  language?: string;
  level?: string;
}

interface AssessmentCardProps {
  assessment: AssessmentData;
  isExpanded: boolean;
  onToggle: () => void;
  index: number;
}

// Helper function to get color class based on score
const getColorClass = (score: number) => {
  if (score >= 80) return 'bg-green-500';
  if (score >= 70) return 'bg-emerald-500';
  if (score >= 60) return 'bg-blue-500';
  if (score >= 50) return 'bg-yellow-500';
  return 'bg-red-500';
};

export const AssessmentCard: React.FC<AssessmentCardProps> = ({ 
  assessment, 
  isExpanded, 
  onToggle,
  index
}) => {
  const formattedDate = assessment.date ? formatDate(new Date(assessment.date)) : 'N/A';
  
  return (
    <div className="mb-4 bg-white dark:bg-slate-800/90 border border-gray-200 dark:border-gray-700 rounded-xl shadow-md overflow-hidden">
      {/* Header - Always visible */}
      <div 
        className="bg-gradient-to-r from-purple-500 to-indigo-600 dark:from-purple-600 dark:to-indigo-700 p-4 text-white relative overflow-hidden cursor-pointer"
        onClick={onToggle}
      >
        <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
        <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/10 rounded-full -ml-12 -mb-12"></div>
        
        <div className="relative z-10 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold flex items-center">
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                className={`h-5 w-5 mr-2 transition-transform ${isExpanded ? 'rotate-90' : ''}`} 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              Assessment #{index + 1}: {assessment.source || 'Speaking Assessment'}
            </h2>
            <p className="text-white/80 text-sm mt-1">
              {formattedDate} • Overall Score: {assessment.overall_score}/100
            </p>
          </div>
          <div className="flex items-center bg-white/20 rounded-full px-3 py-1.5">
            <span className="text-sm font-medium mr-1">Level:</span>
            <span className="text-sm font-bold bg-white/30 px-2 py-0.5 rounded-full">
              {assessment.recommended_level || assessment.level || "B1"}
            </span>
          </div>
        </div>
      </div>
      
      {/* Expanded Content */}
      {isExpanded && (
        <div className="p-5">
          {/* Overall Score and Confidence */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="bg-indigo-50/50 dark:bg-indigo-900/10 p-4 rounded-xl">
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-base font-semibold text-slate-700 dark:text-slate-300 flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1.5 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  Overall Score
                </h3>
                <span className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
                  {assessment.overall_score}/100
                </span>
              </div>
              <div className="h-3 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden mb-2">
                <div 
                  className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                  style={{ width: `${assessment.overall_score}%` }}
                ></div>
              </div>
              <div className="text-sm text-slate-600 dark:text-slate-400 italic">
                {assessment.overall_score >= 80 ? "Excellent" : 
                 assessment.overall_score >= 70 ? "Very Good" :
                 assessment.overall_score >= 60 ? "Good" :
                 assessment.overall_score >= 50 ? "Fair" : "Needs Improvement"}
              </div>
            </div>
            
            <div className="bg-green-50/50 dark:bg-green-900/10 p-4 rounded-xl">
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-base font-semibold text-slate-700 dark:text-slate-300 flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1.5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Confidence
                </h3>
                <span className="text-3xl font-bold text-green-600 dark:text-green-400">
                  {assessment.confidence}%
                </span>
              </div>
              <div className="h-3 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden mb-2">
                <div 
                  className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full"
                  style={{ width: `${assessment.confidence}%` }}
                ></div>
              </div>
              <div className="text-sm text-slate-600 dark:text-slate-400 italic">
                {assessment.confidence >= 80 ? "Very Confident" : 
                 assessment.confidence >= 60 ? "Confident" :
                 assessment.confidence >= 40 ? "Moderately Confident" : "Needs Confidence Building"}
              </div>
            </div>
          </div>
          
          {/* Skill Breakdown */}
          <div className="mb-6">
            <h3 className="text-base font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1.5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
              </svg>
              Skill Breakdown
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
              {['pronunciation', 'grammar', 'vocabulary', 'fluency', 'coherence'].map((skill) => {
                // Type assertion to access dynamic properties safely
                const skillData = assessment ? 
                  (assessment as any)[skill] : { score: 0, feedback: '' };
                
                return (
                  <div key={skill} className="bg-white dark:bg-slate-800/90 border border-gray-200 dark:border-gray-700 rounded-lg p-3 shadow-sm">
                    <div className="flex justify-between items-center mb-1">
                      <div className="text-sm font-medium capitalize text-slate-700 dark:text-slate-300">{skill}</div>
                      <div className="text-lg font-bold text-blue-600 dark:text-blue-400">
                        {skillData.score}
                      </div>
                    </div>
                    <div className="h-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden mb-2">
                      <div 
                        className={`h-full ${getColorClass(skillData.score)} rounded-full`}
                        style={{ width: `${skillData.score}%` }}
                      ></div>
                    </div>
                    <div className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2 h-8" title={skillData.feedback}>
                      {skillData.feedback}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          
          {/* Strengths and Areas for Improvement */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="bg-green-50/50 dark:bg-green-900/10 p-4 rounded-xl">
              <h3 className="text-base font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1.5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Strengths
              </h3>
              <ul className="space-y-2">
                {assessment.strengths?.map((strength: string, index: number) => (
                  <li key={index} className="flex items-start">
                    <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-xs mr-2 mt-0.5 flex-shrink-0">
                      {index + 1}
                    </span>
                    <span className="text-sm text-slate-700 dark:text-slate-300">{strength}</span>
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="bg-amber-50/50 dark:bg-amber-900/10 p-4 rounded-xl">
              <h3 className="text-base font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1.5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Areas to Improve
              </h3>
              <ul className="space-y-2">
                {assessment.areas_for_improvement?.map((area: string, index: number) => (
                  <li key={index} className="flex items-start">
                    <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 text-xs mr-2 mt-0.5 flex-shrink-0">
                      {index + 1}
                    </span>
                    <span className="text-sm text-slate-700 dark:text-slate-300">{area}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          
          {/* Next Steps */}
          <div className="bg-blue-50/50 dark:bg-blue-900/10 p-4 rounded-xl">
            <h3 className="text-base font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1.5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              </svg>
              Recommended Next Steps
            </h3>
            <ul className="space-y-2">
              {assessment.next_steps?.map((step: string, index: number) => (
                <li key={index} className="flex items-start">
                  <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs mr-2 mt-0.5 flex-shrink-0">
                    {index + 1}
                  </span>
                  <span className="text-sm text-slate-700 dark:text-slate-300">{step}</span>
                </li>
              ))}
            </ul>
          </div>
          
          {/* Recognized Text */}
          {assessment.recognized_text && (
            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              <h3 className="text-base font-semibold text-slate-700 dark:text-slate-300 mb-2 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1.5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
                Your Speech Sample
              </h3>
              <div className="bg-slate-50 dark:bg-slate-800/50 p-3 rounded-lg border border-slate-200 dark:border-slate-700 text-sm text-slate-600 dark:text-slate-400 italic">
                "{assessment.recognized_text}"
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AssessmentCard;
