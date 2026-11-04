'use client'

import { useState } from 'react'
import { IconTrash, IconX } from '@tabler/icons-react'

import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { BTN, BTN_P, LABEL, MUTED, Pill } from '@/components/packs/parts'
import { cn } from '@/lib/utils'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useToast } from '@/hooks/use-toast'
import type { Evidence, EvidenceLink, EvidenceUpdateInput } from '@/lib/api/hooks/useEvidence'
import type { ControlAssessment } from '@/lib/api/hooks/useGovernanceAssurance'

interface EvidenceDetailDrawerProps {
  evidence: Evidence | null
  open: boolean
  onClose: () => void
  onUpdate: (id: string, updates: EvidenceUpdateInput) => Promise<Evidence>
  onAddLink: (evidenceId: string, entityType: string, entityId: string) => Promise<EvidenceLink>
  onRemoveLink: (evidenceId: string, linkId: string) => Promise<void>
  controlOptions?: ControlAssessment[]
  /** null while the role is still loading: no edit controls and no read-only note. */
  canEdit?: boolean | null
}

const STATUS_OPTIONS = [
  { value: 'draft', label: 'Draft' },
  { value: 'submitted', label: 'Submitted' },
  { value: 'accepted', label: 'Accepted' },
  { value: 'rejected', label: 'Rejected' },
]

const ENTITY_TYPES = [
  { value: 'control', label: 'Framework control' },
  { value: 'policy', label: 'Policy' },
  { value: 'incident', label: 'Incident' },
  { value: 'remediation', label: 'Remediation task' },
]

const SMALL = 'h-8 px-3.5 text-[12.5px]'
const FIELD =
  'h-9 w-full rounded-[10px] border border-[rgba(21,23,26,.14)] bg-white px-3 text-[13.5px] outline-none placeholder:text-[var(--fm-ink3)] focus:border-[var(--fm-ink)]'
const FIELD_LABEL = 'block text-[12px] font-medium text-[var(--fm-ink2)]'
const PANEL = 'rounded-xl bg-[var(--fm-bg)] p-3.5'

function formatDate(ts: string) {
  if (!ts) return 'Unknown'
  const d = new Date(ts)
  return Number.isNaN(d.getTime()) ? ts : d.toLocaleString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export function EvidenceDetailDrawer({
  evidence,
  open,
  onClose,
  onUpdate,
  onAddLink,
  onRemoveLink,
  controlOptions = [],
  canEdit = false,
}: EvidenceDetailDrawerProps) {
  const { toast } = useToast()
  const [editMode, setEditMode] = useState(false)
  const [saving, setSaving] = useState(false)

  // Edit state
  const [editTitle, setEditTitle] = useState('')
  const [editStatus, setEditStatus] = useState('')
  const [editFolder, setEditFolder] = useState('')
  const [editTagInput, setEditTagInput] = useState('')
  const [editTags, setEditTags] = useState<string[]>([])

  // Link add state
  const [addingLink, setAddingLink] = useState(false)
  const [linkEntityType, setLinkEntityType] = useState('control')
  const [linkEntityId, setLinkEntityId] = useState('')
  const [controlQuery, setControlQuery] = useState('')
  const [linkSaving, setLinkSaving] = useState(false)

  const startEdit = () => {
    if (!evidence) return
    setEditTitle(evidence.title || evidence.type)
    setEditStatus(evidence.status || 'draft')
    setEditFolder(evidence.folder || '')
    setEditTags(evidence.tags || [])
    setEditMode(true)
  }

  const cancelEdit = () => {
    setEditMode(false)
  }

  const saveEdit = async () => {
    if (!evidence) return
    setSaving(true)
    try {
      await onUpdate(evidence.id, {
        title: editTitle,
        status: editStatus,
        folder: editFolder,
        tags: editTags,
      })
      setEditMode(false)
      toast({ title: 'Evidence updated', description: 'Changes saved successfully.' })
    } catch {
      toast({ title: 'Save failed', description: 'Could not update evidence.', variant: 'destructive' })
    } finally {
      setSaving(false)
    }
  }

  const addEditTag = (tag: string) => {
    const t = tag.trim().toLowerCase()
    if (t && !editTags.includes(t)) setEditTags((prev) => [...prev, t])
    setEditTagInput('')
  }

  const handleAddLink = async () => {
    if (!evidence || !linkEntityId.trim()) return
    setLinkSaving(true)
    try {
      await onAddLink(evidence.id, linkEntityType, linkEntityId.trim())
      setLinkEntityId('')
      setControlQuery('')
      setAddingLink(false)
      toast({ title: 'Link added', description: `Linked to ${linkEntityType}: ${linkEntityId}` })
    } catch {
      toast({ title: 'Link failed', description: 'Could not add link.', variant: 'destructive' })
    } finally {
      setLinkSaving(false)
    }
  }

  const handleRemoveLink = async (link: EvidenceLink) => {
    if (!evidence) return
    try {
      await onRemoveLink(evidence.id, link.id)
      toast({ title: 'Link removed' })
    } catch {
      toast({ title: 'Remove failed', variant: 'destructive' })
    }
  }

  if (!evidence) return null

  const displayTitle = evidence.title || evidence.type
  const matchingControls = controlOptions.filter((control) => {
    const query = controlQuery.trim().toLowerCase()
    return !query || `${control.externalId} ${control.title}`.toLowerCase().includes(query)
  }).slice(0, 8)

  return (
    <Sheet open={open} onOpenChange={(o) => { if (!o) onClose() }}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-lg">
        <SheetHeader className="border-b border-[var(--fm-line)] pb-4 text-left">
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <SheetTitle className="text-[20px] font-semibold leading-tight tracking-tight">
                {displayTitle}
              </SheetTitle>
              <SheetDescription>
                Evidence details and scoped governance links for {displayTitle}.
              </SheetDescription>
              <div className="flex flex-wrap items-center gap-1.5">
                <Pill>{evidence.type}</Pill>
                {evidence.stale && <Pill tone="warn">Potentially stale</Pill>}
                <Pill tone={evidence.status === 'accepted' ? 'done' : evidence.status === 'rejected' ? 'block' : 'plain'}>
                  {evidence.status || 'draft'}
                </Pill>
              </div>
            </div>
            {!editMode && canEdit && (
              <button type="button" className={cn(BTN, SMALL, 'shrink-0')} onClick={startEdit}>
                Edit
              </button>
            )}
          </div>
        </SheetHeader>

        <div className="space-y-5 pt-5">
          {/* Edit mode */}
          {editMode ? (
            <div className={cn('grid gap-4', PANEL, 'p-4')}>
              <div>
                <label className={FIELD_LABEL} htmlFor="evidence-edit-title">Title</label>
                <input id="evidence-edit-title" value={editTitle} onChange={(e) => setEditTitle(e.target.value)} className={FIELD} autoComplete="off" />
              </div>
              <div>
                <span className={FIELD_LABEL} id="evidence-edit-status-label">Status</span>
                <Select value={editStatus} onValueChange={setEditStatus}>
                  <SelectTrigger aria-labelledby="evidence-edit-status-label" className="h-9 rounded-[10px] border border-[rgba(21,23,26,.14)] bg-white text-[13.5px] font-medium">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {STATUS_OPTIONS.map((o) => (
                      <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className={FIELD_LABEL} htmlFor="evidence-edit-folder">Folder</label>
                <input id="evidence-edit-folder" value={editFolder} onChange={(e) => setEditFolder(e.target.value)} className={FIELD} placeholder="e.g. EU AI Act" autoComplete="off" />
              </div>
              <div>
                <label className={FIELD_LABEL} htmlFor="evidence-edit-tag">Tags</label>
                <div className="flex gap-2">
                  <input
                    id="evidence-edit-tag"
                    value={editTagInput}
                    onChange={(e) => setEditTagInput(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addEditTag(editTagInput) } }}
                    className={FIELD}
                    placeholder="Add tag"
                    autoComplete="off"
                  />
                  <button type="button" className={cn(BTN, SMALL, 'h-9')} onClick={() => addEditTag(editTagInput)}>
                    Add
                  </button>
                </div>
                {editTags.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {editTags.map((tag) => (
                      <span key={tag} className="inline-flex items-center gap-1 rounded-full bg-[var(--fm-ink)] py-1 pl-3 pr-1.5 text-[12px] font-medium text-white">
                        {tag}
                        <button
                          type="button"
                          aria-label={`Remove tag ${tag}`}
                          onClick={() => setEditTags((prev) => prev.filter((t) => t !== tag))}
                          className="grid h-5 w-5 place-items-center rounded-full hover:bg-white/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
                        >
                          <IconX className="h-3 w-3" aria-hidden />
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <button type="button" className={cn(BTN_P, SMALL)} onClick={saveEdit} disabled={saving}>
                  {saving ? 'Saving' : 'Save changes'}
                </button>
                <button type="button" className={cn(BTN, SMALL)} onClick={cancelEdit}>
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* Provenance */}
              <section className="space-y-3">
                <p className={cn('m-0', LABEL)}>Provenance</p>
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-xl bg-[var(--fm-bg)] p-3.5">
                    <p className={cn('m-0', LABEL)}>Captured</p>
                    <p className="m-0 mt-1 text-[13px] font-medium">{formatDate(evidence.capturedAt || evidence.timestamp)}</p>
                  </div>
                  <div className="rounded-xl bg-[var(--fm-bg)] p-3.5">
                    <p className={cn('m-0', LABEL)}>Confidence</p>
                    <p className="m-0 mt-1 text-[13px] font-medium tabular-nums">{Math.round(evidence.confidence * 100)}%</p>
                  </div>
                  {evidence.uploadedBy && (
                    <div className="col-span-2 rounded-xl bg-[var(--fm-bg)] p-3.5">
                      <p className={cn('m-0', LABEL)}>Uploaded by</p>
                      <p className="m-0 mt-1 text-[13px] font-medium">{evidence.uploadedBy}</p>
                    </div>
                  )}
                  {evidence.source && (
                    <div className="col-span-2 rounded-xl bg-[var(--fm-bg)] p-3.5">
                      <p className={cn('m-0', LABEL)}>Source</p>
                      <p className="m-0 mt-1 text-[13px] font-medium">{evidence.source}</p>
                    </div>
                  )}
                </div>
              </section>

              {/* Artifact */}
              {evidence.artifactKind === 'file' && evidence.fileName && (
                <section className="grid gap-2">
                  <p className={cn('m-0', LABEL)}>File artifact</p>
                  <div className={PANEL}>
                    <p className="m-0 truncate text-[13.5px] font-semibold">{evidence.fileName}</p>
                    {evidence.fileSize > 0 && (
                      <p className={cn('m-0 mt-0.5 text-[12px]', MUTED)}>{(evidence.fileSize / 1024).toFixed(1)} KB</p>
                    )}
                  </div>
                </section>
              )}

              {evidence.artifactKind === 'url' && evidence.fileUrl && (
                <section className="grid gap-2">
                  <p className={cn('m-0', LABEL)}>External artifact</p>
                  <a
                    href={evidence.fileUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={cn(PANEL, 'block truncate text-[13.5px] font-medium underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--fm-ink)]')}
                  >
                    {evidence.fileUrl}
                  </a>
                </section>
              )}

              {evidence.artifactKind === 'attestation' && (
                <section className="grid gap-2">
                  <p className={cn('m-0', LABEL)}>Attestation</p>
                  <div className={PANEL}>
                    <p className="m-0 text-[13.5px] font-semibold">Manually confirmed</p>
                    <p className={cn('m-0 mt-0.5 text-[12px]', MUTED)}>A person attested to this artifact; no automated check backs it.</p>
                  </div>
                </section>
              )}

              {/* Folder */}
              {evidence.folder && (
                <section className="flex items-center gap-2">
                  <p className={cn('m-0', LABEL)}>Folder</p>
                  <Pill>{evidence.folder}</Pill>
                </section>
              )}

              {/* Tags */}
              {evidence.tags && evidence.tags.length > 0 && (
                <section className="grid gap-2">
                  <p className={cn('m-0', LABEL)}>Tags</p>
                  <div className="flex flex-wrap gap-1.5">
                    {evidence.tags.map((tag) => <Pill key={tag}>{tag}</Pill>)}
                  </div>
                </section>
              )}
            </>
          )}

          {/* Stale warning */}
          {evidence.stale && (
            <div className="rounded-xl bg-[#fff4d6] p-4">
              <p className="m-0 text-[13.5px] font-semibold text-[#8a5a00]">Potentially stale evidence</p>
              <p className="m-0 mt-0.5 text-[12.5px] text-[#8a5a00]">
                This artifact is more than 90 days old. Consider refreshing it before a governance review.
              </p>
            </div>
          )}

          {/* Cross-entity links */}
          <section className="grid gap-3">
            <div className="flex items-center justify-between gap-2">
              <p className={cn('m-0', LABEL)}>
                Linked entities ({evidence.linkedEntityCount})
              </p>
              {canEdit ? (
                <button type="button" className={cn(BTN, SMALL)} onClick={() => setAddingLink((v) => !v)}>
                  Link entity
                </button>
              ) : canEdit === false ? (
                <span className={cn('text-[12px] font-medium', MUTED)}>Read-only</span>
              ) : null}
            </div>

            {addingLink && (
              <div className={cn('grid gap-3', PANEL, 'p-4')}>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <span className={FIELD_LABEL} id="evidence-link-type-label">Entity type</span>
                    <Select value={linkEntityType} onValueChange={setLinkEntityType}>
                      <SelectTrigger aria-labelledby="evidence-link-type-label" className="h-9 rounded-[10px] border border-[rgba(21,23,26,.14)] bg-white text-[13.5px] font-medium">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {ENTITY_TYPES.map((o) => (
                          <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  {linkEntityType === 'control' ? (
                    <div>
                      <label htmlFor="framework-control-search" className={FIELD_LABEL}>Search framework controls</label>
                      <input
                        id="framework-control-search"
                        type="search"
                        value={controlQuery}
                        onChange={(event) => {
                          setControlQuery(event.target.value)
                          setLinkEntityId('')
                        }}
                        className={FIELD}
                        placeholder="Search control ID or title"
                        autoComplete="off"
                      />
                    </div>
                  ) : (
                    <div>
                      <label htmlFor="evidence-link-entity-id" className={FIELD_LABEL}>Entity ID</label>
                      <input
                        id="evidence-link-entity-id"
                        value={linkEntityId}
                        onChange={(e) => setLinkEntityId(e.target.value)}
                        className={cn(FIELD, 'font-mono')}
                        placeholder="ID or reference"
                        autoComplete="off"
                        onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); void handleAddLink() } }}
                      />
                    </div>
                  )}
                </div>
                {linkEntityType === 'control' ? (
                  <div className="max-h-48 overflow-y-auto rounded-[10px] border border-[var(--fm-line)] bg-white">
                    {matchingControls.length > 0 ? matchingControls.map((control) => (
                      <button
                        key={control.id}
                        type="button"
                        aria-label={`Select ${control.externalId} ${control.title}`}
                        aria-pressed={linkEntityId === control.id}
                        onClick={() => {
                          setLinkEntityId(control.id)
                          setControlQuery(`${control.externalId} — ${control.title}`)
                        }}
                        className={cn(
                          'block w-full border-t border-[var(--fm-line)] px-3 py-2 text-left text-[13px] first:border-t-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[var(--fm-ink)]',
                          linkEntityId === control.id ? 'bg-[var(--fm-bg)] font-semibold' : 'hover:bg-[var(--fm-bg)]',
                        )}
                      >
                        {control.externalId} — {control.title}
                      </button>
                    )) : (
                      <p className={cn('m-0 p-3 text-[12.5px]', MUTED)}>No assigned controls match this search.</p>
                    )}
                  </div>
                ) : null}
                <div className="flex gap-2">
                  <button type="button" className={cn(BTN_P, SMALL)} onClick={handleAddLink} disabled={linkSaving || !linkEntityId.trim()}>
                    {linkSaving ? 'Adding' : 'Add link'}
                  </button>
                  <button type="button" className={cn(BTN, SMALL)} onClick={() => setAddingLink(false)}>
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {evidence.linkedEntities.length === 0 ? (
              <div className="rounded-xl border border-dashed border-[rgba(21,23,26,.16)] px-4 py-6 text-center">
                <p className="m-0 text-[13px] font-semibold">No linked entities yet</p>
                <p className={cn('m-0 mt-0.5 text-[12.5px]', MUTED)}>
                  Link this evidence to a control, policy, or incident.
                </p>
              </div>
            ) : (
              <div className="rounded-xl border border-[var(--fm-line)]">
                {evidence.linkedEntities.map((link) => (
                  <div key={link.id} className="flex items-center gap-3 border-t border-[var(--fm-line)] px-3.5 py-3 first:border-t-0">
                    <div className="min-w-0 flex-1">
                      <p className={cn('m-0 text-[12px] font-semibold capitalize', MUTED)}>{link.entityType}</p>
                      <p className="m-0 mt-0.5 truncate text-[13.5px] font-medium">
                        {link.entityType === 'control'
                          ? (() => {
                              const control = controlOptions.find((item) => item.id === link.entityId)
                              return control ? `${control.externalId} — ${control.title}` : link.entityId
                            })()
                          : link.entityId}
                      </p>
                    </div>
                    {canEdit ? (
                      <button
                        type="button"
                        aria-label={`Remove link to ${link.entityType}`}
                        onClick={() => void handleRemoveLink(link)}
                        className="grid h-8 w-8 shrink-0 place-items-center rounded-full text-[var(--fm-ink2)] hover:bg-[var(--fm-bg)] hover:text-[#b42318] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--fm-ink)]"
                      >
                        <IconTrash className="h-4 w-4" aria-hidden />
                      </button>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      </SheetContent>
    </Sheet>
  )
}
