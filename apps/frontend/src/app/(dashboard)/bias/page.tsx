'use client'

import Link from 'next/link'
import { BTN_P, MUTED } from '@/components/packs/parts'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { useSystemFile } from '@/lib/api/hooks/useSystemFile'
import { FairnessRunPanel } from '../systems/[id]/FairnessRunPanel'

function Panel({ systemId }: { systemId: string }) {
  const { inspectCsv, runFairness } = useSystemFile(systemId)
  return <FairnessRunPanel inspect={inspectCsv} run={runFairness} />
}

export default function BiasPage() {
  const { selectedSystem, loading, error, refreshSystems } = useSystemContext()
  const hasSystem = Boolean(selectedSystem.id)

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="mt-1.5 text-[30px] font-semibold leading-[1.1] tracking-[-.03em]">Bias test</h1>
        <p className={`mt-2 max-w-[640px] text-[15px] ${MUTED}`}>
          Measure fairness from a predictions file. The result is recorded on the system file.
        </p>
      </div>
      {hasSystem ? (
        <>
          <p className={`text-[13px] ${MUTED}`}>
            System: <Link href={`/systems/${encodeURIComponent(selectedSystem.id)}`} className="font-semibold text-[var(--fm-ink)]">{selectedSystem.name}</Link>
          </p>
          <Panel systemId={selectedSystem.id} />
        </>
      ) : (
        <section className="fm-card grid content-start justify-items-start gap-3 p-6" aria-label="No system">
          {loading ? (
            <p role="status" className={`text-[13px] ${MUTED}`}>Loading your systems</p>
          ) : error ? (
            <>
              <h2 className="text-[15px] font-semibold">Could not load your systems</h2>
              <p role="alert" className={`max-w-[560px] text-[13px] ${MUTED}`}>
                A bias test belongs to a system, so it cannot run until your systems load. {error}
              </p>
              <button type="button" onClick={() => void refreshSystems()} className={BTN_P}>Try again</button>
            </>
          ) : (
            <>
              <h2 className="text-[15px] font-semibold">No AI system is registered yet</h2>
              <p className={`max-w-[560px] text-[13px] ${MUTED}`}>
                A bias test belongs to a system. Register one, then run the test against its predictions file.
              </p>
              <Link href="/onboard" className={BTN_P}>Register a system</Link>
            </>
          )}
        </section>
      )}
    </div>
  )
}
