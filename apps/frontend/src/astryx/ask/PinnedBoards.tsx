'use client'

import { useState } from 'react'
import { Button } from '@astryxdesign/core/Button'
import { Heading, Text } from '@astryxdesign/core/Text'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { useBoards, usePackActions } from '@/lib/api/hooks/usePacks'
import { AskBoard } from './AskBoard'

/** The boards this person pinned from Ask FairMind. Each is drawn live from the current data; nothing shows until one is pinned. */
export function PinnedBoards() {
  const boards = useBoards()
  const { unpinBoard } = usePackActions()
  const [error, setError] = useState<string | null>(null)
  const list = boards.data?.boards ?? []
  if (!list.length && !error) return null

  const unpin = async (id: string) => {
    const res = await unpinBoard(id)
    setError(res.error ?? null)
    boards.reload()
  }
  return (
    <VStack gap={4}>
      {error && <Text color="secondary" size="sm">{error}</Text>}
      {list.map((b) => (
        <section key={b.id} aria-label={`Pinned: ${b.question}`}>
          <VStack gap={2}>
            <HStack gap={3} hAlign="between" vAlign="center" wrap="wrap">
              <Heading level={2}>{b.question}</Heading>
              <Button label="Unpin" variant="secondary" onClick={() => void unpin(b.id)} />
            </HStack>
            <AskBoard board={b.board} />
          </VStack>
        </section>
      ))}
    </VStack>
  )
}
