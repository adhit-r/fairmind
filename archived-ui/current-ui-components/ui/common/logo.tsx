import React from 'react'

interface LogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  className?: string
  showText?: boolean
}

export function Logo({ size = 'md', className = '', showText = true }: LogoProps) {
  const sizeClasses = {
    sm: 'h-6 w-6',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16'
  }

  const textSizes = {
    sm: 'text-sm',
    md: 'text-lg',
    lg: 'text-2xl',
    xl: 'text-3xl'
  }

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Logo Icon - Brain with Circuit Board */}
      <div className={`${sizeClasses[size]} relative`}>
        <svg
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full"
        >
          {/* Brain outline */}
          <path
            d="M12 2C8.5 2 6 4.5 6 8c0 2.5 1.5 4.5 3 5.5C7.5 15 6 17 6 19.5V22h12v-2.5c0-2.5-1.5-4.5-3-6C16.5 12.5 18 10.5 18 8c0-3.5-2.5-6-6-6z"
            stroke="currentColor"
            strokeWidth="2"
            fill="none"
          />
          {/* Brain folds */}
          <path
            d="M8 6c0-1.5 1-2.5 2.5-2.5S13 4.5 13 6"
            stroke="currentColor"
            strokeWidth="1.5"
            fill="none"
          />
          <path
            d="M7 9c0-1 0.5-1.5 1.5-1.5S10 8 10 9"
            stroke="currentColor"
            strokeWidth="1.5"
            fill="none"
          />
          <path
            d="M14 9c0-1-0.5-1.5-1.5-1.5S11 8 11 9"
            stroke="currentColor"
            strokeWidth="1.5"
            fill="none"
          />
          <path
            d="M9 12c0-0.5 0.25-0.75 0.75-0.75S10.5 11.5 10.5 12"
            stroke="currentColor"
            strokeWidth="1.5"
            fill="none"
          />
          <path
            d="M13.5 12c0-0.5-0.25-0.75-0.75-0.75S12 11.5 12 12"
            stroke="currentColor"
            strokeWidth="1.5"
            fill="none"
          />
          
          {/* Circuit board elements */}
          <rect x="16" y="4" width="2" height="2" fill="currentColor" />
          <rect x="16" y="8" width="2" height="2" fill="currentColor" />
          <rect x="16" y="12" width="2" height="2" fill="currentColor" />
          <rect x="16" y="16" width="2" height="2" fill="currentColor" />
          
          {/* Circuit connections */}
          <path d="M18 5h2" stroke="currentColor" strokeWidth="1" />
          <path d="M18 9h2" stroke="currentColor" strokeWidth="1" />
          <path d="M18 13h2" stroke="currentColor" strokeWidth="1" />
          <path d="M18 17h2" stroke="currentColor" strokeWidth="1" />
          
          {/* Vertical connections */}
          <path d="M19 6v2" stroke="currentColor" strokeWidth="1" />
          <path d="M19 10v2" stroke="currentColor" strokeWidth="1" />
          <path d="M19 14v2" stroke="currentColor" strokeWidth="1" />
        </svg>
      </div>
      
      {/* Logo Text */}
      {showText && (
        <div className={`font-bold tracking-tight ${textSizes[size]} text-slate-900 dark:text-white`}>
          FAIRMIND
        </div>
      )}
    </div>
  )
}
