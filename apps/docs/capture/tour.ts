/**
 * A tour is the one thing written per documented page besides its prose: the steps a person takes on that page. The
 * capture runner (`run.ts`) turns it into a narrated video with captions and a click-through demo of the same steps.
 * Tours run in the read-only demo, so they open forms and drawers but never submit a change.
 */
import type { Page } from 'playwright-core'

/** How a step finds its control: by accessible role and name (preferred), visible text, or CSS as a last resort. */
export type Target =
  | { role: Parameters<Page['getByRole']>[0]; name: string | RegExp; exact?: boolean; nth?: number }
  | { text: string | RegExp; nth?: number }
  | { css: string; nth?: number }

export interface Fill { target: Target; text: string }

export interface Step {
  /** Spoken, captioned and shown in the click-through. One or two short sentences. */
  say: string
  /** An app address such as `/systems`. */
  goto?: string
  click?: Target
  /** Types into a field, or into several in order (a whole form in one step). */
  fill?: Fill | Fill[]
  /** Chooses an option in a select (a filter, a language). */
  select?: { target: Target; option: string }
  /** A key to press after the step's action, such as `Enter`. */
  press?: string
  /** Points at a control without clicking it. */
  point?: Target
  /** Pixels to scroll the page (negative scrolls up). */
  scroll?: number
}

export interface Tour {
  /** The documentation page this tour belongs to, e.g. `app/inventory/systems`; also its media folder. */
  page: string
  /** What the person achieves, used as the video's title. */
  title: string
  steps: Step[]
}

export const tour = (t: Tour): Tour => t

export const role = (r: Parameters<Page['getByRole']>[0], name: string | RegExp, nth?: number): Target => ({ role: r, name, ...(nth !== undefined ? { nth } : {}) })
export const text = (t: string | RegExp, nth?: number): Target => ({ text: t, ...(nth !== undefined ? { nth } : {}) })
export const css = (c: string, nth?: number): Target => ({ css: c, ...(nth !== undefined ? { nth } : {}) })
