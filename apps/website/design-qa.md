# FairMind website design QA

## Review target

- Homepage: `http://127.0.0.1:4321/`
- Desktop viewport override: 1586 x 992; visible page surface is 1496 x 936 after browser chrome.
- Mobile viewport override: 390 x 844; visible page surface is 368 x 796 after browser chrome.
- Desktop captures: `/private/tmp/fairmind-website-v2-qa/hero-desktop-final.jpg`, `/private/tmp/fairmind-website-v2-qa/graph-desktop-final.jpg`, `/private/tmp/fairmind-website-v2-qa/footer-desktop-final.jpg`
- Mobile captures: `/private/tmp/fairmind-website-v2-qa/hero-mobile-final.jpg`, `/private/tmp/fairmind-website-v2-qa/footer-mobile-final.jpg`

## Product-truth review

- The opening statement defines FairMind as the vendor-neutral evidence workbench between evaluator tools and accountable governance.
- The page explicitly covers AI evaluation, AI safety, AI governance, research, framework mapping, findings, remediation, retest, and assurance packages.
- The canonical product graph is shown as AI system to evaluation run to artifact to candidate mapping to reviewer decision to finding/risk to remediation/retest to assurance package.
- Current implementation state is separated from roadmap targets. Environmental evidence is presented as a validated path, the LLM judge as an external-provider path, AI BOM as metadata-only, and unavailable routes remain unavailable.
- The current boundary is explicit: mutable workbench records are not yet immutable Evidence Passports.
- Missing evidence never becomes a pass, mappings require human review, and FairMind does not claim certification.

## Visual and interaction review

1. Replaced the flat product diagram with a signature CSS 3D evidence exchange: layered source cards, a raised evidence record, accountable outputs, perspective floor, pointer tilt, replayed evidence flow, and depth changes on hover.
2. Rebuilt the footer around three concrete entry points: run tests, review evidence, and own the decision. Secondary links are grouped by product understanding, evidence inspection, and plain-language legal/support routes.
3. Exercised evaluator switching. Selecting the LLM judge changed the record to `external_provider`, updated evaluator/threshold/artifact fields, and exposed the provider-dependency limitation.
4. Exercised the reviewer role tab, the reviewer-decision graph node, replay animation, and capability filtering. The graph hit target was repaired by keeping perspective on the graph while moving 3D transforms onto the interactive nodes.
5. Verified desktop and mobile composition. There is no horizontal page overflow; intentional internal tracks remain scrollable on narrow screens.
6. Verified reduced-motion rules and transform/opacity-only motion for choreography.

## Secondary-route migration

- Replaced the legacy implementations for `/features`, `/use-cases`, `/comparison`, `/demo`, `/roadmap`, `/about`, `/blog`, `/contact`, `/request-access`, and `/404`.
- Removed the old yellow-on-black pages, purple/pink gradients, generic card grids, unsupported live-integration claims, automatic-compliance language, and the stale “22 dashboards” demo story.
- Every product route now uses the same white, near-black, and `#FF6B35` system, shared dimensional hero, hard shadows, evidence-ledger structures, route-specific copy, and journey-based footer.
- Roadmap content is now a recovery sequence with observed, P0, P1, and P2 boundaries plus an interactive priority filter.
- Request Access and Contact now ask for precise evidence-path context. Their Formspree submission route is explicitly allowed by the production CSP.
- Removed the unused static Astro POST endpoint and stale Netlify Functions configuration. Removed the SPA catch-all so real static routes and the custom 404 resolve independently.
- Desktop route audit covered homepage plus 13 public/404 destinations. Every route produced exactly one `main`, one `h1`, no legacy purple/pink/yellow/gradient classes, no horizontal overflow, and the shared footer.
- Mobile audit covered every non-legal marketing route at 390 x 844 with no page-level horizontal overflow or heading escape.

## Design-system review

- Palette: white `#FFFFFF`, near-black `#101614`, FairMind orange `#FF6B35`, and alpha variants of those tokens only.
- Black is used for typography, borders, structural fields, and hard shadows. Orange identifies state, flow, focus, and primary actions.
- No gradients, purple, blurred shadows, rounded-card drift, stock illustration, or decorative AI imagery.
- Raleway remains the display/body face and the documented platform monospace stack is used for evidence metadata.
- Impeccable's deterministic scan found no blocking design-pattern errors. Its single-font warning is a detector false positive: it counts the one downloaded face but not the distinct platform monospace stack used throughout the evidence UI. Remaining advisories are literal micro-label sizes and permitted palette alpha variants used in the dense evidence visualization.

## Verification

- Browser console: no errors after desktop and mobile navigation, all homepage interactions, the roadmap filter, and the complete secondary-route audit.
- Accessibility structure: semantic headings/landmarks, tabs and tabpanels, button pressed states, live graph detail, focus styles, skip link, and reduced-motion handling are present.
- Build: Astro generated all 14 routes. Only the existing Vite/Astro dependency deprecation warnings remain.
- Hosted preview: all 14 route checks passed on Netlify deploy `6a6ce2f16fbeb9dc675787c9` before production promotion.

final result: passed
