'use client'

import { Button, Check, Icon, Roll, Stage, Text, Window, type Act } from './kit'
import { Cell, type CellState } from './fm'
import './plan-demo.css'

// Beside "Register an AI system": what registering starts. The plan the agent
// recommends for the new system: three packs, each ticked in turn, each
// closing requirements of the framework below it, then the plan is accepted
// on its own button. Plays once in view and holds.

type S = { packs: number; accepted: boolean }

const PACKS = ['Fairness', 'Data governance', 'Human oversight']
// Twelve requirements of the framework; which pack closes each (0 = none of these).
const CLOSES = [1, 1, 2, 2, 1, 3, 0, 2, 3, 3, 1, 0]
const COVERED = (n: number) => CLOSES.filter((p) => p > 0 && p <= n).length

const initial: S = { packs: 0, accepted: false }
const POSTER: S = { packs: 3, accepted: true }

async function script(a: Act<S>) {
  await a.wait(900)
  for (let i = 1; i <= 3; i++) {
    await a.set({ packs: i })
    await a.wait(1100)
  }
  await a.click('accept')
  await a.set({ accepted: true })
  await a.move('rest')
  await a.wait(2400)
}

export function PlanDemo() {
  return (
    <Stage width={420} height={340} initial={initial} poster={POSTER} script={script} play="once" cursor={{ at: 'rest' }} className="fm fo">
      {(s) => (
        <>
          <Window className="fo-window" title="Plan">
            <div className="fo-body">
              <div className="fm-label">Agent recommends</div>
              <div className="fo-packs">
                {PACKS.map((p, i) => (
                  <div key={p} className="fo-pack" data-on={s.packs > i || undefined}>
                    <Check on={s.packs > i} pending={s.packs === i} size={16} />
                    <Text className="fo-pack__name">{p}</Text>
                    <span className="fo-pack__n">{CLOSES.filter((c) => c === i + 1).length} req.</span>
                  </div>
                ))}
              </div>

              <div className="fo-fw">
                <div className="fo-fw__head">
                  <Text className="fo-fw__name">EU AI Act</Text>
                  <span className="fo-fw__count">
                    <Roll>{`${COVERED(s.packs)} of 12`}</Roll>
                  </span>
                </div>
                <div className="fo-cells">
                  {CLOSES.map((p, i) => {
                    const state: CellState = p > 0 && p <= s.packs ? 'planned' : 'open'
                    return <Cell key={i} state={state} />
                  })}
                </div>
              </div>

              <div className="fo-actions">
                <Button variant="primary" data-target="accept" data-cursor="pointer" icon={s.accepted ? <Icon name="check" size={14} /> : undefined}>
                  {s.accepted ? 'Plan accepted' : 'Accept plan'}
                </Button>
              </div>
            </div>
          </Window>
          <span data-target="rest" style={{ position: 'absolute', left: 330, top: 300, width: 1, height: 1 }} />
        </>
      )}
    </Stage>
  )
}
