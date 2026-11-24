'use client'

import './system-assurance.css'
import { Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import AssuranceOverview from './AssuranceOverview'
import { SystemAssuranceReport } from './SystemAssuranceReport'

function ReportRoute() {
  const search = useSearchParams()
  if (search.get('view') === 'assurance' || search.get('mode') === 'auditor') {
    return <div className="sar-page sar-legacy"><AssuranceOverview /></div>
  }
  return <SystemAssuranceReport />
}

export default function SystemAssurancePage() {
  return <Suspense fallback={<div className="sar-page" role="status">Loading reports…</div>}><ReportRoute /></Suspense>
}
