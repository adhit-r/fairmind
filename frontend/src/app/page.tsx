"use client"

import { 
  NeoContainer, 
  NeoGrid, 
  NeoHeading, 
  NeoText, 
  NeoAlert, 
  NeoCard, 
  NeoButton, 
  NeoBadge, 
  NeoProgress
} from "@/components/ui/common/neo-components"
import { JourneyNavigation } from "@/components/core/navigation/journey-navigation"
import { Logo } from "@/components/ui/common/logo"

export default function HomePage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="text-center mb-8">
          <Logo size="xl" className="justify-center mb-4" />
          <NeoHeading size="xl" className="mb-4">
            AI Governance Platform
          </NeoHeading>
        </div>
        <NeoText className="text-xl max-w-3xl mx-auto">
          Build trust, ensure fairness, and maintain compliance across all your AI systems.
        </NeoText>
      </div>

      {/* Journey Navigation */}
      <JourneyNavigation />
    </div>
  )
}
