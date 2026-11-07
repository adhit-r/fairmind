import { UnsupportedEvaluationPackNotice } from '@/components/evaluations/UnsupportedEvaluationPackNotice'

export default function ExplainabilityStudioPage() {
  return (
    <UnsupportedEvaluationPackNotice
      title="Explainability Studio"
      scope="The attribution, attention, counterfactual, and causal-analysis surface is retained as a release boundary while its evaluator pack and evidence contract are independently validated."
    />
  )
}
