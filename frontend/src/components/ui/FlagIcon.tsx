import Image from 'next/image';

const FLAG_MAP: Record<string, string> = {
  dutch:      '/flags/dutch.svg',
  netherlands:'/flags/dutch.svg',
  nl:         '/flags/dutch.svg',
  english:    '/flags/english.svg',
  en:         '/flags/english.svg',
  uk:         '/flags/english.svg',
  french:     '/flags/french.svg',
  français:   '/flags/french.svg',
  fr:         '/flags/french.svg',
  german:     '/flags/german.svg',
  deutsch:    '/flags/german.svg',
  de:         '/flags/german.svg',
  spanish:    '/flags/spanish.svg',
  español:    '/flags/spanish.svg',
  es:         '/flags/spanish.svg',
  portuguese: '/flags/portuguese.svg',
  português:  '/flags/portuguese.svg',
  pt:         '/flags/portuguese.svg',
  italian:    '/flags/italian.svg',
  italiano:   '/flags/italian.svg',
  it:         '/flags/italian.svg',
  turkish:    '/flags/turkish.svg',
  türkçe:     '/flags/turkish.svg',
  tr:         '/flags/turkish.svg',
};

interface FlagIconProps {
  language: string;
  size?: number;
  className?: string;
}

export function FlagIcon({ language, size = 20, className = '' }: FlagIconProps) {
  const src = FLAG_MAP[language?.toLowerCase()];
  if (!src) return null;

  return (
    <Image
      src={src}
      alt={`${language} flag`}
      width={size}
      height={size}
      className={`rounded-sm object-cover flex-shrink-0 ${className}`}
      style={{ width: size, height: size }}
    />
  );
}

// Also export a version that falls back to text if no flag found
export function FlagOrText({ language, size = 20 }: { language: string; size?: number }) {
  const src = FLAG_MAP[language?.toLowerCase()];
  if (!src) {
    return <span className="text-base">🌍</span>;
  }
  return <FlagIcon language={language} size={size} />;
}
