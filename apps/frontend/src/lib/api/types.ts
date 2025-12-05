/**
 * API Types - TypeScript interfaces for all API requests and responses
 * This file should be kept in sync with backend API models
 */

// Common types
export interface HealthStatus {
  status: 'healthy' | 'unhealthy'
  timestamp: string
  version?: string
  services?: Record<string, 'up' | 'down'>
}

// Authentication
export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface User {
  id: string
  username: string
  email: string
  role?: string
}

// Dashboard
export interface DashboardStats {
  totalModels?: number
  totalDatasets?: number
  activeScans?: number
  recentActivity?: ActivityItem[]
  systemHealth?: HealthStatus
  // Backend returns different format
  total_users?: number
  total_analyses?: number
  total_audit_logs?: number
  active_users?: number
  high_risk_analyses?: number
  recent_activity?: number
}

export interface ActivityItem {
  id: string
  type: string
  description: string
  timestamp: string
  user?: string
}

// Models
export interface Model {
  id: string
  name: string
  version: string
  type: string
  status: 'active' | 'inactive' | 'deprecated'
  createdAt: string
  updatedAt: string
  description?: string
  fairness_score: number
  bias_score: number
  accuracy?: number
  tags?: string[]
  metadata?: Record<string, any>
}

// Bias Detection
export interface BiasTestRequest {
  dataset_id: string
  model_id?: string
  sensitive_attributes: string[]
  target_column?: string
  model_outputs?: any[]
  category?: string
  modalities?: string[]
}

export interface BiasTestResponse {
  testId: string
  results: BiasResult[]
  summary: BiasSummary
  timestamp: string
}

export interface BiasResult {
  metric: string
  value: number
  threshold: number
  passed: boolean
}

export interface BiasSummary {
  totalTests: number
  passed: number
  failed: number
  riskLevel: 'low' | 'medium' | 'high' | 'critical'
}

// Security
export interface SecurityScanRequest {
  target: string
  scanType: 'container' | 'llm' | 'model'
  options?: Record<string, any>
}

export interface SecurityScanResponse {
  scanId: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  results?: SecurityResults
  timestamp: string
}

export interface SecurityResults {
  vulnerabilities: Vulnerability[]
  riskScore: number
  recommendations: string[]
}

export interface Vulnerability {
  id: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  title: string
  description: string
  remediation?: string
}

// Security
export interface SecurityScanRequest {
  target: string
  scanType: 'container' | 'llm' | 'model'
  options?: Record<string, any>
}

export interface SecurityScanResponse {
  scanId: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  results?: SecurityResults
  timestamp: string
}

export interface SecurityResults {
  vulnerabilities: Vulnerability[]
  riskScore: number
  recommendations: string[]
}

export interface Vulnerability {
  id: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  title: string
  description: string
  remediation?: string
}


