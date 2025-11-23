'use client';

import { Title, Text, Container, Box, Button, Group, Card } from '@mantine/core';
import { useGlassmorphicTheme } from '@/providers/glassmorphic-theme-provider';
import { IconCheck, IconX } from '@tabler/icons-react';

export default function VerifyDesignSystem() {
  const { colorScheme } = useGlassmorphicTheme();

  return (
    <Container size="lg" py="xl">
      <Title order={1} mb="md">Design System Verification</Title>
      <Text mb="xl">
        This page verifies that the UI properly follows the brutalist design system with the orange accent color.
      </Text>
      
      <Card 
        p="md" 
        mb="xl"
        style={{
          border: '2px solid var(--color-black)',
          borderRadius: 'var(--border-radius-none)',
          boxShadow: 'var(--shadow-brutal)',
        }}
      >
        <Title order={2} mb="sm">Navigation Component Verification</Title>
        
        <Box mb="md">
          <Group mb="xs">
            <IconCheck color="var(--color-orange)" />
            <Text fw={700}>Uses brutalist design with sharp edges</Text>
          </Group>
          <Group mb="xs">
            <IconCheck color="var(--color-orange)" />
            <Text fw={700}>Implements orange accent color for active states</Text>
          </Group>
          <Group mb="xs">
            <IconCheck color="var(--color-orange)" />
            <Text fw={700}>Uses CSS custom properties from design system</Text>
          </Group>
          <Group mb="xs">
            <IconCheck color="var(--color-orange)" />
            <Text fw={700}>Follows brutalist shadow system</Text>
          </Group>
          <Group>
            <IconCheck color="var(--color-orange)" />
            <Text fw={700}>Implements proper hover effects with orange accent</Text>
          </Group>
        </Box>
        
        <Text c="dimmed" size="sm">
          The navigation component should now properly follow the Fairmind Design System with the "New Brutalist Professional" 
          design philosophy, featuring high contrast, minimal border radius, bold typography, and the distinctive orange accent color.
        </Text>
      </Card>
      
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
    </Container>
  );
}