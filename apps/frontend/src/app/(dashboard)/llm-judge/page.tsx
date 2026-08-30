import { UnsupportedEvaluationPackNotice } from '@/components/evaluations/UnsupportedEvaluationPackNotice'

export default function LLMJudgePage() {
  return (
    <UnsupportedEvaluationPackNotice
      title="LLM Judge"
      scope="The LLM-as-judge surface is retained as a release boundary while its evaluator pack is calibrated and secured."
    />
  )
}
