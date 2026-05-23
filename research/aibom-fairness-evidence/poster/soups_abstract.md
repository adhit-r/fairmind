# Making Bias Evidence Reviewable in AI Bills of Materials

AI bills of materials can help reviewers understand which datasets, models, preprocessing steps, evaluation sets, remediation components, monitors, and reports belong to an AI system. However, a component inventory alone does not tell a reviewer whether fairness evidence is missing, stale, simulated, unvalidated, or unsupported by human review. This gap can create false assurance: a system may appear documented while the evidence behind fairness claims is incomplete or no longer applicable.

We propose an AIBOM fairness evidence profile: a structured evidence layer that attaches reviewable fairness state to AI supply-chain components. The profile records protected attributes tested, subgroup coverage, fairness metrics, bias tests, remediation history, evidence freshness, validation state, human review status, regulatory mappings, and explicit unknowns. The profile is not a new BOM standard and does not replace model cards, data cards, CycloneDX ML-BOM, or governance reports. Instead, it provides a focused fairness-evidence view that FairMind can layer onto existing AI/ML BOM artifacts.

We ground the profile in FairMind, an AI governance platform with AI BOM management, bias detection, evidence collection, monitoring, and compliance mapping surfaces. We instantiate the profile with three FairMind synthetic fixtures: a loan approval model, a hiring ranker, and a healthcare triage model. For each system, we create a generic AI/ML BOM and a matching fairness evidence profile. We also construct a 24-case fault-injection set covering missing protected attribute tests, missing subgroup coverage, stale fairness results after model updates, unvalidated remediation, proxy feature risks, disconnected monitors, unsupported regulatory claims, and missing reviewer approval.

The planned formative evaluation asks reviewers to compare generic BOMs with the fairness evidence profile when deciding whether a system should be approved, rejected, or sent back for more evidence. The primary outcomes are evidence gap detection rate, root-cause localization accuracy, false assurance rate, review time, confidence calibration, and unsupported fairness claims accepted.

This work frames AI supply-chain transparency as a usable security and governance review problem. The central claim is modest: reviewers need explicit evidence state, not only component provenance, to assess fairness claims. The current artifact package uses FairMind synthetic fixtures only and does not claim production validation, fairness proof, or demonstrated reviewer-performance improvement.

## Keywords

AI bill of materials; ML bill of materials; fairness evidence; bias review; AI governance; usable security; false assurance; model supply chain
