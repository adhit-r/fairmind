'use client'

import { useEffect, useState, type ReactNode } from 'react'
import { usePackActions, useSystemTarget, type SystemTargetBody } from '@/lib/api/hooks/usePacks'
import { BTN, BTN_P, ErrorNote, MUTED, Pill, when } from '@/components/packs/parts'

const FIELD = 'w-full rounded-[10px] border border-[var(--fm-line)] bg-white px-3 py-2 text-sm text-[var(--fm-ink)] focus:border-[var(--fm-ink)] focus:outline-none'
const EMPTY: SystemTargetBody = { kind: 'openai', url: '', model: '', systemPrompt: '', intendedUse: '', authHeader: '', requestTemplate: '', responsePath: '' }

function Field({ id, label, help, children }: { id: string; label: string; help?: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-[13px] font-semibold text-[var(--fm-ink)]">{label}</label>
      {children}
      {help && <span className={`text-xs ${MUTED}`}>{help}</span>}
    </div>
  )
}

/** How FairMind calls this AI system for behaviour tests: the endpoint, its auth, its system prompt and intended use. */
export function TargetPanel({ systemId }: { systemId: string }) {
  const saved = useSystemTarget(systemId)
  const { saveTarget, deleteTarget, testTarget } = usePackActions()
  const t = saved.data?.target ?? null
  const [form, setForm] = useState<SystemTargetBody>(EMPTY)
  const [authValue, setAuthValue] = useState('')
  const [busy, setBusy] = useState<'save' | 'test' | 'remove' | null>(null)
  const [failure, setFailure] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  useEffect(() => {
    if (t)
      setForm({
        kind: t.kind,
        url: t.url,
        model: t.model ?? '',
        systemPrompt: t.systemPrompt ?? '',
        intendedUse: t.intendedUse ?? '',
        authHeader: t.authHeader ?? '',
        requestTemplate: t.requestTemplate ?? '',
        responsePath: t.responsePath ?? '',
      })
  }, [t])

  const set = (k: keyof SystemTargetBody) => (e: { target: { value: string } }) => setForm((f) => ({ ...f, [k]: e.target.value }))
  const http = form.kind === 'http'

  async function act(kind: 'save' | 'test' | 'remove') {
    setBusy(kind)
    setFailure(null)
    setNotice(null)
    if (kind === 'save') {
      const res = await saveTarget(systemId, { ...form, ...(authValue.trim() ? { authValue: authValue.trim() } : {}) })
      if (res.error) setFailure(res.error)
      else {
        setAuthValue('')
        setNotice('Saved. The auth value is encrypted and is never shown again.')
      }
    } else if (kind === 'test') {
      const res = await testTarget(systemId)
      if (res.error || !res.data) setFailure(res.error)
      else if (!res.data.ok) setFailure(res.data.message)
      else setNotice(`The system answered in ${res.data.latencyMs} ms: ${res.data.answer}`)
    } else {
      const res = await deleteTarget(systemId)
      if (res.error) setFailure(res.error)
      else {
        setForm(EMPTY)
        setNotice('Removed. Behaviour tests cannot call this system until it is connected again.')
      }
    }
    setBusy(null)
    saved.reload()
  }

  return (
    <div id="target" className="grid min-w-0 gap-4 rounded-[12px] border border-[var(--fm-line)] bg-[var(--fm-bg)] p-4 sm:col-span-2 xl:col-span-3">
      <div className="flex flex-wrap items-center gap-2.5">
        <div className="text-[13.5px] font-semibold">Connection for behaviour tests</div>
        {t ? (
          t.testedOk === true ? <Pill tone="done" dot>Answered {t.testedAt ? when(t.testedAt) : ''}</Pill>
          : t.testedOk === false ? <Pill tone="warn" dot>Test failed</Pill>
          : <Pill dot>Saved, not tested</Pill>
        ) : (
          <Pill dot>Not connected</Pill>
        )}
      </div>
      <p className={`m-0 text-[12.5px] leading-snug ${MUTED}`}>
        Behaviour tests such as prompt injection, jailbreak and over-refusal send prompts to this system and have your organisation&apos;s AI provider judge the answers. The endpoint must be public https.
      </p>
      {saved.error && <ErrorNote message={saved.error} onRetry={saved.reload} />}
      {t && !t.authReadable && <ErrorNote message="The saved auth value can no longer be read. Enter it again and save." />}
      <form
        className="grid gap-3.5 lg:grid-cols-2"
        onSubmit={(e) => {
          e.preventDefault()
          act('save')
        }}
      >
        <Field id="target-kind" label="Kind">
          <select id="target-kind" value={form.kind} onChange={set('kind')} className={FIELD}>
            <option value="openai">OpenAI-compatible chat endpoint</option>
            <option value="http">HTTP endpoint, JSON in and out</option>
          </select>
        </Field>
        <Field id="target-url" label={http ? 'Endpoint URL' : 'Base URL'} help={http ? 'FairMind POSTs the request body here.' : 'The API root, ending in /v1. FairMind calls /chat/completions under it.'}>
          <input id="target-url" value={form.url} onChange={set('url')} placeholder="https://" className={FIELD} required />
        </Field>
        {!http && (
          <Field id="target-model" label="Model" help="The model name the endpoint expects.">
            <input id="target-model" value={form.model} onChange={set('model')} className={FIELD} required />
          </Field>
        )}
        {http && (
          <Field id="target-header" label="Auth header" help="The header the auth value goes in. Empty means Authorization.">
            <input id="target-header" value={form.authHeader} onChange={set('authHeader')} className={FIELD} />
          </Field>
        )}
        <Field
          id="target-auth"
          label={http ? 'Auth value' : 'API key'}
          help={t?.hasAuth ? `Saved (${t.authHint}). Leave empty to keep it.` : http ? 'Sent as the header value exactly as entered, for example Bearer and the token.' : 'Sent as a bearer token. Optional.'}
        >
          <input id="target-auth" type="password" autoComplete="off" value={authValue} onChange={(e) => setAuthValue(e.target.value)} className={FIELD} />
        </Field>
        {http && (
          <>
            <Field id="target-template" label="Request body" help="JSON with {{prompt}} where the prompt goes.">
              <textarea id="target-template" rows={3} value={form.requestTemplate} onChange={set('requestTemplate')} className={`${FIELD} font-mono`} required />
            </Field>
            <Field id="target-path" label="Answer path" help="Where the answer is in the JSON response, as a dot path such as data.answer or choices.0.message.content. Empty for a plain-text response.">
              <input id="target-path" value={form.responsePath} onChange={set('responsePath')} className={FIELD} />
            </Field>
          </>
        )}
        <Field
          id="target-system-prompt"
          label="System prompt"
          help={http ? 'Only used to detect system prompt leakage; your endpoint keeps its own.' : 'Sent with every probe, and used to detect system prompt leakage.'}
        >
          <textarea id="target-system-prompt" rows={4} value={form.systemPrompt} onChange={set('systemPrompt')} className={FIELD} />
        </Field>
        <Field id="target-use" label="Intended use" help="What the system is for and who uses it. The judge writes probes from this when you do not upload a probe set.">
          <textarea id="target-use" rows={4} value={form.intendedUse} onChange={set('intendedUse')} className={FIELD} />
        </Field>
        <div className="flex flex-wrap gap-2 lg:col-span-2">
          <button type="submit" className={BTN_P} disabled={!!busy || !form.url.trim()}>{busy === 'save' ? 'Saving' : 'Save'}</button>
          <button type="button" className={BTN} disabled={!!busy || !t} onClick={() => act('test')}>{busy === 'test' ? 'Testing' : 'Test the saved connection'}</button>
          {t && <button type="button" className={BTN} disabled={!!busy} onClick={() => act('remove')}>Remove</button>}
        </div>
      </form>
      {failure && <ErrorNote message={failure} />}
      {notice && <p className={`m-0 text-[12.5px] ${MUTED}`} role="status">{notice}</p>}
    </div>
  )
}
