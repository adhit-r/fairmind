'use client'

interface OrangeLogoProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
  showText?: boolean
}

export function OrangeLogo({ size = 'md', className = '', showText = false }: OrangeLogoProps) {
  const sizeMap = {
    sm: { width: 32, height: 32, textSize: 'text-base', gap: 'gap-2' },
    md: { width: 40, height: 40, textSize: 'text-xl', gap: 'gap-3' },
    lg: { width: 48, height: 48, textSize: 'text-2xl', gap: 'gap-4' },
  }

  const dimensions = sizeMap[size]

  return (
    <div className={`flex items-center ${dimensions.gap} ${className}`}>
      {/* Logo Image */}
      <div className="relative flex-shrink-0">
        <img
          src="/logo.png"
          alt="FairMind Logo"
          style={{
            height: `${dimensions.height}px`,
            width: 'auto',
          }}
          className="object-contain"
        />
      </div>

      {/* Text Label */}
      {showText && (
        <span
          className={`font-black ${dimensions.textSize} tracking-tight uppercase text-black`}
          style={{ letterSpacing: '-0.02em', lineHeight: '1' }}
        >
          FairMind
        </span>
      )}
    </div>
  )
}
