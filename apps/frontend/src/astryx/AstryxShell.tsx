'use client'

import '@astryxdesign/core/reset.css'
import './shell.css'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useMemo, useState } from 'react'
import { Search } from 'lucide-react'
import { Theme } from '@astryxdesign/core/theme'
import { Button } from '@astryxdesign/core/Button'
import { CommandPalette } from '@astryxdesign/core/CommandPalette'
import { Heading, Text } from '@astryxdesign/core/Text'
import { Item } from '@astryxdesign/core/Item'
import { Avatar } from '@astryxdesign/core/Avatar'
import { Layout, LayoutContent, LayoutPanel } from '@astryxdesign/core/Layout'
import { createStaticSource } from '@astryxdesign/core/Typeahead'
import { useOrg } from '@/context/OrgContext'
import { useSession } from '@/context/SessionContext'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { usePendingDecisions } from '@/lib/api/hooks/usePendingDecisions'
import { useAIProvider, useRuns, useWaitingRuns } from '@/lib/api/hooks/usePacks'
import { fairmindTheme } from './theme'
import { ALL, NAV, SETTINGS, groupOf, isOn, type Place } from './nav'

/** Live counts for the menu, read from the API. A count the API cannot give is left out, never guessed. */
function useNavCounts(): Partial<Record<NonNullable<Place['count']>, number>> {
  const { systems } = useSystemContext()
  const { requests } = usePendingDecisions()
  const waiting = useWaitingRuns().data ?? []
  const runs = useRuns().data ?? []
  // Approval requests are not org-scoped yet; count only those for systems in this estate.
  const mine = requests.filter((r) => systems.some((s) => s.id === r.entity_id))
  return {
    needs: mine.length + waiting.length,
    systems: systems.length,
    runs: runs.filter((r) => r.status === 'running' || r.status === 'queued').length,
  }
}

const HOT: Array<NonNullable<Place['count']>> = ['needs', 'found', 'findings']

function OrgName() {
  const { organizations, selectedOrg, selectOrg } = useOrg()
  if (!selectedOrg) return null
  return (
    <div className="fm-org">
      {organizations.length > 1 ? (
        <select aria-label="Organisation" value={selectedOrg.id} onChange={(e) => selectOrg(e.target.value)}>
          {organizations.map((o) => (
            <option key={o.id} value={o.id}>
              {o.name}
            </option>
          ))}
        </select>
      ) : (
        <Text weight="semibold">{selectedOrg.name}</Text>
      )}
      <Text type="supporting" color="secondary">
        {selectedOrg.role}
      </Text>
    </div>
  )
}

/** What the organisation's agents are doing now, from the run list. */
function AgentLine() {
  const runs = useRuns().data ?? []
  const config = useAIProvider().data?.config
  const active = runs.filter((r) => r.status === 'running' || r.status === 'queued')
  return (
    <Link href="/autopilot" className="fm-feed">
      <span className="who">
        <i className={active.length ? 'on' : undefined} aria-hidden />
        {active.length ? `${active.length} agent run${active.length === 1 ? '' : 's'} active` : 'Agents idle'}
      </span>
      <span className="doing">{config?.enabled ? `Using ${config.providerName}` : 'No AI provider set, rules only'}</span>
    </Link>
  )
}

function Me() {
  const { user, logout } = useSession()
  const router = useRouter()
  if (!user) return null
  const name = user.username || user.email
  return (
    <div className="fm-me">
      <Avatar name={name} size="sm" />
      <span>
        <Text weight="semibold" maxLines={1}>
          {name}
        </Text>
        <Text type="supporting" color="secondary" maxLines={1}>
          {user.role ?? user.email}
        </Text>
      </span>
      <Button label="Sign out" variant="ghost" size="sm" onClick={() => logout().finally(() => router.push('/login'))} />
    </div>
  )
}

export function AstryxShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() ?? '/dashboard'
  const router = useRouter()
  const counts = useNavCounts()
  const { systems } = useSystemContext()
  const [isPaletteOpen, setPaletteOpen] = useState(false)
  const group = groupOf(pathname) ?? (pathname.startsWith('/systems') ? NAV[1] : null)

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setPaletteOpen(true)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  // Search covers every page and every system in the estate.
  const source = useMemo(
    () =>
      createStaticSource([
        ...ALL.map((p) => ({ id: p.href, label: p.label })),
        ...systems.map((s) => ({ id: `/systems/${encodeURIComponent(s.id)}`, label: s.name })),
      ]),
    [systems],
  )

  const SettingsIcon = SETTINGS.icon
  const strip = (
    <nav className="fm-strip" aria-label="Sections">
      <Link className="fm-brand" href="/dashboard" aria-label="FairMind home">
        <img src="/logo.png" alt="" />
      </Link>
      {NAV.map((g) => {
        const Icon = g.icon
        const hot = g.places.some((p) => p.count && HOT.includes(p.count) && (counts[p.count] ?? 0) > 0)
        return (
          <Link key={g.key} href={g.places[0].href} className="fm-sb" aria-current={group === g ? 'true' : undefined}>
            <span className="ic">
              <Icon size={20} aria-hidden />
            </span>
            {g.short}
            {hot && <span className="hot" aria-label="Needs a person" />}
          </Link>
        )
      })}
      <span className="fm-grow" />
      <Link href={SETTINGS.href} className="fm-sb" aria-current={isOn(pathname, SETTINGS) ? 'true' : undefined}>
        <span className="ic">
          <SettingsIcon size={20} aria-hidden />
        </span>
        Settings
      </Link>
    </nav>
  )

  const panel = group && (
    <nav className="fm-panel" aria-label={group.title}>
      <OrgName />
      <Button label="Search or ask" icon={<Search size={16} />} width="100%" onClick={() => setPaletteOpen(true)} />
      <div className="fm-list">
        <div className="fm-group-title">
          <Heading level={2}>{group.title}</Heading>
        </div>
        {group.places.map((p) => {
          const Icon = p.icon
          const n = p.count ? counts[p.count] : undefined
          const hot = !!p.count && HOT.includes(p.count) && (n ?? 0) > 0
          return (
            <Item
              key={p.href}
              label={p.label}
              startContent={<Icon size={18} aria-hidden />}
              endContent={
                n != null ? (
                  <Text size="sm" weight="semibold" hasTabularNumbers color="secondary" className={hot ? 'fm-hot-count' : undefined}>
                    {n}
                  </Text>
                ) : undefined
              }
              onClick={() => router.push(p.href)}
              isSelected={isOn(pathname, p)}
            />
          )
        })}
      </div>
      <AgentLine />
      <Me />
    </nav>
  )

  return (
    <Theme theme={fairmindTheme} mode="light">
      <div className="fm-app">
        <Layout
          height="fill"
          start={
            <>
              <LayoutPanel width={78} padding={0}>
                {strip}
              </LayoutPanel>
              {panel && (
                <LayoutPanel width={228} padding={0}>
                  {panel}
                </LayoutPanel>
              )}
            </>
          }
          content={<LayoutContent padding={0}>{children}</LayoutContent>}
        />
      </div>
      <CommandPalette
        isOpen={isPaletteOpen}
        onOpenChange={setPaletteOpen}
        searchSource={source}
        label="Search FairMind"
        onValueChange={(v: unknown) => {
          const id = typeof v === 'string' ? v : (v as { id?: string } | null)?.id
          if (id) router.push(id)
          setPaletteOpen(false)
        }}
      />
    </Theme>
  )
}
