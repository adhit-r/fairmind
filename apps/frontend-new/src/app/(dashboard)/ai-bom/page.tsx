'use client'

import { useState, useMemo } from 'react'
import { useAIBOM, useAIBOMStats } from '@/lib/api/hooks/useAIBOM'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { StatCard } from '@/components/charts/StatCard'
import { Progress } from '@/components/ui/progress'
import { IconFileText, IconAlertTriangle, IconCheck, IconUpload, IconRefresh, IconPackage, IconClock, IconShield } from '@tabler/icons-react'
import { useToast } from '@/hooks/use-toast'

export default function AIBOMPage() {
  const { documents, loading, error, refetch, createBOM } = useAIBOM()
  const { stats, loading: statsLoading } = useAIBOMStats()
  const { toast } = useToast()
  
  // Extract all components from all documents
  const components = useMemo(() => {
    if (!documents || documents.length === 0) return []
    return documents.flatMap(doc => doc.components || [])
  }, [documents])

  const getRiskBadge = (risk?: string) => {
    const variants: Record<string, { variant: 'default' | 'secondary' | 'destructive', label: string }> = {
      low: { variant: 'default', label: 'Low' },
      medium: { variant: 'secondary', label: 'Medium' },
      high: { variant: 'destructive', label: 'High' },
      critical: { variant: 'destructive', label: 'Critical' },
    }
    const config = variants[risk || 'low'] || variants.low
    return <Badge variant={config.variant} className="border-2 border-black">{config.label}</Badge>
  }

  const handleGenerateBOM = async () => {
    try {
      await createBOM({
        projectName: 'Default Project',
        description: 'Auto-generated BOM',
      })
      toast({
        title: "BOM Generated",
        description: "AI Bill of Materials has been generated successfully.",
      })
    } catch (err) {
      toast({
        title: "Generation failed",
        description: err instanceof Error ? err.message : "An error occurred",
        variant: "destructive",
      })
    }
  }

  if (loading || statsLoading) {
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

  if (error && !documents.length) {
    return (
      <div className="space-y-6">
        <Alert className="border-2 border-red-500 shadow-brutal">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertTitle>Error Loading AI BOM</AlertTitle>
          <AlertDescription>
            {error.message}
            <br />
            <Button variant="default" className="mt-4" onClick={() => refetch()}>
              <IconRefresh className="mr-2 h-4 w-4" />
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold">AI Bill of Materials</h1>
          <p className="text-muted-foreground mt-1">
            Track and manage AI model components and dependencies
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="default" onClick={() => refetch()}>
            <IconRefresh className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button variant="default" onClick={handleGenerateBOM}>
            <IconUpload className="mr-2 h-4 w-4" />
            Generate BOM
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Total Components"
            value={stats.totalComponents || components.length}
            icon={<IconPackage className="h-5 w-5" />}
          />
          <StatCard
            title="Vulnerabilities"
            value={stats.vulnerableComponents || components.filter(c => (c.vulnerabilities || 0) > 0).length}
            icon={<IconAlertTriangle className="h-5 w-5" />}
          />
          <StatCard
            title="Compliance Score"
            value={`${stats.complianceScore || 0}%`}
            icon={<IconShield className="h-5 w-5" />}
          />
          <StatCard
            title="Last Scan"
            value={stats.lastScan ? new Date(stats.lastScan).toLocaleDateString() : 'Never'}
            icon={<IconClock className="h-5 w-5" />}
          />
        </div>
      )}

      <Tabs defaultValue="components" className="space-y-4">
        <TabsList className="border-2 border-black">
          <TabsTrigger value="components" className="border-r-2 border-black">Components</TabsTrigger>
          <TabsTrigger value="vulnerabilities" className="border-r-2 border-black">Vulnerabilities</TabsTrigger>
          <TabsTrigger value="licenses">Licenses</TabsTrigger>
        </TabsList>

        <TabsContent value="components">
          <Card className="p-6 border-2 border-black shadow-brutal">
            {components.length === 0 ? (
              <div className="text-center py-12">
                <IconPackage className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-lg font-medium mb-2">No components found</p>
                <p className="text-muted-foreground mb-4">
                  Generate a BOM to start tracking components
                </p>
                <Button variant="default" onClick={handleGenerateBOM}>
                  <IconUpload className="mr-2 h-4 w-4" />
                  Generate BOM
                </Button>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="border-2 border-black">
                    <TableHead className="font-bold">Component</TableHead>
                    <TableHead className="font-bold">Version</TableHead>
                    <TableHead className="font-bold">Type</TableHead>
                    <TableHead className="font-bold">Risk Level</TableHead>
                    <TableHead className="font-bold">Status</TableHead>
                    <TableHead className="font-bold">Vulnerabilities</TableHead>
                    <TableHead className="font-bold">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {components.map((component) => (
                    <TableRow key={component.id} className="border-b-2 border-black">
                      <TableCell className="font-medium">{component.name}</TableCell>
                      <TableCell className="font-mono text-sm">{component.version}</TableCell>
                      <TableCell>{component.type}</TableCell>
                      <TableCell>{getRiskBadge(component.riskLevel)}</TableCell>
                      <TableCell>
                        <Badge variant="default" className="border-2 border-black">
                          {component.status || 'active'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span className={component.vulnerabilities && component.vulnerabilities > 0 ? 'text-red-600 font-bold' : 'text-green-600'}>
                          {component.vulnerabilities || 0}
                        </span>
                      </TableCell>
                      <TableCell>
                        <Button variant="noShadow" size="sm">
                          View Details
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="vulnerabilities">
          <Card className="p-6 border-2 border-black shadow-brutal">
            {components.filter(c => (c.vulnerabilities || 0) > 0).length === 0 ? (
              <div className="text-center py-12">
                <IconCheck className="h-12 w-12 mx-auto text-green-600 mb-4" />
                <p className="text-lg font-medium mb-2">No vulnerabilities found</p>
                <p className="text-muted-foreground">
                  All components are up to date and secure
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {components
                  .filter(c => (c.vulnerabilities || 0) > 0)
                  .map((component) => (
                    <Alert key={component.id} className="border-2 border-red-500">
                      <IconAlertTriangle className="h-4 w-4" />
                      <AlertTitle>{component.name} v{component.version}</AlertTitle>
                      <AlertDescription>
                        {component.vulnerabilities} vulnerabilities found
                        {component.riskLevel && ` - Risk Level: ${component.riskLevel}`}
                      </AlertDescription>
                    </Alert>
                  ))}
              </div>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="licenses">
          <Card className="p-6 border-2 border-black shadow-brutal">
            {components.length === 0 ? (
              <div className="text-center py-12">
                <IconFileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-lg font-medium mb-2">No components found</p>
                <p className="text-muted-foreground">
                  Generate a BOM to view license information
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {components.map((component) => (
                  <div
                    key={component.id}
                    className="p-4 border-2 border-black bg-white flex items-center justify-between"
                  >
                    <div>
                      <p className="font-medium">{component.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {component.license || 'License not specified'}
                      </p>
                    </div>
                    <IconCheck className="h-5 w-5 text-green-600" />
                  </div>
                ))}
              </div>
            )}
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

