# AI Governance Assurance Module Design Brief

## Outcome

Enhance FairMind's existing AI Governance module into a company-scoped, AI-system-first assurance workspace. The module supports versioned frameworks such as AIUC-1, shared controls, evidence from company integrations and FairMind evaluations, findings, remediation, decisions, and auditor handoff.

## Users and Jobs

- Organization administrator: provision the company, members, roles, integrations, and AI systems.
- Model or agent owner: run evaluations, provide implementation evidence, resolve findings, and submit for review.
- Compliance owner: activate frameworks, assign controls, review evidence mappings, decide control state, and prepare assurance packages.
- Auditor: inspect a read-only requirement-to-decision trail and download a version-pinned evidence index.

## Core Experience Decision

The module is system-first with a framework lens:

`Organization → AI system → framework assignment → shared control assessment → evidence/evaluation → finding/remediation → decision/report`

An AI system may be a model, agent, or composite application. Organization is the company tenant. Workspace remains an optional grouping and is not presented as another company concept.

## MVP Scope

1. Consolidate AI Governance navigation into Overview, AI Systems, Frameworks & Controls, Evidence & Evaluations, Findings, and Reports & Assurance.
2. Import the supplied AIUC-1 April 2026 workbook as an immutable versioned framework catalog.
3. Assign a framework version to an AI system and create system-scoped control assessments.
4. Adapt real FairMind evaluation runs and company integration snapshots into provenance-rich evidence envelopes.
5. Suggest control mappings and require reviewer acceptance per evidence link.
6. Surface evidence freshness, findings, remediation, and decision state.
7. Export a version-pinned assurance package and provide a role-scoped read-only auditor view.

## Non-goals

- A standalone portal or separate AIUC-1 application.
- Another tenant, identity, evidence, policy, risk, remediation, or reporting subsystem.
- Automatic certification, automatic control satisfaction, or framework compliance claims.
- A general connector marketplace or workflow engine.
- Default transfer of raw model weights, unrestricted prompts, or private reasoning traces.
- Copying code or unlicensed enrichment from the AIUC1-Mapping-Tool repository.

## Experience Principles

- Scope before score.
- Trace before trust.
- Automation proposes; reviewers decide.
- Failures remain visible after reruns.
- One evidence artifact may support several controls, but every link is reviewed independently.
- Dense task views use tables, grouped rows, and split panels instead of repeated card grids.

## Success Criteria

- A company admin can register an AI system and activate AIUC-1 April 2026.
- A system owner can run or import a FairMind evaluation and see it as evidence with provenance.
- A reviewer can accept or reject a candidate control mapping with rationale.
- A compliance owner can identify missing, stale, rejected, or failed evidence without inspecting raw database identifiers.
- An auditor can trace a requirement to control assessment, evidence, evaluation, finding, remediation, and final decision.
- Cross-organization access is denied for every new resource-by-ID path.
