'use client'

import type { Evidence } from '@/lib/api/hooks/useEvidence'
import { LABEL, MUTED } from '@/components/packs/parts'
import { cn } from '@/lib/utils'

interface EvidenceFolderTreeProps {
  evidence: Evidence[]
  activeFolder: string | null
  onFolderChange: (folder: string | null) => void
}

const ROW =
  'flex w-full items-center gap-2 rounded-[10px] px-2.5 py-1.5 text-left text-[13px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--fm-ink)]'

export function EvidenceFolderTree({ evidence, activeFolder, onFolderChange }: EvidenceFolderTreeProps) {
  const folderCounts: Record<string, number> = {}
  let uncategorized = 0

  for (const item of evidence) {
    if (item.folder) {
      folderCounts[item.folder] = (folderCounts[item.folder] ?? 0) + 1
    } else {
      uncategorized++
    }
  }

  const folders = Object.entries(folderCounts).sort((a, b) => a[0].localeCompare(b[0]))
  const rows: Array<{ key: string; value: string | null; label: string; count: number }> = [
    { key: 'all', value: null, label: 'All evidence', count: evidence.length },
    ...(uncategorized > 0 ? [{ key: 'uncategorized', value: '__uncategorized__', label: 'Uncategorized', count: uncategorized }] : []),
    ...folders.map(([folder, count]) => ({ key: `folder:${folder}`, value: folder, label: folder, count })),
  ]

  return (
    <div>
      <h2 className={cn('m-0 mb-2 px-2.5', LABEL)}>Folders</h2>
      <div className="grid gap-0.5">
        {rows.map((row) => {
          const isActive = activeFolder === row.value
          return (
            <button
              key={row.key}
              type="button"
              aria-pressed={isActive}
              onClick={() => onFolderChange(row.value)}
              className={cn(ROW, isActive ? 'bg-[var(--fm-bg)] font-semibold text-[var(--fm-ink)]' : 'text-[var(--fm-ink2)] hover:bg-[var(--fm-bg)]')}
            >
              <span className="min-w-0 flex-1 truncate">{row.label}</span>
              <span className={cn('text-[12px] tabular-nums', MUTED)}>{row.count}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
