/**
 * PDF Report Generator for Bias Evaluation Results
 * Generates professional, audit-ready PDF reports with FairMind branding
 */

import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'

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
 * Generate a professional PDF report from evaluation results
 */
export async function generateBiasPDF(data: BiasEvaluationPDFData): Promise<void> {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  })

  const pageWidth = doc.internal.pageSize.getWidth()
  const pageHeight = doc.internal.pageSize.getHeight()
  const margin = 15
  const contentWidth = pageWidth - margin * 2
  let yPosition = margin

  // Helper function to add text with proper spacing
  const addText = (
    text: string,
    fontSize: number = 12,
    fontWeight: 'normal' | 'bold' = 'normal',
    color: [number, number, number] = [0, 0, 0],
  ) => {
    doc.setFontSize(fontSize)
    if (fontWeight === 'bold') {
      doc.setFont(undefined, 'bold')
    } else {
      doc.setFont(undefined, 'normal')
    }
    doc.setTextColor(color[0], color[1], color[2])
    const textLines = doc.splitTextToSize(text, contentWidth)
    doc.text(textLines, margin, yPosition)
    yPosition += (textLines.length * fontSize) / 2 + 4
  }

  // Helper function to check page break
  const checkPageBreak = (spaceNeeded: number = 20) => {
    if (yPosition + spaceNeeded > pageHeight - margin) {
      doc.addPage()
      yPosition = margin
      // Add header on new pages
      addHeaderSmall()
    }
  }

  // Header function for new pages
  const addHeaderSmall = () => {
    doc.setFontSize(10)
    doc.setTextColor(128, 128, 128)
    doc.text('FairMind - Bias Evaluation Report', margin, margin / 2)
    doc.setDrawColor(200, 200, 200)
    doc.line(margin, margin - 2, pageWidth - margin, margin - 2)
    yPosition = margin + 2
  }

  // ============ PAGE 1: HEADER & EXECUTIVE SUMMARY ============

  // FairMind Branding
  doc.setFontSize(28)
  doc.setFont(undefined, 'bold')
  doc.setTextColor(0, 0, 0)
  doc.text('FairMind', margin, yPosition)
  yPosition += 12

  // Subtitle
  doc.setFontSize(10)
  doc.setFont(undefined, 'normal')
  doc.setTextColor(100, 100, 100)
  doc.text('AI Governance & Bias Detection Platform', margin, yPosition)
  yPosition += 8

  // Divider
  doc.setDrawColor(255, 107, 53) // Orange accent
  doc.setLineWidth(2)
  doc.line(margin, yPosition, pageWidth - margin, yPosition)
  yPosition += 8

  // Title
  addText('Bias Evaluation Report', 20, 'bold', [0, 0, 0])
  yPosition += 4

  // Report metadata
  doc.setFontSize(9)
  doc.setTextColor(100, 100, 100)
  const reportDate = new Date(data.timestamp).toLocaleString()
  doc.text(`Generated: ${reportDate}`, margin, yPosition)
  yPosition += 5
  doc.text(`Model Type: ${data.modelType.toUpperCase()}`, margin, yPosition)
  yPosition += 8

  // Executive Summary Box
  doc.setFillColor(245, 245, 245)
  doc.rect(margin, yPosition - 2, contentWidth, 50, 'F')
  doc.setDrawColor(200, 200, 200)
  doc.setLineWidth(0.5)
  doc.rect(margin, yPosition - 2, contentWidth, 50)

  yPosition += 4
  addText('EXECUTIVE SUMMARY', 12, 'bold', [0, 0, 0])

  // Risk level with color
  const riskColors: Record<string, [number, number, number]> = {
    low: [34, 197, 94],
    medium: [234, 179, 8],
    high: [249, 115, 22],
    critical: [239, 68, 68],
  }
  const riskColor = riskColors[data.overallRisk] || [100, 100, 100]

  doc.setTextColor(riskColor[0], riskColor[1], riskColor[2])
  doc.setFontSize(14)
  doc.setFont(undefined, 'bold')
  doc.text(`Overall Risk Level: ${data.overallRisk.toUpperCase()}`, margin + 4, yPosition)
  yPosition += 8

  doc.setTextColor(0, 0, 0)
  doc.setFontSize(10)
  doc.setFont(undefined, 'normal')
  doc.text(`Bias Rate: ${(data.evaluationSummary.overallBiasRate * 100).toFixed(1)}%`, margin + 4, yPosition)
  yPosition += 6
  doc.text(
    `Tests: ${data.evaluationSummary.testsPassed}/${data.evaluationSummary.totalTests} passed`,
    margin + 4,
    yPosition,
  )
  yPosition += 12

  // ============ EVALUATION SUMMARY ============
  checkPageBreak(40)
  addText('Evaluation Summary', 14, 'bold', [0, 0, 0])
  yPosition += 4

  // Summary table
  const summaryData = [
    ['Metric', 'Value'],
    ['Total Tests', data.evaluationSummary.totalTests.toString()],
    ['Tests Passed', data.evaluationSummary.testsPassed.toString()],
    ['Tests Failed', data.evaluationSummary.testsFailed.toString()],
    ['Overall Bias Rate', `${(data.evaluationSummary.overallBiasRate * 100).toFixed(1)}%`],
  ]

  if (data.evaluationSummary.evaluationTime) {
    summaryData.push(['Evaluation Time', data.evaluationSummary.evaluationTime])
  }

  doc.setFontSize(9)
  doc.setFont(undefined, 'normal')

  let tableYPosition = yPosition
  const cellHeight = 7
  const col1Width = contentWidth * 0.5
  const col2Width = contentWidth * 0.5

  summaryData.forEach((row, idx) => {
    const isHeader = idx === 0
    if (isHeader) {
      doc.setFillColor(50, 50, 50)
      doc.setTextColor(255, 255, 255)
      doc.setFont(undefined, 'bold')
    } else {
      if (idx % 2 === 0) {
        doc.setFillColor(240, 240, 240)
      } else {
        doc.setFillColor(255, 255, 255)
      }
      doc.setTextColor(0, 0, 0)
      doc.setFont(undefined, 'normal')
    }

    doc.rect(margin, tableYPosition, col1Width, cellHeight, isHeader ? 'F' : 'F')
    doc.rect(margin + col1Width, tableYPosition, col2Width, cellHeight, isHeader ? 'F' : 'F')

    doc.text(row[0], margin + 2, tableYPosition + 5)
    doc.text(row[1], margin + col1Width + 2, tableYPosition + 5)

    tableYPosition += cellHeight
  })

  yPosition = tableYPosition + 4

  // ============ COMPLIANCE STATUS ============
  checkPageBreak(35)
  addText('Compliance Status', 14, 'bold', [0, 0, 0])
  yPosition += 4

  const complianceItems = [
    { label: 'GDPR Compliance', value: data.complianceStatus.gdprCompliant },
    { label: 'EU AI Act Compliance', value: data.complianceStatus.aiActCompliant },
  ]

  complianceItems.forEach(item => {
    const status = item.value ? 'COMPLIANT' : 'NON-COMPLIANT'
    const statusColor = item.value ? [34, 197, 94] : [239, 68, 68]

    doc.setFontSize(10)
    doc.setFont(undefined, 'normal')
    doc.setTextColor(0, 0, 0)
    doc.text(item.label, margin, yPosition)

    doc.setFont(undefined, 'bold')
    doc.setTextColor(statusColor[0], statusColor[1], statusColor[2])
    doc.text(status, margin + 80, yPosition)
    yPosition += 8
  })

  if (data.complianceStatus.fairnessScore !== undefined) {
    doc.setTextColor(0, 0, 0)
    doc.setFont(undefined, 'normal')
    doc.setFontSize(10)
    doc.text(
      'Fairness Score',
      margin,
      yPosition,
    )
    doc.setFont(undefined, 'bold')
    doc.text(`${(data.complianceStatus.fairnessScore * 100).toFixed(1)}%`, margin + 80, yPosition)
    yPosition += 8
  }

  yPosition += 4

  // ============ RISK FACTORS ============
  if (data.riskFactors && data.riskFactors.length > 0) {
    checkPageBreak(30)
    addText('Identified Risk Factors', 14, 'bold', [239, 68, 68])
    yPosition += 4

    data.riskFactors.forEach((factor, idx) => {
      doc.setFontSize(9)
      doc.setTextColor(0, 0, 0)
      const bulletX = margin
      const textX = margin + 5
      doc.text('•', bulletX, yPosition)
      const factorLines = doc.splitTextToSize(factor, contentWidth - 8)
      doc.text(factorLines, textX, yPosition)
      yPosition += (factorLines.length * 4) + 2
    })
    yPosition += 4
  }

  // ============ EXPLAINABILITY ANALYSIS ============
  if (data.explainabilityAnalysis) {
    checkPageBreak(30)
    addText('Explainability Analysis', 14, 'bold', [0, 0, 0])
    yPosition += 4

    if (data.explainabilityAnalysis.methodsUsed && data.explainabilityAnalysis.methodsUsed.length > 0) {
      doc.setFontSize(10)
      doc.setFont(undefined, 'bold')
      doc.setTextColor(0, 0, 0)
      doc.text('Methods Used:', margin, yPosition)
      yPosition += 5

      doc.setFont(undefined, 'normal')
      doc.setFontSize(9)
      data.explainabilityAnalysis.methodsUsed.forEach(method => {
        doc.text(`• ${method.replace(/_/g, ' ')}`, margin + 4, yPosition)
        yPosition += 4
      })
      yPosition += 2
    }

    if (data.explainabilityAnalysis.confidence !== undefined) {
      doc.setFontSize(10)
      doc.setFont(undefined, 'bold')
      doc.setTextColor(0, 0, 0)
      doc.text('Analysis Confidence:', margin, yPosition)
      doc.setFont(undefined, 'normal')
      doc.text(`${(data.explainabilityAnalysis.confidence * 100).toFixed(1)}%`, margin + 60, yPosition)
      yPosition += 8
    }

    if (data.explainabilityAnalysis.insights && data.explainabilityAnalysis.insights.length > 0) {
      doc.setFontSize(10)
      doc.setFont(undefined, 'bold')
      doc.setTextColor(0, 0, 0)
      doc.text('Key Insights:', margin, yPosition)
      yPosition += 5

      doc.setFont(undefined, 'normal')
      doc.setFontSize(9)
      data.explainabilityAnalysis.insights.forEach((insight, idx) => {
        const insightLines = doc.splitTextToSize(`${idx + 1}. ${insight}`, contentWidth - 4)
        doc.text(insightLines, margin + 2, yPosition)
        yPosition += (insightLines.length * 4) + 2
      })
      yPosition += 2
    }
  }

  // ============ RECOMMENDATIONS ============
  checkPageBreak(40)
  addText('Recommendations', 14, 'bold', [34, 197, 94])
  yPosition += 4

  doc.setFontSize(9)
  doc.setTextColor(0, 0, 0)
  data.recommendations.forEach((rec, idx) => {
    const recLines = doc.splitTextToSize(`${idx + 1}. ${rec}`, contentWidth - 6)
    doc.text(recLines, margin + 4, yPosition)
    yPosition += (recLines.length * 4) + 3
  })

  yPosition += 8

  // ============ FOOTER ============
  checkPageBreak(20)
  doc.setDrawColor(200, 200, 200)
  doc.line(margin, yPosition, pageWidth - margin, yPosition)
  yPosition += 5

  doc.setFontSize(8)
  doc.setTextColor(128, 128, 128)
  doc.text('This report was generated by FairMind AI Governance Platform', margin, yPosition)
  yPosition += 4
  doc.text(`Report Generated: ${new Date().toISOString()}`, margin, yPosition)
  yPosition += 4
  doc.text('For more information, visit: https://fairmind.xyz', margin, yPosition)

  // Save the PDF
  const filename = `bias_evaluation_${new Date().toISOString().split('T')[0]}.pdf`
  doc.save(filename)
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
