'use client'

import Link from 'next/link'
import { BTN_P, StagePill } from '@/components/packs/parts'
import { cn } from '@/lib/utils'

export interface CommandBarProps {
  stage?: string
  title: string
  /** Why this is the next step; shown on hover so the bar stays one row. */
  reason?: string
  primary?: { label: string; href?: string; onClick?: () => void; busy?: boolean; disabled?: boolean }
}

/** One row at the top of a page: the stage, what needs doing, and the one button that does it. Below 768px the button drops to a full-width second line. */
export function CommandBar({ stage, title, reason, primary }: CommandBarProps) {
  return (
    <section aria-label="What to do now" className="fm-card fm-cmd flex min-h-[60px] items-center gap-3 px-[18px] py-2.5 max-md:flex-wrap max-md:py-3">
      {stage && <StagePill stage={stage} />}
      <h1 className="min-w-0 flex-1 text-[15px] max-md:line-clamp-2 md:truncate font-semibold tracking-[-0.01em]" title={reason ?? title}>
        {title}
      </h1>
      {primary &&
        (primary.href ? (
          <Link href={primary.href} className={cn(BTN_P, 'max-md:w-full')}>
            {primary.label}
          </Link>
        ) : (
          <button type="button" className={cn(BTN_P, 'max-md:w-full')} onClick={primary.onClick} disabled={primary.busy || primary.disabled} aria-busy={primary.busy || undefined}>
            {primary.label}
          </button>
        ))}
    </section>
  )
}
