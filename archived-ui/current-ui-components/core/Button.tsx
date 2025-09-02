'use client'

import React from 'react'
import { LucideIcon } from 'lucide-react'

interface ButtonProps {
  children: React.ReactNode
  onClick?: () => void
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  icon?: LucideIcon
  iconPosition?: 'left' | 'right'
  disabled?: boolean
  loading?: boolean
  className?: string
  type?: 'button' | 'submit' | 'reset'
}

export function Button({ 
  children, 
  onClick, 
  variant = 'primary', 
  size = 'md',
  icon: Icon,
  iconPosition = 'left',
  disabled = false,
  loading = false,
  className = '',
  type = 'button'
}: ButtonProps) {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-xl transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900'
  
  const variantClasses = {
    primary: 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white shadow-lg hover:shadow-xl transform hover:scale-105',
    secondary: 'bg-white/10 hover:bg-white/20 text-white border border-white/20',
    outline: 'bg-transparent border border-white/20 text-white hover:bg-white/10',
    ghost: 'bg-transparent text-slate-400 hover:text-white hover:bg-white/5',
    danger: 'bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700 text-white shadow-lg hover:shadow-xl'
  }
  
  const sizeClasses = {
    sm: 'px-3 py-2 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  }
  
  const disabledClasses = disabled || loading ? 'opacity-50 cursor-not-allowed transform-none' : ''
  
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${disabledClasses} ${className}`}
    >
      {loading && (
        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
      )}
      {Icon && iconPosition === 'left' && !loading && (
        <Icon className={`h-4 w-4 ${size === 'lg' ? 'mr-3' : 'mr-2'}`} />
      )}
      {children}
      {Icon && iconPosition === 'right' && (
        <Icon className={`h-4 w-4 ${size === 'lg' ? 'ml-3' : 'ml-2'}`} />
      )}
    </button>
  )
}
