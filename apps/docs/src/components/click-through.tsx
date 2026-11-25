'use client'
import { useEffect, useRef, useState } from 'react'
import type { Demo } from './media'

export function ClickThrough({ base, demo }: { base: string; demo: Demo }) {
  const [i, setI] = useState(0)
  const hotspot = useRef<HTMLButtonElement>(null)
  const next = useRef<HTMLButtonElement>(null)
  const done = i >= demo.steps.length
  const step = demo.steps[i]
  const pct = (v: number, of: number) => `${(v / of) * 100}%`

  // Move focus with the steps so the demo can be used from the keyboard and a screen reader follows it.
  const started = useRef(false)
  useEffect(() => {
    if (!started.current) { started.current = true; return }
    ;(hotspot.current ?? next.current)?.focus()
  }, [i])

  return (
    <div className="fm-click">
      <div className="stage" style={{ aspectRatio: `${demo.width} / ${demo.height}` }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={`${base}/${done ? demo.end : step!.image}`}
          alt={done ? `${demo.title}: done` : `Step ${i + 1} of ${demo.steps.length}: ${step!.text}`}
          className="shot"
          width={demo.width}
          height={demo.height}
        />
        {!done && step!.box && (
          <button
            ref={hotspot}
            type="button"
            onClick={() => setI(i + 1)}
            aria-label={`Step ${i + 1} of ${demo.steps.length}: ${step!.text} Activate to continue.`}
            className="fm-hotspot spot"
            style={{
              left: pct(step!.box.x - 4, demo.width), top: pct(step!.box.y - 4, demo.height),
              width: pct(step!.box.w + 8, demo.width), height: pct(step!.box.h + 8, demo.height),
            }}
          />
        )}
      </div>
      <div className="bar">
        <span className="count">
          {done ? 'Done' : `Step ${i + 1} / ${demo.steps.length}`}
        </span>
        <p className="say">{done ? `${demo.title}. That's the whole flow.` : step!.text}</p>
        <div className="btns">
          <button type="button" className="btn" onClick={() => setI(Math.max(0, i - 1))} disabled={i === 0}>
            Back
          </button>
          {done ? (
            <button ref={next} type="button" className="btn primary" onClick={() => setI(0)}>
              Start again
            </button>
          ) : !step!.box ? (
            <button ref={next} type="button" className="btn primary" onClick={() => setI(i + 1)}>
              Next
            </button>
          ) : (
            <span className="hint">Click the highlighted control</span>
          )}
        </div>
      </div>
    </div>
  )
}
