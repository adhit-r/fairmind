'use client'

import '@/astryx/pages/reports.css'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { Suspense, useEffect, useMemo, useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { VStack } from '@astryxdesign/core/Layout'
import { SegmentedControl, SegmentedControlItem } from '@astryxdesign/core/SegmentedControl'
import { Selector } from '@astryxdesign/core/Selector'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import { useOrgResource } from '@/lib/api/hooks/usePacks'
import { LIBRARY, useReportCalls, type Format } from '@/astryx/reports/api'
import { Briefing } from '@/astryx/reports/Briefing'
import { CrosswalkCard, GridCard, TasksCard } from '@/astryx/reports/Compliance'
import { DriftCard, FixesCard, GateCard, ToolsCard } from '@/astryx/reports/Engineering'
import { DecisionsCard, GovernedCard, OversightCard, RoadCard, TopRisksCard } from '@/astryx/reports/Executive'
import { AcceptanceCard, HeatCard, LedgerCard, PacksCard, RegisterCard, SampleCard, SoaCard } from '@/astryx/reports/AuditorRisk'
import { LibraryCard, RecentCard, ReportDrawer } from '@/astryx/reports/Library'
import { Card, ProofBars } from '@/astryx/reports/parts'
import { ROLES, type Briefing as BriefingModel, type ReportModel, type Role, type SealedReport } from '@/astryx/reports/types'

const isRole = (v: string | null): v is Role => ROLES.some((r) => r.key === v)

function Body({ m, role }: { m: ReportModel; role: Role }) {
  const proofBySystem = m.proof ? <Card span={6} title="Proof depth" sub="How each requirement is backed. Auditors weigh measured proof over a person's word."><ProofBars proof={m.proof} by="system" /></Card> : null
  const proofByGroup = (span: 5 | 7) => m.proof ? <Card span={span} title="Proof depth by clause group" sub="How each group of clauses is backed."><ProofBars proof={m.proof} by="group" /></Card> : null
  switch (role) {
    case 'executive':
      return (
        <>
          {m.road ? <RoadCard road={m.road} span={8} /> : null}
          {m.governed || m.decisions ? (
            <div className="rp-stack rp-c4">
              {m.governed ? <GovernedCard g={m.governed} /> : null}
              {m.decisions ? <DecisionsCard list={m.decisions} /> : null}
            </div>
          ) : null}
          {proofBySystem}
          {m.oversight ? <OversightCard o={m.oversight} /> : null}
          {m.risk ? <TopRisksCard risk={m.risk} /> : null}
        </>
      )
    case 'compliance':
      return (
        <>
          {m.road ? <RoadCard road={m.road} span={12} /> : null}
          {proofByGroup(5)}
          {m.crosswalk ? <CrosswalkCard c={m.crosswalk} /> : null}
          {m.tasks ? <TasksCard t={m.tasks} /> : null}
          {m.grid ? <GridCard g={m.grid} /> : null}
        </>
      )
    case 'engineering':
      return (
        <>
          {m.systems ? <GateCard systems={m.systems} /> : null}
          {m.engineering ? (
            <>
              <ToolsCard tools={m.engineering.toolExposure} />
              <DriftCard drift={m.engineering.fairnessDrift} />
              <FixesCard fixes={m.engineering.fixes} />
            </>
          ) : null}
        </>
      )
    case 'auditor':
      return (
        <>
          {m.auditor ? <LedgerCard l={m.auditor.ledger} /> : null}
          {m.auditor ? <SoaCard soa={m.auditor.soa} /> : null}
          {m.auditor ? <SampleCard s={m.auditor.sample} /> : null}
          {proofByGroup(7)}
          {m.auditor ? <PacksCard packs={m.auditor.packs} /> : null}
        </>
      )
    case 'risk':
      return m.risk ? (
        <>
          <HeatCard risk={m.risk} />
          <AcceptanceCard list={m.risk.acceptanceWaiting} />
          <RegisterCard risks={m.risk.risks} />
        </>
      ) : null
  }
}

function ReportsHub() {
  const router = useRouter()
  const search = useSearchParams()
  const role: Role = isRole(search.get('role')) ? (search.get('role') as Role) : 'executive'
  const system = search.get('system') || ''
  const { systems } = useSystemContext()
  const options = useMemo(
    () => [{ value: 'org', label: 'Whole organisation' }, ...systems.filter((s) => s.metadata?.source !== 'fallback').map((s) => ({ value: s.id, label: s.name }))],
    [systems],
  )
  const go = (next: { role?: Role; system?: string }) => {
    const q = new URLSearchParams()
    q.set('role', next.role ?? role)
    const s = next.system ?? system
    if (s) q.set('system', s)
    router.replace(`/reports?${q.toString()}`)
  }

  const path = `${API_ENDPOINTS.aiGovernance.reportOverview}?role=${role}${system ? `&system_id=${encodeURIComponent(system)}` : ''}`
  const overview = useOrgResource<ReportModel>(path)
  const recent = useOrgResource<SealedReport[]>(API_ENDPOINTS.aiGovernance.roleReports)
  const { briefing: reword } = useReportCalls()
  const model = overview.data

  // The organisation's model may reword the briefing; the record's own wording stays if it cannot.
  const [reworded, setReworded] = useState<{ key: string; briefing: BriefingModel } | null>(null)
  const key = model ? `${model.role}|${model.scope.systemId ?? ''}|${model.generatedAt}` : ''
  useEffect(() => {
    if (!model) return
    let live = true
    void reword({ role: model.role, ...(model.scope.systemId ? { system_id: model.scope.systemId } : {}), ...(model.framework.key ? { framework: model.framework.key } : {}) }).then((b) => {
      if (live && b && b.source === 'model') setReworded({ key, briefing: b })
    })
    return () => {
      live = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])
  const shown: ReportModel | null = model ? { ...model, briefing: reworded && reworded.key === key ? reworded.briefing : model.briefing } : null

  const [drawer, setDrawer] = useState<{ item: (typeof LIBRARY)[Role][number]; format: Format } | null>(null)
  const scopeName = shown?.scope.systemName ?? 'Whole organisation'

  return (
    <div className="fm-page rp-page">
      <VStack gap={5}>
        <div className="rp-head">
          <VStack gap={1}>
            <Heading level={1}>Reports</Heading>
            <Text color="secondary">
              {shown?.framework.name ? (
                <>Framework: {shown.framework.name}</>
              ) : shown ? (
                <>No framework followed. <Link href="/plan">Choose one in your plan</Link></>
              ) : (
                'Reading the record'
              )}
            </Text>
          </VStack>
          <div className="rp-controls">
            <div className="rp-scope">
              <Selector label="Scope" options={options} value={system || 'org'} onChange={(v) => go({ system: String(v) === 'org' ? '' : String(v) })} />
            </div>
            <Button label="Download report" variant="primary" isDisabled={!shown} onClick={() => setDrawer({ item: LIBRARY[role][0], format: LIBRARY[role][0].formats[0] })} />
          </div>
        </div>

        <div className="rp-lens">
          <SegmentedControl label="Who is reading" value={role} onChange={(v) => go({ role: String(v) as Role })} size="sm">
            {ROLES.map((r) => <SegmentedControlItem key={r.key} label={r.label} value={r.key} />)}
          </SegmentedControl>
        </div>

        {overview.error ? (
          <Banner status="error" title="The report could not load" description={overview.error} />
        ) : !shown ? (
          <div className="rp-grid" aria-busy="true">
            <div className="rp-c12"><Skeleton height={120} /></div>
            <div className="rp-c8"><Skeleton height={280} /></div>
            <div className="rp-c4"><Skeleton height={280} /></div>
          </div>
        ) : (
          <div className="rp-grid">
            <Briefing briefing={shown.briefing} generatedAt={shown.generatedAt} />
            <Body m={shown} role={role} />
            <LibraryCard role={role} onPick={(item, format) => setDrawer({ item, format })} />
            <RecentCard role={role} reports={recent.data} loading={recent.loading} error={recent.error} />
          </div>
        )}
      </VStack>

      {drawer && shown ? (
        <ReportDrawer item={drawer.item} format={drawer.format} model={shown} scopeName={scopeName} onClose={() => setDrawer(null)} onSealed={recent.reload} />
      ) : null}
    </div>
  )
}

export default function ReportsPage() {
  return (
    <Suspense fallback={null}>
      <ReportsHub />
    </Suspense>
  )
}
