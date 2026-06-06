# Making Bias Evidence Reviewable in AI Bills of Materials

## Abstract

AI and ML bills of materials make system components visible, but component visibility is not the same as fairness-evidence reviewability. A reviewer may know which datasets, preprocessing steps, models, evaluation sets, remediations, monitors, and release reports exist while still being unable to tell whether a fairness claim is current, complete, validated, or reviewed. This paper studies a focused fairness evidence profile layered onto AI/ML BOM artifacts. The profile represents protected attributes tested, subgroup coverage, fairness metrics, bias tests, remediation history, evidence freshness, validation state, review state, regulatory mappings, claim support, explicit unknowns, and component-localized reviewer actions.

The contribution is reviewability-centered: AI BOMs expose components; the fairness evidence profile exposes whether fairness claims are reviewable at the component where the claim is made, weakened, or invalidated. We instantiate the profile in FairMind, a prototype AI governance platform, and define a fault-injection evaluation over three synthetic systems: loan approval, hiring ranking, and healthcare triage. The planned formative pilot compares three artifact conditions: a generic AI/ML BOM, a CycloneDX-style ML-BOM with model-card-like metadata, and the AIBOM fairness evidence profile. The target outcomes are detection of injected evidence gaps, component localization, false assurance, review time, confidence calibration, and rationale quality.

Results are pending until a real pilot is run. This draft does not claim that the profile proves fairness, improves reviewer performance, provides production assurance, or defines a separate BOM specification.

## Introduction

AI governance reviews increasingly depend on structured evidence. Teams are asked to explain which components are in an AI system, what data was used, which tests were run, which risks remain, and which claims can be supported for release or regulatory review. AI and ML bills of materials are one response to this problem: they make component inventories, dependencies, provenance, and lifecycle metadata more visible. Work such as CycloneDX ML-BOM and the OWASP CycloneDX AI/ML-BOM guide provides a strong basis for machine-readable AI/ML component documentation: [CycloneDX ML-BOM](https://cyclonedx.org/capabilities/mlbom/) and [OWASP CycloneDX Authoritative Guide to AI/ML-BOM](https://cyclonedx.org/guides/OWASP_CycloneDX-Authoritative-Guide-to-AI-ML-BOM-en.pdf).

For fairness review, however, the core question is not only "what components exist?" It is also "can a reviewer tell whether the fairness claim attached to this component is supported?" A model component might link to an evaluation report, but the report may be stale after a model update. A remediation component might claim mitigation, but lack a post-remediation test. A monitor might exist, but be disconnected from live outcomes. A release report might cite regulatory coverage, but rely on simulated or incomplete evidence. In these cases, the system can look documented while still creating false assurance.

This paper addresses that gap by studying a fairness evidence profile layered onto AI/ML BOM artifacts. The profile does not replace BOMs, model cards, data cards, or compliance evidence formats. Instead, it adds an explicit review layer that records evidence state, unknown risk, freshness, remediation validation, claim support, and human review status at component level. The profile is intended to help reviewers ask bounded questions: what is known, what is missing, what is stale, what is only simulated, which downstream claim is affected, and what reviewer action is required?

The paper's current evidence is artifact-level and protocol-level. The repository contains a JSON Schema, synthetic examples, generic and CycloneDX-style comparison artifacts, a FairMind generator path, fault-injection cases, reviewer task cards, a pilot protocol, and an analysis plan. Reviewer results are not yet available. All empirical claims in this draft are therefore framed as planned measurements or marked for post-pilot reporting.

## Research Questions

RQ1: Can reviewers detect injected fairness evidence faults from each artifact condition: generic AI/ML BOM, CycloneDX-style ML-BOM with model-card-like metadata, and AIBOM fairness evidence profile?

RQ2: Can reviewers localize detected faults to the responsible component or evidence object?

RQ3: Do reviewers accept unsupported release, regulatory, mitigation, monitoring, or reviewer-approval claims at different rates across artifact conditions?

RQ4: How do review time, confidence, and rationale quality vary across artifact conditions?

RQ5: Which profile fields or baseline omissions explain missed faults, false assurance, or reviewer confusion?

## Contributions

This paper makes four bounded contributions.

First, it defines a reviewer-centered fairness evidence profile layered onto AI/ML BOM artifacts. The profile encodes evidence state, subgroup coverage, freshness, validation state, review status, unknowns, claim support, evidence-gap type, component fault localization, and reviewer-required action.

Second, it grounds the profile in FairMind as a prototype generator and review substrate. FairMind is used to generate and surface profile artifacts from mapped AI BOM components, bias outputs, evidence records, remediation records, and review status. This is a prototype claim, not a production assurance claim.

Third, it creates a synthetic fault-injection evaluation package with three systems and twenty-four evidence-gap cases. The fault set covers missing protected-attribute tests, missing subgroup coverage, stale fairness results, unvalidated remediation, proxy risks, disconnected monitors, unsupported regulatory claims, and missing reviewer approval.

Fourth, it specifies a formative pilot protocol and analysis plan for measuring reviewability. The planned analysis reports detection, localization, false assurance, review time, confidence calibration, unsupported claims accepted, and qualitative error themes. Results are pending until a real pilot is run.

## Related Work

AI/ML BOMs provide the strongest baseline for this work. CycloneDX ML-BOM and the OWASP CycloneDX AI/ML-BOM guide support machine-readable AI/ML component transparency, lifecycle metadata, and model-card-like AI metadata, including fairness-assessment examples. This paper treats that work as an adjacent baseline rather than a strawman. The narrower question here is whether reviewers can detect and localize missing, stale, simulated, unsupported, or unreviewed fairness evidence across the BOM graph.

Model documentation work motivates the evidence fields used by the profile. Model Cards for Model Reporting, Mitchell et al., FAT* 2019, emphasizes intended use and disaggregated evaluation: [Model Cards](https://arxiv.org/abs/1810.03993). Datasheets for Datasets, Gebru et al., CACM 2021, and Data Cards, Pushkarna et al., FAccT 2022, provide dataset-centered transparency and process guidance: [Datasheets](https://arxiv.org/abs/1803.09010) and [Data Cards](https://arxiv.org/abs/2204.01075). The profile complements these formats by linking evidence state across datasets, preprocessing, models, evaluation sets, monitors, remediations, and release reports.

Risk-management and compliance-evidence work provides governance context. NIST AI RMF 1.0 frames AI risk management across governance, mapping, measuring, and managing activities: [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework). NIST's AIBOM presentation motivates AIBOMs as a mechanism for AI ecosystem and supply-chain transparency: [NIST AIBOM presentation](https://csrc.nist.gov/presentations/2024/securing-ai-ecosystems-the-critical-role-of-aibom). OSCAL provides a machine-readable structure for security and compliance controls, assessments, and evidence: [NIST OSCAL](https://pages.nist.gov/OSCAL/).

Recent AI assurance work is also adjacent. The prior-art matrix identifies machine-readable AI compliance evidence, AIBoMGen, operationalized AIBOM lifecycle assurance, audit-as-code, and AI risk scanning as related work on provenance, signed AIBOM generation, assurance architecture, policy-as-code, and risk documentation: [AIBoMGen](https://arxiv.org/abs/2601.05703), [Making AI Compliance Evidence Machine-Readable](https://arxiv.org/abs/2604.13767), [Operationalising Artificial Intelligence Bills of Materials](https://www.frontiersin.org/articles/10.3389/fcomp.2026.1735919), [Audit-as-Code](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2026.1759211/full), and [AI Bill of Materials and Beyond](https://arxiv.org/abs/2511.12668). This paper's focus is narrower: fairness-evidence reviewability and reviewer false assurance over BOM-linked artifacts.

## Fairness Evidence Profile Design

The profile is a structured evidence layer attached to an AI/ML BOM. Its design principle is that missing or weak fairness evidence should become explicit review state, not disappear into absent fields or ambiguous documentation.

The top-level schema records profile identity, BOM reference, system name and domain, generation time, FairMind context, components, a risk summary, a review summary, and limitations. Each component records identity, type, version, upstream and downstream components, protected attributes tested, subgroup coverage, fairness metrics, bias tests, known bias risks, remediation history, validation state, evidence references, evidence freshness, review status, regulatory mappings, unknowns, risk summary, claim support, evidence-gap type, evidence-state reason, component fault localization, and reviewer-required action.

The profile uses explicit evidence states: `unknown`, `missing`, `simulated`, `stale`, `current`, `reviewed`, and `not_applicable`. This vocabulary is intentionally reviewer-facing. A simulated monitor is not treated as a live monitor. A stale fairness result is not treated as current evidence. Missing subgroup coverage is recorded as an evidence gap rather than silently omitted. Unknown fairness evidence is represented as unknown risk rather than low risk.

The component-level fields are designed to answer four review questions.

1. What evidence exists? Relevant fields include protected attributes tested, subgroup coverage, fairness metrics, bias tests, remediation history, evidence references, and regulatory mappings.
2. What is the state of that evidence? Relevant fields include evidence state, evidence freshness, validation state, review status, and claim support.
3. What is missing or weakened? Relevant fields include unknowns, evidence-gap type, evidence-state reason, unsupported reason, stale evidence counts, simulated evidence counts, and key risks.
4. What should the reviewer do? Relevant fields include reviewer-required action, risk summary reviewer action, pending review actions, component fault localization, and downstream claims affected.

This design deliberately avoids turning the profile into a fairness score or certification label. The profile can support an approval, rejection, or request for more evidence only to the extent that the artifact shows reviewable evidence. It does not show that the underlying system is fair.

## FairMind Prototype

FairMind is the prototype platform used to generate and surface the fairness evidence profile. The prototype connects existing FairMind AI BOM, bias detection, evidence collection, monitoring, remediation, and compliance mapping surfaces into a reviewer-facing artifact.

The integration map links profile fields to current FairMind services. AI BOM services provide BOM references, component identity, and upstream/downstream lineage. Bias detection and benchmark services provide protected attributes tested, subgroup coverage, fairness metrics, and bias tests. Evidence collection services provide evidence references and timestamps. Compliance mapping provides regulatory controls and evidence requirements. Remediation and review records provide validation state, review status, and pending actions. When a required field cannot be supported from mapped inputs, the generator records an explicit unknown.

The generator path is implemented in `apps/backend/src/application/services/fairness_evidence_profile_service.py`, with route and service tests supporting implementation-level claims. In this paper, those tests support only the claim that FairMind can generate profile-shaped artifacts from mapped inputs. They do not support claims about production deployment, reviewer performance, or fairness outcomes.

The current synthetic profile examples cover three domains: loan approval, hiring ranking, and healthcare triage. Each profile is paired with baseline artifacts so reviewers can compare what is visible in a generic AI/ML BOM, a CycloneDX-style ML-BOM with model-card-like metadata, and the AIBOM fairness evidence profile.

## Fault-Injection Evaluation

The fault-injection package defines twenty-four synthetic evidence-gap cases across the three systems. The cases cover eight fault families:

1. Missing protected attribute tests.
2. Missing subgroup coverage.
3. Stale fairness results after model updates or deployment-population changes.
4. Remediation attempted but not validated.
5. Proxy feature risks not surfaced as fairness evidence gaps.
6. Fairness monitors absent, simulated, incomplete, or disconnected from live outcomes.
7. Unsupported regulatory or release claims.
8. Missing reviewer approval.

The evaluation compares three artifact conditions. The generic AI/ML BOM condition contains component inventory and high-level metadata. The CycloneDX-style condition contains stronger component, dependency, model, dataset, and model-card-like metadata, but omits the profile-specific unknown-risk, evidence-state, reviewer-action, and remediation-validation framing. The profile condition exposes fairness evidence state, evidence gaps, component localization, remediation validation state, reviewer action, and unsupported claim risk.

This design is intended to avoid a weak baseline comparison. The CycloneDX-style condition recognizes that existing ML-BOM and model-card-style artifacts can include fairness-relevant information. The evaluation question is not whether baselines contain no fairness information. The question is whether the profile's explicit evidence-state and action fields make fairness evidence gaps easier to detect, localize, and explain.

The finalized paper can include a compact fault-injection coverage table once the evaluation materials are frozen.

## Formative Pilot Protocol

The pilot protocol is formative. It is designed to test artifact reviewability and refine the profile before any larger study. It does not establish production assurance, fairness certification, or controlled-study results unless a separate formal human-subjects protocol and approval process are completed.

The target participants are reviewers familiar with at least one of AI governance, software supply-chain review, model risk review, ML evaluation, fairness assessment, compliance review, security review, or technical audit. Reviewers should be able to read JSON-like artifacts in English and should not have prior access to the answer key for the task materials they review.

The protocol uses three synthetic systems: Loan Approval Model, Hiring Ranker, and Healthcare Triage Model. Reviewers complete task cards that ask for a decision, risk found, responsible component, evidence missing or stale, confidence score, and short rationale. Decisions are coded as approve, reject, or request more evidence.

When feasible, the protocol uses a within-subject design: each reviewer sees all three artifact conditions, with artifact order and system order rotated. The protocol records task timing, confidence, rationale text, localized component, evidence gap type, unsupported-claim acceptance, and facilitator notes. The debrief asks which artifacts made gaps easiest to find, which fields were confusing, and whether any artifact wording implied stronger assurance than the evidence supported.

Results are pending until a real pilot is run.

The finalized report should record the exact counterbalancing schedule used for the pilot.

TODO: Insert participant count and reviewer background summary after pilot execution.

## Expected Analysis

The planned analysis treats one reviewer response to one task under one artifact condition as the primary unit of analysis. It reports descriptive results by artifact condition, system, task, and fault type. For small samples, the analysis plan prioritizes counts, percentages, medians, interquartile ranges, and qualitative themes over strong significance language.

The primary metrics are:

1. Detection rate: whether reviewers identify injected faults or expected evidence gaps.
2. Localization accuracy: whether detected faults are localized to the correct component or evidence object.
3. False assurance rate: whether reviewers approve or accept a release, mitigation, monitoring, regulatory, or review claim when the supporting evidence is missing, stale, unsupported, simulated-only, unreviewed, or unvalidated.
4. Review time: elapsed time per task and per artifact block.
5. Confidence calibration: the relationship between confidence and correctness, including high-confidence errors.
6. Unsupported claims accepted: claim-level acceptance of unsupported release, regulatory, mitigation, monitoring, or reviewer-approval claims.

Secondary analysis codes evidence-gap classification accuracy and rationale support level. Qualitative error-theme coding covers missed faults, false assurance cases, confusing fields, task ambiguity, component-localization errors, and imported assumptions.

No outcome is claimed before data collection. The expected reporting form is descriptive: "In this formative pilot, reviewers detected N of M injected evidence faults under condition C." If the data are sparse, mixed, or inconclusive, the paper will report that directly and treat the result as protocol feedback.

TODO: Insert detection, localization, false assurance, timing, confidence, and qualitative-theme tables after pilot execution.

## Limitations

The current artifact package is synthetic. The loan approval, hiring, and healthcare examples do not represent real deployments, real protected-class outcomes, or live model behavior.

The current evidence is schema-level, example-level, generator-level, and protocol-level. Reviewer performance results are pending until a real pilot is run. The paper therefore cannot claim improved detection, reduced false assurance, faster review, better calibration, or generalizable reviewer behavior.

The profile exposes reviewable evidence state, but it does not prove fairness. A complete and current profile can still be attached to a system whose fairness metrics are unacceptable, whose task framing is flawed, or whose deployment context changes after review.

The profile is not a new AI BOM standard and does not replace CycloneDX ML-BOM, model cards, data cards, OSCAL, governance reports, or regulatory review. It is a focused profile that can be layered onto those artifacts where component-level fairness evidence state is needed.

The pilot may be underpowered, affected by order effects, and dependent on the realism of the task materials. If a small internal run is conducted, it should be described as formative feedback unless formal human-subjects review and study controls are in place.

## Ethics

The pilot uses synthetic systems and synthetic evidence artifacts. Reviewers are not asked to make decisions affecting real applicants, patients, workers, or borrowers. The protocol should make clear that the task evaluates artifact reviewability, not reviewer competence.

Participant data should be minimized. Response records should use stable reviewer identifiers that do not reveal identity, and analysis should avoid publishing identifiable rationale text. Facilitator notes should not include unnecessary personal details.

The paper should avoid fairness washing. A reviewable profile could still be misused as a badge of safety if readers interpret structured evidence as proof of fairness. The draft therefore states the boundary explicitly: the profile makes evidence state visible; it does not certify that a system is fair.

## Artifact Availability

The current artifact package is located at `research/aibom-fairness-evidence`. It includes:

1. `schema/aibom_fairness_evidence.schema.json`: JSON Schema for the fairness evidence profile.
2. `examples/*_fairness_profile.json`: synthetic FairMind fairness profile fixtures.
3. `examples/generic_*_mlbom.json`: generic AI/ML BOM comparison artifacts.
4. `examples/cyclonedx_style_*_mlbom.json`: stronger CycloneDX-style baseline artifacts.
5. `evaluation/fault_injection_cases.csv`: twenty-four evidence-gap cases.
6. `evaluation/reviewer_task_cards.md`: twelve reviewer tasks.
7. `evaluation/study_protocol.md`: formative pilot protocol.
8. `evaluation/analysis_plan.md`: planned analysis for detection, localization, false assurance, timing, confidence, and qualitative themes.
9. `apps/backend/src/application/services/fairness_evidence_profile_service.py`: FairMind prototype generator path.

The artifact package should be versioned before pilot execution so each reported number traces back to the exact artifacts shown to reviewers.

## Conclusion

AI BOMs can make AI system components visible, but fairness review requires more than component inventory. Reviewers need to know whether fairness claims are supported, stale, simulated, missing, unsupported by downstream evidence, or still awaiting human review at the component where risk arises.

This paper proposes a focused AIBOM fairness evidence profile for that reviewability problem. The profile layers explicit evidence state, unknown risk, freshness, remediation validation, claim support, and review action onto AI/ML BOM components. FairMind provides a prototype generator and synthetic artifacts for evaluating the profile. The planned fault-injection pilot measures whether reviewers can detect, localize, and explain fairness evidence gaps across baseline and profile conditions.

Results are pending until a real pilot is run. Until then, the contribution is a bounded artifact and evaluation design for making bias evidence reviewable in AI bills of materials.
