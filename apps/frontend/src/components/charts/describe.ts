/**
 * A sentence a screen reader reads in place of a chart: its title and the
 * plotted values, up to `max` points (WCAG 1.1.1).
 */
export function describeChart(title: string, points: Array<[string, number | string]>, max = 12): string {
  if (!points.length) return `${title}: no data`
  const shown = points.slice(0, max).map(([label, value]) => `${label} ${value}`).join(', ')
  const more = points.length > max ? `, and ${points.length - max} more` : ''
  return `${title}: ${shown}${more}`
}
