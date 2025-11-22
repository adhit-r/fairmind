# FairMind – Ethical AI Governance Platform

[![Backend Status](https://img.shields.io/badge/Backend-FastAPI-green)](https://api.fairmind.xyz)
[![Frontend Status](https://img.shields.io/badge/Frontend-Next.js-blue)](https://app-demo.fairmind.xyz)
[![Testing Coverage](https://img.shields.io/badge/Testing-100%25%20Coverage-brightgreen)](./FINAL_TESTING_SUMMARY.md)
[![Contributors](https://img.shields.io/github/contributors/adhit-r/fairmind)](https://github.com/adhit-r/fairmind/graphs/contributors)
[![Issues](https://img.shields.io/github/issues/adhit-r/fairmind/good%20first%20issue)](https://github.com/adhit-r/fairmind/issues?q=is%3Aissue+is%3Aopen+label%3A%22good%20first%20issue%22)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Stars](https://img.shields.io/github/stars/adhit-r/fairmind?style=social)](https://github.com/adhit-r/fairmind/stargazers)

---

## 📋 Table of Contents

1. [What is FairMind?](#what-is-fairmind)
2. [Key Features](#key-features)
3. [Architecture & Workflows](#architecture--workflows)
4. [Getting Started](#getting-started)
5. [Feature Matrix](#feature-matrix)
6. [API Reference](#api-reference)
7. [Frontend Overview](#frontend-overview)
8. [Technology Stack](#technology-stack)
9. [Project Statistics](#project-statistics)
10. [Documentation](#documentation)
11. [License](#license)

---

## 🤖 What is FairMind?

FairMind is a comprehensive **AI Governance & Bias Detection Platform** designed for the modern AI stack. It empowers organizations to:

*   **Detect Bias**: Analyze Classic ML, LLMs, and Multimodal systems for fairness issues.
*   **Remediate**: Automatically generate code to fix detected biases.
*   **Govern**: Generate AI BOMs (Bill of Materials) and Compliance Reports (GDPR, EU AI Act).
*   **Track**: Seamlessly log experiments to Weights & Biases and MLflow.

Built with a **premium neobrutalist UI**, FairMind makes complex ethical AI metrics accessible and actionable.

---

## ✨ Key Features

### 1. Advanced Bias Detection
*   **Classic ML**: Demographic Parity, Equalized Odds, Disparate Impact.
*   **LLMs**: WEAT, SEAT, Minimal Pairs testing.
*   **Multimodal**: Bias detection in Image, Audio, and Video models.

### 2. Automated Remediation
*   **Strategies**: Reweighting, Resampling, Threshold Optimization.
*   **Code Gen**: Get ready-to-run Python code to fix your model.

### 3. MLOps Integration 🚀 *New*
*   **Zero-Config Logging**: Automatically log bias tests to **Weights & Biases** and **MLflow**.
*   **Deep Linking**: Jump directly from FairMind results to your experiment tracking dashboard.
*   **Environment Toggles**: Enable/disable integrations via `.env`.

### 4. Compliance & Governance 🛡️ *New*
*   **AI BOM**: Generate standard Software Bill of Materials for your AI models.
*   **Compliance Reports**: Automated assessment against EU AI Act and GDPR.
*   **Risk Assessment**: High/Medium/Low risk categorization based on policy definitions.

---

## 🏗️ Architecture & Workflows

### System Architecture
FairMind uses a modern, decoupled architecture with a FastAPI backend and Next.js frontend, supported by robust services and storage.

![System Architecture](docs/images/fairmind_system_architecture.png)

### Bias Detection Pipeline
From upload to remediation, the pipeline is designed for automation and transparency.

![Bias Detection Pipeline](docs/images/bias_detection_pipeline.png)

### Compliance Workflow
Ensure your models meet regulatory standards with our automated governance flow.

![Compliance Workflow](docs/images/compliance_governance_flow.png)

---

## 🚀 Getting Started

### Prerequisites
*   **Python 3.9+** (Backend)
*   **Node.js 18+** (Frontend)
*   **UV** (Python package manager)
*   **Bun** (JS runtime)

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/adhit-r/fairmind.git
cd fairmind

# 2. Backend Setup
cd apps/backend
uv sync
cp .env.example .env  # Configure MLOps credentials here
uv run python -m uvicorn api.main:app --reload

# 3. Frontend Setup (New Terminal)
cd ../frontend-new
bun install
bun run dev
```

Visit **http://localhost:3000** to access the dashboard.

---

## 📊 Feature Matrix

| Feature Category | Traditional AI Platforms | FairMind (2025) |
|------------------|--------------------------|-----------------|
| **Bias Detection** | Tabular only | **LLM, Multimodal, Tabular** |
| **Remediation** | Manual | **Automated Code Gen** |
| **MLOps** | Hard-coded | **Plug-and-Play (W&B, MLflow)** |
| **Governance** | Manual Docs | **Automated AI BOMs & Reports** |
| **UI/UX** | Generic Admin | **Premium Neobrutal Design** |
| **Deployment** | Complex | **Docker / Railway / Netlify** |

---

## 🔌 API Reference

Full documentation available at [api.fairmind.xyz/docs](https://api.fairmind.xyz/docs).

| Scope | Endpoint | Method | Description |
|-------|----------|--------|-------------|
| **Bias** | `/api/v1/bias/detect` | POST | Run bias detection |
| **Remediation** | `/api/v1/bias/remediate` | POST | Generate fix strategies |
| **MLOps** | `/api/v1/mlops/status` | GET | Check integration status |
| **MLOps** | `/api/v1/mlops/log-test` | POST | Manually log experiments |
| **Compliance** | `/api/v1/compliance/report` | POST | Generate compliance report |
| **AI BOM** | `/api/v1/aibom/generate` | POST | Create AI Bill of Materials |

---

## 🖥️ Frontend Overview

| Page | Route | Features |
|------|-------|----------|
| **Dashboard** | `/dashboard` | System health, recent activity, quick actions |
| **Bias Detection** | `/bias` | Upload datasets, configure tests, view metrics |
| **Test Results** | `/tests/[id]` | Deep dive analysis, **W&B/MLflow links**, export JSON |
| **Remediation** | `/remediation` | Strategy selection, code generation |
| **Compliance** | `/compliance` | Policy management, report generation |
| **Settings** | `/settings` | **MLOps configuration**, profile management |

---

## 🛠️ Technology Stack

*   **Backend**: Python 3.9+, FastAPI, UV, scikit-learn, transformers, torch
*   **Frontend**: TypeScript, Next.js 14, Mantine v7, Tailwind CSS
*   **Storage**: Supabase (PostgreSQL), Local File System, Redis (Caching)
*   **Integrations**: Weights & Biases, MLflow, OpenAI (optional)
*   **DevOps**: Docker, GitHub Actions

---

## 📈 Project Statistics

| Metric | Value |
|--------|-------|
| **Backend Endpoints** | 50+ |
| **Test Coverage** | 100% |
| **Frontend Components** | 60+ |
| **Core Services** | 6 (Bias, Remediation, MLOps, Compliance, BOM, Storage) |
| **Supported Models** | Sklearn, PyTorch, HuggingFace, OpenAI |

---

## 📚 Documentation

*   **[Setup Guide](SETUP.md)** - Detailed installation instructions
*   **[MLOps Integration](apps/backend/services/MLOPS_README.md)** - W&B and MLflow setup
*   **[Compliance Guide](apps/backend/services/COMPLIANCE_REPORTING.md)** - Generating reports and BOMs
*   **[Contributing](docs/CONTRIBUTING.md)** - How to contribute to FairMind

---

## 📄 License

This project is licensed under the MIT License – see the `LICENSE` file for details.

---

*FairMind – Making AI fair, transparent, and accountable for everyone.*
