/**
 * Mock data for API fallbacks and development
 */

export const mockDashboardStats = {
  totalModels: 12,
  activeModels: 8,
  biasDetections: 23,
  complianceScore: 0.87,
  recentAlerts: [
    {
      id: 'alert-1',
      type: 'bias',
      severity: 'medium',
      message: 'Gender bias detected in HR model',
      timestamp: '2024-03-22T10:30:00Z'
    },
    {
      id: 'alert-2', 
      type: 'compliance',
      severity: 'low',
      message: 'Documentation update required',
      timestamp: '2024-03-22T09:15:00Z'
    }
  ],
  systemHealth: {
    status: 'healthy',
    uptime: '99.9%',
    lastCheck: '2024-03-22T11:00:00Z'
  }
};

export const mockModels = [
  {
    id: 'model-1',
    name: 'Credit Risk Assessment',
    description: 'ML model for evaluating credit risk in loan applications',
    type: 'classification',
    version: 'v2.1.0',
    status: 'active',
    accuracy: 0.94,
    bias_score: 0.12,
    fairness_score: 0.88,
    created_at: '2024-01-15T10:30:00Z',
    updated_at: '2024-03-20T14:45:00Z'
  },
  {
    id: 'model-2',
    name: 'HR Screening Model', 
    description: 'AI model for initial candidate screening and evaluation',
    type: 'ranking',
    version: 'v1.3.2',
    status: 'active',
    accuracy: 0.89,
    bias_score: 0.23,
    fairness_score: 0.77,
    created_at: '2024-02-01T09:15:00Z',
    updated_at: '2024-03-18T11:20:00Z'
  },
  {
    id: 'model-3',
    name: 'Healthcare Diagnosis Assistant',
    description: 'Deep learning model for medical diagnosis support',
    type: 'classification', 
    version: 'v3.0.1',
    status: 'active',
    accuracy: 0.96,
    bias_score: 0.08,
    fairness_score: 0.92,
    created_at: '2024-01-10T16:00:00Z',
    updated_at: '2024-03-22T13:30:00Z'
  }
];

export const mockBiasDetectionData = {
  overall_risk: 'medium',
  bias_tests: [
    {
      test_name: 'Gender Bias Test',
      bias_score: 0.23,
      is_biased: true,
      confidence: 0.87,
      category: 'gender'
    },
    {
      test_name: 'Racial Bias Test',
      bias_score: 0.15,
      is_biased: false,
      confidence: 0.92,
      category: 'race'
    },
    {
      test_name: 'Age Bias Test',
      bias_score: 0.31,
      is_biased: true,
      confidence: 0.78,
      category: 'age'
    }
  ],
  explainability_analysis: [
    {
      method: 'LIME',
      confidence: 0.85,
      insights: ['Feature importance analysis shows gender-related features have high impact'],
      visualizations: ['feature_importance.png']
    }
  ],
  recommendations: [
    'Review training data for gender balance',
    'Implement bias mitigation techniques',
    'Add fairness constraints to model training'
  ],
  compliance_status: {
    gdpr_compliant: true,
    ai_act_compliant: false,
    fairness_score: 0.72
  },
  evaluation_summary: {
    total_tests_run: 3,
    biased_tests: 2,
    bias_rate: 0.67
  }
};

export const mockReports = [
  {
    id: 'report-1',
    title: 'Monthly Bias Assessment Report',
    type: 'bias_assessment',
    status: 'completed',
    created_at: '2024-03-01T00:00:00Z',
    summary: 'Comprehensive bias analysis across all active models'
  },
  {
    id: 'report-2',
    title: 'Compliance Audit Report',
    type: 'compliance',
    status: 'completed',
    created_at: '2024-02-15T00:00:00Z',
    summary: 'GDPR and AI Act compliance assessment'
  },
  {
    id: 'report-3',
    title: 'Fairness Metrics Report',
    type: 'fairness',
    status: 'in_progress',
    created_at: '2024-03-20T00:00:00Z',
    summary: 'Detailed fairness analysis and recommendations'
  }
];

export const mockMonitoringMetrics = {
  system_health: 'healthy',
  active_models: 8,
  total_predictions: 15420,
  avg_response_time: 245,
  error_rate: 0.02,
  bias_alerts: 2,
  compliance_score: 0.89,
  uptime: '99.9%',
  cpu_usage: 0.45,
  memory_usage: 0.67,
  disk_usage: 0.23
};

export const mockBiasHealth = {
  status: 'healthy',
  active_detectors: 5,
  last_scan: '2024-03-22T10:30:00Z',
  bias_alerts: 2,
  overall_score: 0.85,
  recent_scans: [
    { model_id: 'model-1', score: 0.88, timestamp: '2024-03-22T10:30:00Z' },
    { model_id: 'model-2', score: 0.77, timestamp: '2024-03-22T09:15:00Z' },
    { model_id: 'model-3', score: 0.92, timestamp: '2024-03-22T08:45:00Z' }
  ]
};

export const mockSecurityHealth = {
  status: 'secure',
  vulnerabilities: 0,
  last_scan: '2024-03-22T09:15:00Z',
  security_score: 0.92,
  threat_level: 'low',
  active_protections: 7,
  recent_incidents: []
};

// Utility function to get mock data by endpoint
export const getMockDataForEndpoint = (endpoint: string): any => {
  const endpointMap: Record<string, any> = {
    '/api/v1/database/dashboard-stats': mockDashboardStats,
    '/api/v1/models': mockModels,
    '/api/v1/modern-bias/detection-results': mockBiasDetectionData,
    '/api/v1/reports': mockReports,
    '/api/v1/monitoring/metrics': mockMonitoringMetrics,
    '/api/v1/bias/health': mockBiasHealth,
    '/api/v1/security/health': mockSecurityHealth,
  };

  return endpointMap[endpoint] || null;
};