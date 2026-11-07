'use client'

import { apiClient } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'
import type { ReleaseGate } from './useSystemFile'

export type Tier = 'low' | 'medium' | 'high' | 'critical'
export type Market = 'IN' | 'EU' | 'OTHER'

export const TIERS: Tier[] = ['low', 'medium', 'high', 'critical']

export interface ApplicabilityAnswers {
  use: string | null
  decidesAboutPeople: boolean | null
  /** Only meaningful when decidesAboutPeople is true. */
  humanReview: 'each' | 'automatic' | null
  markets: Market[]
  rbiRegulated: 'yes' | 'no' | 'unsure' | null
  personalDataIndia: boolean | null
  /** Optional, kept verbatim for the audit record. */
  intendedPurpose: string | null
}

export const EMPTY_ANSWERS: ApplicabilityAnswers = {
  use: null,
  decidesAboutPeople: null,
  humanReview: null,
  markets: [],
  rbiRegulated: null,
  personalDataIndia: null,
  intendedPurpose: null,
}

/** A rule that fired; cite.key is a catalogue requirement key and its title is read from the catalogue. */
export interface ApplicabilityRule {
  id: string
  text: string
  cite: { key: string; title: string } | null
}

export interface SuggestedFramework {
  key: string
  name: string
  /** The key is in the pack catalogue; unavailable ones cannot be confirmed yet. */
  available: boolean
  rule: { id: string; text: string }
  binding: string | null
}

export interface ApplicabilitySuggestion {
  rulesVersion: string
  /** Null until use and decidesAboutPeople are answered. */
  tier: Tier | null
  tierRules: ApplicabilityRule[]
  frameworks: SuggestedFramework[]
  uses: Array<{ key: string; label: string }>
  rules: Array<{ id: string; text: string }>
}

export interface ApplicabilityRecord {
  rulesVersion: string
  answers: ApplicabilityAnswers
  suggestedTier: Tier
  tier: Tier
  tierRules: ApplicabilityRule[]
  suggestedFrameworks: string[]
  frameworks: Array<{ key: string; name: string }>
  added: string[]
  removed: string[]
  reason: string | null
  tierBelowSuggestion: boolean
  overrideAcceptedBy: string | null
  overrideAcceptedAt: string | null
  confirmedBy: string
  confirmedAt: string
  evidenceId: string
}

export interface ApplicabilityConfirmBody {
  answers: ApplicabilityAnswers
  tier: Tier
  frameworks: string[]
  reason?: string
}

export interface ApplicabilityResult {
  applicability: ApplicabilityRecord
  gate: ReleaseGate
}

/** What the form would send, and whether it may be sent yet. */
export interface ApplicabilityDraft {
  /** Null until use and decidesAboutPeople are answered. */
  body: ApplicabilityConfirmBody | null
  tier: Tier
  frameworks: string[]
  /** The choice departs from the suggestion: another tier, or a suggested framework dropped. */
  needsReason: boolean
  /** A fresh suggestion is loaded, the first two questions are answered and any required reason is given. */
  ready: boolean
  failed: boolean
}

export const MIN_REASON = 12

/** Builds the confirmation from the person's choices; the server recomputes the suggestion and has the last word. */
export function draftOf(
  choice: { answers: ApplicabilityAnswers; tier: Tier; removed: string[]; added: string[]; reason: string },
  suggestion: ApplicabilitySuggestion | null,
  state: { loading: boolean; failed: boolean },
): ApplicabilityDraft {
  const suggested = (suggestion?.frameworks ?? []).filter((f) => f.available).map((f) => f.key)
  const frameworks = [...new Set([...suggested.filter((k) => !choice.removed.includes(k)), ...choice.added])]
  const needsReason = !!suggestion?.tier && (choice.tier !== suggestion.tier || suggested.some((k) => choice.removed.includes(k)))
  const reason = choice.reason.trim()
  const answered = !!choice.answers.use && choice.answers.decidesAboutPeople !== null
  const body = answered ? { answers: choice.answers, tier: choice.tier, frameworks, ...(reason ? { reason } : {}) } : null
  const ready = !!body && !state.loading && !state.failed && !!suggestion?.tier && (!needsReason || reason.length >= MIN_REASON)
  return { body, tier: choice.tier, frameworks, needsReason, ready, failed: state.failed }
}

/** "Rule T3: ..." from the rules that fired, or "Set by hand: {reason}" when the tier was changed. */
export function tierBasis(record: ApplicabilityRecord | null): string {
  if (!record) return 'Not confirmed'
  if (record.tier !== record.suggestedTier) return `Set by hand: ${record.reason ?? ''}`
  return record.tierRules.map((r) => `Rule ${r.id}: ${r.text}`).join(' ')
}

const GOV = API_ENDPOINTS.aiGovernance

export async function suggestApplicability(answers: Partial<ApplicabilityAnswers>) {
  const res = await apiClient.post<ApplicabilitySuggestion>(GOV.applicabilitySuggest, answers)
  if (!res.success || !res.data) throw new Error(res.error || 'Could not load suggestions')
  return res.data
}

export async function confirmApplicability(systemId: string, body: ApplicabilityConfirmBody) {
  const res = await apiClient.put<ApplicabilityResult>(GOV.systemApplicability(systemId), body, { enableRetry: false })
  if (!res.success || !res.data) throw new Error(res.error || 'Could not record the tier and rules')
  return res.data
}

export async function acceptOverride(systemId: string) {
  const res = await apiClient.post<ApplicabilityResult>(GOV.systemApplicabilityAcceptOverride(systemId), {}, { enableRetry: false })
  if (!res.success || !res.data) throw new Error(res.error || 'Could not accept the lower tier')
  return res.data
}

/** Tier and framework applicability: suggest from answers, confirm on a system, accept a lowered tier. */
export const useApplicability = () => ({ suggest: suggestApplicability, confirm: confirmApplicability, acceptOverride })
