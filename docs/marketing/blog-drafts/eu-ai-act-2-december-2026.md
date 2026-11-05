---
title: "EU AI Act on 2 December 2026, Article 50(2) marking and two new prohibitions"
slug: eu-ai-act-2-december-2026
status: draft
meta_title: "EU AI Act December 2026, Article 50(2) and new bans"
meta_description: "The EU AI Act December 2026 changes cover Article 50(2) marking for generative systems already on the market and new bans on sexual deepfakes and CSAM."
custom_excerpt: "From 2 December 2026, generative systems already on the market must mark their output in machine-readable form, and new prohibitions cover non-consensual sexual deepfakes and CSAM generators. This post reads the amending text and sets out a four-week plan."
tags: [governance, eu-ai-act, deadline]
author: Adhithya Rajasekaran
target_term: "eu ai act december 2026"
last_checked: 2026-11-04
---

This post is an engineering reading of the text. Check your own position with counsel.

On 2 December 2026, four weeks from now, two parts of the EU AI Act start to apply. Providers of generative systems already on the market must mark synthetic output in a machine-readable way, and two new prohibitions on sexual deepfakes and child sexual abuse material take effect. Most Digital Omnibus coverage is about the delayed high-risk rules, so this post covers the December changes and a plan. We read the amending regulation itself, and say so where a point rests on a Commission guideline or a law-firm note.

## What the Digital Omnibus changed

The Digital Omnibus on AI is [Regulation (EU) 2026/1744](https://eur-lex.europa.eu/eli/reg/2026/1744/oj), adopted on 8 July 2026 and published in the Official Journal on 24 July 2026. Its Article 4 says it enters into force on the third day after publication, which is 27 July 2026. It amends the AI Act, [Regulation (EU) 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj), along with two other regulations.

Two amendments set the December date. A new paragraph 4 in Article 111 gives providers of generative systems placed on the market before 2 August 2026 until 2 December 2026 to comply with Article 50(2). A rewritten Article 113 makes the new prohibitions in Article 5(1)(ba), 5(1)(bb), 5(1a) and 5(1b) apply from the same day. The rest of Article 50 applied from 2 August 2026, as planned.

## What Article 50(2) requires

[Article 50(2)](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-50) applies to providers of AI systems, including general-purpose AI systems, that generate synthetic audio, image, video or text. Outputs must be marked in a machine-readable format and be detectable as artificially generated or manipulated. The technical solution has to be effective, interoperable, robust and reliable as far as technically feasible, and feasibility takes into account the type of content, the cost of implementation and the generally acknowledged state of the art. The duty sits with the provider, so a team that only deploys someone else's model mainly faces the labelling rules in Article 50(4).

The Commission adopted its [Article 50 guidelines](https://ai-act-service-desk.ec.europa.eu/sites/default/files/2026-07/guidelines_on_the_implementation_of_the_transparency_obligations_for_certain_ai_systems_under_article_50_of_the_ai_act_bzptwqhk0ikg1dtlddap41psfy_131215.pdf) on 20 July 2026. They are non-binding, since only the Court of Justice can give an authoritative reading, but they are the best signal of how regulators will apply the text. A provider may use one technique or a combination, provided the overall solution meets the four quality tests (paragraph 72). Feasibility is objective, so you need not use a technique that does not yet exist or cannot fit your architecture (paragraph 81). The state of the art means accepted good practice rather than experimental research, and you must keep adapting as it moves (paragraph 83).

Detection has to be available to the people exposed to the content, with results a human can read (paragraphs 75 and 77). You may rely on an upstream provider's marking or a third-party service, but you remain responsible for showing compliance (paragraph 74). For agents, an action is in scope when it produces content that people perceive, while reasoning steps and web requests fall outside (paragraph 63).

The guidelines identify three exceptions (paragraphs 89 to 93). They cover systems performing an assistive function for standard editing such as grammar, formatting or compression (changes to meaning, style or intent go beyond this), systems that do not substantially alter the input data or its meaning, and systems authorised by law to detect, prevent, investigate or prosecute criminal offences. Paragraphs 86 to 88 also describe narrow, cumulative conditions under which lighter marking or none may be enough, for outputs locked inside a closed physical product, strictly technical business-to-business output that never leaves the company, and ephemeral real-time content where users are told it is generated.

## Who gets the extra time

The relief in new Article 111(4), for generative systems placed on the market before 2 August 2026, covers only the steps needed to comply with Article 50(2). A system that interacts with people still had to tell them they were dealing with an AI system from 2 August 2026 (guidelines, paragraph 153). Systems placed on the market on or after 2 August 2026 get no extra time, and content created before 2 August 2026 does not need retroactive marking (guidelines, paragraph 154; [Commission FAQ](https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act)).

Article 111(4) says "placed on the market", while the guidelines say "placed on the market or put into service". If you are in a grey area, such as an internal tool later offered to customers, ask counsel.

## The Code of Practice

The [Commission's page](https://digital-strategy.ec.europa.eu/en/policies/code-practice-ai-generated-content) for the Code of Practice on Transparency of AI-generated Content lists a closing plenary on 10 June 2026 and reports about 190 signatories by the end of July. Section 1 is for providers (marking and detection) and section 2 for deployers (labelling deepfakes and certain public-interest text).

According to the [Commission FAQ](https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act), the Code is voluntary, and the Commission and the AI Board have assessed it as adequate, although the FAQ gives no date for that assessment. Signatories can rely on it to show compliance with Article 50(2), (4) and (5). Non-signatories must show compliance by other adequate means and may get more information requests. This follows [Article 50(7)](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-50) as rewritten by the Omnibus, under which the Commission may adopt an implementing act with common rules if it finds a code inadequate.

Some law-firm summaries say the Code requires at least two layers of marking and describe its effect as a presumption of conformity. We could not confirm either point on a Commission page, so check the Code's own text. Signing gives you a route to showing compliance, and the decision on whether your marking is adequate still rests with the people responsible for the system.

## Marking techniques and their limits

No single technique meets all four quality tests everywhere, so the guidelines accept combinations. Recital 133 of the AI Act, as the guidelines cite it, names watermarks, metadata, cryptographic provenance, logging and fingerprints.

| Technique | What it gives you | Where it fails |
|---|---|---|
| Metadata (EXIF, XMP, ID3, similar) | Cheap, widely supported | Lost when a file is re-encoded, screenshotted or rewritten by a platform |
| C2PA Content Credentials | Signed, tamper-evident record of origin and edits | Can be separated from the asset, and the signature reveals tampering without preventing it |
| Invisible watermark | Travels with the pixels or samples and survives some edits | How well it survives varies by method and content type. The guidelines name adversarial removal as a concern. Detection usually needs a detector you control |
| Fingerprint or output logging | Lets you check whether you generated something | Needs stored records, which raises privacy and retention questions |
| Text marking | Statistical text watermarks and signed metadata exist | Copied text carries no file metadata, and paraphrasing weakens statistical marks. Text is the hardest modality |

The [C2PA specification](https://spec.c2pa.org/specifications/specifications/2.2/specs/C2PA_Specification.html) lets a manifest that has been separated from its asset be matched again through a soft binding, which is a fingerprint or a watermark. Many designs therefore pair a signed manifest with a watermark.

A provider that marks every output but offers no way to check it has not met the detectability requirement. The guidelines prefer public, industry-standard detection, and until standards exist they allow your own or a shared tool if it stays interoperable (paragraph 76).

## The new prohibitions

Paraphrasing the [Omnibus text](https://eur-lex.europa.eu/eli/reg/2026/1744/oj), new point (ba) of Article 5(1) bans placing on the market, putting into service or using an AI system that generates or manipulates realistic images, video, audio or similar material showing an identifiable person's intimate parts, or showing them engaged in sexually explicit activity, without that person's freely given, specific, informed, unambiguous and explicit consent. Point (bb) bans the same for material or performances within Directive 2011/93/EU, the child sexual abuse directive, except where a "without right" defence applies under national law.

New Article 5(1a) sets separate tests for providers and deployers. A provider is caught where generating such material is the system's intended purpose, or where it is a reasonably foreseeable and reproducible outcome of the system's design, training, architecture, capabilities or user-facing features without significant technical modification, and the system lacks reasonable and adequate safeguards to prevent it and to correct observed or reported misuse. A deployer is caught only where it uses the system for the purpose of generating the material. Article 5(1b) adds that manipulation which neither increases the exposure of intimate parts nor changes the nature of the sexual activity does not count as manipulation.

Recitals are not operative text but show intent. Recital 12 lists safeguards a provider might use, including data cleaning, refusal training, safe prompt design, output controls, runtime guardrails, content classification and filtering, usage restrictions, abuse detection and notice-and-action mechanisms. After observed or reported circumvention, reasonable corrective measures should follow, taking the release strategy (such as an open-source release) into account. For model providers, the sensible reading is that "reasonable and adequate" is judged against the state of the art and foreseeable circumvention. A one-off filter is unlikely to meet that, so plan for a documented set of safeguards, an abuse-report channel that someone acts on, and evidence that the safeguards were tested.

If you build on someone else's model, the ban reaches you only when you use the system to produce this material. Your exposure is then mostly product design, meaning what your interface lets users ask for, what you log, and what you do when you learn of misuse.

Recital 13 says legitimate red-teaming and evaluation to check compliance with the CSAM ban should not be caught. How far that protects you under national criminal law is a question for counsel, to answer before you run any such test.

## All AI Act dates after the Omnibus

| Date | What applies | Source |
|---|---|---|
| 2 Feb 2025 | Chapters I and II, including the Article 5 prohibitions | [Art. 113](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-113) |
| 2 Aug 2025 | General-purpose AI obligations (Chapter V), governance and penalties chapters | [Art. 113](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-113) |
| 27 Jul 2026 | Omnibus in force; Articles 102 to 110 apply | [Omnibus](https://eur-lex.europa.eu/eli/reg/2026/1744/oj) |
| 2 Aug 2026 | General date of application, including Article 50 | [Art. 113](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-113) |
| 2 Dec 2026 | Article 50(2) for generative systems placed on the market before 2 Aug 2026; Article 5(1)(ba), (bb), (1a), (1b) | [Omnibus](https://eur-lex.europa.eu/eli/reg/2026/1744/oj) |
| 2 Aug 2027 | General-purpose AI models placed on the market before 2 Aug 2025 | [Art. 111](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-111) |
| 2 Dec 2027 | High-risk systems under Annex III | [Omnibus](https://eur-lex.europa.eu/eli/reg/2026/1744/oj) |
| 2 Aug 2028 | High-risk systems under Annex I | [Omnibus](https://eur-lex.europa.eu/eli/reg/2026/1744/oj) |
| 2 Aug 2030 | Compliance by high-risk systems intended for public authorities placed on the market earlier | [Omnibus](https://eur-lex.europa.eu/eli/reg/2026/1744/oj) |

Article 50(1), (3) and (4) have applied since 2 August 2026, and the Omnibus did not defer them. The other Article 5 prohibitions have applied since 2 February 2025, and the obligations for general-purpose AI models since 2 August 2025. The Code of Practice remains voluntary and the guidelines remain non-binding. Recital 12 makes clear that the new bans do not stop providers building the capability to generate or manipulate media; they cover only the two categories above and do not reach all nudity or all deepfakes.

## A plan for the next four weeks

Spend the first week on scope.

- List every system you provide that generates audio, image, video or text.
- Record when each was placed on the market, which decides the grace period.
- Note which systems fall under an exception, and why.

In the second week, settle marking and detection.

- For each modality, write down the techniques used and why they meet the four tests as far as feasible.
- Check whether an upstream provider's marking covers you, and keep their evidence.
- Define how a third party can check an output, and name who owns that service.

The third week is for the prohibitions.

- Review safeguards against Article 5(1)(ba) and (bb), such as input filters, output classifiers, refusals and rate limits.
- Confirm the abuse-report channel has a named owner and a response time.
- Ask counsel how to handle testing and reports involving CSAM.

Use the last week to test and record decisions.

- Run marking and detection checks on production-like output, including re-encoded, cropped and screenshotted samples.
- Write down the limits you found, and have a named reviewer sign off on what remains.
- Decide whether to sign the Code, and record why.

## About FairMind

FairMind is an agentic AI governance platform with 90 governance workflows and 109 evaluations across 51 frameworks, including the [EU AI Act](https://fairmind.xyz/frameworks/eu-ai-act/). Every workflow has a human approval gate and a hash-chained run record, and test results become Evidence Passports recording the subject, versions, threshold, artifacts, integrity hashes, result, limitations and reviewer decision. For this deadline it helps with the record of what you tested, against what threshold, and who decided. It does not mark your content; marking stays in your own pipeline, and people make the compliance decision, which regulators or auditors may review.

[Request access](https://fairmind.xyz/request-access?utm_source=blog&utm_medium=post&utm_campaign=eu-ai-act-2-december-2026)

## FAQ

**Does the grace period apply to a new model I launch in November 2026?**
No. Article 111(4) covers only systems placed on the market before 2 August 2026, and Article 50(2) already applies to anything placed on the market after that.

**Does Article 50(2) require visible labels?**
No. It requires machine-readable marking and detectability. Visible labelling of deepfakes is a separate duty for deployers under Article 50(4).

**Is a metadata tag alone enough?**
The text does not say. The guidelines allow lighter metadata marking only in narrow cases, such as outputs locked inside a closed physical product. For public-facing output, expect to need more.

## Sources

- [Regulation (EU) 2026/1744 (Digital Omnibus on AI), EUR-Lex](https://eur-lex.europa.eu/eli/reg/2026/1744/oj) (publication date, entry into force, new Article 111(4), Article 113 amendments, new Article 5(1)(ba), (bb), (1a), (1b), Article 50(7), recitals 12, 13 and 38)
- [Regulation (EU) 2024/1689 (AI Act), EUR-Lex](https://eur-lex.europa.eu/eli/reg/2024/1689/oj) (the base text being amended)
- [AI Act Service Desk, Article 50](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-50) (Article 50(2) requirements, qualifiers and exceptions)
- [AI Act Service Desk, Article 111](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-111) (paragraph 3 on GPAI models placed before 2 Aug 2025, by 2 Aug 2027, and new paragraph 4)
- [AI Act Service Desk, Article 113](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-113) (application dates by chapter)
- [Commission Guidelines on Article 50 transparency obligations (20 July 2026)](https://ai-act-service-desk.ec.europa.eu/sites/default/files/2026-07/guidelines_on_the_implementation_of_the_transparency_obligations_for_certain_ai_systems_under_article_50_of_the_ai_act_bzptwqhk0ikg1dtlddap41psfy_131215.pdf) (marking and detection reading, exceptions, transitional period, retroactivity)
- [Commission FAQ on Article 50 transparency obligations](https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act) (transitional period, Code of Practice adequacy assessment)
- [Commission page on the Code of Practice on Transparency of AI-generated Content](https://digital-strategy.ec.europa.eu/en/policies/code-practice-ai-generated-content) (structure, 10 June 2026 plenary, signatory count)
- [C2PA Technical Specification 2.2](https://spec.c2pa.org/specifications/specifications/2.2/specs/C2PA_Specification.html) (soft bindings, manifest recovery, tamper-evidence)
- [Jones Day, final Code of Practice on marking and labelling](https://www.jonesday.com/en/insights/2026/06/european-commission-publishes-final-code-of-practice-on-marking-and-labelling-aigenerated-content) (secondary source for the multi-layer approach; not a primary text)
- [FairMind, EU AI Act framework page](https://fairmind.xyz/frameworks/eu-ai-act/) (framework coverage)

<!-- REVIEWER NOTES (not for publication)
- EUR-Lex HTML pages could not be fetched (the server returned an empty HTTP 202 to automated requests). The Omnibus was read from the Official Journal PDF (OJ L, 24.7.2026) obtained via the afec.es mirror (afec.es/documentos/english/regulation-2026-1744.pdf). Its header and article text matched the EUR-Lex ELI. Please re-read the Omnibus on EUR-Lex before publishing.
- The original AI Act text (Regulation 2024/1689) was NOT read directly. Article 50(2), Article 111(3) and the Article 113 base dates come from the Commission's AI Act Service Desk pages (which mark amended passages) and the Commission's guidelines. Treat those as Commission publications, not EUR-Lex.
- Discrepancy: the Service Desk Article 113 page says it is based on the EUR-Lex consolidated text as at 27 July 2026. Your tracker says no consolidated text was found. Not resolved. We cite the Omnibus and Service Desk, not a consolidated text.
- Regulation number, publication date (24 Jul 2026) and the 2 Dec 2026 dates in the tracker are confirmed in the primary text. Entry into force is stated in Article 4 as the third day after publication, which computes to 27 Jul 2026. The Omnibus itself does not print "27 July"; it is derived. The Service Desk page also gives 27 July. One secondary source we saw said 2 July 2026; this is wrong.
- Tracker nuance: the Article 50(2) relief is not an amendment to Article 50(2). It is new Article 111(4). The prohibitions are Article 5(1)(ba), (bb), (1a), (1b) via Article 113(3)(a). Tracker described "non-consensual sexual deepfakes, CSAM generators"; the primary text is wider and more precise (providers: intended purpose, or foreseeable and reproducible outcome without adequate safeguards; deployers: use for the purpose). The post follows the primary text.
- Scope wording varies: Article 111(4) says "placed on the market"; the guidelines (para 153) say "placed on the market or put into service"; Omnibus recital 38 says "already placed their systems on the market". Flagged in the post (first two only).
- Guideline paragraph numbers cited (63, 72-77, 81, 83, 86-88, 89-93, 153, 154) were read from the PDF text extraction. The post says "three exceptions"; the Service Desk and Commission quick facts describe two bullet points, the guidelines say three.
- Code of Practice: final publication is described as June 2026, with a "closing plenary on 10 June 2026" on the Commission page. Jones Day says published 10 June. The Commission and AI Board adequacy assessment is confirmed in the Commission FAQ with no date; secondary sources gave 8 July (Commission) and 9 July (AI Board); not confirmed, not used. A Freshfields piece from late June still described guidelines as pending, consistent with the 20 July adoption.
- "At least two layers" and "presumption of conformity" come only from law-firm summaries (Jones Day, SCL). The Commission FAQ does not use the term "presumption of conformity". The post flags both as unconfirmed. Check the Code's text itself; I could not retrieve the final PDF.
- "About 190 signatories by end of July 2026" is from the Commission Code page (read via a page-summarising fetch tool). Confirm on the page before publishing.
- Article 50(5) (human-readable detection result, timing) was read via the guidelines (para 75, 77), not the base text.
- Article 111(2) as amended: the 2 Aug 2030 date for public-authority high-risk systems is from the Omnibus text. I did not verify it against any other source.
- Table row "2 Aug 2025: governance and penalties chapters" is taken from the Service Desk page's Article 113 summary (Chapter III Section 4, Chapters V, VII, XII, Article 78, excluding Article 101). Not independently confirmed in EUR-Lex.
- Penalties and fine levels for Article 5 and Article 50 are deliberately not stated. The Commission quick-facts page returned a garbled fine summary and I did not read Article 99 directly.
- Technique table: the "where it fails" column for metadata, watermark and text marking is engineering judgement, not cited to a source other than the guidelines' general robustness definition (para 79) and the C2PA soft-binding sections. No success-rate statistics are given on purpose.
- FairMind section uses only the facts supplied. The sentence "FairMind does not mark your content" restates that no marking feature is claimed; confirm with product.
- I did not read the Commission's guidelines on Article 5 prohibitions as updated for the new bans; if the Commission has published updated Article 5 guidance, add it.
- Length: body is about 2,200 words with link URLs and table markup stripped (about 2,290 by a raw count that includes URLs), including tables, the FairMind section and the FAQ. It is at the top of the 1,500-2,200 range; trim the "qualifiers" bullets first if an editor wants it shorter.
- Rewrite (style pass): prose rewritten throughout; no facts, dates, figures, links or sources added or removed. Check these specific changes:
- The statutory wording "effective, interoperable, robust and reliable" (Article 50(2)) is kept despite the house ban on "robust", because it is the legal text. The table cell that said "Robustness varies" now says "How well it survives varies".
- The italic disclaimer is now a plain sentence. Bold was removed from the 2 Dec 2026 row of the dates table and from "providers"/"deployers" in the Article 5(1a) paragraph.
- The "What did not change" bullet list is now a prose paragraph under the dates table. The line "High-risk dates are 2 December 2027 and 2 August 2028" was dropped from it because the table already gives both dates.
- The "qualifiers" bullets from the guidelines and the three exceptions are now prose; paragraph citations are unchanged.
- Source list separators changed from em dashes to brackets; every item and URL is unchanged.
- Title and meta fields rewritten without colons; meta_description now contains the target term verbatim.
-->
