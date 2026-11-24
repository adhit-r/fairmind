import Link from 'next/link'
import { ArrowUpRight } from 'lucide-react'
import type { AISystemSummary } from '@/components/workflow/SystemContext'
import { STAGE_LABEL } from './data/system-file'
import './home-lifecycle-chart.css'

const stages = ['onboard', 'assess', 'govern', 'remediate', 'operate']
const compact = new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 })
const integer = new Intl.NumberFormat('en')

function labelFor(stage: string) {
  if (Object.hasOwn(STAGE_LABEL, stage)) return STAGE_LABEL[stage]
  const label = stage.trim().replace(/[_-]+/g, ' ')
  return label ? label[0].toUpperCase() + label.slice(1) : 'Stage unreported'
}

export function HomeLifecycleChart({ systems }: { systems: readonly Pick<AISystemSummary, 'stage' | 'metadata'>[] }) {
  const counts = new Map<string, number>()
  let total = 0
  for (const system of systems) {
    if (system.metadata?.source === 'fallback') continue
    const stage = system.stage ?? ''
    if (stage.trim().toLowerCase() === 'retired') continue
    counts.set(stage, (counts.get(stage) ?? 0) + 1)
    total++
  }
  const legacy = [...counts.keys()].filter((stage) => !stages.includes(stage)).sort((a, b) => labelFor(a).localeCompare(labelFor(b)))
  const ordered = [...stages.filter((stage) => counts.has(stage)), ...legacy]
  const largest = Math.max(0, ...counts.values())
  // Small estates can show individual systems. For larger estates the bars retain the same 0–100% scale.
  const units = total <= 16 ? Array.from({ length: total }, (_, index) => index) : null

  return (
    <section className="home-lifecycle-chart" aria-labelledby="home-lifecycle-heading">
      <header className="hlc-header">
        <h2 id="home-lifecycle-heading">Systems by lifecycle stage</h2>
        <p>{integer.format(total)} active registered {total === 1 ? 'system' : 'systems'}</p>
      </header>
      {total === 0 ? <p className="hlc-empty">The register has no active systems.</p> : (
        <>
          <ul className="hlc-list" aria-label="Lifecycle stage distribution">
            {ordered.map((stage) => {
              const count = counts.get(stage) ?? 0
              const label = labelFor(stage)
              const detail = `${label}, ${integer.format(count)} of ${integer.format(total)} active systems`
              const contents = (
                <>
                  <span className="hlc-label">{label}</span>
                  {units ? (
                    <span className="hlc-units" aria-hidden="true">
                      {units.map((index) => <i key={index} data-filled={index < count} />)}
                    </span>
                  ) : (
                    <span className="hlc-track" aria-hidden="true"><i style={{ width: `${100 * count / total}%` }} /></span>
                  )}
                  <span className="hlc-count">{compact.format(count)}</span>
                </>
              )
              return (
                <li key={stage}>
                  {stage.trim() ? (
                    <Link className="hlc-row" href={`/systems?stage=${encodeURIComponent(stage)}`} aria-label={detail} data-leading={count === largest}>
                      {contents}<ArrowUpRight size={13} strokeWidth={1.7} aria-hidden="true" />
                    </Link>
                  ) : <span className="hlc-row" data-leading={count === largest}>{contents}</span>}
                </li>
              )
            })}
          </ul>
          <p className="hlc-key">{units ? <><i aria-hidden="true" />Each filled mark represents one system.</> : 'Bar length shows the share of active systems.'}</p>
        </>
      )}
    </section>
  )
}
