/**
 * JSON export of bias evaluation results.
 *
 * Lives in a separate file from `pdf-generator.ts` so that pages which only
 * need JSON export do not pull `jspdf`/`html2canvas` (and their transitive
 * `fflate` dependency) into the SSR bundle. Importing jspdf at module load
 * breaks the Next.js Turbopack production build.
 */

export interface BiasEvaluationPDFData {
  timestamp: string
  modelType: string
  modelDescription?: string
  evaluationSummary: {
    totalTests: number
    testsPassed: number
    testsFailed: number
    overallBiasRate: number
    evaluationTime?: string
  }
  overallRisk: 'low' | 'medium' | 'high' | 'critical'
  riskFactors?: string[]
  complianceStatus: {
    gdprCompliant?: boolean
    aiActCompliant?: boolean
    fairnessScore?: number
  }
  explainabilityAnalysis?: {
    methodsUsed?: string[]
    insights?: string[]
    confidence?: number
  }
  recommendations: string[]
  selectedTests: string[]
}

/**
 * Generate JSON export of evaluation results
 */
export function generateBiasJSON(data: BiasEvaluationPDFData): void {
  const jsonData = {
    metadata: {
      generatedAt: new Date().toISOString(),
      fairmindVersion: '1.0.0',
      platform: 'FairMind AI Governance Platform',
    },
    evaluation: data,
  }

  const jsonString = JSON.stringify(jsonData, null, 2)
  const blob = new Blob([jsonString], { type: 'application/json' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = `bias_evaluation_${new Date().toISOString().split('T')[0]}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
