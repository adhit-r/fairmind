'use client'

import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface StatCardProps {
  title: string
  value: string | number
  icon?: React.ReactNode
  trend?: {
    value: number
    label: string
    isPositive: boolean
  }
  className?: string
}

export function StatCard({ title, value, icon, trend, className }: StatCardProps) {
  return (
    <Card className={cn('p-6 border-2 border-black shadow-brutal hover:shadow-brutal-lg transition-all', className)}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-muted-foreground mb-1">{title}</p>
          <p className="text-3xl font-bold">{value}</p>
          {trend && (
            <p className={cn(
              'text-xs mt-2 font-medium',
              trend.isPositive ? 'text-green-600' : 'text-red-600'
            )}>
              {trend.isPositive ? '+' : ''}{trend.value}% {trend.label}
            </p>
          )}
        </div>
        {icon && (
          <div className="p-2 border-2 border-black bg-orange shadow-brutal">
            {icon}
          </div>
        )}
      </div>
    </Card>
  )
}

