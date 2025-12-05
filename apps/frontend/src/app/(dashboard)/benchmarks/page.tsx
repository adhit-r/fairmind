'use client'

import { useState } from 'react'
import { useBenchmarks } from '@/lib/api/hooks/useBenchmarks'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { benchmarkSchema, type BenchmarkFormData } from '@/lib/validations/schemas'
import { useToast } from '@/hooks/use-toast'
import { Skeleton } from '@/components/ui/skeleton'
import { IconTrendingUp, IconPlus, IconCheck, IconX } from '@tabler/icons-react'

export default function BenchmarksPage() {
  const { data: benchmarks, loading, error, runBenchmark } = useBenchmarks()
  const { toast } = useToast()
  const [dialogOpen, setDialogOpen] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<BenchmarkFormData>({
    resolver: zodResolver(benchmarkSchema),
  })

  const onSubmit = async (data: BenchmarkFormData) => {
    try {
      await runBenchmark(data)
      toast({
        title: 'Benchmark started',
        description: 'Benchmark run has been initiated. Results will be available shortly.',
      })
      setDialogOpen(false)
      reset()
    } catch (err) {
      toast({
        title: 'Benchmark failed',
        description: err instanceof Error ? err.message : 'An error occurred',
        variant: 'destructive',
      })
    }
  }

  const getStatusBadge = (status: string) => {
    if (status === 'completed') {
      return <Badge variant="default" className="border-2 border-black bg-green-500">Completed</Badge>
    } else if (status === 'running') {
      return <Badge variant="secondary" className="border-2 border-black bg-yellow-400">Running</Badge>
    } else {
      return <Badge variant="destructive" className="border-2 border-black">Failed</Badge>
    }
  }

  if (loading && !benchmarks.length) {
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
          <h1 className="text-4xl font-bold">Benchmarks</h1>
          <p className="text-muted-foreground mt-1">
            Model performance benchmarking and evaluation
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button variant="default">
              <IconPlus className="mr-2 h-4 w-4" />
              Run Benchmark
            </Button>
          </DialogTrigger>
          <DialogContent className="border-2 border-black shadow-brutal-lg">
            <DialogHeader>
              <DialogTitle>Run New Benchmark</DialogTitle>
              <DialogDescription>
                Configure and start a new benchmark run
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="modelId">Model ID</Label>
                <Input
                  id="modelId"
                  {...register('modelId')}
                  className="border-2 border-black"
                />
                {errors.modelId && (
                  <p className="text-sm text-red-600">{errors.modelId.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="benchmarkType">Benchmark Type</Label>
                <Select
                  onValueChange={(value) => {
                    register('benchmarkType').onChange({ target: { value } })
                  }}
                >
                  <SelectTrigger className="border-2 border-black">
                    <SelectValue placeholder="Select benchmark type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="performance">Performance</SelectItem>
                    <SelectItem value="bias">Bias Detection</SelectItem>
                    <SelectItem value="fairness">Fairness</SelectItem>
                    <SelectItem value="robustness">Robustness</SelectItem>
                  </SelectContent>
                </Select>
                {errors.benchmarkType && (
                  <p className="text-sm text-red-600">{errors.benchmarkType.message}</p>
                )}
              </div>

              <div className="flex gap-2">
                <Button type="submit" variant="default" className="flex-1">
                  Run Benchmark
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

      {/* Benchmarks Table */}
      <Card className="p-6 border-2 border-black shadow-brutal">
        {error && (
          <div className="mb-4 p-4 border-2 border-red-500 bg-red-50">
            <p className="text-red-600">{error.message}</p>
          </div>
        )}

        {benchmarks.length === 0 ? (
          <div className="text-center py-12">
            <IconTrendingUp className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium mb-2">No benchmarks yet</p>
            <p className="text-muted-foreground mb-4">
              Run your first benchmark to get started
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="border-2 border-black">
                <TableHead className="font-bold">Name</TableHead>
                <TableHead className="font-bold">Type</TableHead>
                <TableHead className="font-bold">Status</TableHead>
                <TableHead className="font-bold">Timestamp</TableHead>
                <TableHead className="font-bold">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {benchmarks.map((benchmark) => (
                <TableRow key={benchmark.id} className="border-b-2 border-black">
                  <TableCell className="font-medium">{benchmark.name}</TableCell>
                  <TableCell>
                    <Badge variant="default" className="border-2 border-black">
                      {benchmark.type}
                    </Badge>
                  </TableCell>
                  <TableCell>{getStatusBadge(benchmark.status)}</TableCell>
                  <TableCell>
                    {new Date(benchmark.timestamp).toLocaleString()}
                  </TableCell>
                  <TableCell>
                    <Button variant="noShadow" size="sm">
                      View Results
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

