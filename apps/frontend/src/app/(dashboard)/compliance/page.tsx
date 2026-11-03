'use client'

import Link from 'next/link'
import { useMemo, useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  useBundles,
  useCatalogue,
  useInstaller,
  useJourneys,
  usePacks,
  type Bundle,
  type JourneySummary,
  type Pack,
} from '@/lib/api/hooks/usePacks'
import { IsoFigure } from '@/components/packs/IsoFigure'
import { packsFigure } from '@/components/packs/figures'
import { BTN, BTN_P, CoverageBar, Empty, ErrorNote, Heading, Loading, MUTED, Pill, cap } from '@/components/packs/parts'

const ALL = 'ALL'
const TAB = 'inline-flex h-10 items-center rounded-full border border-[#15171a24] bg-white px-[18px] text-[13px] font-semibold text-[var(--fm-ink,#15171a)] hover:bg-[#f4f4f2] data-[state=active]:border-[#15171a] data-[state=active]:bg-[#15171a] data-[state=active]:text-white'

const plural = (n: number, one: string, many = `${one}s`) => `${n} ${n === 1 ? one : many}`

function PackCard({ pack, pillarName, busy, onToggle }: { pack: Pack; pillarName?: string; busy: string | null; onToggle: (remove: boolean) => void }) {
  return (
    <article className="pk-card flex flex-col gap-2.5 p-5">
      <div className="flex flex-wrap items-center gap-2">
        {pack.installed && <Pill tone="done">Installed</Pill>}
        {pack.agentic && <Pill tone="you">Agentic</Pill>}
        {pillarName && <Pill>{pillarName}</Pill>}
      </div>
      <Link href={`/compliance/packs/${pack.id}`} className="text-[15px] font-semibold hover:underline">
        {pack.name}
      </Link>
      <p className={`m-0 flex-grow text-[13px] leading-normal ${MUTED}`}>{pack.description}</p>
      <p className={`m-0 text-[12.5px] ${MUTED}`}>
        {plural(pack.patterns.length, 'pattern')}, {plural(pack.workflowCount, 'workflow')}, {plural(pack.evaluationCount, 'evaluation')}
      </p>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          className={pack.installed ? BTN : BTN_P}
          disabled={busy !== null}
          onClick={() => onToggle(pack.installed)}
          aria-label={`${pack.installed ? 'Remove' : 'Install'} ${pack.name}`}
        >
          {busy === pack.id ? (pack.installed ? 'Removing' : 'Installing') : pack.installed ? 'Remove' : 'Install'}
        </button>
        <Link href={`/compliance/packs/${pack.id}`} className={BTN} aria-label={`Open ${pack.name}`}>
          Open
        </Link>
      </div>
    </article>
  )
}

function PackGrid({ packs, pillarName, busy, onToggle }: { packs: Pack[]; pillarName?: (p: Pack) => string | undefined; busy: string | null; onToggle: (id: string, remove: boolean) => void }) {
  return (
    <div className="grid grid-cols-[repeat(auto-fill,minmax(260px,1fr))] gap-4">
      {packs.map((p) => (
        <PackCard key={p.id} pack={p} pillarName={pillarName?.(p)} busy={busy} onToggle={(remove) => onToggle(p.id, remove)} />
      ))}
    </div>
  )
}

function BundleCard({ bundle, journeyKeys, busy, onInstall }: { bundle: Bundle; journeyKeys: Set<string>; busy: string | null; onInstall: () => void }) {
  const complete = bundle.installedCount >= bundle.packs.length
  return (
    <article className="pk-card flex flex-col gap-3 p-5">
      <div className="flex flex-col gap-1">
        <b className="text-[15px] font-semibold">{bundle.name}</b>
        <p className={`m-0 text-[13px] leading-normal ${MUTED}`}>{bundle.for}</p>
      </div>
      <p className="m-0 text-[13px]">
        <b className="font-semibold tabular-nums">
          {bundle.installedCount} of {bundle.packs.length}
        </b>{' '}
        packs installed
      </p>
      <ul className="m-0 flex list-none flex-col gap-2.5 p-0">
        {bundle.targets.map((t) => (
          <li key={t.key} className="flex flex-col gap-1">
            {journeyKeys.has(t.key) ? (
              <Link href={`/compliance/journeys/${t.key}`} className="text-[13px] font-semibold hover:underline">
                {t.name}
              </Link>
            ) : (
              <span className="text-[13px] font-semibold">{t.name}</span>
            )}
            <CoverageBar label={`${t.name} coverage`} installed={t.coveredInstalled} all={t.coveredAll} total={t.active} allLabel="with this bundle" />
          </li>
        ))}
      </ul>
      <button
        type="button"
        className={`${complete ? BTN : BTN_P} mt-auto self-start`}
        disabled={complete || busy !== null}
        onClick={onInstall}
        aria-label={`Install bundle ${bundle.name}`}
      >
        {complete ? 'Bundle installed' : busy === bundle.id ? 'Installing' : 'Install bundle'}
      </button>
    </article>
  )
}

function JourneyRow({ j }: { j: JourneySummary }) {
  return (
    <li className="flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-[#15171a14] py-3">
      <Link href={`/compliance/journeys/${j.key}`} className="min-w-[200px] flex-[1_1_220px] font-semibold hover:underline">
        {j.name}
      </Link>
      <div className="min-w-[220px] flex-[2_1_300px]">
        <CoverageBar label={`${j.name} coverage`} installed={j.coveredInstalled} all={j.coveredAll} total={j.active} />
      </div>
      <Link href={`/compliance/journeys/${j.key}`} className={BTN} aria-label={`Open the ${j.name} journey`}>
        Open journey
      </Link>
    </li>
  )
}

export default function CompliancePage() {
  const catalogue = useCatalogue()
  const packs = usePacks()
  const bundles = useBundles()
  const journeys = useJourneys()
  const [tab, setTab] = useState(ALL)
  const installer = useInstaller(() => {
    packs.reload()
    bundles.reload()
    journeys.reload()
  })

  const pillars = catalogue.data?.pillars ?? []
  const pillarName = (id: string) => pillars.find((p) => p.id === id)?.name ?? cap(id.toLowerCase())
  const all = packs.data ?? []
  const active = pillars.find((p) => p.id === tab)
  const inTab = useMemo(() => (tab === ALL ? all : all.filter((p) => p.pillar === tab)), [all, tab])
  const figure = useMemo(
    // Pack lists carry counts, not workflow ids, so each installed pack shows one open tile per workflow.
    () => packsFigure(inTab.map((p) => ({ label: p.name, installed: p.installed, workflows: Array.from({ length: Math.min(p.workflowCount, 12) }, () => ({ status: null })) }))),
    [inTab],
  )
  const journeyKeys = useMemo(() => new Set((journeys.data ?? []).map((j) => j.key)), [journeys.data])
  const tabJourneys = (journeys.data ?? []).filter((j) => tab === ALL || j.pillar === tab)
  const installedCount = all.filter((p) => p.installed).length

  if (packs.loading && !packs.data) return <Loading label="Loading frameworks" />
  if (packs.error && !packs.data) return <ErrorNote message={`Frameworks could not be loaded. ${packs.error}`} onRetry={packs.reload} />

  const tabInstalled = inTab.filter((p) => p.installed)
  const label = `The ${active ? active.name : 'catalogue'} packs drawn as a board with ${inTab.length} ${inTab.length === 1 ? 'slot' : 'slots'}. ${tabInstalled.length} installed${
    tabInstalled.length ? `: ${tabInstalled.map((p) => p.name).join(', ')}` : ''
  }. Empty slots are dashed.`

  return (
    <div className="flex flex-col gap-[26px]">
      <Heading
        title="Frameworks"
        lead={`${installedCount} of ${all.length} packs installed. Agents run their workflows and file the evidence; you approve anything that would change a system.`}
      >
        <Link href="/compliance/evaluations" className={BTN}>Browse evaluations</Link>
      </Heading>

      {catalogue.error && <ErrorNote message={`The pillars could not be loaded. ${catalogue.error}`} onRetry={catalogue.reload} />}
      {installer.failure && <ErrorNote message={installer.failure} />}

      <Tabs value={tab} onValueChange={setTab} className="flex flex-col gap-5">
        <TabsList aria-label="Pillars" className="h-auto flex-wrap justify-start gap-2 bg-transparent p-0">
          <TabsTrigger value={ALL} className={TAB}>All</TabsTrigger>
          {pillars.map((p) => (
            <TabsTrigger key={p.id} value={p.id} className={TAB}>
              {p.name}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value={tab} className="mt-0 flex flex-col gap-[26px]">
          {inTab.length === 0 ? (
            <Empty>{tab === ALL ? 'The catalogue has no packs.' : 'This pillar has no packs.'}</Empty>
          ) : tab === ALL ? (
            <section aria-label="All packs" className="flex flex-col gap-6">
              {(pillars.length ? pillars.map((p) => p.id) : [...new Set(all.map((p) => p.pillar))]).map((id) => {
                const group = all.filter((p) => p.pillar === id)
                return group.length === 0 ? null : (
                  <div key={id} className="flex flex-col gap-3.5">
                    <h2 className="m-0 text-lg font-semibold">{pillarName(id)}</h2>
                    <PackGrid packs={group} busy={installer.busy} onToggle={installer.pack} />
                  </div>
                )
              })}
            </section>
          ) : (
            <>
              <section aria-label={`${pillarName(tab)} packs board`} className="pk-card flex flex-wrap items-stretch gap-[22px] p-[18px]">
                <div className="min-w-0 flex-[999_1_560px]">
                  <IsoFigure figure={figure} label={label} className="p-2.5" />
                </div>
                <div className="flex flex-[1_1_280px] flex-col gap-3 px-1 py-1.5">
                  <h2 className="m-0 text-base font-semibold">{pillarName(tab)}</h2>
                  {active && <p className={`m-0 text-[13px] leading-normal ${MUTED}`}>{active.description}</p>}
                  <p className="m-0 text-[13px]">
                    <b className="font-semibold tabular-nums">{tabInstalled.length} of {inTab.length}</b> packs installed
                  </p>
                  {active && (
                    <ul className={`m-0 flex list-none flex-col gap-1 p-0 text-[13px] ${MUTED}`}>
                      <li>{plural(active.workflows, 'workflow')}</li>
                      <li>{plural(active.evaluations, 'evaluation')}</li>
                      <li>{plural(active.frameworks, 'framework')} touched</li>
                    </ul>
                  )}
                  <ul className="m-0 mt-auto flex list-none flex-col gap-2 border-t border-[#15171a14] p-0 pt-3 text-[13px]">
                    <li className="flex items-center gap-2.5">
                      <span aria-hidden className="inline-block h-3.5 w-3.5 flex-none rounded border border-[#15171a1f] bg-white" />
                      Installed pack
                    </li>
                    <li className="flex items-center gap-2.5">
                      <span aria-hidden className="inline-block h-3.5 w-3.5 flex-none rounded border border-dashed border-[#8a8f98] bg-[#ebe8e1]" />
                      Slot not installed
                    </li>
                  </ul>
                </div>
              </section>
              <section aria-labelledby="packs-h" className="flex flex-col gap-3.5">
                <h2 id="packs-h" className="m-0 text-lg font-semibold">Packs</h2>
                <PackGrid packs={inTab} busy={installer.busy} onToggle={installer.pack} />
              </section>
            </>
          )}
        </TabsContent>
      </Tabs>

      <section aria-labelledby="bundles-h" className="flex flex-col gap-3.5">
        <div className="flex flex-wrap items-baseline justify-between gap-2.5">
          <h2 id="bundles-h" className="m-0 text-lg font-semibold">Bundles</h2>
          <span className={`text-[13px] ${MUTED}`}>A bundle installs every pack a kind of system needs.</span>
        </div>
        {bundles.loading && !bundles.data ? (
          <Loading label="Loading bundles" />
        ) : bundles.error && !bundles.data ? (
          <ErrorNote message={`Bundles could not be loaded. ${bundles.error}`} onRetry={bundles.reload} />
        ) : (bundles.data ?? []).length === 0 ? (
          <Empty>No bundles are in the catalogue.</Empty>
        ) : (
          <div className="grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-4">
            {(bundles.data ?? []).map((b) => (
              <BundleCard key={b.id} bundle={b} journeyKeys={journeyKeys} busy={installer.busy} onInstall={() => installer.bundle(b.id)} />
            ))}
          </div>
        )}
      </section>

      <section aria-labelledby="journeys-h" className="pk-card px-6 py-5">
        <div className="mb-1.5 flex flex-wrap items-baseline justify-between gap-2.5">
          <h2 id="journeys-h" className="m-0 text-base font-semibold">Journeys{tab === ALL ? '' : `: ${pillarName(tab)}`}</h2>
          <span className={`text-[12.5px] ${MUTED}`}>Dark bar: covered by installed packs. Light bar: covered with every pack.</span>
        </div>
        {journeys.loading && !journeys.data ? (
          <Loading label="Loading journeys" />
        ) : journeys.error && !journeys.data ? (
          <ErrorNote message={`Journeys could not be loaded. ${journeys.error}`} onRetry={journeys.reload} />
        ) : tabJourneys.length === 0 ? (
          <Empty>No frameworks in this pillar have a journey yet.</Empty>
        ) : (
          <ul className="m-0 list-none p-0">
            {tabJourneys.map((j) => (
              <JourneyRow key={j.key} j={j} />
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
