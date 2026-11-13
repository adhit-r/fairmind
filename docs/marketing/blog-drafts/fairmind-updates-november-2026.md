---
title: "What shipped in FairMind in November 2026"
slug: fairmind-updates-november-2026
status: draft
meta_title: "FairMind product updates, November 2026"
meta_description: "A rebuilt app, a live board of release gates, a release autopilot, a governance plan built by discovery, and all 109 evaluations now running."
custom_excerpt: "A rebuilt app on real data, a live board of release gates, an autopilot for the measurable steps, and every one of the 109 evaluations now runs."
tags: [product-updates]
author: Adhithya Rajasekaran
last_checked: 2026-11-13
---

Most posts here explain a rule. This one is shorter and is about our own work: what changed in FairMind over the past two weeks, and why each change matters to someone who has to show an auditor their evidence.

## A rebuilt app, on real data only

Every page in the app has been rebuilt and grouped into seven sections: Home, Inventory, Rules, Testing, Release, Records and Agents. That covers 19 pages, from Needs you and the system file through Evaluations, Decisions, Evidence and Auditor packs.

The rule we held to is that every page reads the real API. Where there is no data source yet, the page says so rather than showing a sample number. A governance tool that fills empty screens with placeholder figures is teaching its users to trust numbers nobody measured, which is the habit this blog argues against.

The app also gained a main landmark, a skip link, readable text descriptions for every chart and proper table header scope, so it works with a screen reader.

## Home is now a live board of release gates

Home shows every registered AI system against the five release checks, with its current release decision, and re-reads the state every minute. One look tells you which systems can ship, which are blocked, and on which check.

## Release autopilot

Each system can now run on autopilot for the steps that can be measured. The agent follows the route the release gate already lays out: it re-runs the fairness test against a kept data source and takes monitoring snapshots when they are due. It always reuses the columns and protected attributes a person confirmed on an earlier run.

Some steps stay with people on purpose. Attestations, uploads, the environmental assessment and the release request itself are never done by the agent. You choose the mode per system: off, ask first, or run on an hourly sweep. Every agent run produces measured evidence and an entry in the agent trace, so you can see what it did and when.

## A governance plan built by discovery

The Plan page starts by reading your AI inventory and then asks only what it cannot work out on its own: a short description of the organisation, its maturity, who holds which role, and which frameworks apply. From that it maps the controls in scope, the systems and the owners.

Each in-scope control becomes a task with its requirements, a suggested owner, dependencies, the workflows to run and a state derived from the evidence you already hold. The plan is recomputed on every load and keeps a change log, so it moves when your evidence does.

## Ask FairMind, on your own model

Ask FairMind (Ctrl K) answers a question about your estate from its release gates and waiting runs. It uses the AI provider your organisation has connected, not ours, and it only cites your own systems. With no provider connected it tells you so instead of guessing.

## All 109 evaluations now run

Every evaluation in the catalogue now runs. 88 run inside FairMind. The other 21 judge results you bring from your own sandbox, drills, attack runs or detectors, because those tests belong in your environment rather than ours.

The indirect prompt-injection evaluation (EV-SEC-02) gained a probe source setting. Choosing CyberSecEval sends 51 indirect cases from Meta's PurpleLlama benchmark, pinned to one commit, instead of uploaded or generated probes. Because every run uses the same cases, results compare across systems and over time, and the run records the dataset and version it used.

## Tighter access

Signup is now by approval only. New organisations come from approved access requests, and approval sends a single-use link that sets the password and proves the email address at the same time. When someone is removed from an organisation or signs out, their access ends on their next request rather than when their token runs out. The public forms (sign-in, signup, access request and password reset) can now carry a bot check, and every page is served with security headers.

## What is next

The FairMind note at the end of each guide will start pointing at these pages directly. If you want to try the app on your own systems, [request access](https://fairmind.xyz/request-access).

<!-- REVIEWER NOTES (not for publication)
- Sources: git log on main, 10-13 Nov 2026: 4268a163 (19 rebuilt pages), c90fadc6 (live board, five checks, 60s refresh), b735faa0 (autopilot), 4a933197 (plan), a07885d4 (Ask FairMind), 13ffab7e (109 run, 21 judge external results; 88 = 109 - 21), 0f3354a1 (CyberSecEval, 51 cases), a5ad0040 / 1b895870 / cd1aee23 (access), c5ca5b72 (Turnstile), ec295624 (security headers), 84804cad (accessibility).
- Confirm these are deployed to production before publishing; this post states them as live.
- Turnstile is off until the keys are set. The post says forms "can now carry" a bot check; change to "now carry" once the keys are live in production.
- Tag product-updates is not in the theme's topic_tags, so the post shows in Latest only, not in the Frameworks rail. Intended.
- Seven section names taken from the approved Astryx menu (memory note 2026-11-11); confirm they match the shipped nav labels.
-->
