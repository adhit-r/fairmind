import type { EvaluationRunV2 } from '@/lib/api/hooks/useEvaluationWorkbenchV2'

import { buildEvidenceTrustPresentation, sentenceLabel } from './evidenceTrust'

function axisClass(label: string, value: string) {
  if (label === 'Governance verdict') {
    if (value === 'Blocked') return 'border-[#D83A2E] bg-[#D83A2E] text-white'
    if (value === 'Approved') return 'border-[#155D46] bg-[#DFF4EA] text-[#155D46]'
    if (value === 'Conditional') return 'border-[#9A5B14] bg-[#FFF1D6] text-[#73420B]'
    if (value === 'Review') return 'border-[#0F1412] bg-[#FF6B35] text-[#0F1412]'
  }
  if (value === 'Failed' || value === 'Error' || value === 'Rejected') return 'border-[#D83A2E] bg-red-50 text-[#8F2019]'
  if (value === 'Passed' || value === 'Succeeded' || value === 'Verified' || value === 'Current' || value === 'Accepted') return 'border-[#155D46] bg-[#DFF4EA] text-[#155D46]'
  if (value === 'Passed with limitations' || value === 'Expiring' || value === 'Review') return 'border-[#9A5B14] bg-[#FFF1D6] text-[#73420B]'
  return 'border-[#59615D] bg-[#F3F5F0] text-[#303834]'
}

function Timestamp({ value }: { value: string | null }) {
  if (!value) return <>Not recorded</>
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return <>{value}</>
  return <>{new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeStyle: 'short' }).format(date)}</>
}

function BindingGrid({
  title,
  rows,
}: {
  title: string
  rows: Array<{ label: string; value: string }>
}) {
  return (
    <section aria-label={title} className="border-2 border-[#0F1412] bg-[#FCFDF8]">
      <h4 className="border-b-2 border-[#0F1412] bg-[#F3F5F0] px-3 py-2 text-sm font-black">{title}</h4>
      <dl className="grid divide-y-2 divide-[#0F1412] sm:grid-cols-2 sm:divide-x-2 sm:divide-y-0">
        {rows.map((item) => (
          <div key={item.label} className="border-b-2 border-[#0F1412] p-3 last:border-b-0 sm:border-b-0 sm:even:border-b-2 lg:even:border-b-0">
            <dt className="text-[11px] font-black uppercase tracking-wide text-[#59615D]">{item.label}</dt>
            <dd className="mt-1 break-all font-mono text-xs font-bold">{item.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}

export function EvidenceTrustPanel({ run }: { run: EvaluationRunV2 }) {
  const presentation = buildEvidenceTrustPresentation(run)
  return (
    <section aria-labelledby="evidence-trust-heading" className="border-4 border-[#0F1412] bg-[#FCFDF8]">
      <div className="border-b-4 border-[#0F1412] p-4 sm:p-5">
        <h2 id="evidence-trust-heading" className="text-lg font-black">Evidence trust state</h2>
        <p className="mt-1 max-w-[72ch] text-sm font-semibold text-[#59615D]">
          Execution, evaluator evidence, and governance remain separate records. A successful run is not a governance approval.
        </p>
      </div>

      <div className="border-b-2 border-[#0F1412] p-4 sm:p-5">
        <h3 className="text-base font-black">Exact execution binding</h3>
        <p className="mt-1 max-w-[72ch] text-sm font-semibold text-[#59615D]">
          These identifiers define which system, target, plan, suite, and execution produced the response. Missing provenance is shown as unavailable.
        </p>
        <div className="mt-3 grid gap-3 lg:grid-cols-3">
          <BindingGrid title="Scope" rows={presentation.binding.scope} />
          <BindingGrid title="Execution" rows={presentation.binding.execution} />
          <BindingGrid title="Target" rows={presentation.binding.target} />
        </div>
        <div className="mt-3 overflow-x-auto border-2 border-[#0F1412]">
          <table aria-label="Exact suite execution bindings" className="w-full min-w-[1180px] border-collapse text-left text-sm">
            <thead className="bg-[#0F1412] text-white">
              <tr>
                <th scope="col" className="px-3 py-3 font-black">Suite execution</th>
                <th scope="col" className="px-3 py-3 font-black">Suite version</th>
                <th scope="col" className="px-3 py-3 font-black">Manifest digest</th>
                <th scope="col" className="px-3 py-3 font-black">Adapter</th>
                <th scope="col" className="px-3 py-3 font-black">Runner image</th>
                <th scope="col" className="px-3 py-3 font-black">Configuration hash</th>
                <th scope="col" className="px-3 py-3 font-black">Passport revision</th>
                <th scope="col" className="px-3 py-3 font-black">Signer</th>
              </tr>
            </thead>
            <tbody>
              {presentation.binding.suites.length === 0 ? (
                <tr className="border-t-2 border-[#0F1412] bg-[#FCFDF8]"><td colSpan={8} className="px-3 py-3 font-semibold text-[#59615D]">No suite bindings are returned by this response.</td></tr>
              ) : presentation.binding.suites.map((suite) => (
                <tr key={suite.suiteExecutionId} className="border-t-2 border-[#0F1412] bg-[#FCFDF8]">
                  <td className="px-3 py-3 font-mono text-xs font-bold">{suite.suiteExecutionId}</td>
                  <td className="px-3 py-3 font-mono text-xs font-bold">{suite.suiteVersionId}</td>
                  <td className="px-3 py-3 font-mono text-xs font-bold">{suite.manifestDigest}</td>
                  <td className="px-3 py-3 font-semibold">{suite.evaluator}</td>
                  <td className="px-3 py-3 font-mono text-xs font-bold">{suite.runnerImageDigest}</td>
                  <td className="px-3 py-3 font-mono text-xs font-bold">{suite.configurationHash}</td>
                  <td className="px-3 py-3 font-semibold text-[#59615D]">{suite.passportRevisionId}</td>
                  <td className="px-3 py-3 font-semibold text-[#59615D]">{suite.signer}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid divide-y-2 divide-[#0F1412] sm:grid-cols-3 sm:divide-x-2 sm:divide-y-0">
        {presentation.axes.map((axis) => (
          <div key={axis.label} className="p-4">
            <p className="text-xs font-black uppercase tracking-wide text-[#59615D]">{axis.label}</p>
            <p className={`mt-2 inline-flex min-h-8 items-center border-2 px-2.5 py-1 text-xs font-black uppercase ${axisClass(axis.label, axis.value)}`}>
              {axis.value}
            </p>
          </div>
        ))}
      </div>

      <dl className="grid border-t-2 border-[#0F1412] bg-[#F3F5F0] text-sm sm:grid-cols-2 lg:grid-cols-4">
        <div className="border-b-2 border-[#0F1412] p-3 sm:border-r-2 lg:border-b-0"><dt className="text-xs font-black uppercase text-[#59615D]">Envelope hash</dt><dd className="mt-1 break-all font-mono text-xs font-bold">{run.envelopeHash}</dd></div>
        <div className="border-b-2 border-[#0F1412] p-3 lg:border-b-0 lg:border-r-2"><dt className="text-xs font-black uppercase text-[#59615D]">Verdict version</dt><dd className="mt-1 font-mono text-xs font-bold">{run.verdictVersion}</dd></div>
        <div className="border-b-2 border-[#0F1412] p-3 sm:border-r-2 lg:border-b-0 lg:border-r-2"><dt className="text-xs font-black uppercase text-[#59615D]">Requested by</dt><dd className="mt-1 break-all font-mono text-xs font-bold">{run.requestedBy}</dd></div>
        <div className="p-3"><dt className="text-xs font-black uppercase text-[#59615D]">Completed</dt><dd className="mt-1 font-bold"><Timestamp value={run.completedAt} /></dd></div>
      </dl>

      <div className="border-t-2 border-[#0F1412] p-4 sm:p-5">
        <h3 className="text-base font-black">Layer verdicts</h3>
        <p className="mt-1 max-w-[72ch] text-sm font-semibold text-[#59615D]">These governance projections remain distinct from the execution and evaluator evidence axes above.</p>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          {[
            { label: 'Suite verdicts', verdicts: run.layerVerdicts.suites },
            { label: 'Modality verdicts', verdicts: run.layerVerdicts.modalities },
            { label: 'Component verdicts', verdicts: run.layerVerdicts.components },
            { label: 'Risk dimension verdicts', verdicts: run.layerVerdicts.riskDimensions },
          ].map(({ label, verdicts }) => {
            const entries = Object.entries(verdicts)
            return (
              <section key={label} aria-label={label} className="border-2 border-[#0F1412] bg-[#F3F5F0]">
                <h4 className="border-b-2 border-[#0F1412] bg-[#FCFDF8] px-3 py-2 text-sm font-black">{label}</h4>
                {entries.length === 0 ? <p className="p-3 text-sm font-semibold text-[#59615D]">Not assessed</p> : <dl className="divide-y-2 divide-[#0F1412]">{entries.map(([name, verdict]) => <div key={name} className="flex items-center justify-between gap-3 px-3 py-2"><dt className="font-semibold">{sentenceLabel(name)}</dt><dd><span className={`inline-flex min-h-8 items-center border-2 px-2 py-1 text-xs font-black uppercase ${axisClass('Governance verdict', sentenceLabel(verdict))}`}>{sentenceLabel(verdict)}</span></dd></div>)}</dl>}
              </section>
            )
          })}
        </div>
      </div>

      <div className="border-t-2 border-[#0F1412] p-4 sm:p-5">
        <h3 className="text-base font-black">Suite evidence metadata</h3>
        {presentation.suiteMetadata.length === 0 ? (
          <div className="mt-3 border-2 border-[#59615D] bg-[#F3F5F0] p-3">
            <p className="font-black">No suite evidence is recorded</p>
            <p className="mt-1 text-sm font-semibold text-[#59615D]">This run response contains no suite execution metadata. FairMind does not infer admission, freshness, or review state.</p>
          </div>
        ) : (
          <div className="mt-3 max-w-full overflow-x-auto border-2 border-[#0F1412]">
            <table aria-label="Suite evidence trust metadata" className="w-full min-w-[1180px] border-collapse text-left text-sm">
              <thead className="bg-[#0F1412] text-white">
                <tr>
                  <th scope="col" className="px-3 py-3 font-black">Suite</th>
                  <th scope="col" className="px-3 py-3 font-black">Source</th>
                  <th scope="col" className="px-3 py-3 font-black">Evidence signer</th>
                  <th scope="col" className="px-3 py-3 font-black">Evidence result</th>
                  <th scope="col" className="px-3 py-3 font-black">Admission</th>
                  <th scope="col" className="px-3 py-3 font-black">Freshness</th>
                  <th scope="col" className="px-3 py-3 font-black">Review</th>
                  <th scope="col" className="px-3 py-3 font-black">Limitations</th>
                </tr>
              </thead>
              <tbody>
                {presentation.suiteMetadata.map((metadata) => {
                  const suite = run.suiteExecutions.find((candidate) => candidate.id === metadata.suiteExecutionId)
                  return (
                    <tr key={metadata.suiteExecutionId} className="border-t-2 border-[#0F1412] bg-[#FCFDF8]">
                      <td className="px-3 py-3"><p className="font-mono text-xs font-bold">{suite?.suiteVersionId ?? metadata.suiteExecutionId}</p><p className="mt-1 text-xs font-semibold text-[#59615D]">Execution {suite?.ordinal ?? 'not recorded'} · {suite ? sentenceLabel(suite.technicalStatus) : 'Not recorded'}</p></td>
                      <td className="px-3 py-3 font-semibold">{metadata.source}</td>
                      <td className="px-3 py-3 text-[#59615D]">{metadata.signer}</td>
                      <td className="px-3 py-3"><span className={`inline-flex min-h-8 items-center border-2 px-2 py-1 text-xs font-black uppercase ${axisClass('Evidence result', metadata.evidenceResult)}`}>{metadata.evidenceResult}</span></td>
                      <td className="px-3 py-3"><span className={`inline-flex min-h-8 items-center border-2 px-2 py-1 text-xs font-black uppercase ${axisClass('Admission', metadata.admission)}`}>{metadata.admission}</span></td>
                      <td className="px-3 py-3"><span className={`inline-flex min-h-8 items-center border-2 px-2 py-1 text-xs font-black uppercase ${axisClass('Freshness', metadata.freshness)}`}>{metadata.freshness}</span></td>
                      <td className="px-3 py-3"><span className={`inline-flex min-h-8 items-center border-2 px-2 py-1 text-xs font-black uppercase ${axisClass('Review', metadata.review)}`}>{metadata.review}</span></td>
                      <td className="px-3 py-3 text-sm font-semibold text-[#59615D]">{metadata.limitations.length > 0 ? <ul className="list-disc space-y-1 pl-4">{metadata.limitations.map((limitation, index) => <li key={`${metadata.suiteExecutionId}-${index}`}>{limitation}</li>)}</ul> : 'None reported'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
        <p className="mt-3 text-xs font-semibold text-[#59615D]">Reviewer identity, evidence signer, expiry timestamp, and invalidation reasons are not returned by the current run response. A review status does not identify a signer or reviewer.</p>
      </div>

      {run.failureCode || run.failureMessage ? (
        <div role="alert" className="border-t-4 border-[#D83A2E] bg-red-50 p-4">
          <h3 className="font-black text-[#8F2019]">Execution failure</h3>
          {run.failureCode ? <p className="mt-1 font-mono text-xs font-bold text-[#5B211D]">{run.failureCode}</p> : null}
          {run.failureMessage ? <p className="mt-2 text-sm font-semibold text-[#5B211D]">{run.failureMessage}</p> : null}
        </div>
      ) : null}
    </section>
  )
}
