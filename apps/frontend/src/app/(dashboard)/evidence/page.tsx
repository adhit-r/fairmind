'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import {
  IconAlertTriangle,
  IconArrowRight,
  IconCircleCheck,
  IconFileText,
  IconFilterSearch,
  IconLoader2,
  IconRouteAltLeft,
  IconShieldCheck,
  IconShieldOff,
  IconSparkles,
  IconUpload,
  IconX,
} from '@tabler/icons-react'

import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Slider } from '@/components/ui/slider'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { useToast } from '@/hooks/use-toast'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { evidenceSchema, type EvidenceFormData } from '@/lib/validations/schemas'
import { useEvidence } from '@/lib/api/hooks/useEvidence'

function formatConfidence(confidence: number) {
  return `${Math.round(confidence * 100)}%`
}

function formatTimestamp(timestamp: string) {
  const date = new Date(timestamp)

  if (Number.isNaN(date.getTime())) {
    return 'Unknown time'
  }

  return date.toLocaleString()
}

function previewContent(content: unknown) {
  if (content === null || content === undefined || content === '') {
    return 'No content provided'
  }

  if (typeof content === 'string') {
    return content.length > 120 ? `${content.slice(0, 117)}...` : content
  }

  try {
    const serialized = JSON.stringify(content)
    return serialized.length > 120 ? `${serialized.slice(0, 117)}...` : serialized
  } catch {
    return 'Structured content attached'
  }
}

function normalizeContent(content: unknown) {
  if (typeof content !== 'string') {
    return content
  }

  const trimmed = content.trim()
  if (!trimmed) {
    return ''
  }

  try {
    return JSON.parse(trimmed)
  } catch {
    return content
  }
}

export default function EvidencePage() {
  const { selectedSystem } = useSystemContext()
  const { data, summary, loading, collecting, error, collectEvidence, refreshEvidence } = useEvidence(selectedSystem.id)
  const { toast } = useToast()
  const [confidence, setConfidence] = useState([0.8])
  const [statusFilter, setStatusFilter] = useState<string>('all')

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<EvidenceFormData>({
    resolver: zodResolver(evidenceSchema),
    defaultValues: {
      systemId: selectedSystem.id,
      type: 'test_results',
      content: '',
      confidence: 0.8,
    },
  })

  useEffect(() => {
    reset({
      systemId: selectedSystem.id,
      type: 'test_results',
      content: '',
      confidence: 0.8,
    })
    setConfidence([0.8])
  }, [reset, selectedSystem.id])

  const localSummary = useMemo(() => {
    const averageConfidence =
      data.length > 0
        ? Math.round((data.reduce((sum, item) => sum + item.confidence, 0) / data.length) * 100)
        : 0
    const latestEvidence = data[0]
    const highConfidenceCount = data.filter((item) => item.confidence >= 0.8).length

    return {
      averageConfidence,
      latestEvidence,
      highConfidenceCount,
    }
  }, [data])

  const completeness = useMemo(() => {
    const totalRequired = summary.linkedEvidence + summary.missingSignals.length
    const linked = summary.linkedEvidence
    const gaps = summary.missingSignals.length
    const readiness = summary.decisionReadiness

    let gate: 'green' | 'yellow' | 'red' = 'green'
    if (readiness !== 'review_ready') {
      gate = gaps > 2 ? 'red' : 'yellow'
    }

    return { totalRequired, linked, gaps, gate, readiness }
  }, [summary])

  const filteredData = useMemo(() => {
    if (statusFilter === 'all') return data
    if (statusFilter === 'high_confidence') return data.filter((e) => e.confidence >= 0.8)
    if (statusFilter === 'low_confidence') return data.filter((e) => e.confidence < 0.8)
    return data
  }, [data, statusFilter])

  const onSubmit = async (formData: EvidenceFormData) => {
    try {
      const collected = await collectEvidence({
        systemId: selectedSystem.id,
        type: formData.type,
        content: normalizeContent(formData.content),
        confidence: confidence[0],
      })

      toast({
        title: 'Evidence collected',
        description: `${collected.type} is now attached to ${selectedSystem.name}.`,
      })
      reset({
        systemId: selectedSystem.id,
        type: 'test_results',
        content: '',
        confidence: 0.8,
      })
      setConfidence([0.8])
    } catch (err) {
      toast({
        title: 'Collection failed',
        description: err instanceof Error ? err.message : 'Unable to store evidence for the selected AI system.',
        variant: 'destructive',
      })
    }
  }

  return (
    <div className="space-y-6">
      <Card className="border-4 border-black bg-gradient-to-br from-[#fff4de] via-white to-[#e9f7f0] p-6 shadow-[10px_10px_0px_0px_rgba(0,0,0,1)]">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="border-2 border-black bg-black px-3 py-1 font-black uppercase text-white">
                <IconSparkles className="mr-2 h-4 w-4" />
                Workflow bridge
              </Badge>
              <Badge className="border-2 border-black bg-white px-3 py-1 font-black uppercase text-black">
                <IconRouteAltLeft className="mr-2 h-4 w-4" />
                Risks to approval
              </Badge>
            </div>

            <div className="space-y-3">
              <h1 className="text-4xl font-black uppercase tracking-tight text-balance">
                Evidence closes the gap between risks and approval
              </h1>
              <p className="max-w-2xl text-base text-muted-foreground">
                Collect artifacts for the selected AI system so governance can decide whether
                risks are controlled, evidence is complete, and release sign-off is justified.
                No system ID retyping, no disconnected uploads.
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              <Badge variant="outline" className="border-2 border-black bg-white px-3 py-1 font-bold uppercase">
                {selectedSystem.name}
              </Badge>
              <Badge variant="outline" className="border-2 border-black bg-white px-3 py-1 font-bold uppercase">
                Owner: {selectedSystem.owner}
              </Badge>
              <Badge className="border-2 border-black bg-black px-3 py-1 font-black uppercase text-white">
                {selectedSystem.stage}
              </Badge>
              <Badge className="border-2 border-black bg-amber-100 px-3 py-1 font-black uppercase text-amber-900">
                Risk tier: {selectedSystem.riskTier}
              </Badge>
            </div>
          </div>

          <Card className="w-full max-w-md border-2 border-black bg-white p-4 shadow-[6px_6px_0px_0px_rgba(0,0,0,1)]">
            <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">
              Selected system
            </p>
            <h2 className="mt-2 text-2xl font-black uppercase">{selectedSystem.name}</h2>
            <p className="mt-1 text-sm text-muted-foreground">{selectedSystem.owner}</p>

            <div className="mt-4 grid grid-cols-2 gap-3">
              <div className="rounded-2xl border-2 border-black bg-slate-50 p-3">
                <p className="text-xs font-bold uppercase text-muted-foreground">Readiness</p>
                <p className="mt-1 text-2xl font-black">{selectedSystem.readiness}%</p>
              </div>
              <div className="rounded-2xl border-2 border-black bg-slate-50 p-3">
                <p className="text-xs font-bold uppercase text-muted-foreground">Stage</p>
                <p className="mt-1 text-2xl font-black uppercase">{selectedSystem.stage}</p>
              </div>
            </div>

            <div className="mt-4 rounded-2xl border-2 border-black bg-black p-3 text-white">
              <p className="text-xs font-black uppercase tracking-[0.2em] text-orange-300">
                Evidence should answer
              </p>
              <p className="mt-2 text-sm leading-6">
                What proof do we have that the selected system is safe enough to move from
                governance review to approval?
              </p>
            </div>
          </Card>
        </div>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="border-2 border-black p-5 shadow-brutal">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">
            Collected artifacts
          </p>
          <p className="mt-2 text-3xl font-black">{data.length}</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Attached to {selectedSystem.name}
          </p>
        </Card>

        <Card className="border-2 border-black p-5 shadow-brutal">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">
            Average confidence
          </p>
          <p className="mt-2 text-3xl font-black">
            {data.length > 0 ? `${localSummary.averageConfidence}%` : '—'}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            {data.length > 0
              ? `${localSummary.highConfidenceCount} artifacts are at or above 80%.`
              : 'Collect the first artifact to start the evidence trail.'}
          </p>
        </Card>

        <Card className="border-2 border-black p-5 shadow-brutal">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">
            Latest capture
          </p>
          <p className="mt-2 text-lg font-black">
            {localSummary.latestEvidence ? localSummary.latestEvidence.type : 'None yet'}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            {localSummary.latestEvidence
              ? formatTimestamp(localSummary.latestEvidence.timestamp)
              : 'Use the form below to add the first governance artifact.'}
          </p>
        </Card>
      </div>

      {/* Completeness indicator + approval-readiness gate */}
      <Card className={`border-4 p-6 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] ${
        completeness.gate === 'green'
          ? 'border-emerald-600 bg-emerald-50'
          : completeness.gate === 'yellow'
            ? 'border-amber-500 bg-amber-50'
            : 'border-red-600 bg-red-50'
      }`}>
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              {completeness.gate === 'green' ? (
                <IconShieldCheck className="h-7 w-7 text-emerald-700" />
              ) : completeness.gate === 'yellow' ? (
                <IconAlertTriangle className="h-7 w-7 text-amber-700" />
              ) : (
                <IconShieldOff className="h-7 w-7 text-red-700" />
              )}
              <div>
                <h2 className="text-xl font-black uppercase">
                  {completeness.gate === 'green'
                    ? 'Evidence complete — approval gate: ready'
                    : completeness.gate === 'yellow'
                      ? 'Evidence gaps present — approval gate: conditional'
                      : 'Critical evidence gaps — approval gate: blocked'}
                </h2>
                {summary.recommendedNextStep && (
                  <p className="mt-1 text-sm font-medium text-muted-foreground">
                    {summary.recommendedNextStep}
                  </p>
                )}
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <div className="border-2 border-black bg-white p-4 shadow-[4px_4px_0px_0px_#000]">
                <p className="text-xs font-bold uppercase text-muted-foreground">Controls requiring evidence</p>
                <p className="mt-2 text-3xl font-black">{completeness.totalRequired || '—'}</p>
              </div>
              <div className="border-2 border-black bg-white p-4 shadow-[4px_4px_0px_0px_#000]">
                <p className="text-xs font-bold uppercase text-muted-foreground">With linked evidence</p>
                <p className="mt-2 text-3xl font-black text-emerald-700">{completeness.linked}</p>
              </div>
              <div className={`border-2 border-black p-4 shadow-[4px_4px_0px_0px_#000] ${completeness.gaps > 0 ? 'bg-red-100' : 'bg-white'}`}>
                <p className="text-xs font-bold uppercase text-muted-foreground">Missing / critical gaps</p>
                <p className={`mt-2 text-3xl font-black ${completeness.gaps > 0 ? 'text-red-700' : 'text-emerald-700'}`}>
                  {completeness.gaps}
                </p>
              </div>
            </div>

            {completeness.totalRequired > 0 && (
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-bold uppercase text-muted-foreground">
                  <span>Evidence coverage</span>
                  <span>{completeness.totalRequired > 0 ? Math.round((completeness.linked / completeness.totalRequired) * 100) : 0}%</span>
                </div>
                <Progress
                  value={completeness.totalRequired > 0 ? Math.round((completeness.linked / completeness.totalRequired) * 100) : 0}
                  className="h-3 border-2 border-black"
                />
              </div>
            )}
          </div>

          {completeness.gate !== 'green' && (
            <Badge className={`self-start whitespace-nowrap border-2 border-black px-4 py-2 text-sm font-black uppercase shadow-[4px_4px_0px_0px_#000] ${
              completeness.gate === 'yellow'
                ? 'bg-amber-400 text-black'
                : 'bg-red-600 text-white'
            }`}>
              {completeness.gate === 'yellow' ? 'Gaps present' : 'Approval blocked'}
            </Badge>
          )}
        </div>
      </Card>

      {/* Evidence gaps routing */}
      {summary.missingSignals.length > 0 && (
        <Card className="border-4 border-black p-6 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <IconFilterSearch className="h-6 w-6 text-red-600" />
              <h2 className="text-xl font-black uppercase">Evidence gaps blocking approval</h2>
            </div>
            <Badge className="border-2 border-red-600 bg-red-100 px-3 py-1 font-black uppercase text-red-800">
              {summary.missingSignals.length} gap{summary.missingSignals.length !== 1 ? 's' : ''}
            </Badge>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {summary.missingSignals.map((signal) => (
              <div key={signal} className="flex flex-col gap-3 border-2 border-black bg-red-50 p-4 shadow-[4px_4px_0px_0px_#000]">
                <div className="flex items-start gap-2">
                  <IconX className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
                  <p className="text-sm font-bold uppercase leading-tight">{signal}</p>
                </div>
                <Button asChild size="sm" variant="default" className="mt-auto border-2 border-black font-black uppercase">
                  <Link
                    href={{
                      pathname: '/remediation',
                      query: {
                        gap: signal,
                        systemId: selectedSystem.id,
                        title: `Evidence gap: ${signal}`,
                        description: `Missing evidence signal "${signal}" is required for ${selectedSystem.name} approval readiness.`,
                        priority: 'high',
                      },
                    }}
                  >
                    <IconRouteAltLeft className="mr-2 h-4 w-4" />
                    Create Remediation
                  </Link>
                </Button>
              </div>
            ))}
          </div>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <Card className="border-2 border-black p-6 shadow-brutal">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-2xl font-black">Collect evidence</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                The selected AI system is already in scope. Attach the artifact that proves a
                control, resolves a risk, or explains an approval decision.
              </p>
            </div>

            <Badge className="border-2 border-black bg-emerald-100 px-3 py-2 font-black uppercase text-emerald-900">
              <IconShieldCheck className="mr-2 h-4 w-4" />
              System locked
            </Badge>
          </div>

          <div className="mt-5 rounded-2xl border-2 border-black bg-slate-50 p-4">
            <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">
              Good evidence examples
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {['Bias test result', 'Monitoring snapshot', 'Model card', 'Audit note', 'Compliance export'].map((item) => (
                <Badge key={item} variant="outline" className="border-2 border-black bg-white px-3 py-1 font-bold">
                  {item}
                </Badge>
              ))}
            </div>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-5">
            <input type="hidden" {...register('systemId')} />

            <div className="space-y-2">
              <Label htmlFor="type" className="font-bold uppercase tracking-wide">
                Evidence type
              </Label>
              <Input
                id="type"
                {...register('type')}
                className="border-2 border-black bg-white font-medium"
                placeholder="e.g. bias_test_result, monitoring_snapshot, compliance_note"
              />
              {errors.type && (
                <p className="text-sm text-red-600">{errors.type.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="content" className="font-bold uppercase tracking-wide">
                Evidence content
              </Label>
              <Textarea
                id="content"
                {...register('content')}
                className="min-h-[180px] border-2 border-black bg-white font-mono text-sm"
                placeholder='Paste JSON or a concise narrative that supports the selected system’s risk review.'
              />
              {errors.content && (
                <p className="text-sm text-red-600">{String(errors.content.message)}</p>
              )}
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between gap-4">
                <Label className="font-bold uppercase tracking-wide">
                  Confidence: {formatConfidence(confidence[0])}
                </Label>
                <span className="text-xs font-medium text-muted-foreground">
                  Higher confidence helps governance decide faster.
                </span>
              </div>
              <Slider
                value={confidence}
                onValueChange={setConfidence}
                min={0}
                max={1}
                step={0.01}
                className="border-2 border-black"
              />
            </div>

            <Button type="submit" className="w-full border-2 border-black text-base font-black uppercase tracking-wide" disabled={collecting}>
              {collecting ? (
                <>
                  <IconLoader2 className="mr-2 h-4 w-4 animate-spin" />
                  Collecting evidence
                </>
              ) : (
                <>
                  <IconUpload className="mr-2 h-4 w-4" />
                  Collect evidence for {selectedSystem.name}
                </>
              )}
            </Button>
          </form>
        </Card>

        <Card className="border-2 border-black p-6 shadow-brutal">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h2 className="text-2xl font-black">Evidence records</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                This list is scoped to the selected AI system and updates as soon as new evidence
                is collected.
              </p>
            </div>

            <div className="flex shrink-0 items-center gap-2">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-44 border-2 border-black font-bold">
                  <SelectValue placeholder="Filter" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All artifacts</SelectItem>
                  <SelectItem value="high_confidence">High confidence</SelectItem>
                  <SelectItem value="low_confidence">Low confidence</SelectItem>
                </SelectContent>
              </Select>
              <Button
                type="button"
                variant="neutral"
                className="border-2 border-black font-bold"
                onClick={() => {
                  void refreshEvidence()
                }}
                disabled={loading}
              >
                <IconArrowRight className="mr-2 h-4 w-4" />
                Refresh
              </Button>
            </div>
          </div>

          {loading && (
            <div className="flex flex-col items-center justify-center gap-3 rounded-3xl border-2 border-dashed border-black bg-slate-50 px-6 py-14 text-center">
              <IconLoader2 className="h-8 w-8 animate-spin" />
              <div>
                <p className="text-base font-bold">Loading evidence for {selectedSystem.name}</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Pulling the selected system’s artifacts so governance can review the current trail.
                </p>
              </div>
            </div>
          )}

          {!loading && error && (
            <div className="rounded-3xl border-2 border-red-600 bg-red-50 px-6 py-6">
              <div className="flex items-start gap-3">
                <IconAlertTriangle className="mt-0.5 h-5 w-5 text-red-700" />
                <div className="space-y-2">
                  <p className="font-bold text-red-800">Could not load evidence</p>
                  <p className="text-sm text-red-700">{error.message}</p>
                  <Button
                    type="button"
                    variant="neutral"
                    className="border-2 border-red-700 font-bold text-red-700"
                    onClick={() => {
                      void refreshEvidence()
                    }}
                  >
                    Retry load
                  </Button>
                </div>
              </div>
            </div>
          )}

          {!loading && !error && data.length === 0 && (
            <div className="rounded-3xl border-2 border-dashed border-black bg-slate-50 px-6 py-14 text-center">
              <IconFileText className="mx-auto h-12 w-12 opacity-60" />
              <h3 className="mt-4 text-xl font-black">No evidence attached yet</h3>
              <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
                Start with a control proof, a test result, or a monitoring export that helps
                governance decide whether this system can move from risks into approval.
              </p>

              <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
                {['Bias test', 'Monitoring export', 'Policy note', 'Audit artifact'].map((item) => (
                  <Badge key={item} variant="outline" className="border-2 border-black bg-white px-3 py-1 font-bold">
                    {item}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {!loading && !error && data.length > 0 && (
            <div className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border-2 border-black bg-slate-50 p-4">
                  <p className="text-xs font-bold uppercase text-muted-foreground">High confidence</p>
                  <p className="mt-1 text-2xl font-black">{localSummary.highConfidenceCount}</p>
                </div>
                <div className="rounded-2xl border-2 border-black bg-slate-50 p-4">
                  <p className="text-xs font-bold uppercase text-muted-foreground">Most recent</p>
                  <p className="mt-1 text-sm font-semibold">{formatTimestamp(data[0].timestamp)}</p>
                </div>
              </div>

              {filteredData.length === 0 ? (
                <div className="rounded-3xl border-2 border-dashed border-black bg-slate-50 px-6 py-10 text-center">
                  <p className="font-bold text-muted-foreground">No artifacts match this filter.</p>
                  <Button
                    type="button"
                    variant="neutral"
                    size="sm"
                    className="mt-3 border-2 border-black font-bold"
                    onClick={() => setStatusFilter('all')}
                  >
                    Clear filter
                  </Button>
                </div>
              ) : (
                <div className="overflow-hidden rounded-3xl border-2 border-black">
                  <Table>
                    <TableHeader>
                      <TableRow className="border-b-2 border-black bg-slate-100">
                        <TableHead className="font-black">Type</TableHead>
                        <TableHead className="font-black">Confidence</TableHead>
                        <TableHead className="font-black">Captured</TableHead>
                        <TableHead className="font-black">Notes</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredData.map((evidence) => (
                        <TableRow key={evidence.id} className="border-b border-black/20">
                          <TableCell className="align-top">
                            <div className="space-y-1">
                              <div className="flex items-center gap-2">
                                <Badge className="border-2 border-black bg-black px-2 py-1 font-black uppercase text-white">
                                  {evidence.type}
                                </Badge>
                                {evidence.confidence >= 0.8 && (
                                  <IconCircleCheck className="h-4 w-4 text-emerald-600" />
                                )}
                              </div>
                              <p className="max-w-[260px] text-xs text-muted-foreground">
                                {previewContent(evidence.content)}
                              </p>
                            </div>
                          </TableCell>
                          <TableCell className="align-top font-semibold">
                            {formatConfidence(evidence.confidence)}
                          </TableCell>
                          <TableCell className="align-top text-sm text-muted-foreground">
                            {formatTimestamp(evidence.timestamp)}
                          </TableCell>
                          <TableCell className="align-top">
                            <div className="space-y-2">
                              <p className="text-sm font-medium">
                                {evidence.metadata?.source
                                  ? String(evidence.metadata.source)
                                  : 'Supports the selected AI system review.'}
                              </p>
                              <div className="flex flex-wrap gap-2">
                                {Object.entries(evidence.metadata || {})
                                  .slice(0, 2)
                                  .map(([key, value]) => (
                                    <Badge key={key} variant="outline" className="border-2 border-black bg-white px-2 py-1 text-[11px] font-bold">
                                      {key}: {String(value)}
                                    </Badge>
                                  ))}
                              </div>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
