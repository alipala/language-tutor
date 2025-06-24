interface LogoProps {
  variant?: 'full' | 'icon'
  className?: string
  onClick?: () => void
}

export function Logo({ variant = 'full', className = '', onClick }: LogoProps) {
  if (variant === 'icon') {
    return (
      <svg 
        width="60" 
        height="60" 
        viewBox="0 0 80 80" 
        className={`cursor-pointer ${className}`}
        onClick={onClick}
      >
        {/* Turquoise gradient background */}
        <defs>
          <linearGradient id="bgGradientIcon" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{stopColor:'#4ECFBF', stopOpacity:1}} />
            <stop offset="100%" style={{stopColor:'#3da5a0', stopOpacity:1}} />
          </linearGradient>
        </defs>
        <rect width="80" height="80" rx="18" fill="url(#bgGradientIcon)"/>
        {/* Voice waveform - bigger and more recognizable */}
        <g transform="translate(12, 28)">
          <rect x="0" y="8" width="4" height="4" rx="2" fill="white"/>
          <rect x="6" y="4" width="4" height="12" rx="2" fill="white"/>
          <rect x="12" y="0" width="4" height="20" rx="2" fill="white"/>
          <rect x="18" y="6" width="4" height="8" rx="2" fill="white"/>
          <rect x="24" y="2" width="4" height="16" rx="2" fill="white"/>
          <rect x="30" y="5" width="4" height="10" rx="2" fill="white"/>
          <rect x="36" y="9" width="4" height="2" rx="2" fill="white"/>
          {/* AI indicator dot with blinking animation */}
          <circle cx="46" cy="10" r="3" fill="#F75A5A" className="animate-pulse"/>
        </g>
      </svg>
    )
  }
  
  return (
    <div className="relative -my-2">
      <svg 
        width="315" 
        height="90" 
        viewBox="0 0 630 180" 
        className={`h-22 w-auto cursor-pointer ${className}`}
        onClick={onClick}
        style={{ zIndex: 10 }}
      >
        <defs>
          <style>
            {`
              .blinking-dot {
                animation: blink-in-place 2s infinite;
              }
              @keyframes blink-in-place {
                0%, 50% { opacity: 1; }
                51%, 100% { opacity: 0.3; }
              }
            `}
          </style>
        </defs>
        {/* Voice waveform - vertically centered on My Taco text */}
        <g transform="translate(45, 67)">
          <rect x="0" y="45" width="9" height="18" rx="4.5" fill="white" opacity="0.95"/>
          <rect x="18" y="33" width="9" height="40" rx="4.5" fill="white" opacity="0.95"/>
          <rect x="36" y="22" width="9" height="63" rx="4.5" fill="white" opacity="0.95"/>
          <rect x="54" y="40" width="9" height="27" rx="4.5" fill="white" opacity="0.95"/>
          <rect x="72" y="18" width="9" height="72" rx="4.5" fill="white" opacity="0.95"/>
          <rect x="90" y="36" width="9" height="36" rx="4.5" fill="white" opacity="0.95"/>
          <rect x="108" y="49" width="9" height="9" rx="4.5" fill="white" opacity="0.95"/>
          {/* AI indicator dot with fixed position blinking animation */}
          <circle cx="130" cy="54" r="6.75" fill="#F75A5A" className="blinking-dot"/>
        </g>
        {/* Typography - Inter font, bigger and more recognizable */}
        <text x="225" y="140" fontFamily="Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif" fontSize="64" fontWeight="800" fill="white" opacity="0.95">My</text>
        <text x="340" y="140" fontFamily="Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif" fontSize="64" fontWeight="800" fill="white">TaCo</text>
      </svg>
    </div>
  )
}
