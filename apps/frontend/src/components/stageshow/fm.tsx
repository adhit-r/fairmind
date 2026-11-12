'use client'

import type { CSSProperties, ReactNode } from 'react'
import { Text } from './kit'

import './fm.css'

// FairMind's own vocabulary, shared by every FairMind demo: the lifecycle-shell
// look (fm.css maps --fm-* onto the kit's tokens), the grid cell from
// components/ui/matrix.tsx, the five release checks and the rail.

export type CellState = 'proven' | 'estimated' | 'attested' | 'planned' | 'open' | 'fails' | 'stale' | 'none'

/** One cell of the Matrix: ink for proof, brand orange only for open. */
export function Cell({ state, style, ...rest }: { state: CellState; style?: CSSProperties } & Record<`data-${string}`, unknown>) {
  return <span className="fm-cel" data-state={state} style={style} {...rest} />
}

/** The five checks of the release gate, in the order the app shows them. */
export const CHECKS = ['Fairness', 'Data governance', 'Human oversight', 'Monitoring', 'Environmental']

/** The app's menu groups, in the order a system moves through them: found, planned, tested, released, on record. */
export const STAGES = ['Inventory', 'Rules', 'Testing', 'Release', 'Records']
const LIBRARY = ['Home', 'Agents', 'Settings']

/** The rail of the app: the five stages, then the library; `at` lights one stage. */
export function Rail({ at, labels = true, library = true }: { at: number; labels?: boolean; library?: boolean }) {
  return (
    <nav className="fm-rail">
      {STAGES.map((s, i) => (
        <div key={s} className="fm-rail__item" data-on={i === at || undefined}>
          <span className="fm-rail__num">0{i + 1}</span>
          {labels && <span className="fm-rail__label">{s}</span>}
        </div>
      ))}
      {library && (
        <>
          <div className="fm-rail__group fm-label">More</div>
          {LIBRARY.map((s) => (
            <div key={s} className="fm-rail__item">
              <span className="fm-rail__num" />
              {labels && <Text filler className="fm-rail__label">{s}</Text>}
            </div>
          ))}
        </>
      )}
    </nav>
  )
}

/**
 * Frames a demo in the app: the picture is decorative, so it is hidden from
 * assistive tech and described once by `label`; the caption marks it as an
 * example, since its rows are illustrative, not the organisation's data.
 */
export function Illustration({ label, children, className, captionFirst }: { label: string; children: ReactNode; className?: string; captionFirst?: boolean }) {
  const caption = (
    <figcaption className={captionFirst ? 'mb-3 pl-14 text-[11px] font-medium text-[var(--fm-ink3)]' : 'mt-2 text-center text-[11px] font-medium text-[var(--fm-ink3)]'}>
      Example
    </figcaption>
  )
  return (
    <figure className={className} aria-label={label} role="img" style={{ margin: 0 }}>
      {captionFirst && caption}
      <div aria-hidden>{children}</div>
      {!captionFirst && caption}
    </figure>
  )
}
