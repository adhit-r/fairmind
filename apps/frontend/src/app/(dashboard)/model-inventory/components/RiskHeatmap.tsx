'use client'

import type { GovernanceRisk } from '@/lib/api/hooks/useModelInventory'

interface RiskHeatmapProps {
  risks: GovernanceRisk[]
}

const IMPACT_LABELS = ['Critical', 'High', 'Medium', 'Low']
const LIKELIHOOD_LABELS = ['Rare', 'Unlikely', 'Possible', 'Likely', 'Almost\nCertain']

const SEVERITY_TO_IMPACT: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
}

const LIKELIHOOD_TO_COL: Record<string, number> = {
  rare: 0,
  unlikely: 1,
  possible: 2,
  likely: 3,
  almost_certain: 4,
  high: 3,
  medium: 2,
  low: 1,
}

function getCellColor(row: number, col: number) {
  const score = (3 - row) * (col + 1)
  if (score >= 12) return 'bg-red-600 text-white'
  if (score >= 8) return 'bg-orange-400 text-white'
  if (score >= 4) return 'bg-amber-300 text-black'
  return 'bg-emerald-100 text-black'
}

export function RiskHeatmap({ risks }: RiskHeatmapProps) {
  // Build a 4×5 matrix of risk counts
  const matrix: number[][] = Array.from({ length: 4 }, () => Array(5).fill(0))

  for (const risk of risks) {
    const row = SEVERITY_TO_IMPACT[risk.severity] ?? 2
    const col = LIKELIHOOD_TO_COL[risk.likelihood?.toLowerCase() ?? 'possible'] ?? 2
    matrix[row][col]++
  }

  return (
    <div className="space-y-3">
      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
        Risk matrix — likelihood × impact
      </p>
      <div className="overflow-x-auto">
        <div className="min-w-[320px]">
          {/* Likelihood labels */}
          <div className="mb-1 ml-16 grid grid-cols-5 gap-1">
            {LIKELIHOOD_LABELS.map((l, i) => (
              <div key={i} className="text-center text-[9px] font-bold uppercase leading-tight text-muted-foreground">
                {l}
              </div>
            ))}
          </div>
          {/* Matrix rows */}
          {IMPACT_LABELS.map((impact, row) => (
            <div key={impact} className="mb-1 flex items-center gap-1">
              <div className="w-14 shrink-0 text-right text-[9px] font-bold uppercase leading-tight text-muted-foreground">
                {impact}
              </div>
              <div className="grid flex-1 grid-cols-5 gap-1">
                {Array.from({ length: 5 }, (_, col) => (
                  <div
                    key={col}
                    className={`flex h-8 items-center justify-center rounded border border-black/10 text-xs font-black ${getCellColor(row, col)}`}
                  >
                    {matrix[row][col] > 0 ? matrix[row][col] : ''}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
