---
title: "Why an AI test result needs a chain of custody"
slug: chain-of-custody-for-ai
status: draft
meta_title: "AI audit evidence needs a chain of custody"
meta_description: "What an AI audit evidence record must hold, how test results go stale, and why a named person still approves each framework mapping."
custom_excerpt: "In forensics, evidence with a broken chain of custody can be excluded. We think AI test results should be held to the same standard, and this post sets out what the record has to contain."
tags: [governance, assurance, manifesto]
author: Adhithya Rajasekaran
target_term: "ai audit evidence"
last_checked: 2026-11-04
---

A court relies on physical evidence only when its chain of custody holds up, meaning a record of who collected it, when, how it was stored and who handled it next. If one link is missing, the evidence can be excluded however convincing it looks.

Most AI governance work has yet to adopt that standard. Teams preparing for an audit usually hand over a screenshot of a dashboard, a spreadsheet of scores or a readiness percentage, and none of those can answer the first question a careful auditor asks, which is what exactly was tested and whether you can show it.

This blog is called Chain of Custody because answering that question is the work. We write about AI safety, governance and security with the evidence attached, and this first post explains what we mean.

## What a test result needs before anyone can rely on it

Take a fairness score of 0.92. To rely on it you need the model and version tested, the dataset or prompt set and how it was chosen, and the metric, tool and tool version. You also need the pass threshold and whether it was fixed before the run, where the raw output is and whether it has changed, what the test could not see, and who reviewed it and what they decided. Without that, nobody outside the team can check the number.

Governance frameworks already ask for this kind of record. The EU AI Act requires technical documentation for high-risk systems under [Article 11 and Annex IV](https://eur-lex.europa.eu/eli/reg/2024/1689/oj) and automatic logging of events under [Article 12](https://eur-lex.europa.eu/eli/reg/2024/1689/oj). [ISO/IEC 42001](https://fairmind.xyz/frameworks/iso-42001/) treats documented information as a management system requirement, and the [NIST AI RMF](https://fairmind.xyz/frameworks/nist-ai-rmf/) gives a whole function, Measure, to testing and tracking AI risk. None of them would accept a green dashboard as evidence.

## What a chain-of-custody record holds

We call the unit of record an Evidence Passport. Each field below closes a gap an auditor would otherwise probe.

| Field | Why it matters |
|---|---|
| Subject identity | The exact model, dataset, prompt or agent version tested, identified by a hash rather than a name. |
| Evaluator and metric version | Tools change their maths between releases, so the same model can score differently. |
| Threshold and its source | A pass mark chosen after seeing the result defeats the purpose of the test, so record where the threshold came from. |
| Scope | Which slices, languages, prompts or tools were covered, and which were left out. |
| Runtime environment | Hardware, libraries and settings that can change the outcome. |
| Raw artifact and integrity digest | The original output, with a hash so anyone can confirm it has not been edited. |
| Result and uncertainty | The number, with its confidence interval or sample size. |
| Limitations | What this test cannot show, written down explicitly. |
| Reviewer decision | Who accepted, rejected or accepted the risk, when, and why. |
| Remediation and rerun | What changed afterwards, and the new result that supersedes the old one. |

Together they let a third party trace the path from raw output to the governance decision.

## Reporting what a tool does not know

The second rule concerns what a tool may say when it lacks information, because much governance tooling turns missing data into a reassuring colour. A provider times out and the check is shown as passed, an analysis that only read file metadata is reported as if it had inspected the content, or a mock result from a demo ends up in a report.

We use a small, explicit set of states instead.

| State | Meaning |
|---|---|
| Validated | The evaluator ran and its method has been checked. |
| External provider | The result came from a third-party tool and carries that tool's limits. |
| Metadata only | The result describes the inventory and does not measure behaviour. |
| Insufficient data | There was not enough data to draw any conclusion. |
| Unavailable | No evaluator exists yet for this case. |

With these states, a provider timeout is recorded as an error and shown to the reviewer as one. A reviewer who can see where the tool had no answer has more reason to believe the results where it did.

## When evidence goes stale

Evidence describes the system at one moment. Once the model is retrained, the prompt edited, the dataset refreshed or the threshold changed, the old result no longer describes what is running in production.

A useful record therefore tracks its own dependencies. If the model changes, every result that tested that model is marked stale. If only the system prompt changes, only the results that depend on the prompt are marked, and everything else stays valid. That selectivity separates continuous assurance from re-running the whole audit every quarter. Superseded results stay in the record rather than being overwritten, so an auditor who asks what changed since last time gets a direct answer.

## Reusing one result across frameworks

A single prompt-injection test can support a requirement in the EU AI Act, a control in ISO/IEC 42001, a subcategory in the NIST AI RMF and an item in the OWASP Top 10 for LLM Applications. It should only need running once.

Reuse needs care, because mapping a test to a requirement is a judgement. A statement such as "this test partially supports Article 15 of the AI Act on accuracy, robustness and cybersecurity" is a claim that a named person has to make and stand behind. A tool can propose the mapping, but it should never approve its own proposal.

Our rule is that evidence can be reused across frameworks provided an accountable person reviews each mapping and records the strength of the link as satisfies, partially satisfies or supports. Whether the evidence is sufficient remains the auditor's decision.

## Agents and the chain of custody

Agents are starting to collect records, run checks, draft findings and file evidence for governance teams. We welcome that, since most of this work is repetitive and people do it badly.

It also raises the bar, because the chain of custody then has to cover the agent too, including what it was permitted to do, what it actually did, what it read and who approved any change it made. That requires a scoped identity for each step, a tool allowlist that a prompt cannot widen, a human gate before any record is accepted and a tamper-evident log of every run. If nobody can verify the agent's audit trail, its work gets checked by hand and the time saved is spent again at review.

## What this blog covers

Governance posts set out what the EU AI Act, ISO/IEC 42001, the NIST AI RMF, India's DPDP Act and other frameworks actually require, as read by engineers, with dates checked against the primary text. Security posts cover prompt injection, agent permissions, MCP servers, model supply chain and the OWASP and MITRE taxonomies, each with the test that shows you checked. Our safety writing deals with evaluation, red teaming, human oversight and incident review, with each method's limits stated.

Every post names its sources, gives a last-checked date and notes where sources disagree. Corrections are made in the post, with a note of what changed.

## About FairMind

FairMind is an agentic AI governance platform. Its agents run 90 governance workflows that collect, check, suggest, act, verify and file evidence; every workflow stops at a human approval gate, and every run is written to a hash-chained record. The catalogue defines 109 evaluations across 51 frameworks, and each evaluator declares whether it is validated, external, metadata only or not yet available. Results become Evidence Passports that carry one accepted test across several frameworks, with a person approving each mapping. If that is the kind of evidence your auditors ask for, [request access](https://fairmind.xyz/request-access?utm_source=blog&utm_medium=post&utm_campaign=chain-of-custody-for-ai).

## FAQ

**What is AI audit evidence?**
A record that lets a third party confirm what was tested, how, against which threshold, with what result, and who accepted it. A score without that context cannot be verified.

**Is an Evidence Passport a certificate?**
No. It is the record a certification body, auditor or internal reviewer examines, and they decide whether it is sufficient.

**Do we need this if we are not high-risk under the EU AI Act?**
The legal duty depends on your systems and jurisdiction. Customers, insurers and boards ask the same questions either way, and a traceable record answers them faster.

**How is this different from model monitoring?**
Monitoring tells you something changed. A chain-of-custody record also tells you which evidence that change invalidated, and keeps the history of what was accepted before.

## Sources
- [Regulation (EU) 2024/1689, the AI Act](https://eur-lex.europa.eu/eli/reg/2024/1689/oj), Articles 11, 12 and Annex IV on technical documentation and logging.
- [ISO/IEC 42001:2023](https://www.iso.org/standard/42001), the AI management system standard and its documented information requirements.
- [NIST AI RMF 1.0](https://www.nist.gov/itl/ai-risk-management-framework), the Measure function.

<!-- REVIEWER NOTES (not for publication)
- Article 15 example is used as an illustration of a mapping judgement, not a claim that a prompt-injection test supports Art 15 in any specific case.
- Article 11 / 12 / Annex IV apply to high-risk systems; under the Digital Omnibus the Annex III application date moved to 2 Dec 2027. Post does not state dates, so no change needed, but confirm wording reads correctly.
- "51 frameworks", "90 workflows", "109 evaluations" taken from apps/backend/src/api/routers/pack_catalogue_data/catalogue.json on main (4 Nov 2026). Re-check counts on publish day.
- The post states runtime controls (scoped identity per step, tool allowlist, hash-chained trace) as FairMind's approach; these match the website homepage copy on main. Confirm they describe shipped behaviour, not roadmap.
- Rewrite (Nov 2026): the Article 15 example names the article by its heading (accuracy, robustness and cybersecurity). Confirm against the OJ text.
- Rewrite: the seven provenance questions and the five-state vocabulary are now prose and a two-column table respectively; the blog-areas bullet list is now prose. Check the state table renders in the theme.
- Rewrite: title, meta_title, meta_description and custom_excerpt reworded to remove the colon reveal and the "claim, not evidence" formula; target_term kept in meta_title and meta_description. Sources list em dashes replaced with commas.
- Rewrite: the agents section drops its signposting phrase; the four controls are stated as what the chain of custody requires. The shipped-behaviour check above still applies.
-->
