import * as React from 'react'
import { IconAlertTriangle, IconRefresh } from '@tabler/icons-react'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export interface ErrorStateProps {
  title?: React.ReactNode
  /** Plain-language reason. Do not show raw stack traces. */
  message?: React.ReactNode
  onRetry?: () => void
  retryLabel?: string
  className?: string
}

export function ErrorState({
  title = 'Something went wrong',
  message,
  onRetry,
  retryLabel = 'Try again',
  className,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn('flex flex-col items-start gap-3 rounded-lg border border-destructive/40 bg-destructive-subtle p-4 text-destructive-strong sm:flex-row sm:items-center', className)}
    >
      <IconAlertTriangle className="h-5 w-5 shrink-0" aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold">{title}</p>
        {message && <p className="mt-0.5 text-sm">{message}</p>}
      </div>
      {onRetry && (
        <Button type="button" variant="outline" size="sm" onClick={onRetry} className="shrink-0 text-foreground">
          <IconRefresh aria-hidden="true" />
          {retryLabel}
        </Button>
      )}
    </div>
  )
}
