# Fairmind Project Structure

This document outlines the current structure of the Fairmind project, what each component does, the technologies used, and the current status.

## Project Overview

Fairmind is a platform for AI governance, providing tools for real-time bias monitoring, model explainability, and automated compliance reporting.

## Directory Structure

-   **`apps/`**: Contains the main applications.
    -   `ml-service/`: A Python-based service for all machine learning-related tasks, including bias detection and explainability.
    -   `web/`: The main web interface, built with Next.js.
-   **`backend/`**: Houses the backend services.
    -   `api/`: A NestJS API that connects the frontend to the ML service and the database.
-   **`apps/`**: Separate applications (backend, frontend, website).
    -   `ui/`: A shared library of UI components.
-   **`supabase/`**: Configuration for the Supabase backend-as-a-service, including database migrations and serverless functions.
-   **`docs/`**: Project documentation.
    -   `v2/`: The most current documentation for the new architecture.

## Completed Work

-   **UI/Frontend**: The user interface is largely complete, providing the necessary views for simulations, results, and reporting.
-   **Architecture**: The new v2 architecture has been defined, separating concerns between the frontend, backend, and ML service.

## Libraries and Technologies

-   **Frontend**: Next.js, React, TypeScript, Tailwind CSS
-   **Backend**: NestJS, TypeScript
-   **ML Service**: Python, Flask/FastAPI (TBD), SHAP, LIME, Fairlearn
-   **Database**: Supabase (PostgreSQL)
-   **Package Management**: Bun (JavaScript) + UV (Python)
