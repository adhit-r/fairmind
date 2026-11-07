import { UnsupportedEvaluationPackNotice } from '@/components/evaluations/UnsupportedEvaluationPackNotice'

export default function MultimodalBiasDetectionPage() {
  return (
    <UnsupportedEvaluationPackNotice
      title="Multimodal Bias Detection"
      scope="The image, audio, video, and cross-modal detection surface is retained as a release boundary while its modality packs are independently validated."
    />
  )
}
