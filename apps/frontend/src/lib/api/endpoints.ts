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
    // The public read-only demo (off unless the backend sets DEMO_USER_EMAIL).
    demo: '/api/v1/auth/demo',
    register: '/api/v1/auth/register',
    // Without an invitation, an account starts as an access request a platform admin approves.
    requestAccess: '/api/v1/register',
    refresh: '/api/v1/auth/refresh',
    logout: '/api/v1/auth/logout',
    me: '/api/v1/auth/me',
    requestPasswordReset: '/api/v1/auth/password-reset/request',
    resetPassword: '/api/v1/auth/password-reset',
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
    health: '/api/v1/database/health',
  },

  // Bias Detection
  biasDetection: {
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
    policies: (orgId: string) => `/api/v1/ai-governance/organizations/${orgId}/policies`,
    complianceFrameworks: '/api/v1/ai-governance/compliance/frameworks',
    lifecycleSummary: (systemId: string) => `/api/v1/ai-governance/lifecycle/${systemId}/summary`,
    evidenceCollectV2: '/api/v1/ai-governance/evidence/collect-v2',
    evidenceV2: (systemId: string) => `/api/v1/ai-governance/evidence-v2/${systemId}`,
    evidenceSummary: (systemId: string) => `/api/v1/ai-governance/evidence/${systemId}/summary`,
    evidenceItem: (evidenceId: string) => `/api/v1/ai-governance/evidence-item/${evidenceId}`,
    evidenceItemLinks: (evidenceId: string) => `/api/v1/ai-governance/evidence-item/${evidenceId}/links`,
    evidenceItemLink: (evidenceId: string, linkId: string) => `/api/v1/ai-governance/evidence-item/${evidenceId}/links/${linkId}`,
    environmentalImpact: (orgId: string, systemId: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/systems/${systemId}/environmental-impact`,
    remediation: '/api/v1/ai-governance/remediation',
    updateRemediation: (taskId: string) => `/api/v1/ai-governance/remediation/${taskId}`,
    approvalRequests: '/api/v1/ai-governance/approval-requests',
    approvalRequest: (requestId: string) => `/api/v1/ai-governance/approval-requests/${requestId}`,
    approvalDecision: (requestId: string) => `/api/v1/ai-governance/approval-requests/${requestId}/decision`,
    systemApproval: (systemId: string) => `/api/v1/ai-governance/approval/system/${systemId}`,
    systemApprovalRequest: (systemId: string) => `/api/v1/ai-governance/approval/system/${systemId}/request`,
    workspaces: '/api/v1/ai-governance/workspaces',
    systems: '/api/v1/ai-governance/systems',
    system: (systemId: string) => `/api/v1/ai-governance/systems/${systemId}`,
    applicabilitySuggest: '/api/v1/ai-governance/applicability/suggest',
    systemApplicability: (systemId: string) => `/api/v1/ai-governance/systems/${systemId}/applicability`,
    systemApplicabilityAcceptOverride: (systemId: string) => `/api/v1/ai-governance/systems/${systemId}/applicability/accept-override`,
    generateReport: '/api/v1/ai-governance/reports/generate',
    listReports: '/api/v1/ai-governance/reports',
    exportReport: (id: string, format: 'pdf' | 'docx') => `/api/v1/reports/snapshots/${encodeURIComponent(id)}/${format}`,
    assessRisks: '/api/v1/ai-governance/risks/assess',
    riskDashboard: '/api/v1/ai-governance/dashboard/risk',
    status: '/api/v1/ai-governance/status',
    // Model Inventory
    aiSystems: '/api/v1/ai-governance/systems',
    aiSystem: (systemId: string) => `/api/v1/ai-governance/systems/${systemId}`,
    aiSystemRisks: (systemId: string) => `/api/v1/ai-governance/dashboard/risk?system_id=${systemId}`,
    aiSystemApprovals: (systemId: string) => `/api/v1/ai-governance/systems/${systemId}/approvals`,
    frameworkAssignments: (orgId: string, systemId: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/systems/${systemId}/framework-assignments`,
    frameworks: (orgId: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/frameworks`,
    importFramework: (orgId: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/frameworks/import`,
    frameworkVersions: (orgId: string, frameworkKey: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/frameworks/${frameworkKey}/versions`,
    frameworkVersionControls: (orgId: string, versionId: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/framework-versions/${versionId}/controls`,
    assignmentControls: (orgId: string, assignmentId: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/framework-assignments/${assignmentId}/controls`,
    assignmentReadiness: (orgId: string, assignmentId: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/framework-assignments/${assignmentId}/readiness`,
    controlAssessment: (orgId: string, assessmentId: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/control-assessments/${assessmentId}`,
    evidenceRuns: (orgId: string, systemId: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/systems/${systemId}/evidence-runs`,
    evaluationPlans: (orgId: string, systemId: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/systems/${systemId}/evaluation-plans`,
    evaluationPlanActivation: (orgId: string, systemId: string, planId: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/systems/${systemId}/evaluation-plans/${planId}/activate`,
    evaluationPlanPreflight: (orgId: string, systemId: string, planId: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/systems/${systemId}/evaluation-plans/${planId}/preflight`,
    evaluationPlanRuns: (orgId: string, systemId: string, planId: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/systems/${systemId}/evaluation-plans/${planId}/runs`,
    evaluationRuns: (orgId: string, systemId: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/systems/${systemId}/evaluation-runs`,
    evaluationRun: (orgId: string, systemId: string, runId: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/systems/${systemId}/evaluation-runs/${runId}`,
    evaluationRunPassportLink: (orgId: string, systemId: string, runId: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/systems/${systemId}/evaluation-runs/${runId}/evidence-passport-link`,
    // The current GET workbench routes derive workspace from the server-owned
    // system binding. The client still keys and validates every response by
    // organization, workspace, and system before rendering it.
    evaluationV2Plans: (orgId: string, systemId: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/systems/${systemId}/evaluation-v2/plans`,
    evaluationV2Plan: (orgId: string, systemId: string, planId: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/systems/${systemId}/evaluation-v2/plans/${planId}`,
    evaluationV2Runs: (orgId: string, systemId: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/systems/${systemId}/evaluation-v2/runs`,
    evaluationV2Run: (orgId: string, systemId: string, runId: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/systems/${systemId}/evaluation-v2/runs/${runId}`,
    evaluatorCatalogRegistrations: (orgId: string, { limit, offset }: { limit: number; offset: number }) =>
      `/api/v1/ai-governance/organizations/${orgId}/evaluation-v2/evaluator-catalog/registrations?limit=${limit}&offset=${offset}`,
    evidenceMappings: (orgId: string, evidenceId: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/evidence/${evidenceId}/control-mappings`,
    reviewEvidenceMapping: (orgId: string, mappingId: string) =>
      `/api/v1/ai-governance/organizations/${orgId}/evidence-mappings/${mappingId}/review`,
    estateGates: '/api/v1/ai-governance/estate/gates',
    frameworkSystems: (frameworkKey: string) => `/api/v1/ai-governance/frameworks/${encodeURIComponent(frameworkKey)}/systems`,
  },

  // Datasets
  datasets: {
    list: '/api/v1/core/datasets',
    upload: '/api/v1/core/datasets',
  },

  // Monitoring
  monitoring: {
    metrics: '/api/v1/monitoring/metrics',
    alerts: '/api/v1/monitoring/alerts',
    logs: '/api/v1/monitoring/logs',
    health: '/api/v1/monitoring/health',
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

  // Model Performance Benchmarking
  modelPerformanceBenchmarking: {
    benchmarkRuns: '/api/v1/model-performance-benchmarking/benchmark-runs',
    runBenchmark: '/api/v1/model-performance-benchmarking/run-benchmark',
  },
  // MLOps Integration
  mlops: {
    status: '/api/v1/mlops/status',
    runUrl: (provider: string, runId: string) => `/api/v1/mlops/run-url/${provider}/${runId}`,
  },
  // Agentic packs
  packs: {
    catalogue: '/api/v1/packs/catalogue',
    list: '/api/v1/packs',
    install: (packId: string) => `/api/v1/packs/${encodeURIComponent(packId)}/install`,
    detail: (packId: string) => `/api/v1/packs/library/${encodeURIComponent(packId)}`,
    bundles: '/api/v1/packs/bundles',
    installBundle: (bundleId: string) => `/api/v1/packs/bundles/${encodeURIComponent(bundleId)}/install`,
    journeys: '/api/v1/packs/journeys',
    controls: '/api/v1/packs/controls',
    journey: (frameworkKey: string) => `/api/v1/packs/journeys/${encodeURIComponent(frameworkKey)}`,
    installFramework: (frameworkKey: string) => `/api/v1/packs/journeys/${encodeURIComponent(frameworkKey)}/install`,
    evaluations: '/api/v1/packs/evaluations',
    evaluation: (evaluationId: string) => `/api/v1/packs/evaluations/${encodeURIComponent(evaluationId)}`,
    evaluationEngine: (evaluationId: string) => `/api/v1/packs/evaluations/${encodeURIComponent(evaluationId)}/engine`,
    evaluationRuns: (evaluationId: string) => `/api/v1/packs/evaluations/${encodeURIComponent(evaluationId)}/runs`,
    evaluationRun: (runId: string) => `/api/v1/packs/evaluation-runs/${runId}`,
    evaluationJob: (jobId: string) => `/api/v1/packs/evaluation-jobs/${jobId}`,
    systemTarget: (systemId: string) => `/api/v1/packs/ai-systems/${systemId}/target`,
    systemTargetTest: (systemId: string) => `/api/v1/packs/ai-systems/${systemId}/target/test`,
    workflow: (workflowId: string) => `/api/v1/packs/workflows/${workflowId}`,
    startRun: (workflowId: string) => `/api/v1/packs/workflows/${workflowId}/runs`,
    draft: (workflowId: string) => `/api/v1/packs/workflows/${workflowId}/draft`,
    publishDraft: (workflowId: string) => `/api/v1/packs/workflows/${workflowId}/draft/publish`,
    runs: '/api/v1/packs/runs',
    run: (runId: string) => `/api/v1/packs/runs/${runId}`,
    stepOutput: (runId: string, stepId: string) => `/api/v1/packs/runs/${runId}/steps/${stepId}/output`,
    decision: (runId: string) => `/api/v1/packs/runs/${runId}/decision`,
    agentStep: (runId: string, stepId: string) => `/api/v1/packs/runs/${runId}/steps/${stepId}/agent`,
    ask: '/api/v1/packs/ask',
    aiProviders: '/api/v1/packs/ai-providers',
    aiProvider: '/api/v1/packs/ai-provider',
    aiProviderTest: '/api/v1/packs/ai-provider/test',
    platformConnections: '/api/v1/packs/platform-connections',
    platformConnection: (platform: string) => `/api/v1/packs/platform-connections/${encodeURIComponent(platform)}`,
    platformConnectionTest: (platform: string) => `/api/v1/packs/platform-connections/${encodeURIComponent(platform)}/test`,
  },

  // Organizations (Multi-org support)
  organizations: {
    list: '/api/v1/organizations',
    get: (orgId: string) => `/api/v1/organizations/${orgId}`,
    create: '/api/v1/organizations',
    update: (orgId: string) => `/api/v1/organizations/${orgId}`,
    members: (orgId: string) => `/api/v1/organizations/${orgId}/members`,
    inviteMembers: (orgId: string) => `/api/v1/organizations/${orgId}/members/invite`,
  },

  // Invitations
  invitations: {
    getDetails: (token: string) => `/api/v1/organizations/invitations/${encodeURIComponent(token)}`,
    accept: (token: string) => `/api/v1/organizations/invitations/${encodeURIComponent(token)}/accept`,
  },
} as const
