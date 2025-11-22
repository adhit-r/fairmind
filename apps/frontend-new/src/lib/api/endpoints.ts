/**
 * API Endpoints - Centralized endpoint definitions
 * All API endpoints should be defined here for consistency
 */

export const API_ENDPOINTS = {
  // Health
  health: '/health',
  healthReady: '/health/ready',
  healthLive: '/health/live',

  // Authentication
  auth: {
    login: '/api/v1/auth/login',
    refresh: '/api/v1/auth/refresh',
    logout: '/api/v1/auth/logout',
    me: '/api/v1/auth/me',
    apiKeys: '/api/v1/auth/api-keys',
    createApiKey: '/api/v1/auth/api-keys',
    deleteApiKey: (keyName: string) => `/api/v1/auth/api-keys/${keyName}`,
    users: '/api/v1/auth/users',
    health: '/api/v1/auth/health',
  },

  // Core
  core: {
    root: '/api/v1/core/',
    health: '/api/v1/core/health',
    models: '/api/v1/core/models',
    datasets: '/api/v1/core/datasets',
    recentActivity: '/api/v1/core/activity/recent',
    governanceMetrics: '/api/v1/core/governance/metrics',
    metricsSummary: '/api/v1/core/metrics/summary',
  },

  // Database
  database: {
    profiles: '/api/v1/database/profiles',
    biasAnalyses: '/api/v1/database/bias-analyses',
    auditLogs: '/api/v1/database/audit-logs',
    countryMetrics: '/api/v1/database/country-metrics',
    dashboardStats: '/api/v1/database/dashboard-stats',
    models: '/api/v1/database/models',
    reports: '/api/v1/database/reports',
    monitoringMetrics: '/api/v1/database/monitoring-metrics',
    health: '/api/v1/database/health',
  },

  // Bias Detection
  biasDetection: {
    detect: '/api/v1/bias-detection/detect',
    testWeat: '/api/v1/bias-detection/test/weat',
    testFairness: '/api/v1/bias-detection/test/fairness',
    testImage: '/api/v1/bias-detection/test/image',
    testText: '/api/v1/bias-detection/test/text',
    templates: '/api/v1/bias-detection/templates',
    libraries: '/api/v1/bias-detection/libraries',
    installLibrary: (libraryName: string) => `/api/v1/bias-detection/libraries/${libraryName}/install`,
    history: '/api/v1/bias-detection/history',
    export: '/api/v1/bias-detection/export',
    health: '/api/v1/bias-detection/health',
  },

  // Security
  security: {
    containerScan: '/api/v1/security/container/scan',
    llmTest: '/api/v1/security/llm/test',
    modelAnalyze: '/api/v1/security/model/analyze',
    generateReport: '/api/v1/security/report/generate',
    status: '/api/v1/security/status',
    scansHistory: '/api/v1/security/scans/history',
    scanDetails: (scanId: string) => `/api/v1/security/scans/${scanId}`,
    complianceFrameworks: '/api/v1/security/compliance/frameworks',
  },

  // Modern Bias Detection
  modernBiasDetection: {
    comprehensiveEvaluation: '/api/v1/modern-bias-detection/comprehensive-evaluation',
    multimodalDetection: '/api/v1/modern-bias-detection/multimodal-detection',
    explainabilityAnalysis: '/api/v1/modern-bias-detection/explainability-analysis',
    biasTests: '/api/v1/modern-bias-detection/bias-tests',
    configureBiasTest: '/api/v1/modern-bias-detection/bias-tests/configure',
    biasCategories: '/api/v1/modern-bias-detection/bias-categories',
    evaluationDatasets: '/api/v1/modern-bias-detection/evaluation-datasets',
    batchEvaluation: '/api/v1/modern-bias-detection/batch-evaluation',
    detectionResults: '/api/v1/modern-bias-detection/detection-results',
    evaluationHistory: '/api/v1/modern-bias-detection/evaluation-history',
    health: '/api/v1/modern-bias-detection/health',
  },

  // Advanced Bias Detection
  advancedBiasDetection: {
    root: '/api/v1/advanced-bias-detection/',
    causalAnalysis: '/api/v1/advanced-bias-detection/causal-analysis',
    counterfactualAnalysis: '/api/v1/advanced-bias-detection/counterfactual-analysis',
    intersectionalAnalysis: '/api/v1/advanced-bias-detection/intersectional-analysis',
    adversarialTesting: '/api/v1/advanced-bias-detection/adversarial-testing',
    temporalAnalysis: '/api/v1/advanced-bias-detection/temporal-analysis',
    contextualAnalysis: '/api/v1/advanced-bias-detection/contextual-analysis',
    biasTypes: '/api/v1/advanced-bias-detection/bias-types',
    analysisMethods: '/api/v1/advanced-bias-detection/analysis-methods',
    health: '/api/v1/advanced-bias-detection/health',
  },

  // Provenance
  provenance: {
    root: '/api/v1/provenance/',
    getProvenance: (modelId: string) => `/api/v1/provenance/${modelId}`,
  },

  // AI Governance
  aiGovernance: {
    policies: '/api/v1/ai-governance/policies',
    evaluatePolicy: (ruleId: string) => `/api/v1/ai-governance/policies/${ruleId}/evaluate`,
    complianceAssess: '/api/v1/ai-governance/compliance/assess',
    complianceFrameworks: '/api/v1/ai-governance/compliance/frameworks',
    frameworkControls: (framework: string) => `/api/v1/ai-governance/compliance/frameworks/${framework}/controls`,
    lifecycleProcess: '/api/v1/ai-governance/lifecycle/process',
    lifecycleSummary: (systemId: string) => `/api/v1/ai-governance/lifecycle/${systemId}/summary`,
    lifecycleChecks: '/api/v1/ai-governance/lifecycle/checks',
    evidenceCollect: '/api/v1/ai-governance/evidence/collect',
    evidenceUpload: '/api/v1/ai-governance/evidence/upload',
    evidence: (systemId: string) => `/api/v1/ai-governance/evidence/${systemId}`,
    evidenceCollections: '/api/v1/ai-governance/evidence/collections',
    generateReport: '/api/v1/ai-governance/reports/generate',
    exportReport: (reportId: string) => `/api/v1/ai-governance/reports/${reportId}/export`,
    assessRisks: '/api/v1/ai-governance/risks/assess',
    incidents: '/api/v1/ai-governance/incidents',
    updateIncidentStatus: (incidentId: string) => `/api/v1/ai-governance/incidents/${incidentId}/status`,
    riskDashboard: '/api/v1/ai-governance/dashboard/risk',
    registerModel: '/api/v1/ai-governance/ai-models/register',
    modelExplainability: (modelId: string) => `/api/v1/ai-governance/ai-models/${modelId}/explainability`,
    modelBiasDetection: (modelId: string) => `/api/v1/ai-governance/ai-models/${modelId}/bias-detection`,
    modelExplainabilitySummary: (modelId: string) => `/api/v1/ai-governance/ai-models/${modelId}/explainability/summary`,
    modelBiasSummary: (modelId: string) => `/api/v1/ai-governance/ai-models/${modelId}/bias/summary`,
    status: '/api/v1/ai-governance/status',
  },

  // AI BOM
  aiBOM: {
    documents: '/api/v1/ai-bom/documents',
    create: '/api/v1/ai-bom/create',
    document: (bomId: string) => `/api/v1/ai-bom/documents/${bomId}`,
    analyze: (bomId: string) => `/api/v1/ai-bom/documents/${bomId}/analyze`,
    metrics: (bomId: string) => `/api/v1/ai-bom/documents/${bomId}/metrics`,
    dependencyGraph: (bomId: string) => `/api/v1/ai-bom/documents/${bomId}/dependency-graph`,
    componentTypes: '/api/v1/ai-bom/components/types',
    riskLevels: '/api/v1/ai-bom/risk-levels',
    stats: '/api/v1/ai-bom/stats',
  },

  // Datasets
  datasets: {
    list: '/api/v1/datasets/',
    upload: '/api/v1/datasets/upload',
    get: (datasetId: string) => `/api/v1/datasets/${datasetId}`,
    delete: (datasetId: string) => `/api/v1/datasets/${datasetId}`,
  },

  // Bias Detection V2 (Production API)
  biasV2: {
    uploadDataset: '/api/v1/bias-v2/upload-dataset',
    detect: '/api/v1/bias-v2/detect',
    detectLLM: '/api/v1/bias-v2/detect-llm',
    getTest: (testId: string) => `/api/v1/bias-v2/test/${testId}`,
    datasets: '/api/v1/bias-v2/datasets',
    getDataset: (datasetId: string) => `/api/v1/bias-v2/datasets/${datasetId}`,
    deleteDataset: (datasetId: string) => `/api/v1/bias-v2/datasets/${datasetId}`,
    history: '/api/v1/bias-v2/history',
    statistics: '/api/v1/bias-v2/statistics',
  },

  // Monitoring
  monitoring: {
    metrics: '/api/v1/monitoring/metrics',
    alerts: '/api/v1/monitoring/alerts',
    logs: '/api/v1/monitoring/logs',
    health: '/api/v1/monitoring/health',
  },

  // Multimodal Bias Detection
  multimodalBiasDetection: {
    imageDetection: '/api/v1/multimodal-bias-detection/image-detection',
    audioDetection: '/api/v1/multimodal-bias-detection/audio-detection',
    videoDetection: '/api/v1/multimodal-bias-detection/video-detection',
    crossModalDetection: '/api/v1/multimodal-bias-detection/cross-modal-detection',
    comprehensiveAnalysis: '/api/v1/multimodal-bias-detection/comprehensive-analysis',
    availableModalities: '/api/v1/multimodal-bias-detection/available-modalities',
    biasDetectors: '/api/v1/multimodal-bias-detection/bias-detectors',
    batchAnalysis: '/api/v1/multimodal-bias-detection/batch-analysis',
    health: '/api/v1/multimodal-bias-detection/health',
  },

  // Modern Tools Integration
  modernToolsIntegration: {
    comprehensiveIntegration: '/api/v1/modern-tools-integration/comprehensive-integration',
    cometLLM: '/api/v1/modern-tools-integration/comet-llm',
    deepeval: '/api/v1/modern-tools-integration/deepeval',
    arizePhoenix: '/api/v1/modern-tools-integration/arize-phoenix',
    awsClarify: '/api/v1/modern-tools-integration/aws-clarify',
    confidentAI: '/api/v1/modern-tools-integration/confident-ai',
    transformerLens: '/api/v1/modern-tools-integration/transformer-lens',
    bertviz: '/api/v1/modern-tools-integration/bertviz',
    availableTools: '/api/v1/modern-tools-integration/available-tools',
    configureTool: (toolId: string) => `/api/v1/modern-tools-integration/configure-tool/${toolId}`,
    toolStatus: '/api/v1/modern-tools-integration/tool-status',
    batchIntegration: '/api/v1/modern-tools-integration/batch-integration',
    integrationHistory: '/api/v1/modern-tools-integration/integration-history',
    health: '/api/v1/modern-tools-integration/health',
  },

  // Comprehensive Bias Evaluation
  comprehensiveBiasEvaluation: {
    runComprehensive: '/api/v1/comprehensive-bias-evaluation/run-comprehensive',
    runPhase: '/api/v1/comprehensive-bias-evaluation/run-phase',
    evaluationHistory: '/api/v1/comprehensive-bias-evaluation/evaluation-history',
    evaluation: (evaluationId: string) => `/api/v1/comprehensive-bias-evaluation/evaluation/${evaluationId}`,
    availablePhases: '/api/v1/comprehensive-bias-evaluation/available-phases',
    riskLevels: '/api/v1/comprehensive-bias-evaluation/risk-levels',
    complianceFrameworks: '/api/v1/comprehensive-bias-evaluation/compliance-frameworks',
    configurePhase: '/api/v1/comprehensive-bias-evaluation/configure-phase',
    pipelineStatus: '/api/v1/comprehensive-bias-evaluation/pipeline-status',
    batchEvaluation: '/api/v1/comprehensive-bias-evaluation/batch-evaluation',
    evaluationMetrics: '/api/v1/comprehensive-bias-evaluation/evaluation-metrics',
    health: '/api/v1/comprehensive-bias-evaluation/health',
  },

  // Real-time Model Integration
  realtimeModelIntegration: {
    connect: '/api/v1/realtime-model-integration/connect',
    disconnect: '/api/v1/realtime-model-integration/disconnect',
    status: '/api/v1/realtime-model-integration/status',
    health: '/api/v1/realtime-model-integration/health',
  },

  // Benchmark Suite
  benchmarkSuite: {
    run: '/api/v1/benchmark-suite/run',
    results: '/api/v1/benchmark-suite/results',
    available: '/api/v1/benchmark-suite/available',
    health: '/api/v1/benchmark-suite/health',
  },

  // Fairness Governance
  fairnessGovernance: {
    computeClassicMLFairness: '/api/v1/fairness-governance/compute-classic-ml-fairness',
    health: '/api/v1/fairness-governance/health',
  },
} as const

