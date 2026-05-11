'use client';
import { useState, useRef, useEffect } from 'react';
import { Calendar, ChevronLeft, ChevronRight, X } from 'lucide-react';

export interface DateRange {
  start: Date | null;
  end: Date | null;
  label: string;
}

interface Props {
  value: DateRange;
  onChange: (range: DateRange) => void;
  align?: 'left' | 'right';
}

const PRESETS = [
  { label: 'All time', days: null },
  { label: 'Last 7 days', days: 7 },
  { label: 'Last 30 days', days: 30 },
  { label: 'This month', days: 'month' as const },
];

function daysAgo(n: number): Date {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() - n);
  return d;
}

function startOfMonth(): Date {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  d.setDate(1);
  return d;
}

function today(): Date {
  const d = new Date();
  d.setHours(23, 59, 59, 999);
  return d;
}

function sameDay(a: Date, b: Date) {
  return a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate();
}

function isBetween(d: Date, start: Date, end: Date) {
  return d >= start && d <= end;
}

const MONTHS = ['January','February','March','April','May','June',
  'July','August','September','October','November','December'];
const DAYS = ['Su','Mo','Tu','We','Th','Fr','Sa'];

function MonthGrid({
  year, month, rangeStart, rangeEnd, hoverDate,
  onDayClick, onDayHover,
}: {
  year: number; month: number;
  rangeStart: Date | null; rangeEnd: Date | null; hoverDate: Date | null;
  onDayClick: (d: Date) => void;
  onDayHover: (d: Date | null) => void;
}) {
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells: (Date | null)[] = Array(firstDay).fill(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(new Date(year, month, d));

  const effectiveEnd = rangeStart && !rangeEnd && hoverDate
    ? (hoverDate >= rangeStart ? hoverDate : rangeStart)
    : rangeEnd;
  const effectiveStart = rangeStart && !rangeEnd && hoverDate
    ? (hoverDate < rangeStart ? hoverDate : rangeStart)
    : rangeStart;

  return (
    <div className="select-none">
      <div className="text-sm font-bold text-gray-900 text-center mb-3">
        {MONTHS[month]} {year}
      </div>
      <div className="grid grid-cols-7 mb-1">
        {DAYS.map(d => (
          <div key={d} className="text-center text-xs font-semibold text-gray-400 py-1">{d}</div>
        ))}
      </div>
      <div className="grid grid-cols-7">
        {cells.map((date, i) => {
          if (!date) return <div key={i} />;

          const isStart = effectiveStart && sameDay(date, effectiveStart);
          const isEnd = effectiveEnd && sameDay(date, effectiveEnd);
          const inRange = effectiveStart && effectiveEnd && isBetween(date, effectiveStart, effectiveEnd);
          const isToday = sameDay(date, new Date());

          return (
            <div
              key={i}
              onClick={() => onDayClick(date)}
              onMouseEnter={() => onDayHover(date)}
              onMouseLeave={() => onDayHover(null)}
              className={`
                relative h-9 flex items-center justify-center cursor-pointer text-sm transition-all
                ${inRange && !isStart && !isEnd ? 'bg-[#4ECFBF]/15' : ''}
                ${isStart ? 'rounded-l-full' : ''}
                ${isEnd ? 'rounded-r-full' : ''}
                ${isStart && isEnd ? 'rounded-full' : ''}
              `}
            >
              <span className={`
                w-8 h-8 flex items-center justify-center rounded-full text-sm font-medium transition-all z-10
                ${isStart || isEnd
                  ? 'bg-[#4ECFBF] text-white font-bold shadow-md'
                  : inRange
                  ? 'text-[#2a9e92] font-semibold'
                  : isToday
                  ? 'ring-2 ring-[#4ECFBF]/50 text-[#4ECFBF] font-bold'
                  : 'text-gray-700 hover:bg-[#4ECFBF]/20 hover:text-[#4ECFBF]'}
              `}>
                {date.getDate()}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function DateRangePicker({ value, onChange, align = 'left' }: Props) {
  const [open, setOpen] = useState(false);
  const [phase, setPhase] = useState<'start' | 'end'>('start');
  const [tempStart, setTempStart] = useState<Date | null>(null);
  const [hoverDate, setHoverDate] = useState<Date | null>(null);
  const [viewYear, setViewYear] = useState(new Date().getFullYear());
  const [viewMonth, setViewMonth] = useState(new Date().getMonth());
  const ref = useRef<HTMLDivElement>(null);

  // Second month
  const month2 = viewMonth === 11 ? 0 : viewMonth + 1;
  const year2 = viewMonth === 11 ? viewYear + 1 : viewYear;

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setTempStart(null);
        setPhase('start');
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleDayClick = (date: Date) => {
    if (phase === 'start') {
      setTempStart(date);
      setPhase('end');
    } else {
      const start = tempStart!;
      const [s, e] = date >= start ? [start, date] : [date, start];
      const endOfDay = new Date(e); endOfDay.setHours(23, 59, 59, 999);
      onChange({ start: s, end: endOfDay, label: 'Custom' });
      setOpen(false);
      setTempStart(null);
      setPhase('start');
    }
  };

  const applyPreset = (preset: typeof PRESETS[number]) => {
    if (preset.days === null) {
      onChange({ start: null, end: null, label: 'All time' });
    } else if (preset.days === 'month') {
      onChange({ start: startOfMonth(), end: today(), label: 'This month' });
    } else {
      onChange({ start: daysAgo(preset.days), end: today(), label: preset.label });
    }
    setOpen(false);
    setTempStart(null);
    setPhase('start');
  };

  const prevMonth = () => {
    if (viewMonth === 0) { setViewMonth(11); setViewYear(y => y - 1); }
    else setViewMonth(m => m - 1);
  };
  const nextMonth = () => {
    if (viewMonth === 11) { setViewMonth(0); setViewYear(y => y + 1); }
    else setViewMonth(m => m + 1);
  };

  const formatDate = (d: Date) =>
    d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

  const hasFilter = value.start !== null;
  const displayLabel = hasFilter
    ? value.label === 'Custom'
      ? `${formatDate(value.start!)} – ${formatDate(value.end!)}`
      : value.label
    : 'All time';

  return (
    <div ref={ref} className="relative inline-block">
      {/* Trigger button */}
      <button
        onClick={() => setOpen(o => !o)}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all ${
          hasFilter
            ? 'bg-[#4ECFBF]/10 border-[#4ECFBF]/40 text-[#4ECFBF]'
            : 'bg-white border-gray-200 text-gray-500 hover:border-[#4ECFBF]/40 hover:text-[#4ECFBF]'
        }`}
      >
        <Calendar className="w-3.5 h-3.5" strokeWidth={1.8} />
        <span>{displayLabel}</span>
        {hasFilter && (
          <span
            onClick={(e) => { e.stopPropagation(); onChange({ start: null, end: null, label: 'All time' }); }}
            className="ml-0.5 hover:bg-[#4ECFBF]/20 rounded-full p-0.5 cursor-pointer"
          >
            <X className="w-3 h-3" />
          </span>
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div className={`absolute top-9 z-50 bg-white rounded-2xl shadow-2xl border border-gray-100 p-5 w-[340px] sm:w-[640px] ${
          align === 'right' ? 'right-0' : 'left-0'
        }`}>
          {/* Preset chips */}
          <div className="flex gap-2 mb-5 flex-wrap">
            {PRESETS.map(p => (
              <button
                key={p.label}
                onClick={() => applyPreset(p)}
                className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
                  value.label === p.label && !open
                    ? 'bg-[#4ECFBF] text-white border-[#4ECFBF]'
                    : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-[#4ECFBF]/10 hover:border-[#4ECFBF]/40 hover:text-[#4ECFBF]'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Phase hint */}
          <div className="flex items-center justify-between mb-4">
            <p className="text-xs text-gray-400 font-medium">
              {phase === 'start' ? '① Select start date' : '② Select end date'}
              {tempStart && phase === 'end' && (
                <span className="ml-2 text-[#4ECFBF] font-semibold">
                  From: {formatDate(tempStart)}
                </span>
              )}
            </p>
            {tempStart && (
              <button
                onClick={() => { setTempStart(null); setPhase('start'); }}
                className="text-xs text-gray-400 hover:text-gray-600 underline"
              >
                Reset
              </button>
            )}
          </div>

          {/* Dual-month calendar */}
          <div className="flex gap-6">
            {/* Month nav */}
            <div className="relative flex-1">
              <button
                onClick={prevMonth}
                className="absolute -top-0 left-0 w-7 h-7 flex items-center justify-center rounded-lg hover:bg-gray-100 text-gray-500 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <MonthGrid
                year={viewYear} month={viewMonth}
                rangeStart={tempStart ?? value.start}
                rangeEnd={tempStart ? null : value.end}
                hoverDate={hoverDate}
                onDayClick={handleDayClick}
                onDayHover={setHoverDate}
              />
            </div>

            <div className="w-px bg-gray-100 self-stretch" />

            <div className="relative flex-1">
              <button
                onClick={nextMonth}
                className="absolute -top-0 right-0 w-7 h-7 flex items-center justify-center rounded-lg hover:bg-gray-100 text-gray-500 transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
              <MonthGrid
                year={year2} month={month2}
                rangeStart={tempStart ?? value.start}
                rangeEnd={tempStart ? null : value.end}
                hoverDate={hoverDate}
                onDayClick={handleDayClick}
                onDayHover={setHoverDate}
              />
            </div>
          </div>

          {/* Footer */}
          <div className="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between">
            <p className="text-xs text-gray-400">
              {value.start && value.end
                ? `Showing: ${formatDate(value.start)} – ${formatDate(value.end)}`
                : 'Showing all sessions'}
            </p>
            <button
              onClick={() => { setOpen(false); setTempStart(null); setPhase('start'); }}
              className="px-3 py-1.5 bg-[#4ECFBF] text-white rounded-xl text-xs font-bold hover:bg-[#3a9e92] transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
