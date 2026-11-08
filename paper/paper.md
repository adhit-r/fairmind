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
metrics with stated assumptions and uncertainty. The second is
accountability: an audit has to show which system was assessed, with which
data, by whom, against which requirement, and what was decided. Work on
internal algorithmic auditing [@raji2020closing], model cards
[@mitchell2019model], datasheets [@gebru2021datasheets] and FactSheets
[@arnold2019factsheets] describes the documentation an audit needs, but
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

The software serves three groups. Researchers studying AI auditing can run
the same evaluation protocol across systems and compare the evidence
trails. Engineers can add a reproducible governance check to CI, the same
way they add tests. Compliance teams can hand auditors a record whose
integrity can be checked independently. FairMind supports readiness for
review; it does not certify compliance or approve a release on its own, and
every gate decision is made by a person.

# State of the field

Measurement libraries are mature. Fairlearn [@weerts2023fairlearn], AI
Fairness 360 [@bellamy2019aif360] and Aequitas [@saleiro2018aequitas]
compute group fairness metrics and mitigations; the Responsible AI Toolbox
[@rai_toolbox] adds error analysis and interpretability dashboards; garak
[@derczynski2024garak] and Giskard [@giskard] probe language models for
vulnerabilities. Each produces results for one analysis, and none records
who accepted a result, which requirement it answers, or whether it was
altered afterwards.

FairMind does not reimplement these libraries' scope. Its engines cover
the evaluations a governance review needs in one place, and results from
external tools can be attached as evidence when FairMind has no engine. We
built a separate platform rather than contributing to one of these projects
because the missing parts are not metrics: they are the workflow with human
gates, the mapping from one result to many framework requirements, and a
tamper-evident record. These change the unit of work from an analysis to an
assessment, which falls outside the stated scope of the measurement
libraries.

# Software design

The backend is a FastAPI service on PostgreSQL; the user interface is a
Next.js application. Four choices shape the design.

*Human gates over automation.* Workflow steps are typed: `trigger` and
`file` steps run automatically, `collect`, `check` and `verify` steps are
completed by a person or drafted by an agent on request, and `ask`,
`exception` and `decide` steps wait for a human decision. An agent can draft
work steps with the operator's own model provider, or without one using
deterministic rules that list which evidence is present and which is
missing. Agent output is written to the ledger as text and changes nothing
outside FairMind. This costs speed, but it keeps responsibility for every
decision with a named person, which is what an audit has to show. When a
person decides on their own proposal, the ledger records a self-review.

*A shared control layer.* Framework requirements are linked to 29 common
controls instead of to evaluations directly. Adding a framework means
mapping its requirements to existing controls, and one evaluation run then
counts as evidence wherever it applies. The cost is that a mapping can be
coarser than a framework's own wording, so mappings are presented as
organising evidence, not as legal interpretation.

*A hash-chained ledger in the application database.* Each entry includes the
hash of the previous one, so any later edit breaks the chain. We chose this
over an external transparency log to keep deployment to a single database;
evidence packs carry a hashed manifest and the chain heads, so the
command-line tool can verify them offline.

*Conservative verdicts.* An engine returns `insufficient` rather than
`passed` when its inputs cannot support a verdict, for example when a drift
check gets too few rows or no agreed threshold was given. Engines for uploaded files make no network calls, and
uploaded model files are inspected but never loaded or executed.

# Research impact statement

FairMind is early, and its evidence of impact is readiness rather than
adoption. Release v0.3.0-alpha is archived on Zenodo with a DOI and on
Software Heritage, and is listed in the OECD.AI Catalogue of Tools & Metrics
for Trustworthy AI and in the Awesome AI Regulation, Principles & Guidelines
list. The repository includes the materials for a study built on the
platform (FairMind-E, on environmental evidence for AI systems): a
measurement harness, hand-labelled fixtures run against the production
gate, and the hypothesis analyses. The backend has over 3,000 tests that run
against PostgreSQL in CI, the fairness metric computations are fuzzed on
every pull request, and releases are signed with Sigstore and carry SLSA
provenance, so results can be reproduced from a verified build.

# Limitations

FairMind is alpha software. Most catalogue workflows are marked as proposed
until organisations have run them in practice, 48 of the catalogued
evaluations have no engine yet and accept externally produced evidence
instead, evaluation engines run inside the backend process rather than in
sandboxed workers, and runs are started by a person rather than on a
schedule. Framework mappings organise evidence; they are not legal advice or
a conformity assessment.

# AI usage disclosure

Generative AI (Claude, by Anthropic, through Claude Code) was used to write
and revise parts of the software, tests and documentation, and to draft this
paper. The author directed the work, reviewed every change before merging,
and verified it through the automated test suite, CodeQL static analysis
and fuzzing, all of which are required checks on the main branch. For the
paper, the author checked every count against the released code and every
reference against its original source, and takes responsibility for the
content.

# Acknowledgements

FairMind is developed at Axonome.

# References
