'use client'

import { Bar, Stage, Text, Window } from './kit'
import { CHECKS, Cell, type CellState } from './fm'
import './estate-demo.css'

// The still above the dashboard's empty state, "No AI systems under
// governance yet": the Estate grid as it reads once sources are connected.
// Pinned, bottom bleed; a corner chip says where the rows came from. Names
// are filler; the cells and the gate are the subject.

const ROWS: { name?: string; w?: number; cells: CellState[]; verdict: 'go' | 'cond' | 'nogo' }[] = [
  { w: 92, cells: ['proven', 'proven', 'attested', 'proven', 'estimated'], verdict: 'go' },
  { w: 70, cells: ['proven', 'estimated', 'attested', 'proven', 'open'], verdict: 'cond' },
  { w: 104, cells: ['fails', 'estimated', 'attested', 'stale', 'open'], verdict: 'nogo' },
  { w: 80, cells: ['proven', 'attested', 'attested', 'estimated', 'open'], verdict: 'cond' },
]
const LABEL = { go: 'Go', cond: 'Conditional go', nogo: 'No go' }
const SHORT = ['Fairness', 'Data', 'Oversight', 'Monitoring', 'Environ.']

export function EstateDemo() {
  return (
    <Stage width={440} height={262} className="fm fe">
      {() => (
        <>
          <Window
            className="fe-window"
            title="Estate"
            toolbar={
              <span className="fe-chip">
                <i />
                MLflow · 4 found
              </span>
            }
          >
            <div className="fe-body">
              <div className="fe-head">
                <span className="fm-label">System</span>
                {SHORT.map((c, i) => (
                  <span key={c} className="fe-vh" title={CHECKS[i]}>
                    {c}
                  </span>
                ))}
                <span className="fm-label fe-gate">Gate</span>
              </div>
              {ROWS.map((r, i) => (
                <div key={i} className="fe-row">
                  <span>{r.name ? <Text>{r.name}</Text> : <Bar w={r.w!} h={6} tone={3} />}</span>
                  {r.cells.map((c, j) => (
                    <span key={j} className="fe-cell">
                      <Cell state={c} />
                    </span>
                  ))}
                  <span className="fe-gate">
                    <span className="fm-verdict" data-tone={r.verdict}>
                      <i />
                      {LABEL[r.verdict]}
                    </span>
                  </span>
                </div>
              ))}
            </div>
          </Window>
        </>
      )}
    </Stage>
  )
}
