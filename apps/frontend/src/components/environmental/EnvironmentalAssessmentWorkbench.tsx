'use client'

import { useMemo, useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  IconLeaf,
  IconAlertTriangle,
  IconCheck,
  IconX,
  IconDownload,
  IconShieldCheck,
  IconPlus,
} from '@tabler/icons-react'
import {
  useEnvironmentalAssessment,
  type AssessmentInput,
  type LifecyclePhase,
  type ProvenanceClass,
  type Recommendation,
} from '@/lib/api/hooks/useEnvironmentalAssessment'

/**
 * The reviewer-facing environmental governance workbench.
 *
 * Runs an assessment, shows where it lands on the impact x confidence decision
 * matrix, lists ENV control coverage and gate blockers, and lets a reviewer
 * attach a mitigation or sign off. Everything is wired to real endpoints; no
 * value shown here is computed client-side except formatting.
 */

const PHASES: Array<{ value: LifecyclePhase; label: string; metric: string }> = [
  { value: 'training', label: 'Training', metric: 'total_kg_co2e_location' },
  { value: 'fine_tune', label: 'Fine-tuning', metric: 'total_kg_co2e_location' },
  { value: 'inference', label: 'Inference', metric: 'kg_co2e_per_1000_requests' },
  { value: 'llm_inference', label: 'LLM inference', metric: 'kg_co2e_per_1m_tokens' },
]

const PROVENANCE: Array<{ value: ProvenanceClass; label: string; hint: string }> = [
  { value: 'measured', label: 'Measured (hardware telemetry)', hint: 'confidence 0.85 - 1.00' },
  { value: 'tool_estimated', label: 'Tool estimated (CodeCarbon, EcoLogits)', hint: 'confidence 0.60 - 0.85' },
  { value: 'vendor_reported', label: 'Vendor reported (cloud billing)', hint: 'capped at 0.60' },
  { value: 'manual', label: 'Manual FLOP estimate', hint: 'confidence 0.20 - 0.40' },
  { value: 'unknown', label: 'Undisclosed', hint: 'forces confidence 0.0 and no_go' },
]

const RECOMMENDATION_STYLE: Record<Recommendation, string> = {
  go: 'bg-green-500 text-black',
  conditional_go: 'bg-yellow-400 text-black',
  no_go: 'bg-red-500 text-white',
}

const RECOMMENDATION_LABEL: Record<Recommendation, string> = {
  go: 'GO',
  conditional_go: 'CONDITIONAL GO',
  no_go: 'NO GO',
}

const TIERS = ['low', 'medium', 'high'] as const
const BANDS = ['measured', 'estimated', 'unknown'] as const

// Mirrors the engine's decision matrix. Display only: every decision shown to
// the user comes from the backend, this grid just highlights where it landed.
const MATRIX: Record<string, Record<string, Recommendation>> = {
  low: { measured: 'go', estimated: 'go', unknown: 'conditional_go' },
  medium: { measured: 'conditional_go', estimated: 'conditional_go', unknown: 'no_go' },
  high: { measured: 'conditional_go', estimated: 'no_go', unknown: 'no_go' },
}

function num(value: string): number | null {
  if (value.trim() === '') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

export function EnvironmentalAssessmentWorkbench({
  systemId,
  title = 'Environmental Impact',
}: {
  systemId: string
  title?: string
}) {
  const {
    latest,
    history,
    controls,
    loading,
    error,
    submitting,
    runAssessment,
    addMitigation,
    approveAssessment,
    exportDisclosure,
  } = useEnvironmentalAssessment(systemId)

  const [showForm, setShowForm] = useState(false)
  const [phase, setPhase] = useState<LifecyclePhase>('inference')
  const [provenance, setProvenance] = useState<ProvenanceClass>('tool_estimated')
  const [functionalUnit, setFunctionalUnit] = useState('1000_requests')
  const [boundary, setBoundary] = useState('')
  const [uncertainty, setUncertainty] = useState('')
  const [kwh, setKwh] = useState('')
  const [co2Location, setCo2Location] = useState('')
  const [co2Market, setCo2Market] = useState('')
  const [per1kRequests, setPer1kRequests] = useState('')
  const [per1mTokens, setPer1mTokens] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  const [mitigationText, setMitigationText] = useState('')
  const [mitigationDate, setMitigationDate] = useState('')
  const [reviewer, setReviewer] = useState('')
  const [actionError, setActionError] = useState<string | null>(null)
  const [actionNote, setActionNote] = useState<string | null>(null)

  const result = latest?.result
  const recommendation = (latest?.recommendation ?? result?.recommendation) as Recommendation | undefined
  const confidence = latest?.confidenceScore ?? result?.confidence_score ?? result?.evidence_confidence
  const band = latest?.confidenceBand ?? result?.confidence_band
  const tier = latest?.impactTier ?? result?.impact_tier ?? latest?.riskTier
  const coverage = latest?.coverage ?? result?.coverage ?? {}
  const coverageRate = latest?.coverageRate ?? result?.coverage_rate
  const assessmentId = latest?.assessmentId ?? latest?.id
  const blockers = latest?.blockers ?? []

  const coverageRows = useMemo(() => {
    if (controls.length > 0) {
      return controls.map((c) => ({
        code: c.code,
        name: c.name,
        status: coverage[c.code] ?? 'missing',
      }))
    }
    return Object.entries(coverage).map(([code, status]) => ({ code, name: code, status }))
  }, [controls, coverage])

  const handleRun = async () => {
    setFormError(null)
    const metrics = {
      total_kwh: num(kwh),
      total_kg_co2e_location: num(co2Location),
      total_kg_co2e_market: num(co2Market),
      kg_co2e_per_1000_requests: num(per1kRequests),
      kg_co2e_per_1m_tokens: num(per1mTokens),
    }
    const required = PHASES.find((p) => p.value === phase)?.metric
    if (required && metrics[required as keyof typeof metrics] == null) {
      const label = PHASES.find((p) => p.value === phase)?.label
      setFormError(
        `The ${label} phase is tiered on ${required.replace(/_/g, ' ')}. Enter that figure to run the assessment.`
      )
      return
    }
    const input: AssessmentInput = {
      lifecycle_phase: phase,
      functional_unit: functionalUnit || '1000_requests',
      boundary: boundary || undefined,
      provenance_class: provenance,
      measurement_source: provenance,
      uncertainty_pct: num(uncertainty),
      metrics,
    }
    try {
      await runAssessment(input)
      setShowForm(false)
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Assessment failed')
    }
  }

  const handleMitigation = async () => {
    if (!assessmentId || !mitigationText.trim()) return
    setActionError(null)
    try {
      await addMitigation(assessmentId, {
        description: mitigationText.trim(),
        target_date: mitigationDate || undefined,
      })
      setMitigationText('')
      setMitigationDate('')
      setActionNote('Mitigation recorded. The assessment was re-evaluated.')
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Failed to add mitigation')
    }
  }

  const handleApprove = async () => {
    if (!assessmentId || !reviewer.trim()) return
    setActionError(null)
    try {
      await approveAssessment(assessmentId, reviewer.trim(), 'Reviewed in model evaluation')
      setActionNote('Sign-off recorded.')
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Sign-off failed')
    }
  }

  const handleExport = async () => {
    setActionError(null)
    try {
      const data = await exportDisclosure()
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `esrs-e1-disclosure-${systemId}.json`
      link.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Export failed')
    }
  }

  if (loading) {
    return (
      <Card className="p-6 border-2 border-black shadow-brutal">
        <p className="text-sm font-bold uppercase tracking-wider">Loading environmental assessment...</p>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <IconLeaf className="h-5 w-5" />
          <h2 className="text-xl font-black uppercase tracking-tight">{title}</h2>
        </div>
        <div className="flex gap-2">
          {latest && (
            <Button
              variant="neutral"
              className="border-2 border-black shadow-brutal font-bold"
              onClick={handleExport}
            >
              <IconDownload className="mr-2 h-4 w-4" />
              Export ESRS E1
            </Button>
          )}
          <Button
            className="border-2 border-black shadow-brutal font-bold"
            onClick={() => setShowForm((open) => !open)}
          >
            <IconPlus className="mr-2 h-4 w-4" />
            {latest ? 'New assessment' : 'Run assessment'}
          </Button>
        </div>
      </div>

      {error && (
        <Alert className="border-2 border-black shadow-brutal">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      )}

      {showForm && (
        <Card className="p-6 border-2 border-black shadow-brutal space-y-4">
          <h3 className="font-black uppercase tracking-wide text-sm">Run an assessment</h3>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label className="font-bold" htmlFor="env-phase">Lifecycle phase</Label>
              <Select value={phase} onValueChange={(v) => setPhase(v as LifecyclePhase)}>
                <SelectTrigger className="border-2 border-black" id="env-phase">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PHASES.map((p) => (
                    <SelectItem key={p.value} value={p.value}>
                      {p.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label className="font-bold" htmlFor="env-provenance">Measurement provenance</Label>
              <Select value={provenance} onValueChange={(v) => setProvenance(v as ProvenanceClass)}>
                <SelectTrigger className="border-2 border-black" id="env-provenance">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PROVENANCE.map((p) => (
                    <SelectItem key={p.value} value={p.value}>
                      {p.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                {PROVENANCE.find((p) => p.value === provenance)?.hint}
              </p>
            </div>

            <div className="space-y-2">
              <Label className="font-bold" htmlFor="env-functional-unit">Functional unit</Label>
              <Input
                id="env-functional-unit"
                className="border-2 border-black"
                value={functionalUnit}
                onChange={(e) => setFunctionalUnit(e.target.value)}
                placeholder="1000_requests"
              />
            </div>

            <div className="space-y-2">
              <Label className="font-bold" htmlFor="env-uncertainty">Uncertainty (percent)</Label>
              <Input
                id="env-uncertainty"
                className="border-2 border-black"
                value={uncertainty}
                onChange={(e) => setUncertainty(e.target.value)}
                inputMode="decimal"
                placeholder="Required for ENV-5 coverage"
              />
            </div>

            <div className="space-y-2 md:col-span-2">
              <Label className="font-bold" htmlFor="env-boundary">Assessment boundary</Label>
              <Input
                id="env-boundary"
                className="border-2 border-black"
                value={boundary}
                onChange={(e) => setBoundary(e.target.value)}
                placeholder="What the measurement covers, e.g. scope 2, in-region serving only"
              />
            </div>

            <div className="space-y-2">
              <Label className="font-bold" htmlFor="env-kwh">Total energy (kWh)</Label>
              <Input
                id="env-kwh"
                className="border-2 border-black"
                value={kwh}
                onChange={(e) => setKwh(e.target.value)}
                inputMode="decimal"
              />
            </div>
            <div className="space-y-2">
              <Label className="font-bold" htmlFor="env-co2-location">Carbon, location-based (kg CO2e)</Label>
              <Input
                id="env-co2-location"
                className="border-2 border-black"
                value={co2Location}
                onChange={(e) => setCo2Location(e.target.value)}
                inputMode="decimal"
              />
            </div>
            <div className="space-y-2">
              <Label className="font-bold" htmlFor="env-co2-market">Carbon, market-based (kg CO2e)</Label>
              <Input
                id="env-co2-market"
                className="border-2 border-black"
                value={co2Market}
                onChange={(e) => setCo2Market(e.target.value)}
                inputMode="decimal"
              />
            </div>
            <div className="space-y-2">
              <Label className="font-bold" htmlFor="env-per-1k">Per 1000 requests (kg CO2e)</Label>
              <Input
                id="env-per-1k"
                className="border-2 border-black"
                value={per1kRequests}
                onChange={(e) => setPer1kRequests(e.target.value)}
                inputMode="decimal"
              />
            </div>
            <div className="space-y-2">
              <Label className="font-bold" htmlFor="env-per-1m">Per 1M tokens (kg CO2e)</Label>
              <Input
                id="env-per-1m"
                className="border-2 border-black"
                value={per1mTokens}
                onChange={(e) => setPer1mTokens(e.target.value)}
                inputMode="decimal"
              />
            </div>
          </div>

          {formError && (
            <Alert className="border-2 border-black">
              <IconAlertTriangle className="h-4 w-4" />
              <AlertDescription>{formError}</AlertDescription>
            </Alert>
          )}

          <div className="flex gap-2">
            <Button
              className="border-2 border-black shadow-brutal font-bold"
              onClick={handleRun}
              disabled={submitting}
            >
              {submitting ? 'Evaluating...' : 'Evaluate against the gate'}
            </Button>
            <Button
              variant="neutral"
              className="border-2 border-black font-bold"
              onClick={() => setShowForm(false)}
            >
              Cancel
            </Button>
          </div>
        </Card>
      )}

      {!latest && !showForm && (
        <Card className="p-6 border-2 border-black shadow-brutal">
          <p className="font-bold">No environmental assessment on record.</p>
          <p className="text-sm text-muted-foreground mt-1">
            This system is blocked at the deployment-approval gate until environmental evidence is
            filed. Run an assessment to record it.
          </p>
        </Card>
      )}

      {latest && (
        <>
          <Card className="p-6 border-2 border-black shadow-brutal">
            <div className="flex flex-wrap items-center gap-4 justify-between">
              <div className="flex items-center gap-3">
                {recommendation && (
                  <Badge
                    className={`border-2 border-black text-base px-4 py-1 font-black ${RECOMMENDATION_STYLE[recommendation]}`}
                  >
                    {RECOMMENDATION_LABEL[recommendation]}
                  </Badge>
                )}
                <div className="text-sm">
                  <span className="font-bold uppercase">{tier ?? 'unknown'}</span> impact ·{' '}
                  <span className="font-bold uppercase">{band ?? 'unknown'}</span> confidence
                  {latest.version != null && <span className="ml-2 text-muted-foreground">v{latest.version}</span>}
                </div>
              </div>
              {latest.reviewerState && (
                <Badge variant="outline" className="border-2 border-black font-bold uppercase">
                  {latest.reviewerState}
                </Badge>
              )}
            </div>

            <div className="mt-4 space-y-2">
              <div className="flex justify-between text-xs font-bold uppercase">
                <span>Evidence confidence</span>
                <span>{confidence != null ? confidence.toFixed(2) : 'not scored'}</span>
              </div>
              <div className="h-4 w-full border-2 border-black bg-white">
                <div
                  className={`h-full ${
                    (confidence ?? 0) >= 0.7
                      ? 'bg-green-500'
                      : (confidence ?? 0) >= 0.35
                        ? 'bg-yellow-400'
                        : 'bg-red-500'
                  }`}
                  style={{ width: `${Math.max(0, Math.min(1, confidence ?? 0)) * 100}%` }}
                />
              </div>
              {coverageRate != null && (
                <p className="text-xs text-muted-foreground">
                  ENV control coverage: {(coverageRate * 100).toFixed(0)} percent
                </p>
              )}
            </div>

            {blockers.length > 0 && (
              <div className="mt-4 space-y-2">
                {blockers.map((blocker, index) => (
                  <Alert key={index} className="border-2 border-black">
                    <IconAlertTriangle className="h-4 w-4" />
                    <AlertDescription className="font-medium">
                      {blocker.message ?? blocker.code}
                    </AlertDescription>
                  </Alert>
                ))}
              </div>
            )}
          </Card>

          <Card className="border-2 border-black shadow-brutal overflow-hidden">
            <div className="p-4 border-b-2 border-black">
              <h3 className="font-black uppercase tracking-wide text-sm">Decision matrix position</h3>
            </div>
            <div className="p-4 overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr>
                    <th className="text-left p-2 font-black uppercase text-xs">Impact</th>
                    {BANDS.map((b) => (
                      <th key={b} className="p-2 font-black uppercase text-xs">
                        {b}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {TIERS.map((t) => (
                    <tr key={t}>
                      <td className="p-2 font-bold uppercase text-xs">{t}</td>
                      {BANDS.map((b) => {
                        const cell = MATRIX[t][b]
                        const active = t === tier && b === band
                        return (
                          <td
                            key={b}
                            className={`p-2 text-center border-2 ${
                              active ? 'border-black font-black' : 'border-gray-200'
                            } ${active ? RECOMMENDATION_STYLE[cell] : 'text-muted-foreground'}`}
                          >
                            {RECOMMENDATION_LABEL[cell]}
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="text-xs text-muted-foreground mt-3">
                Undisclosed provenance forces confidence 0.0 and a no_go for every impact tier.
              </p>
            </div>
          </Card>

          <Card className="border-2 border-black shadow-brutal overflow-hidden">
            <div className="p-4 border-b-2 border-black">
              <h3 className="font-black uppercase tracking-wide text-sm">ENV control coverage</h3>
            </div>
            <div className="divide-y-2 divide-gray-100">
              {coverageRows.map((row) => (
                <div key={row.code} className="flex items-center justify-between gap-4 p-3">
                  <div className="min-w-0">
                    <span className="font-bold text-sm">{row.code}</span>
                    <span className="text-sm text-muted-foreground ml-2">{row.name}</span>
                  </div>
                  <Badge
                    className={`border-2 border-black font-bold uppercase text-xs ${
                      row.status === 'present'
                        ? 'bg-green-500 text-black'
                        : row.status === 'not_applicable'
                          ? 'bg-gray-200 text-black'
                          : 'bg-red-500 text-white'
                    }`}
                  >
                    {row.status === 'present' ? (
                      <IconCheck className="h-3 w-3 mr-1" />
                    ) : row.status === 'missing' ? (
                      <IconX className="h-3 w-3 mr-1" />
                    ) : null}
                    {row.status.replace(/_/g, ' ')}
                  </Badge>
                </div>
              ))}
            </div>
          </Card>

          <div className="grid gap-6 md:grid-cols-2">
            <Card className="p-6 border-2 border-black shadow-brutal space-y-3">
              <h3 className="font-black uppercase tracking-wide text-sm">Add mitigation</h3>
              <p className="text-xs text-muted-foreground">
                A conditional go cannot be approved without a dated mitigation.
              </p>
              <Input
                className="border-2 border-black"
                value={mitigationText}
                onChange={(e) => setMitigationText(e.target.value)}
                placeholder="What will be done to reduce impact"
              />
              <Input
                className="border-2 border-black"
                type="date"
                value={mitigationDate}
                onChange={(e) => setMitigationDate(e.target.value)}
              />
              <Button
                className="border-2 border-black shadow-brutal font-bold w-full"
                onClick={handleMitigation}
                disabled={submitting || !mitigationText.trim()}
              >
                Record mitigation
              </Button>
            </Card>

            <Card className="p-6 border-2 border-black shadow-brutal space-y-3">
              <h3 className="font-black uppercase tracking-wide text-sm">Reviewer sign-off</h3>
              <p className="text-xs text-muted-foreground">
                Blocked while the environmental gate does not pass.
              </p>
              <Input
                className="border-2 border-black"
                value={reviewer}
                onChange={(e) => setReviewer(e.target.value)}
                placeholder="Reviewer name or identifier"
              />
              <Button
                className="border-2 border-black shadow-brutal font-bold w-full"
                onClick={handleApprove}
                disabled={submitting || !reviewer.trim()}
              >
                <IconShieldCheck className="mr-2 h-4 w-4" />
                Sign off
              </Button>
            </Card>
          </div>

          {(actionError || actionNote) && (
            <Alert className="border-2 border-black shadow-brutal">
              <IconAlertTriangle className="h-4 w-4" />
              <AlertDescription>{actionError ?? actionNote}</AlertDescription>
            </Alert>
          )}

          {history.length > 1 && (
            <Card className="border-2 border-black shadow-brutal overflow-hidden">
              <div className="p-4 border-b-2 border-black">
                <h3 className="font-black uppercase tracking-wide text-sm">
                  Assessment history ({history.length} versions)
                </h3>
              </div>
              <div className="divide-y-2 divide-gray-100">
                {history.map((record) => (
                  <div
                    key={record.assessmentId ?? record.id}
                    className="flex items-center justify-between gap-4 p-3 text-sm"
                  >
                    <span className="font-bold">v{record.version}</span>
                    <span className="text-muted-foreground truncate">{record.createdAt}</span>
                    {record.recommendation && (
                      <Badge
                        className={`border-2 border-black font-bold uppercase text-xs ${
                          RECOMMENDATION_STYLE[record.recommendation]
                        }`}
                      >
                        {RECOMMENDATION_LABEL[record.recommendation]}
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
