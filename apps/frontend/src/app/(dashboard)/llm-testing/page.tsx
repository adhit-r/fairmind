import { UnsupportedEvaluationPackNotice } from '@/components/evaluations/UnsupportedEvaluationPackNotice'

export default function LLMTestingPage() {
  return (
    <UnsupportedEvaluationPackNotice
      title="LLM Testing"
      scope="The LLM-as-judge, counterfactual, red-team, embedding, and minimal-pair surfaces are retained as a release boundary while their evaluator packs are independently validated."
    />
  )
}
