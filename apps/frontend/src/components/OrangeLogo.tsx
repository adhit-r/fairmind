'use client'

import { cn } from '@/lib/utils'

interface OrangeLogoProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
  showText?: boolean
}

export function OrangeLogo({ size = 'md', className = '', showText = false }: OrangeLogoProps) {
  const sizeMap = {
    sm: { height: 'h-7', textSize: 'text-base', gap: 'gap-2' },
    md: { height: 'h-8', textSize: 'text-lg', gap: 'gap-2' },
    lg: { height: 'h-12', textSize: 'text-2xl', gap: 'gap-3' },
  }

  const dimensions = sizeMap[size]

  return (
    <div className={cn('flex items-center', dimensions.gap, className)}>
      {/* Decorative when the wordmark is shown; otherwise it carries the name */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/logo.png"
        alt={showText ? '' : 'FairMind'}
        className={cn(dimensions.height, 'w-auto flex-shrink-0 object-contain')}
      />
      {showText && (
        <span className={cn('font-semibold leading-none tracking-tight text-foreground', dimensions.textSize)}>
          FairMind
        </span>
      )}
    </div>
  )
}
