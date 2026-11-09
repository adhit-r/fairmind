'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { StoredAnalyses } from '@/components/workflow/StoredAnalyses'
import { apiClient } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import { parseCsv } from '@/lib/csvRows'

type Method = 'causal' | 'counterfactual' | 'intersectional' | 'adversarial' | 'temporal' | 'contextual'
type Row = Record<string, string | number>

const E = API_ENDPOINTS.advancedBiasDetection
const METHODS: Array<{ value: Method; label: string; about: string; url: string; outcomeLabel: string }> = [
  { value: 'causal', label: 'Causal analysis', about: 'Analyze causal relationships in bias', url: E.causalAnalysis, outcomeLabel: 'Outcome column' },
  { value: 'counterfactual', label: 'Counterfactual analysis', about: 'Evaluate counterfactual fairness', url: E.counterfactualAnalysis, outcomeLabel: 'Prediction column' },
  { value: 'intersectional', label: 'Intersectional analysis', about: 'Detect intersectional bias across the chosen attributes together', url: E.intersectionalAnalysis, outcomeLabel: 'Outcome column' },
  { value: 'adversarial', label: 'Adversarial testing', about: 'Test adversarial robustness', url: E.adversarialTesting, outcomeLabel: 'Prediction column' },
  { value: 'temporal', label: 'Temporal analysis', about: 'Analyze bias over time', url: E.temporalAnalysis, outcomeLabel: 'Outcome column' },
  { value: 'contextual', label: 'Contextual analysis', about: 'Context-aware bias detection', url: E.contextualAnalysis, outcomeLabel: 'Outcome column' },
]
// The service reads these as free-form labels; one perturbation of the protected attributes is what it runs.
const ATTACK_VECTORS = ['attribute_perturbation']

interface Stored {
  stored_id?: string | null
  finding_id?: string | null
  bias_type: string
  analysis_method: string
  overall_bias_score: number
  confidence_level: number
  recommendations: string[]
  risk_assessment: Record<string, unknown>
}

function ColumnSelect({ label, value, onChange, header }: { label: string; value: string; onChange: (v: string) => void; header: string[] }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="rounded-[10px] border border-[var(--fm-line)]"><SelectValue placeholder="Choose a column" /></SelectTrigger>
        <SelectContent>{header.map((h) => <SelectItem key={h} value={h}>{h}</SelectItem>)}</SelectContent>
      </Select>
    </div>
  )
}

function ColumnChecks({ label, values, onChange, header }: { label: string; values: string[]; onChange: (v: string[]) => void; header: string[] }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <div className="flex flex-wrap gap-2">
        {header.map((h) => {
          const on = values.includes(h)
          return (
            <button key={h} type="button" onClick={() => onChange(on ? values.filter((v) => v !== h) : [...values, h])}
              className={`rounded-full border px-3 py-1 text-[12.5px] ${on ? 'border-[var(--fm-ink)] bg-[var(--fm-ink)] text-white' : 'border-[var(--fm-line)] bg-white text-[var(--fm-ink2)]'}`}>
              {h}
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default function AdvancedBiasPage() {
  const { selectedSystem } = useSystemContext()
  const systemId = selectedSystem.metadata?.source === 'fallback' || !selectedSystem.id ? undefined : selectedSystem.id
  const [method, setMethod] = useState<Method>('causal')
  const [file, setFile] = useState<{ name: string; header: string[]; rows: Row[]; truncated: boolean } | null>(null)
  const [outcome, setOutcome] = useState('')
  const [attributes, setAttributes] = useState<string[]>([])
  const [treatment, setTreatment] = useState('')
  const [timeColumn, setTimeColumn] = useState('')
  const [contexts, setContexts] = useState<string[]>([])
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<Stored | null>(null)

  const spec = METHODS.find((m) => m.value === method)!
  const header = file?.header ?? []

  const missing = !file ? 'Choose a CSV file'
    : !outcome ? `Choose the ${spec.outcomeLabel.toLowerCase()}`
    : attributes.length === 0 ? 'Choose at least one protected attribute'
    : method === 'causal' && !treatment ? 'Choose the treatment column'
    : method === 'temporal' && !timeColumn ? 'Choose the time column'
    : method === 'contextual' && contexts.length === 0 ? 'Choose at least one context column'
    : method === 'intersectional' && attributes.length < 2 ? 'Choose at least two attributes to combine'
    : null

  const onFile = async (f: File | undefined) => {
    setResult(null); setError(null)
    if (!f) return setFile(null)
    const parsed = parseCsv(await f.text())
    setFile({ name: f.name, ...parsed })
    setOutcome(''); setAttributes([]); setTreatment(''); setTimeColumn(''); setContexts([])
  }

  const body = () => {
    const rows = file!.rows
    // The counterfactual and adversarial models read the column named "prediction".
    const predictions = rows.map((r) => ({ ...r, prediction: r[outcome] }))
    switch (method) {
      case 'causal': return { data: rows, treatment_variable: treatment, outcome_variable: outcome, protected_attributes: attributes }
      case 'counterfactual': return { model_predictions: predictions, protected_attributes: attributes }
      case 'intersectional': return { data: rows, intersection_groups: [attributes], outcome_variable: outcome }
      case 'adversarial': return { model_predictions: predictions, attack_vectors: ATTACK_VECTORS, protected_attributes: attributes }
      case 'temporal': return { time_series_data: rows, time_column: timeColumn, outcome_variable: outcome, protected_attributes: attributes }
      case 'contextual': return { data: rows, context_features: contexts, protected_attributes: attributes, outcome_variable: outcome }
    }
  }

  const run = async () => {
    setRunning(true); setError(null); setResult(null)
    const res = await apiClient.post<Stored>(spec.url, { ...body(), system_id: systemId })
    if (res.success && res.data) setResult(res.data)
    else setError(res.error || 'The analysis failed')
    setRunning(false)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[30px] font-semibold tracking-[-.03em]">Advanced Bias Detection</h1>
        <p className="text-[var(--fm-ink2)] mt-1">Upload decisions as a CSV, choose the columns, and the result is stored against the selected system.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6 space-y-4">
          <h2 className="text-lg font-semibold">Run an analysis</h2>
          <div className="space-y-2">
            <Label>Method</Label>
            <Select value={method} onValueChange={(v) => { setMethod(v as Method); setResult(null) }}>
              <SelectTrigger className="rounded-[10px] border border-[var(--fm-line)]"><SelectValue /></SelectTrigger>
              <SelectContent>{METHODS.map((m) => <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>)}</SelectContent>
            </Select>
            <p className="text-[12.5px] text-[var(--fm-ink2)]">{spec.about}</p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="csv">CSV file</Label>
            <input id="csv" type="file" accept=".csv,text/csv" onChange={(e) => onFile(e.target.files?.[0])}
              className="block w-full rounded-[10px] border border-[var(--fm-line)] bg-white p-2 text-[13px]" />
            {file && <p className="text-[12.5px] text-[var(--fm-ink2)]">{file.name}: {file.rows.length} rows{file.truncated ? ' (the first 5000 are used)' : ''}</p>}
          </div>
          {file && (
            <>
              <ColumnSelect label={spec.outcomeLabel} value={outcome} onChange={setOutcome} header={header} />
              {method === 'causal' && <ColumnSelect label="Treatment column" value={treatment} onChange={setTreatment} header={header} />}
              {method === 'temporal' && <ColumnSelect label="Time column" value={timeColumn} onChange={setTimeColumn} header={header} />}
              <ColumnChecks label="Protected attributes" values={attributes} onChange={setAttributes} header={header} />
              {method === 'contextual' && <ColumnChecks label="Context columns" values={contexts} onChange={setContexts} header={header} />}
            </>
          )}
          {!systemId && <p className="text-[12.5px] text-[var(--fm-ink2)]">No system is selected, so this result will not be stored.</p>}
          {missing && file && <p className="text-[12.5px] text-[var(--fm-ink2)]">{missing}</p>}
          {error && <p className="text-[13px] text-red-700">{error}</p>}
          <Button className="rounded-full" onClick={run} disabled={running || !!missing}>{running ? 'Running analysis...' : 'Run analysis'}</Button>
        </Card>

        <Card className="p-6 space-y-3">
          <h2 className="text-lg font-semibold">Result</h2>
          {result ? (
            <>
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">{result.analysis_method}</Badge>
                {typeof result.risk_assessment.risk_level === 'string' && <Badge variant="outline">risk {result.risk_assessment.risk_level}</Badge>}
                {result.stored_id && <Badge variant="outline">stored</Badge>}
                {result.finding_id && <Badge variant="outline">finding opened</Badge>}
              </div>
              <p className="text-[13px] text-[var(--fm-ink2)]">Bias score {result.overall_bias_score.toFixed(3)}, confidence {result.confidence_level.toFixed(2)}</p>
              <ul className="list-disc pl-5 text-[13px] space-y-1">{result.recommendations.map((r) => <li key={r}>{r}</li>)}</ul>
            </>
          ) : (
            <p className="text-[13px] text-[var(--fm-ink2)]">Run an analysis to see its result here.</p>
          )}
        </Card>
      </div>

      {systemId && <StoredAnalyses systemId={systemId} sources={['advanced']} refreshKey={result?.stored_id ?? 0} />}
    </div>
  )
}
