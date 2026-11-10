'use client'

import { useState } from 'react'
import { Columns3, Workflow } from 'lucide-react'
import { Discovery } from '@/components/plan/Discovery'
import { COLUMNS, Kanban, TaskDrawer, WorkflowView } from '@/components/plan/Board'
import { usePlan, type PlanTask } from '@/lib/api/hooks/usePlan'
import { cn } from '@/lib/utils'

const when = (iso: string) => new Date(iso).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })

export default function PlanPage() {
  const plan = usePlan()
  const [view, setView] = useState<'kanban' | 'workflow'>('kanban')
  const [openKey, setOpenKey] = useState<string | null>(null)
  const d = plan.data

  if (!d) {
    return <div className="fm-card p-6 text-[13px] text-[var(--fm-ink2)]">{plan.error ?? 'Loading your plan'}</div>
  }
  if (d.status !== 'active') {
    return <Discovery d={d.discovery} onAnswer={plan.answer} onGenerate={plan.generate} />
  }

  const tasks = d.tasks ?? []
  const open: PlanTask | null = tasks.find((t) => t.key === openKey) ?? null
  const proven = d.summary?.proven ?? 0
  const pct = tasks.length ? Math.round((proven / tasks.length) * 100) : 0

  return (
    <div className="grid grid-cols-[minmax(0,1fr)] gap-4">
      <header className="flex flex-wrap items-end gap-4">
        <div className="min-w-0">
          <div className="truncate text-[12.5px] font-medium text-[var(--fm-ink2)]" title={d.discovery.map.frameworks.map((f) => f.name).join(', ')}>
            Governance plan · {d.discovery.map.frameworks.map((f) => f.name.split(/[:(]/)[0].trim()).join(', ')}
          </div>
          <h1 className="mt-1 text-[28px] font-semibold leading-tight tracking-[-.03em]">{proven} of {tasks.length} controls proven</h1>
          <div className="mt-2 flex h-2 w-[320px] max-w-full overflow-hidden rounded-full bg-[var(--fm-line)]" aria-label={`${pct}% proven`}>
            <span className="bg-[var(--fm-ink)]" style={{ width: `${pct}%` }} />
          </div>
        </div>
        <div className="ml-auto flex flex-wrap items-center gap-3 text-[12px] text-[var(--fm-ink2)]">
          {COLUMNS.filter((c) => c.key !== 'proven').map((c) => (
            <span key={c.key} className="tabular-nums">{d.summary?.[c.key] ?? 0} {c.label.toLowerCase()}</span>
          ))}
          <div role="radiogroup" aria-label="Board view" className="flex gap-0.5 rounded-full bg-white p-[3px] shadow-[0_1px_2px_rgba(20,20,30,.05)]">
            {([['kanban', 'Kanban', Columns3], ['workflow', 'Workflow', Workflow]] as const).map(([key, label, Icon]) => (
              <button key={key} type="button" role="radio" aria-checked={view === key} onClick={() => setView(key)}
                className={cn('inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[12.5px] font-medium text-[var(--fm-ink2)]', view === key && 'bg-[var(--fm-ink)] text-white')}>
                <Icon className="h-3.5 w-3.5" aria-hidden />{label}
              </button>
            ))}
          </div>
        </div>
      </header>

      {d.changes && d.changes.length > 0 && (
        <div className="fm-card flex flex-wrap items-baseline gap-x-3 gap-y-1 px-4 py-2.5 text-[12.5px]">
          <span className="font-semibold">What changed</span>
          <span className="min-w-0 flex-1 text-[var(--fm-ink2)]">{d.changes[0].summary}</span>
          <span className="text-[11.5px] text-[var(--fm-ink3)]">{when(d.changes[0].at)}</span>
        </div>
      )}

      {view === 'kanban' ? <Kanban tasks={tasks} onOpen={(t) => setOpenKey(t.key)} /> : <WorkflowView tasks={tasks} lanes={d.lanes} onOpen={(t) => setOpenKey(t.key)} />}

      <TaskDrawer t={open} tasks={tasks} onClose={() => setOpenKey(null)} onAssign={plan.assign} onAttest={plan.attest} />
    </div>
  )
}
