# Chain of Custody design system

A dense reference portal for AI regulation guides, styled calmly. The first screen holds everything a compliance reader needs: frameworks on the left, the latest guide and search in the middle, new guides beside it, and deadlines counted down on the right.

## Layout

| Page | Structure |
|---|---|
| Home | Rail (frameworks, Request access) / grid: Start here lead, New guides, right column (Coming due, newsletter) spanning the lead and Earlier guides |
| Tag | Rail / topic header with facts, Coming due, guide list, newsletter |
| Guide | On this page (sticky) / article at 40rem measure / This guide facts, More on the topic, Coming due, Request access |
| Page | Article with newsletter beside it; the docket page adds the counted-down list |

Breakpoints: 1200px (grid drops to two columns, right column flows below), 900px (one column, rail below content, mobile contents drawer), 520px (compact header).

## Tokens

| Token | Light | Dark |
|---|---|---|
| `--white` (page, modules) | `#fcfcfb` | `#141517` |
| `--surface` (hover, footer, code) | `#f5f5f2` | `#1b1c1f` |
| `--ink` | `#1c1d1f` | `#ececea` |
| `--ink-2` | `#45474b` | `#c4c5c2` |
| `--gray` (meta) | `#65676b` | `#9a9c9f` |
| `--line` | `#e7e7e3` | `#2a2b2f` |
| `--accent` | Ghost accent, `#0b6b52` | `#5fcfa9` |
| `--accent-tint` | `#e8f3ef` | `#173229` |
| `--due` (dates within 30 days, Deadline label) | `#b42318` | `#ff8f80` |

Radius: modules 8px, inputs 6px, labels 4px, buttons are pills.

## Type

- Headlines, module titles, guide titles in lists, day counts: Literata (self-hosted, `assets/fonts/literata-latin.woff2`), weight 600, tight negative tracking.
- Body and UI: the system sans stack at 15px.
- No uppercase, no condensed faces, no italics (`em` renders upright).

## Rules

- Hairline borders only; no hard shadows, thick outlines or filled colour blocks.
- Accent is for actions (Subscribe, Search, Request access), current state and links. Red is only for deadlines.
- Labels (New, Deadline) are soft tints, never solid fills.
- Every number shown comes from Ghost or the docket page; nothing is hardcoded.
