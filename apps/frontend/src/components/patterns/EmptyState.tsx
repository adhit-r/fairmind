import * as React from 'react'
import type { TablerIcon } from '@tabler/icons-react'

import { cn } from '@/lib/utils'

export interface EmptyStateProps {
  icon?: TablerIcon
  title: React.ReactNode
  description?: React.ReactNode
  /** Next-step CTA (usually a Button or Button asChild + Link). */
  action?: React.ReactNode
  className?: string
}

/** Instructive empty state. Always tell the user what to do next. */
export function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-card px-6 py-10 text-center', className)}>
      {Icon && (
        <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-md bg-muted text-muted-foreground">
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
      )}
      <p className="text-base font-semibold text-foreground">{title}</p>
      {description && <p className="mt-1 max-w-[60ch] text-sm text-muted-foreground">{description}</p>}
      {action && <div className="mt-4 flex flex-wrap items-center justify-center gap-2">{action}</div>}
    </div>
  )
}
