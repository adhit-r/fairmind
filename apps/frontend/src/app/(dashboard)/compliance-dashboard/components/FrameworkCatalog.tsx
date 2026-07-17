import { IconCheck, IconLock } from '@tabler/icons-react'

import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import type {
  FrameworkCatalog as CatalogFramework,
  FrameworkVersion,
} from '@/lib/api/hooks/useGovernanceAssurance'

type FrameworkCatalogProps = {
  frameworks: CatalogFramework[]
  versions: FrameworkVersion[]
  selectedFrameworkKey: string
  selectedVersionId: string
  assignedVersionIds: string[]
  loading: boolean
  activating: boolean
  canActivate: boolean
  systemName: string
  onFrameworkChange: (frameworkKey: string) => void
  onVersionChange: (versionId: string) => void
  onActivate: () => void
}

export function FrameworkCatalog({
  frameworks,
  versions,
  selectedFrameworkKey,
  selectedVersionId,
  assignedVersionIds,
  loading,
  activating,
  canActivate,
  systemName,
  onFrameworkChange,
  onVersionChange,
  onActivate,
}: FrameworkCatalogProps) {
  const selectedVersion = versions.find((version) => version.id === selectedVersionId)
  const isAssigned = selectedVersion ? assignedVersionIds.includes(selectedVersion.id) : false

  return (
    <section aria-labelledby="catalog-heading" className="border-4 border-[#0F1412] bg-[#FCFDF8] shadow-[8px_8px_0_0_#0F1412]">
      <div className="border-b-2 border-[#0F1412] bg-[#F3F5F0] px-4 py-3 sm:px-5">
        <h2 id="catalog-heading" className="text-base font-black uppercase">Framework catalog</h2>
        <p className="mt-1 text-sm text-[#59615D]">Choose one immutable version to apply to the selected AI system.</p>
      </div>

      <div className="grid gap-5 p-4 sm:p-5 lg:grid-cols-[240px_minmax(0,1fr)]">
        <div>
          <label htmlFor="framework-family" className="text-xs font-black uppercase tracking-[0.12em]">
            Framework
          </label>
          <select
            id="framework-family"
            value={selectedFrameworkKey}
            onChange={(event) => onFrameworkChange(event.target.value)}
            className="mt-2 min-h-11 w-full rounded-none border-2 border-[#0F1412] bg-[#FCFDF8] px-3 py-2 text-sm font-bold outline-none focus-visible:ring-2 focus-visible:ring-[#0B7659] focus-visible:ring-offset-2"
          >
            {frameworks.map((framework) => (
              <option key={framework.frameworkKey} value={framework.frameworkKey}>{framework.name}</option>
            ))}
          </select>
        </div>

        <div>
          <p id="version-legend" className="text-xs font-black uppercase tracking-[0.12em]">Available versions</p>
          {loading ? (
            <div aria-label="Loading framework versions" className="mt-2 grid gap-3 sm:grid-cols-2">
              <Skeleton className="h-20 rounded-none" />
              <Skeleton className="h-20 rounded-none" />
            </div>
          ) : versions.length === 0 ? (
            <p className="mt-2 border-2 border-[#0F1412] bg-[#F3F5F0] p-4 text-sm font-bold">
              No versions are available for this framework.
            </p>
          ) : (
            <div role="radiogroup" aria-labelledby="version-legend" className="mt-2 grid gap-3 sm:grid-cols-2">
              {versions.map((version) => {
                const assigned = assignedVersionIds.includes(version.id)
                const checked = version.id === selectedVersionId
                return (
                  <label
                    key={version.id}
                    className={`flex min-h-[76px] cursor-pointer items-start gap-3 border-2 border-[#0F1412] p-3 transition-transform focus-within:ring-2 focus-within:ring-[#0B7659] focus-within:ring-offset-2 ${checked ? 'bg-[#DDF4EA] shadow-[4px_4px_0_0_#0F1412]' : 'bg-[#FCFDF8]'}`}
                  >
                    <input
                      type="radio"
                      name="framework-version"
                      value={version.id}
                      checked={checked}
                      onChange={() => onVersionChange(version.id)}
                      aria-label={`${version.name} ${version.versionLabel}`}
                      className="mt-1 h-5 w-5 accent-[#0B7659]"
                    />
                    <span className="min-w-0">
                      <span className="block font-black">{version.name}</span>
                      <span className="block text-sm font-bold">{version.versionLabel}</span>
                      <span className="mt-1 flex items-center gap-1 text-[11px] font-black uppercase tracking-[0.08em] text-[#59615D]">
                        {assigned ? <IconCheck aria-hidden="true" className="h-3.5 w-3.5" /> : <IconLock aria-hidden="true" className="h-3.5 w-3.5" />}
                        {assigned ? 'Active for system' : 'Version pinned'}
                      </span>
                    </span>
                  </label>
                )
              })}
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-col gap-3 border-t-2 border-[#0F1412] bg-[#F3F5F0] px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-5">
        <div>
          <p className="font-black">{isAssigned ? 'This version is active for the selected system' : 'Activate a framework version for this AI system'}</p>
          <p className="text-sm text-[#59615D]">
            {isAssigned
              ? `${systemName} uses this pinned catalog version.`
              : canActivate
                ? 'Activation creates system-scoped control assessments.'
                : 'Ask an organization administrator to activate this version.'}
          </p>
        </div>
        {!isAssigned && selectedVersion ? (
          <Button
            type="button"
            disabled={!canActivate || activating}
            onClick={onActivate}
            className="rounded-none border-[#0F1412] bg-[#FF6B35] font-black uppercase text-[#0F1412]"
          >
            {activating ? 'Activating version' : `Activate ${selectedVersion.name} ${selectedVersion.versionLabel}`}
          </Button>
        ) : null}
      </div>
    </section>
  )
}
