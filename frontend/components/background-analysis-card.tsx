'use client';

import { useState } from 'react';
import { BackgroundAnalysisResponse, getScoreColorClass, getScoreBackgroundClass, formatAnalysisTimestamp } from '@/lib/background-sentence-api';

interface BackgroundAnalysisCardProps {
  analysis: BackgroundAnalysisResponse;
  onClose?: () => void;
}

export default function BackgroundAnalysisCard({ analysis, onClose }: BackgroundAnalysisCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-lg p-4 mb-3 shadow-sm animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <h3 className="text-sm font-semibold text-blue-700">Sentence Analysis</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-blue-600">
            {formatAnalysisTimestamp(analysis.timestamp)}
          </span>
          {onClose && (
            <button
              onClick={onClose}
              className="text-blue-400 hover:text-blue-600 transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Analyzed Text */}
      <div className="mb-3">
        <p className="text-sm text-gray-700 bg-white/70 p-2 rounded border border-blue-100">
          "{analysis.recognized_text}"
        </p>
      </div>

      {/* Quick Scores */}
      <div className="grid grid-cols-4 gap-2 mb-3">
        {[
          { label: "Grammar", score: analysis.grammatical_score },
          { label: "Vocabulary", score: analysis.vocabulary_score },
          { label: "Complexity", score: analysis.complexity_score },
          { label: "Overall", score: analysis.overall_score },
        ].map((item, i) => (
          <div key={i} className="bg-white/70 border border-blue-100 p-2 rounded text-center">
            <div className="text-xs text-gray-600 font-medium">{item.label}</div>
            <div className={`text-lg font-bold ${getScoreColorClass(item.score)}`}>
              {Math.round(item.score)}
            </div>
          </div>
        ))}
      </div>

      {/* Expand/Collapse Button */}
      <div className="flex justify-center">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1 transition-colors"
        >
          {isExpanded ? 'Show Less' : 'Show Details'}
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className={`h-3 w-3 transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="mt-3 pt-3 border-t border-blue-200 space-y-3 animate-fadeIn">
          {/* Grammar Issues */}
          {analysis.grammar_issues.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 mb-2">Grammar Issues</h4>
              <div className="space-y-2">
                {analysis.grammar_issues.map((issue, i) => (
                  <div key={i} className="bg-white/70 p-2 rounded border border-orange-200 border-l-4 border-l-orange-400">
                    <div className="flex justify-between items-start">
                      <span className="text-xs font-medium text-gray-800">{issue.issue_type}</span>
                      <span className={`text-xs font-medium ${
                        issue.severity === 'minor' ? 'text-green-600' : 
                        issue.severity === 'moderate' ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        {issue.severity}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 mt-1">{issue.description}</p>
                    <p className="text-xs text-blue-600 font-medium mt-1">💡 {issue.suggestion}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Corrected Text */}
          {analysis.corrected_text && analysis.corrected_text !== analysis.recognized_text && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 mb-2">Corrected Version</h4>
              <p className="text-xs text-gray-700 bg-green-50 p-2 rounded border border-green-200 border-l-4 border-l-green-400">
                {analysis.corrected_text}
              </p>
            </div>
          )}

          {/* Improvement Suggestions */}
          {analysis.improvement_suggestions.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 mb-2">Improvement Tips</h4>
              <div className="bg-white/70 p-2 rounded border border-blue-100">
                <ul className="list-disc pl-4 space-y-1">
                  {analysis.improvement_suggestions.slice(0, 3).map((suggestion, i) => (
                    <li key={i} className="text-xs text-gray-700">{suggestion}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Alternative Expressions */}
          {analysis.level_appropriate_alternatives && analysis.level_appropriate_alternatives.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 mb-2">Alternative Ways to Say This</h4>
              <div className="space-y-1">
                {analysis.level_appropriate_alternatives.slice(0, 2).map((alt, i) => (
                  <div key={i} className="bg-purple-50 p-2 rounded border border-purple-200 text-xs text-gray-700">
                    {alt}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
