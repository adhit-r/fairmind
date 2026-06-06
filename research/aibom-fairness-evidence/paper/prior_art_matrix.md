# Prior-Art Matrix

This matrix positions the AIBOM fairness evidence profile against adjacent documentation, BOM, assurance, and compliance-evidence work. The novelty claim should be limited to reviewer-visible fairness evidence state across AI BOM components.

## Primary Gap Statement

Existing work can document components, model behavior, dataset properties, controls, provenance, or machine-readable assurance evidence. The gap this paper targets is narrower:

> Reviewers need to know whether fairness claims are supported, stale, simulated, missing, unsupported by downstream evidence, or still awaiting human review at the component where the risk arises.

The paper should not claim that prior work lacks fairness information entirely. The defensible claim is that prior work does not evaluate whether a reviewer can detect and localize fairness-evidence gaps across a BOM graph.

## Comparison Matrix

| Prior work | What it covers | Fairness or evidence support | What it does not settle | Implication for this paper |
| --- | --- | --- | --- | --- |
| CycloneDX ML-BOM and OWASP AI/ML-BOM guide | Machine-readable AI/ML bill of materials for supply-chain transparency, security, compliance, and lifecycle metadata. | Supports ML-BOM concepts and modelCard-like AI metadata; the OWASP guide includes fairness-assessment examples. | Does not by itself evaluate reviewer detection of missing, stale, simulated, unsupported, or unreviewed fairness evidence across components. | Use as the strongest baseline, not as a strawman. |
| Model Cards for Model Reporting, Mitchell et al., FAT* 2019 | Structured model documentation, including intended use and disaggregated evaluation. | Strong model-centered fairness reporting and subgroup-performance framing. | Model-centered rather than BOM-graph-centered; does not enforce component-level unknown-risk or remediation-review state across datasets, preprocessing, monitors, and reports. | The profile should explain how it complements model cards by linking evidence state across components. |
| Datasheets for Datasets, Gebru et al., CACM 2021 | Dataset documentation, provenance, collection, composition, and recommended use. | Strong dataset transparency and accountability framing. | Dataset-centered; does not localize fairness evidence gaps in downstream models, monitors, remediation, or release claims. | Use for dataset evidence fields, not as a whole-system reviewability baseline. |
| Data Cards, Pushkarna et al., FAccT 2022 | Human-centered dataset documentation for practical research and industry settings. | Strong dataset documentation process and transparency support. | Does not cover BOM-level component lineage or reviewer detection of stale and unsupported fairness claims across a system. | Use to justify careful documentation, then distinguish profile-level evidence states. |
| NIST AI RMF 1.0, NIST 2023 | Risk-management framework for trustworthy AI across governance, mapping, measuring, and managing risks. | Defines risk-management practices and trustworthiness considerations. | Framework-level guidance, not a concrete fairness evidence profile or reviewer-task benchmark over BOM artifacts. | Map regulatory controls, but do not treat AI RMF as an implementation baseline. |
| NIST AIBOM presentation, 2024 | Positions AIBOMs as a mechanism for securing AI ecosystems and supply-chain transparency. | Useful framing for AI component visibility, provenance, and ecosystem risk. | Presentation-level guidance; does not provide a fairness-specific reviewer study or profile schema. | Cite for motivation, not as a direct baseline. |
| OSCAL, NIST | Machine-readable security and compliance controls, assessments, and evidence structures. | Strong compliance automation substrate. | General compliance evidence format; not fairness-specific and not a BOM-component reviewer-task study. | Future mapping target for assessment evidence. |
| Making AI Compliance Evidence Machine-Readable, Ugarte et al., arXiv 2026 | Proposes OSCAL extensions and a compliance-as-code architecture for AI assurance evidence. | Strong machine-readable AI compliance evidence framing. | Focuses on assurance architecture and OSCAL evidence, not fairness-evidence reviewability or reviewer false-assurance measurement. | Important adjacent work; this paper must be empirical or fairness-specific to avoid looking redundant. |
| AIBoMGen, arXiv 2026 | Generates signed AIBOMs from model training metadata for secure, transparent, and compliant model training. | Strong AIBOM generation, provenance, signature, and training-metadata focus. | Does not focus on fairness-evidence gaps, reviewer actions, or human review of unsupported fairness claims. | Compare as an AIBOM generation baseline. |
| Operationalising AIBOMs for Verifiable AI Provenance and Lifecycle Assurance, 2026 | AIBOM schema/toolkit for provenance, lifecycle assurance, and trust boundaries. | Strong provenance and lifecycle assurance. | Fairness evidence state and reviewer-centered false assurance are not the central evaluation target. | Use to narrow this paper toward fairness reviewability rather than provenance generally. |
| Audit-as-Code for Continuous AI Assurance, Muhammad et al., Frontiers in AI 2026 | Policy-as-code and continuous assurance framework linked to structured evidence artifacts. | Strong continuous assurance and evidence-gate framing. | Not specialized to fairness-evidence review across BOM components or reviewer localization tasks. | This paper can borrow continuous-assurance vocabulary but should keep its empirical focus on fairness review. |
| AI Risk Scanning and similar AIBOM assurance work | Threat-model-based evidence generation and machine-verifiable AI risk documentation. | Strong security-assurance and risk-evidence framing. | Security-oriented rather than fairness-specific; does not directly test fairness-evidence reviewability. | Good cybersecurity-adjacent motivation, but not a substitute for a fairness pilot. |

## Reviewability Features To Compare

| Feature | Generic ML-BOM | CycloneDX-style ML-BOM or modelCard baseline | Fairness evidence profile |
| --- | --- | --- | --- |
| Component lineage | yes | yes | yes |
| Dataset and model metadata | yes | yes | yes |
| Fairness metrics | no or optional | possible | required where known; missing is explicit |
| Protected attributes tested | no or optional | possible | explicit |
| Subgroup coverage and missing groups | no or optional | possible | explicit |
| Evidence freshness | usually absent | possible but not necessarily review-action oriented | explicit with stale/unknown states |
| Simulated versus validated evidence | usually absent | possible but not central | explicit evidence state |
| Unknown fairness evidence as risk | no | not guaranteed | required via `unknowns` and risk summary |
| Remediation validation state | no | not guaranteed | explicit |
| Unsupported regulatory claim visibility | no | not guaranteed | explicit mapping plus evidence state |
| Human review state | no | not guaranteed | explicit review status and pending actions |
| Component-level reviewer action | no | not guaranteed | explicit risk summary and reviewer action |
| Reviewer-task evaluation | no | no | planned evaluation target |

## Strongest Novelty Claim

Use:

> We contribute and evaluate a reviewer-centered fairness evidence profile for AI/ML BOMs that exposes evidence state, unknown risk, freshness, remediation validation, and review status at the component where a fairness claim is made or invalidated.

Avoid:

> We are the first to add fairness to AI BOMs.

## Evaluation Consequence

The baseline comparison must include at least two conditions:

1. Generic AI/ML BOM: component metadata and dependencies only.
2. CycloneDX-style ML-BOM/model-card baseline: realistic ML-BOM metadata and fairness notes, but without explicit unknown-risk, evidence-state, review-action, and remediation-validation fields.

The profile condition should be evaluated on whether reviewers detect:

- missing protected attribute tests,
- missing subgroup coverage,
- stale fairness results after model updates,
- unvalidated remediation,
- proxy risks not surfaced as evidence gaps,
- disconnected fairness monitors,
- unsupported regulatory claims,
- missing reviewer approval.

## Source List

- CycloneDX ML-BOM: https://cyclonedx.org/capabilities/mlbom/
- OWASP CycloneDX Authoritative Guide to AI/ML-BOM: https://cyclonedx.org/guides/OWASP_CycloneDX-Authoritative-Guide-to-AI-ML-BOM-en.pdf
- Model Cards for Model Reporting: https://arxiv.org/abs/1810.03993
- Datasheets for Datasets: https://arxiv.org/abs/1803.09010
- Data Cards: Purposeful and Transparent Dataset Documentation for Responsible AI: https://arxiv.org/abs/2204.01075
- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework
- NIST AIBOM presentation: https://csrc.nist.gov/presentations/2024/securing-ai-ecosystems-the-critical-role-of-aibom
- NIST OSCAL: https://pages.nist.gov/OSCAL/
- AIBoMGen: Generating an AI Bill of Materials for Secure, Transparent, and Compliant Model Training: https://arxiv.org/abs/2601.05703
- Making AI Compliance Evidence Machine-Readable: https://arxiv.org/abs/2604.13767
- Audit-as-Code: A Policy-as-Code Framework for Continuous AI Assurance: https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2026.1759211/full
- Operationalising Artificial Intelligence Bills of Materials for Verifiable AI Provenance and Lifecycle Assurance: https://www.frontiersin.org/articles/10.3389/fcomp.2026.1735919
- AI Bill of Materials and Beyond: Systematizing Security Assurance through the AI Risk Scanning Framework: https://arxiv.org/abs/2511.12668
