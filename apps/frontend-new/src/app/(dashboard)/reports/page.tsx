'use client'

import { useState } from 'react'
import { useReports } from '@/lib/api/hooks/useReports'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { reportSchema, type ReportFormData } from '@/lib/validations/schemas'
import { useToast } from '@/hooks/use-toast'
import { Skeleton } from '@/components/ui/skeleton'
import { IconFileAnalytics, IconPlus, IconDownload } from '@tabler/icons-react'

export default function ReportsPage() {
  const { data: reports, loading, error, generateReport } = useReports()
  const { toast } = useToast()
  const [dialogOpen, setDialogOpen] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm({
    resolver: zodResolver(reportSchema),
    defaultValues: {
      format: 'pdf' as const,
      includeCharts: true,
    },
  })

  const onSubmit = async (data: any) => {
    try {
      await generateReport(data)
      toast({
        title: 'Report generated',
        description: 'Your report has been generated successfully.',
      })
      setDialogOpen(false)
      reset()
    } catch (err) {
      toast({
        title: 'Generation failed',
        description: err instanceof Error ? err.message : 'An error occurred',
        variant: 'destructive',
      })
    }
  }

  if (loading && !reports.length) {
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold">Reports</h1>
          <p className="text-muted-foreground mt-1">
            Generate and manage compliance and analysis reports
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button variant="default">
              <IconPlus className="mr-2 h-4 w-4" />
              Generate Report
            </Button>
          </DialogTrigger>
          <DialogContent className="border-2 border-black shadow-brutal-lg">
            <DialogHeader>
              <DialogTitle>Generate Report</DialogTitle>
              <DialogDescription>
                Configure and generate a new report
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="type">Report Type</Label>
                <Select
                  onValueChange={(value) => {
                    register('type').onChange({ target: { value } })
                  }}
                >
                  <SelectTrigger className="border-2 border-black">
                    <SelectValue placeholder="Select report type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="compliance">Compliance</SelectItem>
                    <SelectItem value="bias">Bias Analysis</SelectItem>
                    <SelectItem value="security">Security</SelectItem>
                    <SelectItem value="performance">Performance</SelectItem>
                  </SelectContent>
                </Select>
                {errors.type && (
                  <p className="text-sm text-red-600">{errors.type.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="format">Format</Label>
                <Select
                  defaultValue="pdf"
                  onValueChange={(value) => {
                    register('format').onChange({ target: { value } })
                  }}
                >
                  <SelectTrigger className="border-2 border-black">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pdf">PDF</SelectItem>
                    <SelectItem value="json">JSON</SelectItem>
                    <SelectItem value="csv">CSV</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex gap-2">
                <Button type="submit" variant="default" className="flex-1">
                  Generate
                </Button>
                <Button
                  type="button"
                  variant="noShadow"
                  onClick={() => setDialogOpen(false)}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Reports Table */}
      <Card className="p-6 border-2 border-black shadow-brutal">
        {error && (
          <div className="mb-4 p-4 border-2 border-red-500 bg-red-50">
            <p className="text-red-600">{error.message}</p>
          </div>
        )}

        {reports.length === 0 ? (
          <div className="text-center py-12">
            <IconFileAnalytics className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium mb-2">No reports yet</p>
            <p className="text-muted-foreground mb-4">
              Generate your first report to get started
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="border-2 border-black">
                <TableHead className="font-bold">Title</TableHead>
                <TableHead className="font-bold">Type</TableHead>
                <TableHead className="font-bold">Status</TableHead>
                <TableHead className="font-bold">Created</TableHead>
                <TableHead className="font-bold">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {reports.map((report) => (
                <TableRow key={report.id} className="border-b-2 border-black">
                  <TableCell className="font-medium">{report.title}</TableCell>
                  <TableCell>
                    <Badge variant="default" className="border-2 border-black">
                      {report.type}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={report.status === 'completed' ? 'default' : 'secondary'}
                      className="border-2 border-black"
                    >
                      {report.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {new Date(report.createdAt).toLocaleString()}
                  </TableCell>
                  <TableCell>
                    <Button variant="noShadow" size="sm">
                      <IconDownload className="mr-2 h-4 w-4" />
                      Download
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

