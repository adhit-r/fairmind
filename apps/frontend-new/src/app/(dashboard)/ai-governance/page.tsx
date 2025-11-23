'use client'

import { useMemo } from 'react'
import { useAIGovernance } from '@/lib/api/hooks/useAIGovernance'
import { useCompliance } from '@/lib/api/hooks/useCompliance'
import { usePolicies } from '@/lib/api/hooks/usePolicies'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { StatCard } from '@/components/charts/StatCard'
import { PieChart } from '@/components/charts/PieChart'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import {
  IconShield,
  IconCheck,
  IconAlertTriangle,
  IconBrain,
} from '@tabler/icons-react'

export default function AIGovernancePage() {
  const { frameworks, loading: frameworksLoading, error: frameworksError } = useAIGovernance()
  const { data: complianceData, loading: complianceLoading, error: complianceError } = useCompliance()
  const { data: policies, loading: policiesLoading } = usePolicies()

  // Calculate compliance distribution from frameworks
  const complianceDistribution = useMemo(() => {
    if (!complianceData?.frameworks || complianceData.frameworks.length === 0) {
      return [
        { name: 'Compliant', value: 0 },
        { name: 'Partial', value: 0 },
        { name: 'Non-Compliant', value: 0 },
      ]
    }

    const compliant = complianceData.frameworks.filter(f => f.status === 'compliant').length
    const partial = complianceData.frameworks.filter(f => f.status === 'partial').length
    const nonCompliant = complianceData.frameworks.filter(f => f.status === 'non-compliant').length

    return [
      { name: 'Compliant', value: compliant },
      { name: 'Partial', value: partial },
      { name: 'Non-Compliant', value: nonCompliant },
    ]
  }, [complianceData])

  // Calculate overall compliance rate
  const overallComplianceRate = useMemo(() => {
    if (!complianceData?.frameworks || complianceData.frameworks.length === 0) return 0
    const total = complianceData.frameworks.reduce((sum, f) => sum + f.compliance, 0)
    return Math.round(total / complianceData.frameworks.length)
  }, [complianceData])

  // Count issues (non-compliant frameworks)
  const issuesCount = useMemo(() => {
    if (!complianceData?.frameworks) return 0
    return complianceData.frameworks.filter(f => f.status === 'non-compliant').length
  }, [complianceData])

  const loading = frameworksLoading || complianceLoading || policiesLoading

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-96" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold">AI Governance</h1>
        <p className="text-muted-foreground mt-1">
          Comprehensive AI governance and compliance management
        </p>
      </div>

      {frameworksError && (
        <Alert className="border-2 border-red-500 shadow-brutal">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertTitle>Error Loading Frameworks</AlertTitle>
          <AlertDescription>{frameworksError.message}</AlertDescription>
        </Alert>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Frameworks"
          value={frameworks.length}
          icon={<IconShield className="h-5 w-5" />}
        />
        <StatCard
          title="Compliance Rate"
          value={`${overallComplianceRate}%`}
          icon={<IconCheck className="h-5 w-5" />}
        />
        <StatCard
          title="Active Policies"
          value={policies?.length || 0}
          icon={<IconBrain className="h-5 w-5" />}
        />
        <StatCard
          title="Issues"
          value={issuesCount}
          icon={<IconAlertTriangle className="h-5 w-5" />}
        />
      </div>

      {/* Compliance Chart */}
      {complianceDistribution.some(d => d.value > 0) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PieChart
            title="Overall Compliance"
            data={complianceDistribution}
          />
        </div>
      )}

      {/* Frameworks */}
      <Card className="p-6 border-2 border-black shadow-brutal">
        <h2 className="text-2xl font-bold mb-4">Compliance Frameworks</h2>

        {complianceError && (
          <div className="mb-4 p-4 border-2 border-red-500 bg-red-50">
            <p className="text-red-600">{complianceError.message}</p>
          </div>
        )}

        {frameworks.length === 0 ? (
          <div className="text-center py-12">
            <IconShield className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium mb-2">No frameworks configured</p>
            <p className="text-muted-foreground">
              Compliance frameworks will appear here once configured
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {frameworks.map((framework) => (
              <div
                key={framework.id}
                className="p-4 border-2 border-black bg-white"
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-bold text-lg">{framework.name}</h3>
                  <Badge variant="default" className="border-2 border-black">
                    {framework.controls.length} controls
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground mb-3">
                  {framework.description}
                </p>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Compliance Progress</span>
                    <span className="font-bold">
                      {complianceData?.frameworks?.find(f => f.name === framework.name)?.compliance || 0}%
                    </span>
                  </div>
                  <Progress
                    value={complianceData?.frameworks?.find(f => f.name === framework.name)?.compliance || 0}
                    className="h-3 border-2 border-black"
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}

