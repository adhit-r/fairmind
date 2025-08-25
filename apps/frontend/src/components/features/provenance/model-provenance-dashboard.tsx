"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/common/card"
import { Button } from "@/components/ui/common/button"
import { Badge } from "@/components/ui/common/badge"
import { Input } from "@/components/ui/common/input"
import { Textarea } from "@/components/ui/common/textarea"
import { Alert, AlertDescription } from "@/components/ui/common/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/common/tabs"
import { 
  FileText, 
  Shield, 
  CheckCircle, 
  XCircle, 
  Database,
  Code,
  Fingerprint,
  Lock,
  Scan,
  History,
  RefreshCw,
  Plus,
  Info
} from "lucide-react"
import { fairmindAPI } from "@/lib/fairmind-api"

interface ProvenanceModel {
  model_id: string
  name: string
  version: string
  developer: string
  organization: string
  training_date: string
  signature_verified: boolean
}

export function ModelProvenanceDashboard() {
  const [models, setModels] = useState<ProvenanceModel[]>([])
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    loadProvenanceModels()
  }, [])

  const loadProvenanceModels = async () => {
    try {
      setLoading(true)
      // const response = await fairmindAPI.listProvenanceModels()
      // if (response.success) {
      //   setModels(response.data)
      // } else {
      //   setError('Failed to load provenance models')
      // }
      // Mock data for now
      setModels([])
    } catch (error) {
      setError('Error loading provenance models')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Model Provenance & Model Cards</h1>
          <p className="text-gray-600">Track model lineage, verify authenticity, and generate responsible AI documentation</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={loadProvenanceModels} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" />
            Add Model
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Models List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Models with Provenance
          </CardTitle>
          <CardDescription>
            {models.length} models tracked in the provenance system
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {models.map((model) => (
              <div
                key={model.model_id}
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  selectedModel === model.model_id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedModel(model.model_id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div>
                      <h3 className="font-medium">{model.name}</h3>
                      <p className="text-sm text-gray-600">
                        v{model.version} • {model.developer} • {model.organization}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {model.signature_verified ? (
                      <Badge className="bg-green-100 text-green-800">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Verified
                      </Badge>
                    ) : (
                      <Badge className="bg-red-100 text-red-800">
                        <XCircle className="h-3 w-3 mr-1" />
                        Unverified
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {models.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <Database className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No models with provenance records found</p>
                <p className="text-sm">Create your first model provenance to get started</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Model Details */}
      {selectedModel && (
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="model-card">Model Card</TabsTrigger>
            <TabsTrigger value="provenance">Provenance Chain</TabsTrigger>
            <TabsTrigger value="scanning">Security Scan</TabsTrigger>
            <TabsTrigger value="verification">Authenticity</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Model Overview</CardTitle>
              </CardHeader>
              <CardContent>
                <p>Model overview content will be displayed here.</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="model-card" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Model Card</CardTitle>
              </CardHeader>
              <CardContent>
                <p>Model card content will be displayed here.</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="provenance" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Provenance Chain</CardTitle>
              </CardHeader>
              <CardContent>
                <p>Provenance chain content will be displayed here.</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="scanning" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Security Scan</CardTitle>
              </CardHeader>
              <CardContent>
                <p>Security scan content will be displayed here.</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="verification" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Authenticity Verification</CardTitle>
              </CardHeader>
              <CardContent>
                <p>Authenticity verification content will be displayed here.</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}
