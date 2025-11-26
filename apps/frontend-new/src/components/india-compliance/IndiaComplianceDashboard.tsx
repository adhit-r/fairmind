'use client'

import React, { useState, useEffect } from 'react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { AlertCircle, CheckCircle, Clock } from 'lucide-react'

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

interface ComplianceRequirement {
  requirement_id: string
  name: string
  status: 'compliant' | 'non_compliant' | 'pending' | 'partial'
  evidence_count: number
  last_checked?: string
}

interface ComplianceData {
  framework: string
  overall_score: number
  status: 'compliant' | 'non_compliant' | 'partial' | 'pending'
  requirements_met: number
  total_requirements: number
  evidence_count: number
  requirements: ComplianceRequirement[]
  timestamp: string
}

interface IndiaComplianceDashboardProps {
  systemId: string
  onFrameworkChange?: (framework: string) => void
}

const FRAMEWORKS = [
  { value: 'dpdp_act_2023', label: 'DPDP Act 2023' },
  { value: 'niti_aayog_principles', label: 'NITI Aayog Principles' },
  { value: 'meity_guidelines', label: 'MeitY Guidelines' },
  { value: 'digital_india_act', label: 'Digital India Act' },
]

const getStatusColor = (status: string) => {
  switch (status) {
    case 'compliant':
      return 'bg-green-100 text-green-800'
    case 'non_compliant':
      return 'bg-red-100 text-red-800'
    case 'partial':
      return 'bg-yellow-100 text-yellow-800'
    case 'pending':
      return 'bg-blue-100 text-blue-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'compliant':
      return <CheckCircle className="h-4 w-4 text-green-600" />
    case 'non_compliant':
      return <AlertCircle className="h-4 w-4 text-red-600" />
    case 'pending':
      return <Clock className="h-4 w-4 text-blue-600" />
    default:
      return <AlertCircle className="h-4 w-4 text-gray-600" />
  }
}

const getScoreColor = (score: number) => {
  if (score >= 80) return 'text-green-600'
  if (score >= 60) return 'text-yellow-600'
  return 'text-red-600'
}

export const IndiaComplianceDashboard: React.FC<IndiaComplianceDashboardProps> = ({
  systemId,
  onFrameworkChange,
}) => {
  const [selectedFramework, setSelectedFramework] = useState('dpdp_act_2023')
  const [complianceData, setComplianceData] = useState<ComplianceData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchComplianceData = async () => {
      try {
        setLoading(true)
        setError(null)

        // Mock data for demonstration - replace with actual API call
        const mockData: ComplianceData = {
          framework: selectedFramework,
          overall_score: 75,
          status: 'partial',
          requirements_met: 15,
          total_requirements: 20,
          evidence_count: 42,
          timestamp: new Date().toISOString(),
          requirements: [
            {
              requirement_id: 'REQ_001',
              name: 'Consent Management',
              status: 'compliant',
              evidence_count: 5,
              last_checked: new Date(Date.now() - 86400000).toISOString(),
            },
            {
              requirement_id: 'REQ_002',
              name: 'Data Localization',
              status: 'compliant',
              evidence_count: 3,
              last_checked: new Date(Date.now() - 172800000).toISOString(),
            },
            {
              requirement_id: 'REQ_003',
              name: 'Cross-Border Transfer',
              status: 'non_compliant',
              evidence_count: 2,
              last_checked: new Date(Date.now() - 259200000).toISOString(),
            },
            {
              requirement_id: 'REQ_004',
              name: 'Data Principal Rights',
              status: 'partial',
              evidence_count: 4,
              last_checked: new Date(Date.now() - 345600000).toISOString(),
            },
            {
              requirement_id: 'REQ_005',
              name: 'Security Controls',
              status: 'compliant',
              evidence_count: 6,
              last_checked: new Date(Date.now() - 432000000).toISOString(),
            },
          ],
        }

        setComplianceData(mockData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch compliance data')
      } finally {
        setLoading(false)
      }
    }

    fetchComplianceData()
  }, [selectedFramework, systemId])

  const handleFrameworkChange = (value: string) => {
    setSelectedFramework(value)
    onFrameworkChange?.(value)
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>India Compliance Dashboard</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <p className="text-gray-500">Loading compliance data...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>India Compliance Dashboard</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <p className="text-red-500">{error}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!complianceData) {
    return null
  }

  const frameworkLabel = FRAMEWORKS.find(f => f.value === selectedFramework)?.label || selectedFramework

  return (
    <div className="space-y-6">
      {/* Framework Selection */}
      <Card>
        <CardHeader>
          <CardTitle>India Compliance Dashboard</CardTitle>
          <CardDescription>
            Monitor compliance status against Indian AI regulations and data protection laws
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium">Select Framework:</label>
            <Select value={selectedFramework} onValueChange={handleFrameworkChange}>
              <SelectTrigger className="w-64">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {FRAMEWORKS.map(framework => (
                  <SelectItem key={framework.value} value={framework.value}>
                    {framework.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Overall Compliance Score */}
      <Card>
        <CardHeader>
          <CardTitle>Overall Compliance Score</CardTitle>
          <CardDescription>
            {frameworkLabel} - Last updated {formatDate(complianceData.timestamp)}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Compliance Score</p>
              <p className={`text-4xl font-bold ${getScoreColor(complianceData.overall_score)}`}>
                {complianceData.overall_score}%
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600">Status</p>
              <Badge className={getStatusColor(complianceData.status)}>
                {complianceData.status.replace('_', ' ').toUpperCase()}
              </Badge>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Requirements Met</span>
              <span className="font-medium">
                {complianceData.requirements_met} / {complianceData.total_requirements}
              </span>
            </div>
            <Progress
              value={(complianceData.requirements_met / complianceData.total_requirements) * 100}
              className="h-2"
            />
          </div>

          <div className="grid grid-cols-2 gap-4 pt-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Evidence Collected</p>
              <p className="text-2xl font-bold text-blue-600">{complianceData.evidence_count}</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Compliance Rate</p>
              <p className="text-2xl font-bold text-green-600">
                {Math.round((complianceData.requirements_met / complianceData.total_requirements) * 100)}%
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Requirements Status Table */}
      <Card>
        <CardHeader>
          <CardTitle>Requirement-by-Requirement Status</CardTitle>
          <CardDescription>
            Detailed compliance status for each requirement
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Requirement</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Evidence Count</TableHead>
                <TableHead>Last Checked</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {complianceData.requirements.map(req => (
                <TableRow key={req.requirement_id}>
                  <TableCell className="font-medium">{req.name}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {getStatusIcon(req.status)}
                      <Badge className={getStatusColor(req.status)}>
                        {req.status.replace('_', ' ').toUpperCase()}
                      </Badge>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="inline-flex items-center justify-center w-6 h-6 bg-gray-100 rounded-full text-sm font-medium">
                      {req.evidence_count}
                    </span>
                  </TableCell>
                  <TableCell className="text-sm text-gray-600">
                    {req.last_checked ? formatDate(req.last_checked) : 'Never'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}

export default IndiaComplianceDashboard
