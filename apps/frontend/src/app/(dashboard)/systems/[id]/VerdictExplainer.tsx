'use client'

import Link from 'next/link'
import { Pill, cap } from '@/components/packs/parts'
import type { GateCheck, GateExplain, GatePath, GatePathOption, GatePathStep, ReleaseGate, Verdict } from '@/lib/api/hooks/useSystemFile'
import { cn } from '@/lib/utils'

export const VERDICT_LABEL: Record<Verdict, string> = { go: 'Go', conditional_go: 'Conditional go', no_go: 'No go' }
export const VERDICT_TONE: Record<Verdict, string> = { go: 'text-[#1f7a4d]', conditional_go: 'text-[#a14d00]', no_go: 'text-[#b4232c]' }

const SECTION = 'text-[11px] font-semibold uppercase tracking-[.08em] text-[var(--fm-ink3)]'
const two = (n: number) => n.toFixed(2)
const sentence = (s: string) => `${s.replace(/\.$/, '')}.`
const lowerFirst = (s: string) => s.charAt(0).toLowerCase() + s.slice(1)
const day = (iso: string) => new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })

/** "a", "a and b", "a, b and c". */
export function listJoin(items: string[]) {
  return items.length < 2 ? items.join('') : `${items.slice(0, -1).join(', ')} and ${items[items.length - 1]}`
}

/** One cell of the tier's matrix row as a confidence range: "0.70 and up", "0.35 to 0.69", "Below 0.35". */
export function bandRange({ from, to }: GateExplain['row'][number]) {
  if (to === null) return `${two(from)} and up`
  if (from <= 0) return `Below ${two(to)}`
  return `${two(from)} to ${two(to - 0.01)}`
}

export function arithmetic(gate: ReleaseGate) {
  const counts = `${gate.proven} proven, ${gate.attested} attested, ${gate.open} open.`
  if (!gate.explain) return `Confidence ${two(gate.confidence)}: ${counts}`
  return `${cap(gate.explain.effectiveTier)} tier. Confidence ${two(gate.confidence)} is the average of five checks, each worth up to ${two(gate.explain.perCheck)}: ${counts}`
}

const checkName = (key: GateCheck['key'], gate: ReleaseGate) => (gate.checks.find((c) => c.key === key)?.label ?? key.replace(/_/g, ' ')).toLowerCase()

const ACTION_TITLE: Record<GatePathStep['action'], (check: string) => string> = {
  fairness_run: () => 'Run a fairness test',
  environmental_assessment: () => 'Run an environmental assessment',
  monitoring_snapshot: () => 'Record a monitoring snapshot',
  attest: (check) => `Attest ${check}`,
  evidence_upload: (check) => `Upload ${check} evidence`,
}

export const stepTitle = (step: GatePathStep, gate: ReleaseGate) => ACTION_TITLE[step.action](checkName(step.check, gate))

const CLASS_PILL: Record<GatePathStep['evidenceClass'], { label: string; tone: 'done' | 'info' | 'warn' | 'plain' }> = {
  measured: { label: 'Measured', tone: 'done' },
  tool_estimated: { label: 'Tool estimate', tone: 'info' },
  manual: { label: 'Manual evidence', tone: 'plain' },
}

/** The evidence-class pill and what the step can count for; an attestation is always a named person's statement. */
export function stepClass(step: GatePathStep) {
  if (step.action === 'attest') return { label: 'Attestation', tone: 'warn' as const, detail: `a named person's statement, counts ${two(step.counts)} at most` }
  return { ...CLASS_PILL[step.evidenceClass], detail: `counts up to ${two(step.counts)}` }
}

/** The line under a step's title; the cap is said once, in the detail, and the server's note adds what the evidence is. */
export const stepLine = (step: GatePathStep) => `${stepClass(step).detail} · +${two(step.gain)} confidence${step.note ? ` · ${step.note}` : ''}`

const RANK: Record<Verdict, number> = { no_go: 0, conditional_go: 1, go: 2 }

/** The option that reaches the next verdict up (or past it), or null when nothing FairMind records today gets there. */
export function bestOption(path: GatePath | undefined): GatePathOption | null {
  const target = path?.target
  return target ? path.options.find((o) => RANK[o.verdictAfter] >= RANK[target]) ?? null : null
}

const stepKey = (s: GatePathStep) => `${s.check}:${s.action}`

/** The shortest path to Go when it differs from the next-verdict path shown above it, else null. */
export function goPath(path: GatePath | undefined, best: GatePathOption | null) {
  const go = path?.toGo
  return go && best && go.steps.map(stepKey).join() !== best.steps.map(stepKey).join() ? go : null
}

/** True when the target is out of reach for lack of confidence, not because of a failing check. */
export function confidenceShort(gate: ReleaseGate) {
  const target = gate.path?.target
  const need = target ? gate.explain?.row.filter((c) => RANK[c.verdict] >= RANK[target]).map((c) => c.from) ?? [] : []
  return need.length > 0 && gate.path!.ceiling.confidence < Math.min(...need)
}

/** One line for the run result: how far the next verdict is. */
export function pathSummary(gate: ReleaseGate) {
  const path = gate.path
  if (!path?.target) return null
  const best = bestOption(path)
  if (!best) return `${VERDICT_LABEL[path.target]} is not reachable with what FairMind records today. Best possible now: ${two(path.ceiling.confidence)}, ${VERDICT_LABEL[path.ceiling.verdict]}.`
  if (best.steps.length === 0) return null
  const first = lowerFirst(stepTitle(best.steps[0], gate))
  const target = VERDICT_LABEL[best.verdictAfter]
  return best.steps.length === 1 ? `One step reaches ${target}: ${first}.` : `${best.steps.length} steps reach ${target}, starting with: ${first}.`
}

/** Why the attestation-only route is or is not the faster one. */
export function attestationNote(gate: ReleaseGate, best: GatePathOption) {
  const alt = gate.path?.options.find((o) => o !== best && o.kind === 'attestations')
  if (!alt || alt.steps.length === 0) return null
  const checks = listJoin(alt.steps.map((s) => checkName(s.check, gate)))
  const most = two(Math.max(...alt.steps.map((s) => s.counts)))
  const reach = alt.verdictAfter === best.verdictAfter ? 'also reaches' : 'reaches'
  const blocked = alt.approvalReady ? '' : best.approvalReady ? ' Approval would still be blocked by the list below, so it is not faster.' : ' Approval would still be blocked by the list below.'
  return `Attesting ${checks} ${reach} ${two(alt.confidenceAfter)}, ${VERDICT_LABEL[alt.verdictAfter]}. Each is a named person's statement and counts ${most} at most.${blocked}`
}

/** "Tier High, suggested by rule T1, confirmed by {actor} on {date}"; a tier set by hand says whether it is below or above the suggestion. */
export function tierLine(explain: GateExplain) {
  const src = explain.tierSource
  const tier = cap(explain.tier)
  if (!src) return `Tier ${tier}, not confirmed by a person.`
  const rules = src.ruleIds.length ? ` by rule${src.ruleIds.length === 1 ? '' : 's'} ${listJoin(src.ruleIds)}` : ''
  const basis = src.suggestedTier === explain.tier ? `suggested${rules}` : `${src.tierBelowSuggestion ? 'below' : 'above'} the ${cap(src.suggestedTier)} suggested${rules}`
  return `Tier ${tier}, ${basis}, confirmed by ${src.confirmedBy} on ${day(src.confirmedAt)}.`
}

/** A tier set below the suggestion: until a second person accepts it, the gate keeps the suggested tier. */
export function tierOverride(explain: GateExplain | undefined) {
  const src = explain?.tierSource
  if (!src?.tierBelowSuggestion) return null
  const suggested = cap(src.suggestedTier)
  return src.overrideAcceptedBy
    ? { pending: false, text: `Tier set below the suggested ${suggested}; ${src.overrideAcceptedBy} accepted it.` }
    : { pending: true, text: `Tier set below the suggested ${suggested}. The gate uses ${suggested} until another person accepts the lower tier.` }
}

export const STEP_LINK: Record<Exclude<GatePathStep['action'], 'attest'>, { label: string; href: string }> = {
  fairness_run: { label: 'Open the test', href: '#first-verdict' },
  monitoring_snapshot: { label: 'Open monitoring', href: '#operate' },
  environmental_assessment: { label: 'Open assessment', href: '/ai-governance' },
  evidence_upload: { label: 'Record evidence', href: '/evidence?view=artifacts' },
}

function StepAction({ step, primary, onAttest, onOpen }: { step: GatePathStep; primary: boolean; onAttest?: (check: GateCheck['key']) => void; onOpen?: (href: string) => void }) {
  const cls = cn(
    'inline-flex h-9 shrink-0 items-center rounded-full px-4 text-[12.5px] font-semibold',
    primary ? 'bg-[var(--fm-ink)] text-white' : 'border border-[var(--fm-line)] bg-white font-medium text-[var(--fm-ink2)] hover:border-[var(--fm-ink)] hover:text-[var(--fm-ink)]',
  )
  if (step.action === 'attest') return onAttest ? <button type="button" onClick={() => onAttest(step.check)} className={cls}>Attest</button> : null
  const { label, href } = STEP_LINK[step.action]
  if (href.startsWith('#')) return <a href={href} className={cls}>{label}</a>
  if (onOpen) return <button type="button" onClick={() => onOpen(href)} className={cls}>{label}</button>
  return <Link href={href} className={cls}>{label}</Link>
}

type StepRowProps = { step: GatePathStep; n: number; primary: boolean; gate: ReleaseGate; tag?: string; onAttest?: (check: GateCheck['key']) => void; onOpen?: (href: string) => void }

function StepRow({ step, n, primary, gate, tag, onAttest, onOpen }: StepRowProps) {
  const cls = stepClass(step)
  return (
    <li className="grid grid-cols-[20px_minmax(0,1fr)] items-start gap-x-2.5 gap-y-2 rounded-[10px] bg-white p-3 sm:grid-cols-[20px_minmax(0,1fr)_auto]">
      <span className="text-[13px] font-semibold tabular-nums">{n}</span>
      <div className="min-w-0">
        <div className="text-[13px] font-semibold">
          {stepTitle(step, gate)}
          {tag && <span className="font-normal text-[var(--fm-ink3)]"> · {tag}</span>}
        </div>
        <div className="mt-1 flex flex-wrap items-center gap-x-1.5 gap-y-1">
          <Pill tone={cls.tone}>{cls.label}</Pill>
          <span className="text-[12px] text-[var(--fm-ink2)]">{stepLine(step)}</span>
        </div>
      </div>
      <div className="col-start-2 sm:col-start-auto">
        <StepAction step={step} primary={primary} onAttest={onAttest} onOpen={onOpen} />
      </div>
    </li>
  )
}

/**
 * The release gate explaining itself, entirely from what the gate returned: the tier it was computed on,
 * the confidence arithmetic, the tier's row of the decision matrix and the cheapest honest steps up.
 * `onOpen` navigates to another page with this system selected; without it, plain links are used.
 */
export function VerdictExplainer({ gate, compact = false, onAttest, onOpen }: { gate: ReleaseGate; compact?: boolean; onAttest?: (check: GateCheck['key']) => void; onOpen?: (href: string) => void }) {
  if (compact) {
    const summary = pathSummary(gate)
    return (
      <div className="flex flex-wrap items-baseline gap-x-2.5 gap-y-1 border-t border-[var(--fm-line)] pt-3">
        <span className="text-[13px]">
          Release gate after this run: <span className={cn('font-semibold', VERDICT_TONE[gate.verdict])}>{VERDICT_LABEL[gate.verdict]}</span>
        </span>
        {summary && <span className="text-[12.5px] text-[var(--fm-ink2)]">{summary}</span>}
        <a href="#decision" className="ml-auto text-[12.5px] font-semibold text-[var(--fm-ink)] underline-offset-2 hover:underline">Act on it in Decision</a>
      </div>
    )
  }

  const { explain, path } = gate
  const best = bestOption(path)
  const alt = best ? attestationNote(gate, best) : null
  const go = goPath(path, best)
  const override = tierOverride(explain)
  const reasons = [...gate.reasons, ...(path?.notes ?? [])]

  return (
    <div className="mt-4 grid gap-4">
      <div>
        <h3 className={cn('text-[18px] font-semibold tracking-[-.01em]', VERDICT_TONE[gate.verdict])}>Why {VERDICT_LABEL[gate.verdict]}</h3>
        <p className="mt-1.5 text-[13px] leading-normal text-[var(--fm-ink2)]">{arithmetic(gate)}</p>
        {explain && explain.row.length > 0 && (
          <ol aria-label="The decision matrix for this tier" className="mt-2.5 grid max-w-[620px] gap-2 sm:grid-cols-3">
            {explain.row.map((cell) => {
              const here = cell.band === gate.band
              return (
                <li key={cell.band} aria-current={here ? 'true' : undefined} className={cn('rounded-[10px] border bg-white px-3 py-2.5', here ? 'border-[var(--fm-ink)]' : 'border-[var(--fm-line)]')}>
                  <div className={cn('text-[11.5px]', here ? 'text-[var(--fm-ink2)]' : 'text-[var(--fm-ink3)]')}>{bandRange(cell)}{here && ' · you are here'}</div>
                  <div className={cn('text-[13px] font-semibold', here && VERDICT_TONE[cell.verdict])}>{VERDICT_LABEL[cell.verdict]}</div>
                </li>
              )
            })}
          </ol>
        )}
        {reasons.length > 0 && (
          <ul className="mt-2.5 grid gap-0.5 text-[12.5px] leading-snug text-[var(--fm-ink2)]">
            {reasons.map((r, i) => <li key={`${i}:${r}`}>{sentence(r)}</li>)}
          </ul>
        )}
      </div>

      {path?.target && (
        <div className="grid gap-2.5 rounded-[12px] border border-[var(--fm-line)] bg-[var(--fm-bg)] p-4">
          {best ? (
            <>
              <div className="text-[13.5px] font-semibold">Fastest honest path to {VERDICT_LABEL[path.target]}</div>
              <ol className="grid gap-2">
                {best.steps.map((step, i) => (
                  <StepRow key={stepKey(step)} step={step} n={i + 1} primary={i === 0} gate={gate} onAttest={onAttest} onOpen={onOpen} />
                ))}
              </ol>
              <p className="text-[12.5px] text-[var(--fm-ink)]">
                Confidence after: {two(best.confidenceAfter)}, verdict <span className={cn('font-semibold', VERDICT_TONE[best.verdictAfter])}>{VERDICT_LABEL[best.verdictAfter]}</span>.
                {best.verdictAfter === 'conditional_go' && ' Approval then needs written conditions.'}
                {!best.approvalReady && ' Approval would still be blocked by the list below.'}
              </p>
              {alt && (
                <p className="border-t border-[var(--fm-line)] pt-2.5 text-[12.5px] leading-normal text-[var(--fm-ink2)]">
                  <span className="font-semibold text-[var(--fm-ink)]">Attestations instead:</span> {alt}
                </p>
              )}
              {go && (
                <div className="grid gap-2.5 border-t border-[var(--fm-line)] pt-2.5">
                  <div className="text-[13.5px] font-semibold">
                    Shortest path to Go <span className="font-normal text-[var(--fm-ink3)]">· {go.steps.length} step{go.steps.length === 1 ? '' : 's'}</span>
                  </div>
                  <ol className="grid gap-2">
                    {go.steps.map((step, i) => {
                      const above = best.steps.findIndex((s) => stepKey(s) === stepKey(step))
                      const tag = above < 0 ? undefined : best.steps.length === 1 ? 'the step above' : `step ${above + 1} above`
                      return <StepRow key={stepKey(step)} step={step} n={i + 1} primary={false} gate={gate} tag={tag} onAttest={onAttest} onOpen={onOpen} />
                    })}
                  </ol>
                  <p className="text-[12.5px] text-[var(--fm-ink)]">
                    Confidence after: {two(go.confidenceAfter)}, verdict <span className={cn('font-semibold', VERDICT_TONE[go.verdictAfter])}>{VERDICT_LABEL[go.verdictAfter]}</span>.
                    {!go.approvalReady && ' Approval would still be blocked by the list below.'}
                  </p>
                </div>
              )}
            </>
          ) : (
            <>
              <div className="text-[13.5px] font-semibold">Path to {VERDICT_LABEL[path.target]}</div>
              <p className="text-[12.5px] leading-normal text-[var(--fm-ink)]">
                Not reachable with what FairMind records today. Best possible now: {two(path.ceiling.confidence)}, {VERDICT_LABEL[path.ceiling.verdict]}.
              </p>
              {confidenceShort(gate) && (
                <p className="flex flex-wrap items-center gap-2 text-[12.5px] text-[var(--fm-ink2)]">
                  <Pill>Coming soon</Pill>
                  Measured data-governance and oversight checks
                </p>
              )}
            </>
          )}
        </div>
      )}

      {path && path.approvalBlockers.length > 0 && (
        <div>
          <div className={SECTION}>Before anyone can approve</div>
          <ul className="mt-1.5 grid gap-1">
            {path.approvalBlockers.map((b) => (
              <li key={b.key} className="flex items-baseline gap-2 text-[12.5px]">
                <span aria-hidden="true" className={cn('inline-block h-2 w-2 shrink-0 rounded-full', b.met ? 'bg-[#1f7a4d]' : 'border border-[var(--fm-ink3)]')} />
                <span>
                  {b.text.replace(/\.$/, '')}: <span className={cn('font-semibold', b.met ? 'text-[#1f7a4d]' : 'text-[#b4232c]')}>{b.met ? 'met' : 'not yet'}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {explain && (
        <div className="grid gap-1 border-t border-[var(--fm-line)] pt-3 text-[12px] text-[var(--fm-ink2)]">
          <p>
            {tierLine(explain)}{' '}
            <a href="#onboard" className="font-medium text-[var(--fm-ink)] underline-offset-2 hover:underline">{explain.tierSource ? 'Change' : 'Confirm'}</a>
          </p>
          {explain.tierNote && <p className={override?.pending ? 'text-[#a14d00]' : undefined}>{explain.tierNote}</p>}
        </div>
      )}
    </div>
  )
}
