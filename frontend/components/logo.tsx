import Image from 'next/image';

interface LogoProps {
  variant?: 'full' | 'icon'
  context?: 'navigation' | 'footer'
  className?: string
  onClick?: () => void
}

export function Logo({ variant = 'full', context = 'navigation', className = '', onClick }: LogoProps) {
  // Use the new mytacologo.svg logo for all contexts
  const logoSrc = '/logos/mytacologo.svg';
  
  if (variant === 'icon') {
    return (
      <div 
        className={`cursor-pointer ${className}`}
        onClick={onClick}
      >
        <Image
          src={logoSrc}
          alt="MyTaCo AI Language Coach"
          width={60}
          height={60}
          className={`w-[60px] h-[60px] object-contain ${context === 'footer' ? 'mix-blend-normal' : ''}`}
          priority
        />
      </div>
    )
  }
  
  return (
    <div className="flex items-center">
      <div 
        className={`cursor-pointer ${className}`}
        onClick={onClick}
      >
        <Image
          src={logoSrc}
          alt="MyTaCo AI Language Coach"
          width={320}
          height={75}
          className="w-auto h-[75px] object-contain"
          priority
        />
      </div>
    </div>
  )
}
