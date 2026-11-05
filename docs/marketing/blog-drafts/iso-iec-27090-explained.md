---
title: "ISO/IEC 27090 explained, threat by threat"
slug: iso-iec-27090-explained
status: draft
meta_title: "ISO 27090 explained, AI security threat by threat"
meta_description: "ISO 27090 gives guidance on security threats to AI systems. We take each named threat in turn, with example tests and OWASP and ATLAS IDs."
custom_excerpt: "ISO/IEC 27090 is security guidance for AI systems. This post walks through the threats public descriptions say it covers, the test evidence a team can produce for each, and how to add it to an ISO 27001 ISMS."
tags: [security, standards]
author: Adhithya Rajasekaran
target_term: "iso 27090"
last_checked: 2026-11-04
---

ISO/IEC 27090 is the newest ISO standard on securing AI systems. This post covers what it is, how it sits next to ISO/IEC 27001, 27002 and 42001, and the threats public descriptions say it addresses, with the test evidence a team can produce for each.

We have not read the licensed text and we do not quote it. Everything here about its content comes from ISO's public abstract and published third-party descriptions. Buy the standard from ISO or your national body and work from the normative wording before you write it into a policy or a Statement of Applicability.

## What the standard is and who it is for

The full title is "Cybersecurity, Artificial Intelligence, Addressing security threats and compromises to AI systems". It is a first edition from ISO/IEC JTC 1/SC 27, and public sources describe it as guidance on understanding, detecting and mitigating security threats specific to AI systems across their life cycle ([iso27001security.com](https://www.iso27001security.com/html/27090)). Nemko Digital describes the audience as organisations of any size that develop or use AI, and says the scope extends beyond generative AI and chatbots. The standard is about protecting AI systems themselves, and using AI to defend other technology falls outside it ([Nemko Digital](https://digital.nemko.com/news/isoiec-27090-published-as-new-ai-cybersecurity-standard)).

Sources disagree on how to describe its publication status. Nemko Digital reports that ISO's record confirms publication on 14 October 2026 ([Nemko Digital](https://digital.nemko.com/news/isoiec-27090-published-as-new-ai-cybersecurity-standard)). The ISO27001security site gives October 2026 and shows a last-updated date of 31 October 2026 ([iso27001security.com](https://www.iso27001security.com/html/27090)). When we checked on 4 November 2026, ISO's own catalogue pages, [iso.org/standard/27090](https://www.iso.org/standard/27090) and [iso.org/standard/56581.html](https://www.iso.org/standard/56581.html), appeared in search results as "Under publication", and both refused our automated fetch. Treat publication as reported and confirm the status in the ISO store before buying.

Nemko describes 27090 as security guidance and sets it apart from a new set of management-system requirements. It also says following the guidance does not guarantee protection against attacks, and that publication does not by itself establish compliance with legal obligations such as EU AI Act Article 15. None of the sources we read describe a certification scheme for 27090, so we would not expect an auditor to issue a certificate against it.

## How it relates to 27001, 27002, 42001 and 27091

| Standard | What it is | Role next to 27090 |
|---|---|---|
| ISO/IEC 27001 | Management-system requirements for information security | The ISMS that 27090 complements, per [Nemko](https://digital.nemko.com/news/isoiec-27090-published-as-new-ai-cybersecurity-standard). |
| ISO/IEC 27002 | Guidance on information security controls | General controls guidance. 27090 adds detail on threats to AI data, models and workflows. |
| ISO/IEC 42001 | Requirements for an AI management system | Covers organisational duties, risks and opportunities for AI. 27090 sits beside it as security guidance. See our [ISO 42001 page](https://fairmind.xyz/frameworks/iso-42001/). |
| ISO/IEC 27091 | AI privacy protection guidance | Reported at FDIS stage on [ISO's page](https://www.iso.org/standard/56582.html). We could not confirm a publication date. |

For an organisation that already runs 27001, 27090 is most useful as a threat reference for the AI-specific part of the existing security risk assessment. One public commentary adds that 27090 concentrates on deliberate, malicious attacks and largely leaves out accidents and insider threats ([iso27001security.com](https://www.iso27001security.com/html/27090)), so those still need their own entries in your risk register.

The same site says the document contains material on applying information security, types of compromise and mitigations, with annexes that map attacks to the AI life cycle and assets, describe AI versions of conventional attacks, and cover federated machine learning. It also says each named threat gets about a page covering consequences, detection and mitigation.

## The threats public descriptions name

Public descriptions say the standard covers at least a dozen threats. The ones named are poisoning of data and models, evasion, membership inference, model inversion, model stealing, prompt injection and output injection ([iso27001security.com](https://www.iso27001security.com/html/27090)), and Nemko singles out data poisoning and model theft. This post covers only those. The lifecycle stages, examples and tests below are our own judgement and do not come from the standard.

OWASP IDs come from the [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/) and the [OWASP Agentic Top 10](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/), and ATLAS IDs come from the [MITRE ATLAS](https://github.com/mitre-atlas/atlas-data) data.

### Poisoning of data and models

Poisoning means tampering with the data a model learns from, or with the model itself, so that its behaviour changes in ways the owner did not intend. Nemko notes that the risk compounds when operational data feeds retraining. A typical case is a public dataset you fine-tune on that contains planted records teaching the model a hidden trigger phrase. The exposure sits in data collection, training, fine-tuning and retraining.

Keep a provenance record for each dataset, a poisoning or backdoor scan of both the training set and the resulting model, and a trigger-probe test showing how the model behaves on suspected trigger inputs. The OWASP cross-reference is LLM04:2025, with ASI06 covering agent memory and context. In ATLAS the matching techniques are AML.T0020 (poison training data) and AML.T0018.000 (poison AI model).

### Evasion and model stealing

Evasion uses inputs crafted to make a model produce a wrong output at inference time, often through changes a human would not notice. A sticker pattern that makes a vision model misread a sign is one example, and a transaction shaped to slip past a fraud classifier is another. It happens in deployment and operation. The evidence is an adversarial test report recording the attack types used, the perturbation budget, and accuracy before and after, along with the thresholds your team accepted and who approved them. We found no OWASP LLM entry we would call a match, and the ATLAS techniques are AML.T0015 (evade AI model) and AML.T0043 (craft adversarial data).

Model stealing copies a model's behaviour or parameters, and it can be done through many queries that each look legitimate. A competitor might script thousands of API calls and train a look-alike model on your outputs. The exposure is in operation through the inference API, and in the storage and distribution of model files. A useful test measures how many queries it takes to reach a given fidelity against your own endpoint. Keep the result with your rate-limit configuration, query-pattern alerts and access logs for model artefacts. LLM10:2025 is the closest OWASP entry in our reading, and the ATLAS technique is AML.T0024.002 (extract AI model).

### Membership inference and model inversion

Both attacks work back from a model's responses to its training data, with the cause set during training and the attack happening in operation. Membership inference establishes whether a specific record was in the training set, for example whether a named patient appeared in the data behind a clinical model. Model inversion reconstructs training data, or sensitive attributes of it, from outputs, as when repeated queries to a face model rebuild a recognisable image of someone in the training set.

For membership inference, keep a test report comparing attack success against a random-guess baseline, with notes on mitigations such as regularisation or output limits. For inversion, the report should show what could be recovered and at what query cost, alongside a record of how confidence scores and output detail are exposed. Both map to LLM02:2025. The ATLAS IDs are AML.T0024.000 (infer training data membership) and AML.T0024.001 (invert AI model).

### Prompt injection and output injection

Prompt injection hides instructions in a language model's input to steer it away from what its operator intended. The instructions can arrive directly from a user or indirectly through a document, web page or tool result, as when a support bot summarises an email that tells it to forward the customer's history to an outside address. The exposure is in operation and integration, wherever the model reads untrusted content or calls tools. Keep the test suite result with attack categories, pass and fail counts, the model and prompt versions tested and the date, plus a record of what the model is permitted to do when an attack succeeds. It maps to LLM01:2025, to ASI01 for agents, and to ATLAS AML.T0051 (LLM prompt injection), which has direct and indirect variants.

Output injection travels in the opposite direction, with model output carrying a payload into whatever consumes it, such as a browser, a database or a shell. One example is a model returning markup that a web front end renders as live script. The exposure sits at the boundary between the model and downstream systems during integration and operation. The test log should show that model output goes through the same encoding, validation and parameterisation as any untrusted input, with failing cases fixed and retested. The OWASP entry is LLM05:2025. We found no clean ATLAS match and did not force one.

## Summary table

| Threat | Lifecycle stage | Example test | Related IDs |
|---|---|---|---|
| Poisoning (data, model) | Data, training, retraining | Poisoning or backdoor scan; trigger probes | LLM04:2025, ASI06, AML.T0020, AML.T0018.000 |
| Evasion | Operation | Adversarial test run with a set perturbation budget | AML.T0015, AML.T0043 |
| Model stealing | Operation, storage | Extraction-rate test against the endpoint | LLM10:2025, AML.T0024.002 |
| Membership inference | Training, operation | Attack success against a random baseline | LLM02:2025, AML.T0024.000 |
| Model inversion | Training, operation | Reconstruction test with query cost | LLM02:2025, AML.T0024.001 |
| Prompt injection | Operation, integration | Injection suite, direct and indirect | LLM01:2025, ASI01, AML.T0051 |
| Output injection | Integration | Downstream sink test with hostile output | LLM05:2025 |

## Adding 27090 to an existing ISMS

None of this needs a new management system. These steps fit the ISMS you already run.

1. Add AI assets to the risk register as their own entries, covering training data, models, prompts, retrieval stores and tool permissions. For each entry, record which of the threats above apply, the likelihood and impact, and the owner.
2. For each risk you treat, attach the matching test report with the model version and date. Retest when the model, data or prompt changes.
3. In the Statement of Applicability, 27090 does not change your 27001 control set by itself. Use it as a reference when you justify why existing controls such as access control, logging and supplier management are sufficient for AI assets, and write that reasoning yourself, without citing 27090 as a control catalogue.
4. If you use a hosted model or third-party data, ask the supplier which of these threats they test for and what they will share. Record gaps as accepted risks or as actions.
5. Report AI threat test coverage and open findings in the management review pack alongside other security metrics.

If your organisation runs ISO/IEC 42001, link the same evidence to its risk processes. Our [ISO 42001 page](https://fairmind.xyz/frameworks/iso-42001/) covers how that standard differs.

## About FairMind

FairMind is an agentic AI governance platform with 90 governance workflows and 109 evaluations across 51 frameworks. Its 53 security evaluations cover agents (such as MCP permissions and kill switches), LLM apps and RAG (such as prompt injection), and models and data (such as membership inference and backdoors). Each evaluator declares its validation status, and results are stored as Evidence Passports with integrity hashes and reviewer decisions behind a human approval gate on every workflow. We do not claim FairMind maps to ISO/IEC 27090, and no tool makes a system compliant with it. [Request access](https://fairmind.xyz/request-access?utm_source=blog&utm_medium=post&utm_campaign=iso-iec-27090-explained) if you want to see how the evidence is recorded.

## FAQ

**Can we get certified to ISO/IEC 27090?**
Not as far as public sources show. [Nemko](https://digital.nemko.com/news/isoiec-27090-published-as-new-ai-cybersecurity-standard) describes it as guidance and distinguishes it from management-system requirements, and we found no certification scheme described for 27090.

**Does it replace ISO/IEC 27001 or 27002?**
No. Public descriptions say it complements both, so you keep your ISMS and add AI-specific threat knowledge to the risk assessment.

**Does it cover safety, bias or hallucination?**
Reportedly not as a focus. Public commentary says it concentrates on deliberate, malicious attacks and largely excludes accidental threats. Cover safety, bias and hallucination elsewhere in your risk process.

**Does following it satisfy the EU AI Act?**
Nemko states that publication of the standard does not by itself establish compliance with legal obligations such as EU AI Act Article 15. Take legal advice on your own duties.

## Sources
- [ISO/IEC 27090 published as new AI cybersecurity standard (Nemko Digital)](https://digital.nemko.com/news/isoiec-27090-published-as-new-ai-cybersecurity-standard). Reported 14 October 2026 publication, scope, model theft and data poisoning, relationship to 27001, 27002 and 42001, no compliance by itself.
- [ISO/IEC 27090 (iso27001security.com)](https://www.iso27001security.com/html/27090). October 2026 publication, abstract, named threats, structure description, commentary on scope limits.
- [ISO catalogue, iso.org/standard/27090](https://www.iso.org/standard/27090). Appeared as "Under publication" in search results on 4 November 2026.
- [ISO catalogue, iso.org/standard/56581.html](https://www.iso.org/standard/56581.html). Same status in search results.
- [ISO/IEC FDIS 27091 (ISO)](https://www.iso.org/standard/56582.html). AI privacy protection guidance shown at final draft stage.
- [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/). LLM01 to LLM10 IDs and titles.
- [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/). The agentic list; ASI IDs confirmed via secondary summaries such as [Giskard](https://www.giskard.ai/knowledge/owasp-top-10-for-agentic-application-2026).
- [MITRE ATLAS data repository](https://github.com/mitre-atlas/atlas-data). Technique and tactic IDs used in the cross-references.

<!-- REVIEWER NOTES (not for publication)
- ISO status: iso.org/standard/27090 and /56581.html returned HTTP 403 to WebFetch. The "Under publication" status comes from web search result titles only, not from reading the pages. Re-check manually before publishing. Nemko says ISO's record confirms 14 Oct 2026; I could not verify that from ISO. The brief's "BSI edition dated 31 Oct 2026" was NOT found; the 31 Oct 2026 I found is the "last updated" date on iso27001security.com, which I cite as such. The Nemko article is itself dated 30 Oct 2026.
- Sources disagree on precision: Nemko gives 14 Oct 2026, iso27001security gives "October 2026". Nemko says 56 pages; not used.
- The structure description (main clauses, three annexes, "about a page per threat", "at least a dozen threats") is from iso27001security.com only. I deliberately gave no clause numbers or titles. Treat as unverified.
- Threat list is the seven named on iso27001security.com (poisoning of data and model, evasion, membership inference, model inversion, model stealing, prompt injection, output injection). The other reported threats ("at least a dozen") are unknown to me.
- "Not certifiable": no source says this explicitly. Nemko calls it guidance and not management-system requirements and does not mention certification. The post says "as far as public sources show". The FAQ answer on certification rests on the same Nemko description; no source states "not certifiable" outright.
- 27091: ISO page shows FDIS per search summary (fetch not done directly); some mirrors show DIS. No publication date found. The post says unconfirmed.
- EU AI Act Article 15 reference is via Nemko; I did not read the Act. The post only says Nemko states publication does not by itself establish compliance.
- Commentary that 27090 excludes accidental and insider threats and "does not cover safety, bias or hallucination" (FAQ): the exclusion of accidental and insider threats is from iso27001security.com commentary. That safety, bias and hallucination fall outside is my inference from that commentary, hedged with "Reportedly".
- All lifecycle-stage assignments, example tests, evidence artefacts, and the ISMS integration steps are my own judgement, not from the standard. The post says so once; consider repeating near the table.
- OWASP mappings that are my judgement: model stealing to LLM10:2025 (I believe 2025 folded model extraction into Unbounded Consumption; I did not verify the text in this session); membership inference and model inversion to LLM02:2025 (Sensitive Information Disclosure); poisoning to LLM04:2025 and ASI06; output injection to LLM05:2025. Evasion and output injection have no ATLAS/OWASP match I was comfortable with, flagged in the post.
- OWASP LLM IDs/titles verified on genai.owasp.org/llm-top-10. ASI IDs were NOT verified against the primary document (the OWASP page did not list them); they come from secondary summaries (Giskard, search summary). Verify ASI01 and ASI06 against the OWASP PDF.
- ATLAS IDs verified against mitre-atlas/atlas-data ATLAS.yaml (main branch, fetched 4 Nov 2026): AML.T0020, T0018.000, T0015, T0043, T0024.000/.001/.002, T0051. The post cites no tactic IDs; the data shows current tactic names such as "AI Model Access" and "AI Attack Staging", which differ from older ATLAS naming ("ML Model Access"), so avoid older names if tactics are added.
- FairMind counts (90, 109, 51, 53) and descriptions are from the brief, not independently checked against the repo.
- The ISO 42001 link (fairmind.xyz/frameworks/iso-42001/) was not checked for being live.
- Rewrite (5 Nov 2026): per-threat H3s merged into four grouped H3s (poisoning; evasion and model stealing; membership inference and model inversion; prompt and output injection). Bold "What it is / Example / Evidence" labels replaced with prose. Content per threat unchanged.
- Rewrite: the evasion evidence is now called an "adversarial test report"; the old wording used a word on the house banned list. Check the term still reads correctly to ML readers.
- Rewrite: "No auditor can issue a 27090 certificate" softened to "we would not expect an auditor to issue a certificate against it", to match the "no source says not certifiable" note above.
- Rewrite: colon removed from the meta title; the meta description now contains the literal target term "ISO 27090" (the old one only had "ISO/IEC 27090"). Check lengths.
- Rewrite: FairMind paragraph condensed; the examples tool least privilege, out-of-scope actions, jailbreaks and prompt leakage, and the four evaluator status labels (validated, external provider, metadata only, not yet available), were dropped for length only. Restore if wanted.
- Rewrite: source list descriptions now follow the link after a full stop instead of an em dash.
-->
