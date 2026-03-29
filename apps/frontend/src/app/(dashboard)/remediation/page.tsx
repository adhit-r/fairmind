'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import {
  IconAlertTriangle,
  IconArrowRight,
  IconCheck,
  IconClipboardCheck,
  IconFlask,
  IconLoader2,
  IconPlus,
  IconRefresh,
  IconRouteAltLeft,
  IconShieldCheck,
  IconSparkles,
  IconUser,
} from '@tabler/icons-react'

import { useSystemContext } from '@/components/workflow/SystemContext'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useToast } from '@/hooks/use-toast'
import { useRemediation, type RemediationPriority, type RemediationSourceType, type RemediationStatus } from '@/lib/api/hooks/useRemediation'

type DraftState = {
  riskId: string
  title: string
  description: string
  priority: RemediationPriority
  source: RemediationSourceType
  owner: string
  evidenceNeeded: string
  retestRequired: boolean
}

const PRIORITY_OPTIONS: RemediationPriority[] = ['critical', 'high', 'medium', 'low']

function formatTimestamp(timestamp: string) {
  const date = new Date(timestamp)
  if (Number.isNaN(date.getTime())) {
    return 'Unknown time'
  }
  return date.toLocaleString()
}

function normalizePriority(value: string | null): RemediationPriority {
  if (value === 'critical' || value === 'high' || value === 'medium' || value === 'low') {
    return value
  }

  return 'medium'
}

function normalizeSource(value: string | null): RemediationSourceType {
  if (
    value === 'governance_blocker' ||
    value === 'risk' ||
    value === 'bias_scan' ||
    value === 'evidence_gap' ||
    value === 'manual'
  ) {
    return value
  }

  return 'manual'
}

const SOURCE_LABELS: Record<RemediationSourceType, string> = {
  governance_blocker: 'Governance Blocker',
  risk: 'Risk Register',
  bias_scan: 'Bias Scan',
  evidence_gap: 'Evidence Gap',
  manual: 'Manual',
}

function priorityClassName(priority: RemediationPriority) {
  if (priority === 'critical') return 'bg-red-100 text-red-800 border-red-500'
  if (priority === 'high') return 'bg-orange-100 text-orange-800 border-orange-500'
  if (priority === 'medium') return 'bg-amber-100 text-amber-800 border-amber-500'
  return 'bg-emerald-100 text-emerald-800 border-emerald-500'
}

function statusClassName(status: RemediationStatus) {
  if (status === 'blocked') return 'bg-red-100 text-red-800 border-red-500'
  if (status === 'in_progress') return 'bg-blue-100 text-blue-800 border-blue-500'
  if (status === 'done') return 'bg-emerald-100 text-emerald-800 border-emerald-500'
  return 'bg-slate-100 text-slate-800 border-slate-500'
}

function splitEvidenceNeeded(value: string) {
  return value
    .split(/[\n,]/g)
    .map((entry) => entry.trim())
    .filter(Boolean)
}

function getPrimaryAction(status: RemediationStatus, retestRequired: boolean, retestStatus: string) {
  if (status === 'open') {
    return { label: 'Start work', next: 'in_progress' as const, blocked: false }
  }

  if (status === 'in_progress') {
    const retestBlocked = retestRequired && retestStatus !== 'passed'
    return {
      label: retestBlocked ? 'Awaiting re-test' : 'Mark done',
      next: 'done' as const,
      blocked: retestBlocked,
    }
  }

  if (status === 'blocked') {
    return { label: 'Unblock', next: 'in_progress' as const, blocked: false }
  }

  return { label: 'Reopen', next: 'in_progress' as const, blocked: false }
}

function retestStatusClassName(status: string) {
  if (status === 'passed') return 'bg-emerald-100 text-emerald-800 border-emerald-500'
  if (status === 'failed') return 'bg-red-100 text-red-800 border-red-500'
  if (status === 'pending') return 'bg-blue-100 text-blue-800 border-blue-500'
  return 'bg-slate-100 text-slate-800 border-slate-500'
}

export default function RemediationPage() {
  const { selectedSystem } = useSystemContext()
  const searchParams = useSearchParams()
  const { tasks, summary, loading, saving, error, createTask, updateTaskStatus, refreshTasks } = useRemediation(selectedSystem.id)
  const { toast } = useToast()

  const queryRiskId = searchParams.get('riskId') ?? ''
  const queryTitle = searchParams.get('title') ?? ''
  const queryDescription = searchParams.get('description') ?? ''
  const queryPriority = normalizePriority(searchParams.get('priority'))
  const querySource = normalizeSource(searchParams.get('source'))

  const [draft, setDraft] = useState<DraftState>({
    riskId: queryRiskId,
    title: queryTitle,
    description: queryDescription,
    priority: queryPriority,
    source: querySource,
    owner: '',
    evidenceNeeded: '',
    retestRequired: true,
  })

  useEffect(() => {
    setDraft({
      riskId: queryRiskId,
      title: queryTitle,
      description: queryDescription,
      priority: queryPriority,
      source: querySource,
      owner: '',
      evidenceNeeded: '',
      retestRequired: true,
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [queryDescription, queryPriority, queryRiskId, queryTitle, querySource, selectedSystem.id])

  const linkedRiskTitle = useMemo(() => {
    if (!queryRiskId) {
      return ''
    }

    return queryTitle || queryRiskId
  }, [queryRiskId, queryTitle])

  const hasRiskHandoff = Boolean(queryRiskId || queryTitle)

  const handleCreateTask = async () => {
    if (!draft.title.trim()) {
      toast({
        title: 'Task title required',
        description: 'Use the risk title or describe the remediation work before creating the task.',
        variant: 'destructive',
      })
      return
    }

    try {
      const created = await createTask({
        riskId: draft.riskId.trim() || undefined,
        title: draft.title.trim(),
        description: draft.description.trim(),
        priority: draft.priority,
        source: draft.source,
        owner: draft.owner.trim() || undefined,
        evidenceNeeded: splitEvidenceNeeded(draft.evidenceNeeded),
        retestRequired: draft.retestRequired,
      })

      toast({
        title: 'Remediation task created',
        description: `${created.title} is now tracked for ${selectedSystem.name}.`,
      })

      setDraft({
        riskId: '',
        title: '',
        description: '',
        priority: 'medium',
        source: 'manual',
        owner: '',
        evidenceNeeded: '',
        retestRequired: true,
      })
    } catch (creationError) {
      toast({
        title: 'Task creation failed',
        description: creationError instanceof Error ? creationError.message : 'Unable to create remediation work.',
        variant: 'destructive',
      })
    }
  }

  return (
    <div className="space-y-6">
      <Card className="overflow-hidden border-4 border-black bg-[linear-gradient(135deg,#fff4de_0%,#fff_55%,#e9f7f0_100%)] shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
        <div className="grid gap-0 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="border-b-4 border-black p-6 xl:border-b-0 xl:border-r-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="border-2 border-black bg-black px-3 py-1 font-black uppercase text-white">
                <IconSparkles className="mr-2 h-4 w-4" />
                Workflow bridge
              </Badge>
              <Badge className="border-2 border-black bg-white px-3 py-1 font-black uppercase text-black">
                <IconRouteAltLeft className="mr-2 h-4 w-4" />
                Risks to remediation
              </Badge>
            </div>

            <h1 className="mt-4 text-4xl font-black uppercase tracking-tight text-balance">
              Remediation turns risks into owned work
            </h1>
            <p className="mt-3 max-w-2xl text-sm text-slate-700">
              This page is scoped to the selected AI system. It pulls remediation tasks from the
              current risk register, lets you create follow-up work directly from a risk handoff,
              and keeps the team moving toward approval.
            </p>

            <div className="mt-5 flex flex-wrap gap-2">
              <Badge variant="outline" className="border-2 border-black bg-white px-3 py-1 font-bold uppercase">
                {selectedSystem.name}
              </Badge>
              <Badge variant="outline" className="border-2 border-black bg-white px-3 py-1 font-bold uppercase">
                Owner: {selectedSystem.owner}
              </Badge>
              <Badge className="border-2 border-black bg-black px-3 py-1 font-black uppercase text-white">
                Stage: {selectedSystem.stage}
              </Badge>
            </div>

            {hasRiskHandoff && (
              <div className="mt-5 rounded-2xl border-2 border-black bg-white p-4 shadow-[4px_4px_0px_0px_#000]">
                <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">
                  Prefilled from risk handoff
                </p>
                <p className="mt-2 text-lg font-black uppercase">
                  {linkedRiskTitle}
                </p>
                <p className="mt-1 text-sm text-slate-700">
                  Use this as the starting point for a remediation task, then attach evidence and
                  move the status forward.
                </p>
              </div>
            )}
          </div>

          <div className="bg-black p-6 text-white">
            <p className="text-xs font-black uppercase tracking-[0.22em] text-orange">Decision flow</p>
            <div className="mt-4 space-y-3">
              <div className="border-2 border-white p-4">
                <p className="font-black uppercase">1. Review current risks</p>
                <p className="mt-1 text-sm text-slate-200">
                  Risk items feed this page so remediation work stays tied to the real blockers.
                </p>
              </div>
              <div className="border-2 border-white p-4">
                <p className="font-black uppercase">2. Create or update tasks</p>
                <p className="mt-1 text-sm text-slate-200">
                  Create a task from a risk handoff or add a new corrective action manually.
                </p>
              </div>
              <div className="border-2 border-white p-4">
                <p className="font-black uppercase">3. Close the loop</p>
                <p className="mt-1 text-sm text-slate-200">
                  Mark work in progress or done, then recheck evidence before approval.
                </p>
              </div>
            </div>
          </div>
        </div>
      </Card>

      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-2 border-black p-5 shadow-brutal">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">Active</p>
          <p className="mt-2 text-3xl font-black">{summary.active}</p>
          <p className="mt-1 text-sm text-muted-foreground">Open, in progress, and blocked work.</p>
        </Card>
        <Card className="border-2 border-black p-5 shadow-brutal">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">Linked Risks</p>
          <p className="mt-2 text-3xl font-black">{summary.linkedRiskReferences}</p>
          <p className="mt-1 text-sm text-muted-foreground">Tasks prefilled from the risk register.</p>
        </Card>
        <Card className="border-2 border-black p-5 shadow-brutal">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">Manual Tasks</p>
          <p className="mt-2 text-3xl font-black">{Math.max(summary.total - summary.linkedRiskReferences, 0)}</p>
          <p className="mt-1 text-sm text-muted-foreground">Corrective actions added directly here.</p>
        </Card>
        <Card className="border-2 border-black p-5 shadow-brutal">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">Done</p>
          <p className="mt-2 text-3xl font-black">{summary.completed}</p>
          <p className="mt-1 text-sm text-muted-foreground">Closed tasks ready to support approval.</p>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <Card className="border-2 border-black p-6 shadow-brutal">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-2xl font-black">Create remediation task</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Keep the task tied to the selected AI system. Use the risk handoff fields if you
                arrived here from the risk register.
              </p>
            </div>

            <Badge className="border-2 border-black bg-emerald-100 px-3 py-2 font-black uppercase text-emerald-900">
              <IconShieldCheck className="mr-2 h-4 w-4" />
              System scoped
            </Badge>
          </div>

          <div className="mt-5 space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label className="font-bold uppercase tracking-wide">Source</Label>
                <div className="flex flex-wrap gap-2">
                  {(['governance_blocker', 'risk', 'evidence_gap', 'bias_scan', 'manual'] as RemediationSourceType[]).map((option) => (
                    <Button
                      key={option}
                      type="button"
                      variant={draft.source === option ? 'default' : 'neutral'}
                      className="border-2 border-black text-xs font-bold uppercase"
                      onClick={() => setDraft((current) => ({ ...current, source: option }))}
                    >
                      {SOURCE_LABELS[option]}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <Label className="font-bold uppercase tracking-wide">Re-test Required</Label>
                <div className="flex items-center gap-3 rounded-2xl border-2 border-black bg-slate-50 p-3">
                  <button
                    type="button"
                    onClick={() => setDraft((current) => ({ ...current, retestRequired: !current.retestRequired }))}
                    className={`flex h-7 w-14 items-center rounded-full border-2 border-black transition-colors ${draft.retestRequired ? 'bg-black' : 'bg-white'}`}
                  >
                    <span className={`inline-block h-5 w-5 rounded-full border-2 border-black bg-white transition-transform ${draft.retestRequired ? 'translate-x-7' : 'translate-x-0.5'}`} />
                  </button>
                  <div>
                    <p className="text-sm font-bold">{draft.retestRequired ? 'Yes — re-test before closing' : 'No re-test needed'}</p>
                    <p className="text-xs text-muted-foreground">Requires a passing re-test result before the task can be marked done.</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <Label className="font-bold uppercase tracking-wide">Risk ID</Label>
              <Input
                value={draft.riskId}
                onChange={(event) => setDraft((current) => ({ ...current, riskId: event.target.value }))}
                className="border-2 border-black bg-white font-medium"
                placeholder="Optional: link this task to a specific risk"
              />
            </div>

            <div className="space-y-2">
              <Label className="font-bold uppercase tracking-wide">Task title</Label>
              <Input
                value={draft.title}
                onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))}
                className="border-2 border-black bg-white font-medium"
                placeholder="e.g. Re-run fairness evaluation and attach results"
              />
            </div>

            <div className="space-y-2">
              <Label className="font-bold uppercase tracking-wide">Task details</Label>
              <Textarea
                value={draft.description}
                onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))}
                className="min-h-[140px] border-2 border-black bg-white"
                placeholder="Describe the remediation action, success criteria, and what evidence will close the loop."
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label className="font-bold uppercase tracking-wide">Priority</Label>
                <div className="grid grid-cols-2 gap-2">
                  {PRIORITY_OPTIONS.map((option) => (
                    <Button
                      key={option}
                      type="button"
                      variant={draft.priority === option ? 'default' : 'neutral'}
                      className="justify-start border-2 border-black uppercase"
                      onClick={() => setDraft((current) => ({ ...current, priority: option }))}
                    >
                      {option}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <Label className="font-bold uppercase tracking-wide">Owner</Label>
                <Input
                  value={draft.owner}
                  onChange={(event) => setDraft((current) => ({ ...current, owner: event.target.value }))}
                  className="border-2 border-black bg-white font-medium"
                  placeholder="Optional owner or team"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label className="font-bold uppercase tracking-wide">Evidence needed</Label>
              <Textarea
                value={draft.evidenceNeeded}
                onChange={(event) =>
                  setDraft((current) => ({ ...current, evidenceNeeded: event.target.value }))
                }
                className="min-h-[110px] border-2 border-black bg-white"
                placeholder="Enter one item per line or comma-separated: rerun report, dataset slice, sign-off note"
              />
              <p className="text-xs text-muted-foreground">
                This becomes a checklist for the follow-up work and helps the approval step know
                what still needs to be attached.
              </p>
            </div>

            <Button
              type="button"
              className="w-full border-2 border-black font-black uppercase tracking-wide"
              onClick={() => {
                void handleCreateTask()
              }}
              disabled={saving}
            >
              <IconPlus className="mr-2 h-4 w-4" />
              {saving ? 'Saving task...' : `Create task for ${selectedSystem.name}`}
            </Button>
          </div>
        </Card>

        <Card className="border-2 border-black p-6 shadow-brutal">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h2 className="text-2xl font-black">Remediation queue</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Tasks are pulled from the selected system’s risk register and updated here as the
                team works through the blockers.
              </p>
            </div>

            <div className="flex gap-2">
              <Button
                type="button"
                variant="neutral"
                className="border-2 border-black font-bold"
                onClick={() => {
                  void refreshTasks()
                }}
                disabled={loading}
              >
                <IconRefresh className="mr-2 h-4 w-4" />
                Refresh
              </Button>
              <Button asChild variant="neutral" className="border-2 border-black font-bold">
                <Link href="/risks">
                  Review risks
                  <IconArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>

          {loading && (
            <div className="mt-6 space-y-4">
              <div className="flex items-center gap-3 rounded-3xl border-2 border-dashed border-black bg-slate-50 px-5 py-10">
                <IconLoader2 className="h-6 w-6 animate-spin" />
                <div>
                  <p className="font-bold">Loading remediation tasks for {selectedSystem.name}</p>
                  <p className="text-sm text-muted-foreground">
                    Pulling the current risk-linked work so the queue stays scoped.
                  </p>
                </div>
              </div>
            </div>
          )}

          {!loading && error && (
            <div className="mt-6 rounded-3xl border-2 border-red-600 bg-red-50 px-5 py-5">
              <div className="flex items-start gap-3">
                <IconAlertTriangle className="mt-0.5 h-5 w-5 text-red-700" />
                <div className="space-y-2">
                  <p className="font-bold text-red-800">Could not load remediation tasks</p>
                  <p className="text-sm text-red-700">{error.message}</p>
                  <Button
                    type="button"
                    variant="neutral"
                    className="border-2 border-red-700 font-bold text-red-700"
                    onClick={() => {
                      void refreshTasks()
                    }}
                  >
                    Retry load
                  </Button>
                </div>
              </div>
            </div>
          )}

          {!loading && !error && tasks.length === 0 && (
            <div className="mt-6 rounded-3xl border-2 border-dashed border-black bg-slate-50 px-6 py-14 text-center">
              <IconClipboardCheck className="mx-auto h-12 w-12 opacity-60" />
              <h3 className="mt-4 text-xl font-black">No remediation tasks yet</h3>
              <p className="mx-auto mt-2 max-w-lg text-sm text-muted-foreground">
                Start from a risk in the register or create a new task here when the blocker is not
                already captured.
              </p>
              <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
                <Badge variant="outline" className="border-2 border-black bg-white px-3 py-1 font-bold">
                  Risk-linked
                </Badge>
                <Badge variant="outline" className="border-2 border-black bg-white px-3 py-1 font-bold">
                  Evidence-backed
                </Badge>
                <Badge variant="outline" className="border-2 border-black bg-white px-3 py-1 font-bold">
                  Approval-ready
                </Badge>
              </div>
            </div>
          )}

          {!loading && !error && tasks.length > 0 && (
            <div className="mt-6 space-y-4">
              {tasks.map((task) => {
                const primaryAction = getPrimaryAction(task.status, task.retestRequired, task.retestStatus)

                return (
                  <Card key={task.id} className="border-2 border-black bg-white p-5 shadow-[4px_4px_0px_0px_#000]">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                      <div className="space-y-3">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge className={`border-2 font-black uppercase ${priorityClassName(task.priority)}`}>
                            {task.priority}
                          </Badge>
                          <Badge className={`border-2 font-black uppercase ${statusClassName(task.status)}`}>
                            {task.status.replace(/_/g, ' ')}
                          </Badge>
                          <Badge variant="outline" className="border-2 border-black bg-white px-3 py-1 font-bold uppercase">
                            {task.sourceType === 'governance_blocker'
                              ? 'Governance Blocker'
                              : task.sourceType === 'evidence_gap'
                                ? 'Evidence Gap'
                                : task.sourceType === 'bias_scan'
                                  ? 'Bias Scan'
                                  : task.source === 'risk'
                                    ? 'Risk-linked'
                                    : 'Manual'}
                          </Badge>
                          {task.retestRequired && (
                            <Badge className={`border-2 font-black uppercase ${retestStatusClassName(task.retestStatus)}`}>
                              <IconFlask className="mr-1 h-3 w-3" />
                              Re-test: {task.retestStatus.replace(/_/g, ' ')}
                            </Badge>
                          )}
                        </div>

                        <div>
                          <h3 className="text-xl font-black uppercase">{task.title}</h3>
                          <p className="mt-2 text-sm text-slate-700">{task.description}</p>
                        </div>

                        <div className="grid gap-3 md:grid-cols-2">
                          <div className="rounded-2xl border-2 border-black bg-slate-50 p-3">
                            <p className="text-xs font-bold uppercase text-muted-foreground">Next action</p>
                            <p className="mt-1 text-sm font-medium">{task.nextAction}</p>
                          </div>
                          <div className="rounded-2xl border-2 border-black bg-slate-50 p-3">
                            <p className="text-xs font-bold uppercase text-muted-foreground">Owner</p>
                            <p className="mt-1 flex items-center gap-2 text-sm font-medium">
                              <IconUser className="h-4 w-4" />
                              {task.owner || 'Unassigned'}
                            </p>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <p className="text-xs font-bold uppercase text-muted-foreground">
                            Evidence needed
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {task.evidenceNeeded.length > 0 ? (
                              task.evidenceNeeded.map((item) => (
                                <Badge key={item} variant="outline" className="border-2 border-black bg-white px-3 py-1 font-bold">
                                  {item}
                                </Badge>
                              ))
                            ) : (
                              <span className="text-sm text-muted-foreground">
                                Attach the proof that closes this task.
                              </span>
                            )}
                          </div>
                        </div>

                        <p className="text-xs text-muted-foreground">
                          Updated {formatTimestamp(task.updatedAt)} {task.riskId ? `• Risk ID ${task.riskId}` : ''}
                        </p>
                      </div>

                      <div className="flex flex-col gap-2 lg:min-w-[220px]">
                        <Button
                          type="button"
                          className="border-2 border-black font-bold"
                          disabled={saving || primaryAction.blocked}
                          onClick={async () => {
                            try {
                              await updateTaskStatus(task.id, primaryAction.next)
                              toast({
                                title: 'Task updated',
                                description: `${task.title} is now ${primaryAction.next.replace(/_/g, ' ')}.`,
                              })
                            } catch (updateError) {
                              toast({
                                title: 'Task update failed',
                                description: updateError instanceof Error ? updateError.message : 'Unable to update remediation task.',
                                variant: 'destructive',
                              })
                            }
                          }}
                        >
                          {primaryAction.blocked ? (
                            <IconFlask className="mr-2 h-4 w-4" />
                          ) : (
                            <IconCheck className="mr-2 h-4 w-4" />
                          )}
                          {primaryAction.label}
                        </Button>
                        {primaryAction.blocked && (
                          <p className="text-xs font-bold text-amber-700">
                            Re-test must pass before this task can be closed.
                          </p>
                        )}

                        {task.status !== 'done' && (
                          <Button
                            asChild
                            variant="neutral"
                            className="border-2 border-black font-bold"
                          >
                            <Link href="/evidence">
                              Review evidence
                              <IconArrowRight className="ml-2 h-4 w-4" />
                            </Link>
                          </Button>
                        )}

                        {task.riskId && (
                          <Button
                            asChild
                            variant="neutral"
                            className="border-2 border-black font-bold"
                          >
                            <Link href="/risks">
                              Open source risk
                              <IconArrowRight className="ml-2 h-4 w-4" />
                            </Link>
                          </Button>
                        )}
                      </div>
                    </div>
                  </Card>
                )
              })}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
