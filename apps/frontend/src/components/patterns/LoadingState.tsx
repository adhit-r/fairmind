import * as React from 'react'

import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

export interface LoadingStateProps {
  /** Announced to assistive tech. */
  label?: string
  /** Number of placeholder lines. */
  lines?: number
  className?: string
}

/** Generic block loading placeholder (flat skeleton; animation is disabled under reduced motion). */
export function LoadingState({ label = 'Loading', lines = 3, className }: LoadingStateProps) {
  return (
    <div role="status" aria-live="polite" className={cn('space-y-3 rounded-lg border border-border bg-card p-4', className)}>
      <span className="sr-only">{label}</span>
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton key={index} className={cn('h-4', index === lines - 1 ? 'w-2/3' : 'w-full')} />
      ))}
    </div>
  )
}

export interface TableSkeletonProps {
  rows?: number
  columns?: number
  label?: string
  className?: string
}

/** Placeholder for a table while its data loads. Keeps layout stable. */
export function TableSkeleton({ rows = 5, columns = 4, label = 'Loading table', className }: TableSkeletonProps) {
  const gridStyle = { gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }
  return (
    <div role="status" aria-live="polite" className={cn('overflow-hidden rounded-lg border border-border bg-card', className)}>
      <span className="sr-only">{label}</span>
      <div className="grid gap-3 border-b border-border bg-muted/60 px-3 py-3" style={gridStyle}>
        {Array.from({ length: columns }).map((_, index) => (
          <Skeleton key={index} className="h-3 w-1/2" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, row) => (
        <div key={row} className="grid gap-3 border-b border-border px-3 py-3.5 last:border-b-0" style={gridStyle}>
          {Array.from({ length: columns }).map((__, column) => (
            <Skeleton key={column} className={cn('h-4', column === 0 ? 'w-3/4' : 'w-2/3')} />
          ))}
        </div>
      ))}
    </div>
  )
}
