'use client'

import '@/astryx/pages/internal-audit.css'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useRef, useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { VStack } from '@astryxdesign/core/Layout'
import { Selector } from '@astryxdesign/core/Selector'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { TextInput } from '@astryxdesign/core/TextInput'
import { useOrg } from '@/context/OrgContext'
import { useSession } from '@/context/SessionContext'
import { useMembers } from '@/astryx/data/settings'
import {
  acceptArea, approvePlan, blockingConflict, canIssue, GRADES, issueAudit, mine, prepareEvidence, progressPct, reassignArea, uploadPlan, useAudit, warningFor,
  type AuditArea,
} from '@/lib/api/hooks/useInternalAudit'

const STATUS: Record<string, string> = { fieldwork: 'Fieldwork', sent_to_lead: 'Ready for lead review', accepted: 'Accepted' }
const AUDIT_STATUS: Record<string, string> = { planning: 'Planning', fieldwork: 'Fieldwork', issued: 'Issued' }

export default function AuditPage() {
  const { id } = useParams<{ id: string }>()
  const { selectedOrg } = useOrg()
  const orgId = selectedOrg?.id
  const { user } = useSession()
  const { data, loading, error, reload } = useAudit(id)
  const members = useMembers(orgId)
  const file = useRef<HTMLInputElement>(null)
  const [approver, setApprover] = useState('')
  const [reassigning, setReassigning] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [preparing, setPreparing] = useState(false)
  const [problem, setProblem] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const names = new Map(members.data.map((m) => [m.user_id, m.name || m.email || m.user_id]))
  const options = members.data.map((m) => ({ value: m.user_id, label: m.name || m.email || m.user_id }))
  const nameOf = (uid: string | null, email: string | null) => (uid && names.get(uid)) || email || 'Not assigned'

  const act = async (fn: () => Promise<unknown>, done?: string) => {
    setBusy(true)
    setProblem(null)
    setNotice(null)
    try {
      await fn()
      if (done) setNotice(done)
      reload()
    } catch (e) {
      setProblem(e instanceof Error ? e.message : 'The change was not saved')
    } finally {
      setBusy(false)
    }
  }

  if (error) return <div className="fm-page"><Banner status="error" title="The audit could not load" description={error} /></div>
  if (loading || !data || !orgId) return <div className="fm-page"><Skeleton height={200} /></div>

  const { audit, team, areas, conflicts, gradeCounts, unmatchedLines } = data
  const isLead = mine(user?.id, audit.leadAuditorId)
  const planning = audit.status === 'planning'
  const issued = audit.status === 'issued'
  const locked = busy || preparing || issued
  const conflictFor = (a: AuditArea) => blockingConflict(conflicts, a.id)
  const warnFor = (a: AuditArea) => warningFor(conflicts, a.id)
  const leadConflicts = conflicts.filter((c) => !c.areaId || c.kind?.startsWith('lead_'))
  const totalChecks = areas.reduce((n, a) => n + a.checksTotal, 0)
  const dates = [`evidence period ${audit.periodStart} to ${audit.periodEnd}`, audit.fieldworkStart && audit.fieldworkEnd ? `fieldwork ${audit.fieldworkStart} to ${audit.fieldworkEnd}` : null].filter(Boolean).join(' · ')

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <header style={{ display: 'flex', flexWrap: 'wrap', gap: 16, alignItems: 'flex-end', justifyContent: 'space-between' }}>
          <VStack gap={1}>
            <Text color="secondary"><Link href="/internal-audit">Internal audit</Link> · {AUDIT_STATUS[audit.status] ?? audit.status}</Text>
            <Heading level={1}>{audit.title}</Heading>
            <Text color="secondary">ISO/IEC 42001 · {dates}</Text>
          </VStack>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            <Button label="Records" variant="secondary" href={`/internal-audit/${id}/records`} />
            {isLead && !issued && (
              <Button label="Issue report" variant="primary" isDisabled={locked || !canIssue(data)} onClick={() => void act(() => issueAudit(orgId, id), 'The report was issued.')} />
            )}
          </div>
        </header>

        {problem && <Banner status="error" title="That did not work" description={problem} />}
        {notice && <Banner status="success" title={notice} />}
        {leadConflicts.map((c, i) => <Banner key={i} status={c.blocking ? 'error' : 'warning'} title={c.blocking ? 'Independence conflict' : 'Independence could not be checked'} description={c.detail} />)}

        <section className="ia-card ia-plan" aria-label="Audit plan source">
          <VStack gap={1}>
            <span className="ia-label">Your audit plan</span>
            {audit.planFilename ? (
              <Text>
                <b>{audit.planFilename}</b>
                {audit.planApprovedAt ? ` · approved by ${audit.planApprovedBy}, ${audit.planApprovedAt.slice(0, 10)}` : ' · waiting for approval'}
              </Text>
            ) : (
              <Text color="secondary">No plan uploaded yet. Columns: area, clauses, systems, auditor, process_owner (.csv or .xlsx).</Text>
            )}
          </VStack>
          {audit.planFilename && (
            <div className="nums">
              <span><b>{areas.length}</b> areas read from the plan</span>
              <span><b>{totalChecks}</b> checks matched to FairMind evidence</span>
              <span className={unmatchedLines.length ? 'ia-warn' : ''}><b>{unmatchedLines.length}</b> plan lines not matched</span>
            </div>
          )}
          {planning && isLead && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
              <input ref={file} type="file" accept=".csv,.xlsx" aria-label="Plan file" hidden onChange={(e) => {
                const f = e.target.files?.[0]
                e.target.value = ''
                if (f) void act(() => uploadPlan(orgId, id, f), 'The plan was read.')
              }} />
              <Button label={audit.planFilename ? 'Replace plan' : 'Upload plan'} variant="secondary" isDisabled={locked} onClick={() => file.current?.click()} />
            </div>
          )}
        </section>

        {unmatchedLines.length > 0 && (
          <section className="ia-card" aria-label="Unmatched plan lines">
            <VStack gap={2}>
              <Heading level={3}>Plan lines FairMind could not match</Heading>
              <ul className="ia-list">
                {unmatchedLines.map((u, i) => (
                  <li key={i}><span className="ia-warn">Line {u.line}, {u.column}: &ldquo;{u.value}&rdquo; · {u.reason}</span></li>
                ))}
              </ul>
            </VStack>
          </section>
        )}

        {planning && isLead && audit.planFilename && (
          <section className="ia-card" aria-label="Approve plan">
            <VStack gap={2}>
              <Heading level={3}>Approve the plan</Heading>
              <Text color="secondary">Record who approved it. Fieldwork starts once it is approved.</Text>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'flex-end' }}>
                <TextInput label="Approved by (name and role)" value={approver} onChange={setApprover} />
                <Button label="Approve plan" variant="primary" isDisabled={locked || !approver.trim() || areas.length === 0} onClick={() => void act(() => approvePlan(orgId, id, approver), 'The plan was approved.')} />
              </div>
            </VStack>
          </section>
        )}

        <section className="ia-team" aria-label="Audit team">
          {team.map((t) => (
            <div className="ia-card" key={t.userId}>
              <span className="ia-label">{t.role === 'lead' ? 'Lead auditor' : 'Auditor'}</span>
              <b>{nameOf(t.userId, t.email)}</b>
              <small>{t.role === 'lead' ? 'Approves plan, reviews every area, issues the report' : `${t.checksDone} of ${t.checksTotal} checks done`}</small>
            </div>
          ))}
          <div className="ia-card ia-bot">
            <span className="ia-label">Audit assistant</span>
            <b>FairMind agent</b>
            <small>Read-only. Gathers evidence, drafts questions and summaries. Concludes nothing.</small>
          </div>
        </section>

        <section aria-label="Audit areas">
          <VStack gap={3}>
            <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'baseline', gap: 8 }}>
              <Heading level={2}>Scope, as set in your plan</Heading>
              <Text color="secondary">An auditor never audits a system they own or a process they run.</Text>
            </div>
            {areas.length === 0 ? (
              <Text color="secondary">No areas yet. Upload the plan to see them.</Text>
            ) : (
              <div className="ia-card ia-table">
                <div className="ia-row head"><span>Area · clauses</span><span>Systems and process owner</span><span>Auditor</span><span>Progress</span><span>Status</span></div>
                {areas.map((a) => {
                  const conflict = conflictFor(a)
                  return (
                    <div className={`ia-row${conflict ? ' conflict' : ''}`} key={a.id}>
                      <span>
                        <Link className="name" href={`/internal-audit/${id}/areas/${a.id}`}>{a.name}</Link>
                        <small>{a.clauses.join(' · ')}</small>
                      </span>
                      <span>{a.systemNames.join(', ') || 'No systems'}{a.processOwner ? ` · ${a.processOwner}` : ''}</span>
                      <span className={conflict ? 'ia-bad' : ''}>
                        {reassigning === a.id ? (
                          <Selector label="Auditor" size="sm" options={options} value={a.auditorId ?? ''} onChange={(v) => { setReassigning(null); void act(() => reassignArea(orgId, a.id, String(v))) }} />
                        ) : (
                          <>{nameOf(a.auditorId, a.auditorEmail)}{conflict ? ' · conflict' : ''}</>
                        )}
                      </span>
                      <span>
                        {conflict ? (
                          <span className="ia-warn">{conflict.detail}</span>
                        ) : (
                          <>
                            {warnFor(a) && <small className="ia-warn">Owner could not be matched to a member</small>}
                          <>
                            <span className={`ia-bar${a.checksTotal && a.checksDone === a.checksTotal ? ' done' : ''}`}><i style={{ width: `${progressPct(a)}%`, display: 'block' }} /></span>
                            <small>{a.checksDone} of {a.checksTotal}{a.waitingOnOwner ? ` · ${a.waitingOnOwner} waiting on owner` : ''}</small>
                          </>
                          </>
                        )}
                      </span>
                      <span style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
                        <span>{planning ? 'Planned' : (STATUS[a.status] ?? a.status)}</span>
                        {isLead && !issued && conflict && reassigning !== a.id && <Button label="Reassign" size="sm" variant="secondary" isDisabled={locked} onClick={() => setReassigning(a.id)} />}
                        {isLead && a.status === 'sent_to_lead' && <Button label="Accept area" size="sm" variant="primary" isDisabled={locked} onClick={() => void act(() => acceptArea(orgId, a.id))} />}
                      </span>
                    </div>
                  )
                })}
              </div>
            )}
            {isLead && audit.status === 'fieldwork' && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center' }}>
                <Button label={preparing ? 'Preparing…' : 'Prepare evidence'} variant="secondary" isDisabled={locked} onClick={() => {
                  setPreparing(true)
                  void act(() => prepareEvidence(orgId, id), 'The assistant read the evidence for every check not yet graded.').finally(() => setPreparing(false))
                }} />
                {preparing && <Text color="secondary">The assistant is reading the evidence. This can take a minute.</Text>}
              </div>
            )}
          </VStack>
        </section>

        <ul className="ia-counts" aria-label="Grades so far">
          {GRADES.slice().reverse().map((g) => (
            <li key={g.value}><b>{gradeCounts[g.value] ?? 0}</b><span>{g.label}</span></li>
          ))}
          <li><b>{gradeCounts.notConcluded}</b><span>Not concluded</span></li>
        </ul>
      </VStack>
    </div>
  )
}
