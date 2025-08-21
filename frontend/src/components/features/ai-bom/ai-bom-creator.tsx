"use client"

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/common/card"
import { Button } from "@/components/ui/common/button"
import { Input } from "@/components/ui/common/input"
import { Label } from "@/components/ui/common/label"
import { Textarea } from "@/components/ui/common/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/common/select"
import { Badge } from "@/components/ui/common/badge"
import { Plus, X, Save, Loader2 } from "lucide-react"

interface AIBOMCreatorProps {
  onBOMCreated: () => void
}

interface Component {
  id: string
  name: string
  type: string
  version: string
  description: string
  vendor: string
  license: string
  risk_level: string
  compliance_status: string
  dependencies: string[]
  metadata: Record<string, any>
}

export function AIBOMCreator({ onBOMCreated }: AIBOMCreatorProps) {
  const [loading, setLoading] = useState(false)
  const [projectName, setProjectName] = useState("")
  const [description, setDescription] = useState("")
  const [components, setComponents] = useState<Component[]>([])
  const [componentTypes, setComponentTypes] = useState([])
  const [riskLevels, setRiskLevels] = useState([])
  const [complianceStatuses, setComplianceStatuses] = useState([])

  // Fetch component types, risk levels, and compliance statuses
  useState(() => {
    fetchComponentTypes()
    fetchRiskLevels()
    fetchComplianceStatuses()
  })

  const fetchComponentTypes = async () => {
    try {
      const response = await fetch('/api/v1/ai-bom/components/types')
      const data = await response.json()
      if (data.success) {
        setComponentTypes(data.data)
      }
    } catch (error) {
      console.error('Error fetching component types:', error)
    }
  }

  const fetchRiskLevels = async () => {
    try {
      const response = await fetch('/api/v1/ai-bom/risk-levels')
      const data = await response.json()
      if (data.success) {
        setRiskLevels(data.data)
      }
    } catch (error) {
      console.error('Error fetching risk levels:', error)
    }
  }

  const fetchComplianceStatuses = async () => {
    try {
      const response = await fetch('/api/v1/ai-bom/compliance-statuses')
      const data = await response.json()
      if (data.success) {
        setComplianceStatuses(data.data)
      }
    } catch (error) {
      console.error('Error fetching compliance statuses:', error)
    }
  }

  const addComponent = () => {
    const newComponent: Component = {
      id: `comp-${Date.now()}`,
      name: "",
      type: "data",
      version: "",
      description: "",
      vendor: "",
      license: "",
      risk_level: "low",
      compliance_status: "compliant",
      dependencies: [],
      metadata: {}
    }
    setComponents([...components, newComponent])
  }

  const removeComponent = (id: string) => {
    setComponents(components.filter(comp => comp.id !== id))
  }

  const updateComponent = (id: string, field: keyof Component, value: any) => {
    setComponents(components.map(comp => 
      comp.id === id ? { ...comp, [field]: value } : comp
    ))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const request = {
        project_name: projectName,
        description: description,
        components: components,
        analysis_type: "comprehensive"
      }

      const response = await fetch('/api/v1/ai-bom/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })

      const data = await response.json()
      
      if (data.success) {
        onBOMCreated()
        // Reset form
        setProjectName("")
        setDescription("")
        setComponents([])
      } else {
        alert('Error creating AI BOM: ' + data.message)
      }
    } catch (error) {
      console.error('Error creating AI BOM:', error)
      alert('Error creating AI BOM')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <Card className="border-2 border-black shadow-4px-4px-0px-black">
        <CardHeader>
          <CardTitle>Create New AI Bill of Materials</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Project Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="projectName">Project Name</Label>
                <Input
                  id="projectName"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="Enter project name"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Enter project description"
                  required
                />
              </div>
            </div>

            {/* Components Section */}
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold">Components</h3>
                <Button type="button" onClick={addComponent} variant="outline">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Component
                </Button>
              </div>

              {components.length === 0 && (
                <div className="text-center py-8 text-gray-500 border-2 border-dashed border-gray-300 rounded-lg">
                  <p>No components added yet. Click "Add Component" to get started.</p>
                </div>
              )}

              {components.map((component, index) => (
                <Card key={component.id} className="border border-gray-200">
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start mb-4">
                      <h4 className="font-semibold">Component {index + 1}</h4>
                      <Button
                        type="button"
                        onClick={() => removeComponent(component.id)}
                        variant="outline"
                        size="sm"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <Label>Name</Label>
                        <Input
                          value={component.name}
                          onChange={(e) => updateComponent(component.id, 'name', e.target.value)}
                          placeholder="Component name"
                          required
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>Type</Label>
                        <Select
                          value={component.type}
                          onValueChange={(value) => updateComponent(component.id, 'type', value)}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select type" />
                          </SelectTrigger>
                          <SelectContent>
                            {componentTypes.map((type: any) => (
                              <SelectItem key={type.value} value={type.value}>
                                {type.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label>Version</Label>
                        <Input
                          value={component.version}
                          onChange={(e) => updateComponent(component.id, 'version', e.target.value)}
                          placeholder="1.0.0"
                          required
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>Vendor</Label>
                        <Input
                          value={component.vendor}
                          onChange={(e) => updateComponent(component.id, 'vendor', e.target.value)}
                          placeholder="Vendor name"
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>License</Label>
                        <Input
                          value={component.license}
                          onChange={(e) => updateComponent(component.id, 'license', e.target.value)}
                          placeholder="License type"
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>Risk Level</Label>
                        <Select
                          value={component.risk_level}
                          onValueChange={(value) => updateComponent(component.id, 'risk_level', value)}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {riskLevels.map((level: any) => (
                              <SelectItem key={level.value} value={level.value}>
                                {level.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label>Compliance Status</Label>
                        <Select
                          value={component.compliance_status}
                          onValueChange={(value) => updateComponent(component.id, 'compliance_status', value)}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {complianceStatuses.map((status: any) => (
                              <SelectItem key={status.value} value={status.value}>
                                {status.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="md:col-span-2 lg:col-span-3 space-y-2">
                        <Label>Description</Label>
                        <Textarea
                          value={component.description}
                          onChange={(e) => updateComponent(component.id, 'description', e.target.value)}
                          placeholder="Component description"
                          required
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Submit Button */}
            <div className="flex justify-end">
              <Button type="submit" disabled={loading || components.length === 0}>
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Create AI BOM
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
