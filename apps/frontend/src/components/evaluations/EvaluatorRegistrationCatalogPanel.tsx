'use client'

import { useMemo, type ReactNode } from 'react'

import { apiClient } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import {
  createEvaluatorCatalogSource,
  useEvaluatorCatalog,
  type EvaluatorCatalogSnapshot,
  type EvaluatorRegistration,
  type EvaluatorRegistrationStatus,
} from '@/lib/api/hooks/useEvaluatorCatalog'

type EvaluatorCatalogPanelModel = EvaluatorCatalogSnapshot & {
  refresh?: () => Promise<void>
  nextPage?: () => Promise<void>
  previousPage?: () => Promise<void>
}

const statusStyle: Record<EvaluatorRegistrationStatus, string> = {
  pending: 'border-[#D36B1F] bg-[#FFF1D6] text-[#5B492E]',
  approved: 'border-[#0B7659] bg-[#DDF4EA] text-[#0B503D]',
  rejected: 'border-[#D83A2E] bg-[#FDE7E4] text-[#8F2019]',
  revoked: 'border-[rgba(21,23,26,.14)] bg-[var(--fm-bg)] text-[#303633]',
}

function formatStatus(status: EvaluatorRegistrationStatus) {
  return status.slice(0, 1).toUpperCase() + status.slice(1)
}

function formatTimestamp(value: string | null) {
  if (!value) return 'Not recorded'
  const timestamp = new Date(value)
  if (Number.isNaN(timestamp.getTime())) return value
  return new Intl.DateTimeFormat('en', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    timeZoneName: 'short',
  }).format(timestamp)
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid grid-cols-[auto_minmax(0,1fr)] items-baseline gap-x-2 text-xs">
      <dt className="font-semibold tracking-[0.12em] text-[var(--fm-ink2)]">{label}</dt>
      <dd className="min-w-0 break-all font-mono font-bold text-[var(--fm-ink)]">{value}</dd>
    </div>
  )
}

function Timestamp({ value }: { value: string | null }) {
  if (!value) return <>Not recorded</>
  return <time dateTime={value}>{formatTimestamp(value)}</time>
}

function ReviewAndRevocation({ registration }: { registration: EvaluatorRegistration }) {
  const hasReview = registration.reviewedBy || registration.reviewedAt || registration.reviewRationale
  const hasRevocation = registration.revokedBy || registration.revokedAt || registration.revocationRationale

  return (
    <div className="space-y-3 text-xs leading-5 text-[#303633]">
      <div>
        <p className="font-semibold tracking-[0.12em] text-[var(--fm-ink)]">Review</p>
        {hasReview ? (
          <dl className="mt-1 space-y-1">
            {registration.reviewedBy ? <Field label="By" value={registration.reviewedBy} /> : null}
            {registration.reviewedAt ? (
              <div className="grid grid-cols-[auto_minmax(0,1fr)] items-baseline gap-x-2">
                <dt className="font-semibold tracking-[0.12em] text-[var(--fm-ink2)]">At</dt>
                <dd><Timestamp value={registration.reviewedAt} /></dd>
              </div>
            ) : null}
            {registration.reviewRationale ? (
              <div>
                <dt className="font-semibold tracking-[0.12em] text-[var(--fm-ink2)]">Note</dt>
                <dd className="mt-0.5 break-words">{registration.reviewRationale}</dd>
              </div>
            ) : null}
          </dl>
        ) : (
          <p className="mt-1">No review details are recorded.</p>
        )}
      </div>

      <div className="border-t border-[var(--fm-line)] pt-2">
        <p className="font-semibold tracking-[0.12em] text-[var(--fm-ink)]">Revocation</p>
        {hasRevocation ? (
          <dl className="mt-1 space-y-1">
            {registration.revokedBy ? <Field label="By" value={registration.revokedBy} /> : null}
            {registration.revokedAt ? (
              <div className="grid grid-cols-[auto_minmax(0,1fr)] items-baseline gap-x-2">
                <dt className="font-semibold tracking-[0.12em] text-[var(--fm-ink2)]">At</dt>
                <dd><Timestamp value={registration.revokedAt} /></dd>
              </div>
            ) : null}
            {registration.revocationRationale ? (
              <div>
                <dt className="font-semibold tracking-[0.12em] text-[var(--fm-ink2)]">Note</dt>
                <dd className="mt-0.5 break-words">{registration.revocationRationale}</dd>
              </div>
            ) : null}
          </dl>
        ) : (
          <p className="mt-1">No revocation details are recorded.</p>
        )}
      </div>
    </div>
  )
}

function LoadingRows() {
  return (
    <div aria-busy="true" aria-live="polite" className="space-y-2 p-4" role="status">
      <p className="text-sm font-semibold text-[var(--fm-ink)]">Loading evaluator registrations</p>
      {[0, 1, 2].map((row) => (
        <div key={row} className="h-12 animate-pulse border border-[var(--fm-line)] bg-[var(--fm-bg)] motion-reduce:animate-none" />
      ))}
    </div>
  )
}

function StateNotice({
  title,
  children,
  tone = 'neutral',
  role = 'status',
}: {
  title: string
  children: ReactNode
  tone?: 'neutral' | 'warning' | 'danger'
  role?: 'status' | 'alert'
}) {
  const toneClass = tone === 'danger'
    ? 'border-[#D83A2E] bg-[#FDE7E4] text-[#8F2019]'
    : tone === 'warning'
      ? 'border-[#D36B1F] bg-[#FFF1D6] text-[#5B492E]'
      : 'border-[var(--fm-line)] bg-[var(--fm-bg)] text-[#303633]'
  return (
    <div className={`border-4 p-4 ${toneClass}`} role={role}>
      <h3 className="text-base font-semibold text-[var(--fm-ink)]">{title}</h3>
      <div className="mt-1 max-w-[78ch] text-sm font-semibold">{children}</div>
    </div>
  )
}

function CatalogTable({ registrations }: { registrations: EvaluatorRegistration[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[1040px] border-collapse text-left">
        <caption className="sr-only">Evaluator registration identity bindings and lifecycle state.</caption>
        <thead className="bg-[var(--fm-ink)] text-white">
          <tr>
            {['Evaluator binding', 'Binding hash', 'Signer / source', 'Review / revocation', 'Registration status'].map((heading) => (
              <th key={heading} scope="col" className="border-r border-white/40 px-3 py-3 text-xs font-semibold uppercase tracking-[0.08em] last:border-r-0">
                {heading}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {registrations.map((registration) => (
            <tr key={registration.id} className="border-t border-[var(--fm-line)] align-top bg-white even:bg-[var(--fm-bg)]">
              <td className="border-r border-[var(--fm-line)] p-3 last:border-r-0">
                <p className="break-all font-mono text-sm font-semibold text-[var(--fm-ink)]">{registration.evaluatorId}</p>
                <dl className="mt-3 space-y-1.5">
                  <Field label="Adapter" value={`${registration.adapterName} ${registration.adapterVersion}`} />
                  <Field label="Contract" value={registration.resultContractVersion} />
                  <Field label="Registration" value={registration.id} />
                </dl>
              </td>
              <td className="border-r border-[var(--fm-line)] p-3 last:border-r-0">
                <code className="block break-all border border-[var(--fm-line)] bg-white p-2 text-xs font-bold text-[var(--fm-ink)]">
                  {registration.bindingHash}
                </code>
              </td>
              <td className="border-r border-[var(--fm-line)] p-3 last:border-r-0">
                <dl className="space-y-1.5">
                  <Field label="Source" value={registration.sourceType} />
                  <Field label="Issuer" value={registration.issuerId} />
                  <Field label="Key" value={registration.signingKeyId} />
                </dl>
              </td>
              <td className="border-r border-[var(--fm-line)] p-3 last:border-r-0">
                <ReviewAndRevocation registration={registration} />
              </td>
              <td className="p-3">
                <span className={`inline-flex border-2 px-2 py-1 text-xs font-semibold uppercase ${statusStyle[registration.status]}`}>
                  {formatStatus(registration.status)}
                </span>
                <dl className="mt-3 space-y-1.5 text-xs">
                  <Field label="Submitted by" value={registration.submittedBy} />
                  <div className="grid grid-cols-[auto_minmax(0,1fr)] items-baseline gap-x-2">
                    <dt className="font-semibold tracking-[0.12em] text-[var(--fm-ink2)]">Submitted</dt>
                    <dd className="text-[#303633]"><Timestamp value={registration.submittedAt} /></dd>
                  </div>
                </dl>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function CatalogPageNavigation({ catalog }: { catalog: EvaluatorCatalogPanelModel }) {
  const page = catalog.page
  if (!page) return null

  const hasRecords = catalog.registrations.length > 0
  const firstRecord = page.offset + 1
  const lastRecord = page.offset + catalog.registrations.length

  return (
    <footer aria-label="Evaluator catalog page navigation" className="flex flex-col gap-3 border-t border-[var(--fm-line)] bg-[var(--fm-bg)] p-4 sm:flex-row sm:items-center sm:justify-between">
      <p className="max-w-[66ch] text-sm font-semibold leading-6 text-[#303633]" aria-live="polite">
        {hasRecords
          ? `Showing registration records ${firstRecord}–${lastRecord} from offset ${page.offset}.`
          : `No registration records were returned for offset ${page.offset}.`}{' '}
        {page.hasMore
          ? 'More registration records are available on a later page.'
          : 'No later page was reported by the catalog route.'}
      </p>
      <div className="flex shrink-0 gap-2">
        <button
          type="button"
          disabled={page.offset === 0 || !catalog.previousPage}
          onClick={() => { void catalog.previousPage?.() }}
          className="inline-flex min-h-11 items-center px-4 text-sm font-semibold text-[var(--fm-ink)] outline-none transition-[transform,box-shadow] duration-150 focus-visible:ring-2 focus-visible:ring-[#0B7659] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:border-[rgba(21,23,26,.14)] disabled:bg-[#E3E6E1] disabled:text-[var(--fm-ink2)] disabled:shadow-none disabled:hover:translate-x-0 disabled:hover:translate-y-0 motion-reduce:transform-none motion-reduce:transition-none fm-card"
        >
          Previous page
        </button>
        <button
          type="button"
          disabled={!page.hasMore || !catalog.nextPage}
          onClick={() => { void catalog.nextPage?.() }}
          className="inline-flex min-h-11 items-center bg-[#0B7659] px-4 text-sm font-semibold text-white outline-none transition-[transform,box-shadow] duration-150 focus-visible:ring-2 focus-visible:ring-[#0B7659] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:border-[rgba(21,23,26,.14)] disabled:bg-[#E3E6E1] disabled:text-[var(--fm-ink2)] disabled:shadow-none disabled:hover:translate-x-0 disabled:hover:translate-y-0 motion-reduce:transform-none motion-reduce:transition-none rounded-[14px] shadow-[var(--fm-shadow)]"
        >
          Next page
        </button>
      </div>
    </footer>
  )
}

export function EvaluatorRegistrationCatalogPanel({ catalog }: { catalog: EvaluatorCatalogPanelModel }) {
  const unavailableCode = catalog.error && 'code' in catalog.error
    ? (catalog.error as { code?: string }).code
    : undefined

  return (
    <section aria-labelledby="evaluator-registration-catalog-title" className="fm-card">
      <div className="border-b border-[var(--fm-line)] px-4 py-4 sm:px-5">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#0B7659]">Organization catalog</p>
        <h2 id="evaluator-registration-catalog-title" className="mt-1 text-xl font-semibold tracking-tight text-[var(--fm-ink)]">
          Evaluator registration catalog
        </h2>
        <p className="mt-2 max-w-[80ch] text-sm font-semibold leading-6 text-[#303633]">
          This catalog records evaluator identity bindings, signer metadata, and lifecycle decisions for the active organization. It does not state what an evaluator can do or the outcome of an evaluation.
        </p>
      </div>

      {catalog.state === 'loading' ? <LoadingRows /> : null}

      {catalog.state === 'disabled' ? (
        <StateNotice title={
          catalog.disabledReason === 'catalog_route_disabled'
            ? 'Evaluator catalog route disabled'
            : catalog.disabledReason === 'organization_required'
              ? 'Choose an organization'
              : 'Evaluator catalog disabled'
        }>
          {catalog.disabledReason === 'organization_required'
            ? 'Select an organization before evaluator registrations can be requested.'
            : catalog.disabledReason === 'catalog_route_disabled'
              ? 'This deployment did not publish the evaluator catalog route. No registration records were displayed.'
            : 'Catalog display is disabled for this deployment. No catalog request was made.'}
        </StateNotice>
      ) : null}

      {catalog.state === 'denied' ? (
        <StateNotice title="Evaluator catalog access denied" tone="warning" role="alert">
          You do not have the required evaluator catalog permission for this organization. No registration records were displayed.
        </StateNotice>
      ) : null}

      {catalog.state === 'unavailable' ? (
        <StateNotice title="Evaluator catalog unavailable" tone="danger" role="alert">
          <p>{catalog.error?.message || 'The evaluator catalog could not be loaded.'}</p>
          {unavailableCode ? <p className="mt-2 font-mono text-xs">Server code: {unavailableCode}</p> : null}
          {catalog.canRetry && catalog.refresh ? (
            <button
              type="button"
              onClick={() => { void catalog.refresh?.() }}
              className="mt-4 inline-flex min-h-11 items-center px-4 text-sm font-semibold text-[var(--fm-ink)] outline-none transition-[transform,box-shadow] duration-150 focus-visible:ring-2 focus-visible:ring-[#0B7659] focus-visible:ring-offset-2 motion-reduce:transform-none motion-reduce:transition-none fm-card"
            >
              Retry catalog request
            </button>
          ) : null}
        </StateNotice>
      ) : null}

      {catalog.state === 'empty' ? (
        <StateNotice title={catalog.page?.offset ? 'No evaluator registrations on this page' : 'No evaluator registrations returned'}>
          {catalog.page?.offset
            ? `The catalog route returned no evaluator identity registrations at offset ${catalog.page.offset}.`
            : 'The catalog route returned no evaluator identity registrations at the first page.'}
        </StateNotice>
      ) : null}

      {catalog.state === 'ready' ? <CatalogTable registrations={catalog.registrations} /> : null}
      {catalog.state === 'ready' || catalog.state === 'empty' ? <CatalogPageNavigation catalog={catalog} /> : null}
    </section>
  )
}

/**
 * This component is mounted only by the feature-gated route surface. It uses
 * the real API route; test-only sources belong at the controller boundary.
 */
export function EvaluatorRegistrationCatalogSection({
  organizationId,
  authorized,
}: {
  organizationId?: string
  authorized: boolean
}) {
  const source = useMemo(
    () => createEvaluatorCatalogSource(apiClient, API_ENDPOINTS.aiGovernance.evaluatorCatalogRegistrations),
    [],
  )
  const catalog = useEvaluatorCatalog({
    organizationId,
    enabled: true,
    authorized,
    source,
  })

  return <EvaluatorRegistrationCatalogPanel catalog={catalog} />
}
