'use client'

import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface StatCardProps {
  title: string
  value: string | number
  icon?: React.ReactNode
  /** Only pass a trend when it is computed from real data. */
  trend?: {
    value: number
    label: string
    isPositive: boolean
  }
  className?: string
}

/** Legacy metric card. New pages should prefer StatTile from @/components/patterns. */
export function StatCard({ title, value, icon, trend, className }: StatCardProps) {
  return (
    <Card className={cn('p-4 sm:p-5', className)}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="mb-1 text-xs font-medium text-muted-foreground">{title}</p>
          <p className="text-2xl font-semibold tabular-nums tracking-tight">{value}</p>
          {trend && (
            <p
              className={cn(
                'mt-2 text-xs font-medium',
                trend.isPositive ? 'text-success-strong' : 'text-destructive-strong'
              )}
            >
              {trend.isPositive ? '+' : ''}{trend.value}% {trend.label}
            </p>
          )}
        </div>
        {icon && (
          <div className="rounded-md bg-muted p-2 text-muted-foreground" aria-hidden="true">
            {icon}
          </div>
        )}
      </div>
    </Card>
  )
}
