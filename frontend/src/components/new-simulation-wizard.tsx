"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Upload, ChevronLeft, ChevronRight, Info } from "lucide-react"

import Link from "next/link"

const models = [
  { id: "loan_v1", name: "Loan Model v1", type: "pkl", size: "2.3 MB", description: "Credit approval model" },
  { id: "hiring_v2", name: "Hiring Model v2", type: "onnx", size: "5.1 MB", description: "Resume screening model" },
  { id: "credit_v3", name: "Credit Scoring v3", type: "h5", size: "8.7 MB", description: "Credit risk assessment" },
]

const riskDimensions = [
  {
    id: "fairness",
    name: "Fairness",
    description: "Test for bias across demographics and protected classes",
    details: "Analyzes model predictions across different demographic groups to identify potential discrimination",
  },
  {
    id: "explainability",
    name: "Explainability & Transparency",
    description: "Evaluate model interpretability and decision transparency",
    details: "Uses SHAP, LIME, and other techniques to understand model decision-making processes",
  },
  {
    id: "robustness",
    name: "Robustness",
    description: "Test resilience to noise, drift, and adversarial inputs",
    details: "Evaluates model performance under various stress conditions and data perturbations",
  },
  {
    id: "compliance",
    name: "Compliance Checks",
    description: "Verify adherence to regulatory requirements",
    details: "Checks compliance with GDPR, CCPA, and industry-specific regulations",
  },
]

export function NewSimulationWizard() {
  const [currentStep, setCurrentStep] = useState(1)
  const [selectedModel, setSelectedModel] = useState<string>("")
  const [selectedRisks, setSelectedRisks] = useState<string[]>([])
  const [customScenario, setCustomScenario] = useState("")
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)

  const handleNext = () => {
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleRiskToggle = (riskId: string) => {
    setSelectedRisks((prev) => (prev.includes(riskId) ? prev.filter((id) => id !== riskId) : [...prev, riskId]))
  }

  const canProceedStep1 = selectedModel || uploadedFile
  const canProceedStep2 = selectedRisks.length > 0

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Progress Header */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold tracking-tight">NEW_SIMULATION</h1>
          <div className="text-sm text-muted-foreground">Step {currentStep} of 3</div>
        </div>
        <Progress value={(currentStep / 3) * 100} className="w-full" />
      </div>

      {/* Step 1: Select Model */}
      {currentStep === 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">STEP_1 — SELECT_AI_MODEL</CardTitle>
            <CardDescription>Choose an existing model from your inventory or upload a new one</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <Label className="text-base font-medium">Select from Inventory</Label>
              <Select value={selectedModel} onValueChange={setSelectedModel}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a model..." />
                </SelectTrigger>
                <SelectContent>
                  {models.map((model) => (
                    <SelectItem key={model.id} value={model.id}>
                      <div className="flex items-center gap-2">
                        <span>{model.name}</span>
                        <Badge variant="outline">{model.type}</Badge>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">OR</span>
              </div>
            </div>

            <div className="space-y-4">
              <Label className="text-base font-medium">Upload Model</Label>
              <div className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 text-center">
                <Upload className="mx-auto h-12 w-12 text-muted-foreground/50" />
                <div className="mt-4">
                  <Label htmlFor="file-upload" className="cursor-pointer">
                    <span className="text-blue-600 hover:text-blue-500">Click to upload</span>
                    <span className="text-muted-foreground"> or drag and drop</span>
                  </Label>
                  <Input
                    id="file-upload"
                    type="file"
                    className="hidden"
                    accept=".pkl,.onnx,.h5,.joblib,.pt,.pth"
                    onChange={(e) => setUploadedFile(e.target.files?.[0] || null)}
                  />
                </div>
                <p className="text-sm text-muted-foreground mt-2">
                  Supports .pkl, .onnx, .h5, .joblib, .pt, .pth files
                </p>
                {uploadedFile && (
                  <div className="mt-4 p-3 bg-muted rounded-md">
                    <p className="text-sm font-medium">{uploadedFile.name}</p>
                    <p className="text-xs text-muted-foreground">{(uploadedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                )}
              </div>
            </div>

            {selectedModel && (
              <Card className="bg-muted/50">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">Model Preview</CardTitle>
                </CardHeader>
                <CardContent>
                  {(() => {
                    const model = models.find((m) => m.id === selectedModel)
                    return model ? (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{model.name}</span>
                          <Badge variant="outline">{model.type}</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">{model.description}</p>
                        <p className="text-xs text-muted-foreground">Size: {model.size}</p>
                      </div>
                    ) : null
                  })()}
                </CardContent>
              </Card>
            )}
          </CardContent>
        </Card>
      )}

      {/* Step 2: Select Risk Dimensions */}
      {currentStep === 2 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">STEP_2 — SELECT_RISK_DIMENSIONS</CardTitle>
            <CardDescription>Choose which ethical risks you want to test for</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-4">
              {riskDimensions.map((risk) => (
                <div key={risk.id} className="flex items-start space-x-3 p-4 border rounded-lg">
                  <Checkbox
                    id={risk.id}
                    checked={selectedRisks.includes(risk.id)}
                    onCheckedChange={() => handleRiskToggle(risk.id)}
                  />
                  <div className="flex-1 space-y-2">
                    <Label htmlFor={risk.id} className="text-base font-medium cursor-pointer">
                      {risk.name}
                    </Label>
                    <p className="text-sm text-muted-foreground">{risk.description}</p>
                    <div className="flex items-start gap-2 text-xs text-muted-foreground">
                      <Info className="h-3 w-3 mt-0.5 flex-shrink-0" />
                      <span>{risk.details}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="space-y-4">
              <Label htmlFor="custom-scenario" className="text-base font-medium">
                Custom Scenario (Optional)
              </Label>
              <Textarea
                id="custom-scenario"
                placeholder="Describe any specific scenarios or edge cases you want to test..."
                value={customScenario}
                onChange={(e) => setCustomScenario(e.target.value)}
                rows={3}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Review & Run */}
      {currentStep === 3 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">STEP_3 — REVIEW_&_RUN</CardTitle>
            <CardDescription>Review your simulation configuration before running</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <Card className="bg-muted/50">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Simulation Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Model Name</Label>
                  <p className="text-base">
                    {uploadedFile ? uploadedFile.name : models.find((m) => m.id === selectedModel)?.name || "Unknown"}
                  </p>
                </div>

                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Selected Risks</Label>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {selectedRisks.map((riskId) => {
                      const risk = riskDimensions.find((r) => r.id === riskId)
                      return risk ? (
                        <Badge key={riskId} variant="secondary">
                          {risk.name}
                        </Badge>
                      ) : null
                    })}
                  </div>
                </div>

                {customScenario && (
                  <div>
                    <Label className="text-sm font-medium text-muted-foreground">Custom Scenario</Label>
                    <p className="text-sm mt-1 p-3 bg-background rounded border">{customScenario}</p>
                  </div>
                )}

                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Estimated Run Time</Label>
                  <p className="text-base">~12 minutes</p>
                </div>
              </CardContent>
            </Card>
          </CardContent>
        </Card>
      )}

      {/* Navigation Buttons */}
      <div className="flex justify-between">
        <div>
          {currentStep > 1 && (
            <Button variant="outline" onClick={handleBack}>
              <ChevronLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
          )}
        </div>

        <div className="flex gap-2">
          <Link href="/">
            <Button variant="ghost">Cancel</Button>
          </Link>

          {currentStep < 3 ? (
            <Button
              onClick={handleNext}
              disabled={(currentStep === 1 && !canProceedStep1) || (currentStep === 2 && !canProceedStep2)}
            >
              Next
              <ChevronRight className="ml-2 h-4 w-4" />
            </Button>
          ) : (
            <Link href="/simulation/1/progress">
              <Button className="bg-white text-black hover:bg-gray-200 text-xs">RUN_SIMULATION</Button>
            </Link>
          )}
        </div>
      </div>
    </div>
  )
}
