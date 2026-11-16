import * as React from 'react'

import { cn } from '@/lib/utils'
import { Breadcrumbs, type BreadcrumbItem } from './Breadcrumbs'

export interface PageHeaderProps {
  /** Rendered as the page's single <h1>. */
  title: React.ReactNode
  description?: React.ReactNode
  breadcrumbs?: BreadcrumbItem[]
  /** Page-level actions. Put at most ONE variant="action" (orange) button here. */
  actions?: React.ReactNode
  /** Small uppercase label above the title. Use sparingly. */
  eyebrow?: React.ReactNode
  className?: string
}

export function PageHeader({ title, description, breadcrumbs, actions, eyebrow, className }: PageHeaderProps) {
  return (
    <header className={cn('mb-6 space-y-2', className)}>
      {breadcrumbs && breadcrumbs.length > 0 && <Breadcrumbs items={breadcrumbs} />}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 space-y-1">
          {eyebrow && <p className="eyebrow">{eyebrow}</p>}
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">{title}</h1>
          {description && <p className="max-w-[70ch] text-sm text-muted-foreground">{description}</p>}
        </div>
        {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
      </div>
    </header>
  )
}
