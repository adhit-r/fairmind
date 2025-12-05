'use client'

import { useState } from 'react'
import { useSecurityScans } from '@/lib/api/hooks/useSecurity'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/hooks/use-toast'
import {
  IconShield,
  IconAlertTriangle,
  IconCheck,
  IconX,
  IconRefresh,
  IconPlayerPlay,
} from '@tabler/icons-react'

export default function SecurityPage() {
  const { scans, loading, error } = useSecurityScans()
  const { toast } = useToast()
  const [scanType, setScanType] = useState<string>('')

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { variant: 'default' | 'secondary' | 'destructive', label: string }> = {
      completed: { variant: 'default', label: 'Completed' },
      running: { variant: 'secondary', label: 'Running' },
      pending: { variant: 'secondary', label: 'Pending' },
      failed: { variant: 'destructive', label: 'Failed' },
    }
    const config = variants[status] || variants.pending
    return <Badge variant={config.variant} className="border-2 border-black">{config.label}</Badge>
  }

  const handleRunScan = () => {
    if (!scanType) {
      toast({
        title: "Select scan type",
        description: "Please select a scan type before running.",
        variant: "destructive",
      })
      return
    }
    toast({
      title: "Starting scan...",
      description: `Running ${scanType} scan. This may take a few minutes.`,
    })
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-96" />
      </div>
    )
  }

  if (error) {
    return (
      <Alert className="border-2 border-red-500 shadow-brutal">
        <IconAlertTriangle className="h-4 w-4" />
        <AlertDescription>{error.message}</AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold">Security Scans</h1>
          <p className="text-muted-foreground mt-1">
            Scan containers, LLMs, and models for security vulnerabilities
          </p>
        </div>
        <div className="flex gap-2">
          <Select value={scanType} onValueChange={setScanType}>
            <SelectTrigger className="w-48 border-2 border-black">
              <SelectValue placeholder="Select scan type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="container">Container Scan</SelectItem>
              <SelectItem value="llm">LLM Test</SelectItem>
              <SelectItem value="model">Model Analyze</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="default" onClick={handleRunScan}>
            <IconPlayerPlay className="mr-2 h-4 w-4" />
            Run Scan
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4 border-2 border-black shadow-brutal">
          <p className="text-sm text-muted-foreground">Total Scans</p>
          <p className="text-2xl font-bold">{scans.length}</p>
        </Card>
        <Card className="p-4 border-2 border-black shadow-brutal">
          <p className="text-sm text-muted-foreground">Completed</p>
          <p className="text-2xl font-bold text-green-600">
            {scans.filter(s => s.status === 'completed').length}
          </p>
        </Card>
        <Card className="p-4 border-2 border-black shadow-brutal">
          <p className="text-sm text-muted-foreground">Running</p>
          <p className="text-2xl font-bold text-blue-600">
            {scans.filter(s => s.status === 'running').length}
          </p>
        </Card>
        <Card className="p-4 border-2 border-black shadow-brutal">
          <p className="text-sm text-muted-foreground">Failed</p>
          <p className="text-2xl font-bold text-red-600">
            {scans.filter(s => s.status === 'failed').length}
          </p>
        </Card>
      </div>

      {/* Scans Table */}
      <Card className="p-6 border-2 border-black shadow-brutal">
        {scans.length === 0 ? (
          <div className="text-center py-12">
            <IconShield className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium mb-2">No security scans yet</p>
            <p className="text-muted-foreground mb-4">
              Run your first security scan to get started
            </p>
            <Button variant="default" onClick={handleRunScan}>
              <IconPlayerPlay className="mr-2 h-4 w-4" />
              Run Scan
            </Button>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="border-2 border-black">
                <TableHead className="font-bold">Scan ID</TableHead>
                <TableHead className="font-bold">Status</TableHead>
                <TableHead className="font-bold">Risk Score</TableHead>
                <TableHead className="font-bold">Vulnerabilities</TableHead>
                <TableHead className="font-bold">Timestamp</TableHead>
                <TableHead className="font-bold">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {scans.map((scan) => (
                <TableRow key={scan.scanId} className="border-b-2 border-black">
                  <TableCell className="font-mono text-sm">{scan.scanId.slice(0, 8)}...</TableCell>
                  <TableCell>{getStatusBadge(scan.status)}</TableCell>
                  <TableCell>
                    {scan.results ? (
                      <span className={scan.results.riskScore > 7 ? 'text-red-600 font-bold' : 'text-green-600'}>
                        {scan.results.riskScore}/10
                      </span>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {scan.results ? scan.results.vulnerabilities.length : 0}
                  </TableCell>
                  <TableCell>
                    {new Date(scan.timestamp).toLocaleString()}
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
    </div>
  )
}

