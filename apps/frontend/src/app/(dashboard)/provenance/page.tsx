'use client'

import { useState } from 'react'
import { useProvenance } from '@/lib/api/hooks/useProvenance'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { IconFileText, IconSearch, IconAlertTriangle } from '@tabler/icons-react'

export default function ProvenancePage() {
  const [modelId, setModelId] = useState('')
  const [searchModelId, setSearchModelId] = useState('')
  const { data, loading, error } = useProvenance(searchModelId)

  const handleSearch = () => {
    if (modelId.trim()) {
      setSearchModelId(modelId)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold">Model Provenance</h1>
        <p className="text-muted-foreground mt-1">
          Track model lineage and provenance information
        </p>
      </div>

      {/* Search */}
      <Card className="p-6 border-2 border-black shadow-brutal">
        <div className="flex gap-4">
          <div className="flex-1 space-y-2">
            <Label htmlFor="modelId">Model ID</Label>
            <Input
              id="modelId"
              value={modelId}
              onChange={(e) => setModelId(e.target.value)}
              placeholder="Enter model ID to search"
              className="border-2 border-black"
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
          </div>
          <div className="flex items-end">
            <Button variant="default" onClick={handleSearch}>
              <IconSearch className="mr-2 h-4 w-4" />
              Search
            </Button>
          </div>
        </div>
      </Card>

      {/* Results */}
      {loading && (
        <div className="space-y-4">
          <Skeleton className="h-64" />
        </div>
      )}

      {error && (
        <Alert className="border-2 border-red-500 shadow-brutal">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      )}

      {!loading && !error && data.length > 0 && (
        <Card className="p-6 border-2 border-black shadow-brutal">
          <h2 className="text-2xl font-bold mb-4">Provenance Records</h2>
          <Table>
            <TableHeader>
              <TableRow className="border-2 border-black">
                <TableHead className="font-bold">Record ID</TableHead>
                <TableHead className="font-bold">Model ID</TableHead>
                <TableHead className="font-bold">Lineage Depth</TableHead>
                <TableHead className="font-bold">Timestamp</TableHead>
                <TableHead className="font-bold">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((record) => (
                <TableRow key={record.id} className="border-b-2 border-black">
                  <TableCell className="font-mono text-sm">{record.id.slice(0, 8)}...</TableCell>
                  <TableCell className="font-mono text-sm">{record.modelId}</TableCell>
                  <TableCell>
                    <Badge variant="default" className="border-2 border-black">
                      {record.lineage.length} levels
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {new Date(record.timestamp).toLocaleString()}
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
        </Card>
      )}

      {!loading && !error && searchModelId && data.length === 0 && (
        <Card className="p-12 border-2 border-black shadow-brutal text-center">
          <IconFileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-lg font-medium mb-2">No provenance records found</p>
          <p className="text-muted-foreground">
            No provenance data available for model ID: {searchModelId}
          </p>
        </Card>
      )}

      {!searchModelId && (
        <Card className="p-12 border-2 border-black shadow-brutal text-center">
          <IconFileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-lg font-medium mb-2">Search for Model Provenance</p>
          <p className="text-muted-foreground">
            Enter a model ID above to view its provenance and lineage information
          </p>
        </Card>
      )}
    </div>
  )
}

