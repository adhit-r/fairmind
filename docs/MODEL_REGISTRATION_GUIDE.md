# Model Registration Guide - How Companies Use FairMind

## Overview

FairMind is an AI governance platform that helps companies monitor, evaluate, and ensure compliance of their AI models. Companies don't "upload" model weights - they **register** models for governance tracking.

## What Companies Actually Register

### 1. **Company-Trained Models** (Most Common)
Models that companies have trained themselves on their own data:
- **Example**: "ACME Bank Loan Approval Model" - trained on ACME's historical loan data
- **Why**: Companies need to monitor these for bias, especially in regulated industries (finance, healthcare, hiring)
- **What FairMind evaluates**: Model outputs, predictions, bias metrics, fairness scores

### 2. **Fine-Tuned Models**
Base models (like BERT, Llama-2, ResNet) that companies have fine-tuned:
- **Example**: "TechCorp Resume Screening" - BERT fine-tuned on TechCorp's hiring data
- **Why**: Fine-tuning can introduce bias, especially if training data is imbalanced
- **What FairMind evaluates**: Outputs from the fine-tuned model, comparing to base model behavior

### 3. **API-Based Models** (Governance Tracking)
Models accessed via APIs (GPT-4, Claude, etc.) that companies use:
- **Example**: "ACME Customer Support (GPT-4 API)" - GPT-4 API integration
- **Why**: Companies need to track bias in API responses for compliance
- **What FairMind evaluates**: API responses to test prompts, bias in outputs, compliance tracking

### 4. **Production Deployment Models**
Models currently deployed in production that require continuous monitoring:
- **Example**: "AutoDrive Object Detection" - deployed in self-driving vehicles
- **Why**: Production models need ongoing bias monitoring and compliance tracking
- **What FairMind evaluates**: Real-time outputs, bias trends, compliance status

## How FairMind Evaluates Models

FairMind **doesn't need model weights**. Instead, it evaluates:

### 1. **Model Outputs**
- Companies send test inputs to their models
- FairMind analyzes the outputs for bias
- Works for both self-hosted models and API-based models

### 2. **Bias Detection**
- **Traditional ML**: Statistical parity, equalized odds, demographic parity
- **LLMs**: WEAT tests, minimal pairs, allocational bias
- **Vision**: Representation bias, demographic disparities

### 3. **Compliance Tracking**
- GDPR, CCPA, AI Act compliance
- Fair Lending Act, EEOC guidelines
- Industry-specific regulations

### 4. **Continuous Monitoring**
- Track bias metrics over time
- Alert on bias drift
- Generate compliance reports

## Real-World Workflow

### Scenario 1: Company Trains a Model
1. **Train**: Company trains "Loan Approval Model" on their data
2. **Register**: Company registers model in FairMind
3. **Test**: Company sends test loan applications to model
4. **Evaluate**: FairMind analyzes outputs for bias (gender, race, age)
5. **Monitor**: FairMind continuously monitors production predictions
6. **Report**: FairMind generates compliance reports for regulators

### Scenario 2: Company Uses GPT-4 API
1. **Integrate**: Company integrates GPT-4 API for customer support
2. **Register**: Company registers "GPT-4 Customer Support" in FairMind
3. **Test**: Company sends test customer queries to GPT-4
4. **Evaluate**: FairMind analyzes GPT-4 responses for bias
5. **Track**: FairMind tracks API usage and bias trends
6. **Comply**: FairMind ensures compliance with GDPR, CCPA

### Scenario 3: Company Fine-Tunes Llama-2
1. **Fine-tune**: Company fine-tunes Llama-2 on their codebase
2. **Register**: Company registers "Code Assistant (Fine-tuned Llama-2)"
3. **Test**: Company sends test code prompts
4. **Evaluate**: FairMind compares fine-tuned vs base model for bias
5. **Deploy**: Company deploys to production
6. **Monitor**: FairMind monitors production usage for bias

## Key Points

✅ **Companies register models they use** - not necessarily models they own
✅ **FairMind evaluates outputs** - doesn't need model weights
✅ **Works with APIs** - can track GPT-4, Claude, etc. via API calls
✅ **Continuous monitoring** - tracks bias over time in production
✅ **Compliance focused** - ensures regulatory compliance

## Example: ACME Bank Loan Model

**What ACME registers:**
- Model name: "ACME Bank Loan Approval Model"
- Model type: Classification
- Training data: 500K loan applications
- Deployment: Production (handles 10K applications/day)

**What FairMind does:**
1. ACME sends test loan applications (with protected attributes)
2. FairMind analyzes approval rates by demographic
3. FairMind detects if model discriminates (e.g., lower approval for certain groups)
4. FairMind generates compliance report for Fair Lending Act
5. FairMind monitors production predictions continuously
6. FairMind alerts if bias increases over time

**Result**: ACME can prove to regulators that their model is fair and compliant.

