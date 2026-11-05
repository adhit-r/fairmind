---
name: Chain of Custody
description: A calm editorial publication of AI regulation guides, published by FairMind.
colors:
  accent: "#0b6b52"
  accent-strong: "#08513e"
  due: "#b42318"
  on-accent: "#ffffff"
  paper: "#fcfcfb"
  ink: "#1c1d1f"
  ink-2: "#45474b"
  muted: "#65676b"
  rule: "#e5e5e1"
  field: "#8c8e92"
  surface: "#f3f3f0"
  dark-paper: "#141517"
  dark-ink: "#ebebe8"
  dark-ink-2: "#c6c7c9"
  dark-muted: "#9c9ea2"
  dark-rule: "#2c2e31"
  dark-field: "#76787c"
  dark-surface: "#1d1f22"
  dark-accent: "#5fcfa9"
  dark-accent-strong: "#8be0c3"
  dark-due: "#ff8f80"
  dark-on-accent: "#0b1f19"
typography:
  display:
    fontFamily: "Literata, Georgia, serif"
    fontSize: "clamp(2.1rem, 4.4vw, 3.2rem)"
    fontWeight: 600
    lineHeight: 1.12
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Literata, Georgia, serif"
    fontSize: "clamp(2rem, 4.2vw, 3rem)"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.016em"
  title:
    fontFamily: "Literata, Georgia, serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-0.01em"
  title-sm:
    fontFamily: "Literata, Georgia, serif"
    fontSize: "1.3rem"
    fontWeight: 600
    lineHeight: 1.3
  prose-h2:
    fontFamily: "Literata, Georgia, serif"
    fontSize: "1.65rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-0.01em"
  dek:
    fontFamily: "Literata, Georgia, serif"
    fontSize: "1.25rem"
    fontWeight: 400
    lineHeight: 1.6
  body:
    fontFamily: "Literata, Georgia, serif"
    fontSize: "1.1875rem"
    fontWeight: 400
    lineHeight: 1.72
  ui:
    fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  meta:
    fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    fontFeature: "tnum"
  label:
    fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 600
rounded:
  pill: "999px"
  code: "4px"
  pre: "8px"
  avatar: "50%"
spacing:
  read: "40rem"
  wide: "68rem"
  gutter: "clamp(1.25rem, 5vw, 2.5rem)"
  prose-flow: "1.3rem"
  entry: "1.75rem"
  topic: "1.5rem"
  section: "clamp(3rem, 7vw, 4.5rem)"
  lead-top: "clamp(3rem, 8vw, 5.5rem)"
  target: "2.75rem"
components:
  button-pill:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    typography: "{typography.ui}"
    rounded: "{rounded.pill}"
    padding: "0 1.15rem"
    height: "2.75rem"
  button-pill-hover:
    backgroundColor: "{colors.accent-strong}"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "0 1rem"
    height: "2.75rem"
  icon-button:
    textColor: "{colors.ink-2}"
    rounded: "{rounded.pill}"
    size: "2.75rem"
  icon-button-hover:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
  menu-link:
    textColor: "{colors.ink-2}"
    rounded: "{rounded.pill}"
    padding: "0 0.8rem"
    height: "2.75rem"
  menu-link-hover:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
  input-email:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "0 0.9rem"
    height: "2.75rem"
  progress-bar:
    backgroundColor: "{colors.accent}"
    height: "3px"
---

# Design System: Chain of Custody

## Overview

**Creative North Star: "The Quiet Column"**

Chain of Custody is a calm publication, not a portal. A reader meets one strong lead guide set large in Literata, scrolls one dated feed, opens a guide and reads in a single 40rem column, then finishes on one ending: citation, author, the next guides, the newsletter. Every surface sits on the same centred reading axis, so the home page and the guide feel like the same sheet of paper.

The material is near-white paper and soft ink. Structure comes only from whitespace and 1px hairline rules; there are no cards, no filled panels, no shadows. One deep green carries every link and action. A single warm red appears only when a deadline is inside 30 days, so its appearance is itself the news. The type is upright throughout: a self-hosted serif for headlines and long reading, the platform sans for meta and controls. Light and dark follow the reader's system.

This world replaces an earlier high-density portal (red, condensed display type, modules) that the owner rejected; nothing of it survives. It also refuses the newspaper costume and the SaaS hero.

**Key Characteristics:**
- One 40rem centred reading axis across home, feed, guide, tag and pages.
- Whitespace and hairline rules only; no boxes, fills or shadows.
- One green accent; red reserved for deadlines inside 30 days.
- Literata for reading and headlines, platform sans for meta and controls, never italic.
- Pill-shaped controls with 44px targets; everything else unframed.

## Colors

A near-neutral paper-and-ink palette with one green voice and one conditional red.

### Primary
- **Custody Green** (`{colors.accent}`): links, the pill button, the read link, the active contents marker, the progress bar, focus rings, text selection and success messages. It comes from Ghost's accent colour setting (`--ghost-accent-color`), with this value as the default; the theme must keep working with whatever accent the owner sets. **Deep Custody Green** (`{colors.accent-strong}`) is its hover state only.
- **Dark-mode Green** (`{colors.dark-accent}`, hover `{colors.dark-accent-strong}`): a lighter mint that holds contrast on the dark paper; text on it is `{colors.dark-on-accent}`.

### Secondary
- **Deadline Red** (`{colors.due}`, dark `{colors.dark-due}`): the days-left count of a deadline 30 days away or less, a topic's "Next date" when it is that close, and the newsletter error message. Nothing else.

### Neutral
- **Paper** (`{colors.paper}`, dark `{colors.dark-paper}`): the page ground and the email field background.
- **Ink** (`{colors.ink}`, dark `{colors.dark-ink}`): headlines, prose, strong text inside the deadline lines.
- **Soft Ink** (`{colors.ink-2}`, dark `{colors.dark-ink-2}`): deks, callout and next-deadline text, menu links, footer text, blockquotes.
- **Muted Ink** (`{colors.muted}`, dark `{colors.dark-muted}`): meta lines, breadcrumbs, section headings, contents links, captions, list markers.
- **Hairline** (`{colors.rule}`, dark `{colors.dark-rule}`): every 1px rule, the masthead and footer borders, the contents spine.
- **Field Line** (`{colors.field}`, dark `{colors.dark-field}`): the border of the quiet button and the email input, dark enough to read as a control.
- **Wash** (`{colors.surface}`, dark `{colors.dark-surface}`): hover tint on menu links and the search button, and the ground of inline code and code blocks. Never a panel.

### Named Rules
**The One Voice Rule.** Green is the only accent. Links and actions are green; nothing is green for decoration.

**The Thirty Days Rule.** Red appears only when a dated deadline is 30 days away or less (or a form has failed). A deadline further out is set in ink. If red is on screen, something is due soon.

## Typography

**Display Font:** Literata, self-hosted variable woff2 (200 to 900, upright only), with Georgia, serif. Ghost's heading font setting (`--gh-font-heading`) may override it.
**Body Font:** Literata for prose and deks; the platform sans (system-ui, -apple-system, Segoe UI, Roboto, Helvetica Neue, Arial) for meta, controls, tables, captions and the sources list. Ghost's body font setting (`--gh-font-body`) may override the sans.

**Character:** A bookish, slightly warm serif does the reading and the headlines; a neutral system sans does the bookkeeping. Weight, not style, carries emphasis.

### Hierarchy
- **Display** (600, clamp 2.1 to 3.2rem, 1.12, -0.02em, balanced): the home lead guide title only.
- **Headline** (600, clamp 2 to 3rem, 1.15, -0.016em, balanced): guide and page titles; listing titles use 600 2.4rem.
- **Title** (600, 1.5rem, 1.25): feed entry titles. **Title small** (600, 1.3rem, 1.3): topic names, the citation heading and prose h3. The newsletter heading is 600 1.6rem.
- **Prose h2** (600, 1.65rem, 1.25, 3rem above).
- **Dek** (400, 1.25rem serif, 1.55 to 1.6, Soft Ink): the guide standfirst and the lead dek; feed entry deks drop to 1.0625rem.
- **Body** (400, 1.1875rem serif, 1.72; 1.125rem under 760px): guide prose, 1.3rem between blocks.
- **UI** (400, 1rem sans, 1.6): page default and form text. Controls use 500 0.9375rem.
- **Meta** (400, 0.875rem sans, Muted Ink, tabular figures): bylines, dates, read times, breadcrumbs.
- **Label** (600, 0.8125rem sans, Muted Ink, sentence case): "On this page" and footer column headings. Section headings ("Latest guides", "Browse by framework", "Keep reading") are 600 0.875rem sans over a hairline; they head the list below them, not a title.

### Named Rules
**The Upright Rule.** No italics anywhere. `em`, `i` and `cite` render upright; emphasis is weight 600 or nothing.

**The Heading Stands Alone Rule.** Nothing labels a heading from above: no kicker, eyebrow or category tag set over a title. The topic of a guide lives in its meta line and breadcrumb, never stacked on top of the title.

## Layout

One centred axis. The reading measure is 40rem (`{spacing.read}`) plus the fluid gutter (1.25 to 2.5rem) on each side; the lead, the next-deadline line, the feed, the newsletter, the topics list, the guide header, the guide body and the guide ending all sit on it. The wide measure (68rem) is used only for the masthead, the footer and feature images.

Vertical rhythm is generous and fluid: the lead opens with 3 to 5.5rem of space, sections are separated by 3 to 5.5rem clamps, feed entries carry 1.75rem above and below, topics 1.5rem. Prose blocks are 1.3rem apart; headings get 3rem (h2) and 2.25rem (h3) above and 0.8rem below.

On a guide at 1181px and wider, the body is a three-column grid with the reading column in the middle and the contents list sticky in the left margin (up to 15rem, 2rem from the top). At 1180px and below, the margin contents disappear and a collapsible "On this page" sits above the prose. At 760px and below, the menu becomes a horizontally scrolling row under the brand, the footer drops from four columns to two, and prose steps down to 1.125rem. At 420px the brand sub-line hides.

**The Shared Axis Rule.** Home and guide share one 40rem centred axis. No surface introduces a second column width for content; only chrome and images go wide.

## Elevation & Depth

The system is flat. There are no shadows of any kind and no tonal layering of panels; depth is conveyed by whitespace, by type scale and weight, and by 1px hairlines that open and close a region. The only element that sits above the page is the 3px reading-progress bar, fixed to the top edge.

**The No Box Rule.** Whitespace and hairlines only. No cards, no bordered or filled containers, no shadows. A region that needs separation gets a hairline above (and below, for the callout, next-deadline line and mobile contents), never a frame. The only fills are a control's own pill (button, hover tint) and the wash behind code, which is the code's native material.

## Shapes

Two shapes. Interactive controls are pills (999px): the primary and quiet buttons, the email input, menu links on hover and the search button. Everything else has no corners because it has no frame: entries, topics, callouts and the citation are open text between rules. Small exceptions: inline code (4px), code blocks (8px), the author photo (circle) and the 2px-radius focus ring. Rules are always 1px; a table head rule uses Ink, all others use Hairline.

## Components

### Buttons
Quiet, rounded, and few.
- **Shape:** full pill (999px), 2.75rem minimum height.
- **Pill (primary):** Custody Green ground, white text, 500 0.9375rem sans, 0 1.15rem padding. Used for Subscribe in the masthead and newsletter.
- **Hover / Focus:** ground deepens to Deep Custody Green over 0.2s; focus is a 2px green outline offset 3px.
- **Quiet:** no ground, Ink text, 1px Field Line border, 0 1rem padding; the border turns Ink on hover. Used for Copy citation.
- **Icon button:** 2.75rem round target in Soft Ink; Wash tint and Ink on hover. Used for search.

### Inputs / Fields
- **Style:** the newsletter email field is a pill with a 1px Field Line border on Paper, 2.75rem tall, 0 0.9rem padding, 1rem sans, with a visible label above ("Work email").
- **Focus:** 2px green outline offset 2px.
- **Error / Success:** a status line below; success in green, failure in Deadline Red.

### Navigation
- **Masthead:** a slim bar (4.75rem minimum) closed by a hairline: the publication name in 600 1.3rem Literata with a 0.8125rem muted sub-line, the menu (Latest, Frameworks, Deadlines, About) as 0.9375rem Soft Ink links that tint with Wash on hover, the current page in Ink 600, then search and Subscribe.
- **Breadcrumb:** 0.875rem muted links with a slash separator, above the guide title; links go green and underlined on hover.
- **Footer:** a hairline, then the name and a short about, and three link columns under 0.8125rem labels; a final hairline above the 0.8125rem legal line.
- **Pagination:** muted 0.875rem row with green 500 links.

### Lead
The home page's single strong guide: Display title whose underline draws in from the left on hover (1px, 0.5s), a 1.25rem serif dek capped at 38rem, the meta line (topic, author, date, read time), then a green underlined "Read the guide" link with an arrow.

### Next-deadline line and callout
One sentence between two hairlines (1rem vertical padding on the home page, 0.9rem on a guide): "Next deadline: **Title**, date, in N days. All deadlines". Text is Soft Ink, the title Ink, the days count Ink 600, turning Deadline Red inside 30 days; the closing link is green. On a guide the same line names the framework's next date. It is filled from real docket data and stays hidden when there is none.

### Feed entry
An open entry closed by a hairline, 1.75rem above and below: Title in Literata (green on hover), a 1.0625rem serif dek, then the meta line.

### Topics list
Frameworks as a plain list, each item closed by a hairline with 1.5rem padding: name in Literata 1.3rem, an optional 0.9375rem Soft Ink description, and a meta line with the latest guide and the next date (red inside 30 days).

### Contents
- **Desktop:** in the left margin, sticky, with an "On this page" label and a 1px Hairline spine; links are 0.8125rem muted, the current section turns Ink 500 with its spine segment in green.
- **Mobile:** a disclosure between two hairlines above the prose, with a list icon and a drawn chevron that rotates open; links are 0.9375rem Soft Ink.

### Prose
Literata 1.1875rem/1.72 in the 40rem column. Links green, underlined 1px, thickening to 2px on hover. Blockquotes get a 1px green left rule and Soft Ink text. Tables are sans 0.9375rem with an Ink head rule and Hairline row rules and no fills. The sources list is set in 0.9375rem sans.

### Citation block
Opens 4rem below the prose with a hairline: "Cite this guide" in Literata 1.3rem, the citation in 0.9375rem Soft Ink (wrapping anywhere), and a quiet Copy citation button with a green status message.

### Author block
A hairline, then a 3.5rem round photo (when present) beside "Written by" with the author name as a green link, the bio in Soft Ink, and a link to how the guides are written and checked.

### Newsletter
No panel: a 600 1.6rem Literata heading, a Soft Ink line capped at 34rem, the labelled pill input and pill Subscribe button in one wrapping row.

### Progress bar
A 3px green bar fixed to the top edge of a guide, scaled from the left as the reader scrolls; decorative and hidden from assistive tech.

## Do's and Don'ts

### Do:
- **Do** keep every content surface on the 40rem centred axis; go wide (68rem) only for masthead, footer and images.
- **Do** separate regions with 1px hairlines and whitespace.
- **Do** take the accent from Ghost's accent colour (default #0b6b52) and use it only for links, actions and active states.
- **Do** set the days count of a deadline 30 days away or less in Deadline Red, and every other date in ink.
- **Do** keep controls as pills with 2.75rem targets and a visible 2px green focus ring.
- **Do** use tabular figures for dates, meta and day counts.
- **Do** follow the reader's system for light and dark, using the dark token set.

### Don't:
- **Don't** use italics anywhere, for emphasis, titles or citations.
- **Don't** use boxes, cards, block fills or shadows; the wash is for hover tints and code only.
- **Don't** add a second accent, or use red for anything but near deadlines and form errors.
- **Don't** label a heading from above with a kicker, eyebrow or category tag.
- **Don't** bring back the portal: no condensed display type, no modules, no widget dashboard, no newspaper costume, no SaaS hero.
- **Don't** use emoji or glyph icons; icons are inline 1.6-stroke SVG.
