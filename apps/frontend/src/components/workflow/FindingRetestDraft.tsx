'use client'

import Link from 'next/link'
import type { ReactNode } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { isOpenRisk, useRisks } from '@/lib/api/hooks/useRisks'
import { findingHref } from '@/lib/assurance/evaluationLinks'

export function FindingRetestDraft({ systemId, findingId, source, children }: {
  systemId: string
  findingId: string | null
  source: 'fairmind.watch' | 'environmental_impact'
  children: ReactNode
}) {
  const { data, loading, error, reload } = useRisks(systemId)
  if (loading) return <Skeleton height={48} />
  if (error) return <Banner status="error" title="Finding could not load" description={error.message} endContent={<Button label="Retry finding" onClick={reload} />} />
  const finding = data.find((item) => item.id === findingId && item.systemId === systemId && item.source === source)
  const original = source === 'fairmind.watch' ? finding?.metadata?.latest_snapshot_id : finding?.metadata?.assessment_id
  if (!finding || !isOpenRisk(finding) || typeof original !== 'string' || !original.trim()) {
    return <Banner status="warning" title="Retest unavailable" description="An open finding for this check and system could not be verified." />
  }
  return <><Link href={findingHref(systemId, finding.id)}>Back to finding</Link>{children}</>
}
