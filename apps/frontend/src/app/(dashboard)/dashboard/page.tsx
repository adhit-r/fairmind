'use client'

import Link from 'next/link'
import { useMemo } from 'react'
import { useDashboard } from '@/lib/api/hooks/useDashboard'
import { useAuditLogs } from '@/lib/api/hooks/useAuditLogs'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { StatCard, SimpleChart } from '@/components/charts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import {
  IconActivity,
  IconAlertTriangle,
  IconArrowRight,
  IconBrain,
  IconBuildingSkyscraper,
  IconChartBar,
  IconClipboardCheck,
  IconFileCheck,
  IconRefresh,
  IconShield,
  IconTool,
} from '@tabler/icons-react'
import { useToast } from '@/hooks/use-toast'

type JourneyStage = {
  key: string
  label: string
  href: string
  status: 'done' | 'current' | 'next'
}

type ActionItem = {
  title: string
  description: string
  href: string
}

export default function DashboardPage() {
  const { data, loading, error, refetch } = useDashboard()
  const { data: auditLogs, loading: logsLoading } = useAuditLogs(7)
  const { selectedSystem, selectedSystemStatus } = useSystemContext()
  const { toast } = useToast()

  const activityData = useMemo(() => {
    if (!auditLogs || auditLogs.length === 0) {
      return ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((name) => ({ name, value: 0 }))
    }

    const dayCounts: Record<string, number> = {}
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    days.forEach((day) => {
      dayCounts[day] = 0
    })

    auditLogs.forEach((log) => {
      const date = new Date(log.timestamp || log.created_at || Date.now())
      const dayName = days[date.getDay()]
      dayCounts[dayName] = (dayCounts[dayName] || 0) + 1
    })

    return days.map((day) => ({ name: day, value: dayCounts[day] || 0 }))
  }, [auditLogs])

  const readiness = selectedSystemStatus.readiness
  const criticalBlockers = selectedSystemStatus.criticalBlockers
  const failedControls = selectedSystemStatus.failedControls
  const missingEvidence = selectedSystemStatus.missingEvidence

  const journeyStages: JourneyStage[] = useMemo(() => {
    const sequence = ['onboard', 'assess', 'govern', 'remediate', 'operate']
    const currentIndex = sequence.indexOf(selectedSystem.stage)
    const stageMap = [
      { key: 'onboard', label: 'Onboard', href: '/onboard' },
      { key: 'assess', label: 'Assess', href: '/bias' },
      { key: 'govern', label: 'Govern', href: '/risks' },
      { key: 'remediate', label: 'Remediate', href: '/remediation' },
      { key: 'operate', label: 'Operate', href: '/monitoring' },
    ]

    return stageMap.map((stage, index) => ({
      ...stage,
      status: index < currentIndex ? 'done' : index === currentIndex ? 'current' : index === currentIndex + 1 ? 'next' : 'next',
    }))
  }, [selectedSystem.stage])

  const blockers = useMemo(
    () => [
      {
        title: 'Bias review needs sign-off',
        description: 'High-severity fairness gap still blocks release readiness for the selected system.',
        href: '/risks',
      },
      {
        title: 'Evidence pack is incomplete',
        description: 'Governance evidence is missing a final approval note and monitoring baseline artifact.',
        href: '/evidence',
      },
      {
        title: 'Remediation re-test not attached',
        description: 'The remediation workflow exists, but the before/after comparison has not been linked to release approval.',
        href: '/remediation',
      },
    ],
    []
  )

  const nextActions: ActionItem[] = useMemo(() => {
    if (selectedSystem.stage === 'onboard') {
      return [
        {
          title: 'Complete workspace and asset setup',
          description: 'Define the owner, confirm scope, and verify model/dataset readiness before assessments begin.',
          href: '/onboard',
        },
        {
          title: 'Prepare first assessment path',
          description: 'Once assets are ready, move directly into fairness and governance evaluation.',
          href: '/bias',
        },
      ]
    }

    if (selectedSystem.stage === 'assess') {
      return [
        {
          title: 'Run fairness and LLM evaluations',
          description: 'Complete baseline testing before opening governance review.',
          href: '/bias',
        },
        {
          title: 'Check compliance coverage',
          description: 'Confirm required framework checks before risk review starts.',
          href: '/compliance-dashboard',
        },
      ]
    }

    if (selectedSystem.stage === 'govern') {
      return [
        {
          title: 'Review automated risks',
          description: 'Validate blockers and assign owners in the AI risk register.',
          href: '/risks',
        },
        {
          title: 'Close evidence gaps',
          description: 'Attach approval-ready evidence before remediation sign-off.',
          href: '/evidence',
        },
        {
          title: 'Open remediation work',
          description: 'Convert failed controls into tracked corrective actions.',
          href: '/remediation-wizard',
        },
      ]
    }

    return [
      {
        title: 'Monitor drift and alerts',
        description: 'Track post-release health, new issues, and reassessment cadence.',
        href: '/monitoring',
      },
      {
        title: 'Export audit artifacts',
        description: 'Produce current reports for customers, regulators, or internal review.',
        href: '/audit-reports',
      },
    ]
  }, [selectedSystem.stage])

  const handleRefresh = () => {
    refetch()
    toast({
      title: 'Refreshing data...',
      description: 'Dashboard data will be updated shortly.',
    })
  }

  const isFallbackSystem = selectedSystem.metadata?.source === 'fallback'

  if (loading || logsLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-48 w-full" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          {[...Array(4)].map((_, index) => (
            <Skeleton key={index} className="h-32" />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
          <Skeleton className="h-96 xl:col-span-2" />
          <Skeleton className="h-96" />
        </div>
      </div>
    )
  }

  if (isFallbackSystem) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center space-y-6">
        <Card className="w-full max-w-2xl overflow-hidden border-4 border-black bg-[linear-gradient(135deg,#fff4de_0%,#fff_55%,#e9f7f0_100%)] shadow-[10px_10px_0px_0px_rgba(0,0,0,1)]">
          <div className="border-b-4 border-black bg-black p-6 text-white">
            <div className="flex items-center gap-3">
              <div className="border-2 border-white p-2 shadow-[4px_4px_0px_0px_#FF6B35]">
                <IconBuildingSkyscraper className="h-6 w-6 text-orange" />
              </div>
              <Badge className="border-2 border-orange bg-orange/20 px-3 py-1 font-black uppercase text-orange">
                No AI systems registered
              </Badge>
            </div>
            <h1 className="mt-4 text-3xl font-black uppercase">Register your first AI system</h1>
            <p className="mt-2 text-sm text-slate-300">
              FairMind has no AI systems registered yet. Onboard your first system to unlock bias detection,
              compliance checks, risk tracking, and the full governance lifecycle.
            </p>
          </div>
          <div className="p-6">
            <div className="mb-6 space-y-3">
              {[
                { step: '1', label: 'Register', desc: 'Name, owner, risk tier, and workspace' },
                { step: '2', label: 'Select frameworks', desc: 'EU AI Act, GDPR, ISO 42001, NIST AI RMF, DPDP Act' },
                { step: '3', label: 'Queue bias scan', desc: 'Baseline fairness profile for the system' },
                { step: '4', label: 'Enter lifecycle', desc: 'Assess → Govern → Remediate → Operate' },
              ].map((item) => (
                <div key={item.step} className="flex items-start gap-4 border-2 border-black bg-white p-3 shadow-[2px_2px_0px_0px_#000]">
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center border-2 border-black bg-black font-black text-sm text-white">
                    {item.step}
                  </div>
                  <div>
                    <p className="font-black uppercase">{item.label}</p>
                    <p className="text-sm text-muted-foreground">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
            <Button asChild className="w-full border-2 border-black py-4 text-lg font-black uppercase shadow-[4px_4px_0px_0px_#FF6B35]">
              <Link href="/onboard">
                <IconBuildingSkyscraper className="mr-3 h-5 w-5" />
                Start onboarding
                <IconArrowRight className="ml-3 h-5 w-5" />
              </Link>
            </Button>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {!!error && (
        <Alert className="border-2 border-yellow-500 shadow-brutal">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertTitle>Dashboard Data Unavailable</AlertTitle>
          <AlertDescription>
            {error.message || 'Unable to load dashboard data.'} Showing workflow guidance using fallback values.
          </AlertDescription>
        </Alert>
      )}

      <Card className="overflow-hidden border-4 border-black bg-[linear-gradient(135deg,#ffd166_0%,#fff8e7_48%,#dff3e4_100%)] shadow-[10px_10px_0px_0px_rgba(0,0,0,1)]">
        <CardContent className="p-0">
          <div className="grid gap-0 xl:grid-cols-[1.3fr_0.9fr]">
            <div className="border-b-4 border-black p-6 xl:border-b-0 xl:border-r-4">
              <div className="mb-4 flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-black uppercase tracking-[0.25em] text-muted-foreground">
                    Decision Dashboard
                  </p>
                  <h1 className="text-4xl font-black uppercase leading-none">Release Readiness</h1>
                  <p className="mt-2 max-w-2xl text-sm text-slate-700">
                    The selected AI system is in <span className="font-black uppercase">{selectedSystem.stage}</span>.
                    Focus the team on blockers, close evidence gaps, and move to the next controlled stage.
                  </p>
                </div>
                <Button variant="default" onClick={handleRefresh}>
                  <IconRefresh className="mr-2 h-4 w-4" />
                  Refresh
                </Button>
              </div>

              <div className="mb-5 grid gap-4 md:grid-cols-3">
                <div className="border-2 border-black bg-white p-4 shadow-[4px_4px_0px_0px_#000]">
                  <p className="text-xs font-bold uppercase text-muted-foreground">Readiness</p>
                  <p className="mt-2 text-4xl font-black">{readiness}%</p>
                  <Progress value={readiness} className="mt-3 h-3 border-2 border-black" />
                </div>
                <div className="border-2 border-black bg-white p-4 shadow-[4px_4px_0px_0px_#000]">
                  <p className="text-xs font-bold uppercase text-muted-foreground">Critical Blockers</p>
                  <p className="mt-2 text-4xl font-black text-red-600">{criticalBlockers}</p>
                  <p className="mt-2 text-sm text-slate-700">Release should not be approved until these are resolved.</p>
                </div>
                <div className="border-2 border-black bg-white p-4 shadow-[4px_4px_0px_0px_#000]">
                  <p className="text-xs font-bold uppercase text-muted-foreground">Failed Controls</p>
                  <p className="mt-2 text-4xl font-black">{failedControls}</p>
                  <p className="mt-2 text-sm text-slate-700">Controls with missing evidence, unresolved findings, or pending sign-off.</p>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-black uppercase">Journey Status</h2>
                  <Badge className="border-2 border-black bg-black text-white">
                    {selectedSystem.stage}
                  </Badge>
                </div>
                <div className="grid gap-3 md:grid-cols-5">
                  {journeyStages.map((stage) => (
                    <Link
                      key={stage.key}
                      href={stage.href}
                      className={`border-2 p-3 transition-all ${
                        stage.status === 'current'
                          ? 'border-black bg-black text-white shadow-[4px_4px_0px_0px_#FF6B35]'
                          : stage.status === 'done'
                            ? 'border-black bg-[#dff3e4] shadow-[4px_4px_0px_0px_#000]'
                            : 'border-black bg-white hover:bg-[#fff4de]'
                      }`}
                    >
                      <p className="text-xs font-bold uppercase opacity-70">
                        {stage.status === 'done' ? 'Done' : stage.status === 'current' ? 'Current' : 'Next'}
                      </p>
                      <p className="mt-1 text-sm font-black uppercase">{stage.label}</p>
                    </Link>
                  ))}
                </div>
              </div>
            </div>

            <div className="bg-black p-6 text-white">
              <div className="mb-4">
                <p className="text-xs font-black uppercase tracking-[0.25em] text-orange">Immediate Focus</p>
                <h2 className="mt-2 text-2xl font-black uppercase">Top Blockers</h2>
              </div>
              <div className="space-y-3">
                {blockers.slice(0, criticalBlockers).map((blocker) => (
                  <Link
                    key={blocker.title}
                    href={blocker.href}
                    className="block border-2 border-white bg-white/10 p-4 transition hover:bg-orange hover:text-black"
                  >
                    <p className="font-black uppercase">{blocker.title}</p>
                    <p className="mt-1 text-sm opacity-90">{blocker.description}</p>
                  </Link>
                ))}
              </div>
              <div className="mt-5 border-2 border-white p-4">
                <p className="text-xs font-bold uppercase text-orange">Missing Evidence</p>
                <p className="mt-2 text-3xl font-black">{missingEvidence}</p>
                <p className="mt-2 text-sm text-slate-200">
                  Complete the evidence pack before approval and export.
                </p>
                <Button asChild variant="default" className="mt-4">
                  <Link href="/evidence">
                    Review Evidence
                    <IconArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Total Models"
          value={data?.totalModels ?? 0}
          icon={<IconBrain className="h-5 w-5" />}
          trend={{ value: 12, label: 'vs last month', isPositive: true }}
        />
        <StatCard
          title="Total Datasets"
          value={data?.totalDatasets ?? 0}
          icon={<IconChartBar className="h-5 w-5" />}
          trend={{ value: 8, label: 'vs last month', isPositive: true }}
        />
        <StatCard
          title="Active Scans"
          value={data?.activeScans ?? 0}
          icon={<IconShield className="h-5 w-5" />}
          trend={{ value: -3, label: 'vs last week', isPositive: false }}
        />
        <StatCard
          title="System Health"
          value={data?.systemHealth?.status === 'healthy' ? 'Healthy' : 'Degraded'}
          icon={<IconActivity className="h-5 w-5" />}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader className="border-b-2 border-black bg-[#fff4de]">
            <CardTitle className="text-xl font-black uppercase">Next Recommended Actions</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 p-6 md:grid-cols-2">
            {nextActions.map((action) => (
              <Link
                key={action.title}
                href={action.href}
                className="border-2 border-black bg-white p-4 transition hover:bg-orange hover:shadow-[4px_4px_0px_0px_#000]"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-black uppercase">{action.title}</p>
                    <p className="mt-2 text-sm text-slate-700">{action.description}</p>
                  </div>
                  <IconArrowRight className="mt-1 h-4 w-4 shrink-0" />
                </div>
              </Link>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="border-b-2 border-black bg-[#e9f7f0]">
            <CardTitle className="text-xl font-black uppercase">Approval Readiness</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 p-6">
            <div className="border-2 border-black p-4">
              <div className="flex items-center gap-3">
                <IconClipboardCheck className="h-5 w-5" />
                <div>
                  <p className="font-black uppercase">Controls Review</p>
                  <p className="text-sm text-slate-700">{failedControls} controls still need closure.</p>
                </div>
              </div>
            </div>
            <div className="border-2 border-black p-4">
              <div className="flex items-center gap-3">
                <IconTool className="h-5 w-5" />
                <div>
                  <p className="font-black uppercase">Remediation Status</p>
                  <p className="text-sm text-slate-700">At least one remediation workflow should be completed before sign-off.</p>
                </div>
              </div>
            </div>
            <div className="border-2 border-black p-4">
              <div className="flex items-center gap-3">
                <IconFileCheck className="h-5 w-5" />
                <div>
                  <p className="font-black uppercase">Audit Pack</p>
                  <p className="text-sm text-slate-700">Reports are only defensible once evidence links are complete.</p>
                </div>
              </div>
            </div>
            <Button asChild variant="default" className="w-full">
              <Link href="/ai-governance">Open Governance Review</Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <SimpleChart
          title="Recent Governance Activity"
          data={activityData}
          type="line"
          dataKey="value"
        />
        <Card>
          <CardHeader className="border-b-2 border-black bg-[#fff4de]">
            <CardTitle className="text-xl font-black uppercase">What This Dashboard Should Answer</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 p-6">
            <div className="border-2 border-black p-4">
              <p className="font-black uppercase">Can we release?</p>
              <p className="mt-2 text-sm text-slate-700">Not until blockers, failed controls, and missing evidence are resolved.</p>
            </div>
            <div className="border-2 border-black p-4">
              <p className="font-black uppercase">What should the team do next?</p>
              <p className="mt-2 text-sm text-slate-700">Use the recommended actions above to move the selected AI system to the next stage.</p>
            </div>
            <div className="border-2 border-black p-4">
              <p className="font-black uppercase">Where is the proof?</p>
              <p className="mt-2 text-sm text-slate-700">Evidence, reports, and approval status must converge before the release gate is trustworthy.</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
