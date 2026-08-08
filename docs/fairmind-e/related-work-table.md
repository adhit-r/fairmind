# FairMind-E Related Work Comparison

FairMind-E is positioned as an assurance layer for environmental evidence in AI governance. It does not replace carbon calculators, carbon accounting standards, or legal compliance programs. Its contribution is to preserve evidence quality and connect environmental impact evidence to release decisions.

## Comparison Matrix

| Work or standard | Measures environmental impact? | Discloses environmental impact? | Treats evidence quality explicitly? | Links evidence to a decision gate? | Implication for FairMind-E |
| --- | --- | --- | --- | --- | --- |
| Green Software Foundation SCI for AI | Yes. Extends Software Carbon Intensity concepts to AI lifecycle measurement. | Yes. Produces a comparable AI carbon-intensity disclosure. | Partially. Measurement method and boundary matter, but FairMind-E still needs provenance and uncertainty fields. | No direct release gate. | Use as a measurement standard input; FairMind-E adds governance gating and weak-evidence findings. |
| ISO/IEC TR 20226:2025 | Yes. Catalogues environmental sustainability aspects and potential metrics across the AI system lifecycle. | Partially. Supports environmental documentation and metric selection. | Partially. It frames lifecycle evidence needs but does not define FairMind-E confidence scoring. | No direct release gate. | Use as lifecycle metric vocabulary and boundary guidance. |
| EU AI Act Annex XI(e) and Article 95 | Partially. Annex XI(e) requires known or estimated energy consumption for GPAI technical documentation; Article 95 supports voluntary sustainability KPIs. | Yes for covered GPAI documentation and voluntary codes. | Limited. The Act distinguishes known versus estimated energy but does not define provenance classes, uncertainty bands, or vendor caps. | No direct product-release gate. | FairMind-E can supply auditable energy/carbon evidence for documentation and voluntary KPI programs. |
| RBI FREE-AI Sutra 7 | Partially. Frames AI systems as secure, resilient, and energy efficient. | Not a measurement protocol. | Limited. It is a governance principle rather than a data-quality rubric. | No direct release gate. | Use as India-aligned governance framing for energy efficiency and sustainable adoption. |
| Tkachenko 2024, AI carbon footprint in banking risk management | Yes. Connects AI carbon footprint to banking risk-management frameworks. | Partially. Emphasizes compliance and risk-reporting context. | Limited. Does not separate categorical provenance from quantified uncertainty as a gate input. | Partially. Risk-management framing is decision relevant, but not a deterministic go/conditional/no-go gate. | Use for the banking-sector compliance motivation; FairMind-E operationalizes the evidence gate. |
| Llopis 2026, four-tier Scope 3 AI inference methodology | Yes. Defines a tiered estimation method for AI inference in Scope 3 Category 1 inventories. | Yes. Targets corporate GHG inventory reporting. | Yes, but for inventory precision tiers rather than FairMind-E release confidence. | No direct release gate. | Use for inference-accounting methodology and to compare FairMind-E confidence tiers against corporate inventory tiers. |
| CodeCarbon, EcoLogits, cloud telemetry, and manual estimates | Yes. Produce tool-estimated, provider-reported, metered, or manual energy/carbon estimates. | Usually yes as run logs, reports, or metadata exports. | Varies by tool and provider. | No direct release gate. | Treat each as an evidence source; never collapse source provenance and quantified uncertainty into one scalar. |
| FairMind-E | Ingests measured, tool-estimated, vendor-reported, manual, or unknown environmental evidence. | Yes. Stores dual location-based and market-based carbon plus confidence and reviewer state. | Yes. Provenance remains categorical, uncertainty remains numeric, vendor confidence is capped at 0.60, and unknown evidence is a finding. | Yes. The gate returns `go`, `conditional_go`, or `no_go`. | Contribution: environmental evidence assurance and release gating, not a new carbon calculator. |

## Claim Boundary

FairMind-E should claim that it makes environmental evidence reviewable and decision-linked. It should not claim that prior work ignores sustainability, that FairMind-E is itself a certified carbon accounting method, or that an environmental gate proves a system is sustainable.

## Source Anchors

- Green Software Foundation, SCI for AI: https://greensoftware.foundation/standards/sci-ai/
- Green Software Foundation, SCI for AI ratification article: https://greensoftware.foundation/articles/sci-ai-specification-ratified-standard-for-measuring-ai-emissions-across-the/
- ISO/IEC TR 20226:2025: https://www.iso.org/standard/86177.html
- EU AI Act, Regulation (EU) 2024/1689: https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ:L_202401689
- EU AI Act Article 95 text: https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-95
- Tkachenko 2024: https://arxiv.org/abs/2410.01818
- Llopis 2026: https://arxiv.org/abs/2606.10660
- RBI FREE-AI report mirror used for accessible text: https://www.medianama.com/wp-content/uploads/2025/08/Framework-for-Responsible-and-Ethical-Enablement-of-Artificial-Intelligence-FREE-AI-RBI-Report.pdf
