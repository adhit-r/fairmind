'use client'

import { apiClient } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

const GOV = API_ENDPOINTS.aiGovernance

export type ScreenAnswer = 'yes' | 'no' | 'unsure'
export type ScreenOutcome = 'indicated' | 'needs_legal_review' | 'clear'

export interface ProhibitedQuestion {
  key: string
  clause: string
  title: string
  question: string
  /** An exception or carve-out for counsel to weigh; never applied automatically. */
  note: string | null
}

export interface ProhibitedClearance {
  by: string
  at: string
  reason: string
  selfReview: boolean
}

export interface ProhibitedScreenRecord {
  rulesVersion: string
  outcome: ScreenOutcome
  indicated: string[]
  open: string[]
  summary: string
  answers: Array<{ key: string; clause: string; title: string; answer: ScreenAnswer | null }>
  screenedBy: string
  screenedAt: string
  clearance: ProhibitedClearance | null
}

export async function getProhibitedQuestions() {
  const res = await apiClient.get<{ questions: ProhibitedQuestion[] }>(GOV.prohibitedPractices, { enableRetry: true })
  if (!res.success || !res.data) throw new Error(res.error || 'Could not load the Art 5 questions')
  return res.data.questions
}

export async function getProhibitedScreen(systemId: string) {
  const res = await apiClient.get<{ screen: ProhibitedScreenRecord | null; blocking: ScreenOutcome | null }>(GOV.systemProhibitedScreen(systemId), { enableRetry: true })
  if (!res.success || !res.data) throw new Error(res.error || 'Could not load the Art 5 screen')
  return res.data
}

export async function saveProhibitedScreen(systemId: string, answers: Record<string, ScreenAnswer>) {
  const res = await apiClient.put<{ screen: ProhibitedScreenRecord }>(GOV.systemProhibitedScreen(systemId), { answers }, { enableRetry: false })
  if (!res.success || !res.data) throw new Error(res.error || 'Could not save the Art 5 screen')
  return res.data.screen
}

export async function clearProhibitedScreen(systemId: string, reason: string) {
  const res = await apiClient.post<{ screen: ProhibitedScreenRecord }>(GOV.systemProhibitedScreenClear(systemId), { reason }, { enableRetry: false })
  if (!res.success || !res.data) throw new Error(res.error || 'Could not record the clearance')
  return res.data.screen
}
