import { UnsupportedEvaluationPackNotice } from '@/components/evaluations/UnsupportedEvaluationPackNotice'

export default function ModernBiasEvaluationPage() {
  return (
    <UnsupportedEvaluationPackNotice
      title="Modern Bias Evaluation"
      scope="The combined text, image, audio, and video evaluation surface is retained as a release boundary while its evaluator packs are independently validated."
    />
  )
}
