"use client"
import { useEffect, useState } from "react"
import { useAuth } from "@/contexts/auth-context"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Plus, Search, Eye, Play, FileText, TrendingUp, Shield, Brain, AlertTriangle } from "lucide-react"
import Link from "next/link"
import { FairnessChart } from "@/components/charts/fairness-chart"
import { RiskHeatmap } from "@/components/charts/risk-heatmap"
import { PerformanceMatrix } from "@/components/charts/performance-matrix"
import { ComplianceTimeline } from "@/components/charts/compliance-timeline"

// No mock simulations; charts render empty states until data exists

// Governance tiles will be wired to backend; values are filled from API when available
const governanceMetrics: { label: string; value?: string; trend?: string; icon: any }[] = [
  { label: "NIST_COMPLIANCE", icon: Shield },
  { label: "ACTIVE_MODELS", icon: Brain },
  { label: "CRITICAL_RISKS", icon: AlertTriangle },
  { label: "LLM_SAFETY_SCORE", icon: Brain },
]

export default function DashboardPage() {
  const [openQuickSim, setOpenQuickSim] = useState(false)
  const [modelFile, setModelFile] = useState<File | null>(null)
  const [datasetFile, setDatasetFile] = useState<File | null>(null)
  const [target, setTarget] = useState("")
  const [features, setFeatures] = useState("")
  const [protectedAttrs, setProtectedAttrs] = useState("")
  const [engine, setEngine] = useState<"builtin" | "sdv">("builtin")
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [suggestions, setSuggestions] = useState<Array<{ name: string; link: string; target: string; features: string; protectedAttrs?: string }>>([])
  const [fairnessData, setFairnessData] = useState<{ name: string; score: number; baseline: number }[]>([])
  const [recent, setRecent] = useState<any[]>([])
  const [tiles, setTiles] = useState<Record<string, string>>({})
  const [orgId, setOrgId] = useState<string | null>(null)
  const { profile } = useAuth()

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"

  // Fetch dashboard data
  useEffect(() => {
    setOrgId(profile?.default_org_id || null)
  }, [profile?.default_org_id])

  useEffect(() => {
    const load = async () => {
      try {
        const [summaryRes, recentRes] = await Promise.all([
          fetch(`${API_URL}/metrics/summary?company=${orgId || ''}`),
          fetch(`${API_URL}/simulations/recent?company=${orgId || ''}&limit=5`),
        ])
        const summary = await summaryRes.json()
        const recentJson = await recentRes.json()
        if (summaryRes.ok && summary?.fairness?.attributes) {
          const mapped = (summary.fairness.attributes as any[]).map(a => ({
            name: String(a.attribute).toUpperCase(),
            score: Number(a.avg_demographic_parity_difference || 0),
            baseline: 0,
          }))
          setFairnessData(mapped)
          setTiles(t => ({ ...t, RUNS: String(summary.runs || 0) }))
        }
        if (recentRes.ok) setRecent(recentJson.data || [])
      } catch {
        // ignore
      }
    }
    void load()
  }, [API_URL, orgId])

  const runQuickSimulation = async () => {
    try {
      setRunning(true)
      setResult(null)
      if (!modelFile) throw new Error("Select a model file")

      // Upload model
      const mfd = new FormData()
      mfd.append("file", modelFile)
      const mu = await fetch(`${API_URL}/models/upload`, { method: "POST", body: mfd })
      const mres = await mu.json()
      if (!mu.ok || !mres.path) throw new Error(mres.detail || "Model upload failed")
      if (mres.validation && typeof mres.validation === 'string' && mres.validation.startsWith('load_failed')) {
        setResult({ warning: `Model loaded with warnings: ${mres.validation}. We will still run using fallback predictions.` })
      }

      // If dataset provided, upload and run with params; else attempt auto-synthetic if target/features exist
      let body: any = { path: mres.path, company: 'axonome.xyz', org_id: orgId }
      if (datasetFile) {
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
          company: 'axonome.xyz',
          org_id: orgId,
        }
      } else if (target && features) {
        // Auto-generate synthetic dataset based on provided schema
        const schema = {
          columns: [
            ...features.split(',').map((f) => ({ name: f.trim(), dtype: 'float' })),
            { name: target.trim(), dtype: 'int' },
          ],
        }
        const gr = await fetch(`${API_URL}/datasets/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ row_count: 1000, schema, engine }),
        })
        const gj = await gr.json()
        if (!gr.ok || !gj.path) throw new Error(gj.detail || 'Synthetic generation failed')
        body = {
          path: mres.path,
          dataset_path: gj.path,
          target,
          features: features.split(",").map(s => s.trim()).filter(Boolean),
          protected_attributes: protectedAttrs.split(",").map(s => s.trim()).filter(Boolean),
          company: 'axonome.xyz',
          org_id: orgId,
        }
      }

      const run = await fetch(`${API_URL}/simulation/run`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
      const rjson = await run.json()
      if (!run.ok) throw new Error(rjson.detail || "Simulation failed")
      setResult(rjson)
    } catch (e: any) {
      setResult({ error: e?.message || String(e) })
    } finally {
      setRunning(false)
    }
  }

  const suggestDatasets = () => {
    const fname = (modelFile?.name || "").toLowerCase()
    // Very lightweight heuristic; can expand later by inspecting model metadata
    const isCredit = fname.includes("credit") || fname.includes("loan")
    const isTabular = true
    const list: Array<{ name: string; link: string; target: string; features: string; protectedAttrs?: string }> = []

    // UCI Adult Income
    list.push({
      name: "UCI Adult Income",
      link: "https://archive.ics.uci.edu/dataset/2/adult",
      target: "income",
      features: "age,education_num,capital_gain,capital_loss,hours_per_week,sex,race",
      protectedAttrs: "sex,race",
    })

    // UCI German Credit
    list.push({
      name: "UCI German Credit",
      link: "https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data",
      target: "credit_risk",
      features: "duration,credit_amount,age,sex,job,housing",
      protectedAttrs: "sex,age",
    })

    // Kaggle Lending Club
    if (isCredit) {
      list.push({
        name: "Kaggle Lending Club Loans",
        link: "https://www.kaggle.com/datasets/wordsforthewise/lending-club",
        target: "loan_status",
        features: "loan_amnt,term,int_rate,annual_inc,emp_length,purpose,dti",
      })
    }

    // Kaggle Titanic
    if (isTabular) {
      list.push({
        name: "Kaggle Titanic",
        link: "https://www.kaggle.com/c/titanic",
        target: "Survived",
        features: "Pclass,Sex,Age,SibSp,Parch,Fare,Embarked",
        protectedAttrs: "Sex,Age",
      })
    }

    setSuggestions(list)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome to your AI governance dashboard
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Dialog open={openQuickSim} onOpenChange={setOpenQuickSim}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Quick Simulation
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-xl">
              <DialogHeader>
                <DialogTitle>Run Quick Simulation</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-2">
                <div className="space-y-2">
                  <Label>Model file (.pkl/.joblib/.pt/.onnx/.h5)</Label>
                  <Input type="file" accept=".pkl,.pickle,.joblib,.pt,.pth,.onnx,.pb,.h5" onChange={(e) => setModelFile(e.target.files?.[0] || null)} />
                </div>
                <div className="space-y-2">
                  <Label>Dataset file (CSV/Parquet) optional</Label>
                  <Input type="file" accept=".csv,.parquet" onChange={(e) => setDatasetFile(e.target.files?.[0] || null)} />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  <div className="space-y-2">
                    <Label>Target column</Label>
                    <Input placeholder="label" value={target} onChange={(e) => setTarget(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label>Feature columns (comma-separated)</Label>
                    <Input placeholder="age,income" value={features} onChange={(e) => setFeatures(e.target.value)} />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Protected attributes (comma-separated)</Label>
                  <Input placeholder="gender,race" value={protectedAttrs} onChange={(e) => setProtectedAttrs(e.target.value)} />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  <div className="space-y-2">
                    <Label>Synthetic engine</Label>
                    <select className="h-9 rounded-md border px-3 text-sm bg-background" value={engine} onChange={(e) => setEngine(e.target.value as any)}>
                      <option value="builtin">Builtin (NumPy/Pandas)</option>
                      <option value="sdv">SDV (requires sample data)</option>
                    </select>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button type="button" variant="secondary" onClick={suggestDatasets}>Suggest datasets</Button>
                  {suggestions.length > 0 && (
                    <span className="text-xs text-muted-foreground">Select a preset to auto-fill fields</span>
                  )}
                </div>
                {suggestions.length > 0 && (
                  <div className="space-y-2 rounded-md border p-2">
                    {suggestions.map((sug, i) => (
                      <div key={i} className="flex items-center justify-between gap-2 text-sm">
                        <div className="min-w-0">
                          <div className="font-medium truncate">{sug.name}</div>
                          <a className="text-xs text-blue-600 hover:underline" href={sug.link} target="_blank" rel="noreferrer">Open dataset</a>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setTarget(sug.target)
                              setFeatures(sug.features)
                              if (sug.protectedAttrs) setProtectedAttrs(sug.protectedAttrs)
                            }}
                          >
                            Prefill
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {result && (
                  <div className="rounded border p-3 text-sm">
                    {result.error ? (
                      <p className="text-red-600">{result.error}</p>
                    ) : (
                      <pre className="whitespace-pre-wrap break-all">{JSON.stringify(result.metrics, null, 2)}</pre>
                    )}
                  </div>
                )}
              </div>
              <DialogFooter>
                <Button onClick={runQuickSimulation} disabled={running || !modelFile}>{running ? "Running..." : "Run"}</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Governance Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {governanceMetrics.map((metric) => (
          <Card key={metric.label}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {metric.label}
              </CardTitle>
              <metric.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{tiles[metric.label] || '—'}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Visualizations */}
      <div className="grid gap-4 md:grid-cols-2">
        <FairnessChart data={fairnessData} />
        <RiskHeatmap />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Performance Matrix</CardTitle>
          </CardHeader>
          <CardContent>
            <PerformanceMatrix data={undefined} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Compliance Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <ComplianceTimeline data={undefined} />
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card className="md:col-span-2 lg:col-span-3">
          <CardHeader>
            <CardTitle>Recent Runs</CardTitle>
          </CardHeader>
          <CardContent>
            {recent.length === 0 ? (
              <div className="text-sm text-muted-foreground">No recent simulations.</div>
            ) : (
              <div className="grid gap-2">
                {recent.map((r, idx) => (
                  <div key={idx} className="flex justify-between text-sm border rounded p-2">
                    <div className="flex-1">
                      <div className="font-medium">{r.artifact?.path?.split('/').pop() || 'model'}</div>
                      <div className="text-muted-foreground">{new Date(r.created_at).toLocaleString()}</div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div>Acc: {r.metrics?.performance?.accuracy?.toFixed ? r.metrics.performance.accuracy.toFixed(3) : r.metrics?.performance?.accuracy || '—'}</div>
                      <div>Attrs: {(r.metrics?.fairness?.by_attribute || []).length}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Bias Detection</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Test your models for bias and fairness issues
            </p>
            <Link href="/bias-detection">
              <Button className="w-full">Start Analysis</Button>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Model DNA</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Analyze model lineage and inheritance patterns
            </p>
            <Link href="/model-dna">
              <Button className="w-full">View DNA</Button>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Compliance</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Check regulatory compliance status
            </p>
            <Link href="/compliance">
              <Button className="w-full">View Status</Button>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Run Simulation</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Run a full simulation with your model and dataset
            </p>
            <Link href="/simulation">
              <Button className="w-full">Go to Simulation</Button>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Upload Model</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Upload a new model to your inventory
            </p>
            <Link href="/model-upload">
              <Button className="w-full">Upload</Button>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Simulation History</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              View and analyze previous runs
            </p>
            <Link href="/simulation-history">
              <Button className="w-full">View History</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
