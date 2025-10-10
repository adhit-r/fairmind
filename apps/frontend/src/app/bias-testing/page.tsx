"use client";

import React from 'react';
import { Container, Title, Text, Stack } from '@mantine/core';
import BiasTestingSimulator from '../../components/simulation/BiasTestingSimulator';

export default function BiasTestingPage() {
  return (
    <Container size="xl" py="xl">
      <Stack gap="xl">
        <div>
          <Title order={1} mb="sm">
            Bias Testing Laboratory
          </Title>
          <Text size="lg" c="dimmed">
            Interactive bias detection testing environment for AI models and systems
          </Text>
        </div>
        
        <BiasTestingSimulator />
      </Stack>
    </Container>
  );
}
