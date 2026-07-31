# FairMind-E Expert Panel: Recruitment Pack

Everything needed to go from zero raters to a closed panel of 15. Recruitment
is the longest-lead item in the whole study: the instrument is built and the
analysis runs in seconds, but assembling 15 qualified professionals takes
weeks of calendar time that cannot be compressed. Start before the measurement
study, not after.

## 1. Who you need

| Role group | Target | Qualifies |
| --- | --- | --- |
| GRC | 5 | Governance, risk, compliance, audit, or regulatory roles who review systems before release. Internal audit, model risk management, DPO, AI governance leads. |
| ML_ENG | 5 | Engineers or data scientists who train, fine-tune, or operate models in production and would be on the answering side of a release review. |
| ESG | 5 | Sustainability, ESG reporting, carbon accounting, or environmental compliance professionals. CSRD/ESRS reporting experience is ideal but not required. |

**Minimum bar for all groups:** at least two years of professional experience
in the role, and enough context to read a system description and form a
release judgment. Raters do not need AI expertise in the ESG group, nor
sustainability expertise in the ML group. That spread is the point: the study
asks whether the mechanism produces agreement across professional
backgrounds, so recruiting three groups that already think alike would
weaken the result rather than strengthen it.

**Sampling caution.** A panel drawn entirely from one company, one client
list, or the authors' immediate colleagues is a convenience sample, and a
reviewer will say so. Aim for at least six distinct organisations across the
15 raters, and record each rater's organisation type (not name) so the paper
can report the spread. If the panel does end up concentrated, report it as a
limitation rather than leaving it for a reviewer to discover.

## 2. Where to find them

Ordered roughly by yield per unit effort:

1. **Direct professional network, one hop out.** Ask contacts for an
   introduction to someone in the target role rather than asking the contact
   themselves. This gets you out of the immediate-colleague problem while
   keeping the warm-intro response rate.
2. **Referral chaining.** Every accepted rater is asked, at the end, to
   suggest one person in a role group that is still short. This is the single
   highest-yield channel once the first few are in.
3. **Professional communities.** AI governance and responsible-AI
   communities, ISACA and IIA chapters, model-risk-management groups, CSRD
   and sustainability-reporting forums, local AI ethics meetups.
4. **Conference and workshop contacts.** People who present or attend at
   governance and sustainable-computing venues are pre-selected for interest
   and are usually receptive.
5. **Open call on professional social platforms.** Lowest yield and the
   highest screening burden, but useful for filling a stubborn gap in one
   role group.

**Over-recruit.** Plan for 20 to 22 commitments to land 15 completions.
Attrition between "yes" and "submitted" is normal and is not a reflection on
the study.

## 3. Outreach templates

Keep the first message short. The detailed information sheet is in
`INSTRUMENT.md` and goes out with the packet, not with the invitation.

### 3.1 GRC

> Subject: 45 minutes of your governance judgment for an academic study
>
> Hi [name],
>
> I am running a research study on how organisations decide whether an AI
> system is ready to release when its environmental evidence is incomplete or
> hard to trust. The results are going into an academic paper on AI governance
> mechanisms.
>
> I am looking for people who actually sit in review-and-approve seats, which
> is why I am asking you. The task is to read eight short system profiles and
> record, for each one, whether you would release it and what evidence you
> would require first. It takes about 45 to 60 minutes, and you can do it in
> your own time within a two-week window.
>
> Nothing is recorded against your name or your employer. The systems are all
> fictional. There is no product being sold here and no follow-up sales
> contact; it is a research study and you would be acknowledged in the paper
> if you want to be.
>
> Would you be willing? If it is not for you but someone in your network fits,
> an introduction would help just as much.
>
> [name, affiliation, ORCID or institutional page]

### 3.2 ML engineering

> Subject: 45 minutes of engineering judgment for an academic study
>
> Hi [name],
>
> I am researching how release decisions get made for AI systems when the
> carbon and energy numbers attached to them are of uncertain quality. The
> study is going into an academic paper, and I need people who have actually
> trained or shipped models in production.
>
> The task: eight short system profiles, and for each, your call on whether it
> should be released and what evidence you would want first. About 45 to 60
> minutes, done whenever suits you inside a two-week window.
>
> You do not need any sustainability or carbon-accounting background. That is
> deliberate: part of what the study measures is whether people from different
> professional backgrounds converge on the same call. Responses are anonymous,
> the systems are fictional, and this is not a disguised sales pitch.
>
> Interested? And if not, is there someone on your team who might be?
>
> [name, affiliation, ORCID or institutional page]

### 3.3 ESG and sustainability

> Subject: 45 minutes of sustainability judgment for an academic study
>
> Hi [name],
>
> I am running an academic study on environmental evidence quality in AI
> deployment decisions: specifically, what reviewers do when a carbon figure
> exists but its provenance is weak. Your side of the house is the one that
> deals with this problem in every other reporting context, which is why I am
> asking.
>
> The task is to read eight short system profiles and record whether you would
> approve each for release and what evidence you would require. Roughly 45 to
> 60 minutes, in your own time within a two-week window.
>
> No AI or machine learning background is needed. Everything is fictional and
> anonymous, and you can withdraw at any point.
>
> Would you take part, or is there a colleague in sustainability reporting who
> might?
>
> [name, affiliation, ORCID or institutional page]

### 3.4 Referral request (send to raters who have completed)

> Thank you for completing the panel. One small ask: I am still short in the
> [role group] group. If someone in your network fits that description and
> might spare an hour, would you introduce us or pass on my details? No
> obligation at all, and thank you again.

## 4. Screening

Ask these before assigning a rater identifier. Two minutes, and it prevents
the expensive failure mode of discovering mid-study that a rater does not fit
the group they were counted in.

1. Which best describes your current role? (governance/risk/compliance/audit;
   ML engineering or data science; sustainability/ESG/environmental
   reporting; none of these)
2. How many years have you worked in that area? (under 2; 2 to 5; 6 to 10;
   more than 10)
3. Have you been involved in a decision about whether a system, model, or
   product could go live? (yes routinely; yes occasionally; no)
4. Organisation type, not name (large enterprise; SME; startup; public sector;
   consultancy; academia; independent)
5. Do you have any prior involvement with FairMind or with this research?
   (This is a disclosure question, not a disqualifier; record it and report
   the count.)
6. Can you complete roughly one hour of assessment within the study window of
   [dates]?

**Exclude** anyone answering "none of these" to Q1, "under 2" to Q2, or "no"
to Q6. Route Q1 answers into the role group they select, not the group you
hoped to fill; a misassigned rater contaminates the by-role breakdown in H3.

## 5. Rater identifiers and the linking list

`INSTRUMENT.md` promises participants that their name is not stored alongside
their responses. Honour it mechanically:

- Assign identifiers R01 to R15 in the order raters are confirmed, filling
  role groups as they come in (R01 to R05 are not required to be GRC; the
  role lives in the assignment plan, not in the number).
- Keep the name-to-identifier linking list in a separate file, outside this
  repository, accessible only to the study team.
- Never commit the linking list, contact details, or completed response files
  containing identifying information to version control.
- Destroy the linking list once data collection closes and the responses have
  been imported, unless a participant has asked to be acknowledged by name in
  the paper, in which case keep only the acknowledgment consent.

`recruitment_tracker.csv` in this folder is the template for tracking outreach
status. It carries no names by design: track people by their identifier and
keep the mapping in the separate linking list.

## 6. Timeline and cadence

Working backwards from a target close date:

| Week | Activity |
| --- | --- |
| 1 to 2 | First-wave outreach to the full target list. Screen and confirm as replies arrive. |
| 3 | Second wave to non-responders (one reminder only), plus referral requests to anyone already confirmed. |
| 3 to 4 | Assign identifiers, send packets and form links. Two-week completion window opens. |
| 5 | Mid-window reminder to anyone who has not submitted. |
| 6 | Close collection. Final reminder 48 hours before close, then import. |

Two reminders per person, maximum, ever. A third is pressure, and pressured
raters produce careless ratings that damage the agreement statistics you are
trying to measure.

## 7. Before you send anything

- [ ] Institutional review decision recorded (see `INSTRUMENT.md` Section 4).
      Do not begin recruiting until this is settled.
- [ ] Consent text finalised with a real contact address.
- [ ] Study window dates fixed.
- [ ] Survey form built to the question spec and tested end to end with a
      throwaway response, which is then deleted before real collection.
- [ ] `build_instrument.py` run, so packets exist to send.
- [ ] Linking-list location chosen, outside the repository.
