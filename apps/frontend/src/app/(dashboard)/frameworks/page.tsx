'use client'

import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import Link from 'next/link'
import { Empty, ErrorNote, Loading } from '@/components/packs/parts'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { useJourneys } from '@/lib/api/hooks/usePacks'
import { confirmedFrameworks } from './[key]/grid'

/** Opens the first framework a system confirmed, else the first in the catalogue. */
export default function FrameworksIndex() {
  const { systems, loading } = useSystemContext()
  const journeys = useJourneys()
  const router = useRouter()
  const confirmed = confirmedFrameworks(systems)[0]?.key
  const first = confirmed ?? journeys.data?.[0]?.key
  const ready = !loading && (confirmed || !journeys.loading)

  useEffect(() => {
    if (ready && first) router.replace(`/frameworks/${encodeURIComponent(first)}`)
  }, [ready, first, router])

  if (ready && !first) {
    if (journeys.error) return <ErrorNote message={journeys.error} onRetry={journeys.reload} />
    return (
      <Empty>
        No frameworks are loaded for this organisation. <Link href="/compliance" className="font-medium text-[var(--fm-ink)] underline">Open the packs hub</Link>
      </Empty>
    )
  }
  return <Loading label="Opening frameworks" />
}
