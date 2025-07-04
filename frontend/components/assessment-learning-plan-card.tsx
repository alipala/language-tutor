import React, { useState } from 'react';
import { formatDate } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useRouter } from 'next/navigation';
import ShareProgressModal from './share-progress-modal';
import { 
  ChevronDown, 
  ChevronRight, 
  Award, 
  Target, 
  BookOpen, 
  TrendingUp,
  CheckCircle,
  Star,
  Calendar,
  Clock,
  Share2,
  Heart,
  GraduationCap,
  Timer,
  BarChart3,
  Download,
  Instagram,
  MessageCircle,
  Copy,
  X,
  Loader2
} from 'lucide-react';

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

interface LearningPlan {
  id: string;
  user_id?: string;
  language: string;
  proficiency_level: string;
  goals: string[];
  duration_months: number;
  custom_goal?: string;
  plan_content: {
    overview: string;
    weekly_schedule: {
      week: number;
      focus: string;
      activities: string[];
      resources?: string[];
      sessions_completed?: number;
      total_sessions?: number;
    }[];
    resources?: any;
    milestones?: any[];
    title?: string;
    assessment_summary?: {
      overall_score: number;
      recommended_level: string;
      strengths: string[];
      areas_for_improvement: string[];
      skill_scores: {
        pronunciation: number;
        grammar: number;
        vocabulary: number;
        fluency: number;
        coherence: number;
      };
    };
  };
  assessment_data?: AssessmentData;
  created_at: string;
  total_sessions?: number;
  completed_sessions?: number;
  progress_percentage?: number;
}

interface AssessmentLearningPlanCardProps {
  assessment: AssessmentData;
  learningPlan?: LearningPlan | null;
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

const getSkillColor = (score: number) => {
  if (score >= 85) return 'bg-green-400';
  if (score >= 70) return 'bg-blue-400';
  if (score >= 55) return 'bg-yellow-400';
  return 'bg-red-400';
};

const getProgressBarColor = (progress: number) => {
  if (progress >= 80) return '#FFD63A';
  if (progress >= 60) return '#FFA955';
  return '#F75A5A';
};

export const AssessmentLearningPlanCard: React.FC<AssessmentLearningPlanCardProps> = ({ 
  assessment, 
  learningPlan,
  isExpanded, 
  onToggle,
  index
}) => {
  const router = useRouter();
  const [showPlanDetails, setShowPlanDetails] = useState(false);
  const [currentWeekPage, setCurrentWeekPage] = useState(0);
  const [showShareModal, setShowShareModal] = useState(false);
  
  const formattedDate = assessment.date ? formatDate(new Date(assessment.date)) : 'N/A';
  const planDate = learningPlan?.created_at ? formatDate(new Date(learningPlan.created_at)) : null;
  
  return (
    <div className="mb-6 bg-white rounded-2xl shadow-lg overflow-hidden border-2" style={{ borderColor: '#4ECFBF' }}>
      {/* Header - Always visible */}
      <div 
        className="p-6 relative overflow-hidden cursor-pointer"
        style={{ backgroundColor: 'white' }}
        onClick={onToggle}
      >
        <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
        <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/10 rounded-full -ml-12 -mb-12"></div>
        
        <div className="relative z-10">
          <div className="flex justify-between items-start mb-4">
            <div className="flex items-center">
              <div className={`transition-transform mr-3 ${isExpanded ? 'rotate-90' : ''}`}>
                <ChevronRight className="h-5 w-5" style={{ color: '#4ECFBF' }} />
              </div>
              <div>
                <h2 className="text-xl font-bold flex items-center text-gray-800">
                  <Award className="h-5 w-5 mr-2" style={{ color: '#4ECFBF' }} />
                  Your Personalized Learning Plan #{index + 1}
                  {index === 0 && (
                    <span className="ml-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white text-xs px-3 py-1 rounded-full font-medium shadow-sm">
                      Most Recent
                    </span>
                  )}
                </h2>
                <p className="text-gray-600 text-sm mt-1 flex items-center">
                  <Calendar className="h-4 w-4 mr-1" style={{ color: '#4ECFBF' }} />
                  {formattedDate} • {assessment.language || 'Language'} - {assessment.recommended_level || assessment.level || "B1"}
                </p>
              </div>
            </div>
            
            <div className="text-right">
              <div className="flex items-center bg-gray-100 rounded-full px-3 py-1.5 mb-2">
                <span className="text-sm font-medium mr-1 text-gray-700">Score:</span>
                <span className="text-lg font-bold text-gray-800">{assessment.overall_score}/100</span>
              </div>
              {learningPlan && (
                <div className="flex items-center text-gray-600 text-xs">
                  <CheckCircle className="h-3 w-3 mr-1" style={{ color: '#4ECFBF' }} />
                  Learning Plan Created
                </div>
              )}
            </div>
          </div>
          
          {/* Quick Stats Row */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
            {/* Language */}
            <div 
              className="bg-white rounded-lg p-3 text-center shadow-md border-2 transition-all duration-300 hover:shadow-lg hover:-translate-y-1 cursor-pointer group" 
              style={{ borderColor: '#4ECFBF' }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = '#5CCFC0';
                e.currentTarget.style.backgroundColor = '#F0FDFA';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '#4ECFBF';
                e.currentTarget.style.backgroundColor = 'white';
              }}
            >
              <Heart className="h-4 w-4 mx-auto mb-1 transition-colors duration-300" style={{ color: '#4ECFBF' }} />
              <div className="text-sm font-bold text-gray-800">{assessment.language ? assessment.language.charAt(0).toUpperCase() + assessment.language.slice(1) : 'Language'}</div>
              <div className="text-gray-600 text-xs">Language</div>
            </div>
            
            {/* CEFR Level */}
            <div 
              className="bg-white rounded-lg p-3 text-center shadow-md border-2 transition-all duration-300 hover:shadow-lg hover:-translate-y-1 cursor-pointer group" 
              style={{ borderColor: '#FFD63A' }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = '#ECC235';
                e.currentTarget.style.backgroundColor = '#FFFBEB';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '#FFD63A';
                e.currentTarget.style.backgroundColor = 'white';
              }}
            >
              <GraduationCap className="h-4 w-4 mx-auto mb-1 transition-colors duration-300" style={{ color: '#FFD63A' }} />
              <div className="text-sm font-bold text-gray-800">{assessment.recommended_level || "B1"}</div>
              <div className="text-gray-600 text-xs">CEFR Level</div>
            </div>
            
            {/* Learning Goals */}
            {learningPlan && (
              <div 
                className="bg-white rounded-lg p-2 text-center shadow-md border-2 transition-all duration-300 hover:shadow-lg hover:-translate-y-1 cursor-pointer group" 
                style={{ borderColor: '#3B82F6' }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = '#2563EB';
                  e.currentTarget.style.backgroundColor = '#EFF6FF';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = '#3B82F6';
                  e.currentTarget.style.backgroundColor = 'white';
                }}
              >
                <Target className="h-4 w-4 mx-auto mb-1 transition-colors duration-300" style={{ color: '#3B82F6' }} />
                <div className="text-xs font-bold text-gray-800 leading-tight">
                  {learningPlan.goals.slice(0, 2).map((goal, index) => (
                    <div key={index} className="truncate">{goal.charAt(0).toUpperCase() + goal.slice(1)}</div>
                  ))}
                  {learningPlan.custom_goal && (
                    <div className="truncate">{learningPlan.custom_goal.charAt(0).toUpperCase() + learningPlan.custom_goal.slice(1)}</div>
                  )}
                  {learningPlan.goals.length > 2 && (
                    <div className="text-gray-500">+{learningPlan.goals.length - 2} more</div>
                  )}
                </div>
                <div className="text-gray-600 text-xs">Goals</div>
              </div>
            )}
            
            {learningPlan && (
              <>
                {/* Plan Duration */}
                <div 
                  className="bg-white rounded-lg p-3 text-center shadow-md border-2 transition-all duration-300 hover:shadow-lg hover:-translate-y-1 cursor-pointer group" 
                  style={{ borderColor: '#FFA955' }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = '#FF9A42';
                    e.currentTarget.style.backgroundColor = '#FFF7ED';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = '#FFA955';
                    e.currentTarget.style.backgroundColor = 'white';
                  }}
                >
                  <Timer className="h-4 w-4 mx-auto mb-1 transition-colors duration-300" style={{ color: '#FFA955' }} />
                  <div className="text-sm font-bold text-gray-800">{learningPlan.duration_months} {learningPlan.duration_months === 1 ? 'Month' : 'Months'}</div>
                  <div className="text-gray-600 text-xs">Plan Duration</div>
                </div>
                
                {/* Progress */}
                <div 
                  className="bg-white rounded-lg p-3 text-center shadow-md border-2 transition-all duration-300 hover:shadow-lg hover:-translate-y-1 cursor-pointer group" 
                  style={{ borderColor: '#F75A5A' }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = '#E55252';
                    e.currentTarget.style.backgroundColor = '#FEF2F2';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = '#F75A5A';
                    e.currentTarget.style.backgroundColor = 'white';
                  }}
                >
                  <BarChart3 className="h-4 w-4 mx-auto mb-1 transition-colors duration-300" style={{ color: '#F75A5A' }} />
                  <div className="text-sm font-bold text-gray-800">{Math.round(learningPlan.progress_percentage || 0)}%</div>
                  <div className="text-gray-600 text-xs">Progress</div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
      
      {/* Expanded Content */}
      {isExpanded && (
        <div className="p-6">
          {/* Assessment Results Section */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
              <Award className="h-5 w-5 mr-2" style={{ color: '#4ECFBF' }} />
              Assessment Results
            </h3>
            
            {/* Overall Score and Confidence */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-xl">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="text-base font-semibold text-gray-700 flex items-center">
                    <TrendingUp className="h-4 w-4 mr-1.5 text-blue-500" />
                    Overall Score
                  </h4>
                  <span className="text-2xl font-bold text-blue-600">
                    {assessment.overall_score}/100
                  </span>
                </div>
                <Progress value={assessment.overall_score} className="mb-2" />
                <div className="text-sm text-gray-600">
                  {assessment.overall_score >= 80 ? "Excellent" : 
                   assessment.overall_score >= 70 ? "Very Good" :
                   assessment.overall_score >= 60 ? "Good" :
                   assessment.overall_score >= 50 ? "Fair" : "Needs Improvement"}
                </div>
              </div>
              
              <div className="bg-green-50 p-4 rounded-xl">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="text-base font-semibold text-gray-700 flex items-center">
                    <CheckCircle className="h-4 w-4 mr-1.5 text-green-500" />
                    Confidence
                  </h4>
                  <span className="text-2xl font-bold text-green-600">
                    {assessment.confidence}%
                  </span>
                </div>
                <Progress value={assessment.confidence} className="mb-2" />
                <div className="text-sm text-gray-600">
                  {assessment.confidence >= 80 ? "Very Confident" : 
                   assessment.confidence >= 60 ? "Confident" :
                   assessment.confidence >= 40 ? "Moderately Confident" : "Needs Confidence Building"}
                </div>
              </div>
            </div>
            
            {/* Skill Breakdown */}
            <div className="mb-6">
              <h4 className="font-semibold text-gray-800 mb-3">Skill Breakdown</h4>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                {['pronunciation', 'grammar', 'vocabulary', 'fluency', 'coherence'].map((skill) => {
                  const skillData = assessment ? 
                    (assessment as any)[skill] : { score: 0, feedback: '' };
                  
                  return (
                    <div key={skill} className="bg-gray-50 border rounded-lg p-3">
                      <div className="flex justify-between items-center mb-1">
                        <div className="text-sm font-medium capitalize text-gray-700">{skill}</div>
                        <div className="text-lg font-bold text-blue-600">
                          {skillData.score}
                        </div>
                      </div>
                      <Progress value={skillData.score} className="mb-2" />
                      <div className="text-xs text-gray-600 line-clamp-2" title={skillData.feedback}>
                        {skillData.feedback}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            
            {/* Strengths and Areas for Improvement */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-green-50 p-4 rounded-xl">
                <h4 className="font-semibold text-green-700 mb-3 flex items-center">
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Strengths
                </h4>
                <ul className="space-y-2">
                  {assessment.strengths?.map((strength: string, index: number) => (
                    <li key={index} className="flex items-start">
                      <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-green-100 text-green-700 text-xs mr-2 mt-0.5 flex-shrink-0">
                        {index + 1}
                      </span>
                      <span className="text-sm text-gray-700">{strength}</span>
                    </li>
                  ))}
                </ul>
              </div>
              
              <div className="bg-orange-50 p-4 rounded-xl">
                <h4 className="font-semibold text-orange-700 mb-3 flex items-center">
                  <Target className="h-4 w-4 mr-2" />
                  Areas to Improve
                </h4>
                <ul className="space-y-2">
                  {assessment.areas_for_improvement?.map((area: string, index: number) => (
                    <li key={index} className="flex items-start">
                      <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-orange-100 text-orange-700 text-xs mr-2 mt-0.5 flex-shrink-0">
                        {index + 1}
                      </span>
                      <span className="text-sm text-gray-700">{area}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
          
          {/* Learning Plan Section */}
          {learningPlan ? (
            <div className="border-t pt-6">
              

              {/* Progress Tracking Section - Modern Card Design */}
              <div className="mb-6">
                <h4 className="font-semibold text-gray-800 mb-6 flex items-center">
                  <BarChart3 className="h-5 w-5 mr-2" style={{ color: '#4ECFBF' }} />
                  Learning Progress
                </h4>
                
                {/* Modern Session Progress Card */}
                <div className="relative overflow-hidden bg-white rounded-2xl shadow-lg border border-gray-100 mb-6">
                  {/* Animated Background Gradient */}
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 opacity-60"></div>
                  <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-blue-200/30 to-transparent rounded-full -mr-16 -mt-16"></div>
                  <div className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-tr from-indigo-200/30 to-transparent rounded-full -ml-12 -mb-12"></div>
                  
                  <div className="relative z-10 p-6">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex items-center">
                        <div className="relative">
                          <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                            <CheckCircle className="h-6 w-6 text-white" />
                          </div>
                          <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white"></div>
                        </div>
                        <div className="ml-4">
                          <h5 className="text-lg font-bold text-gray-800">Session Progress</h5>
                          <p className="text-sm text-gray-600">
                            {learningPlan.completed_sessions || 0} of {learningPlan.total_sessions || 0} sessions completed
                          </p>
                        </div>
                      </div>
                      
                      {/* Circular Progress Indicator */}
                      <div className="relative w-16 h-16">
                        <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 64 64">
                          <circle
                            cx="32"
                            cy="32"
                            r="28"
                            stroke="currentColor"
                            strokeWidth="4"
                            fill="none"
                            className="text-gray-200"
                          />
                          <circle
                            cx="32"
                            cy="32"
                            r="28"
                            stroke="currentColor"
                            strokeWidth="4"
                            fill="none"
                            strokeDasharray={`${2 * Math.PI * 28}`}
                            strokeDashoffset={`${2 * Math.PI * 28 * (1 - (learningPlan.progress_percentage || 0) / 100)}`}
                            className="text-blue-500 transition-all duration-1000 ease-out"
                            strokeLinecap="round"
                          />
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="text-sm font-bold text-gray-800">
                            {Math.round(learningPlan.progress_percentage || 0)}%
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    {/* Modern Progress Bar with Sliding Animation */}
                    <div className="mb-6">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-gray-700">Overall Progress</span>
                        <span className="text-sm text-gray-500">{Math.round(learningPlan.progress_percentage || 0)}% Complete</span>
                      </div>
                      <div className="relative h-3 bg-gray-200 rounded-full overflow-hidden">
                        {/* Background shimmer effect */}
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse"></div>
                        {/* Progress fill with sliding animation */}
                        <div 
                          className="h-full bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 rounded-full transition-all duration-1000 ease-out relative overflow-hidden"
                          style={{ width: `${Math.min(learningPlan.progress_percentage || 0, 100)}%` }}
                        >
                          {/* Sliding highlight effect */}
                          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-pulse"></div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Stats Cards with Hover Effects */}
                    <div className="grid grid-cols-3 gap-4">
                      <div className="group bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-gray-100 hover:shadow-md transition-all duration-300 hover:-translate-y-1">
                        <div className="text-center">
                          <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-2 group-hover:bg-green-200 transition-colors">
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          </div>
                          <div className="text-xl font-bold text-green-600">
                            {learningPlan.completed_sessions || 0}
                          </div>
                          <div className="text-xs text-gray-600 font-medium">Completed</div>
                        </div>
                      </div>
                      
                      <div className="group bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-gray-100 hover:shadow-md transition-all duration-300 hover:-translate-y-1">
                        <div className="text-center">
                          <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center mx-auto mb-2 group-hover:bg-orange-200 transition-colors">
                            <Clock className="h-4 w-4 text-orange-600" />
                          </div>
                          <div className="text-xl font-bold text-orange-600">
                            {(learningPlan.total_sessions || 0) - (learningPlan.completed_sessions || 0)}
                          </div>
                          <div className="text-xs text-gray-600 font-medium">Remaining</div>
                        </div>
                      </div>
                      
                      <div className="group bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-gray-100 hover:shadow-md transition-all duration-300 hover:-translate-y-1">
                        <div className="text-center">
                          <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-2 group-hover:bg-blue-200 transition-colors">
                            <Target className="h-4 w-4 text-blue-600" />
                          </div>
                          <div className="text-xl font-bold text-blue-600">
                            {learningPlan.total_sessions || 0}
                          </div>
                          <div className="text-xs text-gray-600 font-medium">Total</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Weekly Schedule Progress - Modern Card */}
                {learningPlan.plan_content.weekly_schedule && learningPlan.plan_content.weekly_schedule.length > 0 && (
                  <div className="relative overflow-hidden bg-white rounded-2xl shadow-lg border border-gray-100">
                    {/* Animated Background */}
                    <div className="absolute inset-0 bg-gradient-to-br from-amber-50 via-orange-50 to-red-50 opacity-60"></div>
                    <div className="absolute top-0 left-0 w-28 h-28 bg-gradient-to-br from-amber-200/30 to-transparent rounded-full -ml-14 -mt-14"></div>
                    <div className="absolute bottom-0 right-0 w-20 h-20 bg-gradient-to-tl from-orange-200/30 to-transparent rounded-full -mr-10 -mb-10"></div>
                    
                    <div className="relative z-10 p-6">
                      <div className="flex items-center mb-6">
                        <div className="w-12 h-12 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl flex items-center justify-center shadow-lg">
                          <Calendar className="h-6 w-6 text-white" />
                        </div>
                        <div className="ml-4">
                          <h5 className="text-lg font-bold text-gray-800">Weekly Schedule</h5>
                          <p className="text-sm text-gray-600">Track your weekly learning journey</p>
                        </div>
                      </div>
                      
                      {/* Calculate weeks progress based on sessions */}
                      {(() => {
                        const totalWeeks = learningPlan.duration_months * 4; // 4 weeks per month
                        const sessionsPerWeek = 2; // Assuming 2 sessions per week
                        
                        // Calculate progress based on individual week completion
                        const weeklySchedule = learningPlan.plan_content.weekly_schedule || [];
                        let completedWeeks = 0;
                        let currentWeek = 1;
                        
                        // Find the current week (next week after last completed week)
                        for (let i = 0; i < weeklySchedule.length; i++) {
                          const week = weeklySchedule[i];
                          const weekSessionsCompleted = week.sessions_completed || 0;
                          const weekTotalSessions = week.total_sessions || sessionsPerWeek;
                          
                          if (weekSessionsCompleted >= weekTotalSessions) {
                            completedWeeks++;
                            // Current week is the next week after this completed one
                            currentWeek = week.week + 1;
                          } else {
                            // If this week has some sessions but not completed, it's current
                            // If this week has no sessions, it's still current (next to work on)
                            currentWeek = week.week;
                            break;
                          }
                        }
                        
                        // Ensure currentWeek doesn't exceed available weeks
                        if (currentWeek > weeklySchedule.length) {
                          currentWeek = weeklySchedule.length;
                        }
                        
                        const weekProgress = (completedWeeks / totalWeeks) * 100;
                        
                        return (
                          <div className="space-y-4">
                            {/* Week Progress Header */}
                            <div className="flex justify-between items-center">
                              <div className="flex items-center space-x-3">
                                <div className="bg-white/80 backdrop-blur-sm rounded-lg px-3 py-1 border border-amber-200">
                                  <span className="text-sm font-medium text-amber-800">
                                    Week {currentWeek} of {totalWeeks}
                                  </span>
                                </div>
                                <div className="text-sm text-gray-600">
                                  {Math.round(weekProgress)}% weeks completed
                                </div>
                              </div>
                            </div>
                            
                            {/* Modern Week Progress Bar */}
                            <div className="relative">
                              <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
                                <div 
                                  className="h-full bg-gradient-to-r from-amber-500 via-orange-500 to-red-500 rounded-full transition-all duration-1000 ease-out relative"
                                  style={{ width: `${Math.min(weekProgress, 100)}%` }}
                                >
                                  {/* Sliding shine effect */}
                                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent animate-pulse"></div>
                                </div>
                              </div>
                              {/* Progress markers */}
                              <div className="absolute top-0 left-0 w-full h-full flex justify-between items-center px-1">
                                {Array.from({ length: Math.min(totalWeeks, 12) }, (_, i) => (
                                  <div 
                                    key={i}
                                    className={`w-1 h-6 rounded-full ${
                                      i < completedWeeks ? 'bg-white/80' : 'bg-gray-300/50'
                                    }`}
                                  />
                                ))}
                              </div>
                            </div>
                            
                            {/* Current Week Focus Card */}
                            {learningPlan.plan_content.weekly_schedule[Math.min(currentWeek - 1, learningPlan.plan_content.weekly_schedule.length - 1)] && (
                              <div className="bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-amber-200 hover:shadow-md transition-all duration-300">
                                <div className="flex items-start space-x-3">
                                  <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center flex-shrink-0">
                                    <Star className="h-4 w-4 text-amber-600" />
                                  </div>
                                  <div>
                                    <h6 className="font-semibold text-gray-800 text-sm mb-1">
                                      Current Focus (Week {currentWeek})
                                    </h6>
                                    <p className="text-sm text-gray-600 leading-relaxed">
                                      {learningPlan.plan_content.weekly_schedule[Math.min(currentWeek - 1, learningPlan.plan_content.weekly_schedule.length - 1)].focus}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })()}
                    </div>
                  </div>
                )}
              </div>
              
              {/* Detailed Plan View - Always Visible */}
              <div className="space-y-4 mt-6 pt-4 border-t border-gray-200">
                  {/* Weekly Schedule Preview with Slider for All Weeks */}
                  {(() => {
                    // Use only the personalized weekly schedule from the learning plan
                    // Don't generate generic weeks - show only what was created based on assessment
                    const allWeeks = learningPlan.plan_content.weekly_schedule || [];
                    
                    // Find the current week and most recently completed week
                    const sessionsPerWeek = 2;
                    let currentWeekNumber = 1;
                    let lastCompletedWeekNumber = 0;
                    
                    // Find current week based on individual week completion status
                    for (let i = 0; i < allWeeks.length; i++) {
                      const week = allWeeks[i];
                      const weekSessionsCompleted = week.sessions_completed || 0;
                      const weekTotalSessions = week.total_sessions || sessionsPerWeek;
                      
                      if (weekSessionsCompleted >= weekTotalSessions) {
                        lastCompletedWeekNumber = week.week;
                        currentWeekNumber = week.week + 1; // Next week after completed
                      } else {
                        // This is the current week (either in progress or upcoming)
                        currentWeekNumber = week.week;
                        break;
                      }
                    }
                    
                    // Ensure currentWeek doesn't exceed available weeks
                    if (currentWeekNumber > allWeeks.length) {
                      currentWeekNumber = allWeeks.length;
                    }
                    
                    const weeksPerPage = 2;
                    const totalPages = Math.ceil(allWeeks.length / weeksPerPage);
                    
                    // Show most recently completed week + current week
                    let weeksToShow = [];
                    if (lastCompletedWeekNumber > 0) {
                      // Show last completed week + current week
                      weeksToShow = allWeeks.filter(week => 
                        week.week === lastCompletedWeekNumber || week.week === currentWeekNumber
                      );
                    } else {
                      // No completed weeks yet, show first two weeks
                      weeksToShow = allWeeks.slice(0, 2);
                    }
                    
                    // If user is navigating manually, use pagination
                    let currentWeeks;
                    if (currentWeekPage > 0) {
                      const startIndex = currentWeekPage * weeksPerPage;
                      const endIndex = startIndex + weeksPerPage;
                      currentWeeks = allWeeks.slice(startIndex, endIndex);
                    } else {
                      // Default view: show relevant weeks
                      currentWeeks = weeksToShow;
                    }
                    
                    return allWeeks.length > 0 && (
                      <div>
                        <div className="flex items-center justify-between mb-4">
                          <h5 className="font-semibold text-gray-800">Weekly Schedule Preview</h5>
                          <div className="flex items-center space-x-2">
                            <span className="text-sm text-gray-500">
                              Showing weeks {currentWeekPage * weeksPerPage + 1}-{Math.min((currentWeekPage + 1) * weeksPerPage, allWeeks.length)} of {allWeeks.length}
                            </span>
                            {/* Navigation buttons - Made more visible */}
                            <div className="flex items-center space-x-2">
                              <button
                                onClick={() => setCurrentWeekPage(Math.max(0, currentWeekPage - 1))}
                                disabled={currentWeekPage === 0}
                                className="p-2 rounded-lg bg-white border border-gray-200 hover:bg-gray-50 hover:border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition-all duration-200"
                                title="Previous weeks"
                              >
                                <ChevronRight className="h-4 w-4 rotate-180 text-gray-600" />
                              </button>
                              <span className="text-sm text-gray-600 px-3 py-1 bg-white rounded-md border border-gray-200 font-medium min-w-[50px] text-center">
                                {currentWeekPage + 1}/{totalPages}
                              </span>
                              <button
                                onClick={() => setCurrentWeekPage(Math.min(totalPages - 1, currentWeekPage + 1))}
                                disabled={currentWeekPage >= totalPages - 1}
                                className="p-2 rounded-lg bg-white border border-gray-200 hover:bg-gray-50 hover:border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition-all duration-200"
                                title="Next weeks"
                              >
                                <ChevronRight className="h-4 w-4 text-gray-600" />
                              </button>
                            </div>
                          </div>
                        </div>
                        
                        {/* Week Cards Display */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                          {currentWeeks.map((week, weekIndex) => {
                            // Use individual week's sessions_completed to determine status
                            const weekSessionsCompleted = week.sessions_completed || 0;
                            const weekTotalSessions = week.total_sessions || 2;
                            
                            const isCompleted = weekSessionsCompleted >= weekTotalSessions;
                            
                            // Determine if this is the current week (next week to work on)
                            let isCurrentWeek = false;
                            
                            // Find the current week by checking if this is the next week after the last completed week
                            if (weekSessionsCompleted > 0 && weekSessionsCompleted < weekTotalSessions) {
                              // Week is in progress
                              isCurrentWeek = true;
                            } else if (weekSessionsCompleted === 0) {
                              // Check if this is the next week after the last completed week
                              const previousWeek = allWeeks.find(w => w.week === week.week - 1);
                              if (!previousWeek) {
                                // This is week 1 and no previous week exists
                                isCurrentWeek = true;
                              } else {
                                // Check if previous week is completed
                                const prevWeekCompleted = (previousWeek.sessions_completed || 0) >= (previousWeek.total_sessions || 2);
                                if (prevWeekCompleted) {
                                  isCurrentWeek = true;
                                }
                              }
                            }
                            
                            return (
                              <div 
                                key={week.week} 
                                className={`relative rounded-xl p-5 border-2 transition-all duration-300 hover:shadow-lg ${
                                  isCurrentWeek 
                                    ? 'border-blue-300 bg-blue-50 shadow-md' 
                                    : isCompleted 
                                      ? 'border-green-200 bg-green-50' 
                                      : 'border-gray-200 bg-gray-50 hover:border-gray-300'
                                }`}
                              >
                                {/* Week Status Badge */}
                                <div className="absolute top-3 right-3">
                                  {isCompleted ? (
                                    <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                                      <CheckCircle className="h-4 w-4 text-white" />
                                    </div>
                                  ) : isCurrentWeek ? (
                                    <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                                      <Clock className="h-4 w-4 text-white" />
                                    </div>
                                  ) : (
                                    <div className="w-6 h-6 bg-gray-300 rounded-full flex items-center justify-center">
                                      <span className="text-xs font-bold text-gray-600">{week.week}</span>
                                    </div>
                                  )}
                                </div>
                                
                                {/* Week Header */}
                                <div className="mb-4 pr-8">
                                  <h6 className={`font-bold text-lg mb-1 ${
                                    isCurrentWeek ? 'text-blue-800' : 
                                    isCompleted ? 'text-green-800' : 'text-gray-800'
                                  }`}>
                                    Week {week.week}
                                  </h6>
                                  <p className={`text-sm font-medium ${
                                    isCurrentWeek ? 'text-blue-700' : 
                                    isCompleted ? 'text-green-700' : 'text-gray-600'
                                  }`}>
                                    {week.focus}
                                  </p>
                                </div>
                                
                                {/* Week Activities */}
                                <div className="space-y-2">
                                  <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                                    Activities
                                  </div>
                                  <ul className="space-y-2">
                                    {week.activities.slice(0, 3).map((activity: string, actIndex: number) => (
                                      <li key={actIndex} className="flex items-start text-sm">
                                        <div className={`w-1.5 h-1.5 rounded-full mt-2 mr-3 flex-shrink-0 ${
                                          isCurrentWeek ? 'bg-blue-500' : 
                                          isCompleted ? 'bg-green-500' : 'bg-gray-400'
                                        }`}></div>
                                        <span className={`leading-relaxed ${
                                          isCurrentWeek ? 'text-blue-800' : 
                                          isCompleted ? 'text-green-800' : 'text-gray-700'
                                        }`}>
                                          {activity}
                                        </span>
                                      </li>
                                    ))}
                                    {week.activities.length > 3 && (
                                      <li className="text-xs text-gray-500 ml-5">
                                        +{week.activities.length - 3} more activities
                                      </li>
                                    )}
                                  </ul>
                                </div>
                                
                                {/* Progress Indicator for Current Week */}
                                {isCurrentWeek && (
                                  <div className="mt-4 pt-3 border-t border-blue-200">
                                    <div className="flex items-center justify-between text-xs text-blue-700 mb-1">
                                      <span>Week Progress</span>
                                      <span>{Math.floor(((learningPlan?.completed_sessions || 0) % 2) / 2 * 100)}% Complete</span>
                                    </div>
                                    <div className="w-full bg-blue-200 rounded-full h-1.5">
                                      <div 
                                        className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                                        style={{ width: `${Math.floor(((learningPlan?.completed_sessions || 0) % 2) / 2 * 100)}%` }}
                                      ></div>
                                    </div>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                        
                        {/* Circle Navigation Dots */}
                        {totalPages > 1 && (
                          <div className="flex justify-center space-x-2 mt-4">
                            {Array.from({ length: totalPages }, (_, i) => (
                              <button
                                key={i}
                                onClick={() => setCurrentWeekPage(i)}
                                className={`w-2 h-2 rounded-full transition-all duration-300 ${
                                  i === currentWeekPage 
                                    ? 'bg-blue-500 w-6' 
                                    : 'bg-gray-300 hover:bg-gray-400'
                                }`}
                                title={`Go to weeks ${i * weeksPerPage + 1}-${Math.min((i + 1) * weeksPerPage, allWeeks.length)}`}
                              />
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })()}
                  
                  {/* Resources */}
                  {learningPlan.plan_content.resources && (
                    <div>
                      <h5 className="font-semibold text-gray-800 mb-3">Recommended Resources</h5>
                      <div className="bg-blue-50 rounded-lg p-4">
                        <ul className="text-sm text-gray-700 space-y-1">
                          {Array.isArray(learningPlan.plan_content.resources) ? 
                            learningPlan.plan_content.resources.map((resource, index) => (
                              <li key={index} className="flex items-start">
                                <Star className="h-3 w-3 mt-1 mr-2 text-blue-500 flex-shrink-0" />
                                {resource}
                              </li>
                            )) :
                            Object.entries(learningPlan.plan_content.resources).map(([category, items]) => (
                              <li key={category} className="mb-2">
                                <span className="font-medium capitalize">{category}:</span>
                                <ul className="ml-4 mt-1">
                                  {Array.isArray(items) && items.map((item, index) => (
                                    <li key={index} className="flex items-start">
                                      <span className="inline-block w-1 h-1 rounded-full bg-blue-400 mt-2 mr-2 flex-shrink-0"></span>
                                      {item}
                                    </li>
                                  ))}
                                </ul>
                              </li>
                            ))
                          }
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              
              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3 mt-6">
                <Button 
                  onClick={() => router.push(`/speech?plan=${learningPlan.id}`)}
                  className="flex-1 text-white py-3 px-6 rounded-xl font-medium hover:opacity-90 transition-opacity flex items-center justify-center" 
                  style={{ backgroundColor: '#4ECFBF' }}
                >
                  <BookOpen className="h-5 w-5 mr-2" />
                  Continue Learning
                </Button>
                <Button 
                  onClick={() => setShowShareModal(true)}
                  variant="outline"
                  className="flex-1 border-2 py-3 px-6 rounded-xl font-medium hover:bg-opacity-10 transition-all flex items-center justify-center" 
                  style={{ borderColor: '#4ECFBF', color: '#4ECFBF' }}
                >
                  <Share2 className="h-5 w-5 mr-2" />
                  Share Progress
                </Button>
              </div>
            </div>
          ) : (
            /* No Learning Plan - Show Create Plan Option */
            <div className="border-t pt-6">
              <div className="bg-yellow-50 rounded-xl p-6 text-center">
                <BookOpen className="h-12 w-12 mx-auto mb-4 text-yellow-600" />
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Ready to Start Learning?</h3>
                <p className="text-gray-600 mb-4">
                  Based on your assessment results, we can create a personalized learning plan to help you improve your {assessment.language || 'language'} skills.
                </p>
                <Button 
                  onClick={() => router.push(`/curriculum/create-plan?assessment=${index}`)}
                  className="text-white py-3 px-6 rounded-xl font-medium hover:opacity-90 transition-opacity" 
                  style={{ backgroundColor: '#4ECFBF' }}
                >
                  Create Learning Plan
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Share Progress Modal */}
      <ShareProgressModal
        isOpen={showShareModal}
        onClose={() => setShowShareModal(false)}
        assessmentData={assessment}
        learningPlanData={learningPlan}
        assessmentId={assessment.date} // Using date as ID since we don't have a proper assessment ID
        learningPlanId={learningPlan?.id}
      />
    </div>
  );
};

export default AssessmentLearningPlanCard;
