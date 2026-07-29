# FairMind-E: Verified Prior Art and Submission Plan

Live-verified 2026-07-30 (web sweep of arXiv, Semantic Scholar, OpenAlex,
CEN-CENELEC JTC 21 trackers, HotCarbon 2026 program, G7 policy documents, and
venue CFP pages). Supersedes the venue and novelty sections of the June 2026
re-evaluation where they conflict.

## 1. Novelty verdict: WEDGE THREATENED, not taken

No published work gates AI release on a provenance-derived evidence-confidence
score crossed with impact tier (the FairMind-E primitive). The wedge is intact
by strict definition. It is THREATENED because three directions converged on it
between March and June 2026, and each author group is one combination step away:

1. Uncertainty entered the carbon gate: Green SARC uses split-conformal
   calibration inside a budget gate.
2. Provenance-derived reliability tiers for AI carbon numbers now exist
   descriptively: Hugging Carbon (v2 issued 2026-07-02, actively iterating).
3. Confidence-gated action on emissions estimates is demonstrated in an
   adjacent industrial domain: Trust-Aware PEMS (gas-turbine NOx).

Operational consequence: the CCAI workshop submission (deadline 2026-08-29) is
the priority stamp. Preprint to SSRN in September. Speed is part of the
strategy, not a preference.

## 2. Mandatory citation ledger

Each entry: work, what it holds, and the one-line differentiation the paper
must state.

| Work | Holds | Differentiation |
|---|---|---|
| CAGG v2, arXiv 2602.19718v2 (2026-06-10) | Carbon budgets in governance layers; Provenance Ledger is audit-only; graduated outcomes (deny / retry in low-carbon window / human review) | Gates on magnitude; acknowledges estimation uncertainty but has no confidence mechanism or decision matrix. Cite v2, and credit the graduated-outcome precedent. |
| G-TRACE v3, arXiv 2511.04776v3 (2026-05-19) | Readiness-level gates (L1-L7); L4: "launch blocking without carbon sign-off creates financial-grade controls" | Maturity checkpoints on magnitude/readiness indicators; no evidence-quality dimension. Quote the L4 phrase and differentiate directly. |
| Criteria for Credible AI-assisted Carbon Footprinting, arXiv 2509.00240 (Suh group) | Recommends pedigree/DQI-style qualitative uncertainty for AI-assisted product footprinting | Reverse direction: they assess AI as a tool that produces carbon numbers; FairMind-E scores carbon numbers to gate the AI. No numeric score, no thresholds, no gating. Biggest un-cited-prior-art risk; cite prominently. |
| Hugging Carbon, arXiv 2605.01549v2 (2026-07-02) | 3-tier estimation reliability by metadata completeness across 5,227 HF models (Tier 2 ~1.2x error, Tier 3 ~2x) | Descriptive, explicitly not a decision framework. Use as the empirical motivation that reliability varies by disclosure tier. |
| Green SARC, arXiv 2606.15954 (2026-06-14) | Predictive cost/carbon gates for agentic AI with split-conformal calibration | Gate fires on budget magnitude; calibration bounds the prediction, does not score evidence provenance. Closest "uncertainty inside a gate" work. |
| Trust-Aware PEMS, arXiv 2606.06156 (2026-06-04) | Calibrated trust scores on emissions estimates with confidence-gated filtering | Different domain (gas turbines) and different decision object (which predictions to trust, not whether to release a system). |
| Four-Tier Scope 3 for AI inference, arXiv 2606.10660 (2026-06-09) | Data-availability-tiered reporting hierarchy for CSRD; documents 10-40x overestimation in fallback tiers | Reporting hierarchy, no confidence scores, no gating. Rhymes with a provenance hierarchy; cite and differentiate. |
| Automated Self-Testing as a Quality Gate, arXiv 2603.15676 (2026-03-13) | Evidence-driven release gates (PROMOTE/HOLD/ROLLBACK), "evidence coverage" as a gate dimension | Zero environmental content. Shows the release-gate vocabulary is in circulation. |
| Weidema and Wesnaes (1996); Funtowicz and Ravetz (1990, NUSAP) | LCA pedigree matrices / data quality indicators; post-normal-science uncertainty pedigree | Claimed intellectual ancestry. No one has bridged them into AI release governance; being first to do so is a claimable contribution. Confirmed unplanted as of 2026-07-30. |
| Tkachenko, J. Financial Compliance (Jun 2025 journal version of arXiv 2410.01818) | AI carbon in banking risk-management frameworks | Cite the journal version. Risk framing, no evidence-quality gating. |
| Sustainable GenAI scoping review, IEEE Access vol. 14, 2026 (DOI 10.1109/ACCESS.2026.3659894) | Authoritative measurement-landscape survey | Cite the journal version, not the arXiv preprint. |

Citation counts for CAGG and G-TRACE were zero on OpenAlex and Semantic Scholar
as of 2026-07-30; neither has moved toward evidence quality across their 2026
revisions.

## 3. Regulatory framing: strengthened

- CEN-CENELEC JTC 21 has nine AI Act deliverables in flight; none environmental;
  zero cited in the Official Journal under Article 40 as of June 2026.
- Existing pre-standard measurement infrastructure (CEN/CLC/TR 18145:2025,
  ISO/IEC TR 20226:2025, IEEE P7100, ITU-T L.1801, AFNOR Spec 2314) quantifies
  and inventories; none defines evidence-quality scoring or trust-gated
  decisions. AFNOR's "accurate and verifiable claims" is the closest language.
- G7 French Presidency overview of AI energy/resource measurement initiatives
  (2026-05-29) catalogues 13 initiatives across measurement, monitoring, and
  reporting; none defines a decision layer above the measurements. Use as
  government-level evidence that the measurement layer exists and the
  trust-gated decision layer is empty.
- FAccT 2026 regulatory landscape paper (arXiv 2603.00068) demands disclosure
  and verification access, not deployment gatekeeping on measurement
  confidence. The anticipatory-infrastructure claim holds.

## 4. Verified submission calendar

| Date | Venue | Status |
|---|---|---|
| 2026-08-05 | CCAI mentorship program (optional) | Verified |
| 2026-08-29 AoE | CCAI workshop @ NeurIPS 2026 (Sydney, Dec 11-12). 4-page Papers track, non-archival, deployed-tool work welcomed. Decisions Sept 29. OpenReview account needed; creation can take two weeks | Verified |
| Sept 2026 | Full preprint to SSRN. FAccT author guide explicitly names SSRN as acceptable; do not self-cite it in the anonymized submission | Verified policy (2026 guide) |
| 2026-10-27 | FAccT 2027 abstract deadline | Verified |
| 2026-11-03 | FAccT 2027 full paper (14 pp + ethics statement). Timeline moved up from the historical ~Jan cycle; a January plan misses it | Verified |
| ~late Jan 2027 | ICT4S 2027 (Paris, June 21-25). Research-paper deadline estimated from the 2026 cycle; no call posted yet | Estimated |
| ~Feb-Mar 2027 | COMPASS 2027 | Estimated, unannounced |
| ~May 2027 | AIES 2027 | Estimated, unannounced |
| Rolling | ACM JCSS; AI and Ethics (Springer); ACM J. on Responsible Computing | Verified open |

Closed or missed in this cycle: COMPASS 2026 (ran July 2026), AIES 2026,
HotCarbon 2026, LOCO 2026, EAAMO 2026, ACM JRC "Computing within Planetary
Boundaries" special issue (closed 2026-05-31).

## 5. Two-stage plan

1. Stage 1 (now to 2026-08-29): 4-page CCAI Papers-track submission -
   repositioned concept plus working implementation plus fixture ablation,
   clearly bounded. Non-archival; burns no novelty; stamps priority against the
   converging groups.
2. Stage 2 (to 2026-11-03): FAccT 2027 full paper if and only if the expert
   panel (M6) is recruited in August and executed by mid-October. Otherwise
   ICT4S 2027 (~late Jan 2027) is the primary full-paper target, with COMPASS
   2027 / AIES 2027 / journals as fallbacks.

Gating risk for Stage 2 remains recruitment of the 15-expert panel, not
statistics or implementation.
