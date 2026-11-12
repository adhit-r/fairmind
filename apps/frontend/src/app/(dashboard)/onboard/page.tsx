'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useRef, useState, type FormEvent } from 'react'
import { useSystemContext, type AISystemSummary } from '@/components/workflow/SystemContext'
import { ApplicabilityForm } from '@/components/workflow/ApplicabilityForm'
import { confirmApplicability, type ApplicabilityDraft } from '@/lib/api/hooks/useApplicability'
import { STAGES } from '@/components/layout/AppShell'
import { PlanDemo } from '@/components/stageshow/PlanDemo'
import { Illustration } from '@/components/stageshow/fm'
import { apiClient } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import { readSystemsCsv, SYSTEMS_CSV_TEMPLATE, type SystemRow } from '@/lib/systemsCsv'

const field =
  'h-10 w-full rounded-[10px] border border-[rgba(21,23,26,.14)] bg-white px-3 text-[14px] outline-none focus:border-[var(--fm-ink)]'
const label = 'block text-[12.5px] font-medium text-[var(--fm-ink2)]'

/**
 * Register one AI system. Creates a workspace and the system, records the confirmed tier and frameworks,
 * then opens the system file. If recording the tier fails, a retry records it on the system already created.
 * Both creates carry ids chosen once per visit, so a retry after a timeout or a failed step replays them
 * and gets back the workspace and system already made rather than new ones.
 */
export default function OnboardPage() {
  const { createWorkspaceAndSystem } = useSystemContext()
  const router = useRouter()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [draft, setDraft] = useState<ApplicabilityDraft | null>(null)
  const [registeredId, setRegisteredId] = useState<string | null>(null)
  const ids = useRef<{ workspace: string; system: string } | null>(null)

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!draft) return
    const f = new FormData(e.currentTarget)
    const v = (k: string) => String(f.get(k) ?? '').trim()
    setBusy(true)
    setError(null)
    let id = registeredId
    try {
      if (!id) {
        ids.current ??= { workspace: crypto.randomUUID(), system: crypto.randomUUID() }
        const system = await createWorkspaceAndSystem({
          ids: ids.current,
          workspaceName: v('workspace'),
          workspaceOwner: v('workspaceOwner'),
          systemName: v('name'),
          systemOwner: v('owner'),
          riskTier: draft.tier,
          stage: v('stage') as AISystemSummary['stage'],
          systemVersion: v('version') || undefined,
          businessLine: v('line') || undefined,
        })
        id = system.id
        setRegisteredId(id)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
      setBusy(false)
      return
    }
    try {
      // Without answers (suggestions could not load) the tier is confirmed later on the system file.
      if (draft.body) await confirmApplicability(id, draft.body)
      router.push(`/systems/${id}`)
    } catch (err) {
      setError(`System registered. The tier and rules were not recorded: ${err instanceof Error ? err.message : 'request failed'}`)
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto grid max-w-[760px] gap-8 xl:max-w-[1220px] xl:grid-cols-[760px_minmax(0,420px)]">
      <div>
      <div className="text-[12.5px] font-medium text-[var(--fm-ink2)]">
        <Link href="/systems" className="hover:text-[var(--fm-ink)]">AI systems</Link> · Register
      </div>
      <h1 className="mt-1.5 text-[30px] font-semibold leading-[1.1] tracking-[-.03em]">Register an AI system</h1>
      <p className="mt-2 max-w-[560px] text-[15px] text-[var(--fm-ink2)]">
        One system by hand, or{' '}
        <a href="#import" className="font-medium text-[var(--fm-ink)] underline-offset-2 hover:underline">many from a CSV</a>. To find systems in MLflow, GitHub or Hugging Face instead, use{' '}
        <Link href="/discovery" className="font-medium text-[var(--fm-ink)] underline-offset-2 hover:underline">Discovery</Link>.
      </p>

      <form onSubmit={submit} className="fm-card mt-6 grid gap-6 p-7">
        <section className="grid gap-3">
          <h2 className="text-[11px] font-semibold uppercase tracking-[.08em] text-[var(--fm-ink3)]">System</h2>
          <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_140px]">
            <div>
              <label className={label} htmlFor="name">Name</label>
              <input id="name" name="name" required className={field} autoComplete="off" />
            </div>
            <div>
              <label className={label} htmlFor="version">Version</label>
              <input id="version" name="version" className={field} autoComplete="off" />
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className={label} htmlFor="owner">Owner</label>
              <input id="owner" name="owner" required className={field} autoComplete="off" />
            </div>
            <div>
              <label className={label} htmlFor="line">Business line</label>
              <input id="line" name="line" className={field} autoComplete="off" />
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className={label} htmlFor="stage">Lifecycle stage</label>
              <select id="stage" name="stage" defaultValue="onboard" className={field}>
                {STAGES.map((s) => (
                  <option key={s.key} value={s.key}>{s.label}</option>
                ))}
              </select>
            </div>
          </div>
        </section>

        <section className="grid gap-3 border-t border-[var(--fm-line)] pt-5">
          <h2 className="text-[11px] font-semibold uppercase tracking-[.08em] text-[var(--fm-ink3)]">What you&apos;re shipping</h2>
          <ApplicabilityForm onChange={setDraft} />
        </section>

        <section className="grid gap-3 border-t border-[var(--fm-line)] pt-5">
          <h2 className="text-[11px] font-semibold uppercase tracking-[.08em] text-[var(--fm-ink3)]">Workspace</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className={label} htmlFor="workspace">Workspace name</label>
              <input id="workspace" name="workspace" required className={field} autoComplete="off" />
            </div>
            <div>
              <label className={label} htmlFor="workspaceOwner">Workspace owner</label>
              <input id="workspaceOwner" name="workspaceOwner" required className={field} autoComplete="off" />
            </div>
          </div>
        </section>

        {error && (
          <p className="rounded-[10px] bg-[#fde9ea] px-3 py-2 text-[13px] text-[#b4232c]">
            {error}
            {registeredId && (
              <>
                {' '}
                <Link href={`/systems/${registeredId}`} className="font-semibold underline">Open the system file</Link>
              </>
            )}
          </p>
        )}

        <div className="flex items-center justify-end gap-3">
          <Link href="/dashboard" className="text-[13px] font-medium text-[var(--fm-ink2)] hover:text-[var(--fm-ink)]">Cancel</Link>
          <button
            type="submit"
            disabled={busy || !draft || !(draft.ready || draft.failed)}
            className="h-10 rounded-full bg-[var(--fm-ink)] px-5 text-[13px] font-semibold text-white disabled:opacity-60"
          >
            {busy ? 'Registering' : registeredId ? 'Record tier and rules' : 'Register system'}
          </button>
        </div>
      </form>

      <CsvImport />
      </div>

      <aside className="hidden xl:block">
        <div className="sticky top-6 mt-[112px]">
          <div className="mb-3 text-[11px] font-semibold uppercase tracking-[.08em] text-[var(--fm-ink3)]">After you register</div>
          <Illustration label="The agent recommends packs for the new system, each closing framework requirements, and the plan is accepted">
            <PlanDemo />
          </Illustration>
        </div>
      </aside>
    </div>
  )
}

type Outcome = { row: SystemRow; id?: string; error?: string }

/**
 * Register many systems from one CSV into one workspace. Rows go one at a time so each gets its own result;
 * ids are fixed per file, so running it again after a failure skips nothing and duplicates nothing.
 */
function CsvImport() {
  const { refreshSystems } = useSystemContext()
  const [file, setFile] = useState<{ name: string; rows: SystemRow[]; problems: { line: number; message: string }[] } | null>(null)
  const [outcomes, setOutcomes] = useState<Outcome[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const ids = useRef<{ workspace: string; rows: Map<number, string> } | null>(null)

  async function read(f: File | undefined) {
    setOutcomes([])
    setError(null)
    if (!f) return setFile(null)
    ids.current = { workspace: crypto.randomUUID(), rows: new Map() }
    setFile({ name: f.name, ...readSystemsCsv(await f.text()) })
  }

  async function register(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!file || !ids.current) return
    const form = new FormData(e.currentTarget)
    const v = (k: string) => String(form.get(k) ?? '').trim()
    setBusy(true)
    setError(null)
    const ws = await apiClient.post<{ id: string }>(API_ENDPOINTS.aiGovernance.workspaces, {
      id: ids.current.workspace,
      name: v('importWorkspace'),
      owner: v('importOwner'),
    })
    if (!ws.success || !ws.data) {
      setError(ws.error || 'The workspace could not be created.')
      setBusy(false)
      return
    }
    const done: Outcome[] = []
    for (const row of file.rows) {
      const already = outcomes.find((o) => o.row.line === row.line && o.id)
      if (already) { done.push(already); continue }
      const id = ids.current.rows.get(row.line) ?? crypto.randomUUID()
      ids.current.rows.set(row.line, id)
      const res = await apiClient.post<{ id: string }>(API_ENDPOINTS.aiGovernance.systems, {
        id,
        workspace_id: ws.data.id,
        name: row.name,
        owner: row.owner || v('importOwner'),
        risk_tier: row.riskTier,
        lifecycle_stage: row.stage,
        metadata: {
          created_from: 'csv_import',
          workspace_name: v('importWorkspace'),
          ...(row.version && { system_version: row.version }),
          ...(row.businessLine && { business_line: row.businessLine }),
        },
      })
      done.push(res.success && res.data ? { row, id: res.data.id } : { row, error: res.error || 'Not registered' })
      setOutcomes([...done])
    }
    await refreshSystems()
    setBusy(false)
  }

  const registered = outcomes.filter((o) => o.id).length
  const failed = outcomes.filter((o) => o.error).length

  return (
    <form id="import" onSubmit={register} className="fm-card mt-6 grid gap-4 p-7">
      <div>
        <h2 className="text-[18px] font-semibold tracking-[-.01em]">Register many from a CSV</h2>
        <p className="mt-1 text-[13.5px] text-[var(--fm-ink2)]">
          One system per row. Columns: <code>name</code> and <code>risk_tier</code> (low, medium, high or critical) are required;{' '}
          <code>owner</code>, <code>stage</code>, <code>business_line</code> and <code>version</code> are optional.{' '}
          <a
            className="font-medium text-[var(--fm-ink)] underline-offset-2 hover:underline"
            href={`data:text/csv;charset=utf-8,${encodeURIComponent(SYSTEMS_CSV_TEMPLATE)}`}
            download="fairmind-systems.csv"
          >
            Download the header
          </a>
        </p>
      </div>
      <div>
        <label className={label} htmlFor="importFile">CSV file</label>
        <input id="importFile" type="file" accept=".csv,text/csv" onChange={(e) => void read(e.target.files?.[0])} className="mt-1 block text-[13px]" />
      </div>
      {file && (
        <div className="grid gap-2 text-[13px]">
          <p>
            <b>{file.rows.length}</b> {file.rows.length === 1 ? 'system' : 'systems'} ready in {file.name}
            {file.problems.length > 0 && <>, <b className="text-[#b4232c]">{file.problems.length}</b> {file.problems.length === 1 ? 'row' : 'rows'} will be skipped</>}.
          </p>
          {file.problems.length > 0 && (
            <ul className="grid gap-1 text-[#b4232c]">
              {file.problems.slice(0, 20).map((p) => <li key={p.line}>Line {p.line}: {p.message}</li>)}
            </ul>
          )}
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className={label} htmlFor="importWorkspace">Workspace for these systems</label>
              <input id="importWorkspace" name="importWorkspace" required className={field} autoComplete="off" />
            </div>
            <div>
              <label className={label} htmlFor="importOwner">Owner when a row names none</label>
              <input id="importOwner" name="importOwner" required className={field} autoComplete="off" />
            </div>
          </div>
        </div>
      )}
      {outcomes.length > 0 && (
        <div className="grid gap-1 text-[13px]" aria-live="polite">
          <p><b>{registered}</b> registered{failed > 0 && <>, <b className="text-[#b4232c]">{failed}</b> failed</>}{busy && ', working'}.</p>
          <ul className="grid gap-1">
            {outcomes.map((o) => (
              <li key={o.row.line}>
                {o.id ? <Link className="underline-offset-2 hover:underline" href={`/systems/${o.id}`}>{o.row.name}</Link> : <span className="text-[#b4232c]">{o.row.name}: {o.error}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}
      {error && <p className="rounded-[10px] bg-[#fde9ea] px-3 py-2 text-[13px] text-[#b4232c]">{error}</p>}
      <div className="flex justify-end">
        <button
          type="submit"
          disabled={busy || !file?.rows.length || (outcomes.length > 0 && failed === 0)}
          className="h-10 rounded-full bg-[var(--fm-ink)] px-5 text-[13px] font-semibold text-white disabled:opacity-60"
        >
          {busy ? 'Registering' : failed ? `Retry ${failed} failed` : `Register ${file?.rows.length ?? 0} systems`}
        </button>
      </div>
    </form>
  )
}
