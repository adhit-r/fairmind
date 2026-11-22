'use client'

import { useState } from 'react'
import { Button } from '@astryxdesign/core/Button'
import { usePackActions, type AskAnswer } from '@/lib/api/hooks/usePacks'
import type { Briefing as BriefingModel } from './types'
import { when } from './parts'

const SUGGESTED = ['What blocks the audit?', 'Which proof is out of date?', 'What changed since the last report?']

export function Briefing({ briefing, generatedAt }: { briefing: BriefingModel; generatedAt: string }) {
  const { ask } = usePackActions()
  const [q, setQ] = useState('')
  const [busy, setBusy] = useState(false)
  const [answer, setAnswer] = useState<{ q: string; res: AskAnswer | null; error: string | null } | null>(null)

  const run = async (question: string) => {
    const text = question.trim()
    if (!text || busy) return
    setBusy(true)
    const r = await ask(text)
    setAnswer({ q: text, res: r.data, error: r.error })
    setBusy(false)
  }

  return (
    <section className="fm-card rp-card rp-c12" aria-label="Briefing">
      <div className="rp-brief">
        <div>
          <div className="rp-who">
            <i aria-hidden="true" />
            {briefing.source === 'model' ? 'Worded by your AI provider' : 'Written from the record'} · {when(generatedAt)}
          </div>
          <p className="rp-say">
            {briefing.parts.map((p, i) =>
              'text' in p ? (
                <span key={i}>{p.text}</span>
              ) : (
                <span key={i} className={`rp-cite ${p.tone}`} title={p.note} aria-label={`${p.fact}: ${p.value}. ${p.note}`}>
                  {p.value}
                </span>
              ),
            )}
          </p>
        </div>
        <div className="rp-ask">
          <form
            className="rp-askbox"
            onSubmit={(e) => {
              e.preventDefault()
              void run(q)
            }}
          >
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ask this report" aria-label="Ask this report" />
            <Button label={busy ? 'Asking' : 'Ask'} variant="primary" size="sm" type="submit" isDisabled={busy || !q.trim()} />
          </form>
          <div className="rp-sugg">
            {SUGGESTED.map((s) => (
              <button key={s} type="button" disabled={busy} onClick={() => { setQ(s); void run(s) }}>
                {s}
              </button>
            ))}
          </div>
          {answer ? (
            <div className="rp-answer" role="status">
              <b>{answer.q}</b>
              {answer.error ? <div className="rp-err">{answer.error}</div> : <div>{answer.res?.answer}</div>}
              {answer.res?.systems?.length ? (
                <div className="rp-src">
                  {answer.res.systems.map((s) => (
                    <span key={s.id}>{s.name}</span>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </section>
  )
}
