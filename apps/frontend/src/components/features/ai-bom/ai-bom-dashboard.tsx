"use client"

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/common/card"
import { Button } from "@/components/ui/common/button"
import { Badge } from "@/components/ui/common/badge"
import { Input } from "@/components/ui/common/input"
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/common/table"
import { 
  Search, 
  Filter, 
  Eye, 
  BarChart3, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  RefreshCw
} from "lucide-react"
import { AIBOMRiskChart } from "./ai-bom-risk-chart"
import { AIBOMComplianceChart } from "./ai-bom-compliance-chart"
import { AIBOMComponentChart } from "./ai-bom-component-chart"

interface AIBOMDashboardProps {
  bomDocuments: any[]
  loading: boolean
  onRefresh: () => void
}

export function AIBOMDashboard({ bomDocuments, loading, onRefresh }: AIBOMDashboardProps) {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedRiskFilter, setSelectedRiskFilter] = useState("all")
  const [selectedComplianceFilter, setSelectedComplianceFilter] = useState("all")

  const filteredDocuments = bomDocuments.filter(doc => {
    const matchesSearch = doc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         doc.project_name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesRisk = selectedRiskFilter === "all" || doc.overall_risk_level === selectedRiskFilter
    const matchesCompliance = selectedComplianceFilter === "all" || doc.overall_compliance_status === selectedComplianceFilter
    
    return matchesSearch && matchesRisk && matchesCompliance
  })

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
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
      case 'review_required': return 'bg-orange-100 text-orange-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getComplianceIcon = (status: string) => {
    switch (status) {
      case 'compliant': return <CheckCircle className="h-4 w-4" />
      case 'non_compliant': return <AlertTriangle className="h-4 w-4" />
      case 'pending': return <Clock className="h-4 w-4" />
      case 'review_required': return <AlertTriangle className="h-4 w-4" />
      default: return <Clock className="h-4 w-4" />
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Filters and Search */}
      <Card className="border-2 border-black shadow-4px-4px-0px-black">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>BOM Documents</span>
            <Button onClick={onRefresh} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search BOM documents..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <select
                value={selectedRiskFilter}
                onChange={(e) => setSelectedRiskFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md bg-white"
              >
                <option value="all">All Risk Levels</option>
                <option value="low">Low Risk</option>
                <option value="medium">Medium Risk</option>
                <option value="high">High Risk</option>
                <option value="critical">Critical Risk</option>
              </select>
              <select
                value={selectedComplianceFilter}
                onChange={(e) => setSelectedComplianceFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md bg-white"
              >
                <option value="all">All Compliance Status</option>
                <option value="compliant">Compliant</option>
                <option value="non_compliant">Non-Compliant</option>
                <option value="pending">Pending</option>
                <option value="review_required">Review Required</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="border-2 border-black shadow-4px-4px-0px-black">
          <CardHeader>
            <CardTitle className="flex items-center">
              <BarChart3 className="h-5 w-5 mr-2 text-red-600" />
              Risk Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <AIBOMRiskChart bomDocuments={bomDocuments} />
          </CardContent>
        </Card>

        <Card className="border-2 border-black shadow-4px-4px-0px-black">
          <CardHeader>
            <CardTitle className="flex items-center">
              <CheckCircle className="h-5 w-5 mr-2 text-green-600" />
              Compliance Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <AIBOMComplianceChart bomDocuments={bomDocuments} />
          </CardContent>
        </Card>

        <Card className="border-2 border-black shadow-4px-4px-0px-black">
          <CardHeader>
            <CardTitle className="flex items-center">
              <BarChart3 className="h-5 w-5 mr-2 text-blue-600" />
              Component Types
            </CardTitle>
          </CardHeader>
          <CardContent>
            <AIBOMComponentChart bomDocuments={bomDocuments} />
          </CardContent>
        </Card>
      </div>

      {/* BOM Documents Table */}
      <Card className="border-2 border-black shadow-4px-4px-0px-black">
        <CardHeader>
          <CardTitle>
            BOM Documents ({filteredDocuments.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {filteredDocuments.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No BOM documents found. Create your first AI BOM to get started.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Project</TableHead>
                  <TableHead>Components</TableHead>
                  <TableHead>Risk Level</TableHead>
                  <TableHead>Compliance</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredDocuments.map((doc) => (
                  <TableRow key={doc.id}>
                    <TableCell className="font-medium">
                      <div>
                        <div className="font-semibold">{doc.name}</div>
                        <div className="text-sm text-gray-500">{doc.description}</div>
                      </div>
                    </TableCell>
                    <TableCell>{doc.project_name}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{doc.total_components} components</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={getRiskColor(doc.overall_risk_level)}>
                        {doc.overall_risk_level}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getComplianceIcon(doc.overall_compliance_status)}
                        <Badge className={getComplianceColor(doc.overall_compliance_status)}>
                          {doc.overall_compliance_status.replace('_', ' ')}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm text-gray-500">
                        {new Date(doc.created_at).toLocaleDateString()}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex space-x-2">
                        <Button size="sm" variant="outline">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button size="sm" variant="outline">
                          <BarChart3 className="h-4 w-4" />
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
