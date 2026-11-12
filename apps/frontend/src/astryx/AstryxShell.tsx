'use client'

import '@astryxdesign/core/reset.css'
import './shell.css'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useMemo, useState } from 'react'
import { Search } from 'lucide-react'
import { Theme } from '@astryxdesign/core/theme'
import { LinkProvider } from '@astryxdesign/core/Link'
import { Button } from '@astryxdesign/core/Button'
import { CommandPalette } from '@astryxdesign/core/CommandPalette'
import { Heading, Text } from '@astryxdesign/core/Text'
import { Item } from '@astryxdesign/core/Item'
import { Avatar } from '@astryxdesign/core/Avatar'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { Layout, LayoutContent, LayoutPanel } from '@astryxdesign/core/Layout'
import { createStaticSource } from '@astryxdesign/core/Typeahead'
import { useMediaQuery } from '@astryxdesign/core/hooks'
import { useOrg } from '@/context/OrgContext'
import { useSession } from '@/context/SessionContext'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { useAIProvider, useRuns } from '@/lib/api/hooks/usePacks'
import { useNeedsYou } from './data/needsYou'
import { useIntegrations } from '@/lib/api/hooks/useIntegrations'
import { useRisks } from '@/lib/api/hooks/useRisks'
import { fairmindTheme } from './theme'
import { ALL, NAV, SETTINGS, groupOf, isOn, type Place } from './nav'

/** Live counts for the menu, read from the API. A count the API cannot give is left out, never guessed. */
function useNavCounts(): Partial<Record<NonNullable<Place['count']>, number>> {
  const { systems } = useSystemContext()
  const needsYou = useNeedsYou()
  const runs = useRuns().data ?? []
  const { discovered, loading: discoveryLoading } = useIntegrations()
  const { summary: risks } = useRisks()
  return {
    // The same list the Needs you page shows, so the badge and the page agree.
    ...(needsYou.loading ? {} : { needs: needsYou.items.length }),
    systems: systems.length,
    runs: runs.filter((r) => r.status === 'running' || r.status === 'queued').length,
    ...(discoveryLoading ? {} : { found: discovered.length }),
    ...(risks ? { findings: risks.open } : {}),
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

/**
 * Everything in the menu belongs to an organisation. When the person has none, or the list could not load,
 * one page says so and what to do, instead of every page failing with its own error.
 */
function NoOrganisation() {
  const { error, refreshOrgs } = useOrg()
  const { user } = useSession()
  if (error) {
    return (
      <div className="fm-page">
        <EmptyState
          title="Your organisations could not load"
          description={`FairMind could not read which organisations you belong to (${error}). Check your connection and try again.`}
          actions={<Button label="Try again" onClick={() => void refreshOrgs()} />}
        />
      </div>
    )
  }
  return (
    <div className="fm-page">
      <EmptyState
        title="You are not in an organisation yet"
        description="AI systems, rules and records all belong to an organisation. Ask an owner of your organisation to invite you; the invitation link brings you straight in."
        actions={user?.role === 'admin' ? <Button label="Review access requests" href="/admin/registrations" /> : undefined}
      />
    </div>
  )
}

/** Platform admin pages work without an organisation. */
const WITHOUT_ORG = /^\/admin(\/|$)/

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

function SignOut() {
  const { user, logout } = useSession()
  const router = useRouter()
  if (!user) return null
  return <Button label="Sign out" variant="ghost" size="sm" onClick={() => logout().finally(() => router.push('/login'))} />
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
  const { selectedOrg, isLoading: orgLoading } = useOrg()
  const [isPaletteOpen, setPaletteOpen] = useState(false)
  const isPhone = useMediaQuery('(max-width: 767px)')
  const group = groupOf(pathname) ?? (pathname.startsWith('/systems') || pathname === '/onboard' ? NAV[1] : null)

  // Each page's title names it, so tabs, history and screen readers can tell pages apart.
  const systemId = pathname.match(/^\/systems\/([^/]+)$/)?.[1]
  const pageName = systemId
    ? systems.find((s) => s.id === decodeURIComponent(systemId))?.name ?? 'AI system'
    : ALL.find((p) => isOn(pathname, p))?.label ?? null
  useEffect(() => {
    document.title = pageName ? `${pageName} | FairMind` : 'FairMind'
  }, [pageName])

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

  const places = group?.places.map((p) => ({ ...p, n: p.count ? counts[p.count] : undefined }))

  // The panel is always there, so the organisation, search, the agents' line and sign out are reachable from every page;
  // a page outside the menu groups simply has no list of places.
  const panel = (
    <nav className="fm-panel" aria-label={group?.title ?? 'FairMind'}>
      <OrgName />
      <Button label="Search or ask" icon={<Search size={16} />} width="100%" onClick={() => setPaletteOpen(true)} />
      {group && <div className="fm-list">
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
              href={p.href}
              isSelected={isOn(pathname, p)}
            />
          )
        })}
      </div>}
      <AgentLine />
      <Me />
    </nav>
  )

  return (
    <Theme theme={fairmindTheme} mode="light">
      {/* Every Astryx link and button with an href navigates with Next's router. */}
      <LinkProvider component={Link}>
      <div className="fm-app">
        <a className="fm-skip" href="#fm-main">Skip to content</a>
        <Layout
          height="fill"
          header={
            isPhone ? (
              <header className="fm-phone">
                <div className="fm-phone-top">
                  <Link className="fm-brand" href="/dashboard" aria-label="FairMind home">
                    <img src="/logo.png" alt="" />
                  </Link>
                  <OrgName />
                  <span className="fm-grow" />
                  <Button label="Search" icon={<Search size={16} />} isIconOnly variant="ghost" onClick={() => setPaletteOpen(true)} />
                  <Link className="fm-chip" href={SETTINGS.href} aria-current={isOn(pathname, SETTINGS) ? 'page' : undefined}>
                    Settings
                  </Link>
                  <SignOut />
                </div>
                <nav className="fm-chips" aria-label="Sections">
                  {NAV.map((g) => (
                    <Link key={g.key} className="fm-chip" href={g.places[0].href} aria-current={group === g ? 'true' : undefined}>
                      {g.short}
                    </Link>
                  ))}
                </nav>
                {places && places.length > 1 && (
                  <nav className="fm-chips sub" aria-label={group?.title}>
                    {places.map((p) => (
                      <Link key={p.href} className="fm-chip" href={p.href} aria-current={isOn(pathname, p) ? 'page' : undefined}>
                        {p.label}
                        {p.n != null && <b>{p.n}</b>}
                      </Link>
                    ))}
                  </nav>
                )}
              </header>
            ) : undefined
          }
          start={
            isPhone ? undefined : (
              <>
                <LayoutPanel width={78} padding={0}>
                  {strip}
                </LayoutPanel>
                <LayoutPanel width={228} padding={0}>
                  {panel}
                </LayoutPanel>
              </>
            )
          }
          content={
            <LayoutContent padding={0}>
              <main id="fm-main" tabIndex={-1} className="fm-main">
                {!orgLoading && !selectedOrg && !WITHOUT_ORG.test(pathname) ? <NoOrganisation /> : children}
              </main>
            </LayoutContent>
          }
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
      </LinkProvider>
    </Theme>
  )
}
