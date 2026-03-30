'use client'

import { useState } from 'react'
import {
  IconAlertTriangle,
  IconCheck,
  IconExternalLink,
  IconFileText,
  IconLink,
  IconLoader2,
  IconPencil,
  IconPlus,
  IconShieldCheck,
  IconTag,
  IconTrash,
  IconX,
} from '@tabler/icons-react'

import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useToast } from '@/hooks/use-toast'
import type { Evidence, EvidenceLink, EvidenceUpdateInput } from '@/lib/api/hooks/useEvidence'

interface EvidenceDetailDrawerProps {
  evidence: Evidence | null
  open: boolean
  onClose: () => void
  onUpdate: (id: string, updates: EvidenceUpdateInput) => Promise<Evidence>
  onAddLink: (evidenceId: string, entityType: string, entityId: string) => Promise<EvidenceLink>
  onRemoveLink: (evidenceId: string, linkId: string) => Promise<void>
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

function formatDate(ts: string) {
  if (!ts) return '—'
  const d = new Date(ts)
  return Number.isNaN(d.getTime()) ? ts : d.toLocaleString()
}

export function EvidenceDetailDrawer({
  evidence,
  open,
  onClose,
  onUpdate,
  onAddLink,
  onRemoveLink,
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

  return (
    <Sheet open={open} onOpenChange={(o) => { if (!o) onClose() }}>
      <SheetContent className="w-full overflow-y-auto border-l-4 border-black sm:max-w-lg">
        <SheetHeader className="border-b-2 border-black pb-4">
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <SheetTitle className="text-xl font-black uppercase leading-tight">
                {displayTitle}
              </SheetTitle>
              <div className="flex flex-wrap items-center gap-1.5">
                <Badge className="border-2 border-black bg-black px-2 py-0.5 text-[11px] font-black uppercase text-white">
                  {evidence.type}
                </Badge>
                {evidence.stale && (
                  <Badge className="border-2 border-amber-500 bg-amber-50 px-2 py-0.5 text-[11px] font-black uppercase text-amber-800">
                    <IconAlertTriangle className="mr-1 h-3 w-3" />
                    Potentially stale
                  </Badge>
                )}
                <Badge className={`border-2 border-black px-2 py-0.5 text-[11px] font-bold uppercase ${
                  evidence.status === 'accepted' ? 'bg-emerald-100 text-emerald-800' :
                  evidence.status === 'rejected' ? 'bg-red-100 text-red-800' :
                  'bg-slate-100 text-slate-800'
                }`}>
                  {evidence.status || 'draft'}
                </Badge>
              </div>
            </div>
            {!editMode && (
              <Button size="sm" variant="neutral" className="shrink-0 border-2 border-black font-bold" onClick={startEdit}>
                <IconPencil className="mr-1.5 h-3.5 w-3.5" />
                Edit
              </Button>
            )}
          </div>
        </SheetHeader>

        <div className="space-y-5 pt-5">
          {/* Edit mode */}
          {editMode ? (
            <div className="space-y-4 rounded-xl border-2 border-black bg-slate-50 p-4">
              <div className="space-y-1.5">
                <Label className="text-xs font-bold uppercase">Title</Label>
                <Input value={editTitle} onChange={(e) => setEditTitle(e.target.value)} className="border-2 border-black" />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs font-bold uppercase">Status</Label>
                <Select value={editStatus} onValueChange={setEditStatus}>
                  <SelectTrigger className="border-2 border-black font-bold">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {STATUS_OPTIONS.map((o) => (
                      <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs font-bold uppercase">Folder</Label>
                <Input value={editFolder} onChange={(e) => setEditFolder(e.target.value)} className="border-2 border-black" placeholder="e.g. EU AI Act" />
              </div>
              <div className="space-y-2">
                <Label className="text-xs font-bold uppercase">Tags</Label>
                <div className="flex gap-2">
                  <Input
                    value={editTagInput}
                    onChange={(e) => setEditTagInput(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addEditTag(editTagInput) } }}
                    className="border-2 border-black"
                    placeholder="Add tag"
                  />
                  <Button type="button" variant="neutral" size="sm" className="border-2 border-black font-bold" onClick={() => addEditTag(editTagInput)}>
                    Add
                  </Button>
                </div>
                {editTags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {editTags.map((tag) => (
                      <Badge key={tag} className="border-2 border-black bg-black px-2 py-0.5 text-[11px] font-bold text-white">
                        {tag}
                        <button type="button" onClick={() => setEditTags((prev) => prev.filter((t) => t !== tag))} className="ml-1.5">
                          <IconX className="h-2.5 w-2.5" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <Button size="sm" className="border-2 border-black font-black uppercase" onClick={saveEdit} disabled={saving}>
                  {saving ? <IconLoader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : <IconCheck className="mr-1.5 h-3.5 w-3.5" />}
                  Save changes
                </Button>
                <Button size="sm" variant="neutral" className="border-2 border-black font-bold" onClick={cancelEdit}>
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <>
              {/* Provenance */}
              <section className="space-y-3">
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">Provenance</p>
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-lg border-2 border-black bg-slate-50 p-3">
                    <p className="text-[10px] font-bold uppercase text-muted-foreground">Captured</p>
                    <p className="mt-0.5 text-xs font-semibold">{formatDate(evidence.capturedAt || evidence.timestamp)}</p>
                  </div>
                  <div className="rounded-lg border-2 border-black bg-slate-50 p-3">
                    <p className="text-[10px] font-bold uppercase text-muted-foreground">Confidence</p>
                    <p className="mt-0.5 text-sm font-black">{Math.round(evidence.confidence * 100)}%</p>
                  </div>
                  {evidence.uploadedBy && (
                    <div className="col-span-2 rounded-lg border-2 border-black bg-slate-50 p-3">
                      <p className="text-[10px] font-bold uppercase text-muted-foreground">Uploaded by</p>
                      <p className="mt-0.5 text-xs font-semibold">{evidence.uploadedBy}</p>
                    </div>
                  )}
                  {evidence.source && (
                    <div className="col-span-2 rounded-lg border-2 border-black bg-slate-50 p-3">
                      <p className="text-[10px] font-bold uppercase text-muted-foreground">Source</p>
                      <p className="mt-0.5 text-xs font-semibold">{evidence.source}</p>
                    </div>
                  )}
                </div>
              </section>

              {/* Artifact */}
              {evidence.artifactKind === 'file' && evidence.fileName && (
                <section className="space-y-2">
                  <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">File artifact</p>
                  <div className="flex items-center gap-3 rounded-lg border-2 border-black bg-slate-50 p-3">
                    <IconFileText className="h-5 w-5 shrink-0" />
                    <div className="min-w-0">
                      <p className="truncate text-sm font-bold">{evidence.fileName}</p>
                      {evidence.fileSize > 0 && (
                        <p className="text-xs text-muted-foreground">{(evidence.fileSize / 1024).toFixed(1)} KB</p>
                      )}
                    </div>
                  </div>
                </section>
              )}

              {evidence.artifactKind === 'url' && evidence.fileUrl && (
                <section className="space-y-2">
                  <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">External artifact</p>
                  <a
                    href={evidence.fileUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 rounded-lg border-2 border-black bg-slate-50 p-3 text-sm font-bold hover:bg-slate-100"
                  >
                    <IconExternalLink className="h-4 w-4 shrink-0" />
                    <span className="truncate">{evidence.fileUrl}</span>
                  </a>
                </section>
              )}

              {evidence.artifactKind === 'attestation' && (
                <section className="space-y-2">
                  <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">Attestation</p>
                  <div className="flex items-center gap-2 rounded-lg border-2 border-emerald-500 bg-emerald-50 p-3">
                    <IconShieldCheck className="h-4 w-4 text-emerald-600" />
                    <p className="text-sm font-bold text-emerald-800">Manually confirmed</p>
                  </div>
                </section>
              )}

              {/* Folder */}
              {evidence.folder && (
                <section className="flex items-center gap-2">
                  <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">Folder</p>
                  <Badge variant="outline" className="border-2 border-black px-2 py-0.5 text-[11px] font-bold">
                    {evidence.folder}
                  </Badge>
                </section>
              )}

              {/* Tags */}
              {evidence.tags && evidence.tags.length > 0 && (
                <section className="space-y-2">
                  <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">Tags</p>
                  <div className="flex flex-wrap gap-1.5">
                    {evidence.tags.map((tag) => (
                      <Badge key={tag} className="border-2 border-black bg-black px-2 py-0.5 text-[11px] font-bold text-white">
                        <IconTag className="mr-1 h-2.5 w-2.5" />
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </section>
              )}
            </>
          )}

          {/* Stale warning */}
          {evidence.stale && (
            <div className="rounded-xl border-2 border-amber-400 bg-amber-50 p-4">
              <div className="flex items-start gap-3">
                <IconAlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
                <div>
                  <p className="text-sm font-bold text-amber-800">Potentially stale evidence</p>
                  <p className="mt-0.5 text-xs text-amber-700">
                    This artifact is more than 90 days old. Consider refreshing it before a governance review.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Cross-entity links */}
          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
                Linked entities ({evidence.linkedEntityCount})
              </p>
              <Button
                size="sm"
                variant="neutral"
                className="border-2 border-black text-[11px] font-bold uppercase"
                onClick={() => setAddingLink((v) => !v)}
              >
                <IconPlus className="mr-1 h-3 w-3" />
                Link entity
              </Button>
            </div>

            {addingLink && (
              <div className="space-y-2 rounded-xl border-2 border-black bg-slate-50 p-4">
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <Label className="text-[10px] font-bold uppercase">Entity type</Label>
                    <Select value={linkEntityType} onValueChange={setLinkEntityType}>
                      <SelectTrigger className="border-2 border-black font-bold">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {ENTITY_TYPES.map((o) => (
                          <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-[10px] font-bold uppercase">Entity ID</Label>
                    <Input
                      value={linkEntityId}
                      onChange={(e) => setLinkEntityId(e.target.value)}
                      className="border-2 border-black font-mono text-sm"
                      placeholder="ID or reference"
                      onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); void handleAddLink() } }}
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" className="border-2 border-black font-black uppercase" onClick={handleAddLink} disabled={linkSaving || !linkEntityId.trim()}>
                    {linkSaving ? <IconLoader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : <IconLink className="mr-1.5 h-3.5 w-3.5" />}
                    Add link
                  </Button>
                  <Button size="sm" variant="neutral" className="border-2 border-black font-bold" onClick={() => setAddingLink(false)}>
                    Cancel
                  </Button>
                </div>
              </div>
            )}

            {evidence.linkedEntities.length === 0 ? (
              <div className="rounded-xl border-2 border-dashed border-black/30 bg-slate-50 p-6 text-center">
                <IconLink className="mx-auto h-6 w-6 text-muted-foreground" />
                <p className="mt-2 text-xs font-bold text-muted-foreground">No linked entities yet</p>
                <p className="mt-0.5 text-[11px] text-muted-foreground">
                  Link this evidence to a control, policy, or incident.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {evidence.linkedEntities.map((link) => (
                  <div key={link.id} className="flex items-center gap-3 rounded-lg border-2 border-black bg-white p-3">
                    <div className="flex-1 min-w-0">
                      <p className="text-[10px] font-bold uppercase text-muted-foreground">{link.entityType}</p>
                      <p className="truncate text-sm font-bold font-mono">{link.entityId}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => void handleRemoveLink(link)}
                      className="shrink-0 rounded p-1 text-muted-foreground hover:bg-red-50 hover:text-red-600"
                    >
                      <IconTrash className="h-3.5 w-3.5" />
                    </button>
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
