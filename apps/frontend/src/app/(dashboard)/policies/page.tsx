'use client'

import { useState } from 'react'
import { usePolicies } from '@/lib/api/hooks/usePolicies'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { policySchema, type PolicyFormData } from '@/lib/validations/schemas'
import { useToast } from '@/hooks/use-toast'
import { Skeleton } from '@/components/ui/skeleton'
import { IconFileText, IconPlus, IconShield } from '@tabler/icons-react'

export default function PoliciesPage() {
  const [framework, setFramework] = useState<string>('')
  const { data: policies, loading, error, createPolicy } = usePolicies(framework)
  const { toast } = useToast()
  const [dialogOpen, setDialogOpen] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<PolicyFormData>({
    resolver: zodResolver(policySchema),
  })

  const onSubmit = async (data: PolicyFormData) => {
    try {
      await createPolicy(data)
      toast({
        title: 'Policy created',
        description: 'Policy has been created successfully.',
      })
      setDialogOpen(false)
      reset()
    } catch (err) {
      toast({
        title: 'Creation failed',
        description: err instanceof Error ? err.message : 'An error occurred',
        variant: 'destructive',
      })
    }
  }

  if (loading && !policies.length) {
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
          <h1 className="text-4xl font-bold">Policies</h1>
          <p className="text-muted-foreground mt-1">
            Manage governance policies and compliance rules
          </p>
        </div>
        <div className="flex gap-2">
          <Select value={framework} onValueChange={setFramework}>
            <SelectTrigger className="w-48 border-2 border-black">
              <SelectValue placeholder="Filter by framework" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All Frameworks</SelectItem>
              <SelectItem value="eu-ai-act">EU AI Act</SelectItem>
              <SelectItem value="nist">NIST AI RMF</SelectItem>
              <SelectItem value="iso">ISO/IEC 23053</SelectItem>
            </SelectContent>
          </Select>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="default">
                <IconPlus className="mr-2 h-4 w-4" />
                Create Policy
              </Button>
            </DialogTrigger>
            <DialogContent className="border-2 border-black shadow-brutal-lg max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create Policy</DialogTitle>
                <DialogDescription>
                  Define a new governance policy
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Policy Name</Label>
                  <Input
                    id="name"
                    {...register('name')}
                    className="border-2 border-black"
                  />
                  {errors.name && (
                    <p className="text-sm text-red-600">{errors.name.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="framework">Framework</Label>
                  <Select
                    onValueChange={(value) => {
                      register('framework').onChange({ target: { value } })
                    }}
                  >
                    <SelectTrigger className="border-2 border-black">
                      <SelectValue placeholder="Select framework" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="eu-ai-act">EU AI Act</SelectItem>
                      <SelectItem value="nist">NIST AI RMF</SelectItem>
                      <SelectItem value="iso">ISO/IEC 23053</SelectItem>
                      <SelectItem value="gdpr">GDPR</SelectItem>
                    </SelectContent>
                  </Select>
                  {errors.framework && (
                    <p className="text-sm text-red-600">{errors.framework.message}</p>
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
                </div>

                <div className="flex gap-2">
                  <Button type="submit" variant="default" className="flex-1">
                    Create
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
      </div>

      {/* Policies Table */}
      <Card className="p-6 border-2 border-black shadow-brutal">
        {error && (
          <div className="mb-4 p-4 border-2 border-red-500 bg-red-50">
            <p className="text-red-600">{error.message}</p>
          </div>
        )}

        {policies.length === 0 ? (
          <div className="text-center py-12">
            <IconShield className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium mb-2">No policies defined</p>
            <p className="text-muted-foreground mb-4">
              Create your first policy to get started
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="border-2 border-black">
                <TableHead className="font-bold">Name</TableHead>
                <TableHead className="font-bold">Framework</TableHead>
                <TableHead className="font-bold">Status</TableHead>
                <TableHead className="font-bold">Rules</TableHead>
                <TableHead className="font-bold">Created</TableHead>
                <TableHead className="font-bold">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {policies.map((policy) => (
                <TableRow key={policy.id} className="border-b-2 border-black">
                  <TableCell className="font-medium">{policy.name}</TableCell>
                  <TableCell>
                    <Badge variant="default" className="border-2 border-black">
                      {policy.framework}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="default" className="border-2 border-black">
                      {policy.status}
                    </Badge>
                  </TableCell>
                  <TableCell>{policy.rules.length} rules</TableCell>
                  <TableCell>
                    {new Date(policy.createdAt).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Button variant="noShadow" size="sm">
                        View
                      </Button>
                      <Button variant="noShadow" size="sm">
                        Edit
                      </Button>
                    </div>
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

