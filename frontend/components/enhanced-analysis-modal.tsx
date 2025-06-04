'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  TrendingUp, Target, Lightbulb, CheckCircle, AlertCircle,
  Brain, MessageSquare, Clock, Star, ChevronRight,
  BarChart3, Zap, Trophy, ArrowUp, ArrowDown, Minus
} from 'lucide-react';

interface EnhancedAnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  analysis: any;
  sessionInfo: {
    language: string;
    level: string;
    topic?: string;
    duration_minutes: number;
    message_count: number;
    created_at: string;
  };
  conversationMessages?: any[];
}

export default function EnhancedAnalysisModal({
  isOpen,
  onClose,
  analysis,
  sessionInfo
}: EnhancedAnalysisModalProps) {
  const [activeTab, setActiveTab] = useState('conversation');

  if (!analysis) return null;

  // Safe value extraction function
  const safeGetValue = (obj: any, fallback: any = 0) => {
    if (obj === null || obj === undefined) return fallback;
    if (typeof obj === 'object' && obj.score !== undefined) return obj.score;
    if (typeof obj === 'object' && obj.value !== undefined) return obj.value;
    if (typeof obj === 'string' || typeof obj === 'number') return obj;
    return fallback;
  };

  // Safe array extraction function
  const safeGetArray = (obj: any, fallback: any[] = []) => {
    if (Array.isArray(obj)) return obj;
    if (obj === null || obj === undefined) return fallback;
    return fallback;
  };

  // Safe string extraction function
  const safeGetString = (obj: any, fallback: string = '') => {
    if (typeof obj === 'string') return obj;
    if (typeof obj === 'number') return obj.toString();
    if (obj === null || obj === undefined) return fallback;
    if (typeof obj === 'object' && obj.value !== undefined) return String(obj.value);
    return fallback;
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-blue-600 bg-blue-100';
    if (score >= 40) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getProgressColor = (score: number) => {
    if (score >= 80) return '#10B981';
    if (score >= 60) return '#3B82F6';
    if (score >= 40) return '#F59E0B';
    return '#EF4444';
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return <ArrowUp className="h-4 w-4 text-green-500" />;
      case 'declining':
        return <ArrowDown className="h-4 w-4 text-red-500" />;
      default:
        return <Minus className="h-4 w-4 text-gray-500" />;
    }
  };

  // Extract safe values - handle nested objects correctly based on backend structure
  const engagementScore = safeGetValue(analysis.conversation_quality?.engagement?.score || analysis.conversation_quality?.engagement_score, 0);
  const topicDepthScore = safeGetValue(analysis.conversation_quality?.topic_depth?.score || analysis.conversation_quality?.topic_depth_score, 0);
  const confidenceLevel = safeGetString(analysis.ai_insights?.confidence_level, 'Medium');
  const complexityGrowth = safeGetString(analysis.learning_progress?.complexity_growth?.trend || analysis.learning_progress?.complexity_growth, 'Stable');
  
  // Extract detailed metrics from engagement object
  const engagementDetails = analysis.conversation_quality?.engagement?.details || {};
  const wordCount = safeGetValue(engagementDetails.total_user_messages || analysis.conversation_quality?.word_count, sessionInfo.message_count);
  const questionsAsked = safeGetValue(engagementDetails.questions_asked || analysis.conversation_quality?.questions_asked, 0);
  const elaborationRate = safeGetValue(engagementDetails.elaboration_rate || analysis.conversation_quality?.elaboration_rate, 0);
  
  // Extract topic depth details
  const topicDepthDetails = analysis.conversation_quality?.topic_depth?.details || {};
  const keywordsUsed = safeGetArray(topicDepthDetails.keywords_found || analysis.conversation_quality?.keywords_used, []);
  
  // Extract AI insights
  const breakthroughMoments = safeGetArray(analysis.ai_insights?.breakthrough_moments, []);
  const strugglePoints = safeGetArray(analysis.ai_insights?.struggle_points, []);
  
  // Extract learning progress
  const improvementIndicators = safeGetArray(analysis.learning_progress?.improvement_indicators, []);
  const complexityAnalysis = safeGetString(
    analysis.learning_progress?.complexity_growth?.feedback || 
    analysis.learning_progress?.complexity_analysis, 
    'Your language complexity is developing steadily.'
  );
  
  // Extract recommendations
  const immediateActions = safeGetArray(analysis.recommendations?.immediate_actions, []);
  const weeklyFocus = safeGetArray(analysis.recommendations?.weekly_focus, []);
  const longTermGoals = safeGetArray(analysis.recommendations?.long_term_goals, []);

  const tabs = [
    { id: 'conversation', label: 'Conversation', icon: MessageSquare },
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'quality', label: 'Quality Metrics', icon: Target },
    { id: 'progress', label: 'Progress', icon: TrendingUp },
    { id: 'insights', label: 'AI Insights', icon: Brain },
    { id: 'recommendations', label: 'Recommendations', icon: Lightbulb }
  ];

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl h-[85vh] p-0 flex flex-col">
        <DialogHeader className="p-6 pb-0">
          <DialogTitle className="text-2xl font-bold flex items-center">
            <Brain className="h-6 w-6 mr-2 text-purple-600" />
            Enhanced Analysis
          </DialogTitle>
          <div className="flex items-center space-x-4 text-sm text-gray-600 mt-2">
            <span className="capitalize">{sessionInfo.language} - {sessionInfo.level}</span>
            {sessionInfo.topic && <span>• Topic: {sessionInfo.topic}</span>}
            <span>• {Math.round(sessionInfo.duration_minutes)} min</span>
            <span>• {sessionInfo.message_count} messages</span>
            <span>• {new Date(sessionInfo.created_at).toLocaleDateString()}</span>
          </div>
        </DialogHeader>

        <div className="flex border-b">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-purple-500 text-purple-600 bg-purple-50'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <tab.icon className="h-4 w-4 mr-2" />
              {tab.label}
            </button>
          ))}
        </div>

        <ScrollArea className="flex-1 p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Key Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4 text-center">
                  <MessageSquare className="h-8 w-8 mx-auto mb-2 text-blue-600" />
                  <div className="text-2xl font-bold text-blue-700">{engagementScore}</div>
                  <div className="text-sm text-blue-600">Engagement</div>
                </div>
                <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-4 text-center">
                  <Target className="h-8 w-8 mx-auto mb-2 text-green-600" />
                  <div className="text-2xl font-bold text-green-700">{topicDepthScore}</div>
                  <div className="text-sm text-green-600">Topic Depth</div>
                </div>
                <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-4 text-center">
                  <Brain className="h-8 w-8 mx-auto mb-2 text-purple-600" />
                  <div className="text-2xl font-bold text-purple-700">{confidenceLevel}</div>
                  <div className="text-sm text-purple-600">Confidence</div>
                </div>
                <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl p-4 text-center">
                  <TrendingUp className="h-8 w-8 mx-auto mb-2 text-orange-600" />
                  <div className="text-2xl font-bold text-orange-700">{complexityGrowth}</div>
                  <div className="text-sm text-orange-600">Growth</div>
                </div>
              </div>

              {/* Quick Insights */}
              <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                  <Zap className="h-5 w-5 mr-2 text-purple-600" />
                  Key Insights
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {breakthroughMoments.slice(0, 2).map((moment: string, index: number) => (
                    <div key={index} className="bg-white rounded-lg p-4 border border-green-200">
                      <div className="flex items-start">
                        <CheckCircle className="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                        <div>
                          <div className="font-medium text-green-800 text-sm">Breakthrough Moment</div>
                          <div className="text-gray-700 text-sm mt-1">{String(moment)}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                  {strugglePoints.slice(0, 2).map((struggle: string, index: number) => (
                    <div key={index} className="bg-white rounded-lg p-4 border border-orange-200">
                      <div className="flex items-start">
                        <AlertCircle className="h-5 w-5 text-orange-500 mr-3 mt-0.5 flex-shrink-0" />
                        <div>
                          <div className="font-medium text-orange-800 text-sm">Area to Focus</div>
                          <div className="text-gray-700 text-sm mt-1">{String(struggle)}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Quality Metrics Tab */}
          {activeTab === 'quality' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Engagement Metrics */}
                <div className="bg-white border rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                    <MessageSquare className="h-5 w-5 mr-2 text-blue-600" />
                    Engagement Analysis
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-gray-700">Overall Engagement</span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getScoreColor(engagementScore)}`}>
                          {engagementScore}/100
                        </span>
                      </div>
                      <Progress 
                        value={engagementScore} 
                        className="h-2"
                        style={{ 
                          backgroundColor: '#E5E7EB',
                          color: getProgressColor(engagementScore)
                        }}
                      />
                    </div>
                    <div className="text-sm text-gray-600">
                      <strong>Word Count:</strong> {wordCount} words
                    </div>
                    <div className="text-sm text-gray-600">
                      <strong>Questions Asked:</strong> {questionsAsked}
                    </div>
                    <div className="text-sm text-gray-600">
                      <strong>Elaboration Rate:</strong> {elaborationRate}%
                    </div>
                  </div>
                </div>

                {/* Topic Depth */}
                <div className="bg-white border rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                    <Target className="h-5 w-5 mr-2 text-green-600" />
                    Topic Depth
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-gray-700">Depth Score</span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getScoreColor(topicDepthScore)}`}>
                          {topicDepthScore}/100
                        </span>
                      </div>
                      <Progress 
                        value={topicDepthScore} 
                        className="h-2"
                        style={{ 
                          backgroundColor: '#E5E7EB',
                          color: getProgressColor(topicDepthScore)
                        }}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="text-sm font-medium text-gray-700">Key Topics Covered:</div>
                      <div className="flex flex-wrap gap-2">
                        {keywordsUsed.slice(0, 6).map((keyword: string, index: number) => (
                          <Badge key={index} variant="secondary" className="text-xs">
                            {String(keyword)}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Progress Tab */}
          {activeTab === 'progress' && (
            <div className="space-y-6">
              <div className="bg-white border rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                  <TrendingUp className="h-5 w-5 mr-2 text-purple-600" />
                  Learning Progress Indicators
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium text-gray-700 mb-3">Complexity Growth</h4>
                    <div className="flex items-center space-x-2 mb-2">
                      {getTrendIcon(complexityGrowth)}
                      <span className="text-sm font-medium capitalize">{complexityGrowth}</span>
                    </div>
                    <p className="text-sm text-gray-600">{complexityAnalysis}</p>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-700 mb-3">Improvement Indicators</h4>
                    <div className="space-y-2">
                      {improvementIndicators.map((indicator: string, index: number) => (
                        <div key={index} className="flex items-start space-x-2">
                          <Star className="h-4 w-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                          <span className="text-sm text-gray-700">{String(indicator)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* AI Insights Tab */}
          {activeTab === 'insights' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 gap-6">
                {/* Breakthrough Moments */}
                <div className="bg-green-50 border border-green-200 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-green-800 mb-4 flex items-center">
                    <CheckCircle className="h-5 w-5 mr-2" />
                    Breakthrough Moments
                  </h3>
                  <div className="space-y-3">
                    {breakthroughMoments.map((moment: string, index: number) => (
                      <div key={index} className="bg-white rounded-lg p-4 border border-green-200">
                        <p className="text-sm text-gray-700">{String(moment)}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Struggle Points */}
                <div className="bg-orange-50 border border-orange-200 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-orange-800 mb-4 flex items-center">
                    <AlertCircle className="h-5 w-5 mr-2" />
                    Areas for Focus
                  </h3>
                  <div className="space-y-3">
                    {strugglePoints.map((struggle: string, index: number) => (
                      <div key={index} className="bg-white rounded-lg p-4 border border-orange-200">
                        <p className="text-sm text-gray-700">{String(struggle)}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Confidence Level */}
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-blue-800 mb-4 flex items-center">
                    <Brain className="h-5 w-5 mr-2" />
                    Confidence Assessment
                  </h3>
                  <div className="flex items-center space-x-4">
                    <div className="text-3xl font-bold text-blue-700">{confidenceLevel}</div>
                    <div className="text-sm text-blue-600">
                      Based on speech patterns, hesitation, and response fluency
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Recommendations Tab */}
          {activeTab === 'recommendations' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 gap-6">
                {/* Immediate Actions */}
                <div className="bg-purple-50 border border-purple-200 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-purple-800 mb-4 flex items-center">
                    <Zap className="h-5 w-5 mr-2" />
                    For Your Next Session
                  </h3>
                  <div className="space-y-3">
                    {immediateActions.map((action: string, index: number) => (
                      <div key={index} className="bg-white rounded-lg p-4 border border-purple-200 flex items-start space-x-3">
                        <ChevronRight className="h-5 w-5 text-purple-600 mt-0.5 flex-shrink-0" />
                        <p className="text-sm text-gray-700">{String(action)}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Weekly Focus */}
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-blue-800 mb-4 flex items-center">
                    <Clock className="h-5 w-5 mr-2" />
                    This Week's Focus
                  </h3>
                  <div className="space-y-3">
                    {weeklyFocus.map((focus: string, index: number) => (
                      <div key={index} className="bg-white rounded-lg p-4 border border-blue-200 flex items-start space-x-3">
                        <Target className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                        <p className="text-sm text-gray-700">{String(focus)}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Long-term Goals */}
                <div className="bg-green-50 border border-green-200 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-green-800 mb-4 flex items-center">
                    <Trophy className="h-5 w-5 mr-2" />
                    Long-term Goals
                  </h3>
                  <div className="space-y-3">
                    {longTermGoals.map((goal: string, index: number) => (
                      <div key={index} className="bg-white rounded-lg p-4 border border-green-200 flex items-start space-x-3">
                        <Star className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                        <p className="text-sm text-gray-700">{String(goal)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Conversation Tab */}
          {activeTab === 'conversation' && (
            <div className="space-y-6">
              <div className="bg-white border rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                  <MessageSquare className="h-5 w-5 mr-2 text-blue-600" />
                  Full Conversation Transcript
                </h3>
                <div className="space-y-4">
                  {analysis.conversation_messages && analysis.conversation_messages.length > 0 ? (
                    analysis.conversation_messages.map((message: any, index: number) => (
                      <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] rounded-lg p-4 ${
                          message.role === 'user' 
                            ? 'bg-blue-500 text-white' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-medium opacity-75">
                              {message.role === 'user' ? 'You' : 'AI Tutor'}
                            </span>
                            <span className="text-xs opacity-60">
                              {message.timestamp ? new Date(message.timestamp).toLocaleTimeString() : ''}
                            </span>
                          </div>
                          <p className="text-sm leading-relaxed">{message.content}</p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8">
                      <MessageSquare className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                      <p className="text-gray-500">No conversation transcript available</p>
                      <p className="text-sm text-gray-400 mt-2">
                        The conversation messages may not have been saved with this session.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </ScrollArea>

        <div className="p-6 border-t bg-gray-50">
          <div className="flex justify-end">
            <Button onClick={onClose} className="bg-purple-600 hover:bg-purple-700 text-white">
              Close Analysis
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
