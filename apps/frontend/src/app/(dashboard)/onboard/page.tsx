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
      router.push(`/systems/${id}/plan`)
    } catch (err) {
      setError(`System registered. The tier and rules were not recorded: ${err instanceof Error ? err.message : 'request failed'}`)
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto grid max-w-[760px] gap-8 xl:max-w-[1220px] xl:grid-cols-[760px_minmax(0,420px)]">
      <div>
      <div className="text-[12.5px] font-medium text-[var(--fm-ink2)]">
        <Link href="/dashboard" className="hover:text-[var(--fm-ink)]">Today</Link> · Register a system
      </div>
      <h1 className="mt-1.5 text-[30px] font-semibold leading-[1.1] tracking-[-.03em]">Register an AI system</h1>
      <p className="mt-2 max-w-[560px] text-[15px] text-[var(--fm-ink2)]">
        Manual entry for one system. To discover systems from MLflow, GitHub or Hugging Face instead, use{' '}
        <Link href="/integrations" className="font-medium text-[var(--fm-ink)] underline-offset-2 hover:underline">Integrations</Link>.
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
