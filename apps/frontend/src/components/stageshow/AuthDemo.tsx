'use client'

import { Bar, Button, Collapse, Fly, Roll, Spinner, Stage, States, Text, Window, type Act } from './kit'
import { CHECKS, Cell, Rail, type CellState } from './fm'
import './auth-demo.css'

// The panel beside the sign-in form. One continuous story in the real app:
// the agent scans the sources, finds a model, it joins the inventory with
// every release check open, the plan marks what each check needs, the run
// fills them with proof, and the gate reads the result. Plays once in view
// and holds the payoff; the poster is that payoff.

type S = {
  stage: number
  scanning: boolean
  found: boolean
  slot: boolean
  go: boolean
  added: boolean
  cells: CellState[]
  verdict: 'none' | 'planned' | 'cond'
}

const OPEN: CellState[] = ['open', 'open', 'open', 'open', 'open']
const PLANNED: CellState[] = ['planned', 'planned', 'planned', 'planned', 'planned']
const RUN: CellState[] = ['proven', 'estimated', 'attested', 'proven', 'open']

const initial: S = { stage: 0, scanning: false, found: false, slot: false, go: false, added: false, cells: OPEN, verdict: 'none' }
const POSTER: S = { ...initial, stage: 2, slot: true, added: true, cells: RUN, verdict: 'cond' }

// The estate already under governance: names are filler, the cells and
// verdicts are what a governance lead reads.
const ESTATE: { w: number; cells: CellState[]; verdict: 'go' | 'nogo' | 'cond' }[] = [
  { w: 96, cells: ['proven', 'proven', 'attested', 'proven', 'estimated'], verdict: 'go' },
  { w: 78, cells: ['fails', 'estimated', 'attested', 'stale', 'open'], verdict: 'nogo' },
  { w: 110, cells: ['proven', 'attested', 'attested', 'estimated', 'open'], verdict: 'cond' },
  { w: 64, cells: ['proven', 'proven', 'proven', 'attested', 'estimated'], verdict: 'go' },
  { w: 88, cells: ['estimated', 'attested', 'open', 'planned', 'open'], verdict: 'nogo' },
  { w: 102, cells: ['proven', 'proven', 'attested', 'proven', 'proven'], verdict: 'go' },
  { w: 72, cells: ['attested', 'estimated', 'attested', 'stale', 'open'], verdict: 'cond' },
]

const VERDICT = { go: 'Go', nogo: 'No go', cond: 'Conditional go', planned: 'Planned', none: '' }

async function script(a: Act<S>) {
  await a.wait(700)

  // 1. Scan the connected sources
  await a.click('scan')
  await a.set({ scanning: true })
  await a.wait(1300)
  await a.set({ scanning: false, found: true })
  await a.move('rest-1')
  await a.wait(900)

  // 2. Add the candidate: its row opens in the estate, the candidate travels into it
  await a.click('add')
  await a.set({ slot: true })
  await a.wait(420)
  await a.set({ go: true })
  await a.wait(760)
  await a.set({ added: true, go: false, found: false })
  await a.move('rest-2')
  await a.wait(900)

  // 3. Plan: the rail moves on, each check gets what it needs
  await a.set({ stage: 1, verdict: 'planned' })
  await a.wait(250)
  for (let i = 0; i < 5; i++) {
    await a.set((s) => ({ cells: s.cells.map((c, j) => (j === i ? PLANNED[j] : c)) }))
    await a.wait(90)
  }
  await a.wait(1100)

  // 4. Run: proof arrives check by check; Environmental stays open
  await a.set({ stage: 2 })
  await a.wait(300)
  for (let i = 0; i < 5; i++) {
    await a.set((s) => ({ cells: s.cells.map((c, j) => (j === i ? RUN[j] : c)) }))
    await a.wait(320)
  }
  await a.wait(350)

  // 5. The gate reads it
  await a.set({ verdict: 'cond' })
  await a.wait(2400)
}

function Head() {
  return (
    <div className="fa-head">
      <span className="fa-head__sys fm-label">System</span>
      {CHECKS.map((c) => (
        <span key={c} className="fa-vh">
          {c}
        </span>
      ))}
      <span className="fa-head__gate fm-label">Gate</span>
    </div>
  )
}

function Line({ name, cells, verdict, ...rest }: { name: React.ReactNode; cells: CellState[]; verdict: keyof typeof VERDICT } & Record<`data-${string}`, unknown>) {
  return (
    <div className="fa-row" {...rest}>
      <span className="fa-row__name">{name}</span>
      {cells.map((c, i) => (
        <span key={i} className="fa-row__cell">
          <Cell state={c} />
        </span>
      ))}
      <span className="fa-row__gate">
        {verdict === 'none' ? null : (
          <span className="fm-verdict" data-tone={verdict === 'planned' ? undefined : verdict}>
            <i />
            <Roll variant="fade">{VERDICT[verdict]}</Roll>
          </span>
        )}
      </span>
    </div>
  )
}

export function AuthDemo() {
  return (
    <Stage width={720} height={600} initial={initial} poster={POSTER} script={script} play="once" cursor={{ at: 'rest-0' }} className="fm fa">
      {(s, rect) => (
        <>
          <Window className="fa-window" title="Inventory" sidebar={<Rail at={s.stage} />} sidebarWidth={164}>
            <div className="fa-body">
              <div className="fa-toolbar">
                <Button size="medium" data-target="scan" data-cursor="pointer">
                  <States value={s.scanning ? 'busy' : 'idle'} states={{ idle: 'Scan sources', busy: <span className="fa-busy"><span className="fa-spin"><Spinner size={12} /></span>Scanning</span> }} />
                </Button>
                <span className="fa-sources">
                  <span className="fa-source"><i />MLflow</span>
                  <span className="fa-source"><i />GitHub</span>
                </span>
              </div>

              <Collapse open={s.found} reveal="drop">
                <div className="fa-found">
                  <div className="fm-label">Agent discovery</div>
                  <div className="fa-cand" data-target="cand" data-gone={s.go || s.added || undefined}>
                    <span className="fa-source fa-source--on"><i />MLflow</span>
                    <Text className="fa-cand__name" data-target="cand-name">Credit risk scorer</Text>
                    <span className="fa-cand__tier">Suggested tier high</span>
                    <Button size="small" variant="primary" data-target="add" data-cursor="pointer">
                      Add
                    </Button>
                  </div>
                </div>
              </Collapse>

              <div className="fa-grid">
                <Head />
                <Collapse open={s.slot}>
                  <Line data-target="newrow" name={<Text className="fa-row__real" data-target="row-name" style={{ opacity: s.added ? 1 : 0 }}>Credit risk scorer</Text>} cells={s.added ? s.cells : ['none', 'none', 'none', 'none', 'none']} verdict={s.added ? s.verdict : 'none'} />
                </Collapse>
                {ESTATE.map((r, i) => (
                  <Line key={i} name={<Bar w={r.w} h={6} tone={3} />} cells={r.cells} verdict={r.verdict} />
                ))}
              </div>
            </div>
          </Window>

          <Fly from={rect('cand-name')} to={rect('row-name')} go={s.go}>
            <Text className="fa-row__real">Credit risk scorer</Text>
          </Fly>

          <span data-target="rest-0" className="fa-rest" style={{ left: 600, top: 150 }} />
          <span data-target="rest-1" className="fa-rest" style={{ left: 560, top: 250 }} />
          <span data-target="rest-2" className="fa-rest" style={{ left: 620, top: 152 }} />
        </>
      )}
    </Stage>
  )
}
