/**
 * Zod validation schemas for forms
 */

import { z } from 'zod'

// Authentication
export const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
})

export const registerSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
})

// Model Registration
export const modelSchema = z.object({
  name: z.string().min(1, 'Model name is required'),
  version: z.string().min(1, 'Version is required'),
  type: z.string().min(1, 'Model type is required'),
  description: z.string().optional(),
})

// Bias Test
export const biasTestSchema = z.object({
  modelId: z.string().min(1, 'Model ID is required'),
  testType: z.enum(['weat', 'fairness', 'image', 'text'], {
    errorMap: () => ({ message: 'Invalid test type' }),
  } as any),
  parameters: z.string().refine(
    (val) => {
      try {
        JSON.parse(val)
        return true
      } catch {
        return false
      }
    },
    { message: 'Parameters must be valid JSON' }
  ),
})

// Security Scan
export const securityScanSchema = z.object({
  target: z.string().min(1, 'Target is required'),
  scanType: z.enum(['container', 'llm', 'model']),
  options: z.record(z.string(), z.any()).optional(),
})

// Lifecycle
export const lifecycleSchema = z.object({
  systemId: z.string().min(1, 'System ID is required'),
  stage: z.string().min(1, 'Stage is required'),
  metadata: z.record(z.string(), z.any()).optional(),
})

// Evidence Collection
export const evidenceSchema = z.object({
  systemId: z.string().min(1, 'System ID is required'),
  type: z.string().min(1, 'Evidence type is required'),
  content: z.any(),
  confidence: z.number().min(0).max(1),
})

// Risk Assessment
export const riskAssessmentSchema = z.object({
  systemId: z.string().min(1, 'System ID is required'),
  riskType: z.string().min(1, 'Risk type is required'),
  severity: z.enum(['low', 'medium', 'high', 'critical']),
  description: z.string().min(1, 'Description is required'),
})

// Policy Creation
export const policySchema = z.object({
  name: z.string().min(1, 'Policy name is required'),
  framework: z.string().min(1, 'Framework is required'),
  description: z.string().optional(),
  rules: z.array(z.any()).min(1, 'At least one rule is required'),
})

// Dataset Upload
export const datasetSchema = z.object({
  name: z.string().min(1, 'Dataset name is required'),
  type: z.string().min(1, 'Dataset type is required'),
  description: z.string().optional(),
})

// Advanced Bias Analysis
export const advancedBiasSchema = z.object({
  modelId: z.string().min(1, 'Model ID is required'),
  analysisType: z.enum(['causal', 'counterfactual', 'intersectional', 'adversarial', 'temporal', 'contextual']),
  parameters: z.record(z.string(), z.any()).optional(),
})

// Benchmark
export const benchmarkSchema = z.object({
  modelId: z.string().min(1, 'Model ID is required'),
  benchmarkType: z.string().min(1, 'Benchmark type is required'),
  datasetId: z.string().optional(),
  metrics: z.array(z.string()).min(1, 'At least one metric is required'),
})

// Report Generation
export const reportSchema = z.object({
  type: z.string().min(1, 'Report type is required'),
  systemId: z.string().optional(),
  format: z.enum(['pdf', 'json', 'csv']).default('pdf'),
  includeCharts: z.boolean().default(true),
})

export type LoginFormData = z.infer<typeof loginSchema>
export type RegisterFormData = z.infer<typeof registerSchema>
export type ModelFormData = z.infer<typeof modelSchema>
export type BiasTestFormData = z.infer<typeof biasTestSchema>
export type SecurityScanFormData = z.infer<typeof securityScanSchema>
export type LifecycleFormData = z.infer<typeof lifecycleSchema>
export type EvidenceFormData = z.infer<typeof evidenceSchema>
export type RiskAssessmentFormData = z.infer<typeof riskAssessmentSchema>
export type PolicyFormData = z.infer<typeof policySchema>
export type DatasetFormData = z.infer<typeof datasetSchema>
export type AdvancedBiasFormData = z.infer<typeof advancedBiasSchema>
export type BenchmarkFormData = z.infer<typeof benchmarkSchema>
export type ReportFormData = z.infer<typeof reportSchema>

