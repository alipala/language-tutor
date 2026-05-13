'use client';

// Institution dashboard API calls go through /api/institution/* proxy
const getApiBaseUrl = () => '/api';

// ── Shared spinner components ──────────────────────────────────────────
function PageSpinner() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="flex flex-col items-center gap-4">
        <div className="relative">
          <div className="w-14 h-14 rounded-full border-4 border-[#4ECFBF]/20" />
          <div className="w-14 h-14 rounded-full border-4 border-transparent border-t-[#4ECFBF] border-r-[#4ECFBF]/60 animate-spin absolute inset-0" style={{ animationDuration: '0.75s' }} />
        </div>
        <p className="text-sm text-gray-400 font-medium animate-pulse">Loading dashboard...</p>
      </div>
    </div>
  );
}

function ModalSpinner({ label = 'Loading details...' }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-14 gap-4">
      <div className="relative">
        <div className="w-14 h-14 rounded-full border-4 border-[#4ECFBF]/15" />
        <div className="w-14 h-14 rounded-full border-4 border-transparent border-t-[#4ECFBF] border-r-[#4ECFBF]/50 animate-spin absolute inset-0" style={{ animationDuration: '0.7s' }} />
        <div className="w-8 h-8 rounded-full border-[3px] border-transparent border-b-[#3a9e92]/60 animate-spin absolute inset-3" style={{ animationDuration: '1.1s', animationDirection: 'reverse' }} />
      </div>
      <p className="text-sm text-gray-400 font-medium">{label}</p>
    </div>
  );
}

function TableSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="p-4 space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-3 items-center animate-pulse" style={{ animationDelay: `${i * 80}ms` }}>
          <div className="w-9 h-9 bg-gray-100 rounded-xl flex-shrink-0" />
          <div className="h-9 bg-gray-100 rounded-lg flex-1" />
          <div className="h-9 bg-gray-100 rounded-lg w-24" />
          <div className="h-9 bg-gray-100 rounded-lg w-20" style={{ opacity: 0.7 }} />
          <div className="h-9 bg-gray-100 rounded-lg w-16" style={{ opacity: 0.5 }} />
        </div>
      ))}
    </div>
  );
}

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { FlagIcon, FlagOrText } from '../../ui/FlagIcon';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';
import {
  BarChart2, Users, UserCheck, GraduationCap, Globe, TrendingUp,
  BookOpen, Mic, Zap, Bot, CheckCircle, AlertTriangle, Clock,
  Upload, Download, Search, Filter, ChevronDown, ChevronUp,
  UserPlus, UserMinus, RefreshCw, Eye, X, MoreHorizontal,
  Award, Activity, Target, Lightbulb, Flame, Star,
  Settings, Building2, User, Lock, Bell, Shield,
  Camera, MapPin, Phone, Link, Calendar, Save, KeyRound
} from 'lucide-react';

// Register ChartJS components
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement);

interface LanguageDistribution {
  language: string;
  count: number;
  percentage: number;
}

interface LevelDistribution {
  level: string;
  count: number;
  percentage: number;
}

interface Tutor {
  id: string;
  name: string;
  email: string;
  bio?: string;
  specializations: string[];
  learner_count: number;
  learners: Learner[];
  permissions: string[];
  is_active: boolean;
}

interface Learner {
  id: string;
  user_id: string;
  name: string;
  email: string;
  language: string | null;
  level: string | null;
  tutor: { id: string; name: string; email: string } | null;
  enrollment_method: string;
  consent_given: boolean;
  enrolled_at: string;
  is_active: boolean;
  progress?: {
    percentage: number;
    completed_sessions: number;
    total_sessions: number;
    category: string;
    color: string;
    emoji: string;
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// ImportModal — drag-drop or click-to-browse, CSV + XLSX, column guide
// ─────────────────────────────────────────────────────────────────────────────
interface ColHint { col: string; hint: string; }
interface ImportModalProps {
  title: string;
  requiredCols: string[];
  optionalCols: string[];
  colHints?: ColHint[];
  warning?: string;
  onClose: () => void;
  onImport: (file: File) => void;
}

const ImportModal: React.FC<ImportModalProps> = ({
  title, requiredCols, optionalCols, colHints = [], warning, onClose, onImport
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [pickedFile, setPickedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const hintMap = Object.fromEntries(colHints.map(h => [h.col, h.hint]));

  const handleFile = useCallback((f: File) => {
    const ok = /\.(csv|xlsx|xls)$/i.test(f.name);
    if (!ok) { alert('Please upload a .csv or .xlsx file'); return; }
    setPickedFile(f);
  }, []);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const handleSubmit = async () => {
    if (!pickedFile) return;
    setIsUploading(true);
    try { await onImport(pickedFile); }
    finally { setIsUploading(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg" onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#4ECFBF]/10 flex items-center justify-center">
              <Upload className="w-5 h-5 text-[#4ECFBF]" />
            </div>
            <h2 className="text-lg font-bold text-gray-900">{title}</h2>
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-lg hover:bg-gray-100 flex items-center justify-center transition-colors">
            <X className="w-4 h-4 text-gray-500" />
          </button>
        </div>

        <div className="px-6 py-5 space-y-4">

          {/* Warning banner */}
          {warning && (
            <div className="flex gap-2.5 bg-amber-50 border border-amber-200 rounded-xl p-3">
              <span className="text-amber-500 mt-0.5 flex-shrink-0">⚠️</span>
              <p className="text-xs text-amber-700 leading-relaxed">{warning}</p>
            </div>
          )}

          {/* Column guide */}
          <div className="bg-gray-50 rounded-xl p-4 space-y-2">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Column Guide</p>
            <div className="space-y-1.5">
              {requiredCols.map(col => (
                <div key={col} className="flex items-start gap-2">
                  <span className="inline-block mt-0.5 w-1.5 h-1.5 rounded-full bg-[#4ECFBF] flex-shrink-0" />
                  <span className="text-xs font-semibold text-gray-700 w-28 flex-shrink-0">{col}</span>
                  <span className="text-xs text-[#4ECFBF] font-medium">required</span>
                  {hintMap[col] && <span className="text-xs text-gray-400 ml-1">— {hintMap[col]}</span>}
                </div>
              ))}
              {optionalCols.map(col => (
                <div key={col} className="flex items-start gap-2">
                  <span className="inline-block mt-0.5 w-1.5 h-1.5 rounded-full bg-gray-300 flex-shrink-0" />
                  <span className="text-xs font-medium text-gray-500 w-28 flex-shrink-0">{col}</span>
                  <span className="text-xs text-gray-400">optional</span>
                  {hintMap[col] && <span className="text-xs text-gray-400 ml-1">— {hintMap[col]}</span>}
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-400 pt-1">Headers are matched case-insensitively. Common variations (e.g. "First Name", "E-mail") are auto-mapped.</p>
          </div>

          {/* Drop zone */}
          <div
            className={`relative border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
              dragging ? 'border-[#4ECFBF] bg-[#4ECFBF]/5' :
              pickedFile ? 'border-[#4ECFBF] bg-[#4ECFBF]/5' :
              'border-gray-200 hover:border-[#4ECFBF]/50 hover:bg-gray-50'
            }`}
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".csv,.xlsx,.xls"
              className="hidden"
              onChange={e => { if (e.target.files?.[0]) handleFile(e.target.files[0]); }}
            />
            {pickedFile ? (
              <div className="flex flex-col items-center gap-1">
                <div className="w-10 h-10 rounded-full bg-[#4ECFBF]/15 flex items-center justify-center mb-1">
                  <CheckCircle className="w-5 h-5 text-[#4ECFBF]" />
                </div>
                <p className="text-sm font-semibold text-gray-800">{pickedFile.name}</p>
                <p className="text-xs text-gray-400">{(pickedFile.size / 1024).toFixed(1)} KB · click to change</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-1">
                <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center mb-1">
                  <Upload className="w-5 h-5 text-gray-400" />
                </div>
                <p className="text-sm font-semibold text-gray-700">Drop file here or click to browse</p>
                <p className="text-xs text-gray-400">CSV or Excel (.xlsx) · UTF-8 encoding recommended</p>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 pb-6 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 border-2 border-gray-200 text-gray-600 rounded-xl hover:bg-gray-50 font-medium text-sm transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!pickedFile || isUploading}
            className="flex-1 py-2.5 bg-[#4ECFBF] text-white rounded-xl hover:bg-[#3a9e92] font-medium text-sm transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isUploading
              ? <><svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/></svg>Importing...</>
              : <><Upload className="w-4 h-4" />Import {pickedFile ? `"${pickedFile.name}"` : ''}</>
            }
          </button>
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// SettingsTab — Institution Profile + Admin Account
// ─────────────────────────────────────────────────────────────────────────────
const TIMEZONES = [
  'UTC','Europe/Amsterdam','Europe/London','Europe/Berlin','Europe/Paris',
  'Europe/Madrid','Europe/Rome','Europe/Istanbul','America/New_York',
  'America/Chicago','America/Denver','America/Los_Angeles','America/Sao_Paulo',
  'Asia/Dubai','Asia/Singapore','Asia/Tokyo','Asia/Shanghai','Australia/Sydney',
];
const ADMIN_LANGUAGES = [
  { value: 'en', label: 'English' },
  { value: 'tr', label: 'Türkçe' },
  { value: 'de', label: 'Deutsch' },
  { value: 'nl', label: 'Nederlands' },
  { value: 'es', label: 'Español' },
  { value: 'fr', label: 'Français' },
  { value: 'pt', label: 'Português' },
];
const INSTITUTION_TYPES = [
  { value: 'school',          label: 'School' },
  { value: 'university',      label: 'University' },
  { value: 'language_center', label: 'Language Center' },
  { value: 'corporate',       label: 'Corporate' },
];

interface SettingsTabProps {
  institutionId: string;
  token: string;
  onNotify: (type: 'success'|'error', title: string, message: string) => void;
}

const SettingsTab: React.FC<SettingsTabProps> = ({ institutionId, token, onNotify }) => {
  const api = '/api';
  const [section, setSection] = useState<'profile'|'admin'>('profile');
  const [loading, setLoading]   = useState(true);
  const [saving, setSaving]     = useState(false);

  // ── Profile state ──────────────────────────────────────────────────────────
  const [profile, setProfile] = useState({
    name: '', institution_type: 'school', website: '', phone: '',
    address: '', logo_url: '', admin_language: 'en',
    timezone: 'UTC', semester_start: '', semester_end: '',
  });

  // ── Admin state ────────────────────────────────────────────────────────────
  const [admin, setAdmin] = useState({
    admin_name: '', admin_email: '', admin_photo_url: '',
    notify_daily_digest: false, notify_weekly_report: true,
    notify_learner_alerts: true, two_factor_enabled: false,
  });
  const [pwForm, setPwForm] = useState({ current: '', next: '', confirm: '' });
  const [pwSaving, setPwSaving]   = useState(false);
  const [activityLog, setActivityLog] = useState<any[]>([]);

  // ── Load ───────────────────────────────────────────────────────────────────
  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const headers = { Authorization: `Bearer ${token}` };
        const [pRes, aRes, lRes] = await Promise.all([
          fetch(`${api}/institution/dashboard/${institutionId}/settings/profile`, { headers }),
          fetch(`${api}/institution/dashboard/${institutionId}/settings/admin`,   { headers }),
          fetch(`${api}/institution/dashboard/${institutionId}/settings/admin/activity-log`, { headers }),
        ]);
        if (pRes.ok) setProfile(await pRes.json());
        if (aRes.ok) setAdmin(await aRes.json());
        if (lRes.ok) { const d = await lRes.json(); setActivityLog(d.entries || []); }
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [institutionId, token]);

  // ── Save profile ───────────────────────────────────────────────────────────
  const saveProfile = async () => {
    setSaving(true);
    try {
      const res = await fetch(`${api}/institution/dashboard/${institutionId}/settings/profile`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(profile),
      });
      if (res.ok) onNotify('success', 'Profile saved', 'Institution profile updated successfully.');
      else { const e = await res.json(); onNotify('error', 'Save failed', e.detail || 'Could not save profile.'); }
    } finally { setSaving(false); }
  };

  // ── Save admin ─────────────────────────────────────────────────────────────
  const saveAdmin = async () => {
    setSaving(true);
    try {
      const res = await fetch(`${api}/institution/dashboard/${institutionId}/settings/admin`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          admin_name: admin.admin_name,
          admin_photo_url: admin.admin_photo_url,
          notify_daily_digest: admin.notify_daily_digest,
          notify_weekly_report: admin.notify_weekly_report,
          notify_learner_alerts: admin.notify_learner_alerts,
          two_factor_enabled: admin.two_factor_enabled,
        }),
      });
      if (res.ok) onNotify('success', 'Settings saved', 'Admin account updated successfully.');
      else { const e = await res.json(); onNotify('error', 'Save failed', e.detail || 'Could not save settings.'); }
    } finally { setSaving(false); }
  };

  // ── Change password ────────────────────────────────────────────────────────
  const changePassword = async () => {
    if (pwForm.next !== pwForm.confirm) { onNotify('error', 'Mismatch', 'New passwords do not match.'); return; }
    if (pwForm.next.length < 8) { onNotify('error', 'Too short', 'Password must be at least 8 characters.'); return; }
    setPwSaving(true);
    try {
      const res = await fetch(`${api}/institution/dashboard/${institutionId}/settings/admin/change-password`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_password: pwForm.current, new_password: pwForm.next }),
      });
      if (res.ok) { onNotify('success', 'Password changed', 'Your password has been updated.'); setPwForm({ current: '', next: '', confirm: '' }); }
      else { const e = await res.json(); onNotify('error', 'Failed', e.detail || 'Could not change password.'); }
    } finally { setPwSaving(false); }
  };

  const btnCls = "flex items-center gap-2 px-5 py-2.5 bg-[#4ECFBF] hover:bg-[#3a9e92] text-white rounded-xl font-semibold text-sm transition-colors disabled:opacity-40";
  const inputCls = "w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent";
  const labelCls = "block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5";
  const cardCls  = "bg-white rounded-2xl shadow-sm border border-gray-100 p-6";

  if (loading) return (
    <div className="flex items-center justify-center py-24">
      <div className="w-10 h-10 border-4 border-[#4ECFBF]/30 border-t-[#4ECFBF] rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Sub-tab navigation */}
      <div className="flex gap-1 bg-gray-100 rounded-xl p-1 w-fit">
        {([
          { key: 'profile', label: 'Institution Profile', icon: Building2 },
          { key: 'admin',   label: 'Admin Account',       icon: User },
        ] as const).map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setSection(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              section === key
                ? 'bg-white text-[#4ECFBF] shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Icon className="w-4 h-4" /> {label}
          </button>
        ))}
      </div>

      {/* ── INSTITUTION PROFILE ─────────────────────────────────────────────── */}
      {section === 'profile' && (
        <div className="space-y-6">
          {/* Basic info */}
          <div className={cardCls}>
            <h3 className="font-bold text-gray-900 mb-5 flex items-center gap-2">
              <Building2 className="w-5 h-5 text-[#4ECFBF]" /> Basic Information
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div className="sm:col-span-2">
                <label className={labelCls}>Institution Name *</label>
                <input className={inputCls} value={profile.name}
                  onChange={e => setProfile(p => ({ ...p, name: e.target.value }))} />
              </div>
              <div>
                <label className={labelCls}>Institution Type</label>
                <select className={inputCls} value={profile.institution_type}
                  onChange={e => setProfile(p => ({ ...p, institution_type: e.target.value }))}>
                  {INSTITUTION_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>
              <div>
                <label className={labelCls}>Logo URL</label>
                <div className="relative">
                  <Camera className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input className={`${inputCls} pl-9`} placeholder="https://..." value={profile.logo_url}
                    onChange={e => setProfile(p => ({ ...p, logo_url: e.target.value }))} />
                </div>
              </div>
            </div>
          </div>

          {/* Contact */}
          <div className={cardCls}>
            <h3 className="font-bold text-gray-900 mb-5 flex items-center gap-2">
              <Phone className="w-5 h-5 text-[#4ECFBF]" /> Contact Details
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label className={labelCls}>Website</label>
                <div className="relative">
                  <Link className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input className={`${inputCls} pl-9`} placeholder="https://..." value={profile.website}
                    onChange={e => setProfile(p => ({ ...p, website: e.target.value }))} />
                </div>
              </div>
              <div>
                <label className={labelCls}>Phone</label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input className={`${inputCls} pl-9`} placeholder="+31 20 000 0000" value={profile.phone}
                    onChange={e => setProfile(p => ({ ...p, phone: e.target.value }))} />
                </div>
              </div>
              <div className="sm:col-span-2">
                <label className={labelCls}>Address</label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                  <textarea rows={2} className={`${inputCls} pl-9 resize-none`} placeholder="Street, City, Country"
                    value={profile.address}
                    onChange={e => setProfile(p => ({ ...p, address: e.target.value }))} />
                </div>
              </div>
            </div>
          </div>

          {/* Localisation */}
          <div className={cardCls}>
            <h3 className="font-bold text-gray-900 mb-5 flex items-center gap-2">
              <Globe className="w-5 h-5 text-[#4ECFBF]" /> Localisation
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label className={labelCls}>Dashboard Language</label>
                <select className={inputCls} value={profile.admin_language}
                  onChange={e => setProfile(p => ({ ...p, admin_language: e.target.value }))}>
                  {ADMIN_LANGUAGES.map(l => <option key={l.value} value={l.value}>{l.label}</option>)}
                </select>
              </div>
              <div>
                <label className={labelCls}>Time Zone</label>
                <select className={inputCls} value={profile.timezone}
                  onChange={e => setProfile(p => ({ ...p, timezone: e.target.value }))}>
                  {TIMEZONES.map(tz => <option key={tz} value={tz}>{tz}</option>)}
                </select>
              </div>
            </div>
          </div>

          {/* Academic calendar */}
          <div className={cardCls}>
            <h3 className="font-bold text-gray-900 mb-5 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-[#4ECFBF]" /> Academic Calendar
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label className={labelCls}>Semester Start</label>
                <input type="date" className={inputCls} value={profile.semester_start}
                  onChange={e => setProfile(p => ({ ...p, semester_start: e.target.value }))} />
              </div>
              <div>
                <label className={labelCls}>Semester End</label>
                <input type="date" className={inputCls} value={profile.semester_end}
                  onChange={e => setProfile(p => ({ ...p, semester_end: e.target.value }))} />
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button onClick={saveProfile} disabled={saving} className={btnCls}>
              {saving ? <><svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>Saving...</> : <><Save className="w-4 h-4" />Save Profile</>}
            </button>
          </div>
        </div>
      )}

      {/* ── ADMIN ACCOUNT ───────────────────────────────────────────────────── */}
      {section === 'admin' && (
        <div className="space-y-6">
          {/* Identity */}
          <div className={cardCls}>
            <h3 className="font-bold text-gray-900 mb-5 flex items-center gap-2">
              <User className="w-5 h-5 text-[#4ECFBF]" /> Admin Identity
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label className={labelCls}>Display Name</label>
                <input className={inputCls} value={admin.admin_name}
                  onChange={e => setAdmin(a => ({ ...a, admin_name: e.target.value }))} />
              </div>
              <div>
                <label className={labelCls}>Email (read-only)</label>
                <input className={`${inputCls} bg-gray-50 text-gray-400 cursor-not-allowed`}
                  value={admin.admin_email} readOnly />
              </div>
              <div className="sm:col-span-2">
                <label className={labelCls}>Profile Photo URL</label>
                <div className="flex gap-3 items-center">
                  {admin.admin_photo_url
                    ? <img src={admin.admin_photo_url} alt="avatar" className="w-10 h-10 rounded-full object-cover border border-gray-200" />
                    : <div className="w-10 h-10 rounded-full bg-[#4ECFBF]/20 flex items-center justify-center flex-shrink-0">
                        <User className="w-5 h-5 text-[#4ECFBF]" />
                      </div>
                  }
                  <div className="relative flex-1">
                    <Camera className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input className={`${inputCls} pl-9`} placeholder="https://..." value={admin.admin_photo_url}
                      onChange={e => setAdmin(a => ({ ...a, admin_photo_url: e.target.value }))} />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Notifications */}
          <div className={cardCls}>
            <h3 className="font-bold text-gray-900 mb-5 flex items-center gap-2">
              <Bell className="w-5 h-5 text-[#4ECFBF]" /> Email Notifications
            </h3>
            <div className="space-y-4">
              {([
                { key: 'notify_daily_digest',   label: 'Daily digest',         desc: 'Summary of activity from the past 24 hours' },
                { key: 'notify_weekly_report',  label: 'Weekly report',        desc: 'Full progress report every Monday morning' },
                { key: 'notify_learner_alerts', label: 'Learner alerts',       desc: 'Alert when a learner is inactive for 7+ days' },
              ] as const).map(({ key, label, desc }) => (
                <label key={key} className="flex items-center justify-between cursor-pointer group">
                  <div>
                    <p className="text-sm font-semibold text-gray-800 group-hover:text-gray-900">{label}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{desc}</p>
                  </div>
                  <div
                    onClick={() => setAdmin(a => ({ ...a, [key]: !a[key] }))}
                    className={`relative w-11 h-6 rounded-full transition-colors cursor-pointer ${admin[key] ? 'bg-[#4ECFBF]' : 'bg-gray-200'}`}
                  >
                    <div className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${admin[key] ? 'translate-x-5' : 'translate-x-0.5'}`} />
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Security */}
          <div className={cardCls}>
            <h3 className="font-bold text-gray-900 mb-1 flex items-center gap-2">
              <Shield className="w-5 h-5 text-[#4ECFBF]" /> Security
            </h3>
            <p className="text-xs text-gray-400 mb-5">Two-factor authentication adds a second verification step at login.</p>
            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <p className="text-sm font-semibold text-gray-800">Two-Factor Authentication</p>
                <p className="text-xs text-gray-400 mt-0.5">{admin.two_factor_enabled ? 'Enabled — extra security active' : 'Disabled — login uses password only'}</p>
              </div>
              <div
                onClick={() => setAdmin(a => ({ ...a, two_factor_enabled: !a.two_factor_enabled }))}
                className={`relative w-11 h-6 rounded-full transition-colors cursor-pointer ${admin.two_factor_enabled ? 'bg-[#4ECFBF]' : 'bg-gray-200'}`}
              >
                <div className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${admin.two_factor_enabled ? 'translate-x-5' : 'translate-x-0.5'}`} />
              </div>
            </label>
          </div>

          <div className="flex justify-end">
            <button onClick={saveAdmin} disabled={saving} className={btnCls}>
              {saving ? <><svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>Saving...</> : <><Save className="w-4 h-4" />Save Settings</>}
            </button>
          </div>

          {/* Change password */}
          <div className={cardCls}>
            <h3 className="font-bold text-gray-900 mb-5 flex items-center gap-2">
              <KeyRound className="w-5 h-5 text-[#4ECFBF]" /> Change Password
            </h3>
            <div className="space-y-4 max-w-sm">
              {([
                { key: 'current', label: 'Current password',     placeholder: '••••••••' },
                { key: 'next',    label: 'New password',          placeholder: 'Min 8 characters' },
                { key: 'confirm', label: 'Confirm new password',  placeholder: '••••••••' },
              ] as const).map(({ key, label, placeholder }) => (
                <div key={key}>
                  <label className={labelCls}>{label}</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input type="password" className={`${inputCls} pl-9`} placeholder={placeholder}
                      value={pwForm[key]}
                      onChange={e => setPwForm(f => ({ ...f, [key]: e.target.value }))} />
                  </div>
                </div>
              ))}
              <button onClick={changePassword} disabled={pwSaving || !pwForm.current || !pwForm.next} className={btnCls}>
                {pwSaving ? 'Updating...' : 'Update Password'}
              </button>
            </div>
          </div>

          {/* Activity log */}
          {activityLog.length > 0 && (
            <div className={cardCls}>
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                <Clock className="w-5 h-5 text-[#4ECFBF]" /> Recent Activity
              </h3>
              <div className="space-y-2">
                {activityLog.map((entry, i) => (
                  <div key={i} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 rounded-full bg-[#4ECFBF]" />
                      <span className="text-sm text-gray-700 capitalize">{(entry.action || '').replace(/_/g, ' ')}</span>
                      {entry.detail && <span className="text-xs text-gray-400">— {entry.detail}</span>}
                    </div>
                    <span className="text-xs text-gray-400 whitespace-nowrap ml-4">
                      {entry.timestamp ? new Date(entry.timestamp).toLocaleString() : ''}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────

export const InstitutionDashboardComplete: React.FC = () => {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [institutionId, setInstitutionId] = useState('');
  const [institutionName, setInstitutionName] = useState('');
  
  // Analytics data
  const [languageDistribution, setLanguageDistribution] = useState<LanguageDistribution[]>([]);
  const [levelDistribution, setLevelDistribution] = useState<LevelDistribution[]>([]);
  
  // Tutors and Learners
  const [tutors, setTutors] = useState<Tutor[]>([]);
  const [learners, setLearners] = useState<Learner[]>([]);
  const [filteredLearners, setFilteredLearners] = useState<Learner[]>([]);
  const [filteredTutors, setFilteredTutors] = useState<Tutor[]>([]);
  
  // UI State
  const [activeTab, setActiveTab] = useState<'overview' | 'tutors' | 'learners' | 'settings'>('overview');
  const [showAddTutorModal, setShowAddTutorModal] = useState(false);
  const [showAddLearnerModal, setShowAddLearnerModal] = useState(false);
  const [showImportCSVModal, setShowImportCSVModal] = useState(false);
  const [selectedTutor, setSelectedTutor] = useState<Tutor | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [tutorSearchQuery, setTutorSearchQuery] = useState('');
  const [filterLanguage, setFilterLanguage] = useState('all');
  const [filterLevel, setFilterLevel] = useState('all');
  const [filterTutor, setFilterTutor] = useState('all');
  const [filterProgress, setFilterProgress] = useState('all');
  const [filterStatus, setFilterStatus] = useState('active'); // Status filter for learners
  const [filterTutorStatus, setFilterTutorStatus] = useState('active'); // Status filter for tutors
  const [filterTutorSpecialization, setFilterTutorSpecialization] = useState('all');
  const [filterTutorLearnerCount, setFilterTutorLearnerCount] = useState('all');
  const [isExporting, setIsExporting] = useState(false);
  const [isExportingTutors, setIsExportingTutors] = useState(false);
  const [showImportTutorCSVModal, setShowImportTutorCSVModal] = useState(false);
  const [selectedLearnerDetails, setSelectedLearnerDetails] = useState<any>(null);
  const [showLearnerDetailsModal, setShowLearnerDetailsModal] = useState(false);
  const [loadingLearnerDetails, setLoadingLearnerDetails] = useState(false);
  const [showTutorLearnersModal, setShowTutorLearnersModal] = useState(false);
  
  // Pagination states
  const [tutorsPage, setTutorsPage] = useState(1);
  const [learnersPage, setLearnersPage] = useState(1);
  const itemsPerPage = 10;

  // Modal states for notifications and confirmations
  const [notification, setNotification] = useState<{
    show: boolean;
    type: 'success' | 'error' | 'info';
    title: string;
    message: string;
  }>({
    show: false,
    type: 'info',
    title: '',
    message: ''
  });

  const [confirmation, setConfirmation] = useState<{
    show: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
    confirmText?: string;
    cancelText?: string;
  }>({
    show: false,
    title: '',
    message: '',
    onConfirm: () => {},
    confirmText: 'Confirm',
    cancelText: 'Cancel'
  });

  // Form states
  const [tutorForm, setTutorForm] = useState({
    name: '',
    email: '',
    bio: '',
    languages: [] as string[],
    specializations: '',
    permissions: ['view_learners', 'assign_tasks']
  });

  // Available languages with flags
  const availableLanguages = [
    { code: 'english', name: 'English' },
    { code: 'dutch', name: 'Dutch' },
    { code: 'spanish', name: 'Spanish' },
    { code: 'french', name: 'French' },
    { code: 'german', name: 'German' },
    { code: 'portuguese', name: 'Portuguese' }
  ];

  // Authentication check
  useEffect(() => {
    const token = localStorage.getItem('institution_token');
      const backendUrl = getApiBaseUrl();
    const instId = localStorage.getItem('institution_id');
    const instName = localStorage.getItem('institution_name');
    
    if (!token || !instId) {
      router.push('/institution/login');
      return;
    }
    
    setIsAuthenticated(true);
    setInstitutionId(instId);
    setInstitutionName(instName || 'Your Institution');
    setIsLoading(false);
  }, [router]);

  // Load all data when authenticated
  useEffect(() => {
    if (isAuthenticated && institutionId) {
      loadAllData();
    }
  }, [isAuthenticated, institutionId]);

  // Filter tutors based on search and filters
  useEffect(() => {
    let filtered = tutors;
    
    if (tutorSearchQuery) {
      filtered = filtered.filter(t => 
        t.name.toLowerCase().includes(tutorSearchQuery.toLowerCase()) ||
        t.email.toLowerCase().includes(tutorSearchQuery.toLowerCase())
      );
    }
    
    // Status filter
    if (filterTutorStatus === 'active') {
      filtered = filtered.filter(t => t.is_active === true);
    } else if (filterTutorStatus === 'inactive') {
      filtered = filtered.filter(t => t.is_active === false);
    }
    // 'all' shows both active and inactive
    
    if (filterTutorSpecialization !== 'all') {
      filtered = filtered.filter(t => 
        t.specializations && t.specializations.includes(filterTutorSpecialization)
      );
    }
    
    if (filterTutorLearnerCount !== 'all') {
      if (filterTutorLearnerCount === 'none') {
        filtered = filtered.filter(t => t.learner_count === 0);
      } else if (filterTutorLearnerCount === 'low') {
        filtered = filtered.filter(t => t.learner_count > 0 && t.learner_count <= 5);
      } else if (filterTutorLearnerCount === 'medium') {
        filtered = filtered.filter(t => t.learner_count > 5 && t.learner_count <= 15);
      } else if (filterTutorLearnerCount === 'high') {
        filtered = filtered.filter(t => t.learner_count > 15);
      }
    }
    
    setFilteredTutors(filtered);
    setTutorsPage(1); // Reset to first page when filters change
  }, [tutors, tutorSearchQuery, filterTutorSpecialization, filterTutorLearnerCount, filterTutorStatus]);

  // Filter learners based on search and filters
  useEffect(() => {
    let filtered = learners;
    
    if (searchQuery) {
      filtered = filtered.filter(l => 
        l.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        l.email.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    // Status filter
    if (filterStatus === 'active') {
      filtered = filtered.filter(l => l.is_active === true);
    } else if (filterStatus === 'inactive') {
      filtered = filtered.filter(l => l.is_active === false);
    }
    // 'all' shows both active and inactive
    
    if (filterLanguage !== 'all') {
      filtered = filtered.filter(l => l.language === filterLanguage);
    }
    
    if (filterLevel !== 'all') {
      filtered = filtered.filter(l => l.level === filterLevel);
    }
    
    if (filterTutor !== 'all') {
      filtered = filtered.filter(l => l.tutor?.id === filterTutor);
    }
    
    if (filterProgress !== 'all') {
      filtered = filtered.filter(l => {
        if (!l.progress) return filterProgress === 'none';
        return l.progress.category === filterProgress;
      });
    }
    
    setFilteredLearners(filtered);
    setLearnersPage(1); // Reset to first page when filters change
  }, [learners, searchQuery, filterLanguage, filterLevel, filterTutor, filterProgress, filterStatus]);

  const loadAllData = async () => {
    setIsLoadingData(true);
    try {
      const token = localStorage.getItem('institution_token');
      const backendUrl = getApiBaseUrl();
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Load analytics
      const [langRes, levelRes, tutorsRes, learnersRes] = await Promise.all([
        fetch(`${backendUrl}/institution/dashboard/${institutionId}/analytics/language-distribution`, { headers }),
        fetch(`${backendUrl}/institution/dashboard/${institutionId}/analytics/level-distribution`, { headers }),
        fetch(`${backendUrl}/institution/dashboard/${institutionId}/tutors`, { headers }),
        fetch(`${backendUrl}/institution/dashboard/${institutionId}/learners`, { headers })
      ]);

      if (langRes.ok) {
        const data = await langRes.json();
        setLanguageDistribution(data.distribution || []);
      }

      if (levelRes.ok) {
        const data = await levelRes.json();
        setLevelDistribution(data.distribution || []);
      }

      if (tutorsRes.ok) {
        const data = await tutorsRes.json();
        setTutors(data.tutors || []);
        setFilteredTutors(data.tutors || []);
      }

      if (learnersRes.ok) {
        const data = await learnersRes.json();
        setLearners(data.learners || []);
        setFilteredLearners(data.learners || []);
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setIsLoadingData(false);
    }
  };

  const handleAddTutor = async () => {
    try {
      const token = localStorage.getItem('institution_token');
      const backendUrl = getApiBaseUrl();
      const response = await fetch(`${backendUrl}/institution/dashboard/${institutionId}/tutors`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: tutorForm.name,
          email: tutorForm.email,
          bio: tutorForm.bio,
          specializations: tutorForm.specializations.split(',').map(s => s.trim()),
          permissions: tutorForm.permissions
        })
      });

      if (response.ok) {
        setNotification({
          show: true,
          type: 'success',
          title: 'Success!',
          message: 'Tutor added successfully!'
        });
        setShowAddTutorModal(false);
        setTutorForm({ name: '', email: '', bio: '', languages: [], specializations: '', permissions: ['view_learners', 'assign_tasks'] });
        loadAllData();
      } else {
        const error = await response.json();
        setNotification({
          show: true,
          type: 'error',
          title: 'Error',
          message: error.detail || 'Failed to add tutor'
        });
      }
    } catch (error) {
      console.error('Error adding tutor:', error);
      setNotification({
        show: true,
        type: 'error',
        title: 'Error',
        message: `Failed to add tutor: ${error}`
      });
    }
  };

  const handleReactivateTutor = async (tutorId: string) => {
    const tutor = tutors.find(t => t.id === tutorId);
    
    setConfirmation({
      show: true,
      title: 'Reactivate Tutor?',
      message: `Reactivate ${tutor?.name || 'this tutor'}? They will regain access and can be assigned to learners again.`,
      confirmText: 'Yes, Reactivate',
      cancelText: 'Cancel',
      onConfirm: async () => {
        try {
          const token = localStorage.getItem('institution_token');
      const backendUrl = getApiBaseUrl();
          const response = await fetch(`${backendUrl}/institution/dashboard/${institutionId}/tutors/reactivate/${tutorId}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
          });

          if (response.ok) {
            setNotification({
              show: true,
              type: 'success',
              title: 'Success!',
              message: 'Tutor reactivated successfully! They can now access the platform.'
            });
            loadAllData();
          } else {
            setNotification({
              show: true,
              type: 'error',
              title: 'Error',
              message: 'Failed to reactivate tutor'
            });
          }
        } catch (error) {
          console.error('Error reactivating tutor:', error);
          setNotification({
            show: true,
            type: 'error',
            title: 'Error',
            message: 'Failed to reactivate tutor'
          });
        }
      }
    });
  };

  const handleDeactivateTutor = async (tutorId: string) => {
    const tutor = tutors.find(t => t.id === tutorId);
    const hasLearners = tutor && tutor.learner_count > 0;
    
    setConfirmation({
      show: true,
      title: hasLearners ? 'Deactivate Tutor with Assigned Learners?' : 'Temporarily Deactivate Tutor?',
      message: hasLearners 
        ? `${tutor.name} has ${tutor.learner_count} learner${tutor.learner_count > 1 ? 's' : ''} assigned. Deactivating this tutor will unassign all their learners (they'll become "Unassigned"). The tutor account will be preserved and can be reactivated later. Are you sure you want to proceed?`
        : `Deactivate ${tutor?.name || 'this tutor'}? This will temporarily suspend their access while preserving their account. You can reactivate them later.`,
      confirmText: 'Yes, Deactivate',
      cancelText: 'Cancel',
      onConfirm: async () => {
        try {
          const token = localStorage.getItem('institution_token');
      const backendUrl = getApiBaseUrl();
          const response = await fetch(`${backendUrl}/institution/dashboard/${institutionId}/tutors/deactivate/${tutorId}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
          });

          if (response.ok) {
            setNotification({
              show: true,
              type: 'success',
              title: 'Success!',
              message: hasLearners 
                ? `Tutor deactivated and ${tutor.learner_count} learner${tutor.learner_count > 1 ? 's have' : ' has'} been unassigned.`
                : 'Tutor deactivated successfully!'
            });
            loadAllData();
          } else {
            setNotification({
              show: true,
              type: 'error',
              title: 'Error',
              message: 'Failed to deactivate tutor'
            });
          }
        } catch (error) {
          console.error('Error deactivating tutor:', error);
          setNotification({
            show: true,
            type: 'error',
            title: 'Error',
            message: 'Failed to deactivate tutor'
          });
        }
      }
    });
  };

  const handleAssignLearnerToTutor = async (learnerId: string, tutorId: string, learnerName: string, currentTutorName: string | null, newTutorName: string | null) => {
    // Show confirmation modal
    const isUnassigning = tutorId === '';
    const isReassigning = currentTutorName && newTutorName;
    
    let title = '';
    let message = '';
    
    if (isUnassigning) {
      title = 'Unassign Learner from Tutor?';
      message = `Remove ${learnerName} from ${currentTutorName}? They will become "Unassigned" and can be assigned to a different tutor later.`;
    } else if (isReassigning) {
      title = 'Reassign Learner to Different Tutor?';
      message = `Move ${learnerName} from ${currentTutorName} to ${newTutorName}?`;
    } else {
      title = 'Assign Learner to Tutor?';
      message = `Assign ${learnerName} to ${newTutorName}?`;
    }
    
    setConfirmation({
      show: true,
      title,
      message,
      confirmText: 'Yes, Confirm',
      cancelText: 'Cancel',
      onConfirm: async () => {
        try {
          const token = localStorage.getItem('institution_token');
      const backendUrl = getApiBaseUrl();
          const response = await fetch(`${backendUrl}/institution/dashboard/${institutionId}/learners/assign-tutor`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ learner_id: learnerId, tutor_id: tutorId })
          });

          if (response.ok) {
            setNotification({
              show: true,
              type: 'success',
              title: 'Success!',
              message: isUnassigning 
                ? 'Learner unassigned successfully!' 
                : isReassigning
                ? 'Learner reassigned successfully!'
                : 'Learner assigned successfully!'
            });
            loadAllData();
          } else {
            setNotification({
              show: true,
              type: 'error',
              title: 'Error',
              message: 'Failed to assign learner'
            });
          }
        } catch (error) {
          console.error('Error assigning learner:', error);
          setNotification({
            show: true,
            type: 'error',
            title: 'Error',
            message: 'Failed to assign learner'
          });
        }
      }
    });
  };

  const handleDeactivateLearner = async (learnerId: string) => {
    const learner = learners.find(l => l.id === learnerId);
    const hasProgress = learner && learner.progress && learner.progress.completed_sessions > 0;
    
    setConfirmation({
      show: true,
      title: 'Temporarily Deactivate Learner?',
      message: hasProgress
        ? `${learner.name} has completed ${learner.progress?.completed_sessions} session${learner.progress && learner.progress.completed_sessions > 1 ? 's' : ''} (${learner.progress?.percentage}% progress). Deactivating will temporarily suspend their access while preserving all progress data. You can reactivate them at any time to resume from where they left off.`
        : `Deactivate ${learner?.name || 'this learner'}? This will temporarily suspend their platform access while preserving their account. You can reactivate them later.`,
      confirmText: 'Yes, Deactivate',
      cancelText: 'Cancel',
      onConfirm: async () => {
        try {
          const token = localStorage.getItem('institution_token');
      const backendUrl = getApiBaseUrl();
          const response = await fetch(`${backendUrl}/institution/dashboard/${institutionId}/learners/deactivate/${learnerId}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
          });

          if (response.ok) {
            setNotification({
              show: true,
              type: 'success',
              title: 'Success!',
              message: 'Learner deactivated successfully!'
            });
            loadAllData();
          } else {
            setNotification({
              show: true,
              type: 'error',
              title: 'Error',
              message: 'Failed to deactivate learner'
            });
          }
        } catch (error) {
          console.error('Error deactivating learner:', error);
          setNotification({
            show: true,
            type: 'error',
            title: 'Error',
            message: 'Failed to deactivate learner'
          });
        }
      }
    });
  };

  const handleReactivateLearner = async (learnerId: string) => {
    const learner = learners.find(l => l.id === learnerId);
    
    setConfirmation({
      show: true,
      title: 'Reactivate Learner?',
      message: `Reactivate ${learner?.name || 'this learner'}? They will regain full platform access and can resume their learning from where they left off.`,
      confirmText: 'Yes, Reactivate',
      cancelText: 'Cancel',
      onConfirm: async () => {
        try {
          const token = localStorage.getItem('institution_token');
      const backendUrl = getApiBaseUrl();
          const response = await fetch(`${backendUrl}/institution/dashboard/${institutionId}/learners/reactivate/${learnerId}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
          });

          if (response.ok) {
            setNotification({
              show: true,
              type: 'success',
              title: 'Success!',
              message: 'Learner reactivated successfully! They can now access the platform.'
            });
            loadAllData();
          } else {
            setNotification({
              show: true,
              type: 'error',
              title: 'Error',
              message: 'Failed to reactivate learner'
            });
          }
        } catch (error) {
          console.error('Error reactivating learner:', error);
          setNotification({
            show: true,
            type: 'error',
            title: 'Error',
            message: 'Failed to reactivate learner'
          });
        }
      }
    });
  };

  const handleViewLearnerDetails = async (learner: Learner) => {
    setLoadingLearnerDetails(true);
    setShowLearnerDetailsModal(true);
    
    // If no consent, show modal with message
    if (!learner.consent_given) {
      setSelectedLearnerDetails({
        no_consent: true,
        learner_name: learner.name
      });
      setLoadingLearnerDetails(false);
      return;
    }
    
    
    try {
      const token = localStorage.getItem('institution_token');
      const backendUrl = getApiBaseUrl();
      const response = await fetch(
        `${backendUrl}/institution/dashboard/${institutionId}/learners/${learner.user_id}/comprehensive-details`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        setSelectedLearnerDetails(data);
      } else {
        const error = await response.json();
        setNotification({
          show: true,
          type: 'error',
          title: 'Error',
          message: error.detail || 'Failed to load learner details'
        });
        setShowLearnerDetailsModal(false);
      }
    } catch (error) {
      console.error('Error loading learner details:', error);
      setNotification({
        show: true,
        type: 'error',
        title: 'Error',
        message: 'Failed to load learner details'
      });
      setShowLearnerDetailsModal(false);
    } finally {
      setLoadingLearnerDetails(false);
    }
  };

  const handleExportLearners = async () => {
    setIsExporting(true);
    try {
      const token = localStorage.getItem('institution_token');
      const backendUrl = getApiBaseUrl();
      const response = await fetch(`${backendUrl}/institution/dashboard/${institutionId}/learners/export`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `learners_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
        setNotification({ show: true, type: 'success', title: 'Export Successful!', message: 'Learners exported to CSV.' });
      } else {
        setNotification({ show: true, type: 'error', title: 'Export Failed', message: 'Failed to export learners. Please try again.' });
      }
    } catch (error) {
      console.error('Error exporting learners:', error);
      setNotification({ show: true, type: 'error', title: 'Export Error', message: 'An error occurred while exporting learners.' });
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportTutors = async () => {
    setIsExportingTutors(true);
    try {
      const token = localStorage.getItem('institution_token');
      const backendUrl = getApiBaseUrl();
      const response = await fetch(`${backendUrl}/institution/dashboard/${institutionId}/tutors/export`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `tutors_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
        setNotification({ show: true, type: 'success', title: 'Export Successful!', message: 'Tutors exported to CSV.' });
      } else {
        setNotification({ show: true, type: 'error', title: 'Export Failed', message: 'Failed to export tutors. Please try again.' });
      }
    } catch (error) {
      console.error('Error exporting tutors:', error);
      setNotification({ show: true, type: 'error', title: 'Export Error', message: 'An error occurred while exporting tutors.' });
    } finally {
      setIsExportingTutors(false);
    }
  };

  const handleImportTutorCSV = async (file: File) => {
    try {
      const token = localStorage.getItem('institution_token');
      const backendUrl = getApiBaseUrl();
      const formData = new FormData();
      formData.append('file', file);
      const response = await fetch(`${backendUrl}/institution/dashboard/${institutionId}/tutors/bulk-import`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      if (response.ok) {
        const result = await response.json();
        setNotification({
          show: true,
          type: 'success',
          title: 'Import Completed!',
          message: `Successfully imported ${result.success_count} tutors. ${result.failed_count > 0 ? `${result.failed_count} failed.` : ''}`
        });
        setShowImportTutorCSVModal(false);
        loadAllData();
      } else {
        const err = await response.json().catch(() => ({}));
        setNotification({ show: true, type: 'error', title: 'Import Failed', message: err.detail || 'Failed to import CSV file. Please check the format.' });
      }
    } catch (error) {
      console.error('Error importing tutor CSV:', error);
      setNotification({ show: true, type: 'error', title: 'Import Error', message: 'An error occurred while importing the CSV file.' });
    }
  };

  const handleImportCSV = async (file: File) => {
    try {
      const token = localStorage.getItem('institution_token');
      const backendUrl = getApiBaseUrl();
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${backendUrl}/institution/dashboard/${institutionId}/learners/bulk-import`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        setNotification({
          show: true,
          type: 'success',
          title: 'Import Completed!',
          message: `Successfully imported ${result.success_count} learners. ${result.failed_count} failed.`
        });
        setShowImportCSVModal(false);
        loadAllData();
      } else {
        setNotification({
          show: true,
          type: 'error',
          title: 'Import Failed',
          message: 'Failed to import CSV file. Please check the file format.'
        });
      }
    } catch (error) {
      console.error('Error importing CSV:', error);
      setNotification({
        show: true,
        type: 'error',
        title: 'Import Error',
        message: 'An error occurred while importing the CSV file.'
      });
    }
  };

  // Chart data
  const languageChartData = {
    labels: languageDistribution.map(d => d.language),
    datasets: [{
      data: languageDistribution.map(d => d.count),
      backgroundColor: [
        '#4ECFBF',
        '#FF6384',
        '#36A2EB',
        '#FFCE56',
        '#4BC0C0',
        '#9966FF'
      ]
    }]
  };

  const levelChartData = {
    labels: levelDistribution.map(d => d.level),
    datasets: [{
      label: 'Number of Learners',
      data: levelDistribution.map(d => d.count),
      backgroundColor: '#4ECFBF'
    }]
  };

  // Pagination logic
  const paginatedTutors = filteredTutors.slice(
    (tutorsPage - 1) * itemsPerPage,
    tutorsPage * itemsPerPage
  );
  const totalTutorPages = Math.ceil(filteredTutors.length / itemsPerPage);

  const paginatedLearners = filteredLearners.slice(
    (learnersPage - 1) * itemsPerPage,
    learnersPage * itemsPerPage
  );
  const totalLearnerPages = Math.ceil(filteredLearners.length / itemsPerPage);

  // Pagination Component
  const Pagination = ({ 
    currentPage, 
    totalPages,
    totalItems,
    onPageChange 
  }: { 
    currentPage: number; 
    totalPages: number;
    totalItems: number;
    onPageChange: (page: number) => void;
  }) => {
    const getPageNumbers = () => {
      const pages = [];
      const showEllipsis = totalPages > 7;
      
      if (!showEllipsis) {
        for (let i = 1; i <= totalPages; i++) {
          pages.push(i);
        }
      } else {
        if (currentPage <= 3) {
          pages.push(1, 2, 3, 4, '...', totalPages);
        } else if (currentPage >= totalPages - 2) {
          pages.push(1, '...', totalPages - 3, totalPages - 2, totalPages - 1, totalPages);
        } else {
          pages.push(1, '...', currentPage - 1, currentPage, currentPage + 1, '...', totalPages);
        }
      }
      
      return pages;
    };

    return (
      <div className="flex flex-col sm:flex-row items-center justify-between px-6 py-4 border-t bg-gray-50 gap-3">
        <div className="text-sm text-gray-700">
          Showing <span className="font-medium">{(currentPage - 1) * itemsPerPage + 1}</span> to{' '}
          <span className="font-medium">{Math.min(currentPage * itemsPerPage, totalItems)}</span> of{' '}
          <span className="font-medium">{totalItems}</span> results
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className={`px-3 py-2 rounded-lg font-medium transition-all ${
              currentPage === 1
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-white text-gray-700 hover:bg-[#4ECFBF] hover:text-white border'
            }`}
          >
            Previous
          </button>
          
          <div className="flex space-x-1">
            {getPageNumbers().map((page, index) => (
              page === '...' ? (
                <span key={`ellipsis-${index}`} className="px-3 py-2 text-gray-500">...</span>
              ) : (
                <button
                  key={page}
                  onClick={() => onPageChange(page as number)}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${
                    currentPage === page
                      ? 'bg-[#4ECFBF] text-white shadow-md'
                      : 'bg-white text-gray-700 hover:bg-gray-100 border'
                  }`}
                >
                  {page}
                </button>
              )
            ))}
          </div>
          
          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className={`px-3 py-2 rounded-lg font-medium transition-all ${
              currentPage === totalPages
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-white text-gray-700 hover:bg-[#4ECFBF] hover:text-white border'
            }`}
          >
            Next
          </button>
        </div>
      </div>
    );
  };

  if (isLoading) {
    return <PageSpinner />;
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 pt-20 font-nunito">
      {/* Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4">
          <nav className="flex space-x-8 overflow-x-auto">
            <button
              onClick={() => setActiveTab('overview')}
              className={`py-4 border-b-2 flex items-center ${activeTab === 'overview' ? 'border-[#4ECFBF] text-[#4ECFBF]' : 'border-transparent text-gray-500'}`}
            >
              <BarChart2 className="w-4 h-4 mr-1.5 inline-block" /> Overview
            </button>
            <button
              onClick={() => setActiveTab('tutors')}
              className={`py-4 border-b-2 flex items-center ${activeTab === 'tutors' ? 'border-[#4ECFBF] text-[#4ECFBF]' : 'border-transparent text-gray-500'}`}
            >
              <Users className="w-4 h-4 mr-1.5 inline-block" /> Tutors ({tutors.length})
            </button>
            <button
              onClick={() => setActiveTab('learners')}
              className={`py-4 border-b-2 flex items-center whitespace-nowrap ${activeTab === 'learners' ? 'border-[#4ECFBF] text-[#4ECFBF]' : 'border-transparent text-gray-500'}`}
            >
              <GraduationCap className="w-4 h-4 mr-1.5 inline-block" /> Learners ({learners.length})
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`py-4 border-b-2 flex items-center whitespace-nowrap ml-auto ${activeTab === 'settings' ? 'border-[#4ECFBF] text-[#4ECFBF]' : 'border-transparent text-gray-500'}`}
            >
              <Settings className="w-4 h-4 mr-1.5 inline-block" /> Settings
            </button>
          </nav>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* Analytics Charts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Language Distribution */}
              <div className="bg-white p-6 rounded-xl shadow">
                <h3 className="text-lg font-bold text-gray-900 mb-4">Language Distribution</h3>
                {languageDistribution.length > 0 ? (
                  <div className="h-64">
                    <Pie data={languageChartData} options={{ maintainAspectRatio: false }} />
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">No data available</p>
                )}
              </div>

              {/* Level Distribution */}
              <div className="bg-white p-6 rounded-xl shadow">
                <h3 className="text-lg font-bold text-gray-900 mb-4">Proficiency Level Distribution</h3>
                {levelDistribution.length > 0 ? (
                  <div className="h-64">
                    <Bar data={levelChartData} options={{ maintainAspectRatio: false }} />
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">No data available</p>
                )}
              </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
              <div className="bg-white p-6 rounded-xl shadow">
                <div className="flex items-center gap-2 mb-1">
                  <GraduationCap className="w-5 h-5 text-[#4ECFBF]" />
                  <p className="text-gray-600">Total Learners</p>
                </div>
                <p className="text-2xl sm:text-3xl font-bold text-[#4ECFBF]">{learners.length}</p>
              </div>
              <div className="bg-white p-6 rounded-xl shadow">
                <div className="flex items-center gap-2 mb-1">
                  <Users className="w-5 h-5 text-blue-500" />
                  <p className="text-gray-600">Total Tutors</p>
                </div>
                <p className="text-2xl sm:text-3xl font-bold text-[#4ECFBF]">{tutors.length}</p>
              </div>
              <div className="bg-white p-6 rounded-xl shadow">
                <div className="flex items-center gap-2 mb-1">
                  <Globe className="w-5 h-5 text-purple-500" />
                  <p className="text-gray-600">Languages</p>
                </div>
                <p className="text-2xl sm:text-3xl font-bold text-[#4ECFBF]">{languageDistribution.length}</p>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'tutors' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
              <h2 className="text-2xl font-bold">Tutor Management</h2>
              <div className="flex gap-3 flex-wrap">
                <button
                  onClick={() => setShowImportTutorCSVModal(true)}
                  className="px-5 py-2.5 border-2 border-[#4ECFBF] text-[#4ECFBF] rounded-lg hover:bg-[#4ECFBF] hover:text-white transition-colors flex items-center text-sm font-medium"
                >
                  <Upload className="w-4 h-4 mr-1.5" /> Import CSV
                </button>
                <button
                  onClick={handleExportTutors}
                  disabled={isExportingTutors}
                  className={`px-5 py-2.5 border-2 border-[#4ECFBF] rounded-lg transition-all flex items-center text-sm font-medium ${isExportingTutors ? 'bg-[#4ECFBF] text-white cursor-wait' : 'text-[#4ECFBF] hover:bg-[#4ECFBF] hover:text-white'}`}
                >
                  {isExportingTutors ? (
                    <><svg className="animate-spin h-4 w-4 mr-1.5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Exporting...</>
                  ) : (
                    <><Download className="w-4 h-4 mr-1.5" /> Export CSV</>
                  )}
                </button>
                <button
                  onClick={() => setShowAddTutorModal(true)}
                  className="px-5 py-2.5 bg-[#4ECFBF] text-white rounded-lg hover:bg-[#3a9e92] flex items-center text-sm font-medium"
                >
                  <UserPlus className="w-4 h-4 mr-1.5" /> Add Tutor
                </button>
              </div>
            </div>

            {/* Tutors Filters */}
            <div className="bg-white p-4 rounded-xl shadow flex gap-4 flex-wrap">
              <input
                type="text"
                placeholder="Search tutors by name or email..."
                value={tutorSearchQuery}
                onChange={(e) => setTutorSearchQuery(e.target.value)}
                className="flex-1 min-w-[250px] px-4 py-2 border rounded-lg text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-[#4ECFBF] focus:border-[#4ECFBF]"
              />
              <select
                value={filterTutorStatus}
                onChange={(e) => setFilterTutorStatus(e.target.value)}
                className="px-4 py-2 border rounded-lg text-gray-900 font-medium focus:ring-2 focus:ring-[#4ECFBF] focus:border-[#4ECFBF]"
              >
                <option value="active">Active Only</option>
                <option value="inactive">Inactive Only</option>
                <option value="all">All Statuses</option>
              </select>
              <select
                value={filterTutorSpecialization}
                onChange={(e) => setFilterTutorSpecialization(e.target.value)}
                className="px-4 py-2 border rounded-lg text-gray-900 focus:ring-2 focus:ring-[#4ECFBF] focus:border-[#4ECFBF]"
              >
                <option value="all">All Specializations</option>
                {Array.from(new Set(tutors.flatMap(t => t.specializations || []))).sort().map(spec => (
                  <option key={spec} value={spec}>{spec}</option>
                ))}
              </select>
              <select
                value={filterTutorLearnerCount}
                onChange={(e) => setFilterTutorLearnerCount(e.target.value)}
                className="px-4 py-2 border rounded-lg text-gray-900 focus:ring-2 focus:ring-[#4ECFBF] focus:border-[#4ECFBF]"
              >
                <option value="all">All Workloads</option>
                <option value="none">— No Learners (0)</option>
                <option value="low">Light Load (1-5)</option>
                <option value="medium">Medium Load (6-15)</option>
                <option value="high">Heavy Load (15+)</option>
              </select>
              {(tutorSearchQuery || filterTutorSpecialization !== 'all' || filterTutorLearnerCount !== 'all') && (
                <button
                  onClick={() => {
                    setTutorSearchQuery('');
                    setFilterTutorSpecialization('all');
                    setFilterTutorLearnerCount('all');
                  }}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium flex items-center"
                >
                  <X className="w-4 h-4 mr-1.5" /> Clear Filters
                </button>
              )}
            </div>

            {/* Results Summary */}
            <div className="flex justify-between items-center text-sm text-gray-600">
              <span>
                Showing <span className="font-semibold text-gray-900">{filteredTutors.length}</span> of <span className="font-semibold text-gray-900">{tutors.length}</span> tutors
              </span>
              {(tutorSearchQuery || filterTutorSpecialization !== 'all' || filterTutorLearnerCount !== 'all') && (
                <span className="text-[#4ECFBF] font-medium flex items-center">
                  <Search className="w-4 h-4 mr-1 inline-block" /> Filters Active
                </span>
              )}
            </div>

            <div className="bg-white rounded-xl shadow overflow-hidden">
              <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tutor Info</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Bio & Specializations</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Learners</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {paginatedTutors.map(tutor => (
                    <tr key={tutor.id} className={!tutor.is_active ? 'bg-gray-100 border-l-4 border-gray-400' : ''}>
                      <td className="px-6 py-4">
                        <div>
                          <p className={`font-medium ${!tutor.is_active ? 'text-gray-500' : 'text-gray-900'}`}>
                            {tutor.name}
                          </p>
                          <p className="text-sm text-gray-500">{tutor.email}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="space-y-2">
                          {tutor.bio && (
                            <p className="text-sm text-gray-700">{tutor.bio}</p>
                          )}
                          {tutor.specializations && tutor.specializations.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {tutor.specializations.map((spec, idx) => (
                                <span 
                                  key={idx}
                                  className="inline-block px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-700"
                                >
                                  {spec}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {tutor.learner_count === 0 ? (
                          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-gray-100">
                            <span className="text-sm text-gray-500"><span className="text-gray-400">—</span> No learners</span>
                          </div>
                        ) : (
                          <button
                            onClick={() => {
                              setSelectedTutor(tutor);
                              setShowTutorLearnersModal(true);
                            }}
                            className="inline-block px-4 py-2 bg-[#4ECFBF] text-white rounded-lg text-sm font-medium hover:bg-[#3a9e92] transition-all whitespace-nowrap"
                          >
                            View {tutor.learner_count} {tutor.learner_count === 1 ? 'Learner' : 'Learners'}
                          </button>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {tutor.is_active ? (
                          <button
                            onClick={() => handleDeactivateTutor(tutor.id)}
                            className="inline-flex items-center px-4 py-2 bg-red-50 text-red-600 rounded-lg text-sm font-medium hover:bg-red-100 hover:text-red-700 transition-all border border-red-200"
                          >
                            <UserMinus className="w-4 h-4 mr-1.5" /> Deactivate
                          </button>
                        ) : (
                          <button
                            onClick={() => handleReactivateTutor(tutor.id)}
                            className="inline-flex items-center px-4 py-2 bg-green-50 text-green-600 rounded-lg text-sm font-medium hover:bg-green-100 hover:text-green-700 transition-all border border-green-200"
                          >
                            <RefreshCw className="w-4 h-4 mr-1.5" /> Reactivate
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              </div>

              {/* Pagination for Tutors */}
              {totalTutorPages > 1 && (
                <Pagination 
                  currentPage={tutorsPage}
                  totalPages={totalTutorPages}
                  totalItems={filteredTutors.length}
                  onPageChange={setTutorsPage}
                />
              )}
            </div>
          </div>
        )}

        {activeTab === 'learners' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
              <h2 className="text-2xl font-bold text-gray-900">Learner Management</h2>
              <div className="flex gap-3 flex-wrap">
                <button
                  onClick={() => setShowImportCSVModal(true)}
                  className="px-5 py-2.5 border-2 border-[#4ECFBF] text-[#4ECFBF] rounded-lg hover:bg-[#4ECFBF] hover:text-white transition-colors flex items-center text-sm font-medium"
                >
                  <Upload className="w-4 h-4 mr-1.5" /> Import
                </button>
                <button
                  onClick={handleExportLearners}
                  disabled={isExporting}
                  className={`px-5 py-2.5 border-2 border-[#4ECFBF] rounded-lg transition-all flex items-center text-sm font-medium ${isExporting ? 'bg-[#4ECFBF] text-white cursor-wait' : 'text-[#4ECFBF] hover:bg-[#4ECFBF] hover:text-white'}`}
                >
                  {isExporting
                    ? <><svg className="animate-spin h-4 w-4 mr-1.5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/></svg>Exporting...</>
                    : <><Download className="w-4 h-4 mr-1.5" />Export</>
                  }
                </button>
                <button
                  onClick={() => setShowAddLearnerModal(true)}
                  className="px-5 py-2.5 bg-[#4ECFBF] text-white rounded-lg hover:bg-[#3a9e92] flex items-center text-sm font-medium"
                >
                  <UserPlus className="w-4 h-4 mr-1.5" /> Add Learner
                </button>
              </div>
            </div>

            {/* Filters */}
            <div className="bg-white p-4 rounded-xl shadow grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-3">
              <input
                type="text"
                placeholder="Search learners..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="px-4 py-2 border rounded-lg text-gray-900 placeholder-gray-500 col-span-1 sm:col-span-2 lg:col-span-1"
              />
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-4 py-2 border rounded-lg text-gray-900 font-medium focus:ring-2 focus:ring-[#4ECFBF] focus:border-[#4ECFBF]"
              >
                <option value="active">Active Only</option>
                <option value="inactive">Inactive Only</option>
                <option value="all">All Statuses</option>
              </select>
              <select
                value={filterLanguage}
                onChange={(e) => setFilterLanguage(e.target.value)}
                className="px-4 py-2 border rounded-lg text-gray-900"
              >
                <option value="all">All Languages</option>
                {Array.from(new Set(learners.map(l => l.language).filter(Boolean))).map(lang => (
                  <option key={lang} value={lang!}>{lang}</option>
                ))}
              </select>
              <select
                value={filterLevel}
                onChange={(e) => setFilterLevel(e.target.value)}
                className="px-4 py-2 border rounded-lg text-gray-900"
              >
                <option value="all">All Levels</option>
                {['A1', 'A2', 'B1', 'B2', 'C1', 'C2'].map(level => (
                  <option key={level} value={level}>{level}</option>
                ))}
              </select>
              <select
                value={filterProgress}
                onChange={(e) => setFilterProgress(e.target.value)}
                className="px-4 py-2 border rounded-lg text-gray-900"
              >
                <option value="all">All Progress</option>
                <option value="Just Started">Just Started</option>
                <option value="Early Progress">Early Progress</option>
                <option value="Intermediate">Intermediate</option>
                <option value="Advanced">Advanced</option>
                <option value="Nearly Complete">Nearly Complete</option>
                <option value="none">No Progress Data</option>
              </select>
              <select
                value={filterTutor}
                onChange={(e) => setFilterTutor(e.target.value)}
                className="px-4 py-2 border rounded-lg text-gray-900"
              >
                <option value="all">All Tutors</option>
                {tutors.map(tutor => (
                  <option key={tutor.id} value={tutor.id}>{tutor.name}</option>
                ))}
              </select>
            </div>

            {/* Learners Table */}
            <div className="bg-white rounded-xl shadow overflow-hidden relative">
              {isLoadingData && learners.length === 0 && <TableSkeleton rows={4} />}
              <div className="overflow-x-auto">
              <table className={`w-full ${isLoadingData && learners.length === 0 ? 'hidden' : ''}`}>
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Language</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Level</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Progress</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tutor</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {paginatedLearners.map(learner => (
                    <tr key={learner.id} className={!learner.is_active ? 'bg-gray-100 border-l-4 border-gray-400' : ''}>
                      <td className="px-6 py-4">
                        <div>
                          <p className={`font-medium ${!learner.is_active ? 'text-gray-500' : 'text-gray-900'}`}>
                            {learner.name}
                          </p>
                          <p className="text-sm text-gray-500">{learner.email}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-gray-700"><div className="flex items-center gap-1.5"><FlagOrText language={learner.language ?? ''} size={16} />{learner.language ? learner.language.charAt(0).toUpperCase()+learner.language.slice(1) : 'Not set'}</div></td>
                      <td className="px-6 py-4 text-gray-700">{learner.level || 'Not set'}</td>
                      <td className="px-6 py-4">
                        {learner.progress ? (
                          <div className="space-y-2">
                            {/* Progress Bar */}
                            <div className="flex items-center space-x-3">
                              <div className="flex-1">
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                  <div 
                                    className={`h-2 rounded-full ${
                                      learner.progress.color === 'green' ? 'bg-green-500' :
                                      learner.progress.color === 'blue' ? 'bg-blue-500' :
                                      learner.progress.color === 'yellow' ? 'bg-yellow-500' :
                                      learner.progress.color === 'orange' ? 'bg-orange-500' :
                                      'bg-red-500'
                                    }`}
                                    style={{ width: `${learner.progress.percentage}%` }}
                                  ></div>
                                </div>
                              </div>
                              <span className="text-sm font-medium text-gray-700 min-w-[45px]">
                                {learner.progress.percentage}%
                              </span>
                            </div>
                            {/* Session Count and Badge */}
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-gray-600">
                                {learner.progress.completed_sessions}/{learner.progress.total_sessions} sessions
                              </span>
                              <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-700 flex items-center">
                                <span className={`inline-block w-2.5 h-2.5 rounded-full mr-1.5 ${
                                  learner.progress.category === 'Just Started' ? 'bg-emerald-500' :
                                  learner.progress.category === 'Early Progress' ? 'bg-blue-500' :
                                  learner.progress.category === 'Intermediate' ? 'bg-yellow-400' :
                                  learner.progress.category === 'Advanced' ? 'bg-orange-500' :
                                  'bg-rose-500'
                                }`} />
                                <span>{learner.progress.category}</span>
                              </span>
                            </div>
                          </div>
                        ) : (
                          <span className="text-sm text-gray-500">No progress data</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <select
                          value={learner.tutor?.id || ''}
                          onChange={(e) => {
                            const newTutorId = e.target.value;
                            const newTutor = tutors.find(t => t.id === newTutorId);
                            const currentTutorName = learner.tutor?.name || null;
                            const newTutorName = newTutor?.name || null;
                            
                            handleAssignLearnerToTutor(
                              learner.id, 
                              newTutorId, 
                              learner.name,
                              currentTutorName,
                              newTutorName
                            );
                            
                            // Reset dropdown to current value (will update after confirmation)
                            e.target.value = learner.tutor?.id || '';
                          }}
                          className="px-3 py-1 border rounded text-sm text-gray-900 bg-white cursor-pointer hover:border-[#4ECFBF] focus:ring-2 focus:ring-[#4ECFBF] focus:border-[#4ECFBF] transition-all"
                        >
                          <option value="">Unassigned</option>
                          {tutors.map(tutor => (
                            <option key={tutor.id} value={tutor.id}>{tutor.name}</option>
                          ))}
                        </select>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex gap-2">
                          {learner.consent_given ? (
                            <button
                              onClick={() => handleViewLearnerDetails(learner)}
                              disabled={!learner.is_active}
                              className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm ${
                                learner.is_active
                                  ? 'bg-[#4ECFBF] text-white hover:bg-[#3a9e92] hover:shadow-md'
                                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                              }`}
                              title={learner.is_active ? "Full access - consent given" : "Learner is inactive"}
                            >
                              <Eye className="w-4 h-4 mr-1.5" />
                              View Details
                            </button>
                          ) : (
                            <button
                              onClick={() => handleViewLearnerDetails(learner)}
                              disabled={!learner.is_active}
                              className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                                learner.is_active
                                  ? 'bg-gradient-to-r from-orange-100 to-amber-100 text-orange-700 hover:from-orange-200 hover:to-amber-200 border-2 border-orange-300'
                                  : 'bg-gray-300 text-gray-500 cursor-not-allowed border-2 border-gray-400'
                              }`}
                              title={learner.is_active ? "Limited access - consent required" : "Learner is inactive"}
                            >
                              <Eye className="w-4 h-4 mr-1.5" />
                              View Details
                            </button>
                          )}
                          {learner.is_active ? (
                            <button
                              onClick={() => handleDeactivateLearner(learner.id)}
                              className="inline-flex items-center px-4 py-2 bg-red-50 text-red-600 rounded-lg text-sm font-medium hover:bg-red-100 hover:text-red-700 transition-all border border-red-200"
                            >
                              <UserMinus className="w-4 h-4 mr-1.5" /> Deactivate
                            </button>
                          ) : (
                            <button
                              onClick={() => handleReactivateLearner(learner.id)}
                              className="inline-flex items-center px-4 py-2 bg-green-50 text-green-600 rounded-lg text-sm font-medium hover:bg-green-100 hover:text-green-700 transition-all border border-green-200"
                            >
                              <RefreshCw className="w-4 h-4 mr-1.5" /> Reactivate
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              </div>

              {/* Pagination for Learners */}
              {totalLearnerPages > 1 && (
                <Pagination 
                  currentPage={learnersPage}
                  totalPages={totalLearnerPages}
                  totalItems={filteredLearners.length}
                  onPageChange={setLearnersPage}
                />
              )}
            </div>
          </div>
        )}
      </main>

      {/* Add Tutor Modal */}
      {showAddTutorModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white p-8 rounded-xl max-w-md w-full mx-4 sm:mx-auto">
            <h3 className="text-xl font-bold mb-4 text-gray-900">Add New Tutor</h3>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Name"
                value={tutorForm.name}
                onChange={(e) => setTutorForm({...tutorForm, name: e.target.value})}
                className="w-full px-4 py-2 border rounded-lg text-gray-900 placeholder-gray-500"
              />
              <input
                type="email"
                placeholder="Email"
                value={tutorForm.email}
                onChange={(e) => setTutorForm({...tutorForm, email: e.target.value})}
                className="w-full px-4 py-2 border rounded-lg text-gray-900 placeholder-gray-500"
              />
              <textarea
                placeholder="Bio"
                value={tutorForm.bio}
                onChange={(e) => setTutorForm({...tutorForm, bio: e.target.value})}
                className="w-full px-4 py-2 border rounded-lg text-gray-900 placeholder-gray-500"
                rows={3}
              />
              
              {/* Language Selection with Flags */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Languages</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3">
                  {availableLanguages.map((lang) => (
                    <button
                      key={lang.code}
                      type="button"
                      onClick={() => {
                        const isSelected = tutorForm.languages.includes(lang.code);
                        setTutorForm({
                          ...tutorForm,
                          languages: isSelected
                            ? tutorForm.languages.filter(l => l !== lang.code)
                            : [...tutorForm.languages, lang.code]
                        });
                      }}
                      className={`flex items-center space-x-2 px-4 py-3 border-2 rounded-lg transition-all ${
                        tutorForm.languages.includes(lang.code)
                          ? 'border-[#4ECFBF] bg-[#4ECFBF]/10 text-[#4ECFBF]'
                          : 'border-gray-200 hover:border-[#4ECFBF]/50'
                      }`}
                    >
                      <FlagIcon language={lang.code} size={24} />
                      <span className="font-medium text-gray-900">{lang.name}</span>
                      {tutorForm.languages.includes(lang.code) && (
                        <svg className="w-5 h-5 ml-auto" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              <input
                type="text"
                placeholder="Specializations (comma-separated)"
                value={tutorForm.specializations}
                onChange={(e) => setTutorForm({...tutorForm, specializations: e.target.value})}
                className="w-full px-4 py-2 border rounded-lg text-gray-900 placeholder-gray-500"
              />
              <div className="flex gap-3">
                <button
                  onClick={handleAddTutor}
                  className="flex-1 px-4 py-2 bg-[#4ECFBF] text-white rounded-lg hover:bg-[#3a9e92]"
                >
                  Add Tutor
                </button>
                <button
                  onClick={() => setShowAddTutorModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-900 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Settings Tab ────────────────────────────────────────────────── */}
      {activeTab === 'settings' && (
        <SettingsTab
          institutionId={institutionId}
          token={localStorage.getItem('institution_token') || ''}
          onNotify={(type, title, message) =>
            setNotification({ show: true, type, title, message })
          }
        />
      )}

      {/* ── Import Modal — Learners ─────────────────────────────────────── */}
      {showImportCSVModal && (
        <ImportModal
          title="Import Learners"
          requiredCols={['name', 'email']}
          optionalCols={['language', 'level', 'tutor_email']}
          colHints={[
            { col: 'name', hint: 'or split into first_name + last_name' },
            { col: 'tutor_email', hint: 'must match an existing tutor in this institution' },
            { col: 'level', hint: 'A1 · A2 · B1 · B2 · C1 · C2' },
          ]}
          onClose={() => setShowImportCSVModal(false)}
          onImport={handleImportCSV}
        />
      )}

      {/* ── Import Modal — Tutors ───────────────────────────────────────── */}
      {showImportTutorCSVModal && (
        <ImportModal
          title="Import Tutors"
          requiredCols={['name', 'email']}
          optionalCols={['bio', 'qualifications', 'specializations']}
          colHints={[
            { col: 'name', hint: 'or split into first_name + last_name' },
            { col: 'specializations', hint: 'comma-separated, e.g. Dutch,English' },
          ]}
          warning="Imported tutors receive a temporary password and must reset it on first login."
          onClose={() => setShowImportTutorCSVModal(false)}
          onImport={handleImportTutorCSV}
        />
      )}

      {/* Modern Notification Modal */}
      {notification.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 animate-fadeIn">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 transform transition-all animate-slideUp">
            <div className={`p-6 rounded-t-2xl ${
              notification.type === 'success' ? 'bg-gradient-to-r from-green-50 to-emerald-50' :
              notification.type === 'error' ? 'bg-gradient-to-r from-red-50 to-rose-50' :
              'bg-gradient-to-r from-blue-50 to-cyan-50'
            }`}>
              <div className="flex items-center space-x-4">
                <div className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center ${
                  notification.type === 'success' ? 'bg-green-100' :
                  notification.type === 'error' ? 'bg-red-100' :
                  'bg-blue-100'
                }`}>
                  {notification.type === 'success' && (
                    <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                  {notification.type === 'error' && (
                    <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  )}
                  {notification.type === 'info' && (
                    <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  )}
                </div>
                <div className="flex-1">
                  <h3 className={`text-lg font-bold ${
                    notification.type === 'success' ? 'text-green-900' :
                    notification.type === 'error' ? 'text-red-900' :
                    'text-blue-900'
                  }`}>
                    {notification.title}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">{notification.message}</p>
                </div>
              </div>
            </div>
            <div className="p-4 bg-white rounded-b-2xl">
              <button
                onClick={() => setNotification({...notification, show: false})}
                className="w-full px-6 py-3 bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white rounded-lg font-medium hover:shadow-lg transform hover:scale-105 transition-all"
              >
                Got it
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modern Confirmation Modal */}
      {confirmation.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 animate-fadeIn">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 transform transition-all animate-slideUp">
            <div className="p-6 bg-gradient-to-r from-orange-50 to-amber-50 rounded-t-2xl">
              <div className="flex items-center space-x-4">
                <div className="flex-shrink-0 w-12 h-12 rounded-full bg-orange-100 flex items-center justify-center">
                  <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-orange-900">{confirmation.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{confirmation.message}</p>
                </div>
              </div>
            </div>
            <div className="p-4 bg-white rounded-b-2xl flex gap-3">
              <button
                onClick={() => setConfirmation({...confirmation, show: false})}
                className="flex-1 px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-all"
              >
                {confirmation.cancelText || 'Cancel'}
              </button>
              <button
                onClick={() => {
                  confirmation.onConfirm();
                  setConfirmation({...confirmation, show: false});
                }}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg font-medium hover:shadow-lg transform hover:scale-105 transition-all"
              >
                {confirmation.confirmText || 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tutor Learners Modal */}
      {showTutorLearnersModal && selectedTutor && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 animate-fadeIn">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full mx-4 sm:mx-auto my-8 transform transition-all animate-slideUp">
            {/* Header */}
            <div className="p-6 bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] rounded-t-2xl">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-bold text-white flex items-center">
                    <Users className="w-6 h-6 mr-2 inline-block" /> {selectedTutor.name}'s Learners
                  </h2>
                  <p className="text-white/80 text-sm mt-1">
                    {selectedTutor.learner_count} {selectedTutor.learner_count === 1 ? 'learner' : 'learners'} assigned
                  </p>
                </div>
                <button
                  onClick={() => {
                    setShowTutorLearnersModal(false);
                    setSelectedTutor(null);
                  }}
                  className="text-white hover:bg-white/20 rounded-lg p-2 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            {/* Content */}
            <div className="p-6 max-h-[70vh] sm:max-h-[60vh] overflow-y-auto">
              <div className="space-y-3">
                {selectedTutor.learners.map((learner, index) => (
                  <div 
                    key={learner.user_id}
                    className="flex items-center space-x-4 p-4 rounded-xl bg-gradient-to-r from-gray-50 to-white hover:from-[#4ECFBF]/5 hover:to-[#3a9e92]/5 transition-all border border-gray-200 hover:border-[#4ECFBF] group"
                  >
                    {/* Avatar */}
                    <div className="flex-shrink-0">
                      <div className="w-14 h-14 rounded-full bg-gradient-to-br from-[#4ECFBF] to-[#3a9e92] flex items-center justify-center text-white font-bold text-lg shadow-lg group-hover:scale-110 transition-transform">
                        {learner.name.charAt(0).toUpperCase()}
                      </div>
                    </div>
                    
                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <h3 className="font-bold text-gray-900 truncate">{learner.name}</h3>
                        <span className="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-700 font-medium">
                          #{index + 1}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 truncate">{learner.email}</p>
                      <div className="flex items-center space-x-3 mt-2">
                        {learner.language && (
                          <span className="inline-flex items-center text-xs px-2 py-1 rounded-full bg-green-100 text-green-700">
                            <FlagOrText language={learner.language} size={14} /> {learner.language ? learner.language.charAt(0).toUpperCase()+learner.language.slice(1) : ''}
                          </span>
                        )}
                        {learner.level && (
                          <span className="inline-flex items-center text-xs px-2 py-1 rounded-full bg-purple-100 text-purple-700">
                            <BarChart2 className="w-3 h-3 mr-1" /> {learner.level}
                          </span>
                        )}
                      </div>
                    </div>
                    
                    {/* Enrolled Date */}
                    <div className="text-right">
                      <p className="text-xs text-gray-500">Enrolled</p>
                      <p className="text-sm font-medium text-gray-700">
                        {learner.enrolled_at ? new Date(learner.enrolled_at).toLocaleDateString() : 'N/A'}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Footer */}
            <div className="p-4 bg-gray-50 rounded-b-2xl border-t">
              <button
                onClick={() => {
                  setShowTutorLearnersModal(false);
                  setSelectedTutor(null);
                }}
                className="w-full px-6 py-3 bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white rounded-lg font-medium hover:shadow-lg transform hover:scale-105 transition-all"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Learner Details Modal */}
      {showLearnerDetailsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full mx-2 sm:mx-4 my-8">
            {/* Header */}
            <div className="p-6 bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] rounded-t-2xl">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-white flex items-center">
                  <BarChart2 className="w-6 h-6 mr-2 inline-block" /> Learner Progress Deep Dive
                </h2>
                <button
                  onClick={() => {
                    setShowLearnerDetailsModal(false);
                    setSelectedLearnerDetails(null);
                  }}
                  className="text-white hover:bg-white/20 rounded-lg p-2"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            {/* Content */}
            <div className="p-6 max-h-[75vh] sm:max-h-[70vh] overflow-y-auto">
              {loadingLearnerDetails ? (
                <ModalSpinner label="Loading learner progress..." />
              ) : selectedLearnerDetails?.no_consent ? (
                <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
                  <div className="w-20 h-20 rounded-full bg-orange-100 flex items-center justify-center mb-6">
                    <svg className="w-10 h-10 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-3">Consent Required</h3>
                  <p className="text-gray-600 max-w-md">
                    <strong>{selectedLearnerDetails.learner_name}</strong> has not given consent to view their detailed progress data. 
                    Please ask the learner to provide consent through their dashboard settings.
                  </p>
                </div>
              ) : selectedLearnerDetails && selectedLearnerDetails.profile ? (
                <div className="space-y-6">
                  {/* Profile Section */}
                  <div className="bg-gradient-to-r from-blue-50 to-cyan-50 p-6 rounded-xl">
                    <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center"><UserCheck className="w-4 h-4 text-[#4ECFBF] inline-block mr-1.5" /> Learner Profile</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-600">Name</p>
                        <p className="font-medium text-gray-900">{selectedLearnerDetails.profile?.name || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Email</p>
                        <p className="font-medium text-gray-900">{selectedLearnerDetails.profile?.email || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Total Sessions</p>
                        <p className="font-medium text-gray-900">{selectedLearnerDetails.profile?.total_sessions || 0}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Total Minutes</p>
                        <p className="font-medium text-gray-900">{selectedLearnerDetails.profile?.total_minutes || 0}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Languages Studied</p>
                        <p className="font-medium text-gray-900">
                          {selectedLearnerDetails.profile?.languages_studied?.join(', ') || 'None'}
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  {/* All Learning Plans */}
                  {selectedLearnerDetails.all_learning_plans && selectedLearnerDetails.all_learning_plans.length > 0 && (
                    <div className="space-y-4">
                      <h3 className="text-lg font-bold text-gray-900 flex items-center"><BookOpen className="w-4 h-4 text-[#4ECFBF] inline-block mr-1.5" /> Learning Plans</h3>
                      {selectedLearnerDetails.all_learning_plans.map((plan: any, index: number) => (
                        <div key={plan.id || index} className="bg-gradient-to-r from-green-50 to-emerald-50 p-6 rounded-xl">
                          <h4 className="text-md font-bold text-gray-900 mb-3">
                            {plan.language?.charAt(0).toUpperCase() + plan.language?.slice(1)} {plan.proficiency_level}
                          </h4>
                          <div className="space-y-3">
                            <div className="flex justify-between">
                              <span className="text-gray-700">Progress:</span>
                              <span className="font-bold text-[#4ECFBF]">
                                {plan.progress_percentage?.toFixed(1) || 0}%
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-700">Sessions Completed:</span>
                              <span className="font-medium">
                                {plan.completed_sessions || 0} / {plan.total_sessions || 16}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-700">Practice Minutes Used:</span>
                              <span className="font-medium">
                                {plan.practice_minutes_used || 0} / {plan.total_practice_minutes || 80}
                              </span>
                            </div>
                            
                            {/* Progress Bar */}
                            <div className="w-full bg-gray-200 rounded-full h-3 mt-4">
                              <div 
                                className="bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] h-3 rounded-full transition-all"
                                style={{ width: `${plan.progress_percentage || 0}%` }}
                              ></div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {/* AI Insights */}
                  {selectedLearnerDetails.ai_insights && (
                    <div className="bg-gradient-to-r from-indigo-50 to-purple-50 p-6 rounded-xl">
                      <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center"><Bot className="w-4 h-4 text-[#4ECFBF] inline-block mr-1.5" /> AI-Generated Insights</h3>
                      <div className="space-y-4">
                        <p className="text-gray-700 leading-relaxed">
                          {selectedLearnerDetails.ai_insights.overall_summary}
                        </p>
                        
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t">
                          <div>
                            <p className="text-sm text-gray-600">Learning Style</p>
                            <p className="font-medium text-gray-900 capitalize">
                              {selectedLearnerDetails.ai_insights.learning_style?.preferred_time} learner
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">Progress Rate</p>
                            <p className="font-medium text-gray-900 capitalize">
                              {selectedLearnerDetails.ai_insights.progress_rate?.rate}
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">Consistency</p>
                            <p className="font-medium text-gray-900 capitalize">
                              {selectedLearnerDetails.ai_insights.engagement?.consistency}
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">Sessions/Week</p>
                            <p className="font-medium text-gray-900">
                              {selectedLearnerDetails.ai_insights.progress_rate?.sessions_per_week}
                            </p>
                          </div>
                        </div>
                        
                        {selectedLearnerDetails.ai_insights.recommendations && 
                         selectedLearnerDetails.ai_insights.recommendations.length > 0 && (
                          <div className="pt-4 border-t">
                            <p className="font-medium text-gray-900 mb-2">Recommendations:</p>
                            <ul className="space-y-2">
                              {selectedLearnerDetails.ai_insights.recommendations.map((rec: string, idx: number) => (
                                <li key={idx} className="text-sm text-gray-700 pl-4">
                                  {rec}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {/* Recent Sessions */}
                  {selectedLearnerDetails.practice_sessions && selectedLearnerDetails.practice_sessions.length > 0 && (
                    <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-6 rounded-xl">
                      <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center"><BookOpen className="w-4 h-4 text-[#4ECFBF] inline-block mr-1.5" /> Recent Sessions</h3>
                      <div className="space-y-3">
                        {selectedLearnerDetails.practice_sessions.slice(0, 5).map((session: any, idx: number) => (
                          <div key={session.id} className="flex justify-between items-center p-3 bg-white rounded-lg">
                            <div>
                              <p className="font-medium text-gray-900">Session {idx + 1}</p>
                              <p className="text-sm text-gray-600">
                                {new Date(session.created_at).toLocaleDateString()} • {session.duration_minutes} min • {session.message_count} messages
                              </p>
                            </div>
                            <span className="text-sm font-medium text-[#4ECFBF]">
                              {session.language} {session.level}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Subscription Info */}
                  {selectedLearnerDetails.subscription && (
                    <div className="bg-gradient-to-r from-yellow-50 to-orange-50 p-6 rounded-xl">
                      <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center"><Award className="w-4 h-4 text-[#4ECFBF] inline-block mr-1.5" /> Subscription</h3>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-gray-700">Status:</span>
                          <span className={`font-medium ${selectedLearnerDetails.subscription.status === 'active' ? 'text-green-600' : 'text-gray-600'}`}>
                            {selectedLearnerDetails.subscription.status}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-700">Minutes Remaining:</span>
                          <span className="font-medium">
                            {selectedLearnerDetails.subscription.minutes_remaining}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
                  <div className="w-20 h-20 rounded-full bg-gray-100 flex items-center justify-center mb-6">
                    <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-3">No Data Available</h3>
                  <p className="text-gray-600 max-w-md">
                    This learner hasn't started any learning activities yet. Check back after they complete their first practice session.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fadeIn {
          animation: fadeIn 0.2s ease-out;
        }
        .animate-slideUp {
          animation: slideUp 0.3s ease-out;
        }
      `}</style>
    </div>
  );
};
