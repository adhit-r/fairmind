# FairMind docs rewrite: plan and outline

Date: 2026-11-09. Site: `apps/docs` (Fumadocs, served at docs.fairmind.xyz).
Models: Better Auth docs (code-first, plugin-page templates, AI resources) and Olai docs (`~/axonome/olai/apps/docs`: journeys, Watch / Try it, page anatomy, access badges).

## Why the current docs fall short

- 27 pages, 1,210 lines, about 45 lines a page. Most pages describe; few show.
- Navigation follows internal terms (Concepts, Workflows, Engineering reference), not what a user is trying to do.
- The product has about 40 dashboard areas, 56 catalogue evaluations, Agentic Packs, an SDK, a CLI and an MCP server. The docs cover a fraction, and the SDK, CLI and MCP get one shared page.
- Only the EU AI Act has a crosswalk; AIUC-1, NIST AI RMF and DPDP have none.
- No screenshots, recordings, install tabs, `llms.txt` or copy-as-markdown.
- No per-page status, so readers can't tell shipped, alpha (off by default) and not-built apart. `docs/STATUS.md` already has this boundary.

## Principles

1. **Show, then explain.** Every task page opens with a short recording or a code block, before any prose.
2. **Code first for builders.** Install and SDK pages follow Better Auth: `<Steps>`, package-manager tabs remembered across pages, titled code blocks, warn callouts for caveats.
3. **Journeys for operators.** Follow Olai: start-to-finish journeys (register, test, review evidence, remediate, release) that link into the workspace pages.
4. **Honest status on every page.** A `<Status>` badge (Shipped, Alpha, Not built) generated from the same source as `docs/STATUS.md`. Never claim compliance, certification or realtime assurance.
5. **Generated where it drifts.** The API reference, evaluation catalogue, pack pages and framework control lists are generated from source, not typed by hand.
6. **Built for AI readers.** `llms.txt`, `llms-full.txt`, per-page copy as markdown, and a docs page for the FairMind MCP server.

## Outline

```
FairMind
├── Start here
│   ├── What is FairMind           one paragraph, the lifecycle diagram, what it is not
│   ├── Quickstart                 Steps: install, sign in, register a system, run one evaluation, read the verdict
│   ├── Core concepts              system, evaluation, evidence, control, verdict, passport, review
│   ├── How evidence is trusted    signatures, replay and scope checks, freshness, review gates
│   └── Status and limits          generated status table; what FairMind does not claim
├── Journeys                       (Olai style: Watch / Try it, then Steps)
│   ├── Govern your first agent    register, then pack, then evaluate, then evidence, then verdict
│   ├── Block a risky release      release gate in CI
│   ├── Fix a finding and retest   remediation loop with history
│   ├── Prepare for an audit       evidence review, approvals, report export
│   ├── Watch a system after launch   scheduled monitoring and alerts
│   └── Map to a framework         pick EU AI Act / AIUC-1 / NIST / DPDP, see coverage gaps
├── The workspace                  (one page per dashboard area, grouped by lifecycle stage)
│   ├── Onboard                    systems, model inventory, AI-BOM, integrations
│   ├── Assess                     test lab, Agentic Packs, LLM testing, LLM judge, bias, multimodal, benchmarks
│   ├── Govern                     evidence, controls, policies, risks, provenance, compliance dashboard
│   ├── Remediate                  remediation, remediation wizard
│   ├── Operate                    monitoring, alerts, reports, audit reports
│   └── Settings                   organisation, team, roles, API keys
├── Evaluations                    (generated, one template per evaluation)
│   ├── Catalogue                  filterable table: modality, risk, framework controls, status
│   └── <evaluation>               what it tests, inputs, thresholds, evidence it produces, limits
├── Agentic Packs                  (generated, Better Auth plugin template)
│   └── <pack>                     install, evaluations included, controls covered, options
├── Frameworks
│   ├── EU AI Act                  crosswalk: article, control, evaluations, evidence
│   ├── AIUC-1
│   ├── NIST AI RMF
│   └── DPDP Act
├── Build with FairMind            (Better Auth style: code first)
│   ├── Python SDK                 install tabs, client, every method: example, types, errors
│   ├── CLI                        commands, flags, CI recipes
│   ├── MCP server                 tools, setup for Claude / Cursor / VS Code
│   ├── Release gate in CI         GitHub Actions and GitLab recipes
│   └── Webhooks and events
├── Self-host
│   ├── Deploy                     Docker / Netlify / Render, environment variables
│   ├── Configuration              generated from settings
│   ├── Authentication and RBAC    roles, permissions, separation of duties
│   └── Operator runbook
├── Reference
│   ├── REST API                   generated from OpenAPI (fumadocs-openapi)
│   ├── Permissions                generated from the permission registry
│   ├── Evidence Passport schema   from docs/product/evidence-passport.schema.json
│   └── Glossary
└── AI resources                   llms.txt, MCP for the docs, copy as markdown
```

## Page templates

| Template | Used by | Anatomy |
|---|---|---|
| Journey | Journeys | Status, Watch / Try it tabs, one-line outcome, Steps (each links to a workspace page), "What you have now", next journey |
| Workspace | The workspace | Status, `<Access>` (required permission), screenshot with `<PageAnatomy>` callouts, tasks as Steps, related evaluations and controls |
| Evaluation | Evaluations | Status, what it tests, inputs, method and threshold, evidence produced, controls it maps to, known limits |
| Pack | Agentic Packs | Status, install (Steps + SDK tab), evaluations included, controls covered, options table (`<TypeTable>`) |
| Framework | Frameworks | Scope, crosswalk table, coverage gaps, how to export the evidence |
| SDK method | Build | One-line purpose, code block, parameters (`<TypeTable>`), returns, errors |

Reuse from Olai: `watch.tsx`, `try-it.tsx`, `page-anatomy.tsx`, `access.tsx`, `llms.txt` routes. Add: `<Status>`. Fumadocs already ships Steps, Tabs, Callout, TypeTable and Cards.

## Phases

| Phase | Scope | Done when |
|---|---|---|
| P0 Skeleton (day 1) | New nav and `meta.json` files; port Olai components; `<Status>`; `llms.txt`; redirects from the old URLs | Site builds; every old URL resolves |
| P1 Front door (days 1 to 3) | What is FairMind, Quickstart, Core concepts, Status and limits, "Govern your first agent", SDK install | A reviewer can go from the docs home to a first verdict without asking anything |
| P2 Generated reference | Evaluation catalogue, packs, REST API, permissions, configuration, passport schema | Generated in CI; the build fails on drift |
| P3 Journeys and workspace | Remaining journeys; one page per dashboard area | Every dashboard route has a docs page |
| P4 Frameworks | AIUC-1, NIST AI RMF, DPDP crosswalks alongside the EU AI Act | Each control row links to evaluations and evidence |
| P5 Media | Recordings and annotated screenshots | Waits on the v7 "Spine" UI sign-off, so captures match the shipped UI |

P1 is the only phase needed before the funding emails go out. P5 waits for the UI; until then, pages leave named slots for Watch and screenshots instead of capturing the current UI.

## Open questions

- Which pages can show a public sandbox ("Try it") without exposing production data? Neon in `apps/backend/.env` is production.
- Are GRClaw docs part of this site or separate?
- Is the docs domain staying on Netlify?
