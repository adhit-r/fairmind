"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/common/card"
import { Button } from "@/components/ui/common/button"
import { Badge } from "@/components/ui/common/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/common/tabs"
import { Plus, FileText, BarChart3, Shield, Settings, Download, Eye, PlusCircle } from "lucide-react"
import { AIBOMDashboard } from "@/components/features/ai-bom/ai-bom-dashboard"
import { AIBOMCreator } from "@/components/features/ai-bom/ai-bom-creator"
import { AIBOMAnalyzer } from "@/components/features/ai-bom/ai-bom-analyzer"
import { AIBOMCompliance } from "@/components/features/ai-bom/ai-bom-compliance"
import { AIBOMExport } from "@/components/features/ai-bom/ai-bom-export"

export default function AIBOMPage() {
  const [activeTab, setActiveTab] = useState("dashboard")
  const [bomDocuments, setBomDocuments] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchBOMDocuments()
  }, [])

  const fetchBOMDocuments = async () => {
    try {
      const response = await fetch('/api/v1/ai-bom/documents')
      const data = await response.json()
      if (data.success) {
        setBomDocuments(data.data || [])
      }
    } catch (error) {
      console.error('Error fetching BOM documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleBOMCreated = () => {
    fetchBOMDocuments()
    setActiveTab("dashboard")
  }

  return (
    <div className="space-y-6 p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AI Bill of Materials</h1>
          <p className="text-gray-600 mt-2">
            Comprehensive documentation and analysis of AI system components
          </p>
        </div>
        <div className="flex space-x-3">
          <Button 
            onClick={() => setActiveTab("create")}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create BOM
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-2 border-black shadow-4px-4px-0px-black">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total BOMs</p>
                <p className="text-2xl font-bold text-gray-900">{bomDocuments.length}</p>
              </div>
              <FileText className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-2 border-black shadow-4px-4px-0px-black">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">High Risk</p>
                <p className="text-2xl font-bold text-red-600">
                  {bomDocuments.filter(bom => bom.overall_risk_level === 'high' || bom.overall_risk_level === 'critical').length}
                </p>
              </div>
              <Shield className="h-8 w-8 text-red-600" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-2 border-black shadow-4px-4px-0px-black">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Compliant</p>
                <p className="text-2xl font-bold text-green-600">
                  {bomDocuments.filter(bom => bom.overall_compliance_status === 'compliant').length}
                </p>
              </div>
              <BarChart3 className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-2 border-black shadow-4px-4px-0px-black">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Components</p>
                <p className="text-2xl font-bold text-gray-900">
                  {bomDocuments.reduce((sum, bom) => sum + bom.total_components, 0)}
                </p>
              </div>
              <Settings className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-5 bg-white border-2 border-black shadow-4px-4px-0px-black">
          <TabsTrigger value="dashboard" className="data-[state=active]:bg-blue-100">
            <BarChart3 className="h-4 w-4 mr-2" />
            Dashboard
          </TabsTrigger>
          <TabsTrigger value="create" className="data-[state=active]:bg-green-100">
            <PlusCircle className="h-4 w-4 mr-2" />
            Create
          </TabsTrigger>
          <TabsTrigger value="analyze" className="data-[state=active]:bg-purple-100">
            <BarChart3 className="h-4 w-4 mr-2" />
            Analyze
          </TabsTrigger>
          <TabsTrigger value="compliance" className="data-[state=active]:bg-orange-100">
            <Shield className="h-4 w-4 mr-2" />
            Compliance
          </TabsTrigger>
          <TabsTrigger value="export" className="data-[state=active]:bg-gray-100">
            <Download className="h-4 w-4 mr-2" />
            Export
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard" className="space-y-4">
          <AIBOMDashboard 
            bomDocuments={bomDocuments} 
            loading={loading}
            onRefresh={fetchBOMDocuments}
          />
        </TabsContent>

        <TabsContent value="create" className="space-y-4">
          <AIBOMCreator onBOMCreated={handleBOMCreated} />
        </TabsContent>

        <TabsContent value="analyze" className="space-y-4">
          <AIBOMAnalyzer bomDocuments={bomDocuments} />
        </TabsContent>

        <TabsContent value="compliance" className="space-y-4">
          <AIBOMCompliance bomDocuments={bomDocuments} />
        </TabsContent>

        <TabsContent value="export" className="space-y-4">
          <AIBOMExport bomDocuments={bomDocuments} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
