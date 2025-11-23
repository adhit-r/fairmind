'use client';

import { Title, Text, Container, Box, Button, Group } from '@mantine/core';
import { useGlassmorphicTheme } from '@/providers/glassmorphic-theme-provider';

export default function TestUIDesignSystem() {
  const { colorScheme } = useGlassmorphicTheme();

  return (
    <Container size="lg" py="xl">
      <Title order={1} mb="md">UI Design System Test</Title>
      <Text mb="xl">
        This page tests that the UI properly follows the brutalist design system with the orange accent color.
      </Text>
      
      <Box 
        p="md" 
        mb="xl"
        style={{
          border: '2px solid var(--color-black)',
          borderRadius: 'var(--border-radius-none)',
          boxShadow: 'var(--shadow-brutal)',
          background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
        }}
      >
        <Title order={2} mb="sm">Brutalist Design Test</Title>
        <Text mb="sm">
          This box should have the brutalist design with sharp edges, black border, 
          and a brutal shadow effect.
        </Text>
        <Group>
          <Button 
            variant="filled" 
            color="orange"
            style={{
              border: '2px solid var(--color-black)',
              boxShadow: 'var(--shadow-brutal)',
            }}
          >
            Orange Button
          </Button>
          <Button 
            variant="outline"
            style={{
              border: '2px solid var(--color-black)',
              boxShadow: 'var(--shadow-brutal)',
            }}
          >
            Outline Button
          </Button>
        </Group>
      </Box>
    </Container>
  );
}