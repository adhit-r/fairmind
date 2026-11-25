'use client'

import { Bar, Stage, Text, Window } from './kit'
import { Cell, type CellState } from './fm'
import './evidence-demo.css'

// The still above the Evidence page's empty state: the evidence list behind,
// and in front one sealed item, what a run leaves on file. Overlapping
// windows: the card's left edge sits on the list's name column line, over
// filler only.

const ITEMS: { w: number; cls: CellState }[] = [
  { w: 120, cls: 'proven' },
  { w: 96, cls: 'attested' },
  { w: 132, cls: 'estimated' },
  { w: 88, cls: 'proven' },
  { w: 110, cls: 'attested' },
]

export function EvidenceDemo() {
  return (
    <Stage width={440} height={232} className="fm fv">
      {() => (
        <>
          <Window className="fv-window" title="Evidence">
            <div className="fv-body">
              {ITEMS.map((r, i) => (
                <div key={i} className="fv-row">
                  <Cell state={r.cls} />
                  <Bar w={r.w} h={6} tone={3} />
                  <Bar w={44} h={6} tone={2} className="fv-meta" />
                </div>
              ))}
            </div>
          </Window>

          <div className="fv-card">
            <div className="fv-card__top">
              <Cell state="proven" />
              <Text className="fv-card__title">Fairness metrics run</Text>
            </div>
            <div className="fv-card__line">
              <span className="fv-k">Class</span>
              <span className="fv-v">Measured</span>
            </div>
            <div className="fv-card__line">
              <span className="fv-k">Maps to</span>
              <span className="fv-chip">EU AI Act Art. 10</span>
            </div>
            <div className="fv-card__line">
              <span className="fv-k">Sealed</span>
              <span className="fv-hash">sha256 9f3c…e21a</span>
            </div>
          </div>
        </>
      )}
    </Stage>
  )
}
