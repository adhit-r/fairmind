/**
 * Fairmind AI Governance Client
 * 
 * Client for communicating with the ML service for AI governance features:
 * - Bias detection and fairness analysis
 * - Model explainability (SHAP/LIME)
 * - NIST compliance scoring
 * - Real-time monitoring and drift detection
 */

// Types for AI Governance
export interface ModelPrediction {
  prediction: number;
  confidence: number;
  features: Record<string, unknown>;
  protected_attributes: Record<string, unknown>;
  timestamp: string;
}

export interface FairnessMetrics {
  demographic_parity: number;
  equalized_odds: number;
  equal_opportunity: number;
  disparate_impact: number;
  statistical_parity_difference: number;
}

export interface BiasAnalysisRequest {
  model_id: string;
  predictions: ModelPrediction[];
  reference_group: Record<string, unknown>;
}

export interface BiasAnalysisResponse {
  model_id: string;
  fairness_metrics: FairnessMetrics;
  bias_detected: boolean;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  recommendations: string[];
  affected_groups: string[];
}

export interface ExplanationResponse {
  model_id: string;
  explanation_type: 'SHAP' | 'LIME';
  feature_importance: Record<string, number>;
  local_explanation: {
    prediction: number;
    base_value: number;
    contributions: Record<string, number>;
  };
}

export interface NISTComplianceResponse {
  model_id: string;
  overall_score: number;
  framework_scores: {
    GOVERN: number;
    MAP: number;
    MEASURE: number;
    MANAGE: number;
  };
  compliance_status: 'COMPLIANT' | 'NON_COMPLIANT' | 'NEEDS_REVIEW';
  areas_for_improvement: string[];
}

export interface DriftDetectionResponse {
  model_id: string;
  drift_detected: boolean;
  drift_type: 'DATA_DRIFT' | 'CONCEPT_DRIFT' | 'BOTH';
  drift_score: number;
  affected_features: string[];
  recommendation: string;
}

export class AIGovernanceClient {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  /**
   * Analyze model predictions for bias across protected groups
   */
  async analyzeBias(request: BiasAnalysisRequest): Promise<BiasAnalysisResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/analyze/bias`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Bias analysis failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error analyzing bias:', error);
      throw error;
    }
  }

  /**
   * Generate SHAP/LIME explanations for model predictions
   */
  async explainModel(modelId: string, predictionData: Record<string, unknown>): Promise<ExplanationResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/explain/model`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_id: modelId,
          prediction_data: predictionData,
        }),
      });

      if (!response.ok) {
        throw new Error(`Model explanation failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error explaining model:', error);
      throw error;
    }
  }

  /**
   * Calculate NIST AI RMF compliance score
   */
  async calculateNISTCompliance(modelId: string, assessmentData: Record<string, unknown>): Promise<NISTComplianceResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/compliance/nist-score`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_id: modelId,
          assessment_data: assessmentData,
        }),
      });

      if (!response.ok) {
        throw new Error(`NIST compliance calculation failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error calculating NIST compliance:', error);
      throw error;
    }
  }

  /**
   * Detect data/concept drift in model inputs and outputs
   */
  async detectDrift(
    modelId: string, 
    currentData: Record<string, unknown>[], 
    referenceData: Record<string, unknown>[]
  ): Promise<DriftDetectionResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/monitor/drift`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_id: modelId,
          current_data: currentData,
          reference_data: referenceData,
        }),
      });

      if (!response.ok) {
        throw new Error(`Drift detection failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error detecting drift:', error);
      throw error;
    }
  }

  /**
   * Health check for the ML service
   */
  async healthCheck(): Promise<{ status: string; service: string; version: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      
      if (!response.ok) {
        throw new Error(`Health check failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error checking ML service health:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const aiGovernanceClient = new AIGovernanceClient();
