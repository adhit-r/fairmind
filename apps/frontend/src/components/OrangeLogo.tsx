'use client'

interface OrangeLogoProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
  showText?: boolean
}

export function OrangeLogo({ size = 'md', className = '', showText = false }: OrangeLogoProps) {
  const sizeMap = {
    sm: { height: 'h-8', textSize: 'text-base', gap: 'gap-2' },
    md: { height: 'h-10', textSize: 'text-xl', gap: 'gap-3' },
    lg: { height: 'h-12', textSize: 'text-2xl', gap: 'gap-4' },
  }

  const dimensions = sizeMap[size]

  return (
    <div className={`flex items-center ${dimensions.gap} ${className}`}>
      {/* Logo Image */}
      <div className="relative flex-shrink-0">
        <img
          src="/logo.png"
          alt="FairMind Logo"
          className={`${dimensions.height} w-auto object-contain`}
        />
      </div>

      {/* Text Label */}
      {showText && (
        <span
          className={`font-black ${dimensions.textSize} tracking-tight uppercase text-black leading-none`}
          style={{ letterSpacing: '-0.02em' }}
        >
          FairMind
        </span>
      )}
    </div>
  )
}
