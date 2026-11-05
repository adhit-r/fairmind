---
title: "OWASP LLM Top 10 2026 changes and how to re-map from 2025"
slug: owasp-llm-top-10-2026-changes
status: draft
meta_title: "OWASP LLM Top 10 2026 Changes and the 2025 Re-map"
meta_description: "OWASP LLM Top 10 2026 compared with 2025, with the full ID re-map table and how to move tests, controls and audit evidence while keeping old claims valid."
custom_excerpt: "Eight of the ten OWASP LLM IDs changed meaning in the 2026 edition. This post gives the 2025 to 2026 re-map, what to do with existing mappings, and the evidence to keep for each entry."
tags: [security, owasp]
author: Adhithya Rajasekaran
target_term: "owasp llm top 10 2026"
last_checked: 2026-11-04
---

Teams that mapped tests or controls to the 2025 OWASP LLM Top 10 will find that the 2026 edition reuses most of the same IDs for different risks. Prompt Injection and Sensitive Information Disclosure kept LLM01 and LLM02, while LLM03 to LLM10 now refer to different entries than they did a year ago. This post gives the full 2025 to 2026 re-map, what to do with mappings you already hold, and what evidence shows you tested for each entry.

We checked everything below against the official 2026 document from the OWASP GenAI Security Project, which we downloaded and read in full. Where secondary sources disagree with it, we say so.

## How the 2026 edition was produced

The [official 2026 resource page](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/) is dated 3 August 2026, and the cover of the [122-page PDF](https://genai.owasp.org/download/56857/) gives 4 August 2026. [HackerDNA](https://hackerdna.com/blog/owasp-llm-top-10) also reports 4 August and Giskard gives no release date, so we treat the release as 3 or 4 August 2026 and do not pick between them.

The ranking method is new. According to the letter from the project leads in the [2026 PDF](https://genai.owasp.org/download/56857/), the community vote carries three quarters of the weight and a corpus of 7,714 real incidents carries the remaining quarter. The incidents came from public vulnerability databases and an AI-harm database, and 6,639 of them had enough detail to classify. The leads also report that the two inputs disagreed. Prompt Injection ranks first by vote but falls outside the top ten by raw incident count, which they attribute to teams defending against it so heavily that fewer clean exploits get reported. Misinformation went the other way, with voters placing it low and the incident record placing it high.

## What changed from 2025

Eight of the ten IDs changed, and because the numbers were reused, a bare ID in old records is now ambiguous. A spreadsheet row that says only "LLM06" meant Excessive Agency in 2025 and means Unbounded Consumption in 2026, and the row cannot tell you which was meant. No entry was dropped and no standalone category was added. OWASP says it folded newer risks into the entries that already own them instead of splitting the list ([OWASP 2026 PDF, "What's New"](https://genai.owasp.org/download/56857/)).

The largest move is Excessive Agency, which rose from sixth to third and which OWASP calls the most consequential change on the list. OWASP's reason is that both the vote and the incident record show damage landing in agentic deployments. Agent tests filed under a mid-table ID should move up the priority order.

System Prompt Leakage is the only renamed entry, and the rename comes with a wider scope. As LLM08:2026 Hidden Context Exposure it covers hidden context in general, which includes the system prompt, developer instructions, retrieved policy text, and the schemas of tools and functions the application exposes to the model. The [2025 System Prompt Leakage entry](https://genai.owasp.org/llmrisk/llm072025-system-prompt-leakage/) centres on the system prompt and does not mention tool schemas or retrieved content. The 2026 text also tells readers to assume hidden context is discoverable and never to treat it as a security boundary. A test that only tries to extract the system prompt therefore no longer covers LLM08:2026.

OWASP's own summary lists four further widenings inside existing entries. Prompt Injection now covers cross-modal attacks, such as instructions hidden in an image or an audio track. Supply Chain covers a promoted model artifact that is not what it claims to be, Data and Model Poisoning absorbs fine-tuning subversion, and Improper Output Handling extends to the insecure code that assistants generate at scale.

Unbounded Consumption rose four places, Misinformation rose two, and Improper Output Handling fell five, from fifth to tenth. HackerDNA explains that fall by saying the risk is well understood and fixable with existing encoding and validation practice, and that the risk itself did not shrink. That reading is HackerDNA's and does not come from OWASP.

The 2026 list also draws a boundary with agents. It owns the risk while the model is a component inside your application. Once the model has tools, memory and downstream consequences, the risk belongs to the [OWASP Top 10 for Agentic Applications](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/), published 9 December 2025, and Appendix A of the 2026 document maps each LLM entry to that list's ASI IDs.

## The 2025 to 2026 re-map

Rows are ordered by 2025 ID, so you can relabel an existing mapping from top to bottom.

| 2025 ID and name | 2026 ID and name | Nature of change | Action for existing mappings |
|---|---|---|---|
| LLM01:2025 Prompt Injection | LLM01:2026 Prompt Injection | Same ID, scope widened (cross-modal inputs) | Keep the mapping. Add image and audio injection cases. |
| LLM02:2025 Sensitive Information Disclosure | LLM02:2026 Sensitive Information Disclosure | Same ID. 2026 text names more leak channels (tool arguments, reasoning traces, logs, embeddings) | Keep the mapping. Check that tests cover those channels as well as answer text. |
| LLM03:2025 Supply Chain | LLM04:2026 Supply Chain | Moved down one, scope widened (promoted model artifacts) | Re-label. Add an artifact-provenance check. |
| LLM04:2025 Data and Model Poisoning | LLM05:2026 Data and Model Poisoning | Moved down one, scope widened (fine-tuning subversion) | Re-label. Add fine-tune data review. |
| LLM05:2025 Improper Output Handling | LLM10:2026 Improper Output Handling | Moved down five, scope widened (generated code) | Re-label. Add generated-code execution checks. |
| LLM06:2025 Excessive Agency | LLM03:2026 Excessive Agency | Moved up three | Re-label. Raise priority. Pair with ASI IDs. |
| LLM07:2025 System Prompt Leakage | LLM08:2026 Hidden Context Exposure | Renamed, scope widened | Re-label and re-run. Test tool schemas, retrieved policy text and other hidden context. |
| LLM08:2025 Vector and Embedding Weaknesses | LLM09:2026 Vector and Embedding Weaknesses | Moved down one | Re-label only. |
| LLM09:2025 Misinformation | LLM07:2026 Misinformation | Moved up two | Re-label. Raise priority where output drives tool calls. |
| LLM10:2025 Unbounded Consumption | LLM06:2026 Unbounded Consumption | Moved up four | Re-label only. |

No row is a split or a merge. The 2025 list is on the [official LLM Top 10 page](https://genai.owasp.org/llm-top-10/) and the 2026 list is in the [official PDF](https://genai.owasp.org/download/56857/). Giskard, HackerDNA and Superblocks give the same ten IDs in the same order.

## Migrating existing mappings

Leave 2025 IDs alone wherever you have already made a claim with them. If a report, certification file, customer questionnaire or audit response cites "LLM06:2025", that record describes what was tested against that edition and should stay as written. The year suffix carries that meaning, so store it with every ID.

For live tests and controls, carry both editions during the transition. Two fields per test, each with the year in its value, are enough.

```yaml
owasp_llm_2025: LLM07:2025
owasp_llm_2026: LLM08:2026
```

Never store a bare "LLM07". Once nothing external cites the 2025 field any more, retire it.

A relabel is enough for entries that only moved. Where scope widened, re-run or extend tests in these areas:

- Hidden context beyond the system prompt, including tool descriptions, retrieved documents, policy text and memory.
- Prompt injection delivered through images and audio.
- Sensitive information leaving through tool arguments, reasoning traces and logs.
- Provenance of model artifacts you promote between environments.
- Fine-tuning data and process, reviewed for poisoning.
- Code your assistants generate, and where that code runs.

Where an entry's real concern is what an agent does, add an ASI reference next to the LLM ID. Appendix A of the 2026 document gives the primary pointers below. Giskard publishes a shorter table with one counterpart per entry, which simplifies the appendix.

| 2026 LLM entry | ASI pointers in Appendix A |
|---|---|
| Prompt Injection | ASI01 Agent Goal Hijack, ASI02 Tool Misuse and Exploitation |
| Excessive Agency | ASI01, ASI02, ASI03 Identity and Privilege Abuse, ASI05 Unexpected Code Execution, ASI07 Insecure Inter-Agent Communication |
| Hidden Context Exposure | ASI06 Memory and Context Poisoning, ASI07 |
| Supply Chain | ASI04 Agentic Supply Chain Vulnerabilities |
| Unbounded Consumption | ASI02, ASI08 Cascading Failures |

## Evidence for each entry

The table gives our examples of what a reviewer can inspect for each 2026 entry. None of them proves a system is secure.

| 2026 entry | Evidence a reviewer can inspect |
|---|---|
| LLM01 Prompt Injection | A test-suite result with injected instructions delivered through direct input, retrieved content, tool output and images, and a log of what the model did. |
| LLM02 Sensitive Information Disclosure | A red-team log of extraction attempts, plus a review of what appears in tool arguments, traces and logs. |
| LLM03 Excessive Agency | A config review listing each tool, its permissions and which actions need human approval, plus a log of out-of-scope attempts. |
| LLM04 Supply Chain | An inventory of models, adapters, datasets and packages with their sources and pinned versions or hashes. |
| LLM05 Data and Model Poisoning | A record of where training and fine-tuning data came from, how it was reviewed, and what was revalidated after changes. |
| LLM06 Unbounded Consumption | A load or abuse test showing rate, token and spend limits holding, with alerts on breach. |
| LLM07 Misinformation | An evaluation result for grounding and factual accuracy on your own tasks, plus a note on where output feeds an action. |
| LLM08 Hidden Context Exposure | A config review confirming no credentials sit in hidden context, plus an extraction test against the prompt, tool schemas and retrieved policy text. |
| LLM09 Vector and Embedding Weaknesses | A cross-tenant retrieval test and an access-control review of the vector store. |
| LLM10 Improper Output Handling | A test showing model output is encoded or validated before it reaches a browser, shell, database or file path. |

## Licence

OWASP says the 2026 document is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Reusing it means crediting the OWASP GenAI Security Project, linking the licence, saying whether you changed anything, and sharing derived work under the same licence. This post uses the IDs and our own descriptions.

## About FairMind

FairMind is an agentic AI governance platform with 90 governance workflows and 109 evaluations across 51 frameworks, including the OWASP LLM and Agentic Top 10. Its evaluations cover LLM apps and RAG (prompt injection, jailbreaks, prompt leakage, groundedness, harmful content) and agents (tool least privilege, out-of-scope actions, MCP permissions, kill switches). Each evaluator declares whether it is validated, runs through an external provider, reads metadata only, or is not yet available, and results become Evidence Passports. FairMind's own framework mappings still use the 2025 OWASP LLM IDs while the 2026 re-map is pending, so keep the product's 2025 IDs as they are and apply the table above in your own records. The full evaluation list is on the [FairMind homepage](https://fairmind.xyz/#evaluations), and our [ISO/IEC 27090 explainer](https://blog.fairmind.xyz/iso-iec-27090-explained/) covers the standards view of the same threats.

[Request access to FairMind](https://fairmind.xyz/request-access?utm_source=blog&utm_medium=post&utm_campaign=owasp-llm-top-10-2026-changes)

## FAQ

### Does the OWASP LLM Top 10 2026 replace the 2025 list?

OWASP presents the 2026 edition as the current list. The 2025 edition still exists and is what older reports cite. Keep old claims pinned to 2025 and use 2026 IDs for new work.

### Is the OWASP LLM Top 10 a compliance standard?

No. The document describes risks. Mapping a test to an entry does not make a system compliant or secure.

### Which entry changed the most?

By rank, Improper Output Handling fell five places and Excessive Agency rose three. By meaning, the largest change is System Prompt Leakage, which became Hidden Context Exposure and now covers tool schemas and retrieved policy text as well as the system prompt.

### Where do tool-using agents fit?

The LLM list covers the model as a component of your application. Agents with tools, memory and downstream effects fall under the OWASP Top 10 for Agentic Applications, IDs ASI01 to ASI10. Appendix A of the 2026 document maps each LLM entry to those IDs.

## Sources
- [OWASP GenAI LLM Top 10 2026, resource page](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/). Official page, dated 3 August 2026, CC BY-SA 4.0 site footer, download link.
- [OWASP Top 10 for LLM Applications 2026 (official PDF)](https://genai.owasp.org/download/56857/). Ten entries and IDs, 4 August 2026 cover date, 122 pages, 75/25 weighting, 7,714 and 6,639 incident counts, what's new, Hidden Context Exposure scope, Appendix A ASI mappings, CC BY-SA 4.0 licence terms.
- [OWASP LLM Top 10 (2025) landing page](https://genai.owasp.org/llm-top-10/). The 2025 ten IDs and names.
- [LLM07:2025 System Prompt Leakage](https://genai.owasp.org/llmrisk/llm072025-system-prompt-leakage/). 2025 scope used for the scope-widening comparison.
- [OWASP Top 10 for Agentic Applications for 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/). Published 9 December 2025.
- [Giskard: OWASP Top 10 for LLM 2026](https://www.giskard.ai/knowledge/owasp-top-10-for-llm-2026). Independent confirmation of the ten-entry list, ID changes and ASI counterparts.
- [HackerDNA: OWASP LLM Top 10 (2026)](https://hackerdna.com/blog/owasp-llm-top-10). Independent confirmation of the list, 4 August release date and per-entry commentary, including the reading on Improper Output Handling.
- [Superblocks: OWASP LLM Top 10 2026](https://www.superblocks.com/blog/owasp-llm-top-10). Independent confirmation of the list and order.
- [Creative Commons BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Licence terms.

<!-- REVIEWER NOTES (not for publication)
- Official document was reachable. The PDF at genai.owasp.org/download/56857/ (122 pages) was downloaded and read: the ten 2026 IDs and names, the 75/25 weighting, 7,714 and 6,639 incident counts, What's New text, LLM08 scope, and Appendix A ASI mappings are all from it. The official HTML resource page does not list the entries.
- Release date: resource page shows 3 August 2026; PDF cover shows August 4th, 2026 but its own revision history still has a "[2026 release date]" placeholder and the cover also has "[Publication date to be set]". HackerDNA and Superblocks say 4 August (Superblocks adds Black Hat USA, not used in the post); Giskard states no release date, only its own article date of 5 August. The post says 3 or 4 August.
- "Eight of ten moved, one renamed": I interpreted this as eight IDs changed (LLM03 to LLM10), with LLM08 the rename. Superblocks and Giskard phrase it differently (Superblocks says eight entries moved; its own table shows seven rank changes plus the rename). The post says "eight of ten IDs changed", which matches Giskard's wording.
- Page-count growth "46 to 122": 122 is confirmed from the PDF. The 2025 figure of about 46 was not verified, so the post omits the comparison.
- Superblocks says Unbounded Consumption's scope was widened to include Denial of Wallet. The 2025 entry already lists Denial of Wallet as a sub-type, so the post does not claim a widening for LLM06 (relabel only). HackerDNA describes a reframing around cost asymmetry, which I did not treat as a scope change.
- LLM02 "same ID, 2026 text names more leak channels": the channels (tool arguments, reasoning traces, logs, embeddings) are from the official 2026 LLM02 text. I did not diff against the full 2025 LLM02 text, and OWASP's What's New does not list this as a change, so the post phrases it as 2026 text naming more channels rather than as an OWASP-declared widening.
- Scope widenings for LLM01 (cross-modal), LLM04 (promoted artifacts), LLM05 (fine-tuning subversion) and LLM10 (generated code) are taken from OWASP's What's New; I did not diff each against the 2025 text. The "package-name hallucination" variant that HackerDNA calls new is in the official LLM04 text (slopsquatting) but I did not verify it was absent in 2025, so the post does not call it new.
- HackerDNA's explanation that Improper Output Handling fell because it is well understood and fixable is attributed to that source in the post. OWASP's own letter only states that it fell from fifth to tenth.
- The ASI primary pointers in the post come from Appendix A of the official PDF. Giskard's one-per-entry table differs because it is a simplification (for example it lists only ASI01 for LLM03 where Appendix A lists several). ASI names follow the 2026 PDF's wording; secondary sources use shorter variants (for example "Tool Misuse", "Supply Chain", "Memory Poisoning").
- Superblocks' claim of a Black Hat launch, and Superblocks' and Giskard's statement that no new categories were added, were not independently confirmed except that OWASP's What's New says new risks were folded into existing entries.
- The evidence lines are our own suggestions, not OWASP text. FairMind product facts (90 workflows, 109 evaluations, 51 frameworks, 2025 IDs still used) come from the brief and were not checked against the codebase.
- Word count of the body was measured by script and sits within the 1,500 to 2,200 target; recheck after edits.
- Rewrite pass (prose de-slop): title, meta_title, meta_description and custom_excerpt reworded; colon removed from title and meta_title, target term kept. Check meta lengths (title tag 49 chars, meta_description under 155).
- Structure: the six numbered "What changed" subsections are merged into one prose section; the ASI pointers that were a single prose paragraph are now a small table (same IDs and names from Appendix A); the per-entry evidence bullets with bold labels are now a two-column table with the same wording. Please check the theme renders three tables cleanly.
- The evidence section now says these are "our examples", which reflects the earlier note that the evidence lines are our own suggestions, not OWASP text.
- Re-map table: one cell reworded from "not only answer text" to "as well as answer text"; meaning unchanged.
- HackerDNA attribution reworded to say the reading is HackerDNA's and does not come from OWASP (OWASP's letter states only the move, per the note above).
- FAQ questions kept as H3 headings, as in the previous draft (the shared brief mentions bold questions; confirm which format the theme and FAQ schema expect).
- Sources list: em dashes after each link replaced with full stops; every item and URL unchanged.
- Remaining grep hits for underscores are the YAML field names in the code block and the UTM parameters in the request-access URL; both intentional.
-->
