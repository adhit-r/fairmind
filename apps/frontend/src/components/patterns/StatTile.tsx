import * as React from 'react'
import Link from 'next/link'

import { cn } from '@/lib/utils'
import type { StatusTone } from './status'

export interface StatTileProps {
  label: string
  /** Real value only. Pass "Not available" with a hint when unknown; never invent a number. */
  value: React.ReactNode
  hint?: React.ReactNode
  /** Makes the whole tile a link. */
  href?: string
  /** Optional semantic emphasis of the value (e.g. critical for blockers > 0). */
  tone?: StatusTone
  className?: string
}

const VALUE_TONE: Record<StatusTone, string> = {
  neutral: 'text-foreground',
  info: 'text-info-strong',
  success: 'text-success-strong',
  warning: 'text-warning-strong',
  critical: 'text-destructive-strong',
  attention: 'text-attention-strong',
}

/** Single flat metric. No trend arrows, no sparklines. */
export function StatTile({ label, value, hint, href, tone = 'neutral', className }: StatTileProps) {
  const body = (
    <>
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className={cn('mt-1 text-2xl font-semibold tabular-nums tracking-tight', VALUE_TONE[tone])}>{value}</p>
      {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
    </>
  )
  const classes = cn('block rounded-lg border border-border bg-card p-4', className)
  if (href) {
    return (
      <Link
        href={href}
        className={cn(classes, 'transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring')}
      >
        {body}
      </Link>
    )
  }
  return <div className={classes}>{body}</div>
}
