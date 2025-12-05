'use client'

import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { IconShield, IconCheck, IconX, IconAlertTriangle } from '@tabler/icons-react'
import { useCompliance } from '@/lib/api/hooks/useCompliance'

export default function CompliancePage() {
  const { data, loading, error } = useCompliance()
  
  const frameworks = data?.frameworks || []
  const controls = data?.controls || []

  const getStatusBadge = (status: string) => {
    if (status === 'compliant') {
      return <Badge variant="default" className="border-2 border-black bg-green-500">Compliant</Badge>
    } else if (status === 'partial') {
      return <Badge variant="secondary" className="border-2 border-black bg-yellow-400">Partial</Badge>
    } else {
      return <Badge variant="destructive" className="border-2 border-black">Non-Compliant</Badge>
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="space-y-6">
        <Alert className="border-2 border-red-500 shadow-brutal">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertTitle>Error Loading Compliance Data</AlertTitle>
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold">Compliance</h1>
        <p className="text-muted-foreground mt-1">
          Monitor compliance with AI governance frameworks
        </p>
      </div>

      {/* Framework Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {frameworks.map((framework) => (
          <Card key={framework.name} className="p-6 border-2 border-black shadow-brutal">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold">{framework.name}</h3>
              {getStatusBadge(framework.status)}
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Compliance</span>
                <span className="text-sm font-bold">{framework.compliance}%</span>
              </div>
              <Progress value={framework.compliance} className="h-3 border-2 border-black" />
            </div>
          </Card>
        ))}
      </div>

      {/* Controls */}
      <Card className="p-6 border-2 border-black shadow-brutal">
        <h2 className="text-2xl font-bold mb-4">Compliance Controls</h2>
        <div className="space-y-3">
          {controls.map((control) => (
            <div
              key={control.id}
              className="p-4 border-2 border-black bg-white flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                {control.status === 'compliant' ? (
                  <IconCheck className="h-5 w-5 text-green-600" />
                ) : control.status === 'partial' ? (
                  <IconAlertTriangle className="h-5 w-5 text-yellow-600" />
                ) : (
                  <IconX className="h-5 w-5 text-red-600" />
                )}
                <div>
                  <p className="font-medium">{control.name}</p>
                  <p className="text-sm text-muted-foreground">{control.framework}</p>
                </div>
              </div>
              {getStatusBadge(control.status)}
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}

