'use client'

import { useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { Selector } from '@astryxdesign/core/Selector'
import { TextInput } from '@astryxdesign/core/TextInput'
import { VStack } from '@astryxdesign/core/Layout'
import { runEnvAssessment } from '@/astryx/data/environment'

const PHASES = [
  { value: 'inference', label: 'Running the system (inference)' },
  { value: 'llm_inference', label: 'Running a language model (per 1M tokens)' },
  { value: 'training', label: 'Training' },
  { value: 'fine_tune', label: 'Fine-tuning' },
]
const PROVENANCE = [
  { value: 'measured', label: 'Measured' },
  { value: 'tool_estimated', label: 'Estimated by a tool' },
  { value: 'vendor_reported', label: 'Reported by the vendor' },
  { value: 'manual', label: 'Entered by hand' },
  { value: 'unknown', label: 'Unknown' },
]
const MITIGATION = [
  { value: 'missing', label: 'No plan yet' },
  { value: 'planned', label: 'Planned' },
  { value: 'documented', label: 'Documented' },
]
/** Which figure each phase is tiered on: the API picks it from the lifecycle phase. */
const FIGURES: Array<[string, string]> = [
  ['total_kwh', 'Energy used (kWh)'],
  ['total_kg_co2e_location', 'Emissions, location-based (kg CO2e)'],
  ['kg_co2e_per_1000_requests', 'Emissions per 1,000 requests (kg CO2e)'],
  ['kg_co2e_per_1m_tokens', 'Emissions per 1M tokens (kg CO2e)'],
]

/** Starts an environmental assessment on one system: the same POST /assess the API scores and stores. */
export function EnvAssessForm({ orgId, systemId, onSaved }: { orgId: string; systemId: string; onSaved: () => void }) {
  const [phase, setPhase] = useState('inference')
  const [provenance, setProvenance] = useState('unknown')
  const [mitigation, setMitigation] = useState('missing')
  const [source, setSource] = useState('')
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [uncertainty, setUncertainty] = useState('')
  const [figures, setFigures] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async () => {
    const metrics: Record<string, number> = {}
    for (const [k, v] of Object.entries(figures)) if (v.trim() !== '' && Number.isFinite(Number(v))) metrics[k] = Number(v)
    setBusy(true)
    setError(null)
    try {
      await runEnvAssessment(orgId, systemId, {
        lifecycle_phase: phase,
        provenance_class: provenance,
        mitigation_readiness: mitigation,
        measurement_source: source.trim() || 'unknown',
        ...(start ? { period_start: start } : {}),
        ...(end ? { period_end: end } : {}),
        ...(uncertainty.trim() !== '' && Number.isFinite(Number(uncertainty)) ? { uncertainty_pct: Number(uncertainty) } : {}),
        metrics,
      })
      onSaved()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'The assessment was not saved')
    } finally {
      setBusy(false)
    }
  }

  return (
    <VStack gap={4}>
      {error && <Banner status="error" title="The assessment was not saved" description={error} />}
      <Selector label="What is measured" options={PHASES} value={phase} onChange={setPhase} />
      {FIGURES.map(([key, label]) => (
        <TextInput key={key} label={label} description="Leave empty if you do not have it." value={figures[key] ?? ''} onChange={(v) => setFigures((f) => ({ ...f, [key]: v }))} />
      ))}
      <Selector label="How the figures were obtained" options={PROVENANCE} value={provenance} onChange={setProvenance} />
      <TextInput label="Source of the figures" description="For example a tool, a cloud bill or a vendor report." value={source} onChange={setSource} />
      <TextInput label="Period start" placeholder="YYYY-MM-DD" value={start} onChange={setStart} />
      <TextInput label="Period end" placeholder="YYYY-MM-DD" value={end} onChange={setEnd} />
      <TextInput label="Uncertainty (percent)" value={uncertainty} onChange={setUncertainty} />
      <Selector label="Plan to reduce the impact" options={MITIGATION} value={mitigation} onChange={setMitigation} />
      <Button label="Save the assessment" variant="primary" isDisabled={busy} onClick={() => void submit()} />
    </VStack>
  )
}
