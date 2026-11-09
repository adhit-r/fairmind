'use client'

import Link from 'next/link'
import { BTN_P, StagePill } from '@/components/packs/parts'

export interface CommandBarProps {
  stage?: string
  title: string
  /** Why this is the next step; shown on hover so the bar stays one row. */
  reason?: string
  primary?: { label: string; href?: string; onClick?: () => void; busy?: boolean; disabled?: boolean }
}

/** One row at the top of a page: the stage, what needs doing, and the one button that does it. */
export function CommandBar({ stage, title, reason, primary }: CommandBarProps) {
  return (
    <section aria-label="What to do now" className="fm-card fm-cmd flex min-h-[60px] items-center gap-3 px-[18px] py-2.5">
      {stage && (
        <span className="max-md:hidden">
          <StagePill stage={stage} />
        </span>
      )}
      <h1 className="min-w-0 flex-1 truncate text-[15px] font-semibold tracking-[-0.01em]" title={reason ?? title}>
        {title}
      </h1>
      {primary &&
        (primary.href ? (
          <Link href={primary.href} className={BTN_P}>
            {primary.label}
          </Link>
        ) : (
          <button type="button" className={BTN_P} onClick={primary.onClick} disabled={primary.busy || primary.disabled} aria-busy={primary.busy || undefined}>
            {primary.label}
          </button>
        ))}
    </section>
  )
}
