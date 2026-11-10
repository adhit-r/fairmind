'use client'

import Link from 'next/link'
import { useState } from 'react'
import { ArrowUp, Sparkles } from 'lucide-react'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { useAIProvider, usePackActions, type AskAnswer } from '@/lib/api/hooks/usePacks'

type Turn = { question: string; answer?: AskAnswer; error?: string }

/** Ask FairMind: one question at a time about the estate, answered by the organisation's own model. */
export function AskPanel({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const provider = useAIProvider()
  const { ask } = usePackActions()
  const [turns, setTurns] = useState<Turn[]>([])
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const config = provider.data?.config
  const ready = !!config?.enabled

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    const question = draft.trim()
    if (!question || busy) return
    setDraft('')
    setBusy(true)
    setTurns((t) => [...t, { question }])
    const { data, error } = await ask(question)
    setTurns((t) => t.map((turn, i) => (i === t.length - 1 ? { ...turn, answer: data ?? undefined, error: error ?? undefined } : turn)))
    setBusy(false)
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex w-full flex-col gap-4 border-l border-[var(--fm-line)] bg-[var(--fm-bg)] p-5 text-[var(--fm-ink)] sm:max-w-[460px]">
        <SheetHeader className="space-y-1 text-left">
          <SheetTitle className="flex items-center gap-2 text-[15px] font-semibold tracking-[-0.01em] text-[var(--fm-ink)]">
            <Sparkles className="h-4 w-4 text-[var(--fm-brand)]" aria-hidden /> Ask FairMind
          </SheetTitle>
          <SheetDescription className="text-[12px] text-[var(--fm-ink3)]">
            {ready ? `Answers from your release gates and waiting runs, by ${config.providerName}` : 'Answers come from your organisation’s own AI provider'}
          </SheetDescription>
        </SheetHeader>

        <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto">
          {!provider.loading && !ready && (
            <div className="fm-card p-4 text-[13px] leading-relaxed text-[var(--fm-ink2)]">
              No AI provider is switched on for this organisation. An owner or admin can add one, with your own key, in{' '}
              <Link href="/org-admin/settings" className="font-semibold text-[var(--fm-ink)] underline underline-offset-2" onClick={() => onOpenChange(false)}>
                organisation settings
              </Link>
              .
            </div>
          )}
          {turns.map((t, i) => (
            <div key={i} className="flex flex-col gap-2">
              <div className="self-end rounded-[10px] border border-[var(--fm-line)] bg-white px-3 py-2 text-[13px]">{t.question}</div>
              {t.answer ? (
                <div className="fm-card flex flex-col gap-2.5 p-3.5 text-[13px] leading-relaxed text-[var(--fm-ink)]">
                  <p className="whitespace-pre-line">{t.answer.answer}</p>
                  {t.answer.systems.length > 0 && (
                    <div className="flex flex-col gap-1.5">
                      {t.answer.systems.map((s) => (
                        <Link
                          key={s.id}
                          href={`/systems/${encodeURIComponent(s.id)}`}
                          onClick={() => onOpenChange(false)}
                          className="flex items-center gap-2 rounded-[10px] border border-[var(--fm-line)] px-2.5 py-1.5 hover:border-[var(--fm-ink)]"
                        >
                          <b className="font-semibold">{s.name}</b>
                          <span className="ml-auto truncate text-[12px] text-[var(--fm-ink2)]">{s.reason}</span>
                        </Link>
                      ))}
                    </div>
                  )}
                  <small className="text-[11.5px] text-[var(--fm-ink3)]">
                    Read {t.answer.systemsRead} systems and {t.answer.runsRead} waiting runs · {t.answer.model}
                  </small>
                </div>
              ) : t.error ? (
                <div className="rounded-[10px] border border-red-200 bg-red-50 px-3 py-2 text-[12.5px] text-red-700">{t.error}</div>
              ) : (
                <div className="text-[12.5px] text-[var(--fm-ink3)]">Reading your estate…</div>
              )}
            </div>
          ))}
        </div>

        <form onSubmit={submit} className="flex items-center gap-2 rounded-full border border-[var(--fm-line)] bg-white py-1.5 pl-4 pr-1.5 focus-within:border-[var(--fm-ink)]">
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            disabled={!ready}
            maxLength={2000}
            aria-label="Question"
            placeholder={ready ? 'Which systems are blocked from release, and why?' : 'Add an AI provider to ask'}
            className="min-w-0 flex-1 bg-transparent text-[13px] outline-none placeholder:text-[var(--fm-ink3)]"
          />
          <button
            type="submit"
            disabled={!ready || busy || !draft.trim()}
            aria-label="Ask"
            className="grid h-7 w-7 flex-none place-items-center rounded-full bg-[var(--fm-ink)] text-white disabled:opacity-40"
          >
            <ArrowUp className="h-4 w-4" aria-hidden />
          </button>
        </form>
      </SheetContent>
    </Sheet>
  )
}
