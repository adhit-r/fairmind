'use client'

import { useState } from 'react'
import { Button } from '@astryxdesign/core/Button'
import { Drawer } from '@astryxdesign/core/Drawer'
import { Heading } from '@astryxdesign/core/Text'
import { LIBRARY, briefingText, downloadSealed, useReportCalls, type Format, type Scope } from './api'
import type { ReportModel, Role, SealedReport } from './types'
import { Card, shortHash, when } from './parts'

type Item = (typeof LIBRARY)[Role][number]

const Thumb = () => (
  <div className="rp-thumb" aria-hidden="true">
    <i className="h" />
    <i style={{ width: '90%' }} />
    <i style={{ width: '75%' }} />
    <div className="bars">{[40, 55, 48, 70, 62, 85].map((h, k) => <u key={k} style={{ height: `${h}%` }} />)}</div>
    <i style={{ width: '85%' }} />
    <i style={{ width: '60%' }} />
  </div>
)

export function LibraryCard({ role, onPick }: { role: Role; onPick: (item: Item, format: Format) => void }) {
  return (
    <Card span={12} title="Reports to download" sub="Each one prepares a sealed snapshot of this role and scope.">
      <div className="rp-lib">
        {LIBRARY[role].map((it) => (
          <div className="rp-rep" key={it.key}>
            <Thumb />
            <div>
              <div className="t">{it.name}</div>
              <div className="s">{it.description}</div>
              <div className="rp-fmts">
                {it.formats.map((f) => (
                  <button key={f} type="button" className="rp-fmt" onClick={() => onPick(it, f)} aria-label={`Prepare ${it.name} as ${f}`}>
                    {f}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}

export function DownloadButtons({ report, formats }: { report: SealedReport; formats: Format[] }) {
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState<Format | null>(null)
  return (
    <>
      <div className="rp-fmts">
        {formats.map((f) => (
          <button
            key={f}
            type="button"
            className="rp-fmt"
            disabled={busy !== null}
            aria-label={`Download ${report.title} as ${f}`}
            onClick={async () => {
              setBusy(f)
              setError(await downloadSealed(report, f))
              setBusy(null)
            }}
          >
            {f}
          </button>
        ))}
      </div>
      {error ? <div className="rp-err" role="alert">{error}</div> : null}
    </>
  )
}

export function RecentCard({ role, reports, loading, error }: { role: Role; reports: SealedReport[] | null; loading: boolean; error: string | null }) {
  const mine = (reports ?? []).filter((r) => r.role === role)
  const formats = Array.from(new Set(LIBRARY[role].flatMap((i) => i.formats)))
  return (
    <Card span={12} title="Recently prepared" sub="Sealed reports. Every format comes from the same snapshot, so they always agree.">
      {error ? (
        <p className="rp-err">{error}</p>
      ) : loading ? (
        <p className="rp-muted">Loading</p>
      ) : mine.length === 0 ? (
        <p className="rp-muted">Nothing has been prepared for this role yet.</p>
      ) : (
        <div className="rp-scroll">
          <table className="rp-table">
            <thead>
              <tr><th>Report</th><th>Approved by</th><th>When</th><th>Seal</th><th>Download</th></tr>
            </thead>
            <tbody>
              {mine.map((r) => (
                <tr key={r.id}>
                  <td>{r.title}</td>
                  <td className="rp-muted">{r.approvedBy ?? 'Not recorded'}</td>
                  <td className="rp-muted">{when(r.approvedAt ?? r.createdAt)}</td>
                  <td><span className="rp-mono" title={r.sha256}>{shortHash(r.sha256)}</span></td>
                  <td><DownloadButtons report={r} formats={formats} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  )
}

/** Mounted only while open, so every opening starts fresh. */
export function ReportDrawer({
  item,
  format: first,
  model,
  scopeName,
  onClose,
  onSealed,
}: {
  item: Item
  format: Format
  model: ReportModel
  scopeName: string
  onClose: () => void
  onSealed: () => void
}) {
  const { seal } = useReportCalls()
  const [format, setFormat] = useState<Format>(first)
  const [text, setText] = useState(briefingText(model.briefing))
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sealed, setSealed] = useState<SealedReport | null>(null)
  const withSummary = format !== 'CSV'

  const approve = async () => {
    setBusy(true)
    setError(null)
    const body: Scope & { narrative: string } = {
      role: model.role,
      narrative: withSummary ? text.trim() : '',
      ...(model.scope.systemId ? { system_id: model.scope.systemId } : {}),
      ...(model.framework.key ? { framework: model.framework.key } : {}),
    }
    const r = await seal(body)
    setBusy(false)
    if (r.error || !r.data) return setError(r.error ?? 'The report was not sealed')
    setSealed(r.data)
    onSealed()
  }

  return (
    <Drawer isOpen onOpenChange={(o) => !o && onClose()} label={sealed ? 'Report sealed' : item.name} width={520} padding={5}>
      <div className="rp-drawer">
        <div>
          <Heading level={2}>{sealed ? 'Sealed and ready' : item.name}</Heading>
          <p className="rp-hint">{scopeName} · {model.framework.name ?? 'No framework followed'}</p>
        </div>

        {sealed ? (
          <>
            <div className="rp-done">
              <b>Sealed</b>
              <div className="rp-mono rp-hash">{sealed.sha256}</div>
              <p className="rp-hint">Approved by {sealed.approvedBy ?? 'you'}. The seal is recorded on the ledger.</p>
            </div>
            <div>
              <span className="rp-lbl">Download</span>
              <DownloadButtons report={sealed} formats={item.formats} />
              <p className="rp-hint">Every format comes from this one snapshot, so they always agree.</p>
            </div>
            <div className="rp-actions">
              <Button label="Prepare another" variant="secondary" onClick={() => { setSealed(null); setError(null) }} />
              <Button label="Done" variant="primary" onClick={onClose} />
            </div>
          </>
        ) : (
          <>
            <div>
              <span className="rp-lbl">Format</span>
              <div className="rp-opts" role="group" aria-label="Format">
                {item.formats.map((f) => (
                  <button key={f} type="button" className={`rp-opt${f === format ? ' on' : ''}`} aria-pressed={f === format} onClick={() => setFormat(f)}>
                    {f}
                  </button>
                ))}
              </div>
            </div>
            {withSummary ? (
              <div>
                <label className="rp-lbl" htmlFor="rp-summary">Summary on page one</label>
                <textarea id="rp-summary" className="rp-draft" rows={7} value={text} onChange={(e) => setText(e.target.value)} />
                <p className="rp-hint">Edit freely. This is the text printed on page one.</p>
              </div>
            ) : null}
            {error ? <div className="rp-err" role="alert">{error}</div> : null}
            <div className="rp-actions">
              <span className="rp-hint">Nothing is sealed until you approve</span>
              <Button label={busy ? 'Sealing' : 'Approve and seal'} variant="primary" isDisabled={busy} onClick={() => void approve()} />
            </div>
          </>
        )}
      </div>
    </Drawer>
  )
}
