/**
 * Backend Report Generator for Bias Evaluation Results
 * Calls FairMind backend APIs to generate audit-ready PDF and DOCX reports
 */

const getBackendUrl = () => {
  if (typeof window === 'undefined') {
    return '/api/proxy'
  }
  return process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8010'
}

export interface BiasEvaluationReportData {
  modelType: string
  modelDescription: string
  evaluationSummary: {
    totalTests: number
    testsPassed: number
    testsFailed: number
    overallBiasRate: number
    evaluationTime: number
  }
  overallRisk: 'low' | 'medium' | 'high' | 'critical'
  riskFactors: string[]
  recommendations: string[]
  complianceStatus: {
    gdprCompliant: boolean
    aiActCompliant: boolean
    fairnessScore: number
  }
  explainabilityInsights?: Record<string, any>
}

/**
 * Convert frontend data format to backend API format
 */
function convertToBackendFormat(data: BiasEvaluationReportData) {
  return {
    model_type: data.modelType,
    model_description: data.modelDescription,
    evaluation_summary: {
      total_tests: data.evaluationSummary.totalTests,
      tests_passed: data.evaluationSummary.testsPassed,
      tests_failed: data.evaluationSummary.testsFailed,
      overall_bias_rate: data.evaluationSummary.overallBiasRate,
      evaluation_time: data.evaluationSummary.evaluationTime,
    },
    overall_risk: data.overallRisk,
    risk_factors: data.riskFactors,
    recommendations: data.recommendations,
    compliance_status: {
      gdpr_compliant: data.complianceStatus.gdprCompliant,
      ai_act_compliant: data.complianceStatus.aiActCompliant,
      fairness_score: data.complianceStatus.fairnessScore,
    },
    explainability_insights: data.explainabilityInsights || {},
  }
}

/**
 * Generate and download a PDF report from the backend
 */
export async function generatePDFReport(data: BiasEvaluationReportData): Promise<void> {
  try {
    const backendUrl = getBackendUrl()
    const response = await fetch(`${backendUrl}/api/v1/reports/bias-evaluation/pdf`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(convertToBackendFormat(data)),
    })

    if (!response.ok) {
      throw new Error(`Failed to generate PDF report: ${response.statusText}`)
    }

    // Get the PDF blob
    const blob = await response.blob()

    // Create a download link
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `bias_evaluation_report_${new Date().getTime()}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Error generating PDF report:', error)
    throw error
  }
}

/**
 * Generate and download a DOCX report from the backend
 */
export async function generateDOCXReport(data: BiasEvaluationReportData): Promise<void> {
  try {
    const backendUrl = getBackendUrl()
    const response = await fetch(`${backendUrl}/api/v1/reports/bias-evaluation/docx`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(convertToBackendFormat(data)),
    })

    if (!response.ok) {
      throw new Error(`Failed to generate DOCX report: ${response.statusText}`)
    }

    // Get the DOCX blob
    const blob = await response.blob()

    // Create a download link
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `bias_evaluation_report_${new Date().getTime()}.docx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Error generating DOCX report:', error)
    throw error
  }
}

/**
 * Get available report formats from the backend
 */
export async function getAvailableReportFormats() {
  try {
    const backendUrl = getBackendUrl()
    const response = await fetch(`${backendUrl}/api/v1/reports/formats`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch available formats: ${response.statusText}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error fetching available report formats:', error)
    throw error
  }
}
