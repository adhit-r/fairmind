'use client'

import Link from 'next/link'
import { Fragment, useState, type CSSProperties, type ReactNode } from 'react'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import type { GateCheck } from '@/lib/api/hooks/useSystemFile'
import { cn } from '@/lib/utils'

/** The state of one requirement or check for one system. */
export type CellState = 'proven' | 'estimated' | 'attested' | 'planned' | 'open' | 'fails' | 'stale' | 'atorg'
/** A state, a crosswalk relation strength (3 satisfies, 2 partially satisfies, 1 supports, 0 none), or blank. */
export type Cell = CellState | 0 | 1 | 2 | 3 | null
export type CellKind = '' | CellState | 'r1' | 'r2' | 'r3'
type Kind = Exclude<CellKind, ''>

/** `blank` says why a blank cell in this column is blank; it wins over the row's reason. */
export type MatrixCol = { key: string; label: string; title?: string; href?: string; off?: boolean; blank?: string }
/** `blank` says why a blank cell is blank: one reason for the row, or one per cell. */
export type MatrixRow = {
  key: string
  code?: string
  label: string
  title?: string
  href?: string
  cells: Cell[]
  blank?: string | Array<string | undefined>
  tail?: ReactNode[]
  count?: ReactNode
}
export type MatrixGroup = { label: string; rows: MatrixRow[] }
export type MatrixProps = {
  id: string
  head: string
  colGroups: { label: string; cols: MatrixCol[] }[]
  groups: MatrixGroup[]
  tail?: { key: string; label: string }[]
  countHead?: string
  more?: { n: number; href: string }
  onCell?: (rowKey: string, colKey: string) => void
  legendLabels?: Partial<Record<CellState, string>>
}

const ORDER: Kind[] = ['proven', 'estimated', 'attested', 'planned', 'open', 'fails', 'stale', 'atorg', 'r3', 'r2', 'r1']
export const KIND_LABEL: Record<Kind, string> = {
  proven: 'proven',
  estimated: 'estimated',
  attested: 'attested',
  planned: 'planned',
  open: 'open',
  fails: 'fails',
  stale: 'stale',
  atorg: 'at organisation',
  r3: 'satisfies',
  r2: 'partially satisfies',
  r1: 'supports',
}
/** What a cell means, for its title and the drawers. */
export const KIND_TITLE: Record<Kind, string> = {
  proven: 'Proven: measured evidence at 0.70 or above',
  estimated: 'Estimated: a tool estimate, or a measurement below 0.70',
  attested: 'Attested: a named person signed it',
  planned: 'Planned: no evidence yet',
  open: 'Open: nothing current on file',
  fails: 'Fails: measured, and it fails its threshold',
  stale: 'Stale: the evidence is older than its cadence',
  atorg: 'Held at organisation level',
  r3: 'Satisfies',
  r2: 'Partially satisfies',
  r1: 'Supports',
}

const CLASS_LABEL: Record<string, string> = { measured: 'Measured', tool_estimated: 'Tool estimate', manual: 'Manual statement' }
/** A provenance class for the drawers; the backend can send classes beyond the three it grades. */
export const classLabel = (cls: string) => CLASS_LABEL[cls] ?? (cls === 'unknown' ? 'Unclassified' : cls.charAt(0).toUpperCase() + cls.slice(1).replace(/_/g, ' '))

export const cellKind = (cell: Cell | undefined): CellKind =>
  typeof cell === 'number' ? (cell ? (`r${cell}` as CellKind) : '') : (cell ?? '')

/** The kinds present in the grid, in the fixed legend order. */
export function legendKeys(groups: MatrixGroup[]): Kind[] {
  const seen = new Set<CellKind>(groups.flatMap((g) => g.rows.flatMap((r) => r.cells.map(cellKind))))
  return ORDER.filter((k) => seen.has(k))
}

/** Group rows only earn their space when there are two or more non-empty groups. */
export const showGroupRows = (groups: MatrixGroup[]) => groups.filter((g) => g.rows.length > 0).length >= 2

/** One release check as a cell; the same mapping as the backend's clause_map_service.cell_state. */
export function checkCell(check: Pick<GateCheck, 'state' | 'evidenceClass' | 'stale' | 'fails'> & { detail?: GateCheck['detail'] }): CellState {
  const cls = check.evidenceClass
  const measured = cls === 'measured' || cls === 'tool_estimated'
  if (check.fails || (measured && check.detail?.all_checks_pass === false)) return 'fails'
  if (check.stale) return 'stale'
  if (check.state === 'open') return 'open'
  // A payload from before evidenceClass existed: its state is all there is.
  if (cls === undefined) return check.state
  if (cls === 'manual') return 'attested'
  if (cls === 'tool_estimated') return 'estimated'
  if (check.state === 'proven' && cls === 'measured') return 'proven'
  return 'estimated'
}

/**
 * Where each column-group label sits. A one-column group or the last group lets its label run past its columns (`ov`);
 * other labels clip to their colspan. One-column labels prefer the upper line and wider groups the lower one, and a
 * label never shares a line with the label right after an overflowing one, so adjacent narrow groups never collide.
 */
export function groupLabelLines(colGroups: { label: string; cols: unknown[] }[]) {
  const out: Array<{ ov: boolean; up: boolean }> = []
  colGroups.forEach((g, i) => {
    const one = g.cols.length === 1 && !!g.label
    const prev = out[i - 1]
    const up = prev?.ov && prev.up === one ? !one : one
    out.push({ ov: one || i === colGroups.length - 1, up })
  })
  return out
}

/** The one grid of the app: rows of requirements or systems against columns of systems, checks or controls. */
export function Matrix({ id, head, colGroups, groups, tail = [], countHead, more, onCell, legendLabels }: MatrixProps) {
  const [hover, setHover] = useState<number | null>(null)
  const cols = colGroups.flatMap((g) => g.cols)
  const starts = new Set<number>()
  colGroups.reduce((at, g) => (starts.add(at), at + g.cols.length), 0)
  const labels = groupLabelLines(colGroups)
  const legend = legendKeys(groups)
  const grouped = showGroupRows(groups)
  const span = 2 + cols.length + tail.length + (countHead ? 1 : 0)
  const vh = Math.min(120, Math.max(52, Math.ceil(Math.max(0, ...cols.map((c) => c.label.length)) * 6.6) + 16))
  const kindText = (k: Kind) => (k === 'atorg' && legendLabels?.atorg) || KIND_TITLE[k]
  const titleOf = (k: CellKind, c: MatrixCol, r: MatrixRow, j: number) =>
    `${c.title ?? c.label} · ${k ? kindText(k) : (c.blank ?? (Array.isArray(r.blank) ? r.blank[j] : r.blank) ?? 'Not applicable')}`
  const colCls = (c: MatrixCol, j: number) => cn(starts.has(j) && 'mx-gs', c.off && 'mx-off', hover === j && 'mx-hc')

  return (
    <div className="mx" data-mx={id}>
      {legend.length > 0 && (
        <div className="mx-legend">
          {legend.map((k) => (
            <span key={k}>
              <i aria-hidden className={`fm-cel ${k}`} />
              {(k !== 'r1' && k !== 'r2' && k !== 'r3' && legendLabels?.[k]) || KIND_LABEL[k]}
            </span>
          ))}
        </div>
      )}
      <div className="mx-wrap">
        <table className="mx-grid" style={{ '--mx-vh': `${vh}px` } as CSSProperties} onMouseLeave={() => setHover(null)}>
          <thead>
            {colGroups.some((g) => g.label) && (
              <tr className="mx-gh">
                <th className="mx-rq" />
                {colGroups.map((g, i) => (
                  <th key={i} colSpan={g.cols.length} className={cn('mx-gl', labels[i].ov && 'mx-ov', labels[i].up && 'mx-up')}>
                    <span title={g.label || undefined}>{g.label}</span>
                  </th>
                ))}
                <th colSpan={span - 1 - cols.length} />
              </tr>
            )}
            <tr>
              <th scope="col" className="mx-rq mx-hd">
                {head}
              </th>
              {cols.map((c, j) => (
                <th key={c.key} scope="col" className={cn('mx-ch', colCls(c, j))}>
                  {c.href ? (
                    <Link className="mx-vh" href={c.href} title={c.title ?? c.label}>
                      {c.label}
                    </Link>
                  ) : (
                    <span className="mx-vh" title={c.title ?? c.label}>
                      {c.label}
                    </span>
                  )}
                </th>
              ))}
              {tail.map((t) => (
                <th key={t.key} scope="col" className="mx-tl">
                  {t.label}
                </th>
              ))}
              {countHead && (
                <th scope="col" className="mx-cnt">
                  {countHead}
                </th>
              )}
              <th className="mx-fill" />
            </tr>
          </thead>
          <tbody>
            {groups
              .filter((g) => g.rows.length > 0)
              .map((g, gi) => (
                <Fragment key={`${gi}:${g.label}`}>
                  {grouped && (
                    <tr className="mx-grp">
                      <td colSpan={span}>
                        <span>{g.label}</span>
                      </td>
                    </tr>
                  )}
                  {g.rows.map((r) => {
                    const lab = (
                      <>
                        {r.code && <span className="mx-code">{r.code}</span>}
                        {r.label}
                      </>
                    )
                    return (
                      <tr key={r.key}>
                        <th scope="row" className="mx-rq" title={r.title ?? (r.code ? `${r.code} · ${r.label}` : r.label)}>
                          {r.href ? <Link href={r.href}>{lab}</Link> : lab}
                        </th>
                        {cols.map((c, j) => {
                          const k = cellKind(r.cells[j])
                          const t = titleOf(k, c, r, j)
                          return (
                            <td key={c.key} className={cn('mx-c', colCls(c, j))} title={k ? undefined : t} onMouseEnter={() => setHover(j)}>
                              {k &&
                                (onCell ? (
                                  <button type="button" className={`fm-cel ${k}`} title={t} aria-label={`${r.label}, ${t}`} onClick={() => onCell(r.key, c.key)} />
                                ) : (
                                  <i role="img" className={`fm-cel ${k}`} title={t} aria-label={t} />
                                ))}
                            </td>
                          )
                        })}
                        {tail.map((t, ti) => (
                          <td key={t.key} className="mx-tl">
                            {r.tail?.[ti]}
                          </td>
                        ))}
                        {countHead && <td className="mx-cnt">{r.count}</td>}
                        <td className="mx-fill" />
                      </tr>
                    )
                  })}
                </Fragment>
              ))}
          </tbody>
        </table>
      </div>
      {more && more.n > 0 && (
        <div className="mx-more">
          {more.n} more · <Link href={more.href} className="font-medium text-[var(--fm-ink)] underline-offset-2 hover:underline">Open the full grid</Link>
        </div>
      )}
    </div>
  )
}

/** The drawer a cell opens: a small label, the title, one line under it, then the detail blocks. */
export function CellDrawer({ open, onClose, label, title, sub, children }: { open: boolean; onClose: () => void; label: string; title: string; sub?: string; children: ReactNode }) {
  return (
    <Sheet open={open} onOpenChange={(o) => !o && onClose()}>
      <SheetContent className="flex w-full flex-col gap-5 overflow-y-auto border-l border-[var(--fm-line)] bg-white p-6 text-[var(--fm-ink)] sm:max-w-[440px]">
        <SheetHeader className="space-y-1 text-left">
          <span className="text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[var(--fm-ink3)]">{label}</span>
          <SheetTitle className="text-[17px] font-semibold leading-snug tracking-[-0.01em] text-[var(--fm-ink)]">{title}</SheetTitle>
          {sub ? <SheetDescription className="text-[12.5px] text-[var(--fm-ink3)]">{sub}</SheetDescription> : <SheetDescription className="sr-only">{title}</SheetDescription>}
        </SheetHeader>
        {children}
      </SheetContent>
    </Sheet>
  )
}

/** One labelled block inside a CellDrawer. */
export function DrawerBlock({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="grid gap-1.5 border-t border-[var(--fm-line)] pt-3 text-[13px]">
      <span className="text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[var(--fm-ink3)]">{label}</span>
      {children}
    </div>
  )
}

/** A cell swatch with its meaning, for drawers. */
export function CellMeaning({ cell, labels }: { cell: Cell; labels?: MatrixProps['legendLabels'] }) {
  const k = cellKind(cell)
  return (
    <span className="flex items-center gap-2">
      {k && <i aria-hidden className={`fm-cel ${k}`} />}
      {k ? (k === 'atorg' && labels?.atorg) || KIND_TITLE[k] : 'Blank'}
    </span>
  )
}
