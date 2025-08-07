# Plan and Next Steps

This document outlines the development plan for Fairmind. It will be updated after each milestone is completed.

## Current Focus: ML Service Implementation

The immediate priority is to build out the core functionality of the ML service.

### Next Steps

1.  **Implement Core ML Algorithms**:
    -   Integrate fairness metrics algorithms (Demographic Parity, Equalized Odds).
    -   Add explainability methods (SHAP, LIME).
2.  **Develop the ML Service API**:
    -   Create API endpoints in the Python service to expose the ML models.
3.  **Backend API Development**:
    -   Build the NestJS API to act as a bridge between the `web` app and the `ml-service`.
4.  **Supabase Integration**:
    -   Connect the backend to Supabase for user authentication and data storage.
    -   Store ML analysis results and generated reports.

## Future Milestones

-   **Real-time Bias Monitoring**: Implement real-time monitoring of model predictions.
-   **Automated Compliance Reports**: Generate NIST AI RMF and model card reports.
-   **Multi-model Comparison**: Build features for benchmarking models against each other.
