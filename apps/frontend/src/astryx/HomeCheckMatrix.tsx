import Link from 'next/link'
import { Check, ChevronDown, Circle, Clock3, Minus, RefreshCw, X } from 'lucide-react'
import type { CSSProperties } from 'react'
import type { AISystemSummary } from '@/components/workflow/SystemContext'
import type { EstateGate } from '@/lib/api/hooks/useEstate'
import './home-check-matrix.css'

type Row = { system: AISystemSummary; gate: EstateGate }
type Column = { key: string; name: string; group: string }

type Props = {
  shown: Row[]
  empty: Row[]
  columns: Column[]
  partial: boolean
  checkedAt: Date | null
  onRefresh: () => void
  onSelect: (systemId: string, check: string) => void
  stateOf: (gate: EstateGate, column: Column) => string
  wordFor: (column: Column, state: string) => string
}

function StateMark({ state }: { state: string }) {
  const Mark = state === 'fails' ? X
    : state === 'proven' || state === 'attested' ? Check
    : state === 'stale' || state === 'needs' ? Clock3
    : state === 'unavailable' || state === 'excluded' ? Minus
    : Circle
  return <Mark className="hm-state-mark" size={12} aria-hidden />
}

export function HomeCheckMatrix({ shown, empty, columns, partial, checkedAt, onRefresh, onSelect, stateOf, wordFor }: Props) {
  // Keep the first failure in view even when the remaining systems scroll horizontally.
  const failedRow = shown.find(({ gate }) => columns.some(col => stateOf(gate, col) === 'fails'))
  const failedColumn = failedRow && columns.find(col => stateOf(failedRow.gate, col) === 'fails')
  const orderedSystems = failedRow ? [failedRow, ...shown.filter(row => row !== failedRow)] : shown
  const orderedChecks = failedColumn ? [failedColumn, ...columns.filter(col => col !== failedColumn)] : columns
  const groups = [...new Set(orderedChecks.map(col => col.group))].map(name => ({
    name, checks: orderedChecks.filter(col => col.group === name),
  }))

  return (
    <section className="fm-home-matrix" aria-label="Every system against every release check">
      <header className="hm-header">
        <h2>Release check matrix</h2>
        <span className="hm-coverage" data-partial={partial} role="status">
          <i aria-hidden />{partial ? 'Partial coverage' : 'Live'}
          {checkedAt && <time dateTime={checkedAt.toISOString()} title="Last checked">{checkedAt.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}</time>}
        </span>
        <button type="button" className="hm-refresh" aria-label="Check now" title="Check now" onClick={onRefresh}>
          <RefreshCw size={14} aria-hidden />
        </button>
      </header>

      {shown.length ? (
        <div className="hm-scroll" tabIndex={shown.length > 1 ? 0 : undefined} aria-label="Release checks by stage and system">
          <table className={shown.length > 1 ? 'hm-many' : undefined} style={{ '--hm-systems': shown.length } as CSSProperties}>
            <thead>
              <tr>
                <th scope="col" className="hm-stage">Stage</th>
                {orderedSystems.map(({ system, gate }) => (
                  <th scope="col" key={system.id} className="hm-system">
                    <Link href={`/systems/${encodeURIComponent(system.id)}`}>{system.name}</Link>
                    <span>Gate confidence {Math.round(gate.confidence * 100)}%</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {groups.map(({ name, checks }) => (
                <tr key={name}>
                  <th scope="row" className="hm-stage">
                    {name}<small>{name === 'Release' ? 'Human decision' : `${checks.length} ${checks.length === 1 ? 'check' : 'checks'}`}</small>
                  </th>
                  {orderedSystems.map(({ system, gate }) => (
                    <td key={system.id}>
                      <div className="hm-tiles">
                        {checks.map(col => {
                          const state = stateOf(gate, col)
                          const word = wordFor(col, state)
                          return (
                            <button key={col.key} type="button" className="cell" data-state={state}
                              aria-label={`${col.name} on ${system.name}: ${word}`} onClick={() => onSelect(system.id, col.key)}>
                              <strong>{col.name}</strong>
                              <span><StateMark state={state} />{word}</span>
                            </button>
                          )
                        })}
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : <p className="hm-empty">Systems appear here when they have a result or a release decision request.</p>}

      {empty.length > 0 && (
        <details className="hm-inventory">
          <summary>{empty.length} {empty.length === 1 ? 'system' : 'systems'} without evidence<ChevronDown size={15} aria-hidden /></summary>
          <ul>{empty.map(({ system }) => (
            <li key={system.id}><Link href={`/systems/${encodeURIComponent(system.id)}`}>{system.name}</Link></li>
          ))}</ul>
          <ol>
            <li><Link href="/systems">Name an owner and confirm the risk tier</Link> on each system.</li>
            <li><Link href="/frameworks">Confirm which frameworks apply</Link>.</li>
            <li><Link href="/evaluations">Run a first evaluation</Link>.</li>
          </ol>
        </details>
      )}
    </section>
  )
}
