---
title: "DPDP Phase 2 is live and AI teams have until May 2027"
slug: dpdp-phase-2-ai-teams-may-2027
status: draft
meta_title: "DPDP Rules 2025 AI duties to finish before May 2027"
meta_description: "DPDP Rules 2025 AI duties start in May 2027. An engineering reading of what changes for training data, consent, erasure, breach response and audits."
custom_excerpt: "Phase 2 of the DPDP Rules covers Consent Manager registration. Phase 3, in May 2027, brings the notice, consent, erasure, security and breach duties that change how AI teams work, and this post sets out the work in order."
tags: [governance, india, deadline]
author: Adhithya Rajasekaran
target_term: "dpdp rules 2025 ai"
last_checked: 2026-11-04
---

This post is an engineering reading of the Act and Rules and is not legal advice. Check anything you act on with counsel.

India's Digital Personal Data Protection Rules were notified in November 2025 and come into force in stages. The second stage starts this month and covers only Consent Manager registration. The third stage, in May 2027, brings in the duties that change how AI systems are trained and operated, so the months until then are the working window for teams that train, fine-tune or serve models on personal data.

## The dates, and where sources disagree

The Rules were published as [G.S.R. 846(E)](https://egazette.gov.in/WriteReadData/2025/267650.pdf). A separate notification, G.S.R. 843(E), sets when the [Act's own sections](https://www.dpdpa.com/dpdpa_enforcement_timeline.html) start, and Rule 1 ties each stage of the Rules to the date they were published in the Gazette.

Sources do not agree on that date. Most give 13 November 2025, a few give 14 November, and one tracker lists notification on the 13th with Gazette publication on the 14th. We could not open the Gazette PDF to settle it, so the table shows both. Plan to the earlier day.

| Stage | What starts | Date (13 Nov anchor) | Date (14 Nov anchor) |
|---|---|---|---|
| 1 | Definitions, Data Protection Board provisions, Rules 1, 2 and 17 to 21 | 13 Nov 2025 | 14 Nov 2025 |
| 2 | Consent Manager registration (Rule 4; Act s.6(9) and s.27(1)(d)) | 13 Nov 2026 | 14 Nov 2026 |
| 3 | Rules 3, 5 to 16, 22 and 23, and Act sections 3 to 17, 27 to 34 | 13 May 2027 | 14 May 2027 |

Stage 3 covers the Act's operative sections as well as the Rules, so the notice, consent, security and breach duties start on the same day as the penalty provisions.

In January 2026 the Government floated cutting the 18-month window to 12 months for Significant Data Fiduciaries, which would have pulled their duties forward to November 2026. The trackers we checked, the most recent dated August and September 2026, say the change has not been notified and that no Significant Data Fiduciary has been designated. Check the Gazette before relying on either point.

## How the Act reaches AI work

The DPDP Act does not mention AI, machine learning or training data. It applies to any processing of digital personal data, and a training run is processing, as are fine-tuning, embedding, retrieval, evaluation sets and prompt logs. It also reaches processing outside India where it is connected with offering goods or services to people in India.

### Notice and consent for training, fine-tuning and retrieval

A Data Fiduciary has to give notice before it asks for consent. [Section 5](https://www.indiacode.nic.in/bitstream/123456789/22037/2/a2023-22.pdf) sets what the notice covers and Rule 3 sets its form. The notice must stand on its own, itemise each type of personal data and each purpose, and describe the products, services or functions that the processing enables.

The purpose line is where AI teams are most likely to fall short. A notice that says "improve our services" gives a thin account of training a model that will later be reused in other products. If you plan to fine-tune on support tickets, the notice should say so, and if customer documents are embedded into a vector store for retrieval, it should say what that store is for. Rule 3 also requires a way to withdraw consent that takes about the same effort as giving it.

Not every dataset needs consent. Section 7 lists a closed set of other grounds, such as data a person volunteered for a stated purpose and processing for employment, and the Act has no general "legitimate interests" ground of the kind found in the GDPR. Settle the lawful basis for each dataset first. Consent collected before the Act started also has to be followed by a notice "as soon as reasonably practicable" under section 5(2), so an old consent screen will not cover an old dataset indefinitely.

### Scraped data, public data and reuse

Section 3(c)(ii) takes out of the Act personal data that the person made public, or that someone under a legal duty to publish made public. That covers some web data, but the exclusion is narrow. Data that leaked, or that came from a private or friends-only source, does not obviously fit, and the text does not say how it applies to bulk collection for training. Assess each source separately and record why it qualifies.

Consent is tied to purposes, so the pattern to audit is a dataset collected for one purpose and later used to train a model for another. Section 17(2)(b) exempts processing for research, archiving or statistics where the data is not used for decisions specific to an individual and prescribed standards are followed. We read that exemption narrowly, and a production model that scores or ranks people sits poorly with it.

## Withdrawal and erasure for trained models

Under [section 8(7)](https://www.indiacode.nic.in/bitstream/123456789/22037/2/a2023-22.pdf) a fiduciary must erase personal data when consent is withdrawn or the purpose is no longer being served, unless a law requires it to keep the data, and it must have its processors erase data it passed to them. Section 6(6) adds that processing must stop within a reasonable time after withdrawal.

The text does not say whether a trained model's weights hold personal data, and it is silent on machine unlearning, retraining and the treatment of embeddings. We have found no official guidance on any of this, so the next paragraph is our engineering position.

Deleting source records, embeddings and index entries from a vector store is a clear, testable action, and you should be able to show it was done. For training sets, keep lineage of which records went into which run, because without it you cannot answer a withdrawal request. For a model already trained, decide and document in advance how you will handle a request, for example by excluding the record from the next training run on a stated schedule. A regulator may accept a reasoned policy more readily than silence, but that is a judgement and a person should make it.

Retention complicates the design. Rule 8(3) requires personal data, related traffic data and processing logs to be kept for at least one year for specified purposes and then erased, and Rule 6 separately asks for one-year log retention as a security measure. Both pull against erasure, and the erasure procedure has to account for them. Rule 8 also sets an inactivity erasure timer, with 48 hours' notice, for classes of fiduciary listed in the Third Schedule, so check whether you fall into one.

## Security, breaches and children's data

[Rule 6](https://egazette.gov.in/WriteReadData/2025/267650.pdf) sets a floor for reasonable security safeguards. It lists encryption, masking or tokenisation, access controls on the systems involved, logging and monitoring of access, backups for continuity, one-year log retention, and security terms in processor contracts. For an AI team the processors include model API vendors, GPU clouds, labelling vendors and observability tools, and each contract has to carry security terms while the fiduciary stays responsible for what the vendor does. Prompts and completions that contain personal data are data you hold, and a prompt log stored without access controls is an obvious audit finding.

[Rule 7](https://egazette.gov.in/WriteReadData/2025/267650.pdf) sets two breach tracks. Each affected person must be told without delay, in plain language, with the likely consequences and the steps they can take. The Board must be told without delay and then given detailed information within 72 hours, unless it allows longer on written request. Decide in advance what counts as a breach in your AI systems. Candidates include a model that emits another user's data, a retrieval index that ignores access control and a leaked prompt log. Name who declares the incident and who writes to the Board.

Section 9 and [Rule 10](https://egazette.gov.in/WriteReadData/2025/267650.pdf) require verifiable parental consent before processing a child's data, and a child is anyone under 18. The Act also bars tracking or behavioural monitoring of children and targeted advertising aimed at them. Limited exemptions exist for some fiduciaries and purposes, so read them before assuming one applies. If under-18s use your product, or you cannot tell whether they do, the personalisation, recommendation and engagement models are the likely trouble spots.

## Significant Data Fiduciaries, transfers and penalties

The Government can designate a fiduciary, or a class of them, as a Significant Data Fiduciary. Section 10 then requires an India-based Data Protection Officer, an independent data auditor, and periodic impact assessments and audits. [Rule 13](https://egazette.gov.in/WriteReadData/2025/267650.pdf) sets the cycle at once every twelve months from designation, and the person doing the assessment and audit sends a report of significant observations to the Board.

AI teams should read Rule 13(3) closely. It requires the fiduciary to exercise due diligence to verify that technical measures, including algorithmic software used for processing, are not likely to pose a risk to the rights of Data Principals. The Rule does not define a method. Rule 13(4) also lets the Government require that specified data stay in India.

Transfer outside India is allowed, subject to conditions the Government may set, and [Rule 15](https://egazette.gov.in/WriteReadData/2025/267650.pdf) applies those conditions where data would be made available to a foreign state or an entity under its control. Check where your training, inference and logging infrastructure sits and which vendors can reach it.

The Act's Schedule sets maximum penalties. Failing to keep reasonable security safeguards can draw up to Rs 250 crore. Failing to notify the Board or affected people of a breach, or failing the children's duties, can each draw up to Rs 200 crore. Significant Data Fiduciary failures can draw up to Rs 150 crore, and other breaches of the Act or Rules up to Rs 50 crore.

## A checklist for the months before May 2027

1. Inventory the personal data in your AI pipelines (training sets, fine-tuning sets, evaluation sets, vector stores, prompt and completion logs) and record the source, purpose and lawful basis for each.
2. Rewrite notices so they itemise data types and purposes, model training included, and offer a withdrawal route as easy as the consent route.
3. Build lineage that shows which records fed which model version and index.
4. Write an erasure and withdrawal procedure covering source stores, vector stores, logs and processors, with a documented position on trained models and a named owner.
5. Map the one-year log and data retention duties against your erasure commitments.
6. List every vendor that touches personal data, model APIs included, and add security terms to their contracts.
7. Define breach scenarios specific to your AI systems and run a 72-hour drill.
8. If under-18s can use the product, design parental consent and turn off tracking features.
9. Decide whether you may be designated a Significant Data Fiduciary. If so, find an India-based DPO and an independent auditor, and plan the first impact assessment.
10. Publish rights and grievance channels, noting that Rule 14 sets a maximum of ninety days for grievance responses.
11. Re-check the Gazette for amendments, new orders on cross-border data and any Significant Data Fiduciary designations.

## About FairMind

FairMind is an agentic AI governance platform with 90 governance workflows and 109 evaluations across 51 frameworks, one of which is DPDP. Every workflow has a human approval gate and a hash-chained record of each run, and test results are kept as Evidence Passports that record the subject, versions, threshold, artifacts, integrity hashes, result, limitations and reviewer decision. That evidence supports a compliance decision, which a named person makes, together with a regulator or auditor where relevant. You can [request access](https://fairmind.xyz/request-access?utm_source=blog&utm_medium=post&utm_campaign=dpdp-phase-2-ai-teams-may-2027) to see the records for your own systems, and our [DPDP Act guide](https://fairmind.xyz/frameworks/dpdp-act/) covers the framework in more detail.

## FAQ

### Does the DPDP Act say anything about AI training or machine unlearning?

The Act and Rules mention neither. The duties on notice, consent, erasure and security apply to training data as they do to any other personal data. The text does not address how a trained model should respond when consent is withdrawn.

### Is May 2027 the deadline for everything?

Consent Manager registration starts in November 2026, and most other duties start in May 2027 together with the penalty provisions. A proposal to bring some Significant Data Fiduciary duties forward was floated in January 2026, and the trackers we checked say it had not been notified.

### Does public data scraped from the web fall outside the Act?

Only where it fits section 3(c)(ii), meaning the person made it public or someone obliged by law to publish it did. Other scraped data is not clearly excluded. Assess each source and record your reasoning.

### Do foreign companies need to comply?

The Act applies to processing outside India where it relates to offering goods or services to people in India. If you serve Indian users, treat it as applicable and take advice.

## Sources
- [Digital Personal Data Protection Rules, 2025, G.S.R. 846(E) (Gazette of India)](https://egazette.gov.in/WriteReadData/2025/267650.pdf), the Rules, covering commencement (rule 1), notice, security, breach, retention, children, Significant Data Fiduciaries and transfer.
- [Digital Personal Data Protection Act, 2023 (India Code)](https://www.indiacode.nic.in/bitstream/123456789/22037/2/a2023-22.pdf), sections 3, 5 to 10, 16, 17 and the penalty Schedule.
- [MeitY, Data Protection Framework](https://www.meity.gov.in/data-protection-framework), the ministry's page for the Act, Rules and explanatory material.
- [DPDPA enforcement timelines, reproducing G.S.R. 843(E)](https://www.dpdpa.com/dpdpa_enforcement_timeline.html), staged commencement of the Act's sections (secondary reproduction).
- [India Data Law, DPDP deadlines](https://indiadatalaw.org/deadlines/), a tracker noting the 13 and 14 November dates and that the 12-month SDF proposal was not notified (secondary).

<!-- REVIEWER NOTES (not for publication)
- PRIMARY TEXT NOT OPENED: egazette.gov.in PDF failed TLS verification, meity.gov.in and indiacode.nic.in returned 403 to WebFetch (I did not bypass the certificate check). All rule and section wording was read from the dpdpa.com mirror, which reproduces the Gazette and Act text, plus secondary summaries. Every cited Rule/section needs a check against the Gazette PDF (and corrigendum G.S.R. 892(E) of 10 Dec 2025, which a source says corrects eight points). Note the mirror and one draft-rules page use draft numbering in places; I used the final numbering (rule 6 security, 7 breach, 8 retention, 10 children, 13 SDF, 14 rights, 15 transfer).
- 13 vs 14 NOVEMBER NOT RESOLVED. G.S.R. 846(E)/843(E) are consistently reported as dated 13 Nov 2025. Rule 1 anchors to publication in the Gazette. Some sources (Wikipedia, Chambers, one regulatory alert, indiadatalaw.org) say the Gazette publication was 14 Nov. Several trackers give 13 Nov 2026 and 13 May 2027. Both are shown in the table. Needs a look at the Gazette header.
- TITLE ISSUE: "Phase 2 is live" is only true from 13 (or 14) Nov 2026. Today is 4 Nov 2026. Publish on or after the start date, or retitle (e.g. "DPDP Phase 2 starts this month").
- Stage 1 contents: Rules 1, 2, 17-21 and the Act sections list come from secondary reproductions of rule 1 and G.S.R. 843(E). Board establishment (G.S.R. 844(E)) is from a tracker only. I did not cite it in the body.
- Stage 3 Act sections (3 to 17, 27 to 34, 36, 37, 44(2)) from the dpdpa.com reproduction of G.S.R. 843(E), not the Gazette.
- 12-MONTH SDF PROPOSAL: reported by Business Standard (403 to me), Mondaq, S.S. Rana, Chambers, Legal500 and trackers (Aug-Sep 2026) as unnotified. I found nothing from the last weeks. A notification after those dates is possible. Verify before publication.
- No SDF designated: stated by trackers (indiadatalaw.org as of Aug 2026, dpdprules.org as of 23 Aug 2026). Unverified against any official source.
- Supreme Court challenges to the Act (hearings reported 16 Feb and 7 Aug 2026 per indiadatalaw.org) are not mentioned in the body. Unverified, secondary only. Consider whether to add.
- Rule 8(3) one-year retention: I read it as applying to purposes in the Seventh Schedule; I could not read the Seventh Schedule or the Third Schedule. The class list and inactivity period in the Third Schedule (draft: large e-commerce, online gaming, social media; three years) are not stated in the body. A Business Today article reports three years and 48 hours' notice. Check the final Schedule.
- Rule 6(1)(e) and Rule 8(3) both mention one-year retention. I describe them as pulling against erasure. The interplay is my reading.
- Rule 10 exemptions (Fourth Schedule, and the final rule number for the exemptions) not read. Body only says limited exemptions exist.
- Section 6(6) (stop processing after withdrawal) and section 6(4) read from the mirror. Section 6(1) (consent free, specific, informed, limited to necessary data) was NOT re-read; the body says only that consent must be withdrawable and tied to purposes.
- Section 3(b) extraterritorial reach (foreign processing linked to offering goods or services in India) is stated from my own knowledge of the Act and was not re-read this session. Used in the body and FAQ.
- Section 16 (Government may restrict transfers to notified countries) was read from the mirror, which pairs it with a different rule number than I used. I cite Rule 15 for the transfer rule from the mirror's page; the body does not describe section 16.
- Section 17(2)(b) research exemption: statutory wording from the mirror, which also shows a conflicting second version of the section. My "read it narrowly" is an interpretation.
- Section 5(2) refresh of pre-Act consent: from the mirror. The quoted phrase "as soon as reasonably practicable" is under 15 words.
- Penalty ceilings (250/200/200/150/50 crore): from the mirror's Schedule page. Not checked against India Code.
- Machine unlearning / model weights: I found no official guidance and wrote none. The three bullets are an engineering position, flagged as such. A lawyer should review.
- Rule 14 90-day grievance maximum from the mirror's rule 14 page only.
- Rule 13(4) localisation wording from the mirror; the Government's committee-based approach was paraphrased.
- G.S.R. 843(E) link points to a secondary reproduction because I found no verified primary URL for it. Replace with the Gazette link if available.
- meity.gov.in/data-protection-framework is cited as the ministry page; I could not open it (403) and did not confirm the final Rules or FAQs are posted there.
- FairMind facts (90 workflows, 109 evaluations, 51 frameworks, approval gate, hash chain, Evidence Passport fields) are taken from the brief, not checked against the product.
- REWRITE (Nov 2026): prose rewritten to remove AI-writing patterns. Facts, dates, rule and section numbers, figures and URLs are unchanged. Points to check follow.
- Title and meta_title no longer use a colon. New title: "DPDP Phase 2 is live and AI teams have until May 2027". meta_title now contains the exact target term "DPDP Rules 2025 AI".
- The disclaimer is now plain text (was italic); it keeps "not legal advice".
- First person "I" in the body (could not open the Gazette PDF, trackers checked, no guidance found) is now editorial "we".
- The stage 3 row in the table lists Act sections 3 to 17 and 27 to 34, but the note above says the dpdpa.com reproduction also lists 36, 37 and 44(2). Table left as it was; decide whether to add them.
- The draft said Rule 8(3) and Rule 6 "pull in opposite directions". Both are retention duties, so the body now says both pull against erasure.
- The machine-unlearning position, formerly three bullets, is now one paragraph with the same three points.
- FAQ on scraped data said other scraped data is "not clearly covered"; it now says "not clearly excluded" (same meaning, by the section 3(c)(ii) exclusion). Check it reads as intended.
- Source list descriptions now follow the link after a comma instead of a dash; wording otherwise unchanged.
-->
