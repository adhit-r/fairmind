'use client'

import { useEffect, useMemo, useState } from 'react'
import { useAIBOM, useAIBOMFairnessProfile, useAIBOMStats, type FairnessEvidenceComponent } from '@/lib/api/hooks/useAIBOM'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { StatCard } from '@/components/charts/StatCard'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { IconFileText, IconAlertTriangle, IconCheck, IconUpload, IconRefresh, IconPackage, IconClock, IconShield } from '@tabler/icons-react'
import { useToast } from '@/hooks/use-toast'

export default function AIBOMPage() {
  const { documents, loading, error, refetch, createBOM } = useAIBOM()
  const [selectedDocumentId, setSelectedDocumentId] = useState('')
  const selectedDocument = useMemo(() => {
    if (!documents || documents.length === 0) return null
    return documents.find((document) => document.id === selectedDocumentId) || documents[0]
  }, [documents, selectedDocumentId])
  const { stats, loading: statsLoading } = useAIBOMStats(selectedDocument?.id)
  const {
    profile: fairnessProfile,
    loading: fairnessLoading,
    error: fairnessError,
    refetch: refetchFairnessProfile,
  } = useAIBOMFairnessProfile(selectedDocument?.id)
  const { toast } = useToast()

  useEffect(() => {
    if (!documents || documents.length === 0) {
      setSelectedDocumentId('')
      return
    }

    if (!selectedDocumentId || !documents.some((document) => document.id === selectedDocumentId)) {
      setSelectedDocumentId(documents[0].id)
    }
  }, [documents, selectedDocumentId])
  
  const components = useMemo(() => {
    return selectedDocument?.components || []
  }, [selectedDocument])
  const vulnerableComponents = useMemo(
    () => components.filter((component) => typeof component.vulnerabilities === 'number' && component.vulnerabilities > 0),
    [components]
  )
  const unknownVulnerabilityComponents = useMemo(
    () => components.filter((component) => typeof component.vulnerabilities !== 'number'),
    [components]
  )

  const getRiskBadge = (risk?: string) => {
    const variants: Record<string, { variant: 'default' | 'secondary' | 'destructive', label: string }> = {
      none: { variant: 'default', label: 'None' },
      low: { variant: 'default', label: 'Low' },
      medium: { variant: 'secondary', label: 'Medium' },
      high: { variant: 'destructive', label: 'High' },
      critical: { variant: 'destructive', label: 'Critical' },
      unknown: { variant: 'destructive', label: 'Unknown' },
    }
    const config = variants[risk || 'unknown'] || variants.unknown
    return <Badge variant={config.variant} className="border-2 border-black">{config.label}</Badge>
  }

  const getStateBadge = (state?: string) => {
    const normalized = state?.toLowerCase() || 'unknown'
    const variant: 'default' | 'secondary' | 'destructive' =
      ['high', 'critical', 'missing', 'stale', 'unknown', 'untested', 'non_compliant'].includes(normalized)
        ? 'destructive'
        : ['medium', 'simulated', 'pending', 'review_required', 'partial'].includes(normalized)
          ? 'secondary'
          : 'default'

    return (
      <Badge variant={variant} className="border-2 border-black capitalize">
        {normalized.replace(/_/g, ' ')}
      </Badge>
    )
  }

  const formatList = (items: string[] = [], fallback = 'None attached') => {
    return items.length > 0 ? items.join(', ') : fallback
  }

  const evidenceRefsFor = (component: FairnessEvidenceComponent) => {
    const refs = [
      ...component.evidence_refs,
      ...component.bias_tests_run.map((test) => test.evidence_ref).filter(Boolean),
      ...component.remediation_history.map((remediation) => remediation.evidence_ref).filter(Boolean),
    ]
    return Array.from(new Set(refs))
  }

  const evidenceStatesFor = (component: FairnessEvidenceComponent) => {
    const states = [
      component.evidence_freshness.evidence_state,
      ...component.fairness_metrics.map((metric) => metric.evidence_state),
      ...component.bias_tests_run.map((test) => test.evidence_state),
      ...component.known_bias_risks.map((risk) => risk.evidence_state),
      ...component.regulatory_mapping.map((mapping) => mapping.evidence_state),
      ...component.remediation_history.map((remediation) => remediation.validation_state),
    ]
    return Array.from(new Set(states.filter(Boolean)))
  }

  const handleRefresh = () => {
    refetch()
    refetchFairnessProfile()
  }

  const handleGenerateBOM = async () => {
    try {
      await createBOM({
        name: 'Default Project BOM',
        version: '1.0.0',
        description: 'Auto-generated BOM',
        project_name: 'Default Project',
        organization: 'FairMind',
        overall_risk_level: 'medium',
        overall_compliance_status: 'partial',
        components: [
          {
            id: 'default.dataset',
            name: 'Default Dataset',
            type: 'dataset',
            version: 'unknown',
            risk_level: 'medium',
            compliance_status: 'partial',
            component_metadata: {
              profile_component_type: 'dataset',
            },
          },
          {
            id: 'default.model',
            name: 'Default Model',
            type: 'model',
            version: 'unknown',
            risk_level: 'medium',
            compliance_status: 'partial',
            dependencies: ['default.dataset'],
            component_metadata: {
              profile_component_type: 'model',
            },
          },
        ],
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
        <div className="flex flex-wrap items-center justify-end gap-2">
          {documents.length > 0 && selectedDocument && (
            <Select value={selectedDocument.id} onValueChange={setSelectedDocumentId}>
              <SelectTrigger className="w-[280px] border-2 border-black bg-white font-bold">
                <SelectValue placeholder="Select BOM" />
              </SelectTrigger>
              <SelectContent>
                {documents.map((document) => (
                  <SelectItem key={document.id} value={document.id}>
                    {document.projectName}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          <Button variant="default" onClick={handleRefresh}>
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
            value={stats.totalComponents ?? components.length}
            icon={<IconPackage className="h-5 w-5" />}
          />
          <StatCard
            title="Vulnerabilities"
            value={stats.vulnerableComponents ?? vulnerableComponents.length}
            icon={<IconAlertTriangle className="h-5 w-5" />}
          />
          <StatCard
            title="Compliance Score"
            value={typeof stats.complianceScore === 'number' ? `${stats.complianceScore}%` : 'Unknown'}
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
          <TabsTrigger value="licenses" className="border-r-2 border-black">Licenses</TabsTrigger>
          <TabsTrigger value="fairness-evidence">Fairness Evidence</TabsTrigger>
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
                  {components.map((component) => {
                    const vulnerabilityCount = component.vulnerabilities
                    const vulnerabilityClass =
                      typeof vulnerabilityCount !== 'number'
                        ? 'text-muted-foreground font-bold'
                        : vulnerabilityCount > 0
                          ? 'text-red-600 font-bold'
                          : 'text-green-600 font-bold'

                    return (
                      <TableRow key={component.id} className="border-b-2 border-black">
                        <TableCell className="font-medium">{component.name}</TableCell>
                        <TableCell className="font-mono text-sm">{component.version}</TableCell>
                        <TableCell>{component.type}</TableCell>
                        <TableCell>{getRiskBadge(component.riskLevel)}</TableCell>
                        <TableCell>{getStateBadge(component.status || component.complianceStatus)}</TableCell>
                        <TableCell>
                          <span className={vulnerabilityClass}>
                            {typeof vulnerabilityCount === 'number' ? vulnerabilityCount : 'Unknown'}
                          </span>
                        </TableCell>
                        <TableCell>
                          <Button variant="noShadow" size="sm">
                            View Details
                          </Button>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="vulnerabilities">
          <Card className="p-6 border-2 border-black shadow-brutal">
            {components.length === 0 ? (
              <div className="text-center py-12">
                <IconPackage className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-lg font-medium mb-2">No components found</p>
                <p className="text-muted-foreground">
                  Generate a BOM to review vulnerability metadata
                </p>
              </div>
            ) : vulnerableComponents.length === 0 && unknownVulnerabilityComponents.length === 0 ? (
              <div className="text-center py-12">
                <IconCheck className="h-12 w-12 mx-auto text-green-600 mb-4" />
                <p className="text-lg font-medium mb-2">No vulnerabilities found</p>
                <p className="text-muted-foreground">
                  Current BOM metadata reports zero known vulnerabilities
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {vulnerableComponents.map((component) => (
                  <Alert key={component.id} className="border-2 border-red-500">
                    <IconAlertTriangle className="h-4 w-4" />
                    <AlertTitle>{component.name} v{component.version}</AlertTitle>
                    <AlertDescription>
                      {component.vulnerabilities} vulnerabilities found
                      {component.riskLevel && ` - Risk Level: ${component.riskLevel}`}
                    </AlertDescription>
                  </Alert>
                ))}
                {unknownVulnerabilityComponents.map((component) => (
                  <Alert key={component.id} className="border-2 border-black">
                    <IconAlertTriangle className="h-4 w-4" />
                    <AlertTitle>{component.name} v{component.version}</AlertTitle>
                    <AlertDescription>
                      Vulnerability metadata is not attached for this component.
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
                    {component.license ? (
                      <IconCheck className="h-5 w-5 text-green-600" />
                    ) : (
                      <IconAlertTriangle className="h-5 w-5 text-red-600" />
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="fairness-evidence">
          <Card className="p-6 border-2 border-black shadow-brutal">
            {!selectedDocument ? (
              <div className="text-center py-12">
                <IconShield className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-lg font-medium mb-2">No BOM selected</p>
                <p className="text-muted-foreground">
                  Generate a BOM to review fairness evidence state
                </p>
              </div>
            ) : fairnessLoading ? (
              <div className="space-y-4">
                <Skeleton className="h-24 w-full" />
                <Skeleton className="h-64 w-full" />
              </div>
            ) : fairnessError ? (
              <Alert className="border-2 border-red-500">
                <IconAlertTriangle className="h-4 w-4" />
                <AlertTitle>Fairness Evidence Unavailable</AlertTitle>
                <AlertDescription>
                  {fairnessError.message}
                  <br />
                  <Button variant="default" className="mt-4" onClick={() => refetchFairnessProfile()}>
                    <IconRefresh className="mr-2 h-4 w-4" />
                    Retry
                  </Button>
                </AlertDescription>
              </Alert>
            ) : fairnessProfile ? (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="border-2 border-black p-4 bg-white">
                    <p className="text-sm font-medium text-muted-foreground">Overall Severity</p>
                    <div className="mt-2">{getStateBadge(fairnessProfile.risk_summary.overall_severity)}</div>
                  </div>
                  <div className="border-2 border-black p-4 bg-white">
                    <p className="text-sm font-medium text-muted-foreground">Unknowns</p>
                    <p className="text-2xl font-bold mt-1">{fairnessProfile.risk_summary.unknown_count}</p>
                  </div>
                  <div className="border-2 border-black p-4 bg-white">
                    <p className="text-sm font-medium text-muted-foreground">Simulated Evidence</p>
                    <p className="text-2xl font-bold mt-1">{fairnessProfile.risk_summary.simulated_evidence_count}</p>
                  </div>
                  <div className="border-2 border-black p-4 bg-white">
                    <p className="text-sm font-medium text-muted-foreground">Review Status</p>
                    <div className="mt-2">{getStateBadge(fairnessProfile.review_summary.status)}</div>
                  </div>
                </div>

                <Alert className="border-2 border-black">
                  <IconShield className="h-4 w-4" />
                  <AlertTitle>{fairnessProfile.system_name}</AlertTitle>
                  <AlertDescription>
                    {fairnessProfile.risk_summary.reviewer_action}
                  </AlertDescription>
                </Alert>

                <Table>
                  <TableHeader>
                    <TableRow className="border-2 border-black">
                      <TableHead className="font-bold">Component</TableHead>
                      <TableHead className="font-bold">Type</TableHead>
                      <TableHead className="font-bold">Validation</TableHead>
                      <TableHead className="font-bold">Review</TableHead>
                      <TableHead className="font-bold">Unknowns</TableHead>
                      <TableHead className="font-bold">Evidence Refs</TableHead>
                      <TableHead className="font-bold">Risk</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {fairnessProfile.components.map((component) => {
                      const evidenceRefs = evidenceRefsFor(component)

                      return (
                        <TableRow key={component.component_id} className="border-b-2 border-black">
                          <TableCell>
                            <p className="font-medium">{component.component_name}</p>
                            <p className="font-mono text-xs text-muted-foreground">{component.component_id}</p>
                          </TableCell>
                          <TableCell className="capitalize">{component.component_type.replace(/_/g, ' ')}</TableCell>
                          <TableCell>{getStateBadge(component.validation_state)}</TableCell>
                          <TableCell>{getStateBadge(component.review_status)}</TableCell>
                          <TableCell>
                            <span className={component.unknowns.length > 0 ? 'text-red-600 font-bold' : 'text-green-600 font-bold'}>
                              {component.unknowns.length}
                            </span>
                          </TableCell>
                          <TableCell>
                            <span className={evidenceRefs.length > 0 ? 'font-mono text-xs' : 'text-red-600 font-bold'}>
                              {evidenceRefs.length > 0 ? evidenceRefs.length : 'Missing'}
                            </span>
                          </TableCell>
                          <TableCell>{getStateBadge(component.risk_summary.overall_severity)}</TableCell>
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>

                <div className="space-y-4">
                  <div>
                    <h2 className="text-2xl font-bold">Component Evidence Detail</h2>
                    <p className="text-sm text-muted-foreground">
                      Selected BOM: {selectedDocument?.projectName || fairnessProfile.system_name}
                    </p>
                  </div>

                  {fairnessProfile.components.map((component) => {
                    const evidenceRefs = evidenceRefsFor(component)
                    const evidenceStates = evidenceStatesFor(component)

                    return (
                      <div key={component.component_id} className="border-2 border-black bg-white p-4">
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div>
                            <h3 className="text-lg font-bold">{component.component_name}</h3>
                            <p className="font-mono text-xs text-muted-foreground">{component.component_id}</p>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {getStateBadge(component.validation_state)}
                            {getStateBadge(component.review_status)}
                            {getStateBadge(component.risk_summary.overall_severity)}
                          </div>
                        </div>

                        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
                          <div>
                            <p className="text-sm font-bold">Protected Attributes Tested</p>
                            <p className="text-sm text-muted-foreground">
                              {formatList(component.protected_attributes_tested)}
                            </p>
                          </div>
                          <div>
                            <p className="text-sm font-bold">Subgroup Coverage</p>
                            <p className="text-sm text-muted-foreground">
                              Evaluated: {formatList(component.subgroup_coverage.evaluated_groups)}
                            </p>
                            <p className="text-sm text-muted-foreground">
                              Missing: {formatList(component.subgroup_coverage.missing_groups, 'None listed')}
                            </p>
                          </div>
                          <div>
                            <p className="text-sm font-bold">Evidence References</p>
                            <p className="font-mono text-xs text-muted-foreground">
                              {formatList(evidenceRefs)}
                            </p>
                          </div>
                          <div>
                            <p className="text-sm font-bold">Evidence States</p>
                            <p className="text-sm text-muted-foreground">
                              {formatList(evidenceStates)}
                            </p>
                          </div>
                          <div>
                            <p className="text-sm font-bold">Fairness Metrics</p>
                            <p className="text-sm text-muted-foreground">
                              {component.fairness_metrics.length > 0
                                ? component.fairness_metrics
                                    .map((metric) => `${metric.metric}: ${metric.value ?? 'not recorded'} (${metric.evidence_state})`)
                                    .join(', ')
                                : 'None attached'}
                            </p>
                          </div>
                          <div>
                            <p className="text-sm font-bold">Bias Tests</p>
                            <p className="text-sm text-muted-foreground">
                              {component.bias_tests_run.length > 0
                                ? component.bias_tests_run
                                    .map((test) => `${test.test_name}: ${test.result || 'no result'} (${test.evidence_state})`)
                                    .join(', ')
                                : 'None attached'}
                            </p>
                          </div>
                        </div>

                        <div className="mt-4 border-t-2 border-black pt-4">
                          <p className="text-sm font-bold">Reviewer Action</p>
                          <p className="text-sm text-muted-foreground">{component.risk_summary.reviewer_action}</p>
                        </div>

                        {component.unknowns.length > 0 && (
                          <div className="mt-4 border-t-2 border-black pt-4">
                            <p className="text-sm font-bold text-red-600">Unknowns</p>
                            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                              {component.unknowns.map((unknown) => (
                                <li key={unknown}>{unknown}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {component.known_bias_risks.length > 0 && (
                          <div className="mt-4 border-t-2 border-black pt-4">
                            <p className="text-sm font-bold">Known Bias Risks</p>
                            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                              {component.known_bias_risks.map((risk) => (
                                <li key={risk.risk_id}>
                                  {risk.description} Severity: {risk.severity}. Evidence: {risk.evidence_state}.
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {component.remediation_history.length > 0 && (
                          <div className="mt-4 border-t-2 border-black pt-4">
                            <p className="text-sm font-bold">Remediation Validation</p>
                            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                              {component.remediation_history.map((remediation) => (
                                <li key={remediation.remediation_id}>
                                  {remediation.description} Status: {remediation.status}. Validation: {remediation.validation_state}.
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {component.regulatory_mapping.length > 0 && (
                          <div className="mt-4 border-t-2 border-black pt-4">
                            <p className="text-sm font-bold">Regulatory Claims</p>
                            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                              {component.regulatory_mapping.map((mapping) => (
                                <li key={`${mapping.framework}-${mapping.control}-${mapping.claim}`}>
                                  {mapping.framework} {mapping.control}: {mapping.claim}. Evidence: {mapping.evidence_state}.
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <IconShield className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-lg font-medium mb-2">No fairness evidence profile</p>
                <p className="text-muted-foreground">
                  Refresh this BOM to load current fairness evidence state
                </p>
              </div>
            )}
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
