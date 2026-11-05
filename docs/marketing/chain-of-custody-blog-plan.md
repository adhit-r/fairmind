# Chain of Custody: blog plan

**Blog:** Chain of Custody, by FairMind
**Address:** blog.fairmind.xyz
**Tagline:** AI safety, governance and security, with the evidence attached.
**Platform:** Ghost 6, self-hosted
**Owner:** Adhithya Rajasekaran
**Plan date:** 4 Nov 2026

The name comes from the product's own differentiation line: FairMind "leads with the test result and its chain of custody" (`docs/product/FAIRMIND_MARKETING_LAUNCH_KIT_2026-07-18.md`). The blog carries that idea: every claim comes with its source, its date and its limits.

Before launch, check the name against trademarks and existing newsletters. This plan hasn't checked it.

---

## 1. Editorial rules

1. **Evidence over opinion.** Every regulatory claim links to the primary text and gives a "last checked" date. Where sources disagree, say so (for example, DPDP Phase 2 is dated 13 or 14 Nov depending on the source).
2. **A test result is not a compliance claim.** We never write "X makes you compliant". This matches the product's honesty rule.
3. **Licences** (from the Frameworks sheet in the packs catalogue):
   - ISO/IEC standards: copyrighted. Use clause IDs and our own paraphrase, never quoted text.
   - OWASP LLM and Agentic Top 10: CC BY-SA 4.0. Attribute, and keep our own wording separate.
   - OWASP MCP Top 10: CC BY-NC-SA, which bars commercial use. Use IDs and our own words only.
   - NIST: public domain. EU law: reusable with attribution.
4. **Human review before publishing.** Claude drafts each post into Ghost as an unpublished draft, and a named reviewer checks the facts and adds hands-on experience. Mass-published thin AI text breaks Google's scaled-content policy, and a penalty would also hurt fairmind.xyz.
5. **CTAs point only to things that exist.** The v2.3 catalogue (90 workflows, 109 evaluations, 51 frameworks) drives the product on main. When a post describes a workflow, say plainly which steps run on their own today and which a person does.
6. **Brand line.** FairMind is agentic AI governance. India frameworks (DPDP, RBI FREE-AI) are search guides, not the headline. "Where FairMind fits" sections lead with workflows and evaluations.
7. **Every post** has your byline, an author page with your ORCID ID, an "updated" date, a section listing primary sources, and 3 or more internal links.

---

## 2. Keyword research

### Method and limits

- **No search-volume data yet.** The Ahrefs connector needs authorisation (run `/mcp` in a Claude Code terminal). Search Console will have real query data about four weeks after launch.
- **What was done here:** competition was read from live search results on 4 Nov 2026 for five clusters. The remaining clusters are rated from experience and should be checked once Ahrefs or Search Console is connected.
- **The main finding:** FairMind's `Regulatory_Watch` and `Frameworks` sheets already record what changed and when. Anything published or changed in the last 90 days has few good pages yet. Turning that tracker into posts is the most reliable way to rank early.

### Clusters

| Cluster | Example target terms | Competition | Evidence and angle |
|---|---|---|---|
| ISO/IEC 27090 (published Oct 2026) | iso 27090, ai security standard | **Low** (checked) | Only a news item (Nemko), a LinkedIn post and the iso27001security page. Be first with a threat-by-threat explainer and a mapping to 27001 and 42001. |
| OWASP LLM Top 10 2026 | owasp llm top 10 2026, what changed | **High** (checked) | Invicti, Akamai, CSA, Giskard and others covered it within weeks. Win with the one thing they lack: a 2025-to-2026 ID re-map table plus test cases. |
| RBI FREE-AI | rbi free-ai framework, free-ai compliance | **Medium-low** (checked) | Results are law-firm commentary and vendor blogs. Nobody has published the 26 recommendations as an implementation checklist with evidence per item. |
| DPDP Rules 2025 | dpdp rules 2025, dpdp compliance timeline | **High** for general terms (checked) | Big 4, law firms and Taxmann dominate. Avoid head-on. |
| DPDP plus AI or ML | dpdp ai training data, dpdp consent machine learning | **Low** (estimated) | No AI-specific practitioner guide surfaced. This is our India angle. |
| Agent governance | ai agent governance, human in the loop ai agents, ai agent audit trail | **Medium** (checked) | Vendor pages, including many near-duplicate generated pages. A deep, original piece can outrank them. It's also FairMind's category. |
| EU AI Act after the Digital Omnibus | eu ai act timeline, article 50, december 2026 | **High** (estimated) | Win on recency: the omnibus dates (Annex III moved to 2 Dec 2027) and the 2 Dec 2026 deadlines. |
| New and niche frameworks | aiuc-1, singapore agentic ai framework, csa ai controls matrix, korea ai basic act, mas ai risk guidelines, en 18286 | **Low** (estimated) | Each changed in 2026. Coverage is thin. |
| Glossary | what is ai assurance, what is ai bom, what is excessive agency | **Medium** (estimated) | Short definition pages. These are what AI answer engines cite. |
| Comparisons | ai governance platforms, llm evaluation tools | **High** (estimated) | Buyers ready to purchase. Be honest about where competitors are stronger. That candour is the differentiator. |

### After launch

- **Week 4:** connect Search Console. Find queries ranking 8 to 20 and refresh those posts first.
- **Month 2:** if Ahrefs is authorised, pull volume for every calendar row and re-rank weeks 9 to 13.
- **Monthly:** add new `Regulatory_Watch` entries to the calendar within 7 days of the change.

---

## 3. 90-day content calendar

Five long-form posts a week from launch. Week 1 is setup.

**Pillar codes:**
- **G** governance (**G-IN** for India)
- **S** security
- **AS** AI safety

**CTA codes** (each points to the FairMind feature the post leads into):
- **EP:** Evidence Passport
- **XW:** framework mappings, the crosswalk
- **AP:** agent approval workflows
- **REG:** AI system registry
- **EVAL:** bring your evaluation results
- **FME:** FairMind-E environmental evidence

Separately from the 60 posts below, publish about 50 short glossary entries across the 90 days (roughly 4 a week).

| # | Week | Title | Target term | Pillar | Format | CTA |
|---|---|---|---|---|---|---|
| | **W1 9–15 Nov** | **Setup (see runbook)** | | | | |
| 1 | W2 16–22 Nov | Chain of custody for AI: why a test result needs provenance | ai audit evidence | G | Manifesto | EP |
| 2 | W2 | DPDP Phase 2 is live: what AI teams must finish before May 2027 | dpdp rules 2025 ai | G-IN | Deadline | REG |
| 3 | W2 | EU AI Act 2 December 2026: Article 50(2) marking and the new prohibitions | eu ai act december 2026 | G | Deadline | XW |
| 4 | W2 | ISO/IEC 27090 explained, threat by threat | iso 27090 | S | Explainer | XW |
| 5 | W2 | OWASP LLM Top 10 2026: what changed and how to re-map from 2025 | owasp llm top 10 2026 | S | Explainer | EVAL |
| 6 | W3 23–29 Nov | The EU AI Act after the Digital Omnibus: the new timeline on one page | eu ai act timeline | G | Explainer | XW |
| 7 | W3 | RBI FREE-AI: the 26 recommendations as an implementation checklist | rbi free-ai framework | G-IN | Checklist | XW |
| 8 | W3 | Prompt injection in agents: a threat model with test cases | prompt injection agents | S | Guide | EVAL |
| 9 | W3 | What is an AI bill of materials, and what should it record? | ai bom | S | Pillar | EP |
| 10 | W3 | Governing AI agents: autonomy levels A0 to A4 and when to require approval | ai agent governance | G | Pillar | AP |
| 11 | W4 30 Nov–6 Dec | EU AI Act Article 50: disclosure and content marking for generative AI | eu ai act article 50 | G | Explainer | XW |
| 12 | W4 | OWASP Top 10 for Agentic Applications (ASI01 to ASI10) explained | owasp agentic top 10 | S | Pillar | AP |
| 13 | W4 | India's AI Governance Guidelines: the seven sutras as controls | india ai governance guidelines | G-IN | Crosswalk | XW |
| 14 | W4 | MCP security: tool poisoning, rug pulls and over-scoped servers | mcp security | S | Guide | AP |
| 15 | W4 | Fairness metrics that survive an audit, and their limits | fairness metrics | AS | Guide | EVAL |
| 16 | W5 7–13 Dec | ISO 42001 vs NIST AI RMF vs EU AI Act: one control map | iso 42001 vs nist ai rmf | G | Crosswalk | XW |
| 17 | W5 | EN 18286 and harmonised standards: what presumption of conformity means | en 18286 | G | Explainer | XW |
| 18 | W5 | Red-teaming an LLM application: a repeatable playbook | llm red teaming | AS | Playbook | EVAL |
| 19 | W5 | MAS AI Risk Management Guidelines: what Singapore FIs must do by Oct 2027 | mas ai risk management guidelines | G | Deadline | XW |
| 20 | W5 | Human oversight without rubber-stamping: designing approval gates | human in the loop ai agents | AS | Guide | AP |
| 21 | W6 14–20 Dec | Building an AI inventory your auditor will accept | ai inventory | G | Template | REG |
| 22 | W6 | Data poisoning: how it happens and what evidence shows you checked | data poisoning | S | Guide | EVAL |
| 23 | W6 | The DPDP Act for ML teams: consent, purpose limits and training data | dpdp act ai training data | G-IN | Guide | REG |
| 24 | W6 | Singapore's agentic AI governance framework (v1.5) explained | agentic ai governance framework | G | Explainer | XW |
| 25 | W6 | AI impact assessment with ISO/IEC 42005: a worked template | ai impact assessment template | G | Template | EP |
| 26 | W7 21–27 Dec | Hallucination is a measurement problem: evaluating groundedness | llm hallucination evaluation | AS | Guide | EVAL |
| 27 | W7 | Model supply chain security: pickle files, poisoned weights, safetensors | model supply chain security | S | Guide | EP |
| 28 | W7 | Colorado SB 26-189: what changed from SB 24-205 and what's due 1 Jan 2027 | colorado ai act | G | Deadline | XW |
| 29 | W7 | What is AI assurance? Testing, evidence and conformity are different things | ai assurance | G | Pillar | EP |
| 30 | W7 | An AI acceptable-use policy: template with clause notes | ai policy template | G | Template | REG |
| 31 | W8 28 Dec–3 Jan | The 2027 AI compliance calendar: every deadline that matters | ai compliance deadlines 2027 | G | Data | XW |
| 32 | W8 | AI incidents of 2026: what failed and which control would have caught it | ai incidents 2026 | AS | Roundup | EP |
| 33 | W8 | NIST AI 600-1: the 12 generative AI risks as a checklist | nist ai 600-1 | G | Checklist | XW |
| 34 | W8 | Excessive agency: limiting what an LLM can do with tools | excessive agency llm | S | Guide | AP |
| 35 | W8 | Korea AI Basic Act: what foreign providers need to know | korea ai basic act | G | Explainer | XW |
| 36 | W9 4–10 Jan | AIUC-1 explained before the 15 January release | aiuc-1 | G | Explainer | XW |
| 37 | W9 | MITRE ATLAS for defenders: tactics mapped to controls | mitre atlas | S | Crosswalk | XW |
| 38 | W9 | Pre-flight and verify: safe external writes for AI agents | ai agent safety | AS | Guide | AP |
| 39 | W9 | Model cards that auditors actually read | model card template | AS | Template | EP |
| 40 | W9 | Explainability evidence for credit decisions under RBI and DPDP | explainable ai credit india | G-IN | Guide | EVAL |
| 41 | W10 11–17 Jan | CSA AI Controls Matrix v1.1: 18 domains in plain English | csa ai controls matrix | S | Explainer | XW |
| 42 | W10 | Least privilege for AI agents: identity and permissions | ai agent permissions | S | Guide | AP |
| 43 | W10 | LLM evaluation tools compared: what each one actually tests | llm evaluation tools | AS | Comparison | EVAL |
| 44 | W10 | NYC Local Law 144: what three years of bias audits show | nyc local law 144 bias audit | G | Analysis | EVAL |
| 45 | W10 | Measuring the energy and carbon cost of AI: what's possible today | ai carbon footprint measurement | AS | Research | FME |
| 46 | W11 18–24 Jan | Reporting AI risk to the board: ISO 38507 and a one-page template | ai board reporting | G | Template | REG |
| 47 | W11 | Jailbreaks vs prompt injection: different threats, different controls | jailbreak vs prompt injection | S | Explainer | EVAL |
| 48 | W11 | Reviewing third-party AI vendors: what to ask for and what evidence to expect | ai vendor risk assessment | G | Template | EP |
| 49 | W11 | The UK AI Cyber Security Code and ETSI EN 304 223 explained | ai cyber security code of practice | S | Explainer | XW |
| 50 | W11 | AI governance platforms in 2027: an honest comparison | ai governance platforms | G | Comparison | EP |
| 51 | W12 25–31 Jan | An AI incident response runbook for agentic systems | ai incident response | AS | Template | AP |
| 52 | W12 | Agent memory and context poisoning | ai agent memory poisoning | S | Guide | AP |
| 53 | W12 | DPDP Significant Data Fiduciaries: DPIAs and audits for AI systems | dpdp significant data fiduciary | G-IN | Guide | EP |
| 54 | W12 | Reusing evidence across frameworks without overclaiming | ai compliance crosswalk | G | Guide | XW |
| 55 | W12 | Monitoring AI drift: what to log and when to re-test | ai model monitoring | AS | Guide | EVAL |
| 56 | W13 1–7 Feb | State of AI governance in India 2027 (original survey) | ai governance india | G-IN | Research | EP |
| 57 | W13 | The OWASP MCP Top 10 (beta) explained | owasp mcp top 10 | S | Explainer | AP |
| 58 | W13 | Security risks of agent skills: the OWASP Top 10 for Agentic Skills | agent skills security | S | Explainer | AP |
| 59 | W13 | Australia's Guidance for AI Adoption: six practices mapped | australia ai guidance | G | Crosswalk | XW |
| 60 | W13 | Secure AI development with NIST SP 800-218A | nist 800-218a | S | Explainer | XW |

**Notes:**
- **Mix:** 31 governance (7 of them India), 18 security, 11 safety. Safety is the thinnest. If Search Console shows demand for safety topics, swap in more evaluation and red-teaming posts.
- **Date-sensitive posts** (2, 3, 19, 28, 31, 36) must go out before their deadlines. Check each date against the primary text the day before publishing.
- **Post 56** (India survey) needs fieldwork from W5 to W11: a 15-question form and distribution through LinkedIn and partner communities. If there aren't enough responses, publish it as an analysis of public filings instead. Never pad the results.
- **Refreshes:** posts 5, 12 and 57 follow OWASP releases, and post 36 follows AIUC-1's quarterly releases. Re-check them on each new release.

---

## 4. Setup runbook (Week 1)

### 4.1 Host (decided 4 Nov 2026): Lightsail Micro in the FairMind AWS account

- **Account:** the new FairMind AWS account, not Olai's. See `docs/deployment/aws-account-and-database-study.md`.
- **Region:** us-east-1, so the blog sits next to the app box.
- **Plan:** `micro_3_0`, $7 a month: 1 GB RAM, 2 vCPU, 40 GB disk, 1 TB transfer, public IPv4 included. Nano ($5) can't run the Ghost image: its power rating is 298 and the image requires at least 299.
- **Image:** the `ghost_bitnami` blueprint (Ghost 6.37.1 on 4 Nov 2026). MySQL and the web server are included.

```bash
aws lightsail create-instances --region us-east-1 --instance-names fairmind-blog \
  --availability-zone us-east-1a --blueprint-id ghost_bitnami --bundle-id micro_3_0 --tags key=project,value=fairmind key=service,value=blog
aws lightsail enable-add-on --region us-east-1 --resource-name fairmind-blog \
  --add-on-request addOnType=AutoSnapshot,autoSnapshotAddOnRequest={snapshotTimeOfDay=22:00}
aws lightsail put-instance-public-ports --region us-east-1 --instance-name fairmind-blog --port-infos \
  "fromPort=22,toPort=22,protocol=tcp,cidrs=[$(curl -s https://checkip.amazonaws.com)/32]"
```

On the instance, add 2 GB of swap. With only 1 GB of RAM, Ghost upgrades and traffic spikes would otherwise run out of memory:

```bash
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 4.2 DNS and TLS

- **Traffic:** use the same pattern as `deploy/lightsail`. Run `cloudflared` on the blog instance (or add a route in the existing tunnel) for `blog.fairmind.xyz` → `http://localhost:80`, with no inbound web ports. TLS ends at Cloudflare, so Bitnami's certificate tool isn't needed.
- **Ghost settings:** set the site URL with `sudo /opt/bitnami/ctlscript.sh stop` → edit `url` in `/opt/bitnami/ghost/config.production.json` to `https://blog.fairmind.xyz` → start. Check the exact paths against the Bitnami Ghost docs for the image version.

### 4.3 Ghost

- **Owner account:** open `https://blog.fairmind.xyz/ghost` and create the owner account yourself. Don't hand credentials to an agent.
- **Sign-in security:** turn on staff device verification.
- **Updates:** use Bitnami's update path or rebuild from a new blueprint image. A snapshot runs before every update.
- **Backups:** the automatic daily snapshot above, plus a weekly Ghost content export (Settings → Labs → Export).

### 4.4 Email

- **Newsletters:** Ghost sends bulk newsletters only through Mailgun. Add the Mailgun domain, for example `mg.fairmind.xyz`, with its SPF, DKIM and MX records, then enter the API key under Settings → Email newsletter.
- **Transactional email** (sign-in links): send it through Resend's SMTP by setting `mail.transport` to `SMTP` and `mail.options.host` to `smtp.resend.com` in `config.production.json`. Keep the key on the server only, never in git.

### 4.5 Backups (in addition to the snapshots)

- **Nightly cron job:** `mysqldump` of the Ghost database plus a tarball of `/opt/bitnami/ghost/content`, uploaded to S3 in the FairMind account. Keep 30 days. Snapshots protect the whole box; this protects against a bad Ghost upgrade.
- **Restore test:** run one in Week 1. A backup that has never been restored doesn't count.

### 4.6 Theme and brand

- **Theme:** fork Ghost's default Source theme into `apps/blog-theme/` in this repo, and deploy with `gscan` plus a zip upload, or the Ghost Admin API from CI.
- **Look:** follow the redesigned website, not the app's neobrutalist styling.
- **Masthead:** "Chain of Custody", with "by FairMind" linking back to fairmind.xyz.
- **Code:** inject `/llms.txt` and analytics through Code Injection. Article JSON-LD, Open Graph tags, the sitemap and canonical URLs are built in.

### 4.7 Website changes in this repo

- **Old blog page:** `apps/website/src/pages/blog/index.astro` (the research-notes page) moves to `/research`.
- **Redirects:** in `apps/website/netlify.toml`, replace the `/blog` → `/blog/` redirect with a 301 from `/blog/*` to `https://blog.fairmind.xyz/:splat`.
- **Links:** add "Blog" to the site navigation and footer.

### 4.8 Search and indexing

- **Google Search Console:** add a property for `https://blog.fairmind.xyz` and submit `/sitemap.xml`.
- **Bing Webmaster Tools:** import from Search Console. Bing's index feeds ChatGPT search and Copilot.
- **IndexNow:** ping it on publish with a Ghost webhook and a small worker. Skip this until the first 20 posts are live.

### 4.9 Drafting pipeline

- **Access:** create a Ghost Custom Integration to get an Admin API key, and store it in a local `.env`.
- **Drafting:** Claude creates each post through the Admin API with `status: draft`, the target term in the meta title and description, tags for pillar and format, and the CTA block.
- **Publishing:** the reviewer publishes from the Ghost editor. Nothing publishes automatically.

---

## 5. Promotion playbook

### Every post (about 30 minutes after publishing)

1. LinkedIn from your personal account: a 150–250 word take, with the link in the first comment. Then the company page reshares it.
2. One LinkedIn carousel (5–8 slides) for each pillar guide, crosswalk and template.
3. Cross-post to dev.to and Hashnode with the canonical URL pointing back to the blog. Security and evaluation posts only. Wait 3 days so Google indexes the original first.
4. Add 2 links from older posts to the new one.
5. Put UTM tags on every CTA link to fairmind.xyz, so PostHog can tie demo requests back to individual posts.

### Newsletter: "The Custody Log" (weekly, Thursday)

- **Format, in this order:** one deadline, one incident, one control, one new Chain of Custody post, and one line on what's still unknown. Around 400 words.
- **Sign-up points:**
  - Lead magnets: the AI inventory template (post 21), the AI policy template (post 30) and the 2027 compliance calendar (post 31).
  - Inline forms on every post.
- **Target:** 500 subscribers by day 90.

### Communities: share only posts that fit each one, no link-dumping

- **Security:** r/netsec for posts 4, 14 and 57; r/LLMDevs; OWASP GenAI Slack.
- **Hacker News:** posts 4, 14, 27 and 45 only. HN rewards original technical work, not explainers.
- **India:** MediaNama and Inc42 guest pieces built from posts 2, 7 and 56; iSPIRT and NASSCOM AI communities.
- **Research:** mirror post 45 and the India survey on Zenodo with a DOI, and link them from your ORCID record.

### Link building (target 15 good backlinks in 90 days)

- **Curated lists:** submit to GitHub awesome lists for LLM security and AI governance. Crosswalks and the threat library are what list maintainers accept.
- **OWASP GenAI:** check the project's community resources page and contributor channels. Posts 5 and 12 add their own mappings on top of OWASP's lists, which the project tends to welcome.
- **Guest posts:** pitch the CSA blog, IAPP (written as practitioner pieces), and Indian fintech newsletters.
- **Podcasts:** reuse the podcast notes in the marketing launch kit; aim for 2 guest appearances.
- **Original data earns links:** the 2027 deadline calendar (post 31) and the India survey (post 56). Update the calendar monthly so it stays the page people cite.

### Measurement

| Metric | Day 30 | Day 90 |
|---|---|---|
| Posts published | 15 | 60 long-form, 50 glossary |
| Indexed pages (Search Console) | 20 | 100+ |
| Organic clicks per week | 50 | 1,000 |
| Newsletter subscribers | 100 | 500 |
| Demo or access requests from the blog (UTM) | 2 | 20 |

These targets are estimates without volume data. Reset them in week 4 from Search Console.

---

## Sources checked 4 Nov 2026

**Internal:**
- `docs/product/FairMind_agentic_packs_catalogue_v2.3.xlsx` (Frameworks and Regulatory_Watch sheets)
- `docs/product/FAIRMIND_MARKETING_LAUNCH_KIT_2026-07-18.md`

**DPDP timeline:**
- [india-briefing.com](https://www.india-briefing.com/news/india-dpdp-compliance-timeline-enforcement-2026-27-44740.html/)
- [taxmann.com](https://www.taxmann.com/post/blog/analysis-indias-dpdp-act-and-rules/)
- [uniqus.com](https://uniqus.com/digital-personal-data-protection-act-timelines/)

**OWASP LLM Top 10 2026:**
- [Invicti](https://www.invicti.com/blog/web-security/owasp-llm-top-10-2026-whats-new)
- [CSA](https://cloudsecurityalliance.org/articles/the-owasp-top-10-for-llm-applications-2026-what-changed-and-why-it-matters)
- [Giskard](https://www.giskard.ai/knowledge/owasp-top-10-for-llm-2026)

**ISO/IEC 27090:**
- [Nemko](https://digital.nemko.com/news/isoiec-27090-published-as-new-ai-cybersecurity-standard)
- [iso27001security](https://www.iso27001security.com/html/27090)
- [ISO](https://www.iso.org/standard/27090)

**RBI FREE-AI:**
- [Securiti](https://securiti.ai/free-ai-framework-in-indian-finance/)
- [Bar & Bench](https://www.barandbench.com/view-point/rbis-free-ai-framework-navigating-the-legal-and-regulatory-landscape)

**Agent governance search results:**
- [Airtable](https://www.airtable.com/articles/ai-agent-governance-audit-trails)
- [hoop.dev](https://hoop.dev/blog/why-action-level-approvals-matter-for-ai-governance-ai-audit-trail)

**Ghost 6 self-hosting:**
- [Ghost forum overview](https://forum.ghost.org/t/guide-community-overview-of-ghost-v6-0-for-self-hosted-installations/59236)
- [Ghost forum: recommended method](https://forum.ghost.org/t/what-is-the-official-recommended-method-to-self-host-v6/61911)
