---
title: 'FairMind: an open-source workbench for evidence-based governance of AI systems and agents'
tags:
  - Python
  - AI governance
  - algorithmic fairness
  - AI auditing
  - LLM evaluation
  - AI agents
authors:
  - name: Adhithya Rajasekaran
    orcid: 0009-0004-1682-7958
    affiliation: 1
affiliations:
  - name: Axonome
    index: 1
date: 8 November 2026
bibliography: paper.bib
---

# Summary

FairMind is an open-source platform for assessing AI systems, including
machine learning models, LLM applications and AI agents, against governance
frameworks and recording the result as verifiable evidence. It runs
governance as workflows: chains of steps that collect material, run
evaluations, propose findings and stop at gates where a person approves or
rejects. Every step is appended to a hash-chained ledger, so a reviewer can
later check who decided what and on which evidence. One evaluation run is
mapped, through a shared set of controls, to every framework requirement it
supports, so the same evidence serves ISO/IEC 42001, the NIST AI Risk
Management Framework [@nist_ai_rmf], its generative AI profile
[@nist_ai_600_1], the EU AI Act [@eu_ai_act] and the other frameworks in the
catalogue.

The release described here contains 90 workflows in 21 packs, 109 catalogued
evaluations of which 61 run inside FairMind, and 51 frameworks with 539
requirements linked through 29 common controls. Evaluations run on uploaded
files (for example data drift, train-test leakage, calibration and
membership inference), against a live model endpoint (prompt injection,
jailbreaks, system prompt leakage and uneven treatment between groups) and
on agent platform configurations (tools that act without confirmation,
unrestricted network egress, unauthenticated MCP servers). Each run returns
`passed`, `failed` or `insufficient`, the last when the inputs cannot
support a verdict. A release gate combines the results into `go`,
`conditional_go` or `no_go`. A command-line tool, a Python SDK, a GitHub
Action and a Model Context Protocol server expose the gate to CI pipelines
and coding agents, and evidence packs can be verified offline.

# Statement of need

Researchers and practitioners who audit AI systems face two separate
problems. The first is measurement: fairness, robustness and security need
metrics with stated assumptions and uncertainty. Libraries such as
Fairlearn [@weerts2023fairlearn], AI Fairness 360 [@bellamy2019aif360] and
Aequitas [@saleiro2018aequitas] provide fairness metrics and mitigation, and
tools such as garak [@derczynski2024garak] probe language models for
vulnerabilities. The second is accountability: an audit has to show which
system was assessed, with which data, by whom, against which requirement,
and what was decided. Work on internal algorithmic auditing
[@raji2020closing], model cards [@mitchell2019model] and datasheets
[@gebru2021datasheets] describes the documentation an audit needs, but
leaves its collection, linkage and integrity to each organisation.

FairMind connects the two. Its fairness engine reports demographic parity,
equal opportunity [@hardt2016equality], equalized odds and calibration
differences between groups, each with a bootstrap confidence interval and a
permutation-test p-value, so an observed gap can be read against sampling
noise rather than as a bare number. Results are stored as measured evidence
attached to specific framework controls, and the gate refuses approval while
critical findings remain open. Because the ledger is hash-chained and
evidence packs are verifiable without network access, a third party can
check an assessment without trusting the operator's database.

This makes FairMind useful to three groups. Researchers studying AI
auditing can run the same evaluation protocol across systems and compare
the evidence trails. Engineers can add a reproducible governance check to
CI, the same way they add tests. Compliance teams can hand auditors a
record whose integrity can be checked independently. FairMind supports
readiness for review; it does not certify compliance or approve a release
on its own, and every gate decision is made by a person.

# Design

The backend is a FastAPI service on PostgreSQL; the user interface is a
Next.js application. Workflow steps are typed: steps such as `trigger` and
`file` run automatically, steps such as `collect`, `check` and `verify` are
completed by a person or drafted by an agent on request, and `ask`,
`exception` and `decide` steps wait for a human decision. An agent can draft
work steps using the operator's own model provider, or without one using
deterministic rules that list what evidence is present and what is missing.
Agent output is written to the ledger as text and does not change anything
outside FairMind. When a person decides on their own proposal, the ledger
records it as a self-review.

Evaluation engines for uploaded files make no network calls, and uploaded
model files are inspected but never loaded or executed. The fairness metric
computations are fuzzed continuously, and the test suite runs against
PostgreSQL in CI.

# Limitations

FairMind is alpha software. Most catalogue workflows are marked as proposed
until organisations have run them in practice, 48 of the catalogued
evaluations have no engine yet and accept externally produced evidence
instead, evaluation engines run inside the backend process rather than in
sandboxed workers, and runs are started by a person rather than on a
schedule. Framework mappings organise evidence; they are not legal advice or
a conformity assessment.

# AI usage disclosure

Generative AI tools (Claude, Anthropic) were used to assist with software
development and to draft this paper. The author reviewed and edited all
generated text and code and takes responsibility for the content.

# Acknowledgements

FairMind is developed at Axonome.

# References
