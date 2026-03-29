'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRisks } from '@/lib/api/hooks/useRisks'
import { useEvidence } from '@/lib/api/hooks/useEvidence'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Progress } from '@/components/ui/progress'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { riskAssessmentSchema, type RiskAssessmentFormData } from '@/lib/validations/schemas'
import { useToast } from '@/hooks/use-toast'
import { Skeleton } from '@/components/ui/skeleton'
import { PieChart } from '@/components/charts/PieChart'
import {
  IconAlertTriangle,
  IconArrowRight,
  IconClipboardCheck,
  IconPlus,
  IconRouteAltLeft,
  IconShieldCheck,
  IconShieldOff,
  IconSparkles,
} from '@tabler/icons-react'

const riskTypeOptions = [
  'bias',
  'compliance',
  'monitoring',
  'security',
  'explainability',
  'documentation',
]

export default function RisksPage() {
  const { selectedSystem } = useSystemContext()
  const { data: risks, summary, loading, error, assessRisks } = useRisks(selectedSystem.id)
  const { summary: evidenceSummary } = useEvidence(selectedSystem.id)
  const { toast } = useToast()
  const [dialogOpen, setDialogOpen] = useState(false)

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
    reset,
  } = useForm<RiskAssessmentFormData>({
    resolver: zodResolver(riskAssessmentSchema),
    defaultValues: {
      systemId: selectedSystem.id,
      riskType: 'bias',
      severity: 'medium',
      description: '',
    },
  })

  const onSubmit = async (formData: RiskAssessmentFormData) => {
    try {
      await assessRisks({
        ...formData,
        systemId: selectedSystem.id,
      })
      toast({
        title: 'Risk assessed',
        description: `Added a scoped risk entry for ${selectedSystem.name}.`,
      })
      setDialogOpen(false)
      reset({
        systemId: selectedSystem.id,
        riskType: 'bias',
        severity: 'medium',
        description: '',
      })
    } catch (submissionError) {
      toast({
        title: 'Assessment failed',
        description: submissionError instanceof Error ? submissionError.message : 'An error occurred',
        variant: 'destructive',
      })
    }
  }

  const riskDistribution = [
    { name: 'Critical', value: summary.bySeverity.critical },
    { name: 'High', value: summary.bySeverity.high },
    { name: 'Medium', value: summary.bySeverity.medium },
    { name: 'Low', value: summary.bySeverity.low },
  ].filter((item) => item.value > 0)

  const getSeverityBadge = (severity: string) => {
    const variants: Record<string, string> = {
      critical: 'bg-red-100 text-red-800 border-red-500',
      high: 'bg-orange text-black border-black',
      medium: 'bg-amber-100 text-amber-800 border-amber-500',
      low: 'bg-emerald-100 text-emerald-800 border-emerald-500',
    }
    return (
      <Badge className={`border-2 font-black uppercase ${variants[severity] || variants.low}`}>
        {severity}
      </Badge>
    )
  }

  if (loading && !risks.length) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-24 w-full" />
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-4">
          {[...Array(4)].map((_, index) => (
            <Skeleton key={index} className="h-32" />
          ))}
        </div>
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Card className="overflow-hidden border-4 border-black bg-[linear-gradient(135deg,#ffe7cc_0%,#fff 55%,#eff9f0_100%)] shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
        <CardContent className="grid gap-0 p-0 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="border-b-4 border-black p-6 xl:border-b-0 xl:border-r-4">
            <p className="text-xs font-black uppercase tracking-[0.22em] text-muted-foreground">Risk Register</p>
            <h1 className="mt-2 text-4xl font-black uppercase">Govern {selectedSystem.name}</h1>
            <p className="mt-3 max-w-2xl text-sm text-slate-700">
              This page should help the governance team decide whether the selected AI system can move forward,
              what is blocking it, and which evidence or remediation steps still need work.
            </p>

            <div className="mt-5 grid gap-4 md:grid-cols-3">
              <div className="border-2 border-black bg-white p-4 shadow-[4px_4px_0px_0px_#000]">
                <p className="text-xs font-bold uppercase text-muted-foreground">Open Risks</p>
                <p className="mt-2 text-4xl font-black">{summary.open}</p>
              </div>
              <div className="border-2 border-black bg-white p-4 shadow-[4px_4px_0px_0px_#000]">
                <p className="text-xs font-bold uppercase text-muted-foreground">Automated Risks</p>
                <p className="mt-2 text-4xl font-black">{summary.automated}</p>
              </div>
              <div className="border-2 border-black bg-white p-4 shadow-[4px_4px_0px_0px_#000]">
                <p className="text-xs font-bold uppercase text-muted-foreground">Readiness Impact</p>
                <p className="mt-2 text-4xl font-black">{Math.max(0, selectedSystem.readiness - summary.open * 4)}%</p>
                <Progress
                  value={Math.max(0, selectedSystem.readiness - summary.open * 4)}
                  className="mt-3 h-3 border-2 border-black"
                />
              </div>
            </div>
          </div>

          <div className="bg-black p-6 text-white">
            <p className="text-xs font-black uppercase tracking-[0.22em] text-orange">Next Actions</p>
            <div className="mt-4 space-y-3">
              {/* Evidence completeness indicator */}
              <Link href="/evidence" className="block border-2 border-white bg-white/10 p-4 transition hover:bg-orange hover:text-black">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    {evidenceSummary.decisionReadiness === 'review_ready' ? (
                      <IconShieldCheck className="h-5 w-5 shrink-0 text-emerald-400" />
                    ) : (
                      <IconShieldOff className="h-5 w-5 shrink-0 text-red-400" />
                    )}
                    <p className="font-black uppercase">Evidence completeness</p>
                  </div>
                  {evidenceSummary.missingSignals.length > 0 && (
                    <span className="shrink-0 rounded border-2 border-red-500 bg-red-500 px-2 py-0.5 text-xs font-black text-white">
                      {evidenceSummary.missingSignals.length} gap{evidenceSummary.missingSignals.length !== 1 ? 's' : ''}
                    </span>
                  )}
                </div>
                <p className="mt-1 text-sm opacity-90">
                  {evidenceSummary.decisionReadiness === 'review_ready'
                    ? 'Evidence is linked and ready for approval review.'
                    : evidenceSummary.recommendedNextStep || 'Evidence gaps detected — review before proceeding to approval.'}
                </p>
              </Link>
              <Link href="/ai-governance" className="block border-2 border-white bg-white/10 p-4 transition hover:bg-orange hover:text-black">
                <p className="font-black uppercase">Review failed controls</p>
                <p className="mt-1 text-sm opacity-90">Use governance review to validate whether blockers are evidence, policy, or remediation gaps.</p>
              </Link>
              <Link href="/remediation" className="block border-2 border-white bg-white/10 p-4 transition hover:bg-orange hover:text-black">
                <p className="font-black uppercase">Open remediation work</p>
                <p className="mt-1 text-sm opacity-90">Turn unresolved risk items into owned corrective actions before release approval.</p>
              </Link>
              <Link href="/audit-reports" className="block border-2 border-white bg-white/10 p-4 transition hover:bg-orange hover:text-black">
                <p className="font-black uppercase">Export current state</p>
                <p className="mt-1 text-sm opacity-90">Use reports after blockers and evidence gaps are reviewed, not before.</p>
              </Link>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[0.85fr_1.15fr]">
        <div className="space-y-6">
          {riskDistribution.length > 0 && (
            <PieChart title="Scoped Risk Distribution" data={riskDistribution} />
          )}

          <Card>
            <CardHeader className="border-b-2 border-black bg-[#fff4de]">
              <CardTitle className="text-xl font-black uppercase">How To Use This Page</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 p-6">
              <div className="border-2 border-black p-4">
                <div className="flex items-center gap-3">
                  <IconSparkles className="h-5 w-5" />
                  <div>
                    <p className="font-black uppercase">Automated Intake</p>
                    <p className="text-sm text-slate-700">Risk suggestions are generated from the MIT and IBM AI risk libraries for the selected system.</p>
                  </div>
                </div>
              </div>
              <div className="border-2 border-black p-4">
                <div className="flex items-center gap-3">
                  <IconClipboardCheck className="h-5 w-5" />
                  <div>
                    <p className="font-black uppercase">Manual Assessment</p>
                    <p className="text-sm text-slate-700">Add system-specific findings when the automated register is incomplete or too generic.</p>
                  </div>
                </div>
              </div>
              <div className="border-2 border-black p-4">
                <div className="flex items-center gap-3">
                  <IconRouteAltLeft className="h-5 w-5" />
                  <div>
                    <p className="font-black uppercase">Workflow Link</p>
                    <p className="text-sm text-slate-700">A risk is only useful if it leads into evidence review, remediation, and approval.</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="border-2 border-black shadow-brutal">
          <CardHeader className="flex flex-row items-center justify-between border-b-2 border-black bg-white p-6">
            <div>
              <CardTitle className="text-2xl font-black uppercase">Scoped Risks</CardTitle>
              <p className="mt-1 text-sm text-muted-foreground">
                Showing risks for <span className="font-bold">{selectedSystem.name}</span>
              </p>
            </div>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="default">
                  <IconPlus className="mr-2 h-4 w-4" />
                  Assess Risk
                </Button>
              </DialogTrigger>
              <DialogContent className="border-2 border-black shadow-brutal-lg">
                <DialogHeader>
                  <DialogTitle>Assess Risk For {selectedSystem.name}</DialogTitle>
                  <DialogDescription>
                    This creates a manual risk entry scoped to the current AI system.
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="systemId">System ID</Label>
                    <Input
                      id="systemId"
                      value={selectedSystem.id}
                      readOnly
                      className="border-2 border-black bg-muted"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="riskType">Risk Type</Label>
                    <Select
                      defaultValue="bias"
                      onValueChange={(value) => {
                        setValue('riskType', value, { shouldValidate: true })
                      }}
                    >
                      <SelectTrigger className="border-2 border-black">
                        <SelectValue placeholder="Select risk type" />
                      </SelectTrigger>
                      <SelectContent>
                        {riskTypeOptions.map((option) => (
                          <SelectItem key={option} value={option}>
                            {option}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {errors.riskType && (
                      <p className="text-sm text-red-600">{errors.riskType.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="severity">Severity</Label>
                    <Select
                      defaultValue="medium"
                      onValueChange={(value) => {
                        setValue('severity', value as RiskAssessmentFormData['severity'], { shouldValidate: true })
                      }}
                    >
                      <SelectTrigger className="border-2 border-black">
                        <SelectValue placeholder="Select severity" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="critical">Critical</SelectItem>
                      </SelectContent>
                    </Select>
                    {errors.severity && (
                      <p className="text-sm text-red-600">{errors.severity.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                      id="description"
                      {...register('description')}
                      className="border-2 border-black"
                      rows={4}
                    />
                    {errors.description && (
                      <p className="text-sm text-red-600">{errors.description.message}</p>
                    )}
                  </div>

                  <div className="flex gap-2">
                    <Button type="submit" variant="default" className="flex-1">
                      Assess
                    </Button>
                    <Button type="button" variant="noShadow" onClick={() => setDialogOpen(false)}>
                      Cancel
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </CardHeader>

          <CardContent className="p-6">
            {error && (
              <div className="mb-4 border-2 border-red-500 bg-red-50 p-4">
                <p className="text-red-600">{error.message}</p>
              </div>
            )}

            {risks.length === 0 ? (
              <div className="py-12 text-center">
                <IconAlertTriangle className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
                <p className="mb-2 text-lg font-medium">No risks identified yet</p>
                <p className="mb-4 text-muted-foreground">
                  Start with an automated or manual assessment for this AI system.
                </p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="border-2 border-black">
                    <TableHead className="font-bold">Title</TableHead>
                    <TableHead className="font-bold">Severity</TableHead>
                    <TableHead className="font-bold">Status</TableHead>
                    <TableHead className="font-bold">Description</TableHead>
                    <TableHead className="font-bold">Next Step</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {risks.map((risk) => (
                    <TableRow key={risk.id} className="border-b-2 border-black">
                      <TableCell className="font-medium">{risk.title}</TableCell>
                      <TableCell>{getSeverityBadge(risk.severity)}</TableCell>
                      <TableCell>
                        <Badge variant="default" className="border-2 border-black uppercase">
                          {risk.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-md">
                        <p className="line-clamp-2 text-sm text-slate-700">{risk.description}</p>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col gap-2">
                          <Button asChild variant="noShadow" size="sm">
                            <Link href={risk.severity === 'critical' || risk.severity === 'high' ? '/remediation' : '/ai-governance'}>
                              Open
                              <IconArrowRight className="ml-2 h-4 w-4" />
                            </Link>
                          </Button>
                          <Button asChild variant="neutral" size="sm">
                            <Link
                              href={{
                                pathname: '/remediation',
                                query: {
                                  riskId: risk.id,
                                  title: risk.title,
                                  description: risk.description,
                                  priority: risk.severity,
                                },
                              }}
                            >
                              Create task
                              <IconArrowRight className="ml-2 h-4 w-4" />
                            </Link>
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
