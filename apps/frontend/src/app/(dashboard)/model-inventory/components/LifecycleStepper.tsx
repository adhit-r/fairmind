'use client'

import { IconCheck, IconLock } from '@tabler/icons-react'

const STAGES = [
  { id: 'onboard', label: 'Registered' },
  { id: 'assess', label: 'Assessed' },
  { id: 'govern', label: 'Evidenced' },
  { id: 'remediate', label: 'Remediating' },
  { id: 'operate', label: 'Approved' },
] as const

type StageId = typeof STAGES[number]['id']

const STAGE_ORDER: Record<StageId, number> = {
  onboard: 0,
  assess: 1,
  govern: 2,
  remediate: 3,
  operate: 4,
}

interface LifecycleStepperProps {
  currentStage: string
  readiness: number
  compact?: boolean
}

export function LifecycleStepper({ currentStage, readiness, compact = false }: LifecycleStepperProps) {
  const currentOrder = STAGE_ORDER[currentStage as StageId] ?? 0

  if (compact) {
    const stage = STAGES.find((s) => s.id === currentStage) ?? STAGES[0]
    return (
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1">
          {STAGES.map((s, i) => {
            const isComplete = i < currentOrder
            const isCurrent = s.id === currentStage
            return (
              <div
                key={s.id}
                className={`h-2 w-2 rounded-full ${
                  isComplete ? 'bg-emerald-500' :
                  isCurrent ? 'bg-black' :
                  'bg-slate-200'
                }`}
              />
            )
          })}
        </div>
        <span className="text-xs font-bold uppercase">{stage.label}</span>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
          Governance lifecycle
        </p>
        <span className="text-xs font-bold text-muted-foreground">{readiness}% ready</span>
      </div>
      <div className="flex items-center gap-0">
        {STAGES.map((stage, idx) => {
          const isComplete = idx < currentOrder
          const isCurrent = stage.id === currentStage
          const isFuture = idx > currentOrder

          return (
            <div key={stage.id} className="flex flex-1 items-center">
              <div className="relative flex flex-col items-center">
                <div
                  className={`flex h-7 w-7 items-center justify-center rounded-full border-2 font-bold transition-colors ${
                    isComplete
                      ? 'border-emerald-600 bg-emerald-600 text-white'
                      : isCurrent
                        ? 'border-black bg-black text-white'
                        : 'border-black/20 bg-white text-muted-foreground'
                  }`}
                >
                  {isComplete ? (
                    <IconCheck className="h-3.5 w-3.5" />
                  ) : isFuture ? (
                    <IconLock className="h-3 w-3" />
                  ) : (
                    <span className="text-[10px]">{idx + 1}</span>
                  )}
                </div>
                <span className={`mt-1 whitespace-nowrap text-[10px] font-bold ${isCurrent ? 'text-black' : isFuture ? 'text-muted-foreground' : 'text-emerald-700'}`}>
                  {stage.label}
                </span>
              </div>
              {idx < STAGES.length - 1 && (
                <div className={`h-0.5 flex-1 ${isComplete ? 'bg-emerald-500' : 'bg-black/15'}`} />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
