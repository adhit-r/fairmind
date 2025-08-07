"use client"

import { Button } from "../components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Input } from "../components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table"
import { Badge } from "../components/ui/badge"
import { Plus, Search, Eye, Play, FileText, TrendingUp, TrendingDown, Shield, Brain, AlertTriangle } from "lucide-react"
import Link from "next/link"
import { AIGovernanceChart } from "../components/charts/ai-governance-chart"
import { DistributionChart } from "../components/charts/distribution-chart"
import { PerformanceMatrix } from "../components/charts/performance-matrix"
import { NISTComplianceMatrix } from "../components/charts/nist-compliance-matrix"
import { BiasDetectionRadar } from "../components/charts/bias-detection-radar"
import { LLMSafetyDashboard } from "../components/charts/llm-safety-dashboard"

export function SandboxHome() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight">AI_GOVERNANCE_DASHBOARD</h1>
        <p className="text-sm text-muted-foreground font-mono">
          COMPREHENSIVE.AI.RISK.MANAGEMENT.AND.COMPLIANCE.MONITORING.PLATFORM
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">NIST_COMPLIANCE</p>
                <p className="text-lg font-bold">82%</p>
              </div>
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4" />
                <div className="flex items-center gap-1">
                  <TrendingUp className="h-3 w-3" />
                  <span className="text-xs">+3.2%</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">ACTIVE_MODELS</p>
                <p className="text-lg font-bold">47</p>
              </div>
              <div className="flex items-center gap-2">
                <Brain className="h-4 w-4" />
                <div className="flex items-center gap-1">
                  <TrendingUp className="h-3 w-3" />
                  <span className="text-xs">+12</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">CRITICAL_RISKS</p>
                <p className="text-lg font-bold">3</p>
              </div>
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                <div className="flex items-center gap-1">
                  <TrendingDown className="h-3 w-3" />
                  <span className="text-xs">-2</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">LLM_SAFETY_SCORE</p>
                <p className="text-lg font-bold">88%</p>
              </div>
              <div className="flex items-center gap-2">
                <Brain className="h-4 w-4" />
                <div className="flex items-center gap-1">
                  <TrendingUp className="h-3 w-3" />
                  <span className="text-xs">+5.1%</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex gap-2">
          <Link href="/simulation/new">
            <Button className="bg-white text-black hover:bg-gray-200">
              <Plus className="mr-2 h-4 w-4" />
              NEW_SIMULATION
            </Button>
          </Link>
          <Link href="/governance">
            <Button variant="outline">
              <Shield className="mr-2 h-4 w-4" />
              GOVERNANCE_REVIEW
            </Button>
          </Link>
        </div>
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
          <Input
            placeholder="SEARCH_MODELS_AND_ASSESSMENTS..."
            className="pl-10 font-mono"
          />
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-sm">AI_GOVERNANCE_METRICS</CardTitle>
            <CardDescription className="text-xs">FAIRNESS.ROBUSTNESS.EXPLAINABILITY.COMPLIANCE.LLM_SAFETY</CardDescription>
          </CardHeader>
          <CardContent className="h-[300px]">
            <AIGovernanceChart />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">BIAS_DETECTION_RADAR</CardTitle>
            <CardDescription className="text-xs">DEMOGRAPHIC.BIAS.ANALYSIS</CardDescription>
          </CardHeader>
          <CardContent className="h-[300px]">
            <BiasDetectionRadar />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">MODEL_LIFECYCLE_TRACKING</CardTitle>
            <CardDescription className="text-xs">DEVELOPMENT.TO.DEPLOYMENT.METRICS</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[400px] flex items-center justify-center text-muted-foreground">
              Loading model lifecycle data...
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">MODEL_DRIFT_MONITOR</CardTitle>
            <CardDescription className="text-xs">DATA.CONCEPT.PREDICTION.DRIFT</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="animate-pulse rounded-md bg-muted h-6 w-56"></div>
              <div className="animate-pulse rounded-md bg-muted h-[250px] w-full"></div>
              <div className="flex justify-center gap-4">
                <div className="animate-pulse rounded-md bg-muted h-4 w-20"></div>
                <div className="animate-pulse rounded-md bg-muted h-4 w-20"></div>
                <div className="animate-pulse rounded-md bg-muted h-4 w-20"></div>
                <div className="animate-pulse rounded-md bg-muted h-4 w-20"></div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">COMPLIANCE_TIMELINE</CardTitle>
            <CardDescription className="text-xs">REGULATORY.COMPLIANCE.TRACKING</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="animate-pulse rounded-md bg-muted h-6 w-48"></div>
              <div className="animate-pulse rounded-md bg-muted h-[250px] w-full"></div>
              <div className="flex justify-center gap-4">
                <div className="animate-pulse rounded-md bg-muted h-4 w-16"></div>
                <div className="animate-pulse rounded-md bg-muted h-4 w-16"></div>
                <div className="animate-pulse rounded-md bg-muted h-4 w-16"></div>
                <div className="animate-pulse rounded-md bg-muted h-4 w-16"></div>
                <div className="animate-pulse rounded-md bg-muted h-4 w-16"></div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">LLM_SAFETY_DASHBOARD</CardTitle>
            <CardDescription className="text-xs">TOXICITY.BIAS.HALLUCINATION.MONITORING</CardDescription>
          </CardHeader>
          <CardContent className="h-[300px]">
            <LLMSafetyDashboard />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">AGE_DISTRIBUTION</CardTitle>
            <CardDescription className="text-xs">DEMOGRAPHIC.DISTRIBUTION.ANALYSIS</CardDescription>
          </CardHeader>
          <CardContent className="h-[300px]">
            <DistributionChart />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">FEATURE_IMPORTANCE_TREEMAP</CardTitle>
            <CardDescription className="text-xs">MODEL.EXPLAINABILITY.ANALYSIS</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-48 flex items-center justify-center text-muted-foreground">
              Loading feature importance data...
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">MODEL_PERFORMANCE_MATRIX</CardTitle>
            <CardDescription className="text-xs">CONFUSION.MATRIX.ANALYSIS</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="animate-pulse rounded-md bg-muted h-6 w-48"></div>
              <div className="grid grid-cols-5 gap-1">
                {Array.from({ length: 25 }).map((_, i) => (
                  <div key={i} className="animate-pulse rounded-md bg-muted h-12 w-full"></div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">NIST_AI_RMF_COMPLIANCE</CardTitle>
            <CardDescription className="text-xs">RISK.MANAGEMENT.FRAMEWORK</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Loading NIST AI RMF data...</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-32 flex items-center justify-center text-muted-foreground">
                    Loading compliance data...
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Loading risk assessment data...</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-32 flex items-center justify-center text-muted-foreground">
                    Loading risk data...
                  </div>
                </CardContent>
              </Card>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">RECENT_SIMULATIONS</CardTitle>
          <CardDescription className="text-xs">MODEL.TESTING.AND.VALIDATION.HISTORY</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-xs">MODEL_NAME</TableHead>
                <TableHead className="text-xs">MODEL_FILE</TableHead>
                <TableHead className="text-xs">DATE</TableHead>
                <TableHead className="text-xs">STATUS</TableHead>
                <TableHead className="text-xs">FAIRNESS</TableHead>
                <TableHead className="text-xs">ROBUSTNESS</TableHead>
                <TableHead className="text-xs">EXPLAINABILITY</TableHead>
                <TableHead className="text-xs">TYPE</TableHead>
                <TableHead className="text-xs">ACTIONS</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell className="font-mono text-xs">LOAN_MODEL_V1</TableCell>
                <TableCell className="font-mono text-xs">loan_v1.pkl</TableCell>
                <TableCell className="font-mono text-xs">2025.07.01</TableCell>
                <TableCell>
                  <Badge variant="default" className="text-xs">COMPLETED</Badge>
                </TableCell>
                <TableCell className="text-xs">78%</TableCell>
                <TableCell className="text-xs">90%</TableCell>
                <TableCell className="text-xs">70%</TableCell>
                <TableCell>
                  <Badge variant="outline" className="text-xs">TRADITIONAL_ML</Badge>
                </TableCell>
                <TableCell>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      <Eye className="h-3 w-3" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <Play className="h-3 w-3" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <FileText className="h-3 w-3" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-mono text-xs">GPT4_HIRING_ASSISTANT</TableCell>
                <TableCell className="font-mono text-xs">gpt-4-hiring.onnx</TableCell>
                <TableCell className="font-mono text-xs">2025.06.20</TableCell>
                <TableCell>
                  <Badge variant="outline" className="text-xs">IN_PROGRESS</Badge>
                </TableCell>
                <TableCell className="text-xs">0%</TableCell>
                <TableCell className="text-xs">0%</TableCell>
                <TableCell className="text-xs">0%</TableCell>
                <TableCell>
                  <Badge variant="outline" className="text-xs">LLM</Badge>
                </TableCell>
                <TableCell>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      <Eye className="h-3 w-3" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <Play className="h-3 w-3" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <FileText className="h-3 w-3" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-mono text-xs">CREDIT_SCORING_V3</TableCell>
                <TableCell className="font-mono text-xs">credit_v3.h5</TableCell>
                <TableCell className="font-mono text-xs">2025.06.15</TableCell>
                <TableCell>
                  <Badge variant="destructive" className="text-xs">FAILED</Badge>
                </TableCell>
                <TableCell className="text-xs">45%</TableCell>
                <TableCell className="text-xs">67%</TableCell>
                <TableCell className="text-xs">23%</TableCell>
                <TableCell>
                  <Badge variant="outline" className="text-xs">TRADITIONAL_ML</Badge>
                </TableCell>
                <TableCell>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      <Eye className="h-3 w-3" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <Play className="h-3 w-3" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <FileText className="h-3 w-3" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-mono text-xs">CLAUDE_LEGAL_ADVISOR</TableCell>
                <TableCell className="font-mono text-xs">claude-legal.pkl</TableCell>
                <TableCell className="font-mono text-xs">2025.06.10</TableCell>
                <TableCell>
                  <Badge variant="default" className="text-xs">COMPLETED</Badge>
                </TableCell>
                <TableCell className="text-xs">89%</TableCell>
                <TableCell className="text-xs">94%</TableCell>
                <TableCell className="text-xs">82%</TableCell>
                <TableCell>
                  <Badge variant="outline" className="text-xs">LLM</Badge>
                </TableCell>
                <TableCell>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      <Eye className="h-3 w-3" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <Play className="h-3 w-3" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <FileText className="h-3 w-3" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
