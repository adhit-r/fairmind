'use client'

import { useEffect, useMemo, useState } from 'react'
import {
  useAIProvider,
  useAIProviders,
  usePackActions,
  type AIProviderBody,
  type AIProviderTest,
} from '@/lib/api/hooks/usePacks'
import { BTN, BTN_P, ErrorNote, LABEL, MUTED, Pill, when } from '@/components/packs/parts'

const FIELD = 'w-full rounded-[10px] border border-[var(--fm-line)] bg-white px-3 py-2 text-sm text-[var(--fm-ink)] focus:border-[var(--fm-ink)] focus:outline-none'
const NEEDS: Record<'baseUrl' | 'endpoint' | 'region', { label: string; placeholder: string; help: string }> = {
  baseUrl: { label: 'Base URL', placeholder: 'https://', help: 'The OpenAI-compatible API root, ending in /v1. It must be public https.' },
  endpoint: { label: 'Endpoint', placeholder: 'https://', help: 'Your Azure OpenAI resource endpoint, from the Azure portal.' },
  region: { label: 'Region', placeholder: 'us-east-1', help: 'The AWS Region your Bedrock API key works in.' },
}

/** Bring your own key: the model the packs agent uses. With none switched on, the agent works by rules. */
export function AIProviderSettings() {
  const providers = useAIProviders()
  const saved = useAIProvider()
  const { saveAIProvider, deleteAIProvider, testAIProvider } = usePackActions()
  const cfg = saved.data?.config ?? null

  const [provider, setProvider] = useState('')
  const [model, setModel] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [fields, setFields] = useState<Record<string, string>>({})
  const [enabled, setEnabled] = useState(true)
  const [busy, setBusy] = useState<'test' | 'save' | 'remove' | null>(null)
  const [test, setTest] = useState<AIProviderTest | null>(null)
  const [failure, setFailure] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  // The form starts from what is saved, or from the first provider.
  useEffect(() => {
    if (cfg) {
      setProvider(cfg.provider)
      setModel(cfg.model)
      setFields({ baseUrl: cfg.baseUrl ?? '', endpoint: cfg.endpoint ?? '', region: cfg.region ?? '' })
      setEnabled(cfg.enabled)
    } else if (providers.data?.length && !provider) {
      setProvider(providers.data[0].id)
      setModel(providers.data[0].default_model)
    }
  }, [cfg, providers.data])

  const option = useMemo(() => providers.data?.find((p) => p.id === provider) ?? null, [providers.data, provider])
  const keySaved = !!cfg?.hasKey && cfg.provider === provider && cfg.keyReadable
  const body = (): AIProviderBody => ({
    provider,
    model: model.trim(),
    enabled,
    ...(apiKey.trim() ? { apiKey: apiKey.trim() } : {}),
    ...Object.fromEntries((option?.needs ?? []).map((n) => [n, (fields[n] ?? '').trim()])),
  })

  function choose(id: string) {
    const next = providers.data?.find((p) => p.id === id)
    setProvider(id)
    setModel(cfg?.provider === id ? cfg.model : next?.default_model ?? '')
    setApiKey('')
    setTest(null)
    setFailure(null)
  }

  async function act(kind: 'test' | 'save' | 'remove') {
    setBusy(kind)
    setFailure(null)
    setNotice(null)
    if (kind === 'test') {
      const res = await testAIProvider(body())
      if (res.error) setFailure(res.error)
      else setTest(res.data)
    } else if (kind === 'save') {
      const res = await saveAIProvider(body())
      if (res.error) setFailure(res.error)
      else {
        setApiKey('')
        setNotice('Saved. The key is encrypted and is never shown again.')
      }
    } else {
      const res = await deleteAIProvider()
      if (res.error) setFailure(res.error)
      else {
        setTest(null)
        setApiKey('')
        setNotice('Removed. The agent now works by rules.')
      }
    }
    setBusy(null)
    saved.reload()
  }

  if (providers.error || saved.error) {
    return <ErrorNote message={`AI provider settings could not be loaded. ${providers.error ?? saved.error ?? ''}`} onRetry={() => (providers.reload(), saved.reload())} />
  }

  const needsKey = option?.key === 'required' && !keySaved && !apiKey.trim()
  const canSubmit = !!option && !busy && !needsKey && (option.needs ?? []).every((n) => (fields[n] ?? '').trim())

  return (
    <section id="ai-provider" className="mt-8 p-8 fm-card">
      <div className="mb-1 flex flex-wrap items-center gap-2.5">
        <h2 className="m-0 text-lg font-semibold text-[var(--fm-ink)]">AI provider for the agent</h2>
        {cfg ? (
          cfg.enabled && cfg.keyReadable ? <Pill tone="done" dot>On: {cfg.providerName}</Pill> : <Pill tone="warn" dot>Off</Pill>
        ) : (
          <Pill dot>Rules only</Pill>
        )}
      </div>
      <p className={`mb-6 mt-2 text-sm leading-normal ${MUTED}`}>
        Bring your own key and the packs agent uses your model to do workflow steps: collecting, checking and drafting. Without one, it works by rules, listing what is on file and what is missing. Every approval still waits for a person, and each step records which model did it.
      </p>

      {cfg && !cfg.keyReadable && (
        <div className="mb-5">
          <ErrorNote message="The saved key can no longer be read. Enter it again and save." />
        </div>
      )}

      <form
        className="flex flex-col gap-5"
        onSubmit={(e) => {
          e.preventDefault()
          act('save')
        }}
      >
        <div className="flex flex-col gap-1.5">
          <label htmlFor="ai-provider-select" className="text-[13px] font-semibold text-[var(--fm-ink)]">Provider</label>
          <select id="ai-provider-select" value={provider} onChange={(e) => choose(e.target.value)} className={FIELD} disabled={providers.loading}>
            {(providers.data ?? []).map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          {option?.docs && (
            <a href={option.docs} target="_blank" rel="noreferrer" className={`text-xs underline ${MUTED}`}>
              Get a key from {option.name}
            </a>
          )}
        </div>

        {(option?.needs ?? []).map((n) => (
          <div key={n} className="flex flex-col gap-1.5">
            <label htmlFor={`ai-${n}`} className="text-[13px] font-semibold text-[var(--fm-ink)]">{NEEDS[n].label}</label>
            <input
              id={`ai-${n}`}
              value={fields[n] ?? ''}
              onChange={(e) => setFields((f) => ({ ...f, [n]: e.target.value }))}
              placeholder={NEEDS[n].placeholder}
              className={FIELD}
              required
            />
            <span className={`text-xs ${MUTED}`}>{NEEDS[n].help}</span>
          </div>
        ))}

        <div className="flex flex-col gap-1.5">
          <label htmlFor="ai-key" className="text-[13px] font-semibold text-[var(--fm-ink)]">
            API key{option?.key === 'optional' ? ' (optional)' : ''}
          </label>
          <input
            id="ai-key"
            type="password"
            autoComplete="off"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder={keySaved ? `Saved key ${cfg?.keyHint ?? ''}. Leave blank to keep it.` : 'Paste the key'}
            className={`${FIELD} font-mono`}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="ai-model" className="text-[13px] font-semibold text-[var(--fm-ink)]">Model</label>
          <input
            id="ai-model"
            list="ai-models"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder={option?.model_hint || 'Test the connection to list models'}
            className={`${FIELD} font-mono`}
          />
          <datalist id="ai-models">
            {(test?.models ?? []).map((m) => (
              <option key={m} value={m} />
            ))}
          </datalist>
          <span className={`text-xs ${MUTED}`}>
            {option?.lists_models === false ? 'This provider does not list its models; type the model ID.' : 'Test the connection to pick from the models this key can use.'}
          </span>
        </div>

        <label className="flex items-center gap-2.5 text-sm text-[var(--fm-ink)]">
          <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} className="h-4 w-4" />
          Let the agent use this provider
        </label>

        {test && (
          <div role="status" className={`rounded-xl px-4 py-3 text-[13px] ${test.ok ? 'bg-[#e3f5ec] text-[#00704e]' : 'bg-[#fde8e8] text-[#b42318]'}`}>
            <b className="font-semibold">{test.ok ? 'Connection works.' : 'Connection failed.'}</b> {test.message}
            {test.ok && test.latencyMs !== null ? ` (${(test.latencyMs / 1000).toFixed(1)} s)` : ''}
          </div>
        )}
        {!test && cfg?.testedAt && cfg.provider === provider && (
          <p className={`m-0 text-xs ${MUTED}`}>
            Last tested {when(cfg.testedAt)}: {cfg.testedOk ? 'worked' : 'failed'}. {cfg.testMessage}
          </p>
        )}
        {failure && <ErrorNote message={failure} />}
        {notice && <p className="m-0 text-[13px] font-medium text-[#00704e]">{notice}</p>}

        <div className="flex flex-wrap gap-2.5">
          <button type="button" className={BTN} disabled={!canSubmit} onClick={() => act('test')}>
            {busy === 'test' ? 'Testing' : 'Test connection'}
          </button>
          <button type="submit" className={BTN_P} disabled={!canSubmit || !model.trim()}>
            {busy === 'save' ? 'Saving' : 'Save'}
          </button>
          {cfg && (
            <button type="button" className={BTN} disabled={!!busy} onClick={() => act('remove')}>
              {busy === 'remove' ? 'Removing' : 'Remove'}
            </button>
          )}
        </div>
        <p className={`m-0 ${LABEL}`}>Only owners and admins can change this.</p>
      </form>
    </section>
  )
}
