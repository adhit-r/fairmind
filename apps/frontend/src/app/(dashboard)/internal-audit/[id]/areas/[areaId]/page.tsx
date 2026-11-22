'use client'

import '@/astryx/pages/internal-audit.css'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { VStack } from '@astryxdesign/core/Layout'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { TextArea } from '@astryxdesign/core/TextArea'
import { TextInput } from '@astryxdesign/core/TextInput'
import { useOrg } from '@/context/OrgContext'
import { useSession } from '@/context/SessionContext'
import {
  askOwner, canConclude, concludeCheck, GRADES, gradeLabel, needsOverride, sendToLead, useAuditArea,
  type AuditCheck, type Grade,
} from '@/lib/api/hooks/useInternalAudit'

const stateOf = (c: AuditCheck) => (c.grade ? gradeLabel(c.grade) : c.ownerAnswers.some((a) => !a.answeredAt) ? 'Waiting on owner' : c.suggestedGrade ? `${gradeLabel(c.suggestedGrade)}?` : 'Not prepared')

type Act = (fn: () => Promise<unknown>, done: string) => Promise<void>

/** The working paper for one check; keyed by check id so its form starts from that check's saved conclusion or suggestion. */
function Paper({ check, mayWrite, busy, orgId, act }: { check: AuditCheck; mayWrite: boolean; busy: boolean; orgId: string; act: Act }) {
  const [grade, setGrade] = useState<Grade | null>(check.grade ?? check.suggestedGrade)
  const [statement, setStatement] = useState(check.statement ?? '')
  const [reason, setReason] = useState(check.overrideReason ?? '')
  const [email, setEmail] = useState('')
  const [question, setQuestion] = useState('')
  const overriding = needsOverride(grade, check.suggestedGrade)
  const canRecord = mayWrite && !!grade && !!statement.trim() && (!overriding || !!reason.trim())
  return (
    <article className="ia-card ia-paper" aria-label="Working paper">
      <div>
        <span className="ia-label">{check.clause} · {check.systemName}</span>
        <h2>{check.question}</h2>
      </div>

      <section>
        <span className="ia-label">What the assistant found</span>
        <p>{check.assistantSummary ?? 'The assistant has not prepared this check yet.'}</p>
        <div className="ia-chips">
          {check.evidence.map((e, i) => <span key={i} className={e.found ? '' : 'missing'}>{e.text}</span>)}
        </div>
      </section>

      <section>
        <span className="ia-label">Interview with the owner</span>
        {check.ownerAnswers.length === 0 && <Text color="secondary">No question asked yet.</Text>}
        {check.ownerAnswers.map((o) => (
          <div key={o.id} style={{ display: 'grid', gap: 8 }}>
            <p><span className="ia-muted">You asked {o.email}:</span> {o.questions[0]?.text}</p>
            {o.answers
              ? <p className="ia-answer"><span className="ia-muted">{o.answeredAt?.slice(0, 10)}:</span> {Object.values(o.answers).join(' · ')}</p>
              : <p className="ia-muted">Waiting for an answer, sent {o.sentAt.slice(0, 10)}.</p>}
          </div>
        ))}
        {mayWrite && !check.grade && (
          <div style={{ display: 'grid', gap: 8 }}>
            <TextInput label="Owner's email" value={email} onChange={setEmail} />
            <TextArea label="Question" value={question} onChange={setQuestion} rows={2} />
            <div>
              <Button label={check.ownerAnswers.length ? 'Ask a follow-up' : 'Ask the owner'} variant="secondary" isDisabled={busy || !email.includes('@') || !question.trim()} onClick={() => void act(async () => { const r = await askOwner(orgId, check.id, email, question); setQuestion(''); return r }, 'The question was sent through a link.')} />
            </div>
          </div>
        )}
      </section>

      <section style={{ paddingTop: 20, borderTop: '1px solid var(--fm-line)' }}>
        <span className="ia-label">Your conclusion</span>
        <div className="ia-grades" role="radiogroup" aria-label="Grade">
          {GRADES.map((g) => (
            <label key={g.value}>
              <input type="radio" name="grade" checked={grade === g.value} disabled={!mayWrite || !!check.grade} onChange={() => setGrade(g.value)} /> {g.label}
            </label>
          ))}
        </div>
        {check.suggestedGrade && <Text color="secondary">Suggested: {gradeLabel(check.suggestedGrade)}. {check.suggestedBasis}</Text>}
        <TextArea label="Finding statement" value={statement} onChange={setStatement} rows={3} isDisabled={!mayWrite || !!check.grade} />
        {overriding && <TextArea label={`Why ${gradeLabel(grade)} and not ${gradeLabel(check.suggestedGrade)}`} value={reason} onChange={setReason} rows={2} isDisabled={!mayWrite || !!check.grade} />}
        {check.grade ? (
          <Text color="secondary">Concluded{check.remediationTaskId ? '; a remediation task is open for the owner.' : '.'}</Text>
        ) : (
          <div>
            <Button label="Record conclusion" variant="primary" isDisabled={busy || !canRecord} onClick={() => void act(() => concludeCheck(orgId, check.id, grade!, statement, overriding ? reason : undefined), 'The conclusion was recorded.')} />
          </div>
        )}
      </section>
    </article>
  )
}

export default function AreaPage() {
  const { id, areaId } = useParams<{ id: string; areaId: string }>()
  const { selectedOrg } = useOrg()
  const orgId = selectedOrg?.id
  const { user } = useSession()
  const { data, loading, error, reload } = useAuditArea(areaId)
  const [pick, setPick] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const check = data?.checks.find((c) => c.id === pick) ?? data?.checks[0] ?? null
  const act = async (fn: () => Promise<unknown>, done: string) => {
    setBusy(true)
    setProblem(null)
    setNotice(null)
    try {
      await fn()
      setNotice(done)
      reload()
    } catch (e) {
      setProblem(e instanceof Error ? e.message : 'The change was not saved')
    } finally {
      setBusy(false)
    }
  }

  if (error) return <div className="fm-page"><Banner status="error" title="The area could not load" description={error} /></div>
  if (loading || !data || !orgId) return <div className="fm-page"><Skeleton height={200} /></div>

  const { area, checks } = data
  const mayWrite = canConclude(area, user?.id)
  const open = checks.filter((c) => !c.grade).length

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <header style={{ display: 'flex', flexWrap: 'wrap', gap: 16, alignItems: 'flex-end', justifyContent: 'space-between' }}>
          <VStack gap={1}>
            <Text color="secondary"><Link href={`/internal-audit/${id}`}>Back to the audit</Link></Text>
            <Heading level={1}>{area.name}</Heading>
            <Text color="secondary">{area.clauses.join(', ')} · {area.systemIds.length} system{area.systemIds.length === 1 ? '' : 's'}{area.auditorEmail ? ` · auditor ${area.auditorEmail}` : ''}</Text>
          </VStack>
          {mayWrite && <Button label={open ? `Send area to lead (${open} open)` : 'Send area to lead'} variant="primary" isDisabled={busy || open > 0} onClick={() => void act(() => sendToLead(orgId, areaId), 'The area was sent to the lead auditor.')} />}
        </header>

        {problem && <Banner status="error" title="That did not work" description={problem} />}
        {notice && <Banner status="success" title={notice} />}
        {!mayWrite && <Banner status="info" title="Read only" description="Only this area's auditor can ask owners and record conclusions, and only during fieldwork." />}

        {checks.length === 0 || !check ? (
          <Text color="secondary">This area has no checks.</Text>
        ) : (
          <div className="ia-work">
            <nav className="ia-card ia-checks" aria-label="Checks in this area">
              {checks.map((c) => (
                <button key={c.id} type="button" aria-current={c.id === check.id} onClick={() => setPick(c.id)}>
                  <span><b>{c.clause}</b> {c.clauseTitle}<small>{c.systemName}</small></span>
                  <span className="state">{stateOf(c)}</span>
                </button>
              ))}
            </nav>

            <Paper key={check.id} check={check} mayWrite={mayWrite} busy={busy} orgId={orgId} act={act} />
          </div>
        )}
      </VStack>
    </div>
  )
}
