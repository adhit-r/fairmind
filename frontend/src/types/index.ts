// Core Application Types
export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  permissions: Permission[];
  createdAt: Date;
  updatedAt: Date;
}

export type UserRole = 'admin' | 'analyst' | 'viewer' | 'stakeholder';

export type Permission = 
  | 'models:read' 
  | 'models:write' 
  | 'simulations:read' 
  | 'simulations:write'
  | 'governance:read'
  | 'governance:write'
  | 'reports:read'
  | 'reports:write';

// Model Types
export interface AIModel {
  id: string;
  name: string;
  version: string;
  type: ModelType;
  status: ModelStatus;
  filePath: string;
  metadata: ModelMetadata;
  createdAt: Date;
  updatedAt: Date;
}

export type ModelType = 'TRADITIONAL_ML' | 'LLM' | 'DEEP_LEARNING' | 'ENSEMBLE';

export type ModelStatus = 'DRAFT' | 'TRAINING' | 'ACTIVE' | 'DEPRECATED' | 'ARCHIVED';

export interface ModelMetadata {
  description: string;
  tags: string[];
  framework: string;
  algorithm: string;
  hyperparameters: Record<string, any>;
  trainingData: {
    size: number;
    features: number;
    samples: number;
  };
  performance: {
    accuracy: number;
    precision: number;
    recall: number;
    f1Score: number;
  };
}

// Simulation Types
export interface Simulation {
  id: string;
  name: string;
  modelId: string;
  model: AIModel;
  status: SimulationStatus;
  type: SimulationType;
  config: SimulationConfig;
  results: SimulationResults;
  createdAt: Date;
  updatedAt: Date;
  completedAt?: Date;
}

export type SimulationStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export type SimulationType = 'FAIRNESS' | 'ROBUSTNESS' | 'EXPLAINABILITY' | 'COMPLIANCE' | 'LLM_SAFETY';

export interface SimulationConfig {
  testCases: number;
  scenarios: string[];
  thresholds: Record<string, number>;
  parameters: Record<string, any>;
}

export interface SimulationResults {
  fairness: number;
  robustness: number;
  explainability: number;
  compliance: number;
  llmSafety?: number;
  details: Record<string, any>;
  charts: ChartData[];
  logs: SimulationLog[];
}

export interface SimulationLog {
  id: string;
  timestamp: Date;
  level: 'INFO' | 'WARNING' | 'ERROR';
  message: string;
  details?: Record<string, any>;
}

// Chart Types
export interface ChartData {
  id: string;
  type: ChartType;
  title: string;
  data: any;
  config: ChartConfig;
}

export type ChartType = 'line' | 'bar' | 'radar' | 'pie' | 'scatter' | 'heatmap';

export interface ChartConfig {
  responsive: boolean;
  maintainAspectRatio: boolean;
  plugins?: Record<string, any>;
  scales?: Record<string, any>;
}

// Governance Types
export interface GovernanceMetric {
  id: string;
  name: string;
  value: number;
  unit: string;
  trend: number;
  threshold: number;
  status: 'GOOD' | 'WARNING' | 'CRITICAL';
  category: GovernanceCategory;
  updatedAt: Date;
}

export type GovernanceCategory = 'FAIRNESS' | 'ROBUSTNESS' | 'EXPLAINABILITY' | 'COMPLIANCE' | 'LLM_SAFETY';

export interface ComplianceFramework {
  id: string;
  name: string;
  version: string;
  requirements: ComplianceRequirement[];
  status: ComplianceStatus;
  lastAudit: Date;
  nextAudit: Date;
}

export interface ComplianceRequirement {
  id: string;
  code: string;
  description: string;
  status: 'COMPLIANT' | 'NON_COMPLIANT' | 'PARTIAL';
  evidence: string[];
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

export type ComplianceStatus = 'COMPLIANT' | 'NON_COMPLIANT' | 'UNDER_REVIEW';

// API Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: Date;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

// Form Types
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'number' | 'select' | 'textarea' | 'checkbox' | 'radio';
  required: boolean;
  validation?: ValidationRule[];
  options?: SelectOption[];
  placeholder?: string;
  defaultValue?: any;
}

export interface ValidationRule {
  type: 'required' | 'min' | 'max' | 'pattern' | 'email' | 'custom';
  value?: any;
  message: string;
}

export interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
}

// UI Component Types
export interface TableColumn<T> {
  key: keyof T;
  header: string;
  sortable?: boolean;
  filterable?: boolean;
  render?: (value: any, row: T) => React.ReactNode;
  width?: string;
}

export interface TableConfig<T> {
  columns: TableColumn<T>[];
  sortable: boolean;
  filterable: boolean;
  pagination: boolean;
  pageSize: number;
  pageSizeOptions: number[];
}

// Notification Types
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

// AI/ML Bill Related Types
export interface AIBillRequirement {
  id: string;
  title: string;
  description: string;
  category: AIBillCategory;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLIANT' | 'NON_COMPLIANT';
  deadline: Date;
  impact: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  requirements: string[];
  evidence: string[];
  assignedTo?: string;
  createdAt: Date;
  updatedAt: Date;
}

export type AIBillCategory = 
  | 'TRANSPARENCY' 
  | 'ACCOUNTABILITY' 
  | 'FAIRNESS' 
  | 'PRIVACY' 
  | 'SECURITY' 
  | 'HUMAN_OVERSIGHT' 
  | 'RISK_ASSESSMENT' 
  | 'DOCUMENTATION';

export interface AIBillCompliance {
  id: string;
  requirementId: string;
  requirement: AIBillRequirement;
  complianceScore: number;
  evidence: ComplianceEvidence[];
  auditTrail: AuditLog[];
  lastReview: Date;
  nextReview: Date;
  reviewer: string;
  status: 'COMPLIANT' | 'NON_COMPLIANT' | 'UNDER_REVIEW';
}

export interface ComplianceEvidence {
  id: string;
  type: 'DOCUMENT' | 'TEST_RESULT' | 'AUDIT_REPORT' | 'CERTIFICATION' | 'POLICY';
  title: string;
  description: string;
  fileUrl?: string;
  submittedBy: string;
  submittedAt: Date;
  verified: boolean;
  verifiedBy?: string;
  verifiedAt?: Date;
}

export interface AuditLog {
  id: string;
  action: string;
  description: string;
  performedBy: string;
  performedAt: Date;
  details?: Record<string, any>;
}

// Material Types for AI/ML Bill
export interface AIMaterial {
  id: string;
  name: string;
  type: MaterialType;
  description: string;
  content: string;
  tags: string[];
  category: AIBillCategory;
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';
  author: string;
  createdAt: Date;
  updatedAt: Date;
  version: string;
  attachments: MaterialAttachment[];
}

export type MaterialType = 
  | 'POLICY' 
  | 'PROCEDURE' 
  | 'GUIDELINE' 
  | 'TEMPLATE' 
  | 'CHECKLIST' 
  | 'TRAINING' 
  | 'ASSESSMENT' 
  | 'REPORT';

export interface MaterialAttachment {
  id: string;
  name: string;
  type: 'PDF' | 'DOC' | 'XLS' | 'PPT' | 'IMAGE' | 'VIDEO';
  url: string;
  size: number;
  uploadedAt: Date;
  uploadedBy: string;
} 