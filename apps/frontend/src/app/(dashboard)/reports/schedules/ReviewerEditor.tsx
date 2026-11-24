import { useId, useState, type FormEvent } from 'react'
import { Button } from '@/components/ui/button'
import type { Resource } from '@/lib/api/hooks/usePacks'

export type Reviewer = { id: string; name: string }

export function ReviewerEditor({ label, current, reviewers, disabled, onSave }: {
  label: string; current?: Reviewer | null; reviewers: Resource<Reviewer[]>; disabled: boolean
  onSave: (reviewerId: string | null) => Promise<void>
}) {
  const controlId = useId()
  const currentId = current?.id ?? ''
  const [draft, setDraft] = useState<{ from: string; choice: string } | null>(null)
  const choice = draft?.from === currentId ? draft.choice : currentId
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)
  const options = Array.isArray(reviewers.data) ? reviewers.data : []
  const unavailable = Boolean(reviewers.error) || (!reviewers.loading && !Array.isArray(reviewers.data))

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (choice === currentId || disabled || saving || unavailable) return
    setSaving(true)
    setError(null)
    setSaved(false)
    try {
      await onSave(choice || null)
      setSaved(true)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'The reviewer could not be saved.')
    } finally {
      setSaving(false)
    }
  }

  return <form className="rs-reviewer-form" onSubmit={(event) => void save(event)}>
    <div className="rs-reviewer-input">
      <label htmlFor={controlId}>{label}</label>
      <select id={controlId} value={choice} disabled={disabled || saving || reviewers.loading || unavailable}
        onChange={(event) => { setDraft({ from: currentId, choice: event.target.value }); setError(null); setSaved(false) }}>
        <option value="">Unassigned</option>
        {current && !options.some(({ id }) => id === current.id) && <option value={current.id}>{current.name}</option>}
        {options.map(({ id, name }) => <option key={id} value={id}>{name}</option>)}
      </select>
    </div>
    <Button size="sm" type="submit" variant="outline" disabled={disabled || saving || reviewers.loading || unavailable || choice === currentId}>
      {saving ? 'Saving reviewer…' : 'Save reviewer'}
    </Button>
    {reviewers.loading && <p className="rs-reviewer-feedback" role="status">Loading reviewers…</p>}
    {unavailable && <div className="rs-reviewer-feedback rs-state">
      <p role="alert">Reviewers could not be loaded.</p>
      <Button variant="outline" size="sm" type="button" onClick={reviewers.reload}>Retry reviewers</Button>
    </div>}
    {error && <p className="rs-reviewer-feedback" role="alert">{error}</p>}
    {saved && <p className="rs-reviewer-feedback" role="status">Reviewer saved.</p>}
  </form>
}
