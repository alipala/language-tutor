'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Spinner, ModalSpinner, TableLoadingSkeleton, CardLoadingSkeleton } from '@/src/components/ui/Spinner';
import {
  BarChart2, Users, AlertTriangle, TrendingUp, Globe, BookOpen,
  Mic, Zap, Bot, CheckCircle, Clock, Target, Lightbulb,
  Flame, Star, Calendar, GraduationCap, ChevronRight,
  Award, Activity, MessageSquare, Brain, Layout, Dna,
  TrendingDown, Minus, Shield, Heart, Repeat
} from 'lucide-react';
import { FlagIcon, FlagOrText } from '@/src/components/ui/FlagIcon';
import { DateRangePicker, DateRange } from '@/src/components/ui/DateRangePicker';

const API_BASE_URL = '/api';

// ─────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────
interface LearningPlan {
  id: string;
  language: string;
  proficiency_level: string;
  progress_percentage: number;
  progress_status: 'on_track' | 'at_risk' | 'inactive';
  last_activity_date: string | null;
  days_since_activity: number;
  completed_sessions: number;
  total_sessions: number;
  assessment_score: number;
  last_session_summary: string | null;
  next_focus_area: string;
}

interface Learner {
  id: string;
  user_id: string;
  name: string;
  email: string;
  enrolled_at: string;
  consent_given: boolean;
  learning_plans: LearningPlan[];
}

interface Analytics {
  total_assigned_learners: number;
  active_learners: number;
  at_risk_learners: number;
  inactive_learners: number;
  average_progress: number;
  total_sessions_completed: number;
  total_minutes_practiced: number;
  languages_taught: string[];
  level_distribution: Record<string, number>;
  recent_activity: Array<{ learner_id: string; created_at: string; language: string; duration_minutes: number }>;
}

// ─────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────
// Flags rendered via FlagIcon component — no emoji map needed

const LEVEL_COLORS: Record<string, string> = {
  A1: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  A2: 'bg-teal-100 text-teal-700 border-teal-200',
  B1: 'bg-blue-100 text-blue-700 border-blue-200',
  B2: 'bg-indigo-100 text-indigo-700 border-indigo-200',
  C1: 'bg-purple-100 text-purple-700 border-purple-200',
  C2: 'bg-rose-100 text-rose-700 border-rose-200',
};

const LEVEL_BAR_COLORS: Record<string, string> = {
  A1: 'bg-emerald-400', A2: 'bg-teal-400',
  B1: 'bg-blue-400', B2: 'bg-indigo-500',
  C1: 'bg-purple-500', C2: 'bg-rose-500',
};

// ─────────────────────────────────────────────
// Learner Hover Card (snapshot tooltip)
// ─────────────────────────────────────────────
function LearnerHoverCard({ learner, position }: { learner: Learner; position: { x: number; y: number } }) {
  const plan = learner.learning_plans[0];
  if (!plan) return null;

  const statusColor = plan.progress_status === 'on_track' ? 'text-emerald-600 bg-emerald-50'
    : plan.progress_status === 'at_risk' ? 'text-amber-600 bg-amber-50'
    : 'text-gray-500 bg-gray-100';

  const statusLabel = plan.progress_status === 'on_track' ? 'On Track'
    : plan.progress_status === 'at_risk' ? 'At Risk' : 'Inactive';

  // Circular progress ring
  const radius = 20;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(plan.progress_percentage, 100);
  const offset = circumference - (progress / 100) * circumference;

  // Smart vertical offset so card doesn't clip viewport bottom
  const cardH = 220;
  const top = position.y + cardH > window.innerHeight - 20
    ? position.y - cardH - 10
    : position.y + 10;

  return (
    <div
      className="fixed z-50 pointer-events-none"
      style={{ left: position.x + 16, top }}
    >
      <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 w-64 overflow-hidden"
        style={{ animation: 'hoverCardIn 0.15s ease-out' }}>
        {/* Header strip */}
        <div className="bg-gradient-to-r from-[#4ECFBF]/15 to-transparent px-4 pt-4 pb-3 flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-sm flex-shrink-0 ${
            plan.progress_status === 'on_track' ? 'bg-emerald-400' :
            plan.progress_status === 'at_risk' ? 'bg-amber-400' : 'bg-gray-300'
          }`}>
            {learner.name.charAt(0)}
          </div>
          <div className="min-w-0 flex-1">
            <div className="font-bold text-gray-900 text-sm truncate">{learner.name}</div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <FlagOrText language={plan.language} size={13} />
              <span className="text-xs text-gray-500 capitalize">{plan.language}</span>
              <span className={`text-xs px-1.5 py-0.5 rounded-md border font-bold ${LEVEL_COLORS[plan.proficiency_level] || 'bg-gray-100 text-gray-600 border-gray-200'}`}>
                {plan.proficiency_level}
              </span>
            </div>
          </div>
          <span className={`text-xs px-2 py-0.5 rounded-full font-semibold flex-shrink-0 ${statusColor}`}>
            {statusLabel}
          </span>
        </div>

        {/* Progress + stats */}
        <div className="px-4 pb-4 flex items-center gap-4">
          {/* Ring */}
          <div className="relative flex-shrink-0">
            <svg width="52" height="52" className="-rotate-90">
              <circle cx="26" cy="26" r={radius} fill="none" stroke="#f0f0f0" strokeWidth="5" />
              <circle
                cx="26" cy="26" r={radius} fill="none"
                stroke={plan.progress_status === 'on_track' ? '#4ECFBF' : plan.progress_status === 'at_risk' ? '#f59e0b' : '#d1d5db'}
                strokeWidth="5"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={offset}
                style={{ transition: 'stroke-dashoffset 0.6s ease-out' }}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-xs font-bold text-gray-800">{Math.round(progress)}%</span>
            </div>
          </div>

          {/* Stats grid */}
          <div className="flex-1 grid grid-cols-2 gap-x-3 gap-y-2">
            <div>
              <div className="text-xs text-gray-400">Sessions</div>
              <div className="text-sm font-bold text-gray-900">
                {plan.completed_sessions}<span className="text-gray-400 font-normal text-xs">/{plan.total_sessions}</span>
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-400">Score</div>
              <div className={`text-sm font-bold ${plan.assessment_score >= 80 ? 'text-emerald-600' : plan.assessment_score >= 60 ? 'text-amber-600' : plan.assessment_score > 0 ? 'text-rose-600' : 'text-gray-300'}`}>
                {plan.assessment_score > 0 ? plan.assessment_score : '—'}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-400">Last active</div>
              <div className={`text-xs font-semibold ${
                plan.days_since_activity <= 3 ? 'text-emerald-600' :
                plan.days_since_activity <= 7 ? 'text-amber-600' :
                plan.days_since_activity < 999 ? 'text-rose-500' : 'text-gray-400'
              }`}>
                {plan.days_since_activity < 999 ? `${plan.days_since_activity}d ago` : 'No activity'}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-400">Next focus</div>
              <div className="text-xs text-gray-600 truncate max-w-[80px]" title={plan.next_focus_area}>
                {plan.next_focus_area || '—'}
              </div>
            </div>
          </div>
        </div>

        {/* Bottom hint */}
        <div className="border-t border-gray-100 px-4 py-2 bg-gray-50/50">
          <p className="text-xs text-gray-400 text-center">Click <span className="font-semibold text-[#4ECFBF]">View</span> for full history</p>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// Learner Detail Modal
// ─────────────────────────────────────────────
function LearnerDetailModal({
  learner, details, loading, onClose,
}: { learner: Learner; details: any; loading: boolean; onClose: () => void }) {
  const [tab, setTab] = useState<'overview' | 'plans' | 'sessions' | 'challenges' | 'dna' | 'insights'>('overview');
  const [sessionDateRange, setSessionDateRange] = useState<DateRange>({ start: null, end: null, label: 'All time' });
  const [challengeDateRange, setChallengeDateRange] = useState<DateRange>({ start: null, end: null, label: 'All time' });
  const plan = learner.learning_plans[0];

  const tabs: { key: 'overview' | 'plans' | 'sessions' | 'challenges' | 'dna' | 'insights'; label: string; icon: React.ReactNode }[] = [
    { key: 'overview', label: 'Overview', icon: <BarChart2 className="w-3.5 h-3.5" /> },
    { key: 'plans', label: `Plans (${details?.all_learning_plans?.length ?? 0})`, icon: <BookOpen className="w-3.5 h-3.5" /> },
    { key: 'sessions', label: `Sessions (${details?.practice_sessions?.length ?? 0})`, icon: <Mic className="w-3.5 h-3.5" /> },
    { key: 'challenges', label: `Challenges (${details?.challenge_sessions?.length ?? 0})`, icon: <Zap className="w-3.5 h-3.5" /> },
    { key: 'dna', label: 'Speaking DNA', icon: <Dna className="w-3.5 h-3.5" /> },
    { key: 'insights', label: 'AI Insights', icon: <Bot className="w-3.5 h-3.5" /> },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/60 backdrop-blur-sm p-4 pt-8">
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-5xl my-4 sm:my-8 mx-2 sm:mx-4">
        {/* Modal Header */}
        <div className="relative bg-gradient-to-br from-[#4ECFBF] via-[#3bbdad] to-[#2a9e92] rounded-t-3xl p-7">
          <button onClick={onClose} className="absolute top-5 right-5 text-white/80 hover:text-white hover:bg-white/20 rounded-xl p-2 transition-all">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center text-white text-2xl font-bold">
              {learner.name.charAt(0)}
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">{learner.name}</h2>
              <p className="text-white/75 text-sm">{learner.email}</p>
              {plan && (
                <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                  {/* Flag + language — no container, clean inline */}
                  <div className="flex items-center gap-1.5">
                    <FlagOrText language={plan.language} size={16} />
                    <span className="text-white/90 text-sm font-medium capitalize">{plan.language}</span>
                  </div>
                  <span className="bg-white/20 text-white text-xs font-bold px-2 py-0.5 rounded-md">
                    {plan.proficiency_level}
                  </span>
                  <span className={`flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full ${
                    plan.progress_status === 'on_track' ? 'bg-emerald-400/30 text-white' :
                    plan.progress_status === 'at_risk' ? 'bg-amber-400/30 text-white' :
                    'bg-gray-400/30 text-white'
                  }`}>
                    {plan.progress_status === 'on_track'
                      ? <><CheckCircle className="w-3 h-3" /> On Track</>
                      : plan.progress_status === 'at_risk'
                      ? <><AlertTriangle className="w-3 h-3" /> At Risk</>
                      : <><Minus className="w-3 h-3" /> Inactive</>}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Quick Stats Strip */}
          {details?.profile && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5">
              {[
                { label: 'Plan Sessions', value: details.profile.total_sessions },
                { label: 'Voice Sessions', value: details.profile.realtime_sessions ?? details.practice_sessions?.length ?? 0 },
                { label: 'Challenges', value: details.profile.challenge_sessions ?? details.challenge_sessions?.length ?? 0 },
                { label: 'Min Practiced', value: Math.round(details.profile.total_minutes) },
              ].map(s => (
                <div key={s.label} className="bg-white/15 rounded-xl p-3 text-center">
                  <div className="text-2xl font-bold text-white">{s.value}</div>
                  <div className="text-white/70 text-xs mt-0.5">{s.label}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="flex gap-0 border-b border-gray-100 px-4 sm:px-6 bg-gray-50/50 overflow-x-auto">
          {tabs.map(t => (
            <button
              key={t.key}
              onClick={() => setTab(t.key as any)}
              className={`py-3.5 px-4 text-sm font-medium border-b-2 transition-all whitespace-nowrap flex items-center gap-1.5 ${
                tab === t.key ? 'border-[#4ECFBF] text-[#4ECFBF]' : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {t.icon} {t.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="p-6 max-h-[60vh] md:max-h-[55vh] overflow-y-auto">
          {loading ? (
            <div className="py-4">
              <ModalSpinner label="Loading learner data..." /></div>
          ) : !details ? (
            <div className="text-center py-12 text-gray-400">Failed to load details</div>
          ) : (
            <>
              {/* ── OVERVIEW ── */}
              {tab === 'overview' && (() => {
                const plan = details.all_learning_plans?.[0];
                const dna = details.speaking_dna;
                const dailyStats = details.daily_stats;
                const recentDays = dailyStats?.recent_daily || [];
                const activeDays = recentDays.filter((d: any) => d.minutes > 0 || d.sessions > 0);

                // Engagement health: how many of last 7 days had activity?
                const last7 = recentDays.slice(0, 7);
                const activeLast7 = last7.filter((d: any) => d.minutes > 0 || d.sessions > 0).length;
                const engagementScore = Math.round((activeLast7 / 7) * 100);
                const engagementLevel = engagementScore >= 57 ? 'high' : engagementScore >= 28 ? 'medium' : 'low';
                const engagementConfig = {
                  high:   { label: 'Highly Engaged', color: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200', bar: 'bg-emerald-400', dot: 'bg-emerald-400' },
                  medium: { label: 'Moderately Engaged', color: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200', bar: 'bg-amber-400', dot: 'bg-amber-400' },
                  low:    { label: 'Needs Attention', color: 'text-rose-700', bg: 'bg-rose-50', border: 'border-rose-200', bar: 'bg-rose-400', dot: 'bg-rose-400' },
                }[engagementLevel];

                // Completion rate: sessions with end_time / total sessions
                const totalSessions = details.practice_sessions?.length ?? 0;
                const completedSessions = details.practice_sessions?.filter((s: any) => s.duration_minutes > 1).length ?? 0;
                const completionRate = totalSessions > 0 ? Math.round((completedSessions / totalSessions) * 100) : 0;

                // Practice time pattern: group sessions by hour
                const hourBuckets: Record<string, number> = { Morning: 0, Afternoon: 0, Evening: 0, Night: 0 };
                details.practice_sessions?.forEach((s: any) => {
                  if (!s.created_at) return;
                  const h = new Date(s.created_at).getHours();
                  if (h >= 5 && h < 12) hourBuckets.Morning++;
                  else if (h >= 12 && h < 17) hourBuckets.Afternoon++;
                  else if (h >= 17 && h < 21) hourBuckets.Evening++;
                  else hourBuckets.Night++;
                });
                const peakTime = Object.entries(hourBuckets).sort((a, b) => b[1] - a[1])[0];

                // Week-over-week quality trend from DNA history
                const weeklyTrend = dna?.weekly_trend || [];
                const lastWeek = weeklyTrend[weeklyTrend.length - 1];
                const prevWeek = weeklyTrend[weeklyTrend.length - 2];
                const confidenceDelta = lastWeek && prevWeek ? lastWeek.confidence - prevWeek.confidence : null;

                // Weak areas from DNA + sentence analysis
                const weakAreas: string[] = [
                  ...(dna?.growth_areas?.map((g: string) => g.replace(/_/g, ' ')) || []),
                  ...(dna?.strands?.accuracy?.common_errors?.slice(0, 2) || []),
                  ...(dna?.strands?.accuracy?.improving_areas?.slice(0, 2) || []),
                ].filter(Boolean).slice(0, 4);

                // Anxiety triggers
                const anxietyTriggers: string[] = dna?.strands?.emotional?.anxiety_triggers || [];

                // Tutor action: derive the #1 thing to do
                const action = (() => {
                  if (engagementLevel === 'low') return { text: 'Send an encouraging message — student hasn\'t practiced in a while', urgency: 'high' };
                  if (completionRate < 60) return { text: 'Sessions often abandoned — discuss session length and difficulty in next check-in', urgency: 'medium' };
                  if (confidenceDelta !== null && confidenceDelta < -5) return { text: 'Confidence dropped this week — focus on positive reinforcement and familiar topics', urgency: 'medium' };
                  if (weakAreas.length > 0) return { text: `Work on: ${weakAreas[0]}`, urgency: 'normal' };
                  return { text: 'Student is on track — maintain current pace and introduce slightly harder challenges', urgency: 'normal' };
                })();

                return (
                  <div className="space-y-4">
                    {/* ① TUTOR ACTION — the most important thing, top of the page */}
                    <div className={`rounded-2xl border p-4 flex items-start gap-3 ${
                      action.urgency === 'high' ? 'bg-rose-50 border-rose-200' :
                      action.urgency === 'medium' ? 'bg-amber-50 border-amber-200' :
                      'bg-[#4ECFBF]/8 border-[#4ECFBF]/30'
                    }`}>
                      <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${
                        action.urgency === 'high' ? 'bg-rose-100' :
                        action.urgency === 'medium' ? 'bg-amber-100' : 'bg-[#4ECFBF]/20'
                      }`}>
                        <Lightbulb className={`w-4 h-4 ${
                          action.urgency === 'high' ? 'text-rose-600' :
                          action.urgency === 'medium' ? 'text-amber-600' : 'text-[#4ECFBF]'
                        }`} strokeWidth={1.8} />
                      </div>
                      <div>
                        <p className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-0.5">Suggested Action</p>
                        <p className={`text-sm font-medium ${
                          action.urgency === 'high' ? 'text-rose-800' :
                          action.urgency === 'medium' ? 'text-amber-800' : 'text-gray-800'
                        }`}>{action.text}</p>
                      </div>
                    </div>

                    {/* ② ENGAGEMENT HEALTH + KEY STATS — top row */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      {/* Engagement */}
                      <div className={`rounded-2xl border p-3.5 ${engagementConfig.bg} ${engagementConfig.border}`}>
                        <div className="flex items-center gap-2 mb-2">
                          <span className={`w-2 h-2 rounded-full ${engagementConfig.dot} animate-pulse`} />
                          <span className={`text-xs font-bold uppercase tracking-wide ${engagementConfig.color}`}>Engagement</span>
                        </div>
                        <div className={`text-2xl font-bold ${engagementConfig.color}`}>{engagementScore}%</div>
                        <div className={`text-xs mt-0.5 ${engagementConfig.color} opacity-80`}>{engagementConfig.label}</div>
                        <div className="w-full bg-white/50 rounded-full h-1.5 mt-2">
                          <div className={`h-1.5 rounded-full ${engagementConfig.bar}`} style={{ width: `${engagementScore}%` }} />
                        </div>
                        <div className="text-xs text-gray-400 mt-1">{activeLast7}/7 days active</div>
                      </div>

                      {/* Completion Rate */}
                      <div className="bg-white border border-gray-100 rounded-2xl p-3.5">
                        <div className="flex items-center gap-2 mb-2">
                          <div className="w-6 h-6 bg-purple-100 rounded-lg flex items-center justify-center">
                            <CheckCircle className="w-3.5 h-3.5 text-purple-600" strokeWidth={1.8} />
                          </div>
                          <span className="text-xs font-bold text-gray-500 uppercase tracking-wide">Completion</span>
                        </div>
                        <div className={`text-2xl font-bold ${completionRate >= 75 ? 'text-emerald-600' : completionRate >= 50 ? 'text-amber-600' : 'text-rose-600'}`}>
                          {completionRate}%
                        </div>
                        <div className="text-xs text-gray-400 mt-0.5">sessions finished</div>
                        <div className="text-xs text-gray-400 mt-1">{completedSessions}/{totalSessions} sessions</div>
                      </div>

                      {/* Peak Practice Time */}
                      <div className="bg-white border border-gray-100 rounded-2xl p-3.5">
                        <div className="flex items-center gap-2 mb-2">
                          <div className="w-6 h-6 bg-blue-100 rounded-lg flex items-center justify-center">
                            <Clock className="w-3.5 h-3.5 text-blue-600" strokeWidth={1.8} />
                          </div>
                          <span className="text-xs font-bold text-gray-500 uppercase tracking-wide">Peak Time</span>
                        </div>
                        <div className="text-lg font-bold text-gray-900">{peakTime?.[0] || '—'}</div>
                        <div className="text-xs text-gray-400 mt-0.5">most active period</div>
                        <div className="flex gap-1 mt-2">
                          {Object.entries(hourBuckets).map(([label, count]) => {
                            const maxCount = Math.max(...Object.values(hourBuckets), 1);
                            return (
                              <div key={label} className="flex-1 flex flex-col items-center gap-0.5">
                                <div className="w-full bg-gray-100 rounded-sm overflow-hidden" style={{ height: 16 }}>
                                  <div className="bg-blue-400 rounded-sm w-full" style={{ height: `${(count / maxCount) * 100}%`, marginTop: `${(1 - count / maxCount) * 100}%` }} />
                                </div>
                                <span className="text-[9px] text-gray-400">{label[0]}</span>
                              </div>
                            );
                          })}
                        </div>
                      </div>

                      {/* Confidence Trend */}
                      <div className="bg-white border border-gray-100 rounded-2xl p-3.5">
                        <div className="flex items-center gap-2 mb-2">
                          <div className="w-6 h-6 bg-teal-100 rounded-lg flex items-center justify-center">
                            <TrendingUp className="w-3.5 h-3.5 text-[#4ECFBF]" strokeWidth={1.8} />
                          </div>
                          <span className="text-xs font-bold text-gray-500 uppercase tracking-wide">Confidence</span>
                        </div>
                        {lastWeek ? (
                          <>
                            <div className="text-2xl font-bold text-gray-900">{lastWeek.confidence}%</div>
                            <div className={`text-xs font-semibold mt-0.5 flex items-center gap-1 ${
                              confidenceDelta === null ? 'text-gray-400' :
                              confidenceDelta > 0 ? 'text-emerald-600' :
                              confidenceDelta < 0 ? 'text-rose-600' : 'text-gray-400'
                            }`}>
                              {confidenceDelta !== null && (
                                <>{confidenceDelta > 0 ? '↑' : confidenceDelta < 0 ? '↓' : '→'} {Math.abs(confidenceDelta)}% vs last week</>
                              )}
                            </div>
                          </>
                        ) : (
                          <div className="text-sm text-gray-400 mt-1">No trend data yet</div>
                        )}
                        {dna?.strands?.confidence?.level && (
                          <div className="text-xs text-gray-400 mt-1 capitalize">{dna.strands.confidence.level}</div>
                        )}
                      </div>
                    </div>

                    {/* ③ WHAT'S BLOCKING PROGRESS */}
                    {(weakAreas.length > 0 || anxietyTriggers.length > 0) && (
                      <div className="bg-white border border-gray-100 rounded-2xl p-4">
                        <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-3 flex items-center gap-1.5">
                          <Target className="w-3.5 h-3.5 text-amber-500" strokeWidth={1.8} />
                          What's Blocking Progress
                        </h4>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          {weakAreas.length > 0 && (
                            <div>
                              <p className="text-xs font-semibold text-gray-600 mb-2">Language gaps to address:</p>
                              <div className="space-y-1.5">
                                {weakAreas.map((area, i) => (
                                  <div key={i} className="flex items-center gap-2 text-xs text-amber-700 bg-amber-50 rounded-lg px-2.5 py-1.5">
                                    <span className="w-1.5 h-1.5 bg-amber-400 rounded-full flex-shrink-0" />
                                    <span className="capitalize">{area}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                          {anxietyTriggers.length > 0 && (
                            <div>
                              <p className="text-xs font-semibold text-gray-600 mb-2">Emotional triggers to avoid:</p>
                              <div className="space-y-1.5">
                                {anxietyTriggers.map((t: string, i: number) => (
                                  <div key={i} className="flex items-center gap-2 text-xs text-rose-700 bg-rose-50 rounded-lg px-2.5 py-1.5">
                                    <span className="w-1.5 h-1.5 bg-rose-400 rounded-full flex-shrink-0" />
                                    <span className="capitalize">{t.replace(/_/g, ' ')}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* ④ PRACTICE HEATMAP (7 days activity grid) */}
                    {recentDays.length > 0 && (
                      <div className="bg-white border border-gray-100 rounded-2xl p-4">
                        <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-3 flex items-center gap-1.5">
                          <Calendar className="w-3.5 h-3.5 text-[#4ECFBF]" strokeWidth={1.8} />
                          Activity Heatmap — Last 14 Days
                        </h4>
                        <div className="flex gap-1.5 flex-wrap">
                          {recentDays.slice(0, 14).reverse().map((day: any, i: number) => {
                            const intensity = day.minutes === 0 ? 0 : day.minutes < 5 ? 1 : day.minutes < 15 ? 2 : day.minutes < 30 ? 3 : 4;
                            const bgColors = ['bg-gray-100', 'bg-[#4ECFBF]/20', 'bg-[#4ECFBF]/40', 'bg-[#4ECFBF]/70', 'bg-[#4ECFBF]'];
                            return (
                              <div key={i} className="flex flex-col items-center gap-1 group relative">
                                <div className={`w-8 h-8 rounded-lg ${bgColors[intensity]} transition-all group-hover:scale-110`} />
                                <span className="text-[9px] text-gray-400">
                                  {new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' }).charAt(0)}
                                </span>
                                {/* Micro tooltip */}
                                <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-gray-800 text-white text-[10px] px-2 py-0.5 rounded-md whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                                  {day.minutes}m · {day.sessions} sess
                                </div>
                              </div>
                            );
                          })}
                        </div>
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-[10px] text-gray-400">Less</span>
                          {['bg-gray-100', 'bg-[#4ECFBF]/20', 'bg-[#4ECFBF]/40', 'bg-[#4ECFBF]/70', 'bg-[#4ECFBF]'].map((bg, i) => (
                            <div key={i} className={`w-3 h-3 rounded-sm ${bg}`} />
                          ))}
                          <span className="text-[10px] text-gray-400">More</span>
                        </div>
                      </div>
                    )}

                    {/* ⑤ LANGUAGE PROGRESS — compact, tutor context */}
                    {details.all_learning_plans?.length > 0 && (
                      <div className="bg-white border border-gray-100 rounded-2xl p-4">
                        <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-3 flex items-center gap-1.5">
                          <BookOpen className="w-3.5 h-3.5 text-[#4ECFBF]" strokeWidth={1.8} />
                          Learning Plans
                        </h4>
                        <div className="space-y-3">
                          {details.all_learning_plans.map((p: any) => (
                            <div key={p.id} className="flex items-center gap-3">
                              <FlagOrText language={p.language} size={18} />
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between mb-1">
                                  <div className="flex items-center gap-1.5">
                                    <span className="text-sm font-semibold text-gray-800 capitalize">
                                      {p.language ? p.language.charAt(0).toUpperCase()+p.language.slice(1) : '—'}
                                    </span>
                                    <span className={`text-xs px-1.5 py-0.5 rounded-md border font-bold ${LEVEL_COLORS[p.proficiency_level] || 'bg-gray-100 text-gray-600 border-gray-200'}`}>
                                      {p.proficiency_level}
                                    </span>
                                  </div>
                                  <span className="text-xs font-bold text-gray-700">{p.progress_percentage?.toFixed(0)}%</span>
                                </div>
                                <div className="w-full bg-gray-100 rounded-full h-2">
                                  <div className="bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] h-2 rounded-full" style={{ width: `${Math.min(100, p.progress_percentage || 0)}%` }} />
                                </div>
                                <div className="flex justify-between text-xs text-gray-400 mt-0.5">
                                  <span>{p.completed_sessions}/{p.total_sessions} sessions</span>
                                  <span>{p.practice_minutes_used}m used</span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })()}

              {/* ── PLANS ── */}
              {tab === 'plans' && (
                <div className="space-y-4">
                  {details.all_learning_plans?.length > 0 ? details.all_learning_plans.map((p: any) => (
                    <div key={p.id} className="border border-gray-100 rounded-2xl overflow-hidden">
                      <div className="p-5 bg-gradient-to-r from-emerald-50 to-teal-50">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <FlagOrText language={p.language} size={22} />
                            <span className="font-bold text-gray-900">{p.language ? p.language.charAt(0).toUpperCase()+p.language.slice(1) : '—'}</span>
                            <span className={`text-xs px-2 py-0.5 rounded-full border font-semibold ${LEVEL_COLORS[p.proficiency_level] || 'bg-gray-100 text-gray-600 border-gray-200'}`}>
                              {p.proficiency_level}
                            </span>
                          </div>
                          <span className="text-2xl font-bold text-[#4ECFBF]">{p.progress_percentage?.toFixed(0)}%</span>
                        </div>
                        <div className="w-full bg-white/70 rounded-full h-3">
                          <div className="bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] h-3 rounded-full" style={{ width: `${p.progress_percentage || 0}%` }} />
                        </div>
                        <div className="grid grid-cols-3 gap-3 mt-3 text-sm">
                          <div><span className="text-gray-500">Sessions:</span> <span className="font-semibold">{p.completed_sessions}/{p.total_sessions}</span></div>
                          <div><span className="text-gray-500">Minutes:</span> <span className="font-semibold">{p.practice_minutes_used}/{p.total_practice_minutes}</span></div>
                          <div><span className="text-gray-500">Score:</span> <span className="font-semibold">{p.assessment_data?.overall_score ?? '—'}</span></div>
                        </div>
                      </div>
                      {p.assessment_data?.strengths?.length > 0 && (
                        <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4 bg-white">
                          <div>
                            <p className="text-xs font-semibold text-green-700 mb-2 flex items-center"><CheckCircle className="w-3.5 h-3.5 text-green-600 inline mr-1" /> Strengths</p>
                            {p.assessment_data.strengths.slice(0, 3).map((s: string, i: number) => (
                              <div key={i} className="text-xs text-gray-600 bg-green-50 rounded-lg px-3 py-1.5 mb-1">{s}</div>
                            ))}
                          </div>
                          <div>
                            <p className="text-xs font-semibold text-amber-700 mb-2 flex items-center"><Target className="w-3.5 h-3.5 text-amber-600 inline mr-1" /> Areas to Improve</p>
                            {p.assessment_data.areas_for_improvement?.slice(0, 3).map((a: string, i: number) => (
                              <div key={i} className="text-xs text-gray-600 bg-amber-50 rounded-lg px-3 py-1.5 mb-1">{a}</div>
                            ))}
                          </div>
                        </div>
                      )}
                      {p.session_summaries?.length > 0 && (
                        <div className="p-4 border-t border-gray-100">
                          <p className="text-xs font-semibold text-gray-600 mb-2">Recent Session Summaries</p>
                          {p.session_summaries.slice(-2).map((s: any, i: number) => (
                            <div key={i} className="text-xs text-gray-600 bg-purple-50 rounded-lg p-3 mb-1">
                              {typeof s === 'string' ? s : s?.summary || JSON.stringify(s).slice(0, 150)}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )) : (
                    <div className="text-center py-12 text-gray-400"><BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-2" />No learning plans yet</div>
                  )}
                </div>
              )}

              {/* ── SESSIONS ── */}
              {tab === 'sessions' && (
                <div className="space-y-3">
                  {/* Date filter header */}
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-400 font-medium">
                      {(() => {
                        const filtered = (details.practice_sessions || []).filter((s: any) => {
                          if (!sessionDateRange.start || !s.created_at) return true;
                          const d = new Date(s.created_at);
                          return d >= sessionDateRange.start! && d <= sessionDateRange.end!;
                        });
                        return `${filtered.length} of ${details.practice_sessions?.length ?? 0} sessions`;
                      })()}
                    </span>
                    <DateRangePicker value={sessionDateRange} onChange={setSessionDateRange} align="right" />
                  </div>

                  {/* Table */}
                  {(() => {
                    const filtered = (details.practice_sessions || []).filter((s: any) => {
                      if (!sessionDateRange.start || !s.created_at) return true;
                      const d = new Date(s.created_at);
                      return d >= sessionDateRange.start! && d <= sessionDateRange.end!;
                    });
                    if (filtered.length === 0) return (
                      <div className="text-center py-12 text-gray-400">
                        <Calendar className="w-10 h-10 text-gray-200 mx-auto mb-2" strokeWidth={1.5} />
                        <p className="font-medium text-sm">No sessions in this period</p>
                        <button onClick={() => setSessionDateRange({ start: null, end: null, label: 'All time' })} className="text-xs text-[#4ECFBF] mt-1 underline">Clear filter</button>
                      </div>
                    );
                    return (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead><tr className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase">
                            <th className="px-4 py-3 text-left rounded-l-lg">Date</th>
                            <th className="px-4 py-3 text-left">Language</th>
                            <th className="px-4 py-3 text-left">Level</th>
                            <th className="px-4 py-3 text-center">Duration</th>
                            <th className="px-4 py-3 text-center rounded-r-lg">Type</th>
                          </tr></thead>
                          <tbody className="divide-y divide-gray-50">
                            {filtered.map((s: any) => (
                              <tr key={s.id} className="hover:bg-gray-50">
                                <td className="px-4 py-3 text-gray-700 text-xs">{s.created_at ? new Date(s.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '—'}</td>
                                <td className="px-4 py-3 text-gray-700"><div className="flex items-center gap-1.5"><FlagOrText language={s.language} size={16} /><span className="text-xs">{s.language ? s.language.charAt(0).toUpperCase()+s.language.slice(1) : '—'}</span></div></td>
                                <td className="px-4 py-3">
                                  {s.level ? <span className={`text-xs px-2 py-0.5 rounded-full border font-semibold ${LEVEL_COLORS[s.level] || 'bg-gray-100 text-gray-600 border-gray-200'}`}>{s.level}</span> : '—'}
                                </td>
                                <td className="px-4 py-3 text-center text-xs font-medium text-gray-800">{s.duration_minutes}m</td>
                                <td className="px-4 py-3 text-center text-xs text-gray-500 capitalize">{s.session_type?.replace('_', ' ') || 'practice'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    );
                  })()}
                </div>
              )}

              {/* ── CHALLENGES ── */}
              {tab === 'challenges' && (
                <div className="space-y-3">
                  {details.challenge_sessions?.length > 0 ? (() => {
                    const filtered = (details.challenge_sessions || []).filter((c: any) => {
                      if (!challengeDateRange.start || !c.created_at) return true;
                      const d = new Date(c.created_at);
                      return d >= challengeDateRange.start! && d <= challengeDateRange.end!;
                    });

                    const totalSessions = filtered.length;
                    const totalCorrect = filtered.reduce((s: number, c: any) => s + (c.correct_answers || 0), 0);
                    const totalQuestions = filtered.reduce((s: number, c: any) => s + (c.total_challenges || 0), 0);
                    const totalXP = filtered.reduce((s: number, c: any) => s + (c.total_xp || 0), 0);
                    const accuracy = totalQuestions > 0 ? Math.round((totalCorrect / totalQuestions) * 100) : 0;

                    return (
                      <>
                        {/* Date filter header */}
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-400 font-medium">
                            {filtered.length} of {details.challenge_sessions.length} sessions
                          </span>
                          <DateRangePicker value={challengeDateRange} onChange={setChallengeDateRange} align="right" />
                        </div>

                        {/* Summary stats — computed on filtered set */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          <div className="bg-gray-50 rounded-xl p-3 text-center">
                            <div className="text-xl font-bold text-[#4ECFBF]">{totalSessions}</div>
                            <div className="text-xs text-gray-500 mt-0.5">Sessions Played</div>
                          </div>
                          <div className="bg-gray-50 rounded-xl p-3 text-center">
                            <div className="text-xl font-bold text-emerald-600">{totalCorrect}</div>
                            <div className="text-xs text-gray-500 mt-0.5">Correct Answers</div>
                            <div className="text-xs text-gray-400">out of {totalQuestions}</div>
                          </div>
                          <div className="bg-gray-50 rounded-xl p-3 text-center">
                            <div className="text-xl font-bold text-yellow-600">{totalXP}</div>
                            <div className="text-xs text-gray-500 mt-0.5">Total XP</div>
                          </div>
                          <div className="bg-gray-50 rounded-xl p-3 text-center">
                            <div className="text-xl font-bold text-blue-600">{accuracy}%</div>
                            <div className="text-xs text-gray-500 mt-0.5">Overall Accuracy</div>
                            <div className="text-xs text-gray-400">{totalCorrect}/{totalQuestions}</div>
                          </div>
                        </div>

                        {filtered.length === 0 ? (
                          <div className="text-center py-10 text-gray-400">
                            <Calendar className="w-10 h-10 text-gray-200 mx-auto mb-2" strokeWidth={1.5} />
                            <p className="font-medium text-sm">No challenges in this period</p>
                            <button onClick={() => setChallengeDateRange({ start: null, end: null, label: 'All time' })} className="text-xs text-[#4ECFBF] mt-1 underline">Clear filter</button>
                          </div>
                        ) : (
                          <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                              <thead><tr className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase">
                                <th className="px-4 py-3 text-left rounded-l-lg">Date</th>
                                <th className="px-4 py-3 text-left">Type</th>
                                <th className="px-4 py-3 text-left">Language</th>
                                <th className="px-4 py-3 text-center">Correct / Total</th>
                                <th className="px-4 py-3 text-center">Accuracy</th>
                                <th className="px-4 py-3 text-center">XP</th>
                                <th className="px-4 py-3 text-center rounded-r-lg">Combo</th>
                              </tr></thead>
                              <tbody className="divide-y divide-gray-50">
                                {filtered.map((c: any) => (
                                  <tr key={c.id} className="hover:bg-gray-50">
                                    <td className="px-4 py-3 text-gray-600 text-xs">{c.created_at ? new Date(c.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '—'}</td>
                                    <td className="px-4 py-3 text-xs text-gray-700 capitalize">{c.challenge_type?.replace(/_/g, ' ') || '—'}</td>
                                    <td className="px-4 py-3 capitalize text-gray-700 text-xs">{c.language || '—'}</td>
                                    <td className="px-4 py-3 text-center font-bold text-gray-800 text-xs">
                                      {c.total_challenges > 0
                                        ? <span>{c.correct_answers}<span className="text-gray-400 font-normal">/{c.total_challenges}</span></span>
                                        : c.correct_answers > 0 ? c.correct_answers : '—'}
                                    </td>
                                    <td className="px-4 py-3 text-center">
                                      {c.accuracy > 0 ? (
                                        <span className={`font-bold text-xs ${c.accuracy >= 80 ? 'text-emerald-600' : c.accuracy >= 60 ? 'text-amber-600' : 'text-rose-600'}`}>
                                          {Math.round(c.accuracy)}%
                                        </span>
                                      ) : '—'}
                                    </td>
                                    <td className="px-4 py-3 text-center text-xs font-semibold text-yellow-600">
                                      {c.total_xp > 0 ? `+${c.total_xp}` : '—'}
                                    </td>
                                    <td className="px-4 py-3 text-center text-xs text-gray-500">
                                      {c.max_combo > 0 ? <span className="inline-flex items-center gap-1"><Flame className="w-3.5 h-3.5 text-orange-400" strokeWidth={1.5} />{c.max_combo}</span> : '—'}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </>
                    );
                  })() : (
                    <div className="text-center py-12 text-gray-400"><Zap className="w-12 h-12 text-gray-300 mx-auto mb-2" />No challenges completed yet</div>
                  )}
                </div>
              )}

              {/* ── SPEAKING DNA ── */}
              {tab === 'dna' && (
                <div className="space-y-5">
                  {!details?.speaking_dna ? (
                    <div className="text-center py-14">
                      <Dna className="w-12 h-12 text-gray-200 mx-auto mb-3" />
                      <p className="text-gray-400 font-medium">No Speaking DNA data yet</p>
                      <p className="text-gray-300 text-sm mt-1">Data is generated after voice practice sessions</p>
                    </div>
                  ) : (() => {
                    const dna = details.speaking_dna;
                    const strands = dna.strands;

                    // Strand config: color, icon, description for tutors
                    const strandConfig: Record<string, { color: string; bg: string; bar: string; tutorHint: string }> = {
                      rhythm:     { color: 'text-blue-600',   bg: 'bg-blue-50',   bar: 'bg-blue-400',   tutorHint: 'Speaking pace & flow consistency' },
                      confidence: { color: 'text-[#4ECFBF]', bg: 'bg-teal-50',   bar: 'bg-[#4ECFBF]',  tutorHint: 'Self-assurance during speech' },
                      vocabulary: { color: 'text-purple-600', bg: 'bg-purple-50', bar: 'bg-purple-400', tutorHint: 'Word variety & complexity usage' },
                      accuracy:   { color: 'text-emerald-600',bg: 'bg-emerald-50',bar: 'bg-emerald-400',tutorHint: 'Grammar & sentence correctness' },
                      learning:   { color: 'text-amber-600',  bg: 'bg-amber-50',  bar: 'bg-amber-400',  tutorHint: 'How they tackle new challenges' },
                      emotional:  { color: 'text-rose-500',   bg: 'bg-rose-50',   bar: 'bg-rose-400',   tutorHint: 'Energy arc across a session' },
                    };

                    const trendIcon = (trend: string) =>
                      trend === 'improving' ? <TrendingUp className="w-3.5 h-3.5 text-emerald-500" /> :
                      trend === 'declining' ? <TrendingDown className="w-3.5 h-3.5 text-rose-500" /> :
                      <Minus className="w-3.5 h-3.5 text-gray-400" />;

                    return (
                      <>
                        {/* Archetype Banner */}
                        <div className="bg-gradient-to-r from-[#4ECFBF]/10 to-purple-50 border border-[#4ECFBF]/20 rounded-2xl p-4 flex items-start gap-4">
                          <div className="w-12 h-12 bg-gradient-to-br from-[#4ECFBF] to-purple-500 rounded-xl flex items-center justify-center flex-shrink-0">
                            <Dna className="w-6 h-6 text-white" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-bold text-gray-900 text-sm">{dna.archetype || 'Learner Profile'}</span>
                              <span className="text-xs bg-[#4ECFBF]/20 text-[#4ECFBF] px-2 py-0.5 rounded-full font-semibold capitalize">
                                {dna.coach_approach?.replace(/_/g, ' ')}
                              </span>
                            </div>
                            <p className="text-xs text-gray-500 mt-1 leading-relaxed">{dna.summary}</p>
                            <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                              <span><strong className="text-gray-600">{dna.sessions_analyzed}</strong> sessions analyzed</span>
                              <span><strong className="text-gray-600">{dna.total_speaking_minutes}</strong> min of speech</span>
                            </div>
                          </div>
                        </div>

                        {/* 6 Strand Bars with CSS animation */}
                        <div className="bg-white rounded-2xl border border-gray-100 p-5">
                          <h4 className="text-sm font-bold text-gray-800 mb-4 flex items-center gap-2">
                            <Dna className="w-4 h-4 text-[#4ECFBF]" /> Speaking DNA Strands
                          </h4>
                          <div className="space-y-3">
                            {Object.entries(strands).map(([key, strand]: [string, any]) => {
                              const cfg = strandConfig[key] || { color: 'text-gray-600', bg: 'bg-gray-50', bar: 'bg-gray-400', tutorHint: '' };
                              return (
                                <div key={key} className="group">
                                  <div className="flex items-center justify-between mb-1">
                                    <div className="flex items-center gap-2">
                                      <span className={`text-xs font-semibold ${cfg.color}`}>{strand.label}</span>
                                      {key === 'confidence' && strand.trend && (
                                        <span className="flex items-center gap-0.5">{trendIcon(strand.trend)}</span>
                                      )}
                                    </div>
                                    <div className="flex items-center gap-2">
                                      <span className="text-xs text-gray-400 hidden group-hover:block transition-all">{cfg.tutorHint}</span>
                                      <span className={`text-sm font-bold ${cfg.color}`}>{strand.score}%</span>
                                    </div>
                                  </div>
                                  <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                                    <div
                                      className={`h-2.5 rounded-full ${cfg.bar} transition-all duration-1000 ease-out`}
                                      style={{
                                        width: `${strand.score}%`,
                                        animation: 'dnaBarGrow 1.2s ease-out forwards',
                                      }}
                                    />
                                  </div>
                                  <p className="text-xs text-gray-400 mt-0.5">{strand.description}</p>
                                </div>
                              );
                            })}
                          </div>
                        </div>

                        {/* Strengths & Growth Side by Side */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                          <div className="bg-emerald-50 border border-emerald-100 rounded-2xl p-4">
                            <h5 className="text-xs font-bold text-emerald-800 uppercase tracking-wide mb-3 flex items-center gap-1.5">
                              <Shield className="w-3.5 h-3.5" /> Strengths
                            </h5>
                            <div className="space-y-1.5">
                              {dna.strengths?.map((s: string) => (
                                <div key={s} className="flex items-center gap-2 text-xs text-emerald-700">
                                  <CheckCircle className="w-3.5 h-3.5 flex-shrink-0" />
                                  <span className="capitalize">{s.replace(/_/g, ' ')}</span>
                                </div>
                              ))}
                              {(!dna.strengths || dna.strengths.length === 0) && <p className="text-xs text-emerald-600">Building up...</p>}
                            </div>
                          </div>
                          <div className="bg-amber-50 border border-amber-100 rounded-2xl p-4">
                            <h5 className="text-xs font-bold text-amber-800 uppercase tracking-wide mb-3 flex items-center gap-1.5">
                              <Target className="w-3.5 h-3.5" /> Focus Areas
                            </h5>
                            <div className="space-y-1.5">
                              {dna.growth_areas?.map((g: string) => (
                                <div key={g} className="flex items-center gap-2 text-xs text-amber-700">
                                  <Target className="w-3.5 h-3.5 flex-shrink-0" />
                                  <span className="capitalize">{g.replace(/_/g, ' ')}</span>
                                </div>
                              ))}
                              {(!dna.growth_areas || dna.growth_areas.length === 0) && <p className="text-xs text-amber-600">All looking good!</p>}
                            </div>
                          </div>
                        </div>

                        {/* Anxiety Triggers (if any) */}
                        {strands.emotional?.anxiety_triggers?.length > 0 && (
                          <div className="bg-rose-50 border border-rose-100 rounded-2xl p-4">
                            <h5 className="text-xs font-bold text-rose-700 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                              <Heart className="w-3.5 h-3.5" /> Sensitivity Notes for Tutor
                            </h5>
                            <p className="text-xs text-rose-600 mb-2">Be mindful of these triggers during sessions:</p>
                            <div className="flex flex-wrap gap-2">
                              {strands.emotional.anxiety_triggers.map((t: string) => (
                                <span key={t} className="text-xs bg-rose-100 text-rose-700 px-2.5 py-1 rounded-full capitalize">
                                  {t.replace(/_/g, ' ')}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Weekly Confidence Trend */}
                        {dna.weekly_trend?.length > 0 && (
                          <div className="bg-white rounded-2xl border border-gray-100 p-5">
                            <h4 className="text-sm font-bold text-gray-800 mb-4 flex items-center gap-2">
                              <TrendingUp className="w-4 h-4 text-[#4ECFBF]" /> Weekly Progress Trend
                            </h4>
                            <div className="space-y-2">
                              {dna.weekly_trend.slice(-6).map((week: any, i: number) => (
                                <div key={week.week} className="flex items-center gap-3">
                                  <span className="text-xs text-gray-400 w-16 flex-shrink-0">
                                    Week {week.week}
                                  </span>
                                  <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                                    <div
                                      className="bg-gradient-to-r from-[#4ECFBF] to-purple-400 h-2 rounded-full transition-all duration-700"
                                      style={{
                                        width: `${week.confidence}%`,
                                        animationDelay: `${i * 150}ms`
                                      }}
                                    />
                                  </div>
                                  <span className="text-xs font-semibold text-[#4ECFBF] w-9 text-right">{week.confidence}%</span>
                                  <span className="text-xs text-gray-400 w-20 text-right hidden sm:block">{week.sessions} sess · {week.minutes}m</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Assessment History */}
                        {dna.assessments?.length > 0 && (
                          <div className="bg-white rounded-2xl border border-gray-100 p-5">
                            <h4 className="text-sm font-bold text-gray-800 mb-4 flex items-center gap-2">
                              <Award className="w-4 h-4 text-[#4ECFBF]" /> Assessment History
                            </h4>
                            <div className="space-y-2">
                              {dna.assessments.map((a: any, i: number) => (
                                <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                                  <div className="flex items-center gap-2 min-w-0 flex-1">
                                    <FlagOrText language={a.language?.toLowerCase()} size={16} />
                                    <span className="text-xs font-semibold text-gray-700 capitalize">{a.language}</span>
                                    <span className={`text-xs px-2 py-0.5 rounded-full border font-semibold ${LEVEL_COLORS[a.level] || 'bg-gray-100 text-gray-600 border-gray-200'}`}>{a.level}</span>
                                  </div>
                                  <div className={`text-lg font-bold flex-shrink-0 ${a.score >= 80 ? 'text-emerald-600' : a.score >= 60 ? 'text-amber-600' : 'text-rose-600'}`}>
                                    {a.score}
                                  </div>
                                  <div className="text-xs text-gray-400 flex-shrink-0 hidden sm:block min-w-0 max-w-[140px] truncate">{a.feedback}</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Sentence Quality Scores */}
                        {dna.sentence_scores?.length > 0 && (
                          <div className="bg-white rounded-2xl border border-gray-100 p-5">
                            <h4 className="text-sm font-bold text-gray-800 mb-4 flex items-center gap-2">
                              <Mic className="w-4 h-4 text-[#4ECFBF]" /> Recent Sentence Quality
                            </h4>
                            <div className="space-y-2">
                              {dna.sentence_scores.slice(0, 5).map((s: any, i: number) => (
                                <div key={i} className="border border-gray-100 rounded-xl p-3">
                                  <p className="text-xs text-gray-600 italic mb-2">"{s.text}"</p>
                                  <div className="grid grid-cols-4 gap-2">
                                    {[
                                      { label: 'Grammar', val: s.grammatical, color: 'text-emerald-600' },
                                      { label: 'Vocab', val: s.vocabulary, color: 'text-purple-600' },
                                      { label: 'Complexity', val: s.complexity, color: 'text-blue-600' },
                                      { label: 'Overall', val: s.overall, color: 'text-[#4ECFBF] font-bold' },
                                    ].map(m => (
                                      <div key={m.label} className="text-center">
                                        <div className={`text-sm font-bold ${m.color}`}>{m.val}</div>
                                        <div className="text-xs text-gray-400">{m.label}</div>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    );
                  })()}
                </div>
              )}

              {/* ── AI INSIGHTS ── */}
              {tab === 'insights' && (
                <div className="space-y-4">
                  {details.ai_insights ? (
                    <>
                      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-100 rounded-2xl p-5">
                        <h4 className="font-semibold text-indigo-900 mb-2 flex items-center gap-1.5"><Bot className="w-4 h-4" /> AI Summary</h4>
                        <p className="text-gray-700 text-sm leading-relaxed">{details.ai_insights.overall_summary}</p>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div className="bg-white border border-gray-100 rounded-2xl p-4">
                          <h5 className="font-semibold text-gray-800 mb-3 text-sm">Learning Style</h5>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between"><span className="text-gray-500">Preferred time</span><span className="font-medium capitalize">{details.ai_insights.learning_style?.preferred_time || '—'}</span></div>
                            <div className="flex justify-between"><span className="text-gray-500">Sessions/week</span><span className="font-medium">{details.ai_insights.learning_style?.sessions_per_week || '—'}</span></div>
                          </div>
                        </div>
                        <div className="bg-white border border-gray-100 rounded-2xl p-4">
                          <h5 className="font-semibold text-gray-800 mb-3 text-sm">Progress Rate</h5>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between"><span className="text-gray-500">Rate</span><span className="font-medium capitalize">{details.ai_insights.progress_rate?.rate || '—'}</span></div>
                            <div className="flex justify-between"><span className="text-gray-500">Status</span><span className="font-medium capitalize">{details.ai_insights.progress_rate?.description || '—'}</span></div>
                          </div>
                        </div>
                      </div>
                      {details.ai_insights.recommendations?.length > 0 && (
                        <div className="bg-amber-50 border border-amber-100 rounded-2xl p-5">
                          <h5 className="font-semibold text-amber-900 mb-3 flex items-center gap-1.5"><Lightbulb className="w-4 h-4 text-amber-500 inline mr-1.5" /> Recommendations for You</h5>
                          <ul className="space-y-2">
                            {details.ai_insights.recommendations.map((r: string, i: number) => (
                              <li key={i} className="text-sm text-gray-700 flex gap-2"><span className="text-amber-500 font-bold">{i + 1}.</span>{r}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="text-center py-12 text-gray-400"><Bot className="w-12 h-12 text-gray-300 mx-auto mb-2" />No AI insights available yet</div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// Mini bar chart for level distribution
// ─────────────────────────────────────────────
function LevelChart({ distribution, total }: { distribution: Record<string, number>; total: number }) {
  const LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];
  const max = Math.max(...Object.values(distribution), 1);
  return (
    <div className="flex items-end gap-2 h-20">
      {LEVELS.map(lvl => {
        const count = distribution[lvl] || 0;
        const pct = (count / max) * 100;
        return (
          <div key={lvl} className="flex-1 flex flex-col items-center gap-1">
            <span className="text-xs font-bold text-gray-600">{count > 0 ? count : ''}</span>
            <div className="w-full relative flex items-end" style={{ height: 48 }}>
              <div
                className={`w-full rounded-t-md transition-all ${LEVEL_BAR_COLORS[lvl] || 'bg-gray-300'}`}
                style={{ height: `${Math.max(pct, count > 0 ? 8 : 0)}%` }}
              />
            </div>
            <span className="text-xs font-semibold text-gray-500">{lvl}</span>
          </div>
        );
      })}
    </div>
  );
}

// ─────────────────────────────────────────────
// Main Dashboard
// ─────────────────────────────────────────────
export default function TutorDashboardPage() {
  const router = useRouter();
  const params = useParams();
  const tutorId = params.tutorId as string;

  const [tutorName, setTutorName] = useState('');
  const [learners, setLearners] = useState<Learner[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'overview' | 'learners'>('overview');
  const [search, setSearch] = useState('');
  const [langFilter, setLangFilter] = useState('');
  const [levelFilter, setLevelFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedLearner, setSelectedLearner] = useState<Learner | null>(null);
  const [learnerDetails, setLearnerDetails] = useState<any>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [hoveredLearner, setHoveredLearner] = useState<Learner | null>(null);
  const [hoverPos, setHoverPos] = useState({ x: 0, y: 0 });
  const hoverTimer = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchData = useCallback(async (token: string, opts?: { lang?: string; level?: string; status?: string; q?: string }) => {
    setLoading(true);
    try {
      const qs = new URLSearchParams();
      const l = opts?.lang ?? langFilter;
      const lv = opts?.level ?? levelFilter;
      const s = opts?.status ?? statusFilter;
      const q = opts?.q ?? search;
      if (l) qs.set('language', l);
      if (lv) qs.set('level', lv);
      if (s) qs.set('status', s);
      if (q) qs.set('search', q);
      qs.set('per_page', '50');

      const [learnersRes, analyticsRes] = await Promise.all([
        fetch(`${API_BASE_URL}/tutor/dashboard/${tutorId}/learners?${qs}`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_BASE_URL}/tutor/dashboard/${tutorId}/analytics`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);

      if (learnersRes.status === 401) { router.push('/tutor/login'); return; }
      if (learnersRes.ok) { const d = await learnersRes.json(); setLearners(d.learners || []); }
      if (analyticsRes.ok) { const d = await analyticsRes.json(); setAnalytics(d); }
    } finally {
      setLoading(false);
    }
  }, [tutorId, router]); // no filter deps — filters passed as args to avoid stale closure re-fetches

  // Initial load — runs once per tutorId
  useEffect(() => {
    const token = localStorage.getItem('tutorToken');
    const storedId = localStorage.getItem('tutorId');
    if (!token || storedId !== tutorId) { router.push('/tutor/login'); return; }
    setTutorName(localStorage.getItem('tutorName') || 'Tutor');
    fetchData(token);
  }, [tutorId, router]); // fetchData intentionally omitted — stable after mount

  // Re-fetch when filters change, debounced
  useEffect(() => {
    const token = localStorage.getItem('tutorToken');
    if (!token) return;
    const t = setTimeout(() => fetchData(token, { lang: langFilter, level: levelFilter, status: statusFilter, q: search }), 300);
    return () => clearTimeout(t);
  }, [langFilter, levelFilter, statusFilter, search]); // eslint-disable-line

  const openLearnerDetails = async (learner: Learner) => {
    setSelectedLearner(learner);
    setLoadingDetails(true);
    setLearnerDetails(null);
    const token = localStorage.getItem('tutorToken');
    try {
      const res = await fetch(
        `${API_BASE_URL}/tutor/dashboard/${tutorId}/learner/${learner.user_id}/details`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) setLearnerDetails(await res.json());
    } finally {
      setLoadingDetails(false);
    }
  };

  const hasFilters = search || langFilter || levelFilter || statusFilter;
  const uniqueLanguages = Array.from(new Set(learners.flatMap(l => l.learning_plans.map(p => p.language)).filter(Boolean)));

  // Compute language distribution from actual learners (not stale analytics)
  const langDistribution = learners.reduce((acc, l) => {
    const lang = l.learning_plans[0]?.language?.toLowerCase();
    if (lang) acc[lang] = (acc[lang] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="min-h-screen bg-slate-50 pt-20 font-nunito">
      {/* Tab Bar — flush under global teal navbar, same style as institution dashboard */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <nav className="flex overflow-x-auto">
            {[
              { key: 'overview', label: 'Overview', icon: <BarChart2 className="w-4 h-4 inline-block mr-1.5" /> },
              { key: 'learners', label: `Learners${analytics ? ` (${analytics.total_assigned_learners})` : ''}`, icon: <GraduationCap className="w-4 h-4 inline-block mr-1.5" /> },
            ].map(t => (
              <button
                key={t.key}
                onClick={() => setTab(t.key as any)}
                className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors whitespace-nowrap flex items-center ${
                  tab === t.key
                    ? 'border-[#4ECFBF] text-[#4ECFBF]'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-200'
                }`}
              >
                {t.icon}{t.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">

        {/* ═══════════════ OVERVIEW TAB ═══════════════ */}
        {tab === 'overview' && loading && !analytics && (
          <div className="space-y-6">
            <CardLoadingSkeleton cards={4} />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {[1,2].map(i => (
                <div key={i} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 animate-pulse">
                  <div className="h-4 w-24 bg-gray-100 rounded-full mb-4" />
                  <div className="space-y-3">{[1,2,3].map(j => <div key={j} className="h-6 bg-gray-100 rounded-lg" style={{opacity: 1-j*0.2}} />)}</div>
                </div>
              ))}
            </div>
          </div>
        )}
        {tab === 'overview' && (!loading || analytics) && (
          <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
              {[
                { label: 'Total Learners', value: analytics?.total_assigned_learners ?? 0, color: 'text-gray-900', icon: <Users className="w-5 h-5 text-blue-400" />, bg: 'bg-white' },
                { label: 'On Track', value: analytics?.active_learners ?? 0, color: 'text-emerald-600', icon: <CheckCircle className="w-5 h-5 text-emerald-500" />, bg: 'bg-emerald-50' },
                { label: 'Need Attention', value: (analytics?.at_risk_learners ?? 0) + (analytics?.inactive_learners ?? 0), color: 'text-amber-600', icon: <AlertTriangle className="w-5 h-5 text-amber-500" />, bg: 'bg-amber-50' },
                { label: 'Avg Progress', value: `${analytics?.average_progress?.toFixed(1) ?? 0}%`, color: 'text-[#4ECFBF]', icon: <TrendingUp className="w-5 h-5 text-[#4ECFBF]" />, bg: 'bg-teal-50' },
              ].map(card => (
                <div key={card.label} className={`${card.bg} rounded-2xl border border-gray-100 p-5 shadow-sm`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{card.label}</span>
                    <span>{card.icon}</span>
                  </div>
                  <div className={`text-3xl font-bold ${card.color}`}>{card.value}</div>
                </div>
              ))}
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-5">
              {/* Language Distribution */}
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Globe className="w-4 h-4 text-[#4ECFBF]" /> <span>Languages</span>
                  <span className="text-xs text-gray-400 font-normal ml-auto">{Object.keys(langDistribution).length} language{Object.keys(langDistribution).length !== 1 ? 's' : ''}</span>
                </h3>
                {Object.keys(langDistribution).length > 0 ? (
                  <div className="space-y-3">
                    {Object.entries(langDistribution)
                      .sort(([, a], [, b]) => b - a)
                      .map(([lang, count]) => {
                        const total = Object.values(langDistribution).reduce((a, b) => a + b, 0);
                        const pct = Math.round((count / total) * 100);
                        return (
                          <div key={lang}>
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-sm font-medium text-gray-700 flex items-center gap-1.5">
                                <FlagOrText language={lang} size={18} /> <span>{lang ? lang.charAt(0).toUpperCase()+lang.slice(1) : '—'}</span>
                              </span>
                              <span className="text-sm text-gray-500">{count} learner{count !== 1 ? 's' : ''} · {pct}%</span>
                            </div>
                            <div className="w-full bg-gray-100 rounded-full h-2">
                              <div className="bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] h-2 rounded-full" style={{ width: `${pct}%` }} />
                            </div>
                          </div>
                        );
                      })}
                  </div>
                ) : (
                  <div className="text-sm text-gray-400 text-center py-8">No learners with language plans yet</div>
                )}
              </div>

              {/* Proficiency Level Distribution */}
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <BarChart2 className="w-4 h-4 text-[#4ECFBF]" /> <span>Proficiency Levels</span>
                  <span className="text-xs text-gray-400 font-normal ml-auto">{analytics?.total_assigned_learners ?? 0} total</span>
                </h3>
                {analytics?.level_distribution && Object.keys(analytics.level_distribution).length > 0 ? (
                  <>
                    <LevelChart distribution={analytics.level_distribution} total={analytics.total_assigned_learners} />
                    <div className="flex flex-wrap gap-2 mt-4">
                      {Object.entries(analytics.level_distribution).sort(([a], [b]) => {
                        const order = ['A1','A2','B1','B2','C1','C2'];
                        return order.indexOf(a) - order.indexOf(b);
                      }).map(([lvl, count]) => (
                        <span key={lvl} className={`text-xs px-2.5 py-1 rounded-full border font-semibold ${LEVEL_COLORS[lvl] || 'bg-gray-100 text-gray-600 border-gray-200'}`}>
                          {lvl}: {count}
                        </span>
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="text-sm text-gray-400 text-center py-8">No level data available</div>
                )}
              </div>
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-5">
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2"><Activity className="w-4 h-4 text-[#4ECFBF]" /> Class Stats</h3>
                <div className="space-y-3">
                  {[
                    { label: 'Total Sessions Completed', value: analytics?.total_sessions_completed ?? 0 },
                    { label: 'Total Minutes Practiced', value: `${Math.round(analytics?.total_minutes_practiced ?? 0)} min` },
                    { label: 'Languages Taught', value: analytics?.languages_taught?.join(', ') || '—' },
                  ].map(row => (
                    <div key={row.label} className="flex justify-between items-center py-2 border-b border-gray-50 last:border-0">
                      <span className="text-sm text-gray-500">{row.label}</span>
                      <span className="text-sm font-semibold text-gray-900 capitalize">{row.value}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Quick Learner Summary */}
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2"><GraduationCap className="w-4 h-4 text-[#4ECFBF]" /> Learner Snapshot</h3>
                <div className="space-y-2">
                  {learners.slice(0, 5).map(l => {
                    const plan = l.learning_plans[0];
                    return (
                      <div key={l.user_id} className="flex items-center gap-3 p-2 rounded-xl hover:bg-gray-50 cursor-pointer transition-colors" onClick={() => { setTab('learners'); }}>
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold ${
                          plan?.progress_status === 'on_track' ? 'bg-emerald-400' :
                          plan?.progress_status === 'at_risk' ? 'bg-amber-400' : 'bg-gray-300'
                        }`}>{l.name.charAt(0)}</div>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-gray-800 truncate">{l.name}</div>
                          {plan && <div className="text-xs text-gray-400 flex items-center gap-1"><FlagOrText language={plan.language} size={14} />{plan.language ? plan.language.charAt(0).toUpperCase()+plan.language.slice(1) : ''} · {plan.proficiency_level}</div>}
                        </div>
                        {plan && (
                          <div className="text-right">
                            <div className="text-sm font-bold text-[#4ECFBF]">{plan.progress_percentage.toFixed(0)}%</div>
                            <div className="w-14 bg-gray-100 rounded-full h-1.5 mt-1">
                              <div className="bg-[#4ECFBF] h-1.5 rounded-full" style={{ width: `${plan.progress_percentage}%` }} />
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                  {learners.length > 5 && (
                    <button onClick={() => setTab('learners')} className="text-xs text-[#4ECFBF] hover:underline w-full text-center pt-1">
                      View all {learners.length} learners →
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ═══════════════ LEARNERS TAB ═══════════════ */}
        {tab === 'learners' && (
          <div className="space-y-5">
            {/* Filters */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                <div>
                  <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5 block">Search</label>
                  <input
                    value={search} onChange={e => setSearch(e.target.value)}
                    placeholder="Name or email..."
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-[#4ECFBF] bg-white"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5 block">Language</label>
                  <select value={langFilter} onChange={e => setLangFilter(e.target.value)} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-[#4ECFBF]">
                    <option value="">All Languages</option>
                    {uniqueLanguages.map(l => <option key={l} value={l}>{l ? l.charAt(0).toUpperCase() + l.slice(1) : l}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5 block">Level</label>
                  <select value={levelFilter} onChange={e => setLevelFilter(e.target.value)} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-[#4ECFBF]">
                    <option value="">All Levels</option>
                    {['A1','A2','B1','B2','C1','C2'].map(l => <option key={l}>{l}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5 block">Status</label>
                  <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-[#4ECFBF]">
                    <option value="">All Status</option>
                    <option value="on_track">On Track</option>
                    <option value="at_risk">At Risk</option>
                    <option value="inactive">Inactive</option>
                  </select>
                </div>
                {hasFilters && (
                  <button onClick={() => { setSearch(''); setLangFilter(''); setLevelFilter(''); setStatusFilter(''); }} className="sm:col-span-2 lg:col-span-4 px-3 py-2 text-sm text-gray-500 hover:text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl transition-colors w-fit">
                    ✕ Clear
                  </button>
                )}
              </div>
            </div>

            {/* Learner Table */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
              {loading ? (
                <TableLoadingSkeleton rows={4} cols={8} />
              ) : learners.length === 0 ? (
                <div className="text-center py-16">
                  <GraduationCap className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                  <p className="text-gray-500 font-medium">No learners found</p>
                  {hasFilters && <p className="text-gray-400 text-sm mt-1">Try clearing your filters</p>}
                </div>
              ) : (
                <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-100 bg-gray-50/80">
                      {['Learner', 'Language & Level', 'Progress', 'Sessions', 'Score', 'Last Active', 'Status', ''].map(h => (
                        <th key={h} className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {learners.map(learner => {
                      const plan = learner.learning_plans[0];
                      const statusColors = {
                        on_track: { dot: 'bg-emerald-400', badge: 'bg-emerald-50 text-emerald-700 border-emerald-100', label: 'On Track' },
                        at_risk: { dot: 'bg-amber-400', badge: 'bg-amber-50 text-amber-700 border-amber-100', label: 'At Risk' },
                        inactive: { dot: 'bg-gray-300', badge: 'bg-gray-50 text-gray-500 border-gray-100', label: 'Inactive' },
                      };
                      const status = statusColors[plan?.progress_status as keyof typeof statusColors] || statusColors.inactive;

                      return (
                        <tr
                          key={learner.user_id}
                          className="hover:bg-slate-50/80 transition-colors cursor-default"
                          onMouseEnter={e => {
                            const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
                            if (hoverTimer.current) clearTimeout(hoverTimer.current);
                            hoverTimer.current = setTimeout(() => {
                              setHoveredLearner(learner);
                              setHoverPos({ x: rect.right - 20, y: rect.top });
                            }, 300);
                          }}
                          onMouseLeave={() => {
                            if (hoverTimer.current) clearTimeout(hoverTimer.current);
                            setHoveredLearner(null);
                          }}
                        >
                          {/* Learner */}
                          <td className="px-3 py-3">
                            <div className="flex items-center gap-3">
                              <div className={`w-9 h-9 rounded-xl flex items-center justify-center text-white font-bold text-sm flex-shrink-0 ${status.dot === 'bg-emerald-400' ? 'bg-emerald-400' : status.dot === 'bg-amber-400' ? 'bg-amber-400' : 'bg-gray-300'}`}>
                                {learner.name.charAt(0)}
                              </div>
                              <div className="min-w-0">
                                <div className="font-semibold text-gray-900 text-sm truncate max-w-[120px] md:max-w-[160px]">{learner.name}</div>
                                <div className="text-xs text-gray-400 truncate max-w-[120px] md:max-w-[160px]">{learner.email}</div>
                              </div>
                            </div>
                          </td>

                          {/* Language & Level */}
                          <td className="px-3 py-3">
                            {plan ? (
                              <div className="flex items-center gap-2">
                                <FlagOrText language={plan.language} size={22} />
                                <div>
                                  <div className="text-sm font-medium text-gray-800">{plan.language ? plan.language.charAt(0).toUpperCase() + plan.language.slice(1) : '—'}</div>
                                  <span className={`text-xs px-2 py-0.5 rounded-full border font-semibold ${LEVEL_COLORS[plan.proficiency_level] || 'bg-gray-100 text-gray-600 border-gray-200'}`}>
                                    {plan.proficiency_level}
                                  </span>
                                </div>
                              </div>
                            ) : <span className="text-xs text-gray-300">No plan</span>}
                          </td>

                          {/* Progress */}
                          <td className="px-3 py-3">
                            {plan ? (
                              <div className="w-32">
                                <div className="flex justify-between text-xs mb-1.5">
                                  <span className="text-gray-400">{plan.completed_sessions}/{plan.total_sessions}</span>
                                  <span className="font-bold text-gray-800">{plan.progress_percentage.toFixed(0)}%</span>
                                </div>
                                <div className="w-full bg-gray-100 rounded-full h-2">
                                  <div
                                    className={`h-2 rounded-full ${plan.progress_status === 'on_track' ? 'bg-emerald-400' : plan.progress_status === 'at_risk' ? 'bg-amber-400' : 'bg-gray-300'}`}
                                    style={{ width: `${plan.progress_percentage}%` }}
                                  />
                                </div>
                              </div>
                            ) : <span className="text-xs text-gray-300">—</span>}
                          </td>

                          {/* Sessions */}
                          <td className="px-2 py-3 text-center">
                            {plan ? (
                              <div>
                                <div className="text-xl font-bold text-[#4ECFBF]">{plan.completed_sessions}</div>
                                <div className="text-xs text-gray-400">of {plan.total_sessions}</div>
                              </div>
                            ) : '—'}
                          </td>

                          {/* Score */}
                          <td className="px-2 py-3 text-center">
                            {plan?.assessment_score > 0 ? (
                              <div className={`text-xl font-bold ${plan.assessment_score >= 80 ? 'text-emerald-600' : plan.assessment_score >= 60 ? 'text-amber-600' : 'text-rose-600'}`}>
                                {plan.assessment_score}
                              </div>
                            ) : <span className="text-gray-300 text-sm">—</span>}
                          </td>

                          {/* Last Active */}
                          <td className="px-3 py-3">
                            {plan?.last_activity_date ? (
                              <div>
                                <div className="text-xs font-medium text-gray-700">{new Date(plan.last_activity_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</div>
                                <div className={`text-xs ${plan.days_since_activity <= 3 ? 'text-emerald-500' : plan.days_since_activity <= 7 ? 'text-amber-500' : 'text-rose-500'}`}>
                                  {plan.days_since_activity < 999 ? `${plan.days_since_activity}d ago` : 'Never'}
                                </div>
                              </div>
                            ) : <span className="text-xs text-gray-300">No activity</span>}
                          </td>

                          {/* Status */}
                          <td className="px-3 py-3">
                            {plan ? (
                              <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${status.badge}`}>
                                <span className={`w-1.5 h-1.5 rounded-full ${status.dot}`} />
                                {status.label}
                              </span>
                            ) : <span className="text-xs text-gray-300">—</span>}
                          </td>

                          {/* Action */}
                          <td className="px-3 py-3">
                            <button
                              onClick={() => openLearnerDetails(learner)}
                              className="px-3 py-1.5 bg-[#4ECFBF] hover:bg-[#3a9e92] active:bg-[#2d8a80] text-white text-xs font-semibold rounded-xl transition-all shadow-sm hover:shadow"
                            >
                              View
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Hover card — zero API calls, uses already-loaded data */}
      {hoveredLearner && <LearnerHoverCard learner={hoveredLearner} position={hoverPos} />}

      {/* Learner Detail Modal */}
      {selectedLearner && (
        <LearnerDetailModal
          learner={selectedLearner}
          details={learnerDetails}
          loading={loadingDetails}
          onClose={() => { setSelectedLearner(null); setLearnerDetails(null); }}
        />
      )}
    </div>
  );
}
