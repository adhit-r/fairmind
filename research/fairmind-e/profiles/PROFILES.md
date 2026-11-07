# FairMind-E Expert-Panel Profile Pack (M6)

Twelve synthetic AI-system environmental assessments for independent expert
rating. Every profile is fictional; names, figures, and documents do not refer
to real organisations. Do not discuss profiles with other raters until your
ratings are submitted.

## Rating task

For each profile assigned to you on the panel schedule, record on the response
form:

1. Release recommendation: `go`, `conditional_go`, or `no_go`.
2. Impact risk tier: `low`, `medium`, or `high`.
3. Evidence confidence band: `measured`, `estimated`, or `unknown`.
4. Approval blocking: `yes` if you would withhold deployment approval in the
   submission's current state, otherwise `no`.
5. A short free-text rationale (one to three sentences).

Judge each submission exactly as presented: the declared boundary, metrics,
evidence provenance, mitigations, exceptions, and disclosures are everything
the review board would see.

---

## P01: KisanScore agri-credit risk model retraining

KisanScore v3 is the crop-season credit risk model of a Pune-based non-banking financial company that lends to smallholder farmers across Maharashtra and Madhya Pradesh. The model is a gradient-boosted tree ensemble trained on 38 million historical repayment records, mandi price feeds, and district-level rainfall data, and it prices roughly 400,000 loan applications each season.

The quarterly retraining run executes on the company's own eight-node CPU cluster in its Pune data centre. Rack-level PDU meters and per-socket RAPL counters were logged for the full run, and western regional grid emission factors were applied to the metered kilowatt-hours. Market-based figures reflect the renewable energy certificates the lender retires against its data-centre load.

The submission covers the complete hyperparameter search and final fit for the 2026 kharif-season model. Feature-store serving, training-data storage, and the loan officers' scoring interface sit outside the declared boundary.

### Assessment submission

- System id: `kisanscore-agri-credit-v3`
- Lifecycle phase: training
- Functional unit: training_run
- Assessment period: 2026-04-07 to 2026-04-11
- Boundary: Quarterly retraining of the KisanScore v3 gradient-boosted ensemble, including the hyperparameter search and final fit, on the lender's Pune CPU cluster.
  - Includes: hyperparameter search; final model fit; cooling overhead via PUE
  - Excludes: feature-store serving; training-data storage; loan-officer scoring interface
- Declared evidence provenance: measured (rack PDU meters and per-socket RAPL counters)
- Self-reported confidence score: 0.92
- Reported uncertainty: 6 percent
- Intensity vs approved baseline: 0.94

| Metric | Value |
| --- | ---: |
| Total energy (kWh) | 54 |
| Location-based carbon (kgCO2e) | 38.3 |
| Market-based carbon (kgCO2e) | 34.6 |
| Location grid intensity (gCO2e/kWh) | 710 |
| Market grid intensity (gCO2e/kWh) | 640 |
| Carbon intensity basis | average |
| Power usage effectiveness (PUE) | 1.6 |

- Documented mitigations: none declared
- Exception on file: none
- Disclosed offsets or credits: none
- Evidence references: `pdu-export-2026q2.csv`, `rapl-log-kisanscore-v3.parquet`, `western-grid-factors-2026.pdf`

---

## P02: LexRetrieve statute and case-law RAG search

LexRetrieve is the retrieval service behind a Dublin-based legal research product used by law firms in Ireland and the Netherlands. Each query embeds the user question with a compact bi-encoder, retrieves candidate passages from a statute and case-law index, and returns re-ranked citations. Roughly twelve million queries were served in the June 2026 window.

Engineering instrumented the retrieval pods with CodeCarbon, which sampled node power and applied Irish grid intensity for the location figure and the provider's green-tariff residual mix for the market figure. Tool estimates were cross-checked against pod CPU-seconds; the residual uncertainty is dominated by shared-node attribution.

The declared boundary covers embedding, index search, and re-ranking for production queries. The nightly index rebuild is assessed separately and is excluded here.

### Assessment submission

- System id: `lexretrieve-rag-search`
- Lifecycle phase: inference
- Functional unit: 1000_requests
- Assessment period: 2026-06-01 to 2026-06-30
- Boundary: Production query path of the LexRetrieve service: query embedding, index search, and re-ranking for the June 2026 window (about 12 million queries).
  - Includes: query embedding; index search; re-ranking
  - Excludes: nightly index rebuild; document ingestion pipeline
- Declared evidence provenance: tool_estimated (CodeCarbon 2.5 on the retrieval pods)
- Self-reported confidence score: 0.66
- Reported uncertainty: 22 percent
- Intensity vs approved baseline: 0.88

| Metric | Value |
| --- | ---: |
| Total energy (kWh) | 16.5 |
| Location-based carbon (kgCO2e) | 4.8 |
| Market-based carbon (kgCO2e) | 2 |
| Efficiency (kgCO2e per 1000 requests) | 0.0004 |
| Location grid intensity (gCO2e/kWh) | 290 |
| Market grid intensity (gCO2e/kWh) | 120 |
| Carbon intensity basis | average |
| Power usage effectiveness (PUE) | 1.2 |

- Documented mitigations: none declared
- Exception on file: none
- Disclosed offsets or credits: none
- Evidence references: `codecarbon-emissions-2026-06.csv`, `green-tariff-residual-mix-2026.pdf`

---

## P03: TalentSift resume screening ranker

TalentSift ranks incoming resumes for enterprise recruiting teams at a Denver-based HR software vendor. A distilled transformer scores each resume against the job requisition; about eight million screening requests were processed in the June 2026 window across two US production regions.

No energy instrumentation exists yet. A platform engineer produced a spreadsheet estimate from model FLOPs, an assumed accelerator utilisation of 40 percent, and a national average grid factor. The team did not compute a market-based figure, and although instrumentation options are being discussed, no owner or target date has been attached to any of them.

### Assessment submission

- System id: `talentsift-resume-ranker`
- Lifecycle phase: inference
- Functional unit: 1000_requests
- Assessment period: 2026-06-01 to 2026-06-30
- Boundary: Resume scoring API across the two US production regions for the June 2026 window (about 8 million screening requests).
  - Includes: resume scoring API
  - Excludes: model retraining; recruiter web application
  - Assumptions: National average grid factor; accelerator utilisation assumed at 40 percent.
- Declared evidence provenance: manual (engineering FLOP worksheet)
- Self-reported confidence score: 0.3
- Reported uncertainty: 45 percent
- Intensity vs approved baseline: 1.05
- Declared mitigation readiness: missing

| Metric | Value |
| --- | ---: |
| Total energy (kWh) | 12.6 |
| Location-based carbon (kgCO2e) | 4.8 |
| Efficiency (kgCO2e per 1000 requests) | 0.0006 |
| Location grid intensity (gCO2e/kWh) | 380 |
| Carbon intensity basis | average |

- Documented mitigations: none declared
- Exception on file: none
- Disclosed offsets or credits: none
- Evidence references: `flop-estimate-worksheet-v2.xlsx`

---

## P04: TriageAssist clinical intake fine-tune

TriageAssist is a clinical intake assistant for a hospital network that operates 14 facilities across Telangana and Andhra Pradesh. The network fine-tuned an open 8-billion-parameter model on de-identified triage notes and nurse-line transcripts so the assistant can suggest acuity levels and department routing in English and Telugu.

The two-week fine-tune ran on a metered eight-GPU cluster in the network's Hyderabad facility. Rack PDU energy logs supplied kilowatt-hours, southern regional grid factors supplied the location figure, and market figures net off the facility's partial renewable certificates. The AI platform team has signed a dated plan to move the next fine-tuning cycle to the Bengaluru colocation covered by a solar power purchase agreement.

### Assessment submission

- System id: `triageassist-clinical-finetune`
- Lifecycle phase: fine_tune
- Functional unit: fine_tune_run
- Assessment period: 2026-05-04 to 2026-05-18
- Boundary: Supervised fine-tune of an open 8B model on de-identified triage notes on the Hyderabad eight-GPU cluster, including evaluation passes.
  - Includes: fine-tuning epochs; evaluation passes
  - Excludes: base-model pretraining; inference serving; annotation tooling
- Declared evidence provenance: measured (rack PDU energy logs)
- Self-reported confidence score: 0.9
- Reported uncertainty: 8 percent
- Intensity vs approved baseline: 1.1

| Metric | Value |
| --- | ---: |
| Total energy (kWh) | 1875 |
| Location-based carbon (kgCO2e) | 1350 |
| Market-based carbon (kgCO2e) | 1143.8 |
| Location grid intensity (gCO2e/kWh) | 720 |
| Market grid intensity (gCO2e/kWh) | 610 |
| Carbon intensity basis | average |
| Power usage effectiveness (PUE) | 1.5 |

- Documented mitigations:
  - Move the next fine-tuning cycle to the Bengaluru colocation covered by the solar power purchase agreement and re-run this assessment on metered evidence. | owner: Head of Clinical AI Platform | target date: 2026-10-15 | expected reduction: 35 percent | status: proposed
- Exception on file: none
- Disclosed offsets or credits: none
- Evidence references: `pdu-energy-log-2026-05.csv`, `southern-grid-factors-2026.pdf`, `solar-ppa-migration-plan.pdf`

---

## P05: UPI fraud scoring service

A Mumbai payments company scores UPI transactions for fraud in real time with a gradient-boosted ensemble backed by a graph feature service. The June 2026 window covered about 45 million scoring requests across two cloud regions during peak festival-season traffic.

Environmental figures come from the cloud provider's sustainability dashboard, which reports location-based and market-based carbon for the tagged workloads but does not expose the underlying kilowatt-hours, and its methodology is not independently auditable. The platform team claims high confidence in the numbers, but the evidence class remains vendor-reported.

A dated migration of the scoring fleet to the provider's hydro-backed region, with the metered energy export API enabled, is committed for November and is already in progress.

### Assessment submission

- System id: `upi-fraud-scoring-service`
- Lifecycle phase: inference
- Functional unit: 1000_requests
- Assessment period: 2026-06-01 to 2026-06-30
- Boundary: Real-time UPI fraud scoring across two production cloud regions for the June 2026 window (about 45 million requests), as tagged in the provider sustainability dashboard.
  - Includes: scoring API; graph feature service
  - Excludes: model training; case-review tooling; data warehouse
- Declared evidence provenance: vendor_reported (cloud provider sustainability dashboard)
- Self-reported confidence score: 0.88
- Reported uncertainty: 30 percent
- Intensity vs approved baseline: 1.02

| Metric | Value |
| --- | ---: |
| Location-based carbon (kgCO2e) | 171 |
| Market-based carbon (kgCO2e) | 149 |
| Efficiency (kgCO2e per 1000 requests) | 0.0038 |
| Carbon intensity basis | average |

- Documented mitigations:
  - Migrate the scoring fleet to the provider's hydro-backed region and enable the metered energy export API for direct kilowatt-hour evidence. | owner: FinCrime Platform Lead | target date: 2026-11-30 | expected reduction: 40 percent | status: in_progress
- Exception on file: none
- Disclosed offsets or credits: none
- Evidence references: `provider-sustainability-dashboard-2026-06.pdf`, `hydro-region-migration-ticket.pdf`

---

## P06: Workspace chat assistant serving

A productivity software company embeds a conversational assistant in its flagship product for drafting, summarising, and answering workspace questions. The assistant serves a 70-billion-parameter model behind a token-streaming API; June 2026 traffic was about 2.1 billion generated tokens across three serving regions.

The sustainability lead assembled the June estimate manually from published per-token energy figures for comparable 70B-class deployments, an assumed PUE of 1.3, and a blended grid factor across the three regions. There is no telemetry from the serving fleet, and billing data cannot be decomposed to the assistant workload. The team acknowledges the figure could move materially in either direction.

### Assessment submission

- System id: `workspace-chat-assistant`
- Lifecycle phase: llm_inference
- Functional unit: 1m_tokens
- Assessment period: 2026-06-01 to 2026-06-30
- Boundary: Token generation for the embedded workspace assistant across three serving regions in June 2026 (about 2.1 billion generated tokens).
  - Includes: token generation
  - Excludes: model training; search indexing; client applications
  - Assumptions: Per-token energy from published figures for comparable 70B-class deployments; PUE assumed at 1.3; blended grid factor across regions.
- Declared evidence provenance: manual (sustainability-team estimate from published per-token figures)
- Self-reported confidence score: 0.28
- Reported uncertainty: 40 percent
- Intensity vs approved baseline: 1.18

| Metric | Value |
| --- | ---: |
| Total energy (kWh) | 23000 |
| Location-based carbon (kgCO2e) | 9660 |
| Market-based carbon (kgCO2e) | 8740 |
| Efficiency (kgCO2e per 1M tokens) | 4.6 |
| Location grid intensity (gCO2e/kWh) | 420 |
| Market grid intensity (gCO2e/kWh) | 380 |
| Carbon intensity basis | average |
| Power usage effectiveness (PUE) | 1.3 |

- Documented mitigations: none declared
- Exception on file: none
- Disclosed offsets or credits: none
- Evidence references: `assistant-footprint-estimate-2026-06.xlsx`

---

## P07: Biomedical domain LLM pretraining run

A US biomedical research laboratory pretrained a 13-billion-parameter domain language model on curated literature, clinical guidelines, and licensed textbook corpora to support downstream extraction and evidence-synthesis tools. The run processed roughly 500 billion tokens over six weeks on the laboratory's HPC partition.

Node-level IPMI power telemetry and facility PUE were logged for the full run. Hourly average regional grid intensity supplied the location figure, and the laboratory's wind power purchase agreement is reflected in the market figure. Operations has signed a dated plan to place the next pretraining cycle in the overnight low-carbon window using the carbon-aware scheduler and to publish per-checkpoint energy budgets.

### Assessment submission

- System id: `biomed-domain-llm-pretrain`
- Lifecycle phase: training
- Functional unit: training_run
- Assessment period: 2026-04-01 to 2026-05-15
- Boundary: Full pretraining run of the 13B biomedical language model on the laboratory HPC partition, including checkpoint evaluation jobs.
  - Includes: pretraining; checkpoint evaluation jobs
  - Excludes: corpus licensing and preprocessing; downstream fine-tunes
- Declared evidence provenance: measured (node IPMI power telemetry)
- Self-reported confidence score: 0.95
- Reported uncertainty: 5 percent
- Intensity vs approved baseline: 1.12

| Metric | Value |
| --- | ---: |
| Total energy (kWh) | 152000 |
| Location-based carbon (kgCO2e) | 62320 |
| Market-based carbon (kgCO2e) | 33440 |
| Location grid intensity (gCO2e/kWh) | 410 |
| Market grid intensity (gCO2e/kWh) | 220 |
| Carbon intensity basis | average |
| Power usage effectiveness (PUE) | 1.15 |
| Renewable energy share (percent) | 45 |

- Documented mitigations:
  - Schedule the next pretraining cycle in the overnight low-carbon window using the carbon-aware scheduler and publish per-checkpoint energy budgets. | owner: HPC Operations Director | target date: 2026-09-30 | expected reduction: 25 percent | status: proposed
- Exception on file: none
- Disclosed offsets or credits: none
- Evidence references: `ipmi-telemetry-2026q2.parquet`, `hourly-grid-intensity-2026q2.csv`, `wind-ppa-contract-summary.pdf`

---

## P08: Indic multilingual LLM continued pretraining

A Bengaluru startup ran continued pretraining of a 7-billion-parameter multilingual model across ten Indic languages, positioning it for government-service chat and voice interfaces. The five-week run used a rented GPU cluster located in a coal-heavy grid region.

Energy was not metered. The team reconstructed consumption with a green-algorithms style calculator from scheduler GPU-hours, card TDP, and an assumed 65 percent utilisation profile, then applied national grid factors. The startup discloses retired verified carbon units covering roughly the estimated footprint and treats that purchase as its primary environmental answer. Mitigation for the next run is described as planned, but no owner or target date has been documented.

### Assessment submission

- System id: `indic-multilingual-llm-cpt`
- Lifecycle phase: training
- Functional unit: training_run
- Assessment period: 2026-05-01 to 2026-06-05
- Boundary: Continued pretraining of the 7B multilingual model across ten Indic languages on a rented GPU cluster.
  - Includes: continued pretraining
  - Excludes: base checkpoint training; instruction tuning; serving
  - Assumptions: GPU-hours and TDP reconstructed from scheduler logs; utilisation assumed at 65 percent.
- Declared evidence provenance: tool_estimated (green-algorithms style calculator over scheduler logs)
- Self-reported confidence score: 0.64
- Reported uncertainty: 24 percent
- Intensity vs approved baseline: 1.2
- Declared mitigation readiness: planned

| Metric | Value |
| --- | ---: |
| Total energy (kWh) | 40600 |
| Location-based carbon (kgCO2e) | 28623 |
| Market-based carbon (kgCO2e) | 28420 |
| Location grid intensity (gCO2e/kWh) | 705 |
| Market grid intensity (gCO2e/kWh) | 700 |
| Carbon intensity basis | average |

- Documented mitigations: none declared
- Exception on file: none
- Disclosed offsets or credits: retired_kg_co2e: 30000
- Evidence references: `scheduler-gpu-hours-2026-05.csv`, `calculator-worksheet-cpt.pdf`, `vcu-retirement-certificate.pdf`

---

## P09: Third-party document-intelligence API

An enterprise contracts team routes scanned agreements through a third-party document-intelligence API that performs OCR and generates structured summaries with a large generative model. About 600 million generated tokens were consumed in June 2026, and the vendor operates the model as a managed black box across undisclosed regions.

The vendor declined to disclose energy, carbon, hardware, or region information, citing commercial confidentiality, and publishes no sustainability documentation for the service. The efficiency figure on file is the team's own worst-case screening replication using an open model of assumed similar size on previous-generation accelerators; the vendor has neither confirmed nor corrected it. No uncertainty quantification accompanies the submission because there is no disclosure to quantify.

### Assessment submission

- System id: `thirdparty-document-intelligence`
- Lifecycle phase: llm_inference
- Functional unit: 1m_tokens
- Assessment period: 2026-06-01 to 2026-06-30
- Boundary: Contract OCR and structured summarisation through the managed third-party API for the June 2026 window (about 600 million generated tokens).
  - Includes: vendor-hosted OCR and summarisation
  - Excludes: in-house retrieval and review tooling
  - Assumptions: Efficiency figure is the team's worst-case screening replication with an open model of assumed similar size; the vendor has not confirmed it.
- Declared evidence provenance: undisclosed
- Self-reported confidence score: not provided
- Reported uncertainty: not provided
- Intensity vs approved baseline: not provided

| Metric | Value |
| --- | ---: |
| Efficiency (kgCO2e per 1M tokens) | 18 |

- Documented mitigations: none declared
- Exception on file: none
- Disclosed offsets or credits: none
- Notes: Vendor declined energy, carbon, hardware, and region disclosure citing commercial confidentiality.

---

## P10: Digital lending pre-qualification scorer

A digital lending non-banking financial company pre-qualifies personal-loan applicants with a logistic scorecard refined by a small gradient-boosted model. The Chennai region deployment scored about six million applications in June 2026.

The platform team estimated energy from container CPU allocation and the southern grid factor in a documented worksheet; no measurement tooling is deployed yet. Unlike earlier submissions from the same team, this one carries a dated instrumentation commitment: CodeCarbon on the scoring containers, with a re-submission on tool-estimated evidence by mid-September.

### Assessment submission

- System id: `lending-prequal-scorer`
- Lifecycle phase: inference
- Functional unit: 1000_requests
- Assessment period: 2026-06-01 to 2026-06-30
- Boundary: Personal-loan pre-qualification scoring in the Chennai region for the June 2026 window (about 6 million applications).
  - Includes: scoring containers
  - Excludes: bureau data ingestion; collections analytics
  - Assumptions: Energy estimated from container CPU allocation and the southern grid factor.
- Declared evidence provenance: manual (container CPU allocation worksheet)
- Self-reported confidence score: 0.32
- Reported uncertainty: 42 percent
- Intensity vs approved baseline: 0.96

| Metric | Value |
| --- | ---: |
| Total energy (kWh) | 4.2 |
| Location-based carbon (kgCO2e) | 3 |
| Market-based carbon (kgCO2e) | 3 |
| Efficiency (kgCO2e per 1000 requests) | 0.0005 |
| Location grid intensity (gCO2e/kWh) | 710 |
| Market grid intensity (gCO2e/kWh) | 710 |
| Carbon intensity basis | average |

- Documented mitigations:
  - Deploy CodeCarbon instrumentation on the scoring containers and re-submit this assessment on tool-estimated evidence. | owner: Credit Platform Engineering Manager | target date: 2026-09-15 | status: in_progress
- Exception on file: none
- Disclosed offsets or credits: none
- Evidence references: `cpu-allocation-worksheet-2026-06.xlsx`, `instrumentation-rollout-plan.pdf`

---

## P11: Marketplace search re-ranking LLM serving

A global marketplace re-ranks search results with a large language model that scores the candidate set for every query. The Singapore and Frankfurt fleets consumed about 2.4 billion scored tokens in June 2026, and relevance gains from the ranker directly drive gross merchandise volume.

The serving fleet is fully metered: smart-PDU telemetry is aggregated per model endpoint, and location and market figures are computed from hourly grid data. Per-token carbon is high because every query fans out to score dozens of candidates on previous-generation accelerators.

Rather than a dated efficiency mitigation, the VP of Platform Engineering signed a formal exception recording the contracted fourth-quarter migration to next-generation hardware, with quarterly review until the exception expires at year end.

### Assessment submission

- System id: `marketplace-reranker-llm`
- Lifecycle phase: llm_inference
- Functional unit: 1m_tokens
- Assessment period: 2026-06-01 to 2026-06-30
- Boundary: LLM re-ranking of search candidate sets on the Singapore and Frankfurt fleets for the June 2026 window (about 2.4 billion scored tokens).
  - Includes: candidate-set scoring
  - Excludes: first-stage retrieval; catalogue indexing; model training
- Declared evidence provenance: measured (smart-PDU telemetry per model endpoint)
- Self-reported confidence score: 0.88
- Reported uncertainty: 7 percent
- Intensity vs approved baseline: 1.22

| Metric | Value |
| --- | ---: |
| Total energy (kWh) | 66900 |
| Location-based carbon (kgCO2e) | 34788 |
| Market-based carbon (kgCO2e) | 32112 |
| Efficiency (kgCO2e per 1M tokens) | 14.5 |
| Location grid intensity (gCO2e/kWh) | 520 |
| Market grid intensity (gCO2e/kWh) | 480 |
| Carbon intensity basis | average |
| Renewable energy share (percent) | 20 |

- Documented mitigations: none declared
- Exception on file: owner: VP Platform Engineering | expiry: 2026-12-31 | rationale: Accelerator fleet migration to next-generation hardware is contracted for Q4 2026; interim operation approved with quarterly review.
- Disclosed offsets or credits: none
- Evidence references: `smart-pdu-endpoint-telemetry-2026-06.parquet`, `hourly-grid-data-sg-fra.csv`, `exception-record-vp-platform.pdf`

---

## P12: Enterprise semantic embedding pipeline

A Toronto analytics vendor maintains semantic search over customer document stores. A nightly pipeline embeds new and changed content with a 350-million-parameter encoder, processing about 38 million embedding requests in June 2026 across two regions, many of them long multi-page documents.

Instrumentation attached to the inference gateway estimates per-request energy and carbon with documented assumptions, in the style of EcoLogits. Off-peak batching and a distilled encoder are both under discussion as reduction options, but neither has an owner or a target date, and no exception has been requested from the review board.

### Assessment submission

- System id: `semantic-embedding-pipeline`
- Lifecycle phase: inference
- Functional unit: 1000_requests
- Assessment period: 2026-06-01 to 2026-06-30
- Boundary: Nightly and incremental embedding of customer document stores with the 350M encoder across two regions for the June 2026 window (about 38 million embedding requests).
  - Includes: embedding requests; gateway preprocessing
  - Excludes: vector-store serving; retrieval API; encoder training
- Declared evidence provenance: tool_estimated (EcoLogits-style gateway instrumentation)
- Self-reported confidence score: 0.62
- Reported uncertainty: 20 percent
- Intensity vs approved baseline: 1.08
- Declared mitigation readiness: planned

| Metric | Value |
| --- | ---: |
| Total energy (kWh) | 338 |
| Location-based carbon (kgCO2e) | 152.1 |
| Market-based carbon (kgCO2e) | 135.2 |
| Efficiency (kgCO2e per 1000 requests) | 0.004 |
| Location grid intensity (gCO2e/kWh) | 450 |
| Market grid intensity (gCO2e/kWh) | 400 |
| Carbon intensity basis | average |
| Power usage effectiveness (PUE) | 1.25 |

- Documented mitigations: none declared
- Exception on file: none
- Disclosed offsets or credits: none
- Evidence references: `gateway-instrumentation-export-2026-06.csv`, `estimation-assumptions-note.pdf`
