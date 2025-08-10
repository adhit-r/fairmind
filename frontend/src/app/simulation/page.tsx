"use client"
import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Play } from "lucide-react"
import { NewSimulationWizard } from "@/components/new-simulation-wizard"
import { SimulationHistory } from "@/components/simulation-history"
import { ConfusionMatrix } from "@/components/charts/confusion-matrix"
import { PerClassMetrics } from "@/components/charts/per-class-metrics"
import { FairnessByAttribute } from "@/components/charts/fairness-by-attribute"

export default function SimulationPage() {
  const { profile } = require("@/contexts/auth-context").useAuth()
  const orgId = profile?.default_org_id || null
  const [modelFile, setModelFile] = useState<File | null>(null)
  const [datasetFile, setDatasetFile] = useState<File | null>(null)
  const [target, setTarget] = useState("")
  const [features, setFeatures] = useState("")
  const [protectedAttrs, setProtectedAttrs] = useState("")
  const [engine, setEngine] = useState<"builtin" | "sdv">("builtin")
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [logs, setLogs] = useState<string[]>([])
  const [simulationHistory, setSimulationHistory] = useState<any[]>([])
  const [selectedRun, setSelectedRun] = useState<any>(null)
  const [steps, setSteps] = useState<Array<{ id: string; label: string; status: "todo" | "running" | "done" }>>([
    { id: "init", label: "Initializing simulation environment", status: "todo" },
    { id: "load_model", label: "Loading model and dependencies", status: "todo" },
    { id: "generate_data", label: "Generating synthetic scenarios", status: "todo" },
    { id: "fairness", label: "Running fairness checks", status: "todo" },
    { id: "robustness", label: "Analyzing robustness metrics", status: "todo" },
    { id: "explainability", label: "Evaluating explainability", status: "todo" },
    { id: "report", label: "Generating final report", status: "todo" },
  ])
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"

  // Load simulation history on component mount
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const response = await fetch(`${API_URL}/simulations/recent?org_id=${orgId}`)
        if (response.ok) {
          const data = await response.json()
          setSimulationHistory(data)
        }
      } catch (error) {
        console.error('Failed to load simulation history:', error)
      }
    }
    
    if (orgId) {
      loadHistory()
    }
  }, [orgId, API_URL])

  const runSimulation = async () => {
    try {
      setRunning(true)
      setResult(null)
      setLogs([])
      setSteps(prev => prev.map(s => ({ ...s, status: s.id === "init" ? "running" : "todo" })))
      setLogs(prev => [...prev, `[${new Date().toISOString()}] STARTING_SIMULATION`])
      setSteps(prev => prev.map(s => (s.id === "init" ? { ...s, status: "done" } : s)))
      setSteps(prev => prev.map(s => (s.id === "load_model" ? { ...s, status: "running" } : s)))
      if (!modelFile) throw new Error("Select a model file")
      const mfd = new FormData()
      mfd.append("file", modelFile)
      const mu = await fetch(`${API_URL}/models/upload`, { method: "POST", body: mfd })
      const mres = await mu.json()
      if (!mu.ok || !mres.path) throw new Error(mres.detail || "Model upload failed")
      setLogs(prev => [...prev, `[${new Date().toISOString()}] MODEL_UPLOAD_COMPLETE`])
      setSteps(prev => prev.map(s => (s.id === "load_model" ? { ...s, status: "done" } : s)))

      let body: any = { path: mres.path, org_id: orgId }
      if (datasetFile) {
        setSteps(prev => prev.map(s => (s.id === "generate_data" ? { ...s, status: "running" } : s)))
        const dfd = new FormData()
        dfd.append("file", datasetFile)
        const du = await fetch(`${API_URL}/datasets/upload`, { method: "POST", body: dfd })
        const dres = await du.json()
        if (!du.ok || !dres.path) throw new Error(dres.detail || "Dataset upload failed")
        if (!target) throw new Error("Target column required")
        if (!features) throw new Error("Features required (comma-separated)")
        body = {
          path: mres.path,
          dataset_path: dres.path,
          target,
          features: features.split(",").map(s => s.trim()).filter(Boolean),
          protected_attributes: protectedAttrs.split(",").map(s => s.trim()).filter(Boolean),
        }
        setSteps(prev => prev.map(s => (s.id === "generate_data" ? { ...s, status: "done" } : s)))
      } else if (target && features) {
        setSteps(prev => prev.map(s => (s.id === "generate_data" ? { ...s, status: "running" } : s)))
        const schema = { columns: [
          ...features.split(',').map(f => ({ name: f.trim(), dtype: 'float' })),
          { name: target.trim(), dtype: 'int' },
        ]}
        const gr = await fetch(`${API_URL}/datasets/generate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ row_count: 1000, schema, engine }) })
        const gj = await gr.json()
        if (!gr.ok || !gj.path) throw new Error(gj.detail || 'Generation failed')
        body = {
          path: mres.path,
          dataset_path: gj.path,
          target,
          features: features.split(',').map(s => s.trim()).filter(Boolean),
          protected_attributes: protectedAttrs.split(',').map(s => s.trim()).filter(Boolean),
          org_id: orgId,
        }
        setLogs(prev => [...prev, `[${new Date().toISOString()}] DATASET_GENERATED engine=${engine}`])
        setSteps(prev => prev.map(s => (s.id === "generate_data" ? { ...s, status: "done" } : s)))
      }

      setSteps(prev => prev.map(s => (s.id === "fairness" ? { ...s, status: "running" } : s)))
      const run = await fetch(`${API_URL}/simulation/run`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
      const rjson = await run.json()
      if (!run.ok) throw new Error(rjson.detail || "Simulation failed")
      setResult(rjson)
      setLogs(prev => [...prev, `[${new Date().toISOString()}] FAIRNESS_ANALYSIS_COMPLETE`])
      setSteps(prev => prev.map(s => (s.id === "fairness" ? { ...s, status: "done" } : s)))
    } catch (e: any) {
      setResult({ error: e?.message || String(e) })
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">New Simulation</h1>
          <p className="text-muted-foreground">Create and run AI model simulations</p>
        </div>
      </div>

      {/* Simplify: remove embedded wizard to avoid duplicate flows on this page */}

      <Card>
        <CardHeader>
          <CardTitle>Simulation Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="text-sm text-muted-foreground">
            <div className="mb-2">Step 1: Upload/Select Model → Step 2: Provide Dataset or Schema → Step 3: Review & Run</div>
            <div className="mb-4">If you don't have a dataset, provide target and features and use the Generate tab to synthesize data.</div>
          </div>
          {/* Shared columns used by both data paths */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            <div className="space-y-2">
              <Label>Target column</Label>
              <Input placeholder="label" value={target} onChange={(e) => setTarget(e.target.value)} />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label>Feature columns (comma-separated)</Label>
              <Input placeholder="age,income" value={features} onChange={(e) => setFeatures(e.target.value)} />
            </div>
          </div>
          <div className="space-y-2">
            <Label>Protected attributes (comma-separated)</Label>
            <Input placeholder="gender,race" value={protectedAttrs} onChange={(e) => setProtectedAttrs(e.target.value)} />
          </div>
          <Tabs defaultValue="upload" className="w-full">
            <TabsList>
              <TabsTrigger value="upload">Upload Dataset</TabsTrigger>
              <TabsTrigger value="generate">Generate Synthetic Data</TabsTrigger>
            </TabsList>
            <TabsContent value="upload" className="space-y-4">
              <div className="space-y-2">
                <Label>Model file (.pkl/.joblib/.pt/.onnx/.h5)</Label>
                <Input type="file" accept=".pkl,.pickle,.joblib,.pt,.pth,.onnx,.pb,.h5" onChange={(e) => setModelFile(e.target.files?.[0] || null)} />
              </div>
              <div className="space-y-2">
                <Label>Dataset file (CSV/Parquet)</Label>
                <Input type="file" accept=".csv,.parquet" onChange={(e) => setDatasetFile(e.target.files?.[0] || null)} />
              </div>
              <div className="flex items-center gap-3">
                <Button onClick={runSimulation} disabled={running || !modelFile || !datasetFile || !target || !features}>
                  <Play className="mr-2 h-4 w-4" />
                  {running ? "Running..." : "Run Simulation"}
                </Button>
                <span className="text-xs text-muted-foreground">Upload a dataset and provide target/features to run.</span>
              </div>
              {result && (
                <div className="rounded border p-3 text-sm">
                  {result.error ? (
                    <p className="text-red-600">{result.error}</p>
                  ) : (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {result.metrics?.performance?.accuracy && (
                          <div className="text-center">
                            <div className="text-2xl font-bold">{Math.round(result.metrics.performance.accuracy * 100)}%</div>
                            <div className="text-xs text-muted-foreground">Accuracy</div>
                          </div>
                        )}
                        {result.metrics?.performance?.precision_macro && (
                          <div className="text-center">
                            <div className="text-2xl font-bold">{Math.round(result.metrics.performance.precision_macro * 100)}%</div>
                            <div className="text-xs text-muted-foreground">Precision</div>
                          </div>
                        )}
                        {result.metrics?.performance?.recall_macro && (
                          <div className="text-center">
                            <div className="text-2xl font-bold">{Math.round(result.metrics.performance.recall_macro * 100)}%</div>
                            <div className="text-xs text-muted-foreground">Recall</div>
                          </div>
                        )}
                        {result.metrics?.performance?.f1_macro && (
                          <div className="text-center">
                            <div className="text-2xl font-bold">{Math.round(result.metrics.performance.f1_macro * 100)}%</div>
                            <div className="text-xs text-muted-foreground">F1 Score</div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </TabsContent>
            <TabsContent value="generate" className="space-y-4">
              <p className="text-sm text-muted-foreground">Generate a synthetic dataset. If you provide a small sample dataset first, we’ll infer distributions; else we’ll use your schema selections.</p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                <div className="space-y-2">
                  <Label>Optional sample (CSV/Parquet)</Label>
                  <Input type="file" accept=".csv,.parquet" onChange={(e) => setDatasetFile(e.target.files?.[0] || null)} />
                </div>
                <div className="space-y-2">
                  <Label>Rows</Label>
                  <Input type="number" defaultValue={1000} id="gen-rows" />
                </div>
                <div className="space-y-2">
                  <Label>Engine</Label>
                  <select className="h-9 rounded-md border px-3 text-sm bg-background" value={engine} onChange={(e) => setEngine(e.target.value as any)}>
                    <option value="builtin">Builtin (NumPy/Pandas)</option>
                    <option value="sdv">SDV (requires sample data)</option>
                  </select>
                </div>
              </div>
              <div>
                <Button
                  onClick={async () => {
                    try {
                      const rowsEl = document.getElementById('gen-rows') as HTMLInputElement
                      const rowCount = Math.max(1, parseInt(rowsEl?.value || '1000', 10))
                      let samplePath: string | undefined
                      
                      if (datasetFile) {
                        const dfd = new FormData()
                        dfd.append('file', datasetFile)
                        const du = await fetch(`${API_URL}/datasets/upload`, { method: 'POST', body: dfd })
                        const dres = await du.json()
                        if (!du.ok || !dres.path) throw new Error(dres.detail || 'Sample upload failed')
                        samplePath = dres.path
                      }
                      
                      // Validate inputs per engine
                      if (engine === 'sdv' && !samplePath) {
                        setResult({ error: 'SDV engine requires a sample dataset (CSV/Parquet). Upload a small sample or switch engine to Builtin.' })
                        return
                      }
                      if (!samplePath && (!target || !features)) {
                        setResult({ error: 'Provide target and features to generate synthetic data without a sample.' })
                        return
                      }
                      
                      // Build schema from target/features when no sample
                      const payload: any = { row_count: rowCount, engine }
                      if (samplePath) {
                        payload.sample_path = samplePath
                      } else {
                        payload.schema = {
                          columns: [
                            ...features.split(',').map((f) => ({ name: f.trim(), dtype: 'float' })),
                            { name: target.trim(), dtype: 'int' },
                          ],
                        }
                      }
                      
                      const gr = await fetch(`${API_URL}/datasets/generate`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                      })
                      const gj = await gr.json()
                      if (!gr.ok || !gj.path) throw new Error(gj.detail || 'Generation failed')
                      
                      // Auto-run with generated dataset
                      if (!modelFile) throw new Error('Select a model file to run on synthetic data')
                      const mfd = new FormData()
                      mfd.append('file', modelFile)
                      const mu = await fetch(`${API_URL}/models/upload`, { method: 'POST', body: mfd })
                      const mres = await mu.json()
                      if (!mu.ok || !mres.path) throw new Error(mres.detail || 'Model upload failed')
                      
                      const body = {
                        path: mres.path,
                        dataset_path: gj.path,
                        target,
                        features: features.split(',').map(s => s.trim()).filter(Boolean),
                        protected_attributes: protectedAttrs.split(',').map(s => s.trim()).filter(Boolean),
                        org_id: orgId,
                      }
                      
                      const run = await fetch(`${API_URL}/simulation/run`, { 
                        method: 'POST', 
                        headers: { 'Content-Type': 'application/json' }, 
                        body: JSON.stringify(body) 
                      })
                      const rjson = await run.json()
                      if (!run.ok) throw new Error(rjson.detail || 'Simulation failed')
                      setResult(rjson)
                    } catch (error: any) {
                      setResult({ error: error?.message || String(error) })
                    }
                  }}
                >
                  Generate + Run
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Progress Steps</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              {steps.map((s) => (
                <div key={s.id} className="flex items-center justify-between border-b last:border-0 py-2">
                  <span>{s.label}</span>
                  <Badge variant={s.status === 'done' ? 'default' : s.status === 'running' ? 'secondary' : 'outline'}>{s.status}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Live Logs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 overflow-auto rounded border p-2 font-mono text-xs bg-black text-green-200">
              {logs.length === 0 ? (
                <div className="opacity-60">No logs yet…</div>
              ) : (
                logs.map((l, i) => <div key={i}>{l}</div>)
              )}
            </div>
          </CardContent>
        </Card>
        <SimulationHistory 
          runs={simulationHistory} 
          onViewDetails={(run) => setSelectedRun(run)}
        />
      </div>

      {/* Simulation Results Visualizations */}
      {result && !result.error && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Simulation Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Confusion Matrix */}
                <ConfusionMatrix 
                  matrix={result.metrics?.performance?.confusion_matrix}
                  labels={result.metrics?.performance?.labels}
                />
                
                {/* Per-Class Metrics */}
                <PerClassMetrics 
                  perClass={result.metrics?.performance?.per_class}
                />
              </div>
              
              {/* Fairness by Attribute */}
              <div className="mt-6">
                <FairnessByAttribute 
                  byAttribute={result.metrics?.fairness?.by_attribute}
                />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Selected Run Details */}
      {selectedRun && (
        <Card>
          <CardHeader>
            <CardTitle>Run Details: {selectedRun.model_name}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ConfusionMatrix 
                matrix={selectedRun.metrics?.performance?.confusion_matrix}
                labels={selectedRun.metrics?.performance?.labels}
              />
              <PerClassMetrics 
                perClass={selectedRun.metrics?.performance?.per_class}
              />
            </div>
            <div className="mt-6">
              <FairnessByAttribute 
                byAttribute={selectedRun.metrics?.fairness?.by_attribute}
              />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
} 