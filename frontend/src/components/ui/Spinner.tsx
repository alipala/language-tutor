'use client';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  label?: string;
  fullPage?: boolean;
  overlay?: boolean;
}

const SIZE_MAP = {
  sm: 'w-5 h-5',
  md: 'w-8 h-8',
  lg: 'w-12 h-12',
  xl: 'w-16 h-16',
};

export function Spinner({ size = 'md', label, fullPage = false, overlay = false }: SpinnerProps) {
  const spinner = (
    <div className="flex flex-col items-center justify-center gap-3">
      <div className="relative">
        {/* Outer ring */}
        <div className={`${SIZE_MAP[size]} rounded-full border-4 border-brand/20`} />
        {/* Spinning arc */}
        <div
          className={`${SIZE_MAP[size]} rounded-full border-4 border-transparent border-t-[#4ECFBF] border-r-[#4ECFBF]/60 animate-spin absolute inset-0`}
          style={{ animationDuration: '0.75s' }}
        />
      </div>
      {label && (
        <p className="text-sm text-gray-400 font-medium animate-pulse">{label}</p>
      )}
    </div>
  );

  if (overlay) {
    return (
      <div className="absolute inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-20 rounded-xl">
        {spinner}
      </div>
    );
  }

  if (fullPage) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        {spinner}
      </div>
    );
  }

  return spinner;
}

export function TableLoadingSkeleton({ rows = 5, cols = 6 }: { rows?: number; cols?: number }) {
  return (
    <div className="p-6 space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 animate-pulse" style={{ animationDelay: `${i * 80}ms` }}>
          <div className="w-9 h-9 bg-gray-100 rounded-xl flex-shrink-0" />
          {Array.from({ length: cols - 1 }).map((_, j) => (
            <div
              key={j}
              className="h-9 bg-gray-100 rounded-lg flex-1"
              style={{ opacity: 1 - j * 0.12 }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

export function CardLoadingSkeleton({ cards = 4 }: { cards?: number }) {
  return (
    <div className={`grid grid-cols-2 md:grid-cols-${Math.min(cards, 4)} gap-4`}>
      {Array.from({ length: cards }).map((_, i) => (
        <div key={i} className="bg-white rounded-2xl border border-gray-100 p-5 animate-pulse" style={{ animationDelay: `${i * 100}ms` }}>
          <div className="flex justify-between mb-3">
            <div className="h-3 w-20 bg-gray-100 rounded-full" />
            <div className="w-7 h-7 bg-gray-100 rounded-lg" />
          </div>
          <div className="h-8 w-16 bg-gray-100 rounded-lg" />
        </div>
      ))}
    </div>
  );
}

export function ModalSpinner({ label = 'Loading data...' }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-4">
      <div className="relative">
        <div className="w-14 h-14 rounded-full border-4 border-brand/15" />
        <div
          className="w-14 h-14 rounded-full border-4 border-transparent border-t-[#4ECFBF] border-r-[#4ECFBF]/50 animate-spin absolute inset-0"
          style={{ animationDuration: '0.7s' }}
        />
        <div
          className="w-8 h-8 rounded-full border-3 border-transparent border-b-[#3a9e92]/60 animate-spin absolute inset-3"
          style={{ animationDuration: '1.1s', animationDirection: 'reverse', borderWidth: 3 }}
        />
      </div>
      <p className="text-sm text-gray-400 font-medium">{label}</p>
    </div>
  );
}
