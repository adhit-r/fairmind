'use client'

import { IconTag, IconX } from '@tabler/icons-react'
import { Badge } from '@/components/ui/badge'
import type { Evidence } from '@/lib/api/hooks/useEvidence'

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
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
          Tags
        </p>
        {activeTags.length > 0 && (
          <button
            type="button"
            onClick={onClearTags}
            className="flex items-center gap-1 text-[10px] font-bold text-muted-foreground hover:text-black"
          >
            <IconX className="h-3 w-3" />
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
              onClick={() => onTagToggle(tag)}
              className="flex items-center gap-1"
            >
              <Badge
                className={`cursor-pointer border-2 border-black px-2 py-0.5 text-[11px] font-bold transition-colors ${
                  isActive
                    ? 'bg-black text-white'
                    : 'bg-white text-black hover:bg-slate-100'
                }`}
              >
                <IconTag className="mr-1 h-2.5 w-2.5" />
                {tag}
                <span className={`ml-1 ${isActive ? 'text-white/70' : 'text-muted-foreground'}`}>
                  {count}
                </span>
              </Badge>
            </button>
          )
        })}
      </div>
    </div>
  )
}
