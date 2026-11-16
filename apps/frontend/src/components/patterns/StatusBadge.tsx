import * as React from 'react'
import {
  IconAlertTriangle,
  IconCircleCheck,
  IconCircleDashed,
  IconCircleX,
  IconEye,
  IconInfoCircle,
  type TablerIcon,
} from '@tabler/icons-react'

import { cn } from '@/lib/utils'
import type { StatusResult, StatusTone } from './status'

export const statusToneClasses: Record<StatusTone, string> = {
  neutral: 'border-border bg-muted text-muted-foreground',
  info: 'border-info/30 bg-info-subtle text-info-strong',
  success: 'border-success/30 bg-success-subtle text-success-strong',
  warning: 'border-warning/40 bg-warning-subtle text-warning-strong',
  critical: 'border-destructive/40 bg-destructive-subtle text-destructive-strong',
  attention: 'border-attention/50 bg-attention-subtle text-attention-strong',
}

const TONE_ICONS: Record<StatusTone, TablerIcon> = {
  neutral: IconCircleDashed,
  info: IconInfoCircle,
  success: IconCircleCheck,
  warning: IconAlertTriangle,
  critical: IconCircleX,
  attention: IconEye,
}

export interface StatusBadgeProps
  extends Partial<Pick<StatusResult, 'tone'>>,
    Omit<React.HTMLAttributes<HTMLSpanElement>, 'children'> {
  /** Visible text. Required: status is never conveyed by colour alone. */
  label: string
  /** Hide the leading tone icon (the label still carries the meaning). */
  hideIcon?: boolean
}

/**
 * Labelled status chip. Use the domain helpers to choose tone and label:
 *   <StatusBadge {...verdictTone(run.verdict)} />
 */
export function StatusBadge({ tone = 'neutral', label, hideIcon = false, className, ...props }: StatusBadgeProps) {
  const Icon = TONE_ICONS[tone]
  return (
    <span
      data-tone={tone}
      className={cn(
        'inline-flex max-w-full items-center gap-1 whitespace-nowrap rounded-md border px-2 py-0.5 text-xs font-medium',
        statusToneClasses[tone],
        className,
      )}
      {...props}
    >
      {!hideIcon && <Icon className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />}
      <span className="truncate">{label}</span>
    </span>
  )
}
