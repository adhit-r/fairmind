'use client'

import NextLink from 'next/link'
import { useEffect, useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { Drawer } from '@astryxdesign/core/Drawer'
import { Switch } from '@astryxdesign/core/Switch'
import { Bot, Code2, LayoutGrid, Server, ShieldCheck, Sparkles, type LucideIcon } from 'lucide-react'
import { useAnnouncements, useWhatsNew, type Release } from '@/lib/api/hooks/useWhatsNew'

/** An icon for each area heading the release notes use; anything else gets the generic mark. */
const AREA_ICON: Array<[RegExp, LucideIcon]> = [
  [/agent|live run|shadow/i, Bot],
  [/assurance|audit|framework|compliance/i, ShieldCheck],
  [/developer|cli|sdk|api/i, Code2],
  [/operation|infra|deploy|dependenc/i, Server],
  [/app|interface/i, LayoutGrid],
]
const iconFor = (area: string) => AREA_ICON.find(([re]) => re.test(area))?.[1] ?? Sparkles
const MUTED = 'text-[var(--fm-ink2)]'
const CAP = 'text-[11px] font-medium uppercase tracking-wide text-[var(--fm-ink3)]'
const day = (iso: string | null) => (iso ? new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : '')

function ReleaseBody({ r, isNew, onNavigate }: { r: Release; isNew: boolean; onNavigate: () => void }) {
  const [all, setAll] = useState(false)
  const named = r.sections.map((s) => ({ ...s, items: all ? s.items : s.items.filter((i) => i.name).slice(0, 2) })).filter((s) => s.items.length)
  return (
    <div className="flex flex-col gap-2.5">
      <div className="flex flex-wrap items-baseline gap-2.5">
        <b className="text-[16px] font-semibold tracking-tight text-[var(--fm-ink)]">v{r.version}</b>
        <span className={`text-[12px] ${MUTED}`}>{day(r.publishedAt)}</span>
        {isNew && <span className="rounded-[5px] bg-[#ffe7dc] px-1.5 py-px text-[10.5px] font-semibold text-[var(--fm-ink)]">New for you</span>}
      </div>
      {r.title !== `FairMind ${r.tag}` && <p className="m-0 text-[14px] font-semibold text-[var(--fm-ink)]">{r.title}</p>}
      {r.lead && <p className={`m-0 text-[13px] ${MUTED}`}>{r.lead}</p>}
      {named.map((s) => {
        const Icon = iconFor(s.name)
        return (
          <div key={s.name} className="flex flex-col gap-2">
            <span className={`${CAP} mt-1`}>{s.name}</span>
            {s.items.map((i, k) => (
              <div key={k} className="grid grid-cols-[30px_minmax(0,1fr)_auto] items-start gap-2.5 rounded-[12px] border border-[var(--fm-line)] bg-white px-3 py-2.5">
                <span className="grid size-[30px] place-items-center rounded-[8px] bg-[var(--fm-bg)] text-[var(--fm-ink2)]"><Icon className="size-4" aria-hidden /></span>
                <div className="min-w-0">
                  {i.name && <b className="block text-[13px] font-semibold text-[var(--fm-ink)]">{i.name}</b>}
                  <span className={`block text-[12.5px] ${MUTED}`}>{i.text}</span>
                </div>
                {i.href && <NextLink href={i.href} onClick={onNavigate} className="whitespace-nowrap text-[12px] font-medium text-[var(--fm-ink)] underline underline-offset-2">Open</NextLink>}
              </div>
            ))}
          </div>
        )
      })}
      {!all && r.changes > named.reduce((a, s) => a + s.items.length, 0) && (
        <div><Button label={`All ${r.changes} changes in v${r.version}`} variant="secondary" size="sm" onClick={() => setAll(true)} /></div>
      )}
    </div>
  )
}

/** The sidebar's "What's new": marked until this person opens the latest release; opens the release notes beside the page. */
export function WhatsNewButton() {
  const wn = useWhatsNew()
  const [open, setOpen] = useState(false)
  const [older, setOlder] = useState<string | null>(null)
  const [failure, setFailure] = useState<string | null>(null)
  const releases = wn.data?.releases ?? []
  const latest = releases[0]

  useEffect(() => {
    // the release email's link (?whats-new=1) opens it; read here so the shell needs no Suspense boundary
    if (latest && new URLSearchParams(window.location.search).get('whats-new') === '1') setOpen(true)
  }, [latest])
  useEffect(() => {
    if (open && latest && wn.unread) void wn.markSeen(latest.tag)
  }, [open, latest, wn])

  if (!latest) return null
  return (
    <>
      <button type="button" onClick={() => setOpen(true)} className="fm-whatsnew" aria-label={wn.unread ? `What's new: v${latest.version}, not read yet` : "What's new"}>
        {wn.unread && <i aria-hidden />}
        <span>What&apos;s new</span>
        <small>v{latest.version}</small>
      </button>
      <Drawer isOpen={open} onOpenChange={setOpen} label="What's new" width={520} padding={5}>
        <div className="flex flex-col gap-4">
          <h2 className="m-0 text-lg font-semibold text-[var(--fm-ink)]">What&apos;s new</h2>
          <ReleaseBody r={latest} isNew={wn.unread} onNavigate={() => setOpen(false)} />
          {releases.slice(1, 6).map((r) =>
            older === r.tag ? (
              <ReleaseBody key={r.tag} r={r} isNew={false} onNavigate={() => setOpen(false)} />
            ) : (
              <button key={r.tag} type="button" onClick={() => setOlder(r.tag)}
                className="flex items-center justify-between gap-3 rounded-[10px] border border-[var(--fm-line)] bg-white px-3 py-2.5 text-left text-[13px]">
                <span><b className="font-semibold">v{r.version}</b> <span className={`text-[12px] ${MUTED}`}>{day(r.publishedAt)}</span></span>
                <span className={`truncate text-[12px] ${MUTED}`}>{r.title !== `FairMind ${r.tag}` ? r.title : r.sections.map((s) => s.name).join(', ')}</span>
              </button>
            ),
          )}
          <div className="rounded-[12px] bg-[var(--fm-bg)] px-3.5 py-3">
            <Switch
              label="Email me when there's a new release"
              description="A short note with the highlights. Turn it off here or from the email."
              value={wn.data?.emails ?? false}
              changeAction={async (on: boolean) => setFailure(await wn.setEmails(on))}
            />
          </div>
          {failure && <Banner status="error" title={failure} />}
          {latest.url && <a href={latest.url} target="_blank" rel="noreferrer" className={`text-[12px] ${MUTED} underline`}>Full notes on GitHub</a>}
        </div>
      </Drawer>
    </>
  )
}

/** Settings, for platform admins: email a release to the people who asked for release emails, once. */
export function ReleaseEmailsSection() {
  const a = useAnnouncements()
  const [busy, setBusy] = useState<string | null>(null)
  const [failure, setFailure] = useState<string | null>(null)
  if (a.error) return <Banner status="error" title={a.error} />
  if (!a.data) return null
  return (
    <div className="flex flex-col gap-3">
      <p className={`m-0 text-[13px] ${MUTED}`}>
        {a.data.optedIn === 0 ? 'Nobody has turned on release emails yet.' : `${a.data.optedIn} ${a.data.optedIn === 1 ? 'person has' : 'people have'} turned on release emails.`}
        {' '}Each release can be emailed once; a fixes-only release can be left unsent.
      </p>
      {a.data.releases.map((r) => (
        <div key={r.tag} className="flex flex-wrap items-center gap-3 rounded-[12px] border border-[var(--fm-line)] bg-white px-3.5 py-2.5">
          <div className="min-w-0 flex-1">
            <b className="text-[13px] font-semibold">v{r.version}</b> <span className={`text-[12.5px] ${MUTED}`}>{r.title}</span>
            <div className={`text-[12px] ${MUTED}`}>{day(r.publishedAt)}{r.sent ? `, emailed to ${r.sent.recipients} on ${day(r.sent.sent_at)} by ${r.sent.sent_by}` : ''}</div>
          </div>
          {!r.sent && (
            <Button label="Send" variant="secondary" size="sm" isLoading={busy === r.tag} isDisabled={busy !== null || a.data!.optedIn === 0}
              onClick={async () => {
                if (!window.confirm(`Email v${r.version} to ${a.data!.optedIn} ${a.data!.optedIn === 1 ? 'person' : 'people'}? It can only be sent once.`)) return
                setBusy(r.tag)
                setFailure(await a.announce(r.tag))
                setBusy(null)
              }} />
          )}
        </div>
      ))}
      {failure && <Banner status="error" title={failure} />}
    </div>
  )
}
