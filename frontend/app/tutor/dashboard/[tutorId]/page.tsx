'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Spinner, ModalSpinner, TableLoadingSkeleton, CardLoadingSkeleton } from '@/src/components/ui/Spinner';

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
const LANG_FLAGS: Record<string, string> = {
  english: '🇬🇧', dutch: '🇳🇱', spanish: '🇪🇸',
  french: '🇫🇷', german: '🇩🇪', portuguese: '🇧🇷',
  italian: '🇮🇹', turkish: '🇹🇷',
};

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
// Learner Detail Modal
// ─────────────────────────────────────────────
function LearnerDetailModal({
  learner, details, loading, onClose,
}: { learner: Learner; details: any; loading: boolean; onClose: () => void }) {
  const [tab, setTab] = useState<'overview' | 'plans' | 'sessions' | 'challenges' | 'insights'>('overview');
  const plan = learner.learning_plans[0];

  const tabs = [
    { key: 'overview', label: 'Overview', icon: '📊' },
    { key: 'plans', label: `Plans (${details?.all_learning_plans?.length ?? 0})`, icon: '📚' },
    { key: 'sessions', label: `Sessions (${details?.practice_sessions?.length ?? 0})`, icon: '🎙️' },
    { key: 'challenges', label: `Challenges (${details?.challenge_sessions?.length ?? 0})`, icon: '⚡' },
    { key: 'insights', label: 'AI Insights', icon: '🤖' },
  ] as const;

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
                <div className="flex items-center gap-2 mt-1.5">
                  <span className="bg-white/20 text-white text-xs font-semibold px-2.5 py-0.5 rounded-full capitalize">
                    {LANG_FLAGS[plan.language?.toLowerCase()] || '🌍'} {plan.language}
                  </span>
                  <span className="bg-white/20 text-white text-xs font-semibold px-2.5 py-0.5 rounded-full">
                    {plan.proficiency_level}
                  </span>
                  <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${
                    plan.progress_status === 'on_track' ? 'bg-green-400/30 text-white' :
                    plan.progress_status === 'at_risk' ? 'bg-yellow-400/30 text-white' :
                    'bg-gray-400/30 text-white'
                  }`}>
                    {plan.progress_status === 'on_track' ? '✅ On Track' : plan.progress_status === 'at_risk' ? '⚠️ At Risk' : '⏸ Inactive'}
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
              className={`py-3.5 px-4 text-sm font-medium border-b-2 transition-all whitespace-nowrap ${
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
              {tab === 'overview' && (
                <div className="space-y-5">
                  {/* Streak / XP / Days */}
                  {details.daily_stats && (
                    <div className="grid grid-cols-3 gap-3 sm:gap-4">
                      <div className="bg-gradient-to-br from-orange-50 to-amber-50 border border-orange-100 rounded-2xl p-4 text-center">
                        <div className="text-3xl mb-1">🔥</div>
                        <div className="text-2xl font-bold text-orange-600">{details.daily_stats.current_streak ?? 0}</div>
                        <div className="text-xs text-gray-500">Day Streak</div>
                      </div>
                      <div className="bg-gradient-to-br from-yellow-50 to-amber-50 border border-yellow-100 rounded-2xl p-4 text-center">
                        <div className="text-3xl mb-1">⭐</div>
                        <div className="text-2xl font-bold text-yellow-600">{details.daily_stats.total_xp ?? 0}</div>
                        <div className="text-xs text-gray-500">Total XP</div>
                      </div>
                      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100 rounded-2xl p-4 text-center">
                        <div className="text-3xl mb-1">📅</div>
                        <div className="text-2xl font-bold text-blue-600">{details.daily_stats.days_active ?? 0}</div>
                        <div className="text-xs text-gray-500">Active Days</div>
                      </div>
                    </div>
                  )}

                  {/* Learning Plans Progress */}
                  {details.all_learning_plans?.length > 0 && (
                    <div className="bg-gray-50 rounded-2xl p-5">
                      <h4 className="font-semibold text-gray-900 mb-4">Language Progress</h4>
                      <div className="space-y-4">
                        {details.all_learning_plans.map((p: any) => (
                          <div key={p.id}>
                            <div className="flex items-center justify-between mb-1.5">
                              <div className="flex items-center gap-2">
                                <span>{LANG_FLAGS[p.language?.toLowerCase()] || '🌍'}</span>
                                <span className="font-medium text-gray-800 capitalize text-sm">{p.language}</span>
                                <span className={`text-xs px-2 py-0.5 rounded-full border font-semibold ${LEVEL_COLORS[p.proficiency_level] || 'bg-gray-100 text-gray-600 border-gray-200'}`}>
                                  {p.proficiency_level}
                                </span>
                              </div>
                              <div className="text-right">
                                <span className="text-sm font-bold text-gray-900">{p.progress_percentage?.toFixed(0)}%</span>
                                <span className="text-xs text-gray-400 ml-1">({p.completed_sessions}/{p.total_sessions})</span>
                              </div>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2.5">
                              <div
                                className="bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] h-2.5 rounded-full transition-all"
                                style={{ width: `${Math.min(100, p.progress_percentage || 0)}%` }}
                              />
                            </div>
                            <div className="flex justify-between text-xs text-gray-400 mt-1">
                              <span>{p.practice_minutes_used} min practiced</span>
                              <span>{p.total_practice_minutes} min total</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recent Daily Activity */}
                  {details.daily_stats?.recent_daily?.length > 0 && (
                    <div className="bg-gray-50 rounded-2xl p-5">
                      <h4 className="font-semibold text-gray-900 mb-4">Recent Activity (14 days)</h4>
                      <div className="space-y-2">
                        {details.daily_stats.recent_daily.filter((d: any) => d.minutes > 0 || d.sessions > 0).slice(0, 7).map((day: any) => (
                          <div key={day.date} className="flex items-center gap-3">
                            <span className="text-xs text-gray-400 w-16">{new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                            <div className="flex-1 bg-gray-200 rounded-full h-2">
                              <div className="bg-[#4ECFBF] h-2 rounded-full" style={{ width: `${Math.min(100, (day.minutes / 30) * 100)}%` }} />
                            </div>
                            <span className="text-xs text-[#4ECFBF] font-semibold w-12 text-right">{day.minutes}m</span>
                            {day.xp > 0 && <span className="text-xs text-yellow-500 w-14">+{day.xp} XP</span>}
                          </div>
                        ))}
                        {details.daily_stats.recent_daily.filter((d: any) => d.minutes > 0 || d.sessions > 0).length === 0 && (
                          <p className="text-sm text-gray-400">No activity in the last 14 days</p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* ── PLANS ── */}
              {tab === 'plans' && (
                <div className="space-y-4">
                  {details.all_learning_plans?.length > 0 ? details.all_learning_plans.map((p: any) => (
                    <div key={p.id} className="border border-gray-100 rounded-2xl overflow-hidden">
                      <div className="p-5 bg-gradient-to-r from-emerald-50 to-teal-50">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <span className="text-xl">{LANG_FLAGS[p.language?.toLowerCase()] || '🌍'}</span>
                            <span className="font-bold text-gray-900 capitalize">{p.language}</span>
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
                            <p className="text-xs font-semibold text-green-700 mb-2">✅ Strengths</p>
                            {p.assessment_data.strengths.slice(0, 3).map((s: string, i: number) => (
                              <div key={i} className="text-xs text-gray-600 bg-green-50 rounded-lg px-3 py-1.5 mb-1">{s}</div>
                            ))}
                          </div>
                          <div>
                            <p className="text-xs font-semibold text-amber-700 mb-2">🎯 Areas to Improve</p>
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
                    <div className="text-center py-12 text-gray-400"><div className="text-4xl mb-2">📚</div>No learning plans yet</div>
                  )}
                </div>
              )}

              {/* ── SESSIONS ── */}
              {tab === 'sessions' && (
                <div>
                  {details.practice_sessions?.length > 0 ? (
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
                        {details.practice_sessions.map((s: any) => (
                          <tr key={s.id} className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-gray-700">{s.created_at ? new Date(s.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '—'}</td>
                            <td className="px-4 py-3 capitalize text-gray-700">{LANG_FLAGS[s.language?.toLowerCase()] || ''} {s.language || '—'}</td>
                            <td className="px-4 py-3">
                              {s.level ? <span className={`text-xs px-2 py-0.5 rounded-full border font-semibold ${LEVEL_COLORS[s.level] || 'bg-gray-100 text-gray-600 border-gray-200'}`}>{s.level}</span> : '—'}
                            </td>
                            <td className="px-4 py-3 text-center font-medium text-gray-800">{s.duration_minutes}m</td>
                            <td className="px-4 py-3 text-center text-xs text-gray-500 capitalize">{s.session_type?.replace('_', ' ') || 'practice'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    </div>
                  ) : (
                    <div className="text-center py-12 text-gray-400"><div className="text-4xl mb-2">🎙️</div>No practice sessions yet</div>
                  )}
                </div>
              )}

              {/* ── CHALLENGES ── */}
              {tab === 'challenges' && (
                <div>
                  {details.challenge_sessions?.length > 0 ? (
                    <>
                      {/* Summary row */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                        {[
                          { label: 'Total Done', value: details.challenge_sessions.length, color: 'text-[#4ECFBF]' },
                          { label: 'Correct', value: details.challenge_sessions.reduce((s: number, c: any) => s + (c.correct_answers || 0), 0), color: 'text-emerald-600' },
                          { label: 'Total XP', value: details.challenge_sessions.reduce((s: number, c: any) => s + (c.total_xp || 0), 0), color: 'text-yellow-600' },
                          { label: 'Avg Accuracy', value: `${Math.round(details.challenge_sessions.reduce((s: number, c: any) => s + (c.accuracy || 0), 0) / details.challenge_sessions.length)}%`, color: 'text-blue-600' },
                        ].map(stat => (
                          <div key={stat.label} className="bg-gray-50 rounded-xl p-3 text-center">
                            <div className={`text-xl font-bold ${stat.color}`}>{stat.value}</div>
                            <div className="text-xs text-gray-500 mt-0.5">{stat.label}</div>
                          </div>
                        ))}
                      </div>
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
                          {details.challenge_sessions.map((c: any) => (
                            <tr key={c.id} className="hover:bg-gray-50">
                              <td className="px-4 py-3 text-gray-600 text-xs">{c.created_at ? new Date(c.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '—'}</td>
                              <td className="px-4 py-3 text-xs text-gray-700 capitalize">{c.challenge_type?.replace(/_/g, ' ') || '—'}</td>
                              <td className="px-4 py-3 capitalize text-gray-700 text-xs">{c.language || '—'}</td>
                              <td className="px-4 py-3 text-center font-bold text-gray-800">
                                {c.total_challenges > 0
                                  ? <span>{c.correct_answers}<span className="text-gray-400 font-normal">/{c.total_challenges}</span></span>
                                  : c.correct_answers > 0 ? c.correct_answers : '—'}
                              </td>
                              <td className="px-4 py-3 text-center">
                                {c.accuracy > 0 ? (
                                  <span className={`font-bold text-sm ${c.accuracy >= 80 ? 'text-emerald-600' : c.accuracy >= 60 ? 'text-amber-600' : 'text-rose-600'}`}>
                                    {Math.round(c.accuracy)}%
                                  </span>
                                ) : '—'}
                              </td>
                              <td className="px-4 py-3 text-center text-xs font-semibold text-yellow-600">
                                {c.total_xp > 0 ? `+${c.total_xp}` : '—'}
                              </td>
                              <td className="px-4 py-3 text-center text-xs text-gray-500">
                                {c.max_combo > 0 ? `🔥 ${c.max_combo}` : '—'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      </div>
                    </>
                  ) : (
                    <div className="text-center py-12 text-gray-400"><div className="text-4xl mb-2">⚡</div>No challenges completed yet</div>
                  )}
                </div>
              )}

              {/* ── AI INSIGHTS ── */}
              {tab === 'insights' && (
                <div className="space-y-4">
                  {details.ai_insights ? (
                    <>
                      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-100 rounded-2xl p-5">
                        <h4 className="font-semibold text-indigo-900 mb-2">🤖 AI Summary</h4>
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
                          <h5 className="font-semibold text-amber-900 mb-3">💡 Recommendations for You</h5>
                          <ul className="space-y-2">
                            {details.ai_insights.recommendations.map((r: string, i: number) => (
                              <li key={i} className="text-sm text-gray-700 flex gap-2"><span className="text-amber-500 font-bold">{i + 1}.</span>{r}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="text-center py-12 text-gray-400"><div className="text-4xl mb-2">🤖</div>No AI insights available yet</div>
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
    <div className="min-h-screen bg-slate-50 pt-16">
      {/* Top Nav */}
      <nav className="bg-white border-b border-gray-200 fixed top-0 left-0 right-0 z-30 shadow-sm h-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-gradient-to-br from-[#4ECFBF] to-[#3a9e92] rounded-xl flex items-center justify-center text-white font-bold text-sm">
              {tutorName.charAt(0)}
            </div>
            <div>
              <span className="font-semibold text-gray-900 text-sm">{tutorName}</span>
              <span className="text-gray-400 text-xs block -mt-0.5">Tutor Dashboard</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-400 bg-gray-100 px-3 py-1.5 rounded-full font-medium">
              {analytics?.total_assigned_learners ?? 0} learners
            </span>
            <button
              onClick={() => { ['tutorToken','tutorId','tutorName','tutorEmail','institutionId'].forEach(k => localStorage.removeItem(k)); router.push('/tutor/login'); }}
              className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>
      </nav>

      {/* Tab Bar — matches institution dashboard style */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <nav className="flex overflow-x-auto">
            {[
              { key: 'overview', label: 'Overview', icon: '📊' },
              { key: 'learners', label: `Learners${analytics ? ` (${analytics.total_assigned_learners})` : ''}`, icon: '🎓' },
            ].map(t => (
              <button
                key={t.key}
                onClick={() => setTab(t.key as any)}
                className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  tab === t.key
                    ? 'border-[#4ECFBF] text-[#4ECFBF]'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-200'
                }`}
              >
                {t.icon} {t.label}
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
                { label: 'Total Learners', value: analytics?.total_assigned_learners ?? 0, color: 'text-gray-900', icon: '👥', bg: 'bg-white' },
                { label: 'On Track', value: analytics?.active_learners ?? 0, color: 'text-emerald-600', icon: '✅', bg: 'bg-emerald-50' },
                { label: 'Need Attention', value: (analytics?.at_risk_learners ?? 0) + (analytics?.inactive_learners ?? 0), color: 'text-amber-600', icon: '⚠️', bg: 'bg-amber-50' },
                { label: 'Avg Progress', value: `${analytics?.average_progress?.toFixed(1) ?? 0}%`, color: 'text-[#4ECFBF]', icon: '📈', bg: 'bg-teal-50' },
              ].map(card => (
                <div key={card.label} className={`${card.bg} rounded-2xl border border-gray-100 p-5 shadow-sm`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{card.label}</span>
                    <span className="text-xl">{card.icon}</span>
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
                  🌍 <span>Languages</span>
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
                                {LANG_FLAGS[lang] || '🌍'} <span className="capitalize">{lang}</span>
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
                  📊 <span>Proficiency Levels</span>
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
                <h3 className="font-semibold text-gray-900 mb-4">📈 Class Stats</h3>
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
                <h3 className="font-semibold text-gray-900 mb-4">🎓 Learner Snapshot</h3>
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
                          {plan && <div className="text-xs text-gray-400 capitalize">{LANG_FLAGS[plan.language?.toLowerCase()] || ''} {plan.language} · {plan.proficiency_level}</div>}
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
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 items-end">
                <div className="flex-1">
                  <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5 block">Search</label>
                  <input
                    value={search} onChange={e => setSearch(e.target.value)}
                    placeholder="Name or email..."
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#4ECFBF] bg-gray-50"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5 block">Language</label>
                  <select value={langFilter} onChange={e => setLangFilter(e.target.value)} className="border border-gray-200 rounded-xl px-3 py-2 text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#4ECFBF]">
                    <option value="">All Languages</option>
                    {uniqueLanguages.map(l => <option key={l} value={l} className="capitalize">{l}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5 block">Level</label>
                  <select value={levelFilter} onChange={e => setLevelFilter(e.target.value)} className="border border-gray-200 rounded-xl px-3 py-2 text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#4ECFBF]">
                    <option value="">All Levels</option>
                    {['A1','A2','B1','B2','C1','C2'].map(l => <option key={l}>{l}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5 block">Status</label>
                  <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="border border-gray-200 rounded-xl px-3 py-2 text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#4ECFBF]">
                    <option value="">All Status</option>
                    <option value="on_track">On Track</option>
                    <option value="at_risk">At Risk</option>
                    <option value="inactive">Inactive</option>
                  </select>
                </div>
                {hasFilters && (
                  <button onClick={() => { setSearch(''); setLangFilter(''); setLevelFilter(''); setStatusFilter(''); }} className="px-3 py-2 text-sm text-gray-500 hover:text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl transition-colors">
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
                  <div className="text-5xl mb-3">🎓</div>
                  <p className="text-gray-500 font-medium">No learners found</p>
                  {hasFilters && <p className="text-gray-400 text-sm mt-1">Try clearing your filters</p>}
                </div>
              ) : (
                <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-100 bg-gray-50/80">
                      {['Learner', 'Language & Level', 'Progress', 'Sessions', 'Score', 'Last Active', 'Status', ''].map(h => (
                        <th key={h} className="px-5 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
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
                        <tr key={learner.user_id} className="hover:bg-slate-50/80 transition-colors group">
                          {/* Learner */}
                          <td className="px-5 py-4">
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
                          <td className="px-5 py-4">
                            {plan ? (
                              <div className="flex items-center gap-2">
                                <span className="text-lg">{LANG_FLAGS[plan.language?.toLowerCase()] || '🌍'}</span>
                                <div>
                                  <div className="text-sm font-medium text-gray-800 capitalize">{plan.language}</div>
                                  <span className={`text-xs px-2 py-0.5 rounded-full border font-semibold ${LEVEL_COLORS[plan.proficiency_level] || 'bg-gray-100 text-gray-600 border-gray-200'}`}>
                                    {plan.proficiency_level}
                                  </span>
                                </div>
                              </div>
                            ) : <span className="text-xs text-gray-300">No plan</span>}
                          </td>

                          {/* Progress */}
                          <td className="px-5 py-4">
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
                          <td className="px-5 py-4 text-center">
                            {plan ? (
                              <div>
                                <div className="text-xl font-bold text-[#4ECFBF]">{plan.completed_sessions}</div>
                                <div className="text-xs text-gray-400">of {plan.total_sessions}</div>
                              </div>
                            ) : '—'}
                          </td>

                          {/* Score */}
                          <td className="px-5 py-4 text-center">
                            {plan?.assessment_score > 0 ? (
                              <div className={`text-xl font-bold ${plan.assessment_score >= 80 ? 'text-emerald-600' : plan.assessment_score >= 60 ? 'text-amber-600' : 'text-rose-600'}`}>
                                {plan.assessment_score}
                              </div>
                            ) : <span className="text-gray-300 text-sm">—</span>}
                          </td>

                          {/* Last Active */}
                          <td className="px-5 py-4">
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
                          <td className="px-5 py-4">
                            {plan ? (
                              <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${status.badge}`}>
                                <span className={`w-1.5 h-1.5 rounded-full ${status.dot}`} />
                                {status.label}
                              </span>
                            ) : <span className="text-xs text-gray-300">—</span>}
                          </td>

                          {/* Action */}
                          <td className="px-5 py-4">
                            <button
                              onClick={() => openLearnerDetails(learner)}
                              className="px-4 py-1.5 bg-[#4ECFBF] hover:bg-[#3a9e92] text-white text-xs font-semibold rounded-xl transition-all opacity-0 group-hover:opacity-100 shadow-sm hover:shadow"
                            >
                              View →
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
