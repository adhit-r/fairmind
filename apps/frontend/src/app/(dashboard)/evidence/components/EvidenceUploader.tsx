'use client'

import { useRef, useState } from 'react'
import {
  IconCheck,
  IconCloudUpload,
  IconFileText,
  IconLink,
  IconLoader2,
  IconShieldCheck,
  IconX,
} from '@tabler/icons-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import type { CollectEvidenceInput } from '@/lib/api/hooks/useEvidence'

type ArtifactKind = 'file' | 'url' | 'attestation' | 'narrative'

interface EvidenceUploaderProps {
  systemId: string
  onCollect: (params: CollectEvidenceInput) => Promise<void>
  onClose: () => void
}

const SUGGESTED_TAGS = ['eu-ai-act', 'bias-scan', 'monitoring', 'compliance', 'q1-2026', 'iso-42001', 'nist-rmf']
const SUGGESTED_FOLDERS = ['EU AI Act', 'ISO 42001', 'NIST AI RMF', 'Bias Testing', 'Monitoring', 'Audits']

export function EvidenceUploader({ systemId, onCollect, onClose }: EvidenceUploaderProps) {
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
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Artifact kind selector */}
      <div className="grid grid-cols-4 gap-2">
        {([
          { kind: 'narrative' as ArtifactKind, icon: IconFileText, label: 'Narrative' },
          { kind: 'file' as ArtifactKind, icon: IconCloudUpload, label: 'File upload' },
          { kind: 'url' as ArtifactKind, icon: IconLink, label: 'External URL' },
          { kind: 'attestation' as ArtifactKind, icon: IconShieldCheck, label: 'Attestation' },
        ] as const).map(({ kind: k, icon: Icon, label }) => (
          <button
            key={k}
            type="button"
            onClick={() => setKind(k)}
            className={`flex flex-col items-center gap-1.5 rounded-xl border-2 p-3 text-[11px] font-bold uppercase transition-colors ${
              kind === k
                ? 'border-black bg-black text-white'
                : 'border-black bg-white text-black hover:bg-slate-50'
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Title */}
      <div className="space-y-1.5">
        <Label className="font-bold uppercase tracking-wide text-xs">Title</Label>
        <Input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="border-2 border-black font-medium"
          placeholder="Short name for this evidence artifact"
          required
        />
      </div>

      {/* Evidence type */}
      <div className="space-y-1.5">
        <Label className="font-bold uppercase tracking-wide text-xs">Evidence type</Label>
        <Input
          value={evidenceType}
          onChange={(e) => setEvidenceType(e.target.value)}
          className="border-2 border-black font-medium"
          placeholder="e.g. bias_test_result, monitoring_snapshot, audit_log"
          required
        />
      </div>

      {/* Kind-specific content */}
      {kind === 'file' && (
        <div className="space-y-2">
          <Label className="font-bold uppercase tracking-wide text-xs">Upload file</Label>
          <div
            onDragOver={(e) => { e.preventDefault(); setDragActive(true) }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-8 transition-colors ${
              dragActive ? 'border-black bg-slate-100' : 'border-black/40 hover:border-black hover:bg-slate-50'
            }`}
          >
            <IconCloudUpload className="h-8 w-8 text-muted-foreground" />
            {fileName ? (
              <p className="text-sm font-bold">{fileName}</p>
            ) : (
              <>
                <p className="text-sm font-bold">Drop a file here or click to browse</p>
                <p className="text-xs text-muted-foreground">PDF, DOCX, JSON, CSV, PNG, JPG</p>
              </>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFileSelect(f) }}
          />
        </div>
      )}

      {kind === 'url' && (
        <div className="space-y-1.5">
          <Label className="font-bold uppercase tracking-wide text-xs">External URL</Label>
          <Input
            value={fileUrl}
            onChange={(e) => setFileUrl(e.target.value)}
            type="url"
            className="border-2 border-black font-medium"
            placeholder="https://..."
            required
          />
          <p className="text-xs text-muted-foreground">Link to evidence stored in another system (e.g. S3, Confluence, Google Drive)</p>
        </div>
      )}

      {(kind === 'narrative' || kind === 'attestation') && (
        <div className="space-y-1.5">
          <Label className="font-bold uppercase tracking-wide text-xs">
            {kind === 'attestation' ? 'Attestation note' : 'Evidence content'}
          </Label>
          <Textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="min-h-[120px] border-2 border-black font-mono text-sm"
            placeholder={
              kind === 'attestation'
                ? 'Describe what was manually verified and confirmed...'
                : 'Paste JSON, test output, or a narrative description...'
            }
          />
        </div>
      )}

      {/* Tags */}
      <div className="space-y-2">
        <Label className="font-bold uppercase tracking-wide text-xs">Tags</Label>
        <div className="flex gap-2">
          <Input
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') { e.preventDefault(); addTag(tagInput) }
              if (e.key === ',') { e.preventDefault(); addTag(tagInput) }
            }}
            className="border-2 border-black font-medium"
            placeholder="Type a tag and press Enter"
          />
          <Button type="button" variant="neutral" className="border-2 border-black font-bold" onClick={() => addTag(tagInput)}>
            Add
          </Button>
        </div>
        {/* Suggested tags */}
        <div className="flex flex-wrap gap-1.5">
          {SUGGESTED_TAGS.filter((t) => !tags.includes(t)).map((t) => (
            <button key={t} type="button" onClick={() => addTag(t)}>
              <Badge variant="outline" className="cursor-pointer border-2 border-black/30 bg-white px-2 py-0.5 text-[11px] font-bold hover:border-black">
                + {t}
              </Badge>
            </button>
          ))}
        </div>
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {tags.map((tag) => (
              <Badge key={tag} className="border-2 border-black bg-black px-2 py-0.5 text-[11px] font-bold text-white">
                {tag}
                <button type="button" onClick={() => removeTag(tag)} className="ml-1.5">
                  <IconX className="h-2.5 w-2.5" />
                </button>
              </Badge>
            ))}
          </div>
        )}
      </div>

      {/* Folder */}
      <div className="space-y-2">
        <Label className="font-bold uppercase tracking-wide text-xs">Folder (optional)</Label>
        <Input
          value={folder}
          onChange={(e) => setFolder(e.target.value)}
          className="border-2 border-black font-medium"
          placeholder="e.g. EU AI Act, Monitoring, Q1 2026"
        />
        <div className="flex flex-wrap gap-1.5">
          {SUGGESTED_FOLDERS.filter((f) => f !== folder).map((f) => (
            <button key={f} type="button" onClick={() => setFolder(f)}>
              <Badge variant="outline" className="cursor-pointer border-2 border-black/30 bg-white px-2 py-0.5 text-[11px] font-bold hover:border-black">
                {f}
              </Badge>
            </button>
          ))}
        </div>
      </div>

      {/* Confidence */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <Label className="font-bold uppercase tracking-wide text-xs">Confidence</Label>
          <span className="text-sm font-bold">{Math.round(confidence * 100)}%</span>
        </div>
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={confidence}
          onChange={(e) => setConfidence(parseFloat(e.target.value))}
          className="w-full cursor-pointer accent-black"
        />
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <Button
          type="submit"
          className="flex-1 border-2 border-black font-black uppercase"
          disabled={submitting}
        >
          {submitting ? (
            <>
              <IconLoader2 className="mr-2 h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <IconCheck className="mr-2 h-4 w-4" />
              Save evidence
            </>
          )}
        </Button>
        <Button type="button" variant="neutral" className="border-2 border-black font-bold" onClick={onClose}>
          Cancel
        </Button>
      </div>
    </form>
  )
}
