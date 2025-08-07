"use client"

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { 
  Package, 
  Download, 
  Upload, 
  Search, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Database,
  Code,
  FileText,
  Shield
} from "lucide-react"

interface BOMItem {
  id: string
  name: string
  version: string
  type: 'framework' | 'library' | 'dataset' | 'model' | 'dependency'
  license: string
  source: string
  size: string
  checksum: string
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  compliance_status: 'compliant' | 'non_compliant' | 'pending'
  last_updated: string
  description: string
  dependencies: string[]
  vulnerabilities: string[]
}

export function AIMLBOM() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedType, setSelectedType] = useState<string>('all')
  const [selectedRisk, setSelectedRisk] = useState<string>('all')

  // Mock BOM data
  const bomItems: BOMItem[] = [
    {
      id: 'pytorch-2.0',
      name: 'PyTorch',
      version: '2.0.1',
      type: 'framework',
      license: 'BSD-3-Clause',
      source: 'https://pytorch.org/',
      size: '850MB',
      checksum: 'sha256:abc123...',
      risk_level: 'low',
      compliance_status: 'compliant',
      last_updated: '2024-01-15',
      description: 'Deep learning framework for Python',
      dependencies: ['Python 3.8+', 'CUDA 11.8'],
      vulnerabilities: []
    },
    {
      id: 'transformers-4.35',
      name: 'Transformers',
      version: '4.35.0',
      type: 'library',
      license: 'Apache-2.0',
      source: 'https://huggingface.co/transformers',
      size: '45MB',
      checksum: 'sha256:def456...',
      risk_level: 'low',
      compliance_status: 'compliant',
      last_updated: '2024-01-10',
      description: 'State-of-the-art Natural Language Processing',
      dependencies: ['PyTorch 2.0+', 'TensorFlow 2.0+'],
      vulnerabilities: []
    },
    {
      id: 'imagenet-1k',
      name: 'ImageNet-1K',
      version: '1.0',
      type: 'dataset',
      license: 'Custom',
      source: 'https://image-net.org/',
      size: '150GB',
      checksum: 'sha256:ghi789...',
      risk_level: 'medium',
      compliance_status: 'pending',
      last_updated: '2024-01-05',
      description: 'Large-scale image dataset for computer vision',
      dependencies: [],
      vulnerabilities: ['Potential bias in image selection']
    },
    {
      id: 'gpt-4-model',
      name: 'GPT-4',
      version: '2024',
      type: 'model',
      license: 'Proprietary',
      source: 'OpenAI',
      size: '1.7TB',
      checksum: 'sha256:jkl012...',
      risk_level: 'high',
      compliance_status: 'non_compliant',
      last_updated: '2024-01-12',
      description: 'Large language model for text generation',
      dependencies: ['Transformers 4.35+'],
      vulnerabilities: ['Potential bias', 'Privacy concerns', 'Hallucination risk']
    },
    {
      id: 'scikit-learn-1.3',
      name: 'scikit-learn',
      version: '1.3.0',
      type: 'library',
      license: 'BSD-3-Clause',
      source: 'https://scikit-learn.org/',
      size: '12MB',
      checksum: 'sha256:mno345...',
      risk_level: 'low',
      compliance_status: 'compliant',
      last_updated: '2024-01-08',
      description: 'Machine learning library for Python',
      dependencies: ['NumPy 1.21+', 'SciPy 1.7+'],
      vulnerabilities: []
    }
  ]

  const filteredItems = bomItems.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.description.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = selectedType === 'all' || item.type === selectedType
    const matchesRisk = selectedRisk === 'all' || item.risk_level === selectedRisk
    
    return matchesSearch && matchesType && matchesRisk
  })

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'bg-green-100 text-green-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'high': return 'bg-orange-100 text-orange-800'
      case 'critical': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getComplianceColor = (status: string) => {
    switch (status) {
      case 'compliant': return 'bg-green-100 text-green-800'
      case 'non_compliant': return 'bg-red-100 text-red-800'
      case 'pending': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'framework': return <Code className="h-4 w-4" />
      case 'library': return <Package className="h-4 w-4" />
      case 'dataset': return <Database className="h-4 w-4" />
      case 'model': return <Shield className="h-4 w-4" />
      case 'dependency': return <FileText className="h-4 w-4" />
      default: return <Package className="h-4 w-4" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">AI/ML Bill of Materials</h2>
          <p className="text-muted-foreground">
            Track dependencies, licenses, and compliance for AI/ML components
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Upload className="mr-2 h-4 w-4" />
            Import BOM
          </Button>
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export BOM
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Search</Label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search components..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Type</Label>
              <Select value={selectedType} onValueChange={setSelectedType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="framework">Framework</SelectItem>
                  <SelectItem value="library">Library</SelectItem>
                  <SelectItem value="dataset">Dataset</SelectItem>
                  <SelectItem value="model">Model</SelectItem>
                  <SelectItem value="dependency">Dependency</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Risk Level</Label>
              <Select value={selectedRisk} onValueChange={setSelectedRisk}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Risk Levels</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Components</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{bomItems.length}</div>
            <p className="text-xs text-muted-foreground">
              All components
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compliant</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {bomItems.filter(item => item.compliance_status === 'compliant').length}
            </div>
            <p className="text-xs text-muted-foreground">
              Passed compliance
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">High Risk</CardTitle>
            <AlertTriangle className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {bomItems.filter(item => item.risk_level === 'high' || item.risk_level === 'critical').length}
            </div>
            <p className="text-xs text-muted-foreground">
              Needs attention
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Review</CardTitle>
            <Clock className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {bomItems.filter(item => item.compliance_status === 'pending').length}
            </div>
            <p className="text-xs text-muted-foreground">
              Awaiting review
            </p>
          </CardContent>
        </Card>
      </div>

      {/* BOM Table */}
      <Card>
        <CardHeader>
          <CardTitle>Components</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Component</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Version</TableHead>
                <TableHead>License</TableHead>
                <TableHead>Risk Level</TableHead>
                <TableHead>Compliance</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredItems.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        {getTypeIcon(item.type)}
                        <span className="font-medium">{item.name}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">{item.description}</p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="capitalize">
                      {item.type}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <span className="font-mono text-sm">{item.version}</span>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm">{item.license}</span>
                  </TableCell>
                  <TableCell>
                    <Badge className={getRiskColor(item.risk_level)}>
                      {item.risk_level}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge className={getComplianceColor(item.compliance_status)}>
                      {item.compliance_status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <Button size="sm" variant="outline">
                        View
                      </Button>
                      <Button size="sm" variant="outline">
                        Edit
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Vulnerabilities Alert */}
      {bomItems.some(item => item.vulnerabilities.length > 0) && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            {bomItems.filter(item => item.vulnerabilities.length > 0).length} components have vulnerabilities that need attention.
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
} 