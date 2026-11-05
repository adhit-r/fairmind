---
name: Chain of Custody
description: AI regulation guides from FairMind, set as a packed reference portal on white with one utility red.
colors:
  utility-red: "#e60012"
  red-deep: "#b8000e"
  red-tint: "#fdecee"
  ink: "#111111"
  ink-soft: "#3a3a3a"
  prose-ink: "#222222"
  gray: "#6b6b6b"
  rule-mid: "#d6d6d6"
  hairline: "#e0e0e0"
  panel: "#f2f2f2"
  row-wash: "#fafafa"
  white: "#ffffff"
  confirm-green: "#1d6b3a"
typography:
  display:
    fontFamily: "Barlow Condensed, Noto Sans, sans-serif"
    fontSize: "clamp(2.1rem, 3.4vw, 3.1rem)"
    fontWeight: 800
    lineHeight: 1.02
    letterSpacing: "-0.005em"
  numeral:
    fontFamily: "Barlow Condensed, Noto Sans, sans-serif"
    fontSize: "2rem"
    fontWeight: 700
    lineHeight: 1
  wordmark:
    fontFamily: "Barlow Condensed, Noto Sans, sans-serif"
    fontSize: "1.65rem"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "0.01em"
  headline:
    fontFamily: "Noto Sans, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Noto Sans, system-ui, sans-serif"
    fontSize: "1.06rem"
    fontWeight: 700
    lineHeight: 1.35
  module-head:
    fontFamily: "Noto Sans, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 700
  prose:
    fontFamily: "Noto Sans, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.75
  body:
    fontFamily: "Noto Sans, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.6
    fontFeature: "\"tnum\""
  meta:
    fontFamily: "Noto Sans, system-ui, sans-serif"
    fontSize: "0.76rem"
    fontWeight: 400
  label:
    fontFamily: "Noto Sans, system-ui, sans-serif"
    fontSize: "0.72rem"
    fontWeight: 700
    letterSpacing: "0.04em"
rounded:
  none: "0px"
  badge: "999px"
spacing:
  xs: "0.35rem"
  sm: "0.75rem"
  md: "1rem"
  gap: "1.25rem"
  lg: "1.75rem"
  rail: "15.5rem"
  aside: "19rem"
  column: "46rem"
  measure: "40rem"
  max: "90rem"
  target: "2.75rem"
components:
  button-primary:
    backgroundColor: "{colors.utility-red}"
    textColor: "{colors.white}"
    rounded: "{rounded.none}"
    padding: "0 1.1rem"
    height: "2.75rem"
    typography: "{typography.module-head}"
  button-primary-hover:
    backgroundColor: "{colors.red-deep}"
  button-line:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "0 1.1rem"
    height: "2.75rem"
  module:
    backgroundColor: "{colors.white}"
    rounded: "{rounded.none}"
  module-header:
    padding: "0.8rem 1rem"
    typography: "{typography.module-head}"
  rail-header:
    backgroundColor: "{colors.utility-red}"
    textColor: "{colors.white}"
    padding: "0.75rem 1rem"
  rail-item:
    textColor: "{colors.ink}"
    padding: "0.55rem 0.75rem 0.55rem 1rem"
    height: "2.75rem"
  rail-item-current:
    backgroundColor: "{colors.red-tint}"
    textColor: "{colors.red-deep}"
  tab:
    textColor: "{colors.ink-soft}"
    padding: "0 1rem"
    height: "2.875rem"
  tab-current:
    textColor: "{colors.utility-red}"
  label-new:
    backgroundColor: "{colors.utility-red}"
    textColor: "{colors.white}"
    typography: "{typography.label}"
    height: "1.3rem"
    padding: "0 0.45rem"
  label-deadline:
    textColor: "{colors.utility-red}"
    typography: "{typography.label}"
    height: "1.3rem"
    padding: "0 0.45rem"
  chip-topic:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink-soft}"
    padding: "0.1rem 0.5rem"
  due-count:
    textColor: "{colors.ink}"
    typography: "{typography.numeral}"
    width: "3.4rem"
  due-count-urgent:
    textColor: "{colors.utility-red}"
  promo:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.white}"
    padding: "1.1rem"
  input:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "0 0.8rem"
    height: "2.75rem"
---

# Design System: Chain of Custody

## Overview

**Creative North Star: "The Reference Counter"**

Chain of Custody is a packed reference portal, not a magazine. Every framework, the newest guides and the next deadlines sit in one viewport, each inside its own hairline-ruled module with a small bold header and an optional "View all" link. The page reads like a well-run information desk: white ground, near-black ink, a family of four grays doing all the structural work, and a single utility red that marks what is current, what is new, what is due soon and what to press.

Density is the point. Body copy is compact (14px gothic sans) and modules butt against each other on a 1.25rem gap so the reader scans instead of scrolls. The one place the system slows down is the guide itself: a calm 40rem column of 17px prose with generous leading, flanked by an on-this-page rail and a side column of facts, related guides, deadlines and the FairMind promo.

The world is flat and square. Depth comes only from hairlines, the one ink-filled promo block and the red rail header. Condensed bold display type is reserved for headlines, the wordmark and the deadline day counts, which are the system's loudest numerals.

**Key Characteristics:**
- White ground, #111 ink, four structural grays, one utility red.
- Every content group is a 1px hairline module with a header bar; no floating cards, no shadows.
- Condensed bold display for headlines and day-count numerals; compact Noto Sans for everything else.
- Square corners throughout; the deadline badge is the only rounded form.
- No italics anywhere, including inside prose.

## Colors

A white-and-ink utility palette in which red is a signal, never a fill for decoration.

### Primary
- **Utility Red** (utility-red): the active tab and its 3px underline, the rail header block, New and Deadline labels, day counts 30 or fewer days out, the next-deadline date in the rail, primary buttons (Subscribe, Request access, Search), and the shared hover, focus ring, selection and reading-progress state.
- **Deep Red** (red-deep): hover on primary buttons; text of the current rail item and current table-of-contents entry; prose links at rest.
- **Red Tint** (red-tint): background wash behind the current or hovered rail item and the current table-of-contents entry. Never a panel fill.

### Neutral
- **Ink** (ink): headlines, body, the promo block fill, the footer's 3px top rule, code blocks.
- **Soft Ink** (ink-soft): secondary text, tab labels at rest, ledes and deks, chip text.
- **Prose Ink** (prose-ink): long-form guide body only; a hair softer than ink for sustained reading.
- **Gray** (gray): metadata, dates, counts, captions, placeholders. Darkened from the contract's #7A7A7A to keep small meta text legible on white.
- **Mid Rule** (rule-mid): outlined button and input borders, search field borders, table head rule.
- **Hairline** (hairline): every module border, header divider and list-row separator.
- **Panel** (panel): topic chips, table heads, inline code, footer ground.
- **Row Wash** (row-wash): list-row hover, zebra table rows, the sources box.
- **Confirm Green** (confirm-green): the newsletter success message only.

### Named Rules
**The One Signal Rule.** Red marks state and urgency: current location, New, Deadline, 30 days or fewer, the primary action, and hover/focus. If an element is red and none of those apply, it is wrong.

**The Gray Structure Rule.** Hierarchy between regions is carried by hairlines and gray text, never by tinted panels or colored section backgrounds.

## Typography

**Display Font:** Barlow Condensed 600/700/800 (Ghost heading font override, falling back to Noto Sans)
**Body Font:** Noto Sans 400/500/600/700 (Ghost body font override, falling back to system-ui)

**Character:** A tall condensed gothic for the few things that must shout, over a plain, sturdy sans that disappears into data. Tabular numerals are on site-wide so dates, counts and day numbers align.

### Hierarchy
- **Display** (800, clamp 2.1rem to 3.1rem, 1.02): the guide title. The home lead uses the same face at clamp 2rem to 2.9rem / 1.0; topic heroes go up to 3.6rem at 700.
- **Numeral** (700, 2rem, 1.0): deadline day counts, right-aligned in their column; topic fact values at 1.5rem.
- **Wordmark** (700, 1.65rem, uppercase, 0.01em): site name in header and footer; the promo heading uses the same uppercase condensed treatment at 1.35rem.
- **Headline** (700 sans, 1.5rem, 1.25): prose H2, preceded by a hairline rule and 1rem of air. Prose H3 is 1.15rem.
- **Title** (700 sans, 1.06rem, 1.35): guide titles in list rows; 0.95rem in New guides, 0.875rem in the due list.
- **Module head** (700 sans, 1rem): module header titles.
- **Prose** (400, 1.0625rem, 1.75, 40rem measure): guide body.
- **Body** (400, 14px, 1.6): all UI copy.
- **Meta** (400, 0.75 to 0.78rem, gray): dates, reading time, counts, breadcrumbs.
- **Label** (700, 0.72rem, 0.04em, uppercase): New and Deadline labels only.

### Named Rules
**The Upright Rule.** No italics anywhere. Prose em, i and cite render upright; emphasis is carried by weight (strong at 700 in ink).

**The No Kicker Rule.** Nothing sits above a heading to introduce it: no eyebrow, no category line, no small caps label. Labels and chips go in the meta line below the headline or inline before a list title.

**The Condensed Is Loud Rule.** Barlow Condensed is for titles, the wordmark and numerals. Never set running text, buttons, labels or module headers in it.

## Layout

A 90rem max container with a fluid gutter (clamp 1rem to 1.75rem). The home and topic views use a two-track grid: a 15.5rem sticky rail plus a content grid of three tracks (1.9fr / 1fr / 1fr) holding the lead, New guides and Coming due, with the list spanning two tracks and the side stack (newsletter, deadlines) in the third. The guide view uses three tracks: 15.5rem on-this-page rail, a fluid 46rem-max document column, and a 19rem side column that turns sticky on screens at least 880px tall.

Every gap between modules is 1.25rem. Module internals use 1rem horizontal padding; list rows use 0.75 to 1.1rem vertical padding with hairline separators. The header is 4.5rem tall; the tab row is 2.875rem and sticky at the top; rails stick at tab height plus 1.25rem.

Responsive: at 1200px the content grid becomes two columns and side stacks sit two-up below; the guide drops to a 13rem rail plus document. At 900px everything is a single column, the rail moves below content, the table of contents becomes a collapsible "On this page" disclosure, the header search collapses to an icon button and the FairMind outlined button hides. At 520px the wordmark shrinks to 1.2rem and the subtitle and Deadlines action hide.

**The One Glance Rule.** On desktop the first viewport shows the framework rail, the lead guide with search, New guides and Coming due together. Do not push any of them below the fold with a hero.

## Elevation & Depth

Flat. There are no box shadows anywhere in the system. Depth is conveyed by 1px hairline borders, the ink-filled promo block, the red rail header, and the 3px ink rule that opens the footer. Hover states change border color (mid rule to ink) or apply the row wash; they never lift.

**The Hairline Rule.** Separation is a 1px hairline. Heavier strokes are reserved for the 3px tab underline, the 3px reading-progress bar, the 3px footer top rule and the 2px sources heading rule.

## Shapes

Square corners on every surface, button, input, label and chip (0px). The single exception is the deadline count badge in the header, a red pill (999px) so it reads as a counter rather than a label. Icons are 1.6px-stroke line drawings on a 24px grid, round caps and joins, rendered at 12 to 20px in currentColor.

## Components

### Buttons
Plain, rectangular, 2.75rem tall.
- **Shape:** square (0px), 2.75rem minimum height, 600 weight at 0.875rem.
- **Primary:** utility red fill, white text; hover to deep red. Used for Subscribe, Request access and the inline Search.
- **Line (secondary):** white with a mid-rule 1px border; hover darkens the border to ink. A full-width 2.5rem variant closes the due module ("All deadlines").
- **Focus:** 2px utility red outline, 2px offset (site-wide).

### Modules
The system's container. Every content group lives in one.
- **Border:** 1px hairline, white ground, square.
- **Header bar:** module-head title left, a meta-sized "View all"/"Calendar" link with a 12px chevron or a gray count right; 0.8rem by 1rem padding; hairline below.
- **Body:** 1rem padding, or flush lists with hairline row separators.
- **Promo:** the one inverted module, ink fill, uppercase condensed heading, light gray copy, full-width primary button.

### Rail
- **Header:** solid utility red block, white 700 0.9rem text with a list icon.
- **Items:** 2.75rem rows, 18px framework line icon, name, optional red next-deadline date, gray post count (or "Soon"). Hover and current: red tint wash with deep red text.
- **Reused** as the on-this-page table of contents on guides (0.8rem items; current entry in deep red on tint, 700).

### Tabs
- **Style:** 0.875rem 500 soft ink, 1rem side padding, horizontally scrollable without a scrollbar.
- **Hover:** text to ink, the red underline grows to 40% from the left.
- **Current:** utility red 700 text with a full 3px red underline sitting on the hairline.

### Labels and Chips
- **New:** solid red, white uppercase label type, 1.3rem tall; shown for guides 14 days old or less.
- **Deadline:** 1px red outline, red uppercase label type.
- **Topic chip:** panel gray ground, soft ink 600 at 0.72rem, sentence case; hover text to red.

### Due list
- **Row:** a 3.4rem right-aligned condensed day count with "days" in small gray sans beneath, then a bold title, a 600 date and gray context lines. Wide variant on the deadlines page uses a 4.5rem count column.
- **Urgent:** counts of 30 days or fewer turn utility red; the header badge counts the same set.

### Lists
- **Guide row:** date column (6.5rem), title + excerpt (62ch) + meta line, right column for reading time and source count; hover applies the row wash. Collapses to one column at 900px.

### Inputs
- **Style:** 2.75rem, 1px mid rule, white, square, 0.9rem body text, gray placeholder.
- **Focus:** border turns utility red.
- **Search triggers:** the header and lead search are buttons styled as fields (mid rule border, hover to ink); the lead version carries an inset red Search block.

### Prose
- 40rem measure, 1.0625rem / 1.75, prose ink.
- H2 with a hairline above; links in deep red with a 1px underline offset 0.2em, hover to red; strong in ink at 700.
- Blockquote: 1px ink left rule, soft ink text, upright.
- Tables: full width, hairline frame, panel head with a mid-rule underline, zebra row wash.
- Code: inline on panel gray; blocks on ink with light text.
- Sources list: hairline box on row wash, under a heading with a 2px ink rule.

## Do's and Don'ts

### Do:
- **Do** put every new content group in a hairline module with a header bar, 1.25rem from its neighbours.
- **Do** keep utility red to tabs, labels, urgent day counts (30 days or fewer), primary actions, the rail header and hover/focus/current states.
- **Do** carry emphasis with weight and ink; set em, i and cite upright.
- **Do** place labels and topic chips in the meta line below a headline or inline before a list title.
- **Do** use 1.6px line icons in currentColor, 12 to 20px.
- **Do** keep interactive targets at least 2.75rem tall.

### Don't:
- **Don't** use italics anywhere.
- **Don't** put a kicker, eyebrow or label above a heading.
- **Don't** use shadows, gradients or rounded corners (the header badge is the only pill).
- **Don't** use red for decoration, panel fills or body text.
- **Don't** set running text, buttons or labels in Barlow Condensed.
- **Don't** lead a page with a full-width hero or a card grid; the first viewport is modules.
