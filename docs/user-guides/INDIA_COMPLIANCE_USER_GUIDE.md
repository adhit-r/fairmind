# India Compliance Features - User Guide

This guide explains how to use FairMind's India-specific compliance features to ensure your AI systems comply with Indian regulations.

**Requirements**: 1.1, 1.2, 1.3, 2.1, 3.1, 6.1, 8.1

## Table of Contents

1. [Getting Started](#getting-started)
2. [DPDP Act Compliance Checking](#dpdp-act-compliance-checking)
3. [NITI Aayog Principles Evaluation](#niti-aayog-principles-evaluation)
4. [Bias Detection for Indian Demographics](#bias-detection-for-indian-demographics)
5. [AI-Powered Automation Features](#ai-powered-automation-features)
6. [Dashboard and Reporting](#dashboard-and-reporting)
7. [Best Practices](#best-practices)

---

## Getting Started

### Accessing India Compliance Features

1. Log in to FairMind dashboard
2. Navigate to **Compliance** → **India Compliance**
3. You'll see the India Compliance Dashboard

### Dashboard Overview

The India Compliance Dashboard shows:
- **Overall Compliance Score**: Aggregate score across all frameworks
- **Framework Status**: Individual scores for each framework
- **Recent Gaps**: Latest identified compliance gaps
- **Evidence Count**: Number of evidence items collected
- **Trends**: Compliance trend over time

### Initial Setup

1. **Register Your System**:
   - Go to **Systems** → **Add System**
   - Enter system name and description
   - Select data types processed
   - Click **Create**

2. **Select Frameworks**:
   - Go to **Compliance** → **India Compliance**
   - Click **Select Frameworks**
   - Choose applicable frameworks:
     - DPDP Act 2023 (required for personal data processing)
     - NITI Aayog Principles (recommended for all AI systems)
     - MeitY Guidelines (for government AI systems)
     - Digital India Act (for emerging compliance)

3. **Configure Integrations** (Optional):
   - Go to **Settings** → **Integrations**
   - Connect compliance tools (OneTrust, Securiti.ai, Sprinto)
   - Enable automatic evidence collection

---

## DPDP Act Compliance Checking

The Digital Personal Data Protection (DPDP) Act 2023 is India's primary data protection law. FairMind helps you verify compliance with key requirements.

**Requirements**: 1.1, 1.2, 1.3, 2.1

### What is DPDP Act?

The DPDP Act 2023 regulates how organizations collect, process, and store personal data in India. Key areas include:

- **Consent Management**: Obtaining valid consent before processing
- **Data Localization**: Storing sensitive personal data in India
- **Cross-Border Transfer**: Restrictions on transferring data outside India
- **Data Principal Rights**: Right to access, correct, and erase data
- **Grievance Redressal**: Mechanism for handling complaints

### Running DPDP Compliance Check

1. **Navigate to Compliance Check**:
   - Go to **Compliance** → **India Compliance** → **Check Compliance**

2. **Select System and Framework**:
   - Choose your system from dropdown
   - Select **DPDP Act 2023** framework
   - Click **Start Check**

3. **Review Results**:
   - Overall compliance score (0-100)
   - Status: Compliant, Partial, Non-Compliant
   - Breakdown of requirements met vs. failed
   - Evidence collected count

4. **Examine Gaps**:
   - Click on each gap to see details
   - Review failed checks
   - Read remediation recommendations
   - Check legal citations

### DPDP Act Requirements Checked

| Requirement | Description | Status |
|-------------|-------------|--------|
| Consent Management | Valid consent with withdrawal mechanism | ✓ |
| Data Localization | Sensitive data stored in India | ✓ |
| Cross-Border Transfer | Approved country compliance | ✓ |
| Data Principal Rights | Access, correction, erasure mechanisms | ✓ |
| Grievance Redressal | Complaint handling system | ✓ |
| Data Retention | Deletion after purpose fulfilled | ✓ |
| Security Controls | Encryption and access controls | ✓ |
| Data Breach Notification | Notification procedures | ✓ |
| Data Protection Officer | Appointment for significant fiduciaries | ✓ |

### Example: Addressing Data Localization Gap

**Gap Identified**: "Sensitive personal data stored in AWS Singapore"

**Remediation Steps**:
1. Identify sensitive data types (name, email, phone, address)
2. Migrate to AWS Mumbai region (ap-south-1)
3. Update data residency policy
4. Verify encryption in transit and at rest
5. Document data localization controls
6. Re-run compliance check

**Legal Reference**: DPDP Act 2023, Section 16

---

## NITI Aayog Principles Evaluation

NITI Aayog's Responsible AI Principles provide ethical guidelines for AI development in India.

**Requirements**: 1.1, 1.2, 1.3, 3.1

### What are NITI Aayog Principles?

NITI Aayog (National Institution for Transforming India) published 12 principles for responsible AI:

1. **Safety and Reliability**: AI systems must be robust and fail safely
2. **Equality**: AI should not discriminate based on protected characteristics
3. **Inclusivity**: AI should be accessible to diverse populations
4. **Privacy and Security**: Data protection and security safeguards
5. **Transparency**: Clear explanation of AI decisions
6. **Accountability**: Human oversight and responsibility
7. **Fairness**: Equitable treatment across demographics
8. **Explainability**: Interpretable AI decisions
9. **Auditability**: Ability to audit AI systems
10. **Contestability**: Mechanism to challenge AI decisions
11. **Sustainability**: Environmentally responsible AI
12. **Governance**: Proper oversight and control

### Running NITI Aayog Evaluation

1. **Navigate to Principles Evaluation**:
   - Go to **Compliance** → **India Compliance** → **Check Compliance**

2. **Select Framework**:
   - Choose your system
   - Select **NITI Aayog Principles**
   - Click **Start Evaluation**

3. **Review Principle-by-Principle Results**:
   - Each principle gets a score
   - See which principles are met/failed
   - Review evidence for each principle

4. **Address Gaps**:
   - Click on failed principles
   - Review specific checks that failed
   - Implement recommended improvements

### Example: Addressing Equality Principle Gap

**Gap Identified**: "Model shows bias against SC/ST categories"

**Remediation Steps**:
1. Run bias detection for caste categories
2. Analyze training data representation
3. Rebalance training data for underrepresented groups
4. Apply algorithmic debiasing techniques
5. Re-test model fairness
6. Document fairness improvements
7. Re-run evaluation

**Legal Reference**: NITI Aayog Responsible AI Principles, Principle 2

---

## Bias Detection for Indian Demographics

FairMind provides specialized bias detection for Indian demographic groups and social structures.

**Requirements**: 6.1, 6.2, 6.3, 6.4, 6.5, 6.7

### Supported Demographic Categories

FairMind tests for bias across:

| Category | Groups | Examples |
|----------|--------|----------|
| **Caste** | SC, ST, OBC, General | Scheduled Castes, Scheduled Tribes, Other Backward Classes |
| **Religion** | Hindu, Muslim, Christian, Sikh, Buddhist, Jain, Others | Major religions in India |
| **Language** | Hindi, English, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Odia, Punjabi, Urdu | Scheduled languages |
| **Region** | North, South, East, West, Northeast | Geographic regions |
| **Gender** | Male, Female, Third Gender | Gender categories |
| **Intersectional** | Combinations of above | e.g., SC + Female + Hindi |

### Running Bias Detection

1. **Navigate to Bias Detection**:
   - Go to **Compliance** → **India Compliance** → **Bias Detection**

2. **Select Model and Test Data**:
   - Choose system and model
   - Upload test dataset (CSV format)
   - Select demographic categories to test
   - Click **Start Detection**

3. **Review Results**:
   - Overall bias detected: Yes/No
   - Bias severity: Critical, High, Medium, Low
   - Affected demographic groups
   - Fairness metrics for each group

4. **Examine Fairness Metrics**:
   - **Demographic Parity**: Equal positive outcome rates
   - **Equal Opportunity**: Equal true positive rates
   - **Equalized Odds**: Equal false positive and true positive rates
   - **Disparate Impact**: Ratio of outcomes between groups

### Example: Caste-Based Bias Detection

**Test Setup**:
- Model: Loan approval system
- Test data: 1000 loan applications
- Categories: SC, ST, OBC, General

**Results**:
```
Caste Bias Detected: YES (Severity: HIGH)

Demographic Parity:
- SC: 45% approval rate
- ST: 48% approval rate
- OBC: 62% approval rate
- General: 75% approval rate

Disparate Impact: 1.67 (SC vs General)
Recommendation: Rebalance training data, apply fairness constraints
```

**Remediation**:
1. Analyze why SC/ST have lower approval rates
2. Check for proxy variables (income, education)
3. Rebalance training data
4. Apply fairness-aware algorithms
5. Re-test and verify improvement

### Interpreting Fairness Metrics

**Demographic Parity** (DP):
- Ideal: All groups have equal positive outcome rates
- Interpretation: If DP = 0.6, minority group has 60% of majority group's positive rate
- Use when: Equal representation is important

**Equal Opportunity** (EO):
- Ideal: All groups have equal true positive rates
- Interpretation: If EO = 0.8, minority group has 80% of majority group's true positive rate
- Use when: Equal access to benefits is important

**Equalized Odds** (EqOdds):
- Ideal: All groups have equal true positive and false positive rates
- Interpretation: Most stringent fairness metric
- Use when: Both false positives and false negatives matter

---

## AI-Powered Automation Features

FairMind provides AI-powered features to automate compliance tasks using large language models.

**Requirements**: 8.1, 8.2, 8.3, 8.5

### 1. AI Gap Analysis

Automatically identify compliance gaps using LLM analysis.

**How It Works**:
1. Analyzes system documentation
2. Reviews current controls
3. Identifies potential gaps
4. Provides confidence scores

**Using AI Gap Analysis**:

1. Go to **Compliance** → **India Compliance** → **AI Gap Analysis**
2. Select system and framework
3. Upload system documentation (optional)
4. Click **Analyze**
5. Review identified gaps with confidence scores
6. Click on each gap for details and recommendations

**Example Output**:
```
Gap 1: Consent Management (Confidence: 95%)
- Issue: No explicit consent mechanism found
- Severity: High
- Legal Reference: DPDP Act Section 6
- Recommendation: Implement consent collection form

Gap 2: Data Retention Policy (Confidence: 87%)
- Issue: No documented data retention schedule
- Severity: Medium
- Legal Reference: DPDP Act Section 10
- Recommendation: Create data retention policy
```

### 2. Remediation Plan Generation

Generate step-by-step remediation plans with effort estimates.

**Using Remediation Planning**:

1. Go to **Compliance** → **India Compliance** → **Remediation Plan**
2. Select identified gaps
3. Set priority level (Critical, High, Medium, Low)
4. Set target timeline (weeks)
5. Click **Generate Plan**
6. Review prioritized steps with effort estimates

**Example Plan**:
```
Total Gaps: 3
Total Effort: 120 hours
Timeline: 8 weeks

Step 1: Implement Consent Management (80 hours)
- Responsible: Backend Team
- Dependencies: None
- Success Criteria: Consent records stored with timestamp

Step 2: Create Data Retention Policy (20 hours)
- Responsible: Legal Team
- Dependencies: Step 1
- Success Criteria: Policy documented and approved

Step 3: Implement Data Deletion (20 hours)
- Responsible: Backend Team
- Dependencies: Step 2
- Success Criteria: Automated deletion working
```

### 3. Policy Generation

Auto-generate DPDP-compliant policy documents.

**Using Policy Generation**:

1. Go to **Compliance** → **India Compliance** → **Generate Policy**
2. Select policy type:
   - Privacy Policy
   - Consent Form
   - Data Processing Agreement
   - Data Retention Policy
   - Grievance Redressal Procedure
3. Enter system details:
   - System name
   - System description
   - Data types processed
4. Click **Generate**
5. Review generated policy
6. Download or edit as needed

**Generated Policy Includes**:
- Legal compliance clauses
- Indian regulatory citations
- Data subject rights
- Grievance procedures
- Contact information
- Signature blocks

### 4. Compliance Q&A

Ask compliance questions and get answers with legal citations.

**Using Compliance Q&A**:

1. Go to **Compliance** → **India Compliance** → **Ask Question**
2. Type your compliance question
3. Optionally select framework context
4. Click **Ask**
5. Review answer with legal citations
6. Click citations to view source documents

**Example Questions**:
- "What are the requirements for cross-border data transfer?"
- "How long can we retain personal data?"
- "What is the process for handling data subject requests?"
- "What are the penalties for DPDP Act violations?"

**Example Answer**:
```
Question: What are the requirements for cross-border data transfer?

Answer: Under DPDP Act Section 16, cross-border transfer of personal data 
is permitted only to countries that provide adequate data protection. 
The Data Protection Board maintains a list of approved countries. 
Organizations must ensure data transfer agreements are in place.

Legal Citations:
- DPDP Act 2023, Section 16
- DPDP Act 2023, Section 17
- DPDP Rules 2024, Rule 8

Confidence: 95%
```

### 5. Risk Prediction

Predict compliance risk based on planned system changes.

**Using Risk Prediction**:

1. Go to **Compliance** → **India Compliance** → **Predict Risk**
2. Describe planned changes:
   - New data types
   - New storage locations
   - New third parties
   - New processing purposes
3. Select framework
4. Click **Predict**
5. Review risk level and recommendations

**Example Prediction**:
```
Planned Change: Store biometric data in AWS Singapore

Predicted Risk Level: HIGH (Score: 78/100)

Potential Gaps:
- Cross-border transfer compliance
- Data localization violation
- Biometric data protection

Recommendations:
1. Verify Singapore is approved country per DPDP Act
2. Ensure biometric data is stored in India
3. Implement additional security controls
4. Update privacy policy
```

---

## Dashboard and Reporting

### Compliance Dashboard

The India Compliance Dashboard provides real-time visibility into compliance status.

**Dashboard Components**:

1. **Overall Score Card**:
   - Aggregate compliance score
   - Trend indicator (improving/degrading)
   - Last check timestamp

2. **Framework Status**:
   - Individual scores for each framework
   - Status indicators (Compliant/Partial/Non-Compliant)
   - Requirements met vs. total

3. **Recent Gaps**:
   - Latest identified gaps
   - Severity indicators
   - Quick links to remediation

4. **Evidence Summary**:
   - Total evidence collected
   - Evidence by source
   - Last collection timestamp

5. **Compliance Trends**:
   - Historical score trend
   - Gap count over time
   - Improvement/degradation pattern

### Generating Reports

**Creating a Report**:

1. Go to **Compliance** → **India Compliance** → **Reports**
2. Click **Generate Report**
3. Select frameworks to include
4. Choose report format:
   - PDF (for auditors)
   - JSON (for systems)
   - Excel (for analysis)
5. Click **Generate**
6. Download or share report

**Report Contents**:
- Executive summary
- Compliance scores by framework
- Detailed findings
- Evidence references
- Remediation recommendations
- Compliance trends
- Legal citations
- Audit trail

### Exporting Evidence

**Exporting Evidence**:

1. Go to **Compliance** → **India Compliance** → **Evidence**
2. Filter by:
   - Control ID
   - Evidence type
   - Date range
   - Source
3. Select evidence items
4. Click **Export**
5. Choose format (CSV, JSON, PDF)
6. Download

---

## Best Practices

### 1. Regular Compliance Checks

- Run compliance checks **monthly** at minimum
- Run checks **weekly** for critical systems
- Run checks **immediately** after system changes

### 2. Proactive Gap Management

- Address **critical** gaps within 1 week
- Address **high** gaps within 2 weeks
- Address **medium** gaps within 1 month
- Address **low** gaps within 3 months

### 3. Evidence Collection

- Set up integrations for **automatic** evidence collection
- Verify evidence quality regularly
- Maintain evidence **audit trail**
- Archive evidence for **3+ years**

### 4. Bias Testing

- Test for bias **before** production deployment
- Test for bias **quarterly** in production
- Test for **all** demographic categories
- Document bias testing results

### 5. Documentation

- Document all **compliance decisions**
- Maintain **audit trail** of changes
- Keep **evidence** organized
- Update **policies** regularly

### 6. Team Collaboration

- Assign **compliance owner**
- Involve **legal team** in policy review
- Involve **engineering team** in remediation
- Communicate **status** to stakeholders

### 7. Continuous Improvement

- Review **compliance trends** monthly
- Identify **patterns** in gaps
- Implement **preventive** measures
- Share **learnings** across teams

---

## Troubleshooting

### Common Issues

**Issue**: "Compliance check failed"
- Verify system is registered
- Check system has data
- Verify integrations are connected
- Try again after a few minutes

**Issue**: "No evidence collected"
- Verify integrations are configured
- Check integration credentials
- Trigger manual sync
- Review integration logs

**Issue**: "Bias detection timeout"
- Reduce test data size
- Try with smaller dataset
- Check system resources
- Contact support

**Issue**: "Policy generation failed"
- Verify system details are complete
- Check data types are valid
- Try with different policy type
- Contact support

### Getting Help

- **Documentation**: https://docs.fairmind.ai/
- **Support Email**: support@fairmind.ai
- **Chat Support**: Available in dashboard
- **Community Forum**: https://community.fairmind.ai/

---

## Next Steps

1. Register your AI system
2. Select applicable frameworks
3. Run initial compliance check
4. Address identified gaps
5. Set up integrations
6. Schedule regular checks
7. Monitor compliance trends
8. Generate audit reports

For more information, see:
- [API Documentation](../api/INDIA_COMPLIANCE_API.md)
- [Integration Setup Guides](../integrations/INTEGRATION_SETUP_GUIDES.md)
- [Regulatory Reference](./REGULATORY_REFERENCE.md)
