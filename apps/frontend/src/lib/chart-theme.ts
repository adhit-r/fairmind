/**
 * Chart theme: every colour comes from the design-token CSS variables in
 * globals.css, so charts follow light/dark mode. Never use recharts defaults or
 * hardcoded hex values in chart components.
 */
export const CHART_SERIES = [
  'var(--chart-1)',
  'var(--chart-2)',
  'var(--chart-3)',
  'var(--chart-4)',
  'var(--chart-5)',
  'var(--chart-6)',
] as const

/** Series colour by index (wraps around after six series). */
export function seriesColor(index: number): string {
  return CHART_SERIES[((index % CHART_SERIES.length) + CHART_SERIES.length) % CHART_SERIES.length]
}

/** Semantic colours for charts that encode status (always pair with labels/legend, never colour alone). */
export const CHART_TONES = {
  neutral: 'var(--chart-5)',
  info: 'var(--info)',
  success: 'var(--success)',
  warning: 'var(--warning)',
  critical: 'var(--destructive)',
  attention: 'var(--accent-action)',
} as const

export const chartTheme = {
  grid: 'var(--chart-grid)',
  axis: 'var(--chart-axis)',
  text: 'var(--foreground)',
  mutedText: 'var(--muted-foreground)',
  surface: 'var(--popover)',
  border: 'var(--border)',
  /** Spread onto <XAxis>/<YAxis>. */
  axisProps: {
    stroke: 'var(--chart-axis)',
    tick: { fill: 'var(--chart-axis)', fontSize: 12 },
    tickLine: false,
    axisLine: { stroke: 'var(--chart-grid)' },
  },
  /** Spread onto <CartesianGrid>. */
  gridProps: {
    stroke: 'var(--chart-grid)',
    strokeDasharray: '3 3',
    vertical: false,
  },
  /** Spread onto <Tooltip>. */
  tooltipProps: {
    contentStyle: {
      border: '1px solid var(--border)',
      borderRadius: 6,
      backgroundColor: 'var(--popover)',
      color: 'var(--popover-foreground)',
      fontSize: 12,
      boxShadow: 'none',
    },
    labelStyle: { color: 'var(--popover-foreground)', fontWeight: 600 },
    itemStyle: { color: 'var(--popover-foreground)' },
    cursor: { fill: 'var(--muted)', fillOpacity: 0.6 },
  },
  /** Spread onto <Legend>. */
  legendProps: {
    wrapperStyle: { fontSize: 12, color: 'var(--muted-foreground)' },
  },
} as const
