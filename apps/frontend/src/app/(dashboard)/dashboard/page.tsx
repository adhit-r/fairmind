'use client'

import '@/astryx/pages/home.css'
import Link from 'next/link'
import { Button } from '@astryxdesign/core/Button'
import { Heading, Text } from '@astryxdesign/core/Text'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { LiveBoard } from '@/astryx/LiveBoard'

/** The lifecycle stages a registered system moves through, as the API names them. */
const STAGES = [
  { key: 'onboard', label: 'Onboard' },
  { key: 'assess', label: 'Assess' },
  { key: 'govern', label: 'Govern' },
  { key: 'remediate', label: 'Remediate' },
  { key: 'operate', label: 'Operate' },
] as const

export default function HomePage() {
  const { systems } = useSystemContext()
  const counts = STAGES.map((s) => ({ ...s, n: systems.filter((x) => x.stage === s.key).length }))

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <HStack gap={4} hAlign="between" vAlign="end" wrap="wrap">
          <VStack gap={1}>
            <Heading level={1}>AI estate</Heading>
            <Text color="secondary">
              {systems.length} registered AI system{systems.length === 1 ? '' : 's'}, each against the five release checks and its release decision.
            </Text>
          </VStack>
          <HStack gap={2}>
            <Button label="Find unregistered AI" variant="secondary" href="/discovery" />
            <Button label="Open AI systems" variant="primary" href="/systems" />
          </HStack>
        </HStack>

        <LiveBoard />

        {systems.length > 0 && (
          <section className="fm-card" aria-labelledby="stages-title">
            <VStack gap={3}>
              <Heading level={2} id="stages-title">
                Where the systems are
              </Heading>
              <ol className="fm-stages">
                {counts.map((s) => (
                  <li key={s.key}>
                    <Link href={`/systems?stage=${s.key}`}>
                      <b>{s.n}</b>
                      <span>{s.label}</span>
                    </Link>
                  </li>
                ))}
              </ol>
            </VStack>
          </section>
        )}
      </VStack>
    </div>
  )
}
