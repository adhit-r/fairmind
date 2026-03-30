'use client'

import { IconFolder, IconFolderOpen, IconStack2 } from '@tabler/icons-react'
import { Badge } from '@/components/ui/badge'
import type { Evidence } from '@/lib/api/hooks/useEvidence'

interface EvidenceFolderTreeProps {
  evidence: Evidence[]
  activeFolder: string | null
  onFolderChange: (folder: string | null) => void
}

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

  return (
    <div className="space-y-1">
      <p className="mb-2 text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
        Folders
      </p>

      <button
        type="button"
        onClick={() => onFolderChange(null)}
        className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-bold transition-colors ${
          activeFolder === null
            ? 'bg-black text-white'
            : 'hover:bg-slate-100'
        }`}
      >
        <IconStack2 className="h-4 w-4 shrink-0" />
        <span className="flex-1 text-left">All evidence</span>
        <Badge className={`border border-black/20 px-1.5 py-0 text-[10px] font-bold ${activeFolder === null ? 'bg-white/20 text-white' : 'bg-slate-200 text-black'}`}>
          {evidence.length}
        </Badge>
      </button>

      {uncategorized > 0 && (
        <button
          type="button"
          onClick={() => onFolderChange('__uncategorized__')}
          className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-bold transition-colors ${
            activeFolder === '__uncategorized__'
              ? 'bg-black text-white'
              : 'hover:bg-slate-100'
          }`}
        >
          <IconFolder className="h-4 w-4 shrink-0" />
          <span className="flex-1 text-left">Uncategorized</span>
          <Badge className={`border border-black/20 px-1.5 py-0 text-[10px] font-bold ${activeFolder === '__uncategorized__' ? 'bg-white/20 text-white' : 'bg-slate-200 text-black'}`}>
            {uncategorized}
          </Badge>
        </button>
      )}

      {folders.map(([folder, count]) => {
        const isActive = activeFolder === folder
        return (
          <button
            key={folder}
            type="button"
            onClick={() => onFolderChange(folder)}
            className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-bold transition-colors ${
              isActive ? 'bg-black text-white' : 'hover:bg-slate-100'
            }`}
          >
            {isActive ? (
              <IconFolderOpen className="h-4 w-4 shrink-0" />
            ) : (
              <IconFolder className="h-4 w-4 shrink-0" />
            )}
            <span className="flex-1 truncate text-left">{folder}</span>
            <Badge className={`border border-black/20 px-1.5 py-0 text-[10px] font-bold ${isActive ? 'bg-white/20 text-white' : 'bg-slate-200 text-black'}`}>
              {count}
            </Badge>
          </button>
        )
      })}
    </div>
  )
}
