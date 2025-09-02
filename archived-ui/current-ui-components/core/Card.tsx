'use client'

import React from 'react'

interface CardProps {
  children: React.ReactNode
  className?: string
  title?: string
  subtitle?: string
  icon?: React.ReactNode
  gradient?: 'blue' | 'green' | 'orange' | 'purple' | 'red'
  hover?: boolean
}

export function Card({ 
  children, 
  className = '', 
  title, 
  subtitle, 
  icon,
  gradient,
  hover = false 
}: CardProps) {
  const gradientClasses = {
    blue: 'bg-gradient-to-r from-blue-500/10 to-purple-600/10 border-blue-500/20',
    green: 'bg-gradient-to-r from-green-500/10 to-emerald-600/10 border-green-500/20',
    orange: 'bg-gradient-to-r from-orange-500/10 to-red-600/10 border-orange-500/20',
    purple: 'bg-gradient-to-r from-purple-500/10 to-pink-600/10 border-purple-500/20',
    red: 'bg-gradient-to-r from-red-500/10 to-pink-600/10 border-red-500/20'
  }

  const baseClasses = 'bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden'
  const gradientClass = gradient ? gradientClasses[gradient] : ''
  const hoverClass = hover ? 'hover:bg-white/10 transition-all duration-300' : ''
  
  return (
    <div className={`${baseClasses} ${gradientClass} ${hoverClass} ${className}`}>
      {(title || subtitle || icon) && (
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center space-x-3">
            {icon && (
              <div className="flex-shrink-0">
                {icon}
              </div>
            )}
            <div className="flex-1">
              {title && (
                <h3 className="text-lg font-bold text-white">{title}</h3>
              )}
              {subtitle && (
                <p className="text-slate-400 text-sm mt-1">{subtitle}</p>
              )}
            </div>
          </div>
        </div>
      )}
      <div className="p-6">
        {children}
      </div>
    </div>
  )
}
