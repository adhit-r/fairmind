# FairMind: An Open Platform for Multi-Framework AI Compliance Auditing and Bias Detection with India-Specific Regulatory Support

**Authors**: Adhi R. et al.

**Target venues**: ACM FAccT 2027, CODS-COMAD 2027, AIES 2027, NeurIPS SafeGenAI Workshop 2026

---

## Abstract

As AI systems are deployed across regulated sectors in India and globally, organizations face a fragmented compliance landscape spanning the EU AI Act, GDPR, India's Digital Personal Data Protection (DPDP) Act 2023, NITI Aayog Responsible AI Principles, ISO 42001, and NIST AI RMF. Existing fairness toolkits (AIF360, Fairlearn, What-If Tool) address bias measurement but do not bridge the gap between bias metrics and regulatory compliance evidence. We present FairMind, an open-source platform that unifies (1) multi-modal bias detection across text, image, audio, and video modalities using WEAT, SEAT, causal, counterfactual, adversarial, and temporal methods; (2) a compliance audit engine implementing 24 automated checks across 5 regulatory frameworks; (3) an automated evidence collection pipeline that maps bias test results to specific regulatory requirements; and (4) an AI Bill of Materials (AI BOM) for component-level risk attribution. To our knowledge, FairMind is the first platform to implement automated compliance checks for India's DPDP Act and NITI Aayog principles alongside international frameworks in a single system. We describe the architecture, detail the regulatory mapping methodology, and report on the compliance audit engine's coverage across framework requirements.

**Keywords**: AI fairness, regulatory compliance, bias detection, DPDP Act, EU AI Act, AI Bill of Materials, responsible AI

---

## 1. Introduction

The global regulatory landscape for AI systems is expanding rapidly but unevenly. The EU AI Act (2024) establishes risk-based obligations for AI providers. India's DPDP Act 2023 introduces consent, localization, and breach notification requirements that apply to AI systems processing personal data. NITI Aayog's Responsible AI principles (2021) and MeitY's guidelines add sector-specific expectations for fairness, transparency, and accountability. ISO 42001 (2023) provides an AI management systems standard, while NIST AI RMF offers a voluntary risk management framework.

Organizations deploying AI in India face a unique challenge: they must simultaneously satisfy domestic frameworks (DPDP Act, NITI Aayog, MeitY, Digital India Act) and international standards (EU AI Act, GDPR, ISO 42001) -- often for the same model. No existing tool addresses this multi-jurisdictional compliance burden.

**Existing tools and their limitations.** IBM AIF360 and Microsoft Fairlearn provide bias metrics (statistical parity, equalized odds, disparate impact) but have no compliance mapping layer. Google's What-If Tool offers interactive exploration but no regulatory reporting. Holistic AI and Credo AI provide commercial compliance platforms but do not cover Indian regulatory frameworks. None of these tools support multi-modal bias detection (image, audio, video) or generate framework-specific evidence artifacts.

**Contributions.** We make the following contributions:

1. **Multi-framework compliance audit engine**: 24 automated checks across EU AI Act (6 checks), GDPR (5), India DPDP Act (4), ISO 42001 (5), and NIST AI RMF (4), with gap analysis, severity ratings, and actionable recommendations.

2. **India-specific regulatory library**: Machine-readable encodings of DPDP Act 2023 (14 requirements with legal citations), NITI Aayog principles, and MeitY guidelines -- the first open-source implementation of these frameworks.

3. **Multi-modal bias detection pipeline**: A unified 5-phase evaluation pipeline (pre-deployment, real-time monitoring, post-deployment audit, human-in-loop, continuous learning) supporting 10 bias types across text, image, audio, and video modalities.

4. **Automated evidence collection**: A system that maps bias test results, model metadata, and monitoring data to specific regulatory requirements, producing audit-ready evidence artifacts.

5. **AI Bill of Materials**: Component-level tracking with risk scoring across 7 layers (data, model development, infrastructure, deployment, monitoring, security, compliance).

---

## 2. System Architecture

FairMind follows a domain-driven architecture with three tiers:

### 2.1 Backend (Python/FastAPI)

The backend is organized into domain services:

- **Bias Detection Domain**: `AdvancedBiasDetectionService` (causal, counterfactual, intersectional, adversarial, temporal, contextual, amplification, emergent, compound, latent bias types), `MultimodalBiasDetectionService` (image, audio, video modalities), `LLMAsJudgeService` (multi-judge ensemble evaluation), `ComprehensiveBiasEvaluationPipeline` (5-phase lifecycle).

- **Compliance Domain**: `ComplianceAuditEngine` (24 checks across 5 frameworks), `IndiaComplianceService` (DPDP Act, NITI Aayog, MeitY), `ComplianceMapper` (policy-to-regulatory-control mapping), `AutomatedEvidenceCollector` (10 evidence categories).

- **Governance Domain**: `AIBOMService` (7-layer Bill of Materials), `PolicyEngine` (rule-based policy enforcement), `RiskIncidentManager` (incident tracking and response).

- **Explainability Domain**: `GenerativeAIExplainability` (attention visualization, activation patching, circuit discovery, concept bottleneck, prompt ablation, gradient-based, counterfactual, uncertainty quantification).

### 2.2 Fairness Library

A standalone library (`fairness_library/`) encodes regulatory frameworks as structured data:

- `india_regulatory_frameworks.py`: DPDP Act 2023 (14 requirements), NITI Aayog principles, MeitY guidelines -- each with requirement IDs, legal citations, control mappings, key requirements, and evidence types.
- `metrics.py`: Standard fairness metrics (statistical parity, equalized odds, disparate impact, four-fifths rule).
- `llm_bias.py`: LLM-specific bias benchmarks (StereoSet, CrowS-Pairs, BBQ, WEAT, SEAT).
- `governance.py`: Governance structures and policy templates.

### 2.3 Frontend (Next.js)

A dashboard with 20+ views including compliance dashboard, AI BOM explorer, explainability studio, evidence collection, model lifecycle management, LLM testing, stakeholder dashboards, and advanced bias analysis.

---

## 3. Compliance Audit Engine

### 3.1 Design

The engine evaluates AI models against regulatory requirements using a declare-and-check pattern. Model owners declare context attributes (risk level, consent mechanisms, transparency measures, etc.), and the engine evaluates these declarations against framework-specific requirements.

Each framework is encoded as a `FrameworkSpec` containing `Requirement` objects with:
- **ID**: Unique requirement identifier (e.g., `EU-1`, `DPDP-3`)
- **Description**: Human-readable requirement description
- **Severity**: `critical | major | minor | info`
- **Check function**: A callable that evaluates model context against the requirement, returning `(passed: bool, finding: str, recommendation: str)`

### 3.2 Framework Coverage

| Framework | Checks | Critical | Major | Minor |
|-----------|--------|----------|-------|-------|
| EU AI Act | 6 | 1 | 4 | 1 |
| GDPR | 5 | 2 | 3 | 0 |
| India DPDP Act | 4 | 1 | 3 | 0 |
| ISO 42001 | 5 | 2 | 1 | 2 |
| NIST AI RMF | 4 | 1 | 3 | 0 |
| **Total** | **24** | **7** | **14** | **3** |

### 3.3 India DPDP Act Implementation

The DPDP Act module encodes 14 requirements from the Act with legal citations to specific sections:

- **Section 6**: Consent management (explicit, informed, withdrawable)
- **Section 16**: Data localization (sensitive data must be stored in India)
- **Section 16**: Cross-border transfer (approved country list)
- **Chapter III**: Data principal rights
- **Section 9**: Children's data protection
- **Section 8**: Data breach notification (72-hour window)
- **Section 8**: Data retention limits
- **Section 10**: Significant data fiduciary obligations
- **Section 8**: Grievance redressal mechanism
- **Section 10**: Data Protection Officer appointment
- **Section 10**: Data audit requirements
- **Section 10**: Data impact assessment
- **Section 8**: Security safeguards
- **Section 7**: Transparency and disclosure

Each requirement maps to specific evidence types (e.g., consent records, location verification audits, breach notification logs) that the automated evidence collector gathers from the platform's existing features.

### 3.4 Gap Analysis Output

For each non-compliant requirement, the engine produces:
- The specific regulatory gap identified
- Severity classification (critical/major/minor/info)
- Actionable recommendation with regulatory citation
- Per-framework compliance score (0.0 - 1.0)
- Overall compliance status (compliant/non-compliant)

---

## 4. Multi-Modal Bias Detection Pipeline

### 4.1 Bias Taxonomy

FairMind implements 10 bias types organized by detection method:

| Bias Type | Method | Modalities |
|-----------|--------|------------|
| Causal | Causal inference, treatment effects | Text, Tabular |
| Counterfactual | Counterfactual generation | Text, Image |
| Intersectional | Multi-attribute analysis | All |
| Adversarial | Adversarial perturbation | Text, Image, Audio |
| Temporal | Time-series drift analysis | All |
| Contextual | Context-sensitive evaluation | Text |
| Amplification | Bias amplification detection | All |
| Emergent | Emergence in multi-agent systems | Text |
| Compound | Multi-factor compound effects | All |
| Latent | Latent bias mining | Text, Tabular |

### 4.2 Multi-Modal Support

For each modality, specialized detectors address modality-specific bias patterns:

- **Image**: Demographic representation bias, object detection bias, scene bias, style/aesthetic bias, cultural bias
- **Audio**: Voice characteristic bias, accent bias, language bias
- **Video**: Motion bias, activity bias, temporal representation bias
- **Cross-modal**: Stereotype propagation across modalities, modality preference bias

### 4.3 Five-Phase Evaluation Lifecycle

Unlike point-in-time bias testing, FairMind treats bias evaluation as a continuous lifecycle:

1. **Pre-deployment**: StereoSet, CrowS-Pairs, BBQ, WEAT, SEAT, minimal pairs, red teaming (minimum 1000 samples, 95% confidence)
2. **Real-time monitoring**: 5-minute intervals, spike detection (threshold: 0.2), drift alerts
3. **Post-deployment auditing**: Periodic deep audits, regression testing, compliance evidence generation
4. **Human-in-loop**: Expert review of flagged cases, calibration of automated thresholds
5. **Continuous learning**: Model updates based on monitoring feedback, threshold adaptation

### 4.4 LLM-as-Judge Evaluation

A multi-judge ensemble where judge LLMs (GPT-4, Claude, Gemini) evaluate target model outputs for bias across 8 categories (gender, race, age, cultural, socioeconomic, intersectional, professional, religious). Each judge produces:
- Bias score (0.0 - 1.0)
- Confidence rating
- Structured reasoning
- Specific evidence from outputs
- Severity classification
- Remediation recommendations

---

## 5. AI Bill of Materials

The AI BOM tracks model components across 7 layers:

1. **Data Layer**: Training datasets, preprocessing pipelines, data quality metrics
2. **Model Development Layer**: Architecture, training methodology, hyperparameters
3. **Infrastructure Layer**: Compute resources, deployment environment
4. **Deployment Layer**: Serving configuration, scaling policies
5. **Monitoring Layer**: Metrics collected, alert configurations
6. **Security Layer**: Access controls, adversarial robustness
7. **Compliance Layer**: Regulatory mappings, certification status

Each component receives a risk score and compliance status, enabling component-level bias attribution -- tracing which pretrained components contribute what fraction of observed bias.

---

## 6. Automated Evidence Collection

The evidence collector maps 10 evidence categories to platform features:

| Evidence Category | Source Service | Regulatory Mapping |
|---|---|---|
| Dataset quality | Dataset Service | EU AI Act Art. 10 |
| Privacy controls | Dataset + Bias Detection | GDPR Art. 5, DPDP Sec. 6 |
| Training data bias | Bias Detection | EU AI Act Art. 10, NITI Aayog |
| Access controls | Model Service | ISO 42001 Cl. 6, DPDP Sec. 8 |
| Adversarial robustness | Security Testing | EU AI Act Art. 15 |
| Model versioning | Model Registry | ISO 42001 Cl. 7 |
| Performance drift | Monitoring Service | NIST AI RMF MEASURE |
| Fairness monitoring | Bias + Monitoring | EU AI Act Art. 9, NITI Aayog |
| Audit logging | Monitoring Service | EU AI Act Art. 12, DPDP Sec. 10 |
| Documentation | Model Service | EU AI Act Annex IV, ISO 42001 |

This closes the loop between bias metrics and regulatory evidence -- a gap that no existing open-source tool addresses.

---

## 7. Related Work

| Tool | Bias Detection | Compliance Mapping | India Frameworks | Multi-Modal | AI BOM | Evidence Collection |
|------|---------------|-------------------|-----------------|-------------|--------|-------------------|
| AIF360 | Yes | No | No | No | No | No |
| Fairlearn | Yes | No | No | No | No | No |
| What-If Tool | Limited | No | No | No | No | No |
| Holistic AI | Yes | Partial (EU) | No | No | No | Partial |
| Credo AI | Yes | Yes (EU, NIST) | No | No | No | Yes |
| **FairMind** | **Yes** | **Yes (5 frameworks)** | **Yes** | **Yes** | **Yes** | **Yes** |

---

## 8. Discussion and Future Work

**Limitations.** The current compliance checks are attribute-presence checks rather than deep semantic validation. The DPDP Act is still evolving (rules under Sections 16-17 are pending), and the engine will require updates as regulations mature. Multi-modal bias detection for audio and video is in early stages compared to text.

**Future directions.** Our roadmap includes:
- **Causal fairness engine**: Causal DAGs for counterfactual fairness testing (Plecko & Bareinboim, 2024)
- **Agentic AI fairness**: Bias propagation analysis across multi-agent chains
- **Multilingual fairness**: Cross-language bias testing for 12+ Indic languages
- **Fairness certification passports**: W3C Verifiable Credential-based fairness certificates
- **RBI FREE-AI compliance**: Indian financial sector AI regulatory coverage
- **Privacy-preserving auditing**: Differential privacy for fairness audits without accessing protected attributes

---

## 9. Conclusion

FairMind addresses a critical gap in the AI governance tooling ecosystem: the disconnect between bias metrics and regulatory compliance evidence, particularly for India's emerging regulatory landscape. By unifying multi-modal bias detection, multi-framework compliance auditing, automated evidence collection, and AI Bill of Materials in a single open-source platform, FairMind enables organizations to move from ad-hoc bias testing to systematic, audit-ready compliance management. The India-specific regulatory library -- encoding DPDP Act 2023, NITI Aayog principles, and MeitY guidelines with legal citations and evidence mappings -- represents, to our knowledge, the first open-source implementation of these frameworks for automated AI compliance.

---

## References

[1] EU AI Act. Regulation (EU) 2024/1689 of the European Parliament. 2024.

[2] Digital Personal Data Protection Act, 2023. The Gazette of India. No. 22 of 2023.

[3] NITI Aayog. Responsible AI #AIforAll -- Approach Document for India. 2021.

[4] Bellamy, R.K.E. et al. AI Fairness 360: An Extensible Toolkit for Detecting and Mitigating Algorithmic Bias. IBM Journal of Research and Development, 2019.

[5] Bird, S. et al. Fairlearn: A toolkit for assessing and improving fairness in AI. Microsoft Research, 2020.

[6] ISO/IEC 42001:2023. Information technology -- Artificial intelligence -- Management system. 2023.

[7] NIST AI 100-1. Artificial Intelligence Risk Management Framework. 2023.

[8] Plecko, D. & Bareinboim, E. Causal Fairness Analysis: A Causal Toolkit for Fair Decision Making. Foundations and Trends in Machine Learning, 2024.

[9] Nadeem, M. et al. StereoSet: Measuring stereotypical bias in pretrained language models. ACL 2021.

[10] Nangia, N. et al. CrowS-Pairs: A Challenge Dataset for Measuring Social Biases in Masked Language Models. EMNLP 2020.

[11] Parrish, A. et al. BBQ: A Hand-Built Bias Benchmark for Question Answering. ACL Findings 2022.

[12] Caliskan, A. et al. Semantics derived automatically from language corpora contain human-like biases. Science, 2017. (WEAT)

[13] May, C. et al. On Measuring Social Biases in Sentence Encoders. NAACL 2019. (SEAT)

[14] MeitY. Guidelines for Responsible AI. Ministry of Electronics and Information Technology, Government of India, 2024.

---

## Appendix A: Venue-Specific Submission Notes

### Option 1: ACM FAccT 2027 (Primary recommendation)
- **Track**: Systems and tools
- **Angle**: Lead with the India compliance gap, position as Global South AI governance tooling
- **Page limit**: 10 pages + references
- **Strength**: FAccT's growing interest in non-Western regulatory contexts; no competing India-focused tool paper

### Option 2: CODS-COMAD 2027 (India CS conference)
- **Track**: Industry / applied track
- **Angle**: India-specific regulatory automation, DPDP Act implementation
- **Strength**: Home audience, direct relevance to Indian organizations

### Option 3: AIES 2027
- **Track**: Full paper
- **Angle**: Multi-framework compliance as a sociotechnical system design problem
- **Strength**: Interdisciplinary audience (policy + tech)

### Option 4: NeurIPS SafeGenAI Workshop 2026
- **Track**: Workshop paper (4-6 pages)
- **Angle**: Multi-modal bias detection pipeline + LLM-as-Judge
- **Strength**: Technical depth in bias methods, workshop format is lower bar

### Option 5: Demo Paper (any venue)
- **Track**: Demo/systems track at AAAI, IJCAI, or WWW
- **Angle**: Live demo of compliance dashboard, audit workflow, evidence generation
- **Page limit**: 2-4 pages
- **Strength**: FairMind's 20+ dashboard views make for a strong demo
