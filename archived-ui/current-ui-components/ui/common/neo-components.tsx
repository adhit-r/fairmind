"use client"

import React from 'react'
import { cn } from '@/lib/utils'

// Neobrutalism Alert Component
interface NeoAlertProps {
  variant?: 'danger' | 'warning' | 'success' | 'info'
  title?: string
  children: React.ReactNode
  className?: string
  icon?: React.ReactNode
}

export function NeoAlert({ 
  variant = 'info', 
  title, 
  children, 
  className,
  icon 
}: NeoAlertProps) {
  return (
    <div className={cn(
      'neo-alert',
      `neo-alert--${variant}`,
      className
    )}>
      <div className="flex items-start gap-3">
        {icon && <div className="flex-shrink-0">{icon}</div>}
        <div className="flex-1">
          {title && (
            <h4 className="neo-text neo-text--bold mb-1 text-lg">
              {title}
            </h4>
          )}
          <div className="neo-text">{children}</div>
        </div>
      </div>
    </div>
  )
}

// Neobrutalism Card Component
interface NeoCardProps {
  variant?: 'default' | 'achievement' | 'compliance' | 'risk' | 'warning' | 'info'
  title?: string
  children: React.ReactNode
  className?: string
  icon?: React.ReactNode
  action?: React.ReactNode
}

export function NeoCard({ 
  variant = 'default', 
  title, 
  children, 
  className,
  icon,
  action 
}: NeoCardProps) {
  return (
    <div className={cn(
      'neo-card',
      variant !== 'default' && `neo-card--${variant}`,
      className
    )}>
      {(title || icon) && (
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            {icon && <div className="flex-shrink-0">{icon}</div>}
            {title && (
              <h3 className="neo-heading neo-heading--md">{title}</h3>
            )}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div className="neo-text">{children}</div>
    </div>
  )
}

// Neobrutalism Button Component
interface NeoButtonProps {
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'info'
  size?: 'sm' | 'md' | 'lg'
  children: React.ReactNode
  className?: string
  onClick?: () => void
  disabled?: boolean
  icon?: React.ReactNode
}

export function NeoButton({ 
  variant = 'primary', 
  size = 'md',
  children, 
  className,
  onClick,
  disabled = false,
  icon 
}: NeoButtonProps) {
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  }

  return (
    <button
      className={cn(
        'neo-button',
        `neo-button--${variant}`,
        sizeClasses[size],
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
      onClick={onClick}
      disabled={disabled}
    >
      <div className="flex items-center gap-2">
        {icon && <span>{icon}</span>}
        <span>{children}</span>
      </div>
    </button>
  )
}

// Neobrutalism Badge Component
interface NeoBadgeProps {
  variant?: 'success' | 'warning' | 'danger' | 'info'
  children: React.ReactNode
  className?: string
  icon?: React.ReactNode
}

export function NeoBadge({ 
  variant = 'info', 
  children, 
  className,
  icon 
}: NeoBadgeProps) {
  return (
    <span className={cn(
      'neo-badge',
      `neo-badge--${variant}`,
      className
    )}>
      {icon && <span>{icon}</span>}
      <span>{children}</span>
    </span>
  )
}

// Neobrutalism Progress Bar Component
interface NeoProgressProps {
  value: number
  max?: number
  variant?: 'success' | 'warning' | 'danger'
  label?: string
  className?: string
}

export function NeoProgress({ 
  value, 
  max = 100, 
  variant = 'success',
  label,
  className 
}: NeoProgressProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100)

  return (
    <div className={cn('space-y-2', className)}>
      {label && (
        <div className="flex justify-between items-center">
          <span className="neo-text neo-text--bold">{label}</span>
          <span className="neo-text">{Math.round(percentage)}%</span>
        </div>
      )}
      <div className="neo-progress">
        <div 
          className={cn(
            'neo-progress__bar',
            `neo-progress__bar--${variant}`
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

// Neobrutalism Heading Component
interface NeoHeadingProps {
  level?: 1 | 2 | 3 | 4 | 5 | 6
  size?: 'xl' | 'lg' | 'md'
  children: React.ReactNode
  className?: string
}

export function NeoHeading({ 
  level = 1, 
  size = 'lg',
  children, 
  className 
}: NeoHeadingProps) {
  const Tag = `h${level}` as keyof React.JSX.IntrinsicElements
  
  return (
    <Tag className={cn(
      'neo-heading',
      `neo-heading--${size}`,
      className
    )}>
      {children}
    </Tag>
  )
}

// Neobrutalism Text Component
interface NeoTextProps {
  variant?: 'default' | 'bold'
  children: React.ReactNode
  className?: string
}

export function NeoText({ 
  variant = 'default', 
  children, 
  className 
}: NeoTextProps) {
  return (
    <div className={cn(
      'neo-text',
      variant === 'bold' && 'neo-text--bold',
      className
    )}>
      {children}
    </div>
  )
}

// Neobrutalism Container Component
interface NeoContainerProps {
  children: React.ReactNode
  className?: string
}

export function NeoContainer({ children, className }: NeoContainerProps) {
  return (
    <div className={cn('neo-container', className)}>
      {children}
    </div>
  )
}

// Neobrutalism Grid Component
interface NeoGridProps {
  columns?: 2 | 3 | 4
  children: React.ReactNode
  className?: string
}

export function NeoGrid({ columns = 2, children, className }: NeoGridProps) {
  return (
    <div className={cn(
      'neo-grid',
      `neo-grid--${columns}`,
      className
    )}>
      {children}
    </div>
  )
}

// Neobrutalism Achievement Card Component
interface NeoAchievementProps {
  title: string
  description: string
  icon: React.ReactNode
  progress?: number
  maxProgress?: number
  className?: string
}

export function NeoAchievement({ 
  title, 
  description, 
  icon, 
  progress,
  maxProgress = 100,
  className 
}: NeoAchievementProps) {
  const isComplete = progress !== undefined && progress >= maxProgress

  return (
    <NeoCard 
      variant="achievement" 
      className={cn(
        isComplete && 'neo-pulse',
        className
      )}
      icon={icon}
      title={title}
    >
      <NeoText className="mb-3">{description}</NeoText>
      {progress !== undefined && (
        <NeoProgress 
          value={progress} 
          max={maxProgress}
          variant={isComplete ? 'success' : 'warning'}
          label="Progress"
        />
      )}
      {isComplete && (
        <NeoBadge variant="success" className="mt-3">
          🎉 Complete!
        </NeoBadge>
      )}
    </NeoCard>
  )
}

// Neobrutalism Compliance Score Card Component
interface NeoComplianceScoreProps {
  title: string
  score: number
  maxScore?: number
  status: 'excellent' | 'good' | 'fair' | 'poor'
  description: string
  className?: string
}

export function NeoComplianceScore({ 
  title, 
  score, 
  maxScore = 100,
  status,
  description,
  className 
}: NeoComplianceScoreProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'excellent': return 'success'
      case 'good': return 'info'
      case 'fair': return 'warning'
      case 'poor': return 'danger'
      default: return 'info'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'excellent': return '🏆'
      case 'good': return '✅'
      case 'fair': return '⚠️'
      case 'poor': return '❌'
      default: return 'ℹ️'
    }
  }

  return (
    <NeoCard 
      variant="compliance" 
      className={className}
      title={title}
      icon={<span className="text-2xl">{getStatusIcon(status)}</span>}
    >
      <div className="space-y-4">
        <div className="text-center">
          <NeoHeading size="xl" className="text-6xl mb-2">
            {score}
          </NeoHeading>
          <NeoText className="text-lg">out of {maxScore}</NeoText>
        </div>
        
        <NeoProgress 
          value={score} 
          max={maxScore}
          variant={getStatusColor(status) as any}
        />
        
        <NeoText>{description}</NeoText>
        
        <NeoBadge variant={getStatusColor(status) as any}>
          {status.toUpperCase()}
        </NeoBadge>
      </div>
    </NeoCard>
  )
}

// Neobrutalism Risk Alert Component
interface NeoRiskAlertProps {
  title: string
  description: string
  severity: 'low' | 'medium' | 'high' | 'critical' | 'info'
  recommendations?: string[]
  className?: string
}

export function NeoRiskAlert({ 
  title, 
  description, 
  severity,
  recommendations = [],
  className 
}: NeoRiskAlertProps) {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low': return 'info'
      case 'medium': return 'warning'
      case 'high': return 'danger'
      case 'critical': return 'danger'
      case 'info': return 'info'
      default: return 'info'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'low': return 'ℹ️'
      case 'medium': return '⚠️'
      case 'high': return '🚨'
      case 'critical': return '💥'
      case 'info': return 'ℹ️'
      default: return 'ℹ️'
    }
  }

  return (
    <NeoAlert 
      variant={getSeverityColor(severity) as any}
      title={title}
      icon={<span className="text-2xl">{getSeverityIcon(severity)}</span>}
      className={cn(
        severity === 'critical' && 'neo-pulse',
        className
      )}
    >
      <div className="space-y-3">
        <NeoText>{description}</NeoText>
        
        {recommendations.length > 0 && (
          <div>
            <NeoText variant="bold" className="mb-2">Recommendations:</NeoText>
            <ul className="space-y-1">
              {recommendations.map((rec, index) => (
                <li key={index} className="neo-text flex items-start gap-2">
                  <span>•</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        <NeoBadge variant={getSeverityColor(severity) as any}>
          {severity.toUpperCase()} RISK
        </NeoBadge>
      </div>
    </NeoAlert>
  )
}
