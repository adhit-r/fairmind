'use client'

import { useId, useRef, useState } from 'react'
import { IconX } from '@tabler/icons-react'

import { BTN, BTN_P, MUTED } from '@/components/packs/parts'
import { cn } from '@/lib/utils'
import type { CollectEvidenceInput } from '@/lib/api/hooks/useEvidence'

type ArtifactKind = 'file' | 'url' | 'attestation' | 'narrative'

interface EvidenceUploaderProps {
  systemId: string
  onCollect: (params: CollectEvidenceInput) => Promise<void>
  onClose: () => void
  /** External URLs are untrusted evidence, offered only when that linking is switched on. */
  externalUrlsEnabled?: boolean
}

const KINDS: Array<{ kind: ArtifactKind; label: string }> = [
  { kind: 'narrative', label: 'Narrative' },
  { kind: 'file', label: 'File upload' },
  { kind: 'url', label: 'External URL' },
  { kind: 'attestation', label: 'Attestation' },
]

const SUGGESTED_TAGS = ['eu-ai-act', 'bias-scan', 'monitoring', 'compliance', 'q1-2026', 'iso-42001', 'nist-rmf']
const SUGGESTED_FOLDERS = ['EU AI Act', 'ISO 42001', 'NIST AI RMF', 'Bias Testing', 'Monitoring', 'Audits']

const FIELD =
  'h-9 w-full rounded-[10px] border border-[rgba(21,23,26,.14)] bg-white px-3 text-[13.5px] outline-none placeholder:text-[var(--fm-ink3)] focus:border-[var(--fm-ink)]'
const LABEL_CLS = 'block text-[12px] font-medium text-[var(--fm-ink2)]'
const SUGGEST = 'rounded-full bg-[var(--fm-bg)] px-2.5 py-1 text-[12px] font-medium text-[var(--fm-ink2)] hover:text-[var(--fm-ink)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--fm-ink)]'

export function EvidenceUploader({ systemId, onCollect, onClose, externalUrlsEnabled = false }: EvidenceUploaderProps) {
  const kinds = externalUrlsEnabled ? KINDS : KINDS.filter((option) => option.kind !== 'url')
  const uid = useId()
  const [kind, setKind] = useState<ArtifactKind>('narrative')
  const [title, setTitle] = useState('')
  const [evidenceType, setEvidenceType] = useState('test_results')
  const [content, setContent] = useState('')
  const [fileUrl, setFileUrl] = useState('')
  const [fileName, setFileName] = useState('')
  const [confidence, setConfidence] = useState(0.8)
  const [tags, setTags] = useState<string[]>([])
  const [tagInput, setTagInput] = useState('')
  const [folder, setFolder] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const addTag = (tag: string) => {
    const t = tag.trim().toLowerCase()
    if (t && !tags.includes(t)) setTags((prev) => [...prev, t])
    setTagInput('')
  }

  const removeTag = (tag: string) => setTags((prev) => prev.filter((t) => t !== tag))

  const handleFileSelect = (file: File) => {
    setFileName(file.name)
    setTitle(file.name)
    // Read as base64 for content
    const reader = new FileReader()
    reader.onload = (e) => {
      const dataUrl = e.target?.result as string
      setContent(dataUrl || '')
    }
    reader.readAsDataURL(file)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    const file = e.dataTransfer.files?.[0]
    if (file) handleFileSelect(file)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setFormError(null)
    try {
      await onCollect({
        systemId,
        type: evidenceType,
        title,
        content: kind === 'file' ? { base64: content, fileName } :
                 kind === 'url' ? { url: fileUrl } :
                 kind === 'attestation' ? { attested: true, note: content } :
                 { text: content },
        confidence,
        tags,
        folder,
        artifactKind: kind,
        fileUrl: kind === 'url' ? fileUrl : '',
        fileName: kind === 'file' ? fileName : '',
      })
      onClose()
    } catch (reason) {
      setFormError(reason instanceof Error ? reason.message : 'The evidence could not be saved')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-5">
      {/* Artifact kind selector */}
      <div role="group" aria-label="Artifact kind" className={cn('grid grid-cols-2 gap-1 rounded-[22px] bg-[#ebebe8] p-1 sm:rounded-full', externalUrlsEnabled ? 'sm:grid-cols-4' : 'sm:grid-cols-3')}>
        {kinds.map(({ kind: k, label }) => (
          <button
            key={k}
            type="button"
            aria-pressed={kind === k}
            onClick={() => setKind(k)}
            className={cn(
              'h-8 whitespace-nowrap rounded-full px-3 text-[12.5px] font-semibold text-[var(--fm-ink2)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--fm-ink)]',
              kind === k && 'bg-white text-[var(--fm-ink)] shadow-[0_1px_2px_rgba(20,20,30,.08)]',
            )}
          >
            {label}
          </button>
        ))}
      </div>

      <div>
        <label className={LABEL_CLS} htmlFor={`${uid}-title`}>Title</label>
        <input
          id={`${uid}-title`}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className={FIELD}
          placeholder="Short name for this evidence artifact"
          autoComplete="off"
          required
        />
      </div>

      <div>
        <label className={LABEL_CLS} htmlFor={`${uid}-type`}>Evidence type</label>
        <input
          id={`${uid}-type`}
          value={evidenceType}
          onChange={(e) => setEvidenceType(e.target.value)}
          className={FIELD}
          placeholder="e.g. bias_test_result, monitoring_snapshot, audit_log"
          autoComplete="off"
          required
        />
      </div>

      {/* Kind-specific content */}
      {kind === 'file' && (
        <div>
          <span className={LABEL_CLS} id={`${uid}-file`}>Upload file</span>
          <button
            type="button"
            aria-labelledby={`${uid}-file ${uid}-file-state`}
            aria-describedby={fileName ? undefined : `${uid}-file-hint`}
            onDragOver={(e) => { e.preventDefault(); setDragActive(true) }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={cn(
              'mt-1 flex w-full flex-col items-center justify-center gap-1 rounded-xl border border-dashed px-4 py-8 text-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--fm-ink)]',
              dragActive ? 'border-[var(--fm-ink)] bg-[var(--fm-bg)]' : 'border-[rgba(21,23,26,.2)] hover:border-[var(--fm-ink)] hover:bg-[var(--fm-bg)]',
            )}
          >
            {fileName ? (
              <span id={`${uid}-file-state`} className="text-[13.5px] font-semibold">{fileName}</span>
            ) : (
              <>
                <span id={`${uid}-file-state`} className="text-[13.5px] font-semibold">Drop a file here or click to browse</span>
                <span id={`${uid}-file-hint`} className={cn('text-[12px]', MUTED)}>PDF, DOCX, JSON, CSV, PNG, JPG</span>
              </>
            )}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            tabIndex={-1}
            aria-hidden
            className="hidden"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFileSelect(f) }}
          />
        </div>
      )}

      {kind === 'url' && (
        <div>
          <label className={LABEL_CLS} htmlFor={`${uid}-url`}>External URL</label>
          <input
            id={`${uid}-url`}
            value={fileUrl}
            onChange={(e) => setFileUrl(e.target.value)}
            type="url"
            className={FIELD}
            placeholder="https://..."
            autoComplete="off"
            required
          />
          <p className={cn('m-0 mt-1.5 text-[12px]', MUTED)}>Link to evidence stored in another system (for example S3, Confluence or Google Drive).</p>
        </div>
      )}

      {(kind === 'narrative' || kind === 'attestation') && (
        <div>
          <label className={LABEL_CLS} htmlFor={`${uid}-content`}>
            {kind === 'attestation' ? 'Attestation note' : 'Evidence content'}
          </label>
          <textarea
            id={`${uid}-content`}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={5}
            className="w-full resize-y rounded-[10px] border border-[rgba(21,23,26,.14)] bg-white p-3 font-mono text-[13px] outline-none placeholder:text-[var(--fm-ink3)] focus:border-[var(--fm-ink)]"
            placeholder={
              kind === 'attestation'
                ? 'Describe what was manually verified and confirmed...'
                : 'Paste JSON, test output, or a narrative description...'
            }
          />
        </div>
      )}

      {/* Tags */}
      <div>
        <label className={LABEL_CLS} htmlFor={`${uid}-tag`}>Tags</label>
        <div className="flex gap-2">
          <input
            id={`${uid}-tag`}
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ',') { e.preventDefault(); addTag(tagInput) }
            }}
            className={FIELD}
            placeholder="Type a tag and press Enter"
            autoComplete="off"
          />
          <button type="button" className={cn(BTN, 'h-9 px-4 text-[12.5px]')} onClick={() => addTag(tagInput)}>
            Add
          </button>
        </div>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {SUGGESTED_TAGS.filter((t) => !tags.includes(t)).map((t) => (
            <button key={t} type="button" className={SUGGEST} onClick={() => addTag(t)}>
              + {t}
            </button>
          ))}
        </div>
        {tags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {tags.map((tag) => (
              <span key={tag} className="inline-flex items-center gap-1 rounded-full bg-[var(--fm-ink)] py-1 pl-3 pr-1.5 text-[12px] font-medium text-white">
                {tag}
                <button
                  type="button"
                  aria-label={`Remove tag ${tag}`}
                  onClick={() => removeTag(tag)}
                  className="grid h-5 w-5 place-items-center rounded-full hover:bg-white/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
                >
                  <IconX className="h-3 w-3" aria-hidden />
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Folder */}
      <div>
        <label className={LABEL_CLS} htmlFor={`${uid}-folder`}>Folder (optional)</label>
        <input
          id={`${uid}-folder`}
          value={folder}
          onChange={(e) => setFolder(e.target.value)}
          className={FIELD}
          placeholder="e.g. EU AI Act, Monitoring, Q1 2026"
          autoComplete="off"
        />
        <div className="mt-2 flex flex-wrap gap-1.5">
          {SUGGESTED_FOLDERS.filter((f) => f !== folder).map((f) => (
            <button key={f} type="button" className={SUGGEST} onClick={() => setFolder(f)}>
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Confidence */}
      <div>
        <div className="flex items-center justify-between">
          <label className={LABEL_CLS} htmlFor={`${uid}-confidence`}>Confidence</label>
          <span className="text-[13px] font-semibold tabular-nums">{Math.round(confidence * 100)}%</span>
        </div>
        <input
          id={`${uid}-confidence`}
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={confidence}
          onChange={(e) => setConfidence(parseFloat(e.target.value))}
          className="mt-1 w-full cursor-pointer accent-[var(--fm-ink)]"
        />
      </div>

      {formError && (
        <p role="alert" className="m-0 rounded-[10px] bg-[#fde8e8] px-3 py-2 text-[12.5px] text-[#b42318]">{formError}</p>
      )}

      {/* Actions */}
      <div className="flex gap-2.5">
        <button type="submit" className={cn(BTN_P, 'flex-1')} disabled={submitting}>
          {submitting ? 'Saving' : 'Save evidence'}
        </button>
        <button type="button" className={BTN} onClick={onClose}>
          Cancel
        </button>
      </div>
    </form>
  )
}
