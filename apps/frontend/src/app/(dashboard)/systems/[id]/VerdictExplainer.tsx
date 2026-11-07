'use client'

import type { GateCheck, ReleaseGate } from '@/lib/api/hooks/useSystemFile'

const VERDICT_LABEL: Record<string, string> = { go: 'Go', conditional_go: 'Conditional go', no_go: 'No go' }

/** Placeholder with the agreed signature so FairnessRunPanel typechecks; the verdict builder's file replaces it. */
export function VerdictExplainer({ gate }: { gate: ReleaseGate; compact?: boolean; onAttest?: (check: GateCheck['key']) => void }) {
  return <div className="text-[13px] font-semibold">Release gate after this run: {VERDICT_LABEL[gate.verdict] ?? gate.verdict}</div>
}
