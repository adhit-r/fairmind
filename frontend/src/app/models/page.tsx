"use client"
import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Database, Eye, Edit, Trash2, Plus } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"

export default function ModelsPage() {
  const { profile } = useAuth()
  const orgId = profile?.default_org_id || null
  const [models, setModels] = useState<any[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"

  useEffect(() => {
    const fetchModels = async () => {
      try {
        setLoading(true)
        setError(null)
        const url = orgId ? `${API_URL}/models?org_id=${orgId}` : `${API_URL}/models`
        const res = await fetch(url)
        const json = await res.json()
        if (!res.ok) throw new Error(json.detail || 'Failed to fetch models')
        setModels(json.data || [])
      } catch (e: any) {
        setError(e?.message || 'Failed to fetch models')
      } finally {
        setLoading(false)
      }
    }
    void fetchModels()
  }, [API_URL, orgId])

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Model Registry</h1>
          <p className="text-muted-foreground">
            Manage and track all AI models in your organization
          </p>
        </div>
        <Link href="/model-upload">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Model
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Models</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{models.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Models</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{models.filter(m => m.status === 'Active').length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compliant</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{models.filter(m => (m.compliance || '').toLowerCase() === 'compliant').length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">High Risk</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{models.filter(m => (m.risk_level || '').toLowerCase() === 'high').length}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Registered Models</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-sm text-muted-foreground">Loading...</div>
          ) : error ? (
            <div className="text-sm text-red-600">{error}</div>
          ) : models.length === 0 ? (
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">No models found.</div>
              <Link href="/model-upload">
                <Button size="sm">
                  <Plus className="mr-2 h-4 w-4" />
                  Upload Model
                </Button>
              </Link>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Model Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Accuracy</TableHead>
                  <TableHead>Fairness</TableHead>
                  <TableHead>Compliance</TableHead>
                  <TableHead>Risk Level</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {models.map((model: any) => (
                  <TableRow key={model.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{model.name}</div>
                        {model.version && (
                          <div className="text-sm text-muted-foreground">v{model.version}</div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{model.type || '—'}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge>{model.status || '—'}</Badge>
                    </TableCell>
                    <TableCell>{model.accuracy ? `${model.accuracy}%` : '—'}</TableCell>
                    <TableCell>{model.fairness ? `${model.fairness}%` : '—'}</TableCell>
                    <TableCell>
                      <Badge>{model.compliance || '—'}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge>{model.risk_level || '—'}</Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Button size="sm" variant="outline">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button size="sm" variant="outline">
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button size="sm" variant="outline">
                          <Trash2 className="h-4 w-4" />
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
  )
} 