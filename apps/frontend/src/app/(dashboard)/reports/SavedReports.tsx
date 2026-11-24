import Link from 'next/link'
import { useRef, useState } from 'react'
import { ArrowRight, FileText } from 'lucide-react'
import { Button } from '@astryxdesign/core/Button'
import { Heading, Text } from '@astryxdesign/core/Text'
import { Input } from '@/components/ui/input'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { isReportDefinition, reportHref, type ReportDefinition } from '@/lib/assurance/reportDefinitions'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import { useOrgResource } from '@/lib/api/hooks/usePacks'

export function SavedReports({ systemId }: { systemId: string }) {
  const { systems, loading: systemsLoading } = useSystemContext()
  const { data, loading, error, reload } = useOrgResource<ReportDefinition[]>(API_ENDPOINTS.aiGovernance.systemAssuranceDefinitions)
  const [query, setQuery] = useState('')
  const searchField = useRef<HTMLInputElement>(null)
  const systemNames = new Map(systems.filter((system) => system.metadata?.source !== 'fallback').map(({ id, name }) => [id, name]))
  const valid = Array.isArray(data) && data.every(isReportDefinition)
  const definitions = valid ? data.filter((report) => !systemId || report.systemId === systemId) : []
  const term = query.trim().toLocaleLowerCase()
  const results = definitions.filter((report) =>
    report.title.toLocaleLowerCase().includes(term) || systemNames.get(report.systemId)?.toLocaleLowerCase().includes(term),
  )
  const unavailable = Boolean(error) || (!loading && !valid)

  return (
    <section className="fm-card rp-card rp-saved" aria-labelledby="rp-saved-title">
      <header className="rp-saved-header">
        <Heading level={2} id="rp-saved-title">Saved reports</Heading>
        {definitions.length > 0 && !unavailable && (
          <label className="rp-saved-search">
            <Text as="span" type="supporting" color="secondary">Search saved reports</Text>
            <Input ref={searchField} type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Report name or AI system" />
          </label>
        )}
      </header>
      {loading ? <p className="rp-muted" role="status">Loading saved reports…</p>
        : unavailable ? <div className="rp-saved-feedback">
          <p className="rp-muted" role="alert">Saved reports could not be loaded.</p>
          <Button label="Retry saved reports" variant="secondary" size="sm" onClick={reload} />
        </div>
        : !definitions.length ? (
          <p className="rp-muted">{systemId ? 'No saved reports for this system yet.' : 'No saved reports yet.'}{' '}
            Save your setup while preparing a system assurance report to reuse it later.
          </p>
        ) : !results.length ? <div className="rp-saved-feedback">
          <p className="rp-muted" role="status">No saved reports match your search.</p>
          <Button label="Clear search" variant="secondary" size="sm" onClick={() => {
            setQuery('')
            searchField.current?.focus()
          }} />
        </div> : (
          <ul className="rp-saved-list">
            {results.map((report) => (
              <li key={report.id}>
                <Link href={reportHref(report.systemId, undefined, report.id)}
                  aria-labelledby={`rp-saved-name-${report.id}`} aria-describedby={`rp-saved-system-${report.id}`}>
                  <span className="rp-saved-icon" aria-hidden><FileText size={16} /></span>
                  <span className="rp-saved-copy">
                    <strong id={`rp-saved-name-${report.id}`}>{report.title}</strong>
                    <span id={`rp-saved-system-${report.id}`} className="rp-muted">
                      {systemNames.get(report.systemId) || (systemsLoading ? 'Loading system name…' : 'System name unavailable')}
                    </span>
                  </span>
                  <ArrowRight className="rp-muted" size={15} aria-hidden />
                </Link>
              </li>
            ))}
          </ul>
        )}
    </section>
  )
}
