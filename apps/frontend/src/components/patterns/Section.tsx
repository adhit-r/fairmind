import * as React from 'react'

import { cn } from '@/lib/utils'

export interface SectionProps {
  title: React.ReactNode
  description?: React.ReactNode
  actions?: React.ReactNode
  /** Optional id; also used to label the region. */
  id?: string
  className?: string
  children?: React.ReactNode
}

/** Titled page region with an <h2>. Flat: no card chrome. Wrap content in a bordered div/table as needed. */
export function Section({ title, description, actions, id, className, children }: SectionProps) {
  const generatedId = React.useId()
  const headingId = `${id ?? generatedId}-heading`
  return (
    <section id={id} aria-labelledby={headingId} className={cn('mb-8 space-y-3', className)}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div className="min-w-0">
          <h2 id={headingId} className="text-base font-semibold text-foreground">{title}</h2>
          {description && <p className="mt-0.5 max-w-[70ch] text-sm text-muted-foreground">{description}</p>}
        </div>
        {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
      </div>
      {children}
    </section>
  )
}
