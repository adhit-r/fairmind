'use client'

import Link from 'next/link'
import { useState, type ReactNode } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useRisks, type Risk, type RiskSummary, type SuggestedRisk } from '@/lib/api/hooks/useRisks'
import { useSystemContext, type AISystemSummary } from '@/components/workflow/SystemContext'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { riskAssessmentSchema, type RiskAssessmentFormData } from '@/lib/validations/schemas'
import { useToast } from '@/hooks/use-toast'
import { BTN, BTN_P, LABEL, MUTED, Pill, cap } from '@/components/packs/parts'

const RISK_TYPES = ['bias', 'compliance', 'monitoring', 'security', 'explainability', 'documentation']
const SEVERITIES = ['low', 'medium', 'high', 'critical'] as const
const SEVERITY_TONE = { critical: 'block', high: 'warn', medium: 'plain', low: 'plain' } as const

const field =
  'h-9 w-full rounded-[10px] border border-[rgba(21,23,26,.14)] bg-white px-3 text-[13.5px] outline-none focus:border-[var(--fm-ink)]'
const label = 'block text-[12px] font-medium text-[var(--fm-ink2)]'
const errorText = 'text-[12.5px] text-[#b4232c]'

function when(iso?: string | null) {
  const d = iso ? new Date(iso) : null
  return d && !Number.isNaN(d.getTime()) ? d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : ''
}

function Severity({ value }: { value: string }) {
  return <Pill tone={SEVERITY_TONE[value as keyof typeof SEVERITY_TONE] ?? 'plain'}>{cap(value)}</Pill>
}

function Fact({ name, value }: { name: string; value: ReactNode }) {
  return (
    <div className="min-w-0">
      <div className={LABEL}>{name}</div>
      <div className="mt-0.5 truncate text-[13.5px] tabular-nums">{value}</div>
    </div>
  )
}

function Crumb() {
  return (
    <div className="text-[12.5px] font-medium text-[var(--fm-ink2)]">
      <Link href="/dashboard" className="hover:text-[var(--fm-ink)]">Today</Link> · Findings
    </div>
  )
}

function AssessForm({ system, onSubmit, onCancel }: { system: AISystemSummary; onSubmit: (data: RiskAssessmentFormData) => Promise<void>; onCancel: () => void }) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RiskAssessmentFormData>({
    resolver: zodResolver(riskAssessmentSchema),
    defaultValues: { systemId: system.id, riskType: 'bias', severity: 'medium', description: '' },
  })

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="grid gap-3">
      <input type="hidden" {...register('systemId')} />
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className={label} htmlFor="riskType">Risk type</label>
          <select id="riskType" {...register('riskType')} aria-invalid={Boolean(errors.riskType)} aria-describedby={errors.riskType ? 'riskType-error' : undefined} className={`${field} capitalize`}>
            {RISK_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
          {errors.riskType && <p id="riskType-error" className={errorText}>{errors.riskType.message}</p>}
        </div>
        <div>
          <label className={label} htmlFor="severity">Severity</label>
          <select id="severity" {...register('severity')} aria-invalid={Boolean(errors.severity)} aria-describedby={errors.severity ? 'severity-error' : undefined} className={`${field} capitalize`}>
            {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          {errors.severity && <p id="severity-error" className={errorText}>{errors.severity.message}</p>}
        </div>
      </div>
      <div>
        <label className={label} htmlFor="description">What is the risk?</label>
        <textarea id="description" rows={4} {...register('description')} aria-invalid={Boolean(errors.description)} aria-describedby={errors.description ? 'description-error' : undefined} className={`${field} h-auto py-2`} />
        {errors.description && <p id="description-error" className={errorText}>{errors.description.message}</p>}
      </div>
      <div className="flex gap-2">
        <button type="submit" disabled={isSubmitting} className={`${BTN_P} flex-1`}>{isSubmitting ? 'Recording' : 'Record finding'}</button>
        <button type="button" onClick={onCancel} className={BTN}>Cancel</button>
      </div>
    </form>
  )
}

function FindingRow({ risk }: { risk: Risk }) {
  const byPerson = risk.source === 'manual_assessment'
  return (
    <li className="grid gap-3 border-t border-[var(--fm-line)] py-3.5 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2 text-[13.5px] font-semibold">
          <span>{risk.title}</span>
          <Severity value={risk.severity} />
        </div>
        {risk.description && <p className={`mt-1 line-clamp-2 text-[12.5px] ${MUTED}`}>{risk.description}</p>}
        <p className={`mt-1 text-[12px] ${MUTED}`}>
          {[cap(risk.status), byPerson ? 'Recorded by a person' : 'Raised by FairMind', when(risk.timestamp)].filter(Boolean).join(' · ')}
        </p>
      </div>
      <Link
        className={BTN}
        href={{
          pathname: '/remediation',
          query: { riskId: risk.id, title: risk.title, description: risk.description, priority: risk.severity, source: 'risk' },
        }}
      >
        Create task
      </Link>
    </li>
  )
}

function SuggestionRow({ item }: { item: SuggestedRisk }) {
  return (
    <li className="border-t border-[var(--fm-line)] py-3.5">
      <div className="flex flex-wrap items-center gap-2 text-[13.5px] font-semibold">
        <span>{item.title}</span>
        <Severity value={item.severity} />
        <Pill>{item.source.toUpperCase()}</Pill>
      </div>
      {item.description && <p className={`mt-1 line-clamp-2 text-[12.5px] ${MUTED}`}>{item.description}</p>}
    </li>
  )
}

export default function FindingsPage() {
  const { selectedSystem, loading: systemsLoading, error: systemsError, refreshSystems } = useSystemContext()
  const hasSystem = Boolean(selectedSystem.id)
  const { data: risks, suggested, summary, loading, error, assessRisks } = useRisks(selectedSystem.id)
  const { toast } = useToast()
  const [dialogOpen, setDialogOpen] = useState(false)

  const record = async (formData: RiskAssessmentFormData) => {
    try {
      await assessRisks({ ...formData, systemId: selectedSystem.id })
      toast({ title: 'Finding recorded', description: `Added to the findings for ${selectedSystem.name}.` })
      setDialogOpen(false)
    } catch (submissionError) {
      toast({
        title: 'Could not record the finding',
        description: submissionError instanceof Error ? submissionError.message : 'An error occurred',
        variant: 'destructive',
      })
    }
  }

  if (!hasSystem) {
    return (
      <div className="grid gap-4">
        <Crumb />
        <div>
          <h1 className="mt-1.5 text-[30px] font-semibold leading-[1.1] tracking-[-.03em]">Findings</h1>
          <p className={`mt-2 max-w-[640px] text-[15px] ${MUTED}`}>
            Risks recorded against an AI system, by your team or by FairMind&apos;s own checks.
          </p>
        </div>
        <section className="fm-card grid content-start justify-items-start gap-3 p-6" aria-label="No system">
          {systemsLoading ? (
            <p role="status" className={`text-[13px] ${MUTED}`}>Loading your systems</p>
          ) : systemsError ? (
            <>
              <h2 className="text-[15px] font-semibold">Could not load your systems</h2>
              <p role="alert" className={`max-w-[560px] text-[13px] ${MUTED}`}>
                Findings belong to a system, so they cannot be shown until your systems load. {systemsError}
              </p>
              <button type="button" onClick={() => void refreshSystems()} className={BTN_P}>Try again</button>
            </>
          ) : (
            <>
              <h2 className="text-[15px] font-semibold">No AI system is registered yet</h2>
              <p className={`max-w-[560px] text-[13px] ${MUTED}`}>
                Findings belong to a system, so there is nothing to list until one exists. Register a system, then record a risk against it.
              </p>
              <Link href="/onboard" className={BTN_P}>Register a system</Link>
            </>
          )}
        </section>
      </div>
    )
  }

  // An unknown count is never shown as zero: a dash while loading, "Unavailable" when the load failed.
  const count = (pick: (s: RiskSummary) => ReactNode): ReactNode =>
    loading ? (
      <>
        <span aria-hidden="true">–</span>
        <span className="sr-only">Loading</span>
      </>
    ) : summary ? (
      pick(summary)
    ) : (
      'Unavailable'
    )

  return (
    <div className="grid gap-4">
      <Crumb />

      <header className="fm-card grid gap-5 p-6 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
        <div className="min-w-0">
          <h1 className="truncate text-[30px] font-semibold leading-[1.1] tracking-[-.03em] lg:text-[34px]">{selectedSystem.name}</h1>
          <p className={`mt-2 max-w-[640px] text-[15px] ${MUTED}`}>
            Findings recorded against this system: risks your team has assessed and ones FairMind has raised itself.
          </p>
          <div className="mt-4 grid gap-x-8 gap-y-3 sm:grid-cols-2 lg:grid-cols-4">
            <Fact name="Open" value={count((s) => `${s.open} of ${s.total}`)} />
            <Fact name="Critical or high" value={count((s) => s.bySeverity.critical + s.bySeverity.high)} />
            <Fact name="Raised by FairMind" value={count((s) => s.automated)} />
            <Fact name="Recorded by a person" value={count((s) => s.total - s.automated)} />
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <button type="button" className={BTN_P}>Assess risk</button>
            </DialogTrigger>
            <DialogContent className="rounded-[14px] border-[var(--fm-line)] bg-white p-6 shadow-[var(--fm-shadow)] sm:rounded-[14px]">
              <DialogHeader>
                <DialogTitle className="text-[17px] font-semibold">Assess a risk for {selectedSystem.name}</DialogTitle>
                <DialogDescription className={`text-[13px] ${MUTED}`}>
                  This records an open finding against {selectedSystem.name}.
                </DialogDescription>
              </DialogHeader>
              <AssessForm system={selectedSystem} onSubmit={record} onCancel={() => setDialogOpen(false)} />
            </DialogContent>
          </Dialog>
          <Link href="/remediation" className={BTN}>Open remediation</Link>
        </div>
      </header>

      <section className="fm-card p-5" aria-label="Recorded findings">
        <div className="flex items-baseline justify-between gap-3">
          <h2 className="text-[15px] font-semibold">Recorded findings</h2>
          <span className={`text-[12.5px] tabular-nums ${MUTED}`}>
            {loading ? <span aria-hidden="true">–</span> : error ? null : risks.length}
          </span>
        </div>
        {!loading && error && (
          <p role="alert" className="mt-3 rounded-[10px] bg-[#fde9ea] px-3 py-2 text-[12.5px] text-[#b4232c]">
            Could not load findings, so the counts above are unavailable. {error.message}
          </p>
        )}
        {loading ? (
          <p role="status" className={`mt-3 border-t border-[var(--fm-line)] pt-4 text-[13px] ${MUTED}`}>Loading findings</p>
        ) : risks.length === 0 ? (
          !error && (
            <p className={`mt-3 border-t border-[var(--fm-line)] pt-4 text-[13px] ${MUTED}`}>
              No findings are recorded for this system. Use Assess risk to record one.
            </p>
          )
        ) : (
          <ul className="mt-3">
            {risks.map((risk) => <FindingRow key={risk.id} risk={risk} />)}
          </ul>
        )}
      </section>

      {suggested.length > 0 && (
        <details className="fm-card group p-5">
          <summary className="flex cursor-pointer list-none items-baseline justify-between gap-3 [&::-webkit-details-marker]:hidden">
            <h2 className="text-[15px] font-semibold">General entries from the MIT and IBM risk libraries</h2>
            <span className={`text-[12.5px] tabular-nums ${MUTED}`}>
              {suggested.length} <span className="group-open:hidden">· Show</span>
              <span className="hidden group-open:inline">· Hide</span>
            </span>
          </summary>
          <p className={`mt-1 max-w-[640px] text-[12.5px] ${MUTED}`}>
            General entries from the public MIT and IBM AI risk libraries. They are not matched to this system and are not counted above. If one applies, record it with Assess risk.
          </p>
          <ul className="mt-3">
            {suggested.map((item) => <SuggestionRow key={item.id} item={item} />)}
          </ul>
        </details>
      )}
    </div>
  )
}
