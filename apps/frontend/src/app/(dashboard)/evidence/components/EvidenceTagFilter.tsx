'use client'

import type { Evidence } from '@/lib/api/hooks/useEvidence'
import { LABEL } from '@/components/packs/parts'
import { cn } from '@/lib/utils'

interface EvidenceTagFilterProps {
  evidence: Evidence[]
  activeTags: string[]
  onTagToggle: (tag: string) => void
  onClearTags: () => void
}

export function EvidenceTagFilter({ evidence, activeTags, onTagToggle, onClearTags }: EvidenceTagFilterProps) {
  const tagCounts: Record<string, number> = {}
  for (const item of evidence) {
    for (const tag of item.tags ?? []) {
      tagCounts[tag] = (tagCounts[tag] ?? 0) + 1
    }
  }

  const tags = Object.entries(tagCounts).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))

  if (tags.length === 0) return null

  return (
    <div className="border-t border-[var(--fm-line)] pt-4">
      <div className="mb-2 flex items-center justify-between px-2.5">
        <h2 className={cn('m-0', LABEL)}>Tags</h2>
        {activeTags.length > 0 && (
          <button
            type="button"
            onClick={onClearTags}
            className="text-[12px] font-medium text-[var(--fm-ink2)] hover:text-[var(--fm-ink)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--fm-ink)]"
          >
            Clear
          </button>
        )}
      </div>
      <div className="flex flex-wrap gap-1.5">
        {tags.map(([tag, count]) => {
          const isActive = activeTags.includes(tag)
          return (
            <button
              key={tag}
              type="button"
              aria-pressed={isActive}
              onClick={() => onTagToggle(tag)}
              className={cn(
                'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[12px] font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--fm-ink)]',
                isActive ? 'bg-[var(--fm-ink)] text-white' : 'bg-[var(--fm-bg)] text-[var(--fm-ink2)] hover:text-[var(--fm-ink)]',
              )}
            >
              {tag}
              <span className={cn('tabular-nums', isActive ? 'text-white/70' : 'text-[var(--fm-ink3)]')}>{count}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
